"""Regression cases from issue #35; inputs are synthetic, not production data."""
from __future__ import annotations

import unittest

from test_static_scan import scan

CONFIG = '''{"main":"src/index.ts","compatibility_date":"2026-10-01",
"observability":{"enabled":true},"d1_databases":[{"binding":"DB","database_id":"x"}],
"r2_buckets":[{"binding":"REPLAYS","bucket_name":"recordings"}]}'''


def report(source: str, **files: str) -> dict:
    return scan({"wrangler.jsonc": CONFIG, "src/index.ts": source, **files})


def ids(result: dict) -> set[str]:
    return {f["check_id"] for f in result["findings"]}


class WorkloadScanTests(unittest.TestCase):
    def test_ci_secret_expressions_are_references_in_yaml(self):
        result = scan({".github/workflows/deploy.yml": """env:
  SECRET_WEBHOOK_URL: ${{secrets.SECRET_WEBHOOK_URL}}
  API_TOKEN: ${{ secrets.API_TOKEN }}
  AUTH_KEY: ${AUTH_KEY}
"""})
        self.assertNotIn("CFDOC-SEC-SECRET-ASSIGNMENT", ids(result))

    def test_explicit_replace_with_example_is_not_a_credential(self):
        result = scan({"README.md": "AUTH_KEY=replace-with-a-local-dev-key\n"})
        self.assertNotIn("CFDOC-SEC-SECRET-ASSIGNMENT", ids(result))

    def test_real_yaml_and_documentation_credentials_remain_leads(self):
        for path in ["README.md", ".github/workflows/deploy.yml"]:
            with self.subTest(path=path):
                result = scan({path: 'AUTH_KEY: "live-9f8a7b6c5d4e3f21"\n'})
                self.assertIn("CFDOC-SEC-SECRET-ASSIGNMENT", ids(result))

    def test_types_labels_and_test_salt_are_not_credentials(self):
        result = scan({
            "cli.ts": "export const CI_SECRET = 'CLOUDFLARE_API_TOKEN';\n"
                      "function put(secrets: Record<string, string>) {}\n"
                      "const credentials: Credentials = loadCredentials();",
            "test/server.ts": "const config = {\n GLASS_SALT_SECRET: 'dev-salt',\n};",
        })
        self.assertNotIn("CFDOC-SEC-SECRET-ASSIGNMENT", ids(result))

    def test_real_test_credential_is_still_reported_and_scoped(self):
        result = scan({"test/leak.ts": 'const apiKey = "live-9f8a7b6c5d4e3f21";'})
        finding = next(f for f in result["findings"] if f["check_id"] == "CFDOC-SEC-SECRET-ASSIGNMENT")
        self.assertEqual("test", finding["runtime_scope"])
        self.assertEqual("lead", finding["status"])

    def test_user_agent_and_header_loop_do_not_become_agent_or_retry(self):
        result = report('''export async function handle(request, env) {
          const ua = request.headers.get('User-Agent');
          for (const [key, value] of Object.entries(headers)) response.headers.set(key, value);
          await env.DB.prepare('SELECT 1').run();
          return new Response(ua);
        }''')
        self.assertNotIn("AGENT-AUTONOMOUS-LOOP-COST", ids(result))
        self.assertNotIn("CFDOC-COST-RETRY-AMPLIFY", ids(result))

    def test_agents_import_and_retry_positive_controls(self):
        result = report('''import { Agent as WorkerAgent } from 'agents';
        export class Runner extends WorkerAgent {
          async run() { while (true) { await this.callTool(); } }
        }
        export async function deliver(url) {
          for (let attempt = 0; attempt < 8; attempt++) {
            const response = await fetch(url);
            if (response.ok) return response;
          }
        }''')
        self.assertIn("AGENT-AUTONOMOUS-LOOP-COST", ids(result))
        self.assertIn("CFDOC-COST-RETRY-AMPLIFY", ids(result))

    def test_node_cli_is_separate_from_worker(self):
        result = report("export default { fetch() { return new Response('ok'); } };", **{
            "cli/package.json": '{"name":"deploy-cli","bin":{"deploy":"index.js"}}',
            "cli/index.js": "const account = process.env.ACCOUNT_ID;",
        })
        self.assertNotIn("CFDOC-CONFIG-PROCESS-ENV", ids(result))
        self.assertEqual("node", next(s for s in result["source_scopes"] if s["path"] == "cli/index.js")["runtime"])

    def test_worker_process_env_positive_control(self):
        result = report("export default { fetch() { return new Response(process.env.MESSAGE); } };")
        self.assertIn("CFDOC-CONFIG-PROCESS-ENV", ids(result))

    def test_worker_node_compat_import_is_not_a_node_cli(self):
        result = report("import {randomUUID} from 'node:crypto'; export default {fetch(){return new Response(process.env.MESSAGE + randomUUID());}};")
        self.assertIn("CFDOC-CONFIG-PROCESS-ENV", ids(result))

    def test_static_assets_do_not_need_worker_observability(self):
        result = scan({"wrangler.jsonc": '{"assets":{"directory":"public"},"compatibility_date":"2026-10-01"}'})
        self.assertNotIn("CFDOC-CONFIG-NO-OBSERVABILITY", ids(result))

    def test_generated_config_is_inventoried_without_execution(self):
        result = scan({"cli.ts": '''import { writeFileSync } from 'node:fs';
        export function render(config) {
          const deployment = { main: 'worker.js', observability: { enabled: true } };
          if (config.lake) deployment.pipelines = [{ binding: 'EVENTS_STREAM', stream: config.stream }];
          return JSON.stringify(deployment);
        }
        throw new Error('scanner must never execute this file');''',
        "worker/lake.ts": "const url = 'https://api.sql.cloudflarestorage.com/api/v1/accounts'; const paths = ['basin-sql'];"})
        self.assertIn("Pipelines", result["detected_products"])
        self.assertIn("Basin SQL", result["detected_products"])
        generated = next(s for s in result["deployment_scopes"] if s["kind"] == "generated")
        self.assertEqual("conditional", generated["products"]["Pipelines"]["availability"])
        self.assertTrue(generated["observability"])
        self.assertNotIn("Stream", result["detected_products"])

    def test_template_serialization_and_test_generator_are_distinct(self):
        result = scan({"deploy.ts": '''function render(config) {
          const deployment = { main: 'worker.js', observability: { enabled: true } };
          return `// generated\n${JSON.stringify(deployment)}`;
        }''', "tests/fake.ts": '''function fake() {
          const config = { main: 'fake.js', ai: true }; return JSON.stringify(config);
        }'''})
        self.assertEqual(1, len(result["deployment_scopes"]))
        self.assertNotIn("Workers AI", result["detected_products"])

    def test_quoted_generated_keys_are_supported(self):
        result = scan({"deploy.ts": '''function render() {
          const config = {"main":"worker.js", "pipelines":[{"binding":"EVENTS","stream":"s"}]};
          return JSON.stringify(config);
        }'''})
        self.assertIn("Pipelines", result["detected_products"])
        self.assertNotIn("Stream", result["detected_products"])

    def test_uppercase_real_credential_is_not_a_ci_label(self):
        result = report('const apiKey = "UPPERCASEVALUE123456789";')
        self.assertIn("CFDOC-SEC-SECRET-ASSIGNMENT", ids(result))

    def test_typed_literal_credential_is_still_reported(self):
        result = report('const apiKey: string = "live-9f8a7b6c5d4e3f21";')
        self.assertIn("CFDOC-SEC-SECRET-ASSIGNMENT", ids(result))

    def test_binding_names_do_not_cross_worker_directories(self):
        result = scan({
            "one/wrangler.jsonc": '{"main":"index.js","compatibility_date":"2026-10-01","kv_namespaces":[{"binding":"DATA","id":"a"}]}',
            "one/index.js": "export default {fetch(){return new Response('ok')}};",
            "two/wrangler.jsonc": '{"main":"index.js","compatibility_date":"2026-10-01","r2_buckets":[{"binding":"DATA","bucket_name":"two"}]}',
            "two/index.js": "export async function list(env) { return env.DATA.list({prefix: 'objects/'}); }",
        })
        self.assertNotIn("CFDOC-COST-KV-LIST-HOTPATH", ids(result))
        self.assertIn("CFDOC-COST-R2-LIST-HOTPATH", ids(result))

    def test_local_window_variable_is_not_a_browser_global(self):
        result = report("async function query(env) { const window = {from: 1}; return env.DB.prepare('SELECT 1').bind(window.from).run(); }")
        self.assertEqual("worker", next(s for s in result["source_scopes"] if s["path"] == "src/index.ts")["runtime"])

    def test_dynamic_bind_parameter_budget(self):
        result = report('''async function touch(db, ids) {
          return db.prepare(`UPDATE persons SET last_seen = ? WHERE project = ? AND id IN (${ids.map(() => '?').join(',')})`)
            .bind(now, project, ...ids).run();
        }''')
        lead = next(f for f in result["findings"] if f["check_id"] == "CFDOC-REL-D1-PARAMETERS")
        self.assertIn("98", lead["message"])
        self.assertTrue(lead["evidence_chain"])
        self.assertIn("https://developers.cloudflare.com/d1/platform/limits/", lead["source_basis"])

    def test_safe_chunk_parameter_budget(self):
        result = report('''async function touch(db, ids) {
          for (let i = 0; i < ids.length; i += 98) {
            const chunk = ids.slice(i, i + 98);
            await db.prepare(`UPDATE persons SET last_seen = ? WHERE project = ? AND id IN (${chunk.map(() => '?').join(',')})`)
              .bind(now, project, ...chunk).run();
          }
        }''')
        self.assertNotIn("CFDOC-REL-D1-PARAMETERS", ids(result))

    def test_parameter_boundaries_and_nested_fixed_arguments(self):
        for size in [98, 99]:
            source = "async function touch(db) { const ids = " + str(list(range(size))) + ''';
              return db.prepare(`UPDATE persons SET last_seen = ? WHERE project = ? AND id IN (${ids.map(() => '?').join(',')})`)
                .bind(Math.max(a, b), project, ...ids).run();
            }'''
            result = report(source)
            self.assertEqual(size == 99, "CFDOC-REL-D1-PARAMETERS" in ids(result))

    def test_repeated_id_parameter_budget(self):
        result = report('''async function erase(db, ids) {
          const marks = ids.map(() => '?').join(',');
          await db.prepare(`DELETE FROM events WHERE project = ? AND (a IN (${marks}) OR b IN (${marks}) OR c IN (${marks}))`)
            .bind(project, ...ids, ...ids, ...ids).run();
        }''')
        lead = next(f for f in result["findings"] if f["check_id"] == "CFDOC-REL-D1-PARAMETERS")
        self.assertIn("33", lead["message"])

    def test_deletion_query_budget(self):
        result = report('''async function erase(db) {
          const { results } = await db.prepare('SELECT id FROM sessions LIMIT 500').all();
          for (const row of results) {
            await db.prepare('DELETE FROM sessions WHERE id = ?').bind(row.id).run();
            await db.prepare('DELETE FROM notes WHERE id = ?').bind(row.id).run();
          }
        }''')
        lead = next(f for f in result["findings"] if f["check_id"] == "CFDOC-REL-D1-QUERY-BUDGET")
        self.assertIn("1001", lead["message"])

    def test_separate_crud_methods_are_not_n_plus_one(self):
        result = report('\n'.join(f"async function action{i}(db) {{ return db.prepare('SELECT id FROM records').all(); }}" for i in range(7)))
        self.assertNotIn("CFDOC-PERF-D1-N-PLUS-ONE", ids(result))

    def test_eu_generated_binding_mismatch_and_safe_pair(self):
        source = '''function create(wrangler, eu) { return wrangler.run(['r2','bucket','create',name,...(eu ? ['--jurisdiction','eu'] : [])]); }
        function render(config) {
          const worker = { main: 'worker.js' };
          worker.r2_buckets = [{ binding: 'REPLAYS', bucket_name: config.bucket EXTRA }];
          return JSON.stringify(worker);
        }'''
        self.assertIn("CFDOC-CONFIG-R2-JURISDICTION", ids(scan({"deploy.ts": source.replace(' EXTRA', '')})))
        self.assertNotIn("CFDOC-CONFIG-R2-JURISDICTION", ids(scan({"deploy.ts": source.replace(' EXTRA', ", jurisdiction: config.eu ? 'eu' : undefined")})))

    def test_route_zone_uses_account_zone_rather_than_label_count(self):
        source = '''function render(config) {
          const zone = config.route.split('/')[0].split('.').slice(-2).join('.');
          return { routes: [{pattern: config.route, zone_name: zone}] };
        }'''
        self.assertIn("CFDOC-CONFIG-ROUTE-ZONE-GUESS", ids(scan({"deploy.ts": source})))
        safe = "function render(config) { return {routes: [{pattern: config.route, zone_id: config.zoneId}]}; }"
        self.assertNotIn("CFDOC-CONFIG-ROUTE-ZONE-GUESS", ids(scan({"deploy.ts": safe})))
        commented = "function render(config) {\n// const zone = config.route.split('.').slice(-2).join('.');\nconst zone = config.zoneName; return {routes:[{pattern:config.route,zone_name:zone}]}; }"
        self.assertNotIn("CFDOC-CONFIG-ROUTE-ZONE-GUESS", ids(scan({"deploy.ts": commented})))

    def test_replay_counter_retry_mismatch_and_receipt_pair(self):
        source = '''async function upload(env, key, bytes) {
          await env.REPLAYS.put(key, bytes);
          RECEIPT
          await env.DB.prepare('INSERT INTO replays (id,chunks) VALUES (?,1) ON CONFLICT(id) DO UPDATE SET chunks = replays.chunks + 1').bind(key).run();
        }'''
        self.assertIn("CFDOC-REL-CROSS-STORE-IDEMPOTENCY", ids(report(source.replace('RECEIPT', ''))))
        receipt = "const receipt = await env.DB.prepare('INSERT OR IGNORE INTO receipts (id) VALUES (?)').bind(key).run(); if (!receipt.meta.changes) return;"
        self.assertNotIn("CFDOC-REL-CROSS-STORE-IDEMPOTENCY", ids(report(source.replace('RECEIPT', receipt))))

    def test_expansion_buffering_and_streamed_pair(self):
        self.assertIn("CFDOC-REL-EXPANSION-BOUND", ids(report('''async function decode(bytes) {
          const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
          return new Response(stream).text();
        }''')))
        self.assertNotIn("CFDOC-REL-EXPANSION-BOUND", ids(report('''async function decode(stream) {
          const reader = stream.pipeThrough(new DecompressionStream('gzip')).getReader();
          let total = 0;
          while (true) { const {value,done} = await reader.read(); if (done) break;
            total += value.byteLength; if (total > 1000000) { await reader.cancel(); throw new Error('large'); }
            await sink.write(value);
          }
        }''')))


if __name__ == "__main__":
    unittest.main()
