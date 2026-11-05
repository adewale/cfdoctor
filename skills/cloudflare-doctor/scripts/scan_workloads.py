"""Bounded source inventory and workload leads; never imports or runs target code.

This module follows local syntax, not arbitrary JavaScript data flow. Unknown
cardinalities, generated values and helper behavior stay unknown in the report.
The caller supplies the scanner's lexer so all offsets refer to original files.
"""
from __future__ import annotations

import ast
import json
import re
from collections import Counter

SOURCES = {
    "CFDOC-REL-D1-PARAMETERS": ["https://developers.cloudflare.com/d1/platform/limits/"],
    "CFDOC-REL-D1-QUERY-BUDGET": ["https://developers.cloudflare.com/d1/platform/limits/"],
    "CFDOC-CONFIG-R2-JURISDICTION": ["https://developers.cloudflare.com/r2/reference/data-location/"],
    "CFDOC-REL-EXPANSION-BOUND": ["https://developers.cloudflare.com/workers/platform/limits/"],
    "CFDOC-REL-DELETION-CONTINUATION": ["https://developers.cloudflare.com/d1/platform/limits/"],
    "CFDOC-REL-CROSS-STORE-IDEMPOTENCY": ["https://developers.cloudflare.com/r2/api/workers/workers-api-reference/"],
    "CFDOC-SEC-INGRESS-POLICY-PARITY": ["https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/"],
    "CFDOC-COST-METER-COVERAGE": [
        "https://developers.cloudflare.com/d1/platform/pricing/",
        "https://developers.cloudflare.com/r2/pricing/",
        "https://developers.cloudflare.com/basin-pipelines/platform/pricing/",
        "https://developers.cloudflare.com/basin-sql/platform/pricing/",
        "https://developers.cloudflare.com/basin-catalog/platform/pricing/",
    ],
    "CFDOC-SEC-RUNTIME-PROVISIONING-TOKEN": ["https://developers.cloudflare.com/fundamentals/api/get-started/create-token/"],
    "CFDOC-REL-TEST-BINDING-CONTRACT": [
        "https://developers.cloudflare.com/d1/platform/limits/",
        "https://developers.cloudflare.com/r2/api/workers/workers-api-reference/",
    ],
}


def blocks(text, mask, matching):
    """Named declarations/methods with balanced bodies; unsupported syntax is skipped."""
    code = mask(text)
    pattern = re.compile(
        r"\bfunction\s+(?P<function>[\w$]+)\s*\(|"
        r"^\s*(?:(?:public|private|protected|static|async)\s+)*(?P<method>[\w$]+)\s*\(",
        re.MULTILINE,
    )
    result = []
    for hit in pattern.finditer(code):
        name = hit.group("function") or hit.group("method")
        if name in {"if", "for", "while", "switch", "catch", "with"}:
            continue
        opening = code.find("(", hit.start())
        closing = matching(code, opening, "(", ")")
        if closing is None:
            continue
        brace = code.find("{", closing)
        if brace < 0 or ";" in code[closing:brace]:
            continue
        end = matching(code, brace, "{", "}")
        if end is None:
            continue
        # A return type can contain an object before the executable body.
        suffix = code[end + 1:].lstrip()
        if code[closing + 1:brace].lstrip().startswith(":") and suffix.startswith((">", "[]", "|")):
            brace = code.find("{", end + 1)
            end = matching(code, brace, "{", "}") if brace >= 0 else None
            if end is None:
                continue
        result.append({"name": name, "start": hit.start(), "body_start": brace,
                       "end": end + 1, "text": text[brace:end + 1],
                       "code": code[brace:end + 1], "params": text[opening + 1:closing]})
    return result


def loops(text, mask, matching):
    code = mask(text)
    for hit in re.finditer(r"\b(for|while)\s*\(", code):
        opening = code.find("(", hit.start())
        closing = matching(code, opening, "(", ")")
        if closing is None:
            continue
        brace = closing + 1
        while brace < len(code) and code[brace].isspace():
            brace += 1
        if brace >= len(code) or code[brace] != "{":
            continue
        end = matching(code, brace, "{", "}")
        if end is not None:
            yield {"start": hit.start(), "end": end + 1,
                   "header": code[opening + 1:closing], "code": code[brace:end + 1],
                   "text": text[brace:end + 1]}


def runtime_inventory(root, files, configs, mask, matching, binding_keys):
    """Describe checked-in and bounded generated scopes without evaluating templates."""
    packages = {}
    for path, text in files:
        if path.name == "package.json":
            try:
                packages[path.parent] = json.loads(text)
            except ValueError:
                pass
    deployments = []
    for path, _, cfg in configs:
        deployments.append({"id": str(path.relative_to(root)), "path": str(path.relative_to(root)),
            "kind": "static-assets" if cfg.get("assets") and not cfg.get("main") else "checked-in",
            "products": {product: {"availability": "declared", "evidence": str(path.relative_to(root))}
                         for key, product in binding_keys.items() if key in cfg},
            "observability": bool(cfg.get("observability")),
            "entrypoint": cfg.get("main"), "deployed": "not inspected"})
    # Generated config candidates require a local object serialized by JSON.stringify.
    for path, text in files:
        if path.suffix not in {".js", ".ts", ".mjs", ".cjs", ".mts"}:
            continue
        if re.search(r"(?:^|/)(?:test|tests|e2e|__tests__|fixtures)(?:/|$)|\.(?:test|spec)\.", str(path.relative_to(root))):
            continue
        for function in blocks(text, mask, matching):
            source, code = function["text"], function["code"]
            for serialized in re.finditer(r"\bJSON\.stringify\s*\(\s*([\w$]+)\b", source):
                if not code[serialized.start():serialized.start() + 4].strip() and not re.search(r"\$\{\s*$", source[:serialized.start()]):
                    continue
                variable = serialized[1]
                declaration = re.search(rf"\b(?:const|let)\s+{re.escape(variable)}(?:\s*:[^=;]+)?\s*=\s*\{{", code)
                if not declaration:
                    continue
                start = code.find("{", declaration.start())
                end = matching(code, start, "{", "}")
                if end is None:
                    continue
                initial = source[start:end + 1]
                assignments = list(re.finditer(rf"\b{re.escape(variable)}\.(\w+)\s*=", code))
                fragments = [(None, initial, declaration.start())]
                for assignment in assignments:
                    opening = code.find("[", assignment.end())
                    if opening >= 0 and not code[assignment.end():opening].strip():
                        closing = matching(code, opening, "[", "]")
                        if closing is not None:
                            fragments.append((assignment[1], source[opening:closing + 1], assignment.start()))
                products, bindings = {}, {}
                for field, fragment, offset in fragments:
                    for key, product in binding_keys.items():
                        fragment_code = mask(fragment)
                        properties = list(re.finditer(rf"\b{key}\s*:", fragment_code))
                        root_property = any(fragment_code[:hit.start()].count("{") - fragment_code[:hit.start()].count("}") == 1 for hit in properties)
                        if (field is not None and field != key) or (field is None and not root_property):
                            continue
                        line = text.count("\n", 0, function["body_start"] + offset) + 1
                        products[product] = {"availability": "conditional" if field else "generated",
                                             "evidence": f"{path.relative_to(root)}:{line}"}
                        names = re.findall(r"\b(?:binding|name)\s*:\s*['\"]([^'\"]+)['\"]", fragment)
                        bindings.setdefault(product, []).extend(names)
                if not products and not re.search(r"\b(?:main|workers_dev|routes)\s*:", mask(initial)):
                    continue
                deployments.append({"id": f"{path.relative_to(root)}#{function['name']}:{variable}",
                    "path": str(path.relative_to(root)), "kind": "generated", "products": products,
                    "bindings": bindings, "observability": bool(re.search(r"\bobservability\s*:\s*\{\s*enabled\s*:\s*true", mask(initial))),
                    "entrypoint": "generated value; not executed", "deployed": "not inspected",
                    "unknowns": ["Generated values, conditions and installed customer configuration require review."]})
    roles = {}
    for path, text in files:
        relative = str(path.relative_to(root))
        code = mask(text) if path.suffix in {".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".mts", ".cts"} else ""
        reasons = []
        if re.search(r"(?:^|/)(?:test|tests|e2e|__tests__|fixtures)(?:/|$)|\.(?:test|spec)\.", relative):
            role, reasons = "test", ["test/fixture path; credential material is still scanned"]
        elif path.suffix in {".md", ".json", ".jsonc", ".toml", ".yml", ".yaml", ".sql"}:
            role, reasons = "data", ["configuration, SQL or prose"]
        else:
            package_dirs = [d for d in packages if path.is_relative_to(d)]
            package = packages[max(package_dirs, key=lambda d: len(d.parts))] if package_dirs else {}
            node = bool(re.search(r"(?:from\s*|import\s*\()['\"]node:", text))
            browser = bool(re.search(r"\b(?:window\.(?:addEventListener|fetch|location|localStorage)|document\.(?:createElement|querySelector|body)|navigator\.(?:sendBeacon|userAgent)|HTMLElement)\b", code))
            static = any(d["kind"] == "static-assets" and path.is_relative_to((root / d["path"]).parent) for d in deployments)
            worker_dirs = [p.parent for p, _, c in configs if c.get("main") or c.get("d1_databases") or c.get("durable_objects")]
            worker_entry = any(c.get("main") and (
                path == p.parent / c["main"] or path.is_relative_to(p.parent / "src")
            ) for p, _, c in configs)
            worker = any(path.is_relative_to(d) for d in worker_dirs) or bool(re.search(
                r"\bextends\s+(?:DurableObject|WorkerEntrypoint|WorkflowEntrypoint|RpcTarget)\b|\b(?:env|this\.env)\.[\w$]+\.(?:prepare|get|put|send)\s*\(", code))
            if package.get("bin") or (node and not worker_entry):
                role, reasons = "node", ["node: import or nearest package bin"]
            elif browser or static:
                role, reasons = "browser", ["DOM API or static-assets deployment directory"]
            elif worker or worker_entry:
                role, reasons = "worker", ["Worker configuration directory or binding/RPC code"]
            else:
                role, reasons = "unresolved", ["No proved runtime; review imports and build graph."]
        roles[relative] = {"path": relative, "runtime": role, "evidence": reasons}
    # Literal HTTP dependencies can expose products absent from Wrangler bindings.
    dependencies = []
    for path, text in files:
        if roles[str(path.relative_to(root))]["runtime"] in {"test", "data"}:
            continue
        if "api.sql.cloudflarestorage.com" in text and re.search(r"['\"](?:basin-sql|r2-sql)['\"]", text):
            dependencies.append({"product": "Basin SQL", "path": str(path.relative_to(root)),
                                 "availability": "HTTP dependency candidate", "deployed": "not inspected"})
        if re.search(r"['\"]r2-data-catalog['\"]", text) and re.search(r"['\"](?:pipelines|sinks)['\"]", text):
            dependencies.append({"product": "Basin Catalog", "path": str(path.relative_to(root)),
                                 "availability": "provisioning candidate", "deployed": "not inspected"})
    return {"deployment_scopes": deployments, "source_scopes": list(roles.values()),
            "dependencies": dependencies, "roles": roles}


def evidence(path, text, offset=0):
    line = text.count("\n", 0, offset) + 1
    excerpt = text.splitlines()[line - 1].strip()[:160] if text.splitlines() else ""
    return f"{path}:{line}: {excerpt}"


def arguments(code):
    """Split already-masked call arguments without splitting nested calls."""
    depth, start, parts = 0, 0, []
    for index, char in enumerate(code):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(code[start:index].strip())
            start = index + 1
    parts.append(code[start:].strip())
    return [part for part in parts if part]


def workload_leads(root, files, inventory, mask, matching):
    leads = []

    def add(check, path, text, offset, message, fix, chain=(), severity="medium", confidence="low"):
        leads.append({"check_id": check, "severity": severity, "title": TITLES[check],
            "category": "security" if "-SEC-" in check else "misconfiguration / reliability" if "-CONFIG-" in check else "cost review" if "-COST-" in check else "reliability / cost review",
            "evidence": evidence(path, text, offset), "why": message, "fix": fix,
            "confidence": confidence, "evidence_chain": list(chain) or [evidence(path, text, offset)]})

    function_index = []
    for path, text in files:
        if path.suffix not in {".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".mts", ".cts"}:
            continue
        relative = str(path.relative_to(root))
        role = inventory["roles"][relative]["runtime"]
        functions = blocks(text, mask, matching)
        for function in functions:
            function_index.append((relative, text, role, function))
        if role == "test":
            if "node:sqlite" in text and re.search(r"\bbind\s*\(\.\.\.", text) and not re.search(r"(?:values|args)\.length\s*>", mask(text)):
                add("CFDOC-REL-TEST-BINDING-CONTRACT", relative, text, text.find("bind("),
                    "SQLite-backed test binding does not visibly enforce a parameter budget; passing SQLite tests does not verify D1 limits.",
                    "Enforce D1 parameter and invocation-query limits in a test binding; keep tests against an authorized Workers runtime for unsupported contracts.", severity="low")
            if re.search(r"\btruncated\s*:", mask(text)) and not re.search(r"\bcursor\s*[:,]", mask(text)):
                add("CFDOC-REL-TEST-BINDING-CONTRACT", relative, text, text.find("truncated"),
                    "A list test double reports truncation without a visible cursor result; multi-page runtime behavior may not be covered.",
                    "Implement cursor round trips and test more than one page, including empty and final pages.", severity="low")
            continue
        # Generator checks are also valid in Node provisioning code.
        generated = [d for d in inventory["deployment_scopes"] if d["kind"] == "generated" and d["path"] == relative]
        if generated and re.search(r"['\"]--jurisdiction['\"]\s*,\s*['\"]eu['\"]", text):
            for function in functions:
                if re.search(r"\.r2_buckets\s*=", function["code"]) and not re.search(r"\bjurisdiction\s*:", function["code"]):
                    add("CFDOC-CONFIG-R2-JURISDICTION", relative, text, function["body_start"],
                        "This generator omits an R2 binding jurisdiction while the same provisioning module can create EU-jurisdiction buckets. Trace the option through callers and reconcile the generated binding with the bucket.",
                        "Carry the actual bucket jurisdiction into each binding; inspect existing resources before changing or replacing buckets.", confidence="medium")
        for function in functions:
            body, code = function["text"], function["code"]
            offset = function["body_start"]
            token = re.search(r"\b([A-Z_]*TOKEN)\s*:\s*([a-zA-Z_$][\w$]*)\s*[,}]", code)
            if token and re.search(rf"\b(?:wrangler|provision|ensure|deploy)\w*\s*\([^;]*\b{re.escape(token[2])}\b|\b(?:createWrangler|listAccounts)\s*\([^;]*\b{re.escape(token[2])}\b", code, re.IGNORECASE):
                add("CFDOC-SEC-RUNTIME-PROVISIONING-TOKEN", relative, text, offset + token.start(),
                    f"The runtime secret {token[1]} receives {token[2]}, which also enters provisioning/account setup in this function. Actual permissions are unknown; secret storage does not narrow capability.",
                    "Accept a separate least-privilege runtime credential, preserve it during upgrades, and verify runtime reads succeed while provisioning edits are denied.")
            if role in {"node", "browser"}:
                continue
            # Match a prepare/bind chain, not unrelated SQL elsewhere in a module.
            for prepared in re.finditer(r"\.prepare\s*\(", code):
                opening = code.find("(", prepared.start())
                closing = matching(code, opening, "(", ")")
                if closing is None:
                    continue
                bound = re.match(r"\s*\.bind\s*\(", code[closing + 1:])
                if not bound:
                    continue
                args_start = closing + 1 + bound.end() - 1
                args_end = matching(code, args_start, "(", ")")
                if args_end is None:
                    continue
                args = code[args_start + 1:args_end]
                spreads = re.findall(r"\.\.\.([\w$]+)(?=\s*[,)]|\s*$)", args)
                if not spreads:
                    continue
                sql = body[opening + 1:closing]
                for variable, copies in Counter(spreads).items():
                    # Only constructed placeholders associated with this collection.
                    if not re.search(rf"\b{re.escape(variable)}\.map\s*\(", body):
                        continue
                    if not re.search(r"\b(?:SELECT|INSERT|UPDATE|DELETE)\b", sql, re.IGNORECASE):
                        continue
                    fixed = len([term for term in arguments(args) if not term.startswith("...")])
                    budget = (100 - fixed) // copies
                    slice_bound = re.search(rf"\b{re.escape(variable)}\s*=\s*[\w$.]+\.slice\s*\(\s*[\w$]+\s*,\s*[\w$]+\s*\+\s*(\d+)\s*\)", code)
                    if slice_bound and int(slice_bound[1]) <= budget:
                        continue
                    literal = re.search(rf"\b{re.escape(variable)}\s*=\s*(\[[^\[\]]*\])", body[:prepared.start()])
                    if literal:
                        try:
                            values = ast.literal_eval(literal[1])
                            if isinstance(values, list) and len(values) <= budget:
                                continue
                        except (ValueError, SyntaxError):
                            pass
                    add("CFDOC-REL-D1-PARAMETERS", relative, text, offset + prepared.start(),
                        f"Constructed SQL binds {fixed} fixed parameters + {copies} × {variable}.length. Under the current documented 100-parameter limit this permits at most {budget} IDs per statement; {budget + 1} would exceed it. Actual incoming cardinality is unknown.",
                        "Prove the incoming collection fits or chunk every statement by its remaining parameter budget; preserve complete operation semantics across chunks.",
                        chain=[evidence(relative, text, offset + prepared.start()), f"bind arguments: {args.strip()[:180]}", f"parameter expression: {fixed} + {copies} * {variable}.length"], confidence="medium")
            for loop in loops(body, mask, matching):
                query_count = len(re.findall(r"\.prepare\s*\([^;]+?\)\s*(?:\.bind\s*\([^;]*?\)\s*)?\.(?:run|all|first)\s*\(", loop["text"], re.DOTALL))
                limit = re.search(r"\bSELECT\b[\s\S]*?\bLIMIT\s+(\d+)", body[:loop["start"]], re.IGNORECASE)
                if query_count and limit and re.search(r"\bof\s+(?:results|rows)\b", loop["header"]):
                    maximum = 1 + int(limit[1]) * query_count
                    if maximum > 50:
                        add("CFDOC-REL-D1-QUERY-BUDGET", relative, text, offset + loop["start"],
                            f"A selection of up to {limit[1]} rows followed by {query_count} individually executed D1 statements per row can issue {maximum} queries including the selection, before caller work. Compare with current invocation limits (50 Free / 1000 Paid); batch calls have different accounting. Early exits and actual row count require review.",
                            "Bound the whole invocation, batch compatible statements, and resume work with persisted progress before the budget is exhausted.", confidence="medium")
            if "DecompressionStream" in code and re.search(r"\.(?:text|arrayBuffer)\s*\(\s*\)", code):
                add("CFDOC-REL-EXPANSION-BOUND", relative, text, offset,
                    "Decompressed output is buffered in full. A compressed upload cap does not bound this allocation; an output-size check after buffering also cannot prevent it.",
                    "Count expanded bytes while reading the stream and stop/cancel before allocating beyond the work budget; validate the decoded schema.")
            elif re.search(r"\b(?:gunzip|inflate|decompress)\s*\(", code, re.IGNORECASE) and re.search(r"\b(?:chunks|events|pages)\[|\.push\s*\(", code):
                guard = re.search(r"\bif\s*\([^)]*(?:total|expanded|sessionBytes|chunkCount)[^)]*[<>]", code, re.IGNORECASE)
                if not guard:
                    add("CFDOC-REL-EXPANSION-BOUND", relative, text, offset,
                        "This path decompresses chunks and accumulates parsed data without a visible total byte/chunk guard. A fetch-concurrency cap does not bound retained data or work across the whole session.",
                        "Trace and bound expanded bytes, retained events and total session work; use incremental processing with resumable progress for larger inputs.")
            additive = re.search(r"\bON\s+CONFLICT[\s\S]*?\bDO\s+UPDATE[\s\S]*?\b(\w+)\s*=\s*(?:\w+\.)?\1\s*\+", body, re.IGNORECASE)
            receipt = re.search(r"INSERT\s+OR\s+IGNORE", body, re.IGNORECASE) and re.search(r"\bif\s*\([^)]*\.meta\.changes", code)
            if re.search(r"\.put\s*\(", code) and additive and not receipt:
                add("CFDOC-REL-CROSS-STORE-IDEMPOTENCY", relative, text, offset,
                    "An object PUT and additive D1 upsert occur in the same operation without a visible guarded receipt. Repeating a deterministic object key can overwrite bytes while incrementing metadata again. Cross-store failure recovery is not established.",
                    "Use unique chunk/delivery receipts and a recoverable protocol between object storage and D1. Verify duplicates, concurrent calls and failure between each side effect.")
        # Estimates are scoped to a computed cost total, not arbitrary pricing prose.
        if re.search(r"\b(?:overageUsd|totalCost)\s*=\s*(?:\w+\s*\(\s*)?\w+\.reduce\s*\(", mask(text)):
            labels = re.findall(r"\bline\s*\(\s*['\"]([^'\"]+)['\"]", text)
            if labels:
                missing = []
                if any("D1" in x for x in labels) and not any(re.search(r"D1.*read", x, re.IGNORECASE) for x in labels):
                    missing.append("D1 rows read")
                if any("R2" in x for x in labels) and not any(re.search(r"Class B|R2.*read", x, re.IGNORECASE) for x in labels):
                    missing.append("R2 read operations")
                if re.search(r"['\"]lake['\"]", text) and not any(re.search(r"Basin|Pipeline|lake|catalog", x, re.IGNORECASE) for x in labels):
                    missing.append("lake storage/transform/delivery/scan/catalog work")
                if missing:
                    add("CFDOC-COST-METER-COVERAGE", relative, text, text.find(".reduce("),
                        "The computed estimate's recognized line items omit " + ", ".join(missing) + ". Inspect alternate calculation paths and exclusions before treating this as a complete bill; no actual spend is measured.",
                        "Label measured, assumed, excluded and unknown meters, preserve per-path execution and product units, and reconcile account allowances for a matching billing window.", severity="low")
    # A limited helper is unsafe as a complete erasure only when its caller
    # proceeds with identity deletion without a continuation loop/job.
    for path, text, role, helper in function_index:
        if role in {"test", "node", "browser"} or not re.search(r"SELECT[\s\S]*?LIMIT\s+\d+", helper["text"], re.IGNORECASE):
            continue
        if not re.search(r"DELETE\s+FROM", helper["text"], re.IGNORECASE):
            continue
        for caller_path, caller_text, caller_role, caller in function_index:
            if caller is helper or caller_role in {"test", "node", "browser"}:
                continue
            call = re.search(rf"\b{re.escape(helper['name'])}\s*\(", caller["code"])
            if not call or not re.search(r"DELETE\s+FROM\s+(?:persons|identities|users)", caller["text"], re.IGNORECASE):
                continue
            if any(loop["start"] <= call.start() < loop["end"] for loop in loops(caller["text"], mask, matching)):
                continue
            if re.search(r"\.send\s*\(|\b(?:cursor|continuation|jobId)\s*:", caller["code"]):
                continue
            add("CFDOC-REL-DELETION-CONTINUATION", caller_path, caller_text, caller["body_start"] + call.start(),
                f"{caller['name']} calls limited deletion helper {helper['name']} once and proceeds to remove identity/person rows. A completed erasure is not established beyond the helper's selected slice.",
                "Persist the erasure identifiers and progress, finish all slices within invocation budgets, and report success only after storage and metadata are verified absent.",
                chain=[evidence(caller_path, caller_text, caller["body_start"] + call.start()), evidence(path, text, helper["body_start"])], confidence="medium")
    # Report sibling ingress-policy differences only when a router actually
    # exposes POST cases and the handlers share a project admission lookup.
    post_handlers = set()
    for _, text in files:
        for case in re.finditer(r"case\s+['\"]([^'\"]+)['\"]\s*:([\s\S]*?)(?=\bcase\s+['\"]|$)", text):
            if re.search(r"request\.method\s*!==?\s*['\"]POST['\"]", case[2]):
                post_handlers.update(re.findall(r"\bawait\s+([\w$]+)\s*\(request\b", case[2]))
    ingress = [(p, t, f) for p, t, role, f in function_index
               if role not in {"test", "node", "browser"} and f["name"] in post_handlers
               and re.search(r"\bgetProject\s*\(", f["code"])]
    guarded = [(p, t, f) for p, t, f in ingress if re.search(r"\ballowedOrigins\b", f["code"]) and ".includes(" in f["code"]]
    for path, text, function in ingress:
        if guarded and not re.search(r"\ballowedOrigins\b|\b(?:admit|admission|requireOrigin)\s*\(", function["code"]):
            add("CFDOC-SEC-INGRESS-POLICY-PARITY", path, text, function["body_start"],
                f"POST handler {function['name']} shares project admission with an origin-checked sibling but has no local equivalent. Inspect inherited middleware before confirming a policy bypass; Origin is not server authentication.",
                "Apply the intended browser admission policy consistently and verify rejected requests perform no storage writes; define server-sender behavior separately.",
                chain=[evidence(path, text, function["body_start"]), evidence(guarded[0][0], guarded[0][1], guarded[0][2]["body_start"])])
    # Nested declarations can expose a call twice; keep the smaller evidence unit.
    unique = {}
    for lead in leads:
        unique[(lead["check_id"], lead["evidence"])] = lead
    return list(unique.values())


TITLES = {
    "CFDOC-REL-D1-PARAMETERS": "Constructed D1 statement needs a parameter budget",
    "CFDOC-REL-D1-QUERY-BUDGET": "Per-item D1 work can exceed an invocation query budget",
    "CFDOC-CONFIG-R2-JURISDICTION": "Bucket creation and generated R2 binding jurisdiction need reconciliation",
    "CFDOC-REL-EXPANSION-BOUND": "Expanded or accumulated data lacks a proved work bound",
    "CFDOC-REL-DELETION-CONTINUATION": "Limited deletion helper is used without visible completion tracking",
    "CFDOC-REL-CROSS-STORE-IDEMPOTENCY": "Object upload and additive metadata need cross-store retry review",
    "CFDOC-SEC-INGRESS-POLICY-PARITY": "Sibling POST handlers apply different admission checks",
    "CFDOC-COST-METER-COVERAGE": "Computed cost estimate omits recognized product meters",
    "CFDOC-SEC-RUNTIME-PROVISIONING-TOKEN": "Provisioning token also supplies a runtime secret",
    "CFDOC-REL-TEST-BINDING-CONTRACT": "Local binding double omits a platform contract",
}
