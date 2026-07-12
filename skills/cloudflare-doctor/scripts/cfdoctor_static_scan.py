#!/usr/bin/env python3
"""Heuristic local scanner for the Cloudflare Doctor skill.

This script is intentionally read-only. It parses wrangler.jsonc, wrangler.json,
legacy wrangler.toml, and local source/docs/IaC text to emit leads for a
human/agent audit; its findings are not proof without checking project context,
current Cloudflare documentation/pricing, and account/dashboard evidence.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except Exception:
        tomllib = None  # type: ignore[assignment]

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    ".wrangler",
    ".next",
    ".nuxt",
    ".svelte-kit",
    "dist",
    "build",
    "coverage",
    ".cache",
    ".turbo",
    ".vercel",
    "corpus-cache",
}

TEXT_EXTS = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".mts",
    ".cts",
    ".json",
    ".jsonc",
    ".toml",
    ".tf",
    ".yaml",
    ".yml",
    ".env",
    ".md",
    ".sql",
}
CODE_EXTS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts", ".tf", ".sql"}
SPECIAL_SOURCE_NAMES = {"_headers", "_redirects", "_routes.json"}

CONFIG_NAMES = {"wrangler.toml", "wrangler.json", "wrangler.jsonc"}
BINDING_KEYS = {
    "kv_namespaces": "KV",
    "d1_databases": "D1",
    "r2_buckets": "R2",
    "durable_objects": "Durable Objects",
    "queues": "Queues",
    "hyperdrive": "Hyperdrive",
    "vectorize": "Vectorize",
    "ai": "Workers AI",
    "analytics_engine_datasets": "Analytics Engine",
    "services": "Service Bindings",
    "workflows": "Workflows",
    "images": "Images",
    "stream": "Stream",
    "browser": "Browser Run",
    "browser_rendering": "Browser Run",
    "worker_loaders": "Dynamic Workers",
    "artifacts": "Artifacts",
    "assets": "Workers Static Assets",
    "containers": "Containers",
    "dispatch_namespaces": "Dynamic Workers",
    "pipelines": "Pipelines",
    "ratelimits": "Rate Limiting bindings",
    "secrets_store_secrets": "Secrets Store",
    "send_email": "Email bindings",
    "vpc_services": "Workers VPC",
}
SECRET_NAME_RE = re.compile(r"(secret|token|password|passwd|private|credential|client_secret|api[_-]?key|auth[_-]?key)", re.I)
SECRET_VALUE_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|cfpat_[A-Za-z0-9_-]+|-----BEGIN [A-Z ]*PRIVATE KEY-----|postgres(?:ql)?://[^\s'\"]+:[^\s'\"]+@|mysql://[^\s'\"]+:[^\s'\"]+@)",
    re.I,
)
SECRET_ASSIGN_RE = re.compile(
    r"^\s*(?:(?:export\s+)?(?:const|let|var)\s+|export\s+)?([A-Za-z_][A-Za-z0-9_-]*)\s*[:=]\s*['\"]?([^'\"\s#]{8,})",
    re.I,
)
PLACEHOLDER_SECRET_RE = re.compile(r"^(?:changeme|change-me|example|placeholder|dummy|test|todo|xxx|your[_-]?)", re.I)
NON_SECRET_ASSIGNMENT_NAMES_RE = re.compile(r"(?:_RE|_REGEX|_PATTERN)$", re.I)

SCANNER_VERSION = "0.3.5"

# check_id -> (pillar, default severity, confidence, title, description). Pillars: COST, SEC, REL, PERF, CONFIG, FIT.
_CHECK_ROWS: list[tuple[str, str, str, str, str, str]] = [
    ("CFDOC-CONFIG-NO-COMPAT-DATE", "CONFIG", "medium", "high", "Missing compatibility_date in Wrangler config", "Wrangler config scope has no explicit compatibility_date."),
    ("CFDOC-CONFIG-COMPAT-DATE-FUTURE", "CONFIG", "high", "high", "compatibility_date is in the future", "compatibility_date is later than today, which can fail deploys or hide unverified copied config."),
    ("CFDOC-CONFIG-COMPAT-DATE-OLD", "CONFIG", "low", "medium", "compatibility_date is old", "compatibility_date is very old, deferring runtime fixes and raising upgrade risk."),
    ("CFDOC-CONFIG-COMPAT-DATE-FORMAT", "CONFIG", "medium", "high", "compatibility_date is not ISO formatted", "compatibility_date is not a YYYY-MM-DD date and can break deploys."),
    ("CFDOC-CONFIG-NODEJS-COMPAT", "CONFIG", "low", "medium", "nodejs_compat enabled; confirm it is required", "nodejs_compat flag is set; unnecessary Node polyfills can hide runtime assumptions."),
    ("CFDOC-SEC-SECRET-IN-CONFIG", "SEC", "high", "medium", "Possible secret stored in Wrangler vars", "A Wrangler vars entry looks like a credential; secrets belong in secret storage."),
    ("CFDOC-CONFIG-DO-NO-MIGRATIONS", "CONFIG", "high", "medium", "Durable Object bindings without migrations in same config scope", "Durable Object bindings exist without Wrangler migrations entries."),
    ("CFDOC-CONFIG-D1-NO-MIGRATIONS", "CONFIG", "medium", "low", "D1 binding without local migration files detected", "A D1 binding has no nearby checked-in migration files; schema may drift."),
    ("CFDOC-REL-QUEUE-NO-DLQ", "REL", "medium", "medium", "Queue consumer has no dead-letter queue; verify terminal failure policy", "Queues retry three times by default, then permanently delete a failed message unless a DLQ is configured; consumers must also tolerate at-least-once delivery."),
    ("CFDOC-REL-CROSS-BOUNDARY-RPC-DEAD", "REL", "low", "low", "Cross-boundary public RPC methods need reachability review", "Public methods on DurableObject/WorkerEntrypoint/WorkflowEntrypoint/RpcTarget/Agent classes may evade generic dead-code linters."),
    ("CFDOC-COST-BROAD-ROUTE", "COST", "medium", "medium", "Broad Worker route should be verified", "A catchall/wildcard Worker route can intercept unintended traffic and invocations."),
    ("CFDOC-COST-CRON-EVERY-MINUTE", "COST", "medium", "high", "Cron trigger runs every minute", "Every-minute cron schedules create constant invocations and downstream usage."),
    ("CFDOC-CONFIG-ENV-BINDING-PARITY", "CONFIG", "low", "low", "Environment binding parity needs verification", "Wrangler env scope is missing bindings declared at top level; envs commonly drift."),
    ("CFDOC-COST-TEMP-ENV-PAID-BINDINGS", "COST", "medium", "medium", "Temporary/preview environment is connected to paid or stateful Cloudflare services", "Preview/demo/workshop env uses paid or stateful Cloudflare products."),
    ("CFDOC-CONFIG-NO-OBSERVABILITY", "CONFIG", "low", "low", "Wrangler observability not configured in this scope", "No observability config; cost/error regressions are harder to diagnose."),
    ("CFDOC-COST-LOG-VOLUME", "COST", "low", "high", "Observability is configured for full head sampling", "Full log/trace sampling is a concrete volume multiplier; materiality still requires traffic, retention, plan, and billing evidence."),
    ("CFDOC-COST-WORKERS-CACHE-BILLING", "COST", "low", "low", "Workers Cache is enabled; verify billing surface and auth-entrypoint exclusion", "Enabling cache.enabled bills hits as requests and makes normally-free static-asset and worker-to-worker traffic billable; auth/gateway entrypoints must disable caching."),
    ("CFDOC-CONFIG-UNPARSEABLE", "CONFIG", "medium", "high", "Could not parse Wrangler config", "Wrangler config failed to parse, so semantic config checks are incomplete."),
    ("CFDOC-SEC-SECRET-VALUE", "SEC", "critical", "medium", "Credential-shaped value appears in repository text", "A token/key/connection-string shaped value appears in tracked text."),
    ("CFDOC-SEC-SECRET-ASSIGNMENT", "SEC", "high", "medium", "Credential-like assignment appears in repository text", "A secret-named variable is assigned a literal value in tracked text."),
    ("CFDOC-COST-PAGES-FUNCTION-ROUTES", "COST", "medium", "medium", "Pages _routes.json broadly invokes Functions without obvious static exclusions", "Broad _routes.json include can send static asset traffic through billable Functions."),
    ("CFDOC-COST-AI-NO-IDEMPOTENCY", "COST", "medium", "medium", "Workers AI call lacks obvious idempotency/cache or is inside retry/loop-shaped code", "Loops, retries, or duplicate actions can repeat paid inference without idempotency/caching."),
    ("CFDOC-COST-VECTORIZE-DIMENSIONS", "COST", "medium", "low", "Vectorize query path should account for queried dimensions and fan-out", "Vectorize cost can depend on dimensions/topK/namespaces; verify against current pricing."),
    ("CFDOC-COST-MEDIA-VARIANT-EXPLOSION", "COST", "medium", "medium", "Media transformation variants or delivery preload may be unbounded", "Image transformation variants or Stream preload can multiply paid work per asset."),
    ("CFDOC-COST-BROWSER-NO-CLOSE", "COST", "high", "medium", "Browser Run session is opened without an obvious close path", "Browser sessions left open or retried blindly can dominate session-time billing."),
    ("DYNAMIC-WORKER-SANDBOX-CAPABILITIES", "SEC", "high", "medium", "Dynamic Worker/code execution lacks obvious capability or resource bounds", "User/LLM code execution without explicit egress/binding/limit posture risks exfiltration and spend."),
    ("CFDOC-COST-DYNAMIC-WORKER-DEDUPE", "COST", "medium", "low", "Dynamic Worker load path lacks obvious stable ID/dedupe", "New Dynamic Workers for repeated identical code can multiply unique-worker cost."),
    ("AGENT-AUTONOMOUS-LOOP-COST", "COST", "medium", "low", "Cloudflare Agent loop/tool path lacks obvious bounds or cancellation", "Agent loops/tools/schedules without max steps or cancellation can repeat paid work."),
    ("ARTIFACTS-UPDATE-SUPPLY-CHAIN", "SEC", "low", "low", "Artifacts-backed loader/update path needs token, signing, and rollback review", "Mutable artifact update flow lacks visible token scope, signing, or rollback controls."),
    ("WORKER-TCP-DB-FIT", "REL", "medium", "low", "Worker TCP/external database path lacks obvious pooling/TLS/timeout controls", "Direct sockets from Workers need TLS, timeouts, pooling, and Hyperdrive fit review."),
    ("CFDOC-COST-UNBOUNDED-FANOUT", "COST", "medium", "medium", "Promise.all map fanout lacks an obvious concurrency cap", "Unbounded fanout multiplies subrequests and downstream paid usage per action."),
    ("CFDOC-COST-RETRY-AMPLIFY", "COST", "medium", "low", "Retry/loop-shaped expensive path lacks obvious backoff or circuit breaker", "Hot retries into paid primitives or degraded dependencies amplify spend and outages."),
    ("CFDOC-COST-WEBHOOK-NO-IDEMPOTENCY", "COST", "medium", "low", "Webhook side effects lack obvious repo-visible idempotency", "Provider retries and duplicate deliveries can repeat downstream writes, fan-out, and paid work."),
    ("CFDOC-SEC-CORS-WILDCARD-CREDS", "SEC", "high", "medium", "Wildcard CORS appears near credentialed responses", "Access-Control-Allow-Origin * combined with credentials breaks browser auth safety."),
    ("CFDOC-SEC-SPOOFABLE-IP-HEADER", "SEC", "medium", "medium", "Code reads spoofable client-IP header", "x-forwarded-for/x-real-ip can be spoofed unless ingress is guaranteed through Cloudflare."),
    ("CFDOC-COST-KV-LIST-HOTPATH", "COST", "medium", "medium", "KV list operation appears in application code", "KV list/prefix scans on hot paths add latency and operation costs."),
    ("CFDOC-FIT-KV-COORDINATION", "FIT", "high", "medium", "KV read-modify-write smell for coordination/counters", "Eventually consistent KV is unsafe for locks, counters, inventory, or rate-limit state."),
    ("CFDOC-COST-R2-LIST-HOTPATH", "COST", "medium", "medium", "R2 bucket list appears in application code", "R2 listing is a storage operation and a poor metadata query path at volume."),
    ("CFDOC-PERF-R2-BUFFERING", "PERF", "medium", "low", "R2 object may be buffered instead of streamed", "Buffering R2 objects increases memory/CPU pressure and delays first byte."),
    ("CFDOC-PERF-D1-SELECT-STAR", "PERF", "low", "medium", "D1 query uses SELECT *; review projection and bounds", "SELECT * widens transfer/decoding and couples code to schema, but does not by itself prove a full scan or increase D1 billed rows read."),
    ("CFDOC-COST-D1-ORDER-RANDOM", "COST", "high", "high", "D1 query orders by RANDOM()", "Random ordering forces expensive scans/sorts that grow with table size."),
    ("CFDOC-PERF-D1-N-PLUS-ONE", "PERF", "low", "low", "Many D1 prepared statements in one file; check for N+1 queries", "Several sequential queries per request can multiply latency and billed rows."),
    ("CFDOC-COST-DO-FRONT-DOOR", "COST", "medium", "low", "Durable Object call path lacks obvious front-door validation", "Invalid/bot traffic should be rejected before it becomes DO requests/duration."),
    ("DO-SHARDING-HOTSPOT", "COST", "high", "high", "Durable Object idFromName uses a global/singleton key", "Low-cardinality DO keys concentrate traffic into one hot object."),
    ("DO-EPHEMERAL-IDEMPOTENCY-OBJECTS", "FIT", "medium", "low", "Durable Object key appears tied to an ephemeral id/request", "One DO per request/idempotency key creates many idle objects and cleanup work."),
    ("DO-STORAGE-LIST-HOTPATH", "COST", "medium", "medium", "Durable Object storage.list appears in code", "DO storage list/prefix scans on hot paths cost more than fetching known keys."),
    ("DO-ALARM-RECURSION", "COST", "medium", "low", "Alarm handler reschedules without obvious idle guard", "Alarms that always reschedule create recurring wake-ups when no work remains."),
    ("DO-STORAGE-BATCHING", "COST", "low", "low", "Multiple Durable Object storage.put calls need coalescing/transaction review", "Batching distinct keys does not reduce their billed storage units; only coalescing redundant writes or changing the data model can reduce rows/units written."),
    ("DO-WEBSOCKET-DURATION", "COST", "medium", "low", "WebSocket handling may not use Durable Object hibernation", "Idle WebSockets without hibernation can increase duration cost."),
    ("DO-SOCKET-CLOSE-HYGIENE", "REL", "medium", "low", "WebSocket path lacks obvious close/error cleanup", "Missing close/error/timeout handling leaves stale connection state."),
    ("DO-WAITUNTIL-LIFECYCLE", "REL", "low", "low", "Durable Object background work should be bounded and API-correct", "DO background work needs the right lifecycle API and a durable primitive for long work."),
    ("KV-VS-DO-STORAGE-FIT", "FIT", "low", "low", "Durable Object storage used for possibly read-heavy data", "Read-heavy write-rare data may fit KV/D1/R2 without DO coordination cost."),
    ("DO-FANOUT-TAX", "COST", "medium", "low", "Fan-out to Durable Objects lacks obvious backpressure", "Waking many DOs from one request concentrates latency and duration without caps."),
    ("CFDOC-PERF-AWAITED-CACHE-PUT", "PERF", "low", "medium", "Cache put awaited in request path", "Awaiting cache writes adds user-visible latency when waitUntil would do."),
    ("CFDOC-PERF-PUBLIC-SERVICE-URL", "PERF", "medium", "medium", "Public Cloudflare service URL fetch; consider service bindings", "Public URLs between same-account Workers add routing overhead and auth ambiguity."),
    ("CFDOC-COST-THIRD-PARTY-ORIGIN", "COST", "medium", "medium", "Worker fetches a public third-party/serverless origin hostname", "Cloudflare-fronted third-party origins still bill on cache misses or direct hostname access."),
    ("CFDOC-COST-ASYNC-LOOP", "COST", "medium", "low", "Worker appears to fetch the incoming request URL", "Self-fetch of the handled URL/host can recursively trigger billable invocations or loop errors."),
    ("CFDOC-CONFIG-PROCESS-ENV", "CONFIG", "low", "low", "process.env reference in Worker-adjacent code", "Workers receive env via handler bindings; process.env may be a Node assumption."),
    ("CFDOC-SEC-TLS-FLEXIBLE", "SEC", "high", "high", "Terraform sets SSL/TLS mode to Flexible", "Flexible SSL leaves the Cloudflare-to-origin leg unencrypted."),
    ("CFDOC-SEC-DNS-UNPROXIED", "SEC", "medium", "medium", "Terraform has unproxied DNS record; verify origin exposure", "DNS-only records bypass Cloudflare WAF/cache/Access and may expose origin."),
]
CHECKS: dict[str, dict[str, str]] = {
    cid: {"pillar": pillar, "severity": severity, "confidence": confidence, "title": title, "description": description}
    for cid, pillar, severity, confidence, title, description in _CHECK_ROWS
}


@dataclass
class Finding:
    check_id: str
    severity: str
    title: str
    category: str
    evidence: str
    why: str
    fix: str
    confidence: str = "medium"

    def __post_init__(self) -> None:
        if self.check_id not in CHECKS:
            raise ValueError(f"unregistered check_id: {self.check_id}")


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            if name in CONFIG_NAMES or path.suffix in TEXT_EXTS or name.startswith(".env"):
                if path.stat().st_size <= 1_500_000:
                    yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def strip_json_comments(src: str) -> str:
    """Remove JSONC comments while preserving offsets and string contents."""
    out = list(src)
    i = 0
    in_str = False
    escaped = False
    while i < len(src):
        c = src[i]
        nxt = src[i + 1] if i + 1 < len(src) else ""
        if in_str:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == "/" and nxt == "/":
            out[i] = out[i + 1] = " "
            i += 2
            while i < len(src) and src[i] not in "\r\n":
                out[i] = " "
                i += 1
            continue
        if c == "/" and nxt == "*":
            out[i] = out[i + 1] = " "
            i += 2
            while i + 1 < len(src) and not (src[i] == "*" and src[i + 1] == "/"):
                if src[i] not in "\r\n":
                    out[i] = " "
                i += 1
            if i + 1 < len(src):
                out[i] = out[i + 1] = " "
                i += 2
            else:
                line = src.count("\n", 0, i) + 1
                raise ValueError(f"unterminated block comment at line {line}")
            continue
        i += 1
    return "".join(out)


def strip_json_trailing_commas(src: str) -> str:
    """Remove JSONC trailing commas outside strings while preserving offsets."""
    out = list(src)
    in_str = False
    escaped = False
    for i, c in enumerate(src):
        if in_str:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
            continue
        if c != ",":
            continue
        j = i + 1
        while j < len(src) and src[j].isspace():
            j += 1
        if j < len(src) and src[j] in "]}":
            out[i] = " "
    return "".join(out)


class ConfigParseError(ValueError):
    """A Wrangler config could not be parsed."""


def parse_config(path: Path, text: str) -> dict[str, Any]:
    try:
        if path.name == "wrangler.toml":
            if tomllib is None:
                raise ConfigParseError("TOML parsing requires Python 3.11+ or tomli")
            data = tomllib.loads(text)
        elif path.name in {"wrangler.json", "wrangler.jsonc"}:
            normalized = strip_json_trailing_commas(strip_json_comments(text))
            data = json.loads(normalized)
        else:
            raise ConfigParseError(f"unsupported config format: {path.name}")
    except (json.JSONDecodeError, ConfigParseError) as exc:
        raise ConfigParseError(str(exc)) from exc
    except Exception as exc:
        raise ConfigParseError(str(exc)) from exc
    if not isinstance(data, dict):
        raise ConfigParseError("top-level Wrangler config must be an object/table")
    return data


def line_for(text: str, pattern: str | re.Pattern[str]) -> tuple[int, str] | None:
    rx = re.compile(pattern) if isinstance(pattern, str) else pattern
    for i, line in enumerate(text.splitlines(), 1):
        if rx.search(line):
            return i, line.strip()
    return None


def excerpt(line: str, limit: int = 160) -> str:
    return line.strip().replace("\t", " ")[:limit]


def is_sensitive_assignment(match: re.Match[str]) -> bool:
    name = match.group(1)
    value = match.group(2)
    if not SECRET_NAME_RE.search(name):
        return False
    if NON_SECRET_ASSIGNMENT_NAMES_RE.search(name):
        return False
    if PLACEHOLDER_SECRET_RE.search(value):
        return False
    if re.match(r"(?:re\.compile|RegExp)\(", value):
        return False
    return True


def redacted_secret_line(line: str, limit: int = 160) -> str:
    redacted = SECRET_VALUE_RE.sub("<redacted-secret>", line.strip())
    match = SECRET_ASSIGN_RE.search(redacted)
    if match and is_sensitive_assignment(match):
        start, end = match.span(2)
        redacted = f"{redacted[:start]}<redacted-secret>{redacted[end:]}"
    return redacted.replace("\t", " ")[:limit]


def values_from_binding_entries(entries: Any) -> list[str]:
    names: list[str] = []
    if isinstance(entries, list):
        for item in entries:
            if isinstance(item, dict):
                for key in ("binding", "name", "class_name", "queue", "bucket_name", "database_name"):
                    val = item.get(key)
                    if isinstance(val, str) and val not in names:
                        names.append(val)
            elif isinstance(item, str) and item not in names:
                names.append(item)
    elif isinstance(entries, dict):
        for key, val in entries.items():
            if isinstance(val, dict):
                binding = val.get("binding") or val.get("name") or key
                if isinstance(binding, str) and binding not in names:
                    names.append(binding)
            elif isinstance(val, str) and val not in names:
                names.append(val)
    return names


def collect_bindings(configs: list[tuple[Path, str, dict[str, Any]]]) -> dict[str, set[str]]:
    bindings: dict[str, set[str]] = {product: set() for product in BINDING_KEYS.values()}
    bindings["Workers"] = set()
    bindings["Pages"] = set()

    def visit_cfg(data: dict[str, Any]) -> None:
        project_name = str(data.get("name") or "configured")
        if any(key in data for key in ("main", "routes", "workers_dev", "triggers", "assets", "site")):
            bindings["Workers"].add(project_name)
        if data.get("pages_build_output_dir"):
            bindings["Pages"].add(project_name)
        if data.get("ai") is True:
            bindings["Workers AI"].add("AI")
        for key, product in BINDING_KEYS.items():
            if key in data:
                for name in values_from_binding_entries(data.get(key)):
                    bindings[product].add(name)
        durable = data.get("durable_objects")
        if isinstance(durable, dict):
            for name in values_from_binding_entries(durable.get("bindings")):
                bindings["Durable Objects"].add(name)
        queues = data.get("queues")
        if isinstance(queues, dict):
            for sub in ("producers", "consumers"):
                for name in values_from_binding_entries(queues.get(sub)):
                    bindings["Queues"].add(name)
        envs = data.get("env")
        if isinstance(envs, dict):
            for env_data in envs.values():
                if isinstance(env_data, dict):
                    visit_cfg(env_data)

    for _, _, data in configs:
        visit_cfg(data)
    return bindings


def d1_migration_dirs(config_path: Path, data: dict[str, Any]) -> list[Path]:
    dirs: list[Path] = []
    entries = data.get("d1_databases")
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("migrations_dir"), str):
                dirs.append(config_path.parent / entry["migrations_dir"])
    elif isinstance(entries, dict):
        for entry in entries.values():
            if isinstance(entry, dict) and isinstance(entry.get("migrations_dir"), str):
                dirs.append(config_path.parent / entry["migrations_dir"])
    dirs.extend([config_path.parent / "migrations", config_path.parent / "d1" / "migrations"])
    return dirs


def has_local_d1_migrations(config_path: Path, data: dict[str, Any]) -> bool:
    for directory in d1_migration_dirs(config_path, data):
        if directory.exists() and any(directory.rglob("*.sql")):
            return True
    return False


def queue_consumers(data: dict[str, Any]) -> list[dict[str, Any]]:
    queues = data.get("queues")
    if not isinstance(queues, dict):
        return []
    consumers = queues.get("consumers")
    return [entry for entry in consumers if isinstance(entry, dict)] if isinstance(consumers, list) else []


def add_config_findings(root: Path, configs: list[tuple[Path, str, dict[str, Any]]], findings: list[Finding], parse_errors: list[tuple[Path, str]] | None = None) -> None:
    today = _dt.date.today()
    d1_migrations_reported: set[Path] = set()

    def inspect_one(path: Path, text: str, data: dict[str, Any], prefix: str = "", is_env: bool = False, parent_data: dict[str, Any] | None = None) -> None:
        label = f"{rel(path, root)}{prefix}"
        parent_data = parent_data or {}
        compatibility_date = data.get("compatibility_date")
        if not compatibility_date and not is_env:
            findings.append(Finding(
                "CFDOC-CONFIG-NO-COMPAT-DATE",
                "medium",
                "Missing compatibility_date in Wrangler config",
                "misconfiguration / best-practice drift",
                label,
                "Workers behavior is gated by compatibility dates. Without an explicit maintained date, deploy behavior and platform upgrades are harder to reason about.",
                "Set an intentional `compatibility_date`, update it on a controlled cadence, and test after updates.",
                "high",
            ))
        elif isinstance(compatibility_date, str):
            try:
                dt = _dt.date.fromisoformat(compatibility_date)
                if dt > today + _dt.timedelta(days=1):
                    findings.append(Finding(
                        "CFDOC-CONFIG-COMPAT-DATE-FUTURE",
                        "high",
                        "compatibility_date is in the future",
                        "misconfiguration",
                        f"{label}: compatibility_date={compatibility_date}",
                        "A future compatibility date may fail deployment or hide that config was copied without verification.",
                        "Use today's date or the latest date already validated in this project.",
                        "high",
                    ))
                elif today - dt > _dt.timedelta(days=540):
                    findings.append(Finding(
                        "CFDOC-CONFIG-COMPAT-DATE-OLD",
                        "low",
                        "compatibility_date is old",
                        "best-practice drift / missed optimization",
                        f"{label}: compatibility_date={compatibility_date}",
                        "Very old compatibility dates can defer runtime fixes/improvements and make future upgrades riskier.",
                        "Review Cloudflare compatibility changes, bump the date in staging, and run integration tests.",
                        "medium",
                    ))
            except ValueError:
                findings.append(Finding(
                    "CFDOC-CONFIG-COMPAT-DATE-FORMAT",
                    "medium",
                    "compatibility_date is not ISO formatted",
                    "misconfiguration",
                    f"{label}: compatibility_date={compatibility_date}",
                    "Wrangler expects date-shaped compatibility settings; malformed values can break deploys.",
                    "Use `YYYY-MM-DD` format and validate with Wrangler.",
                    "high",
                ))

        flags = data.get("compatibility_flags")
        if isinstance(flags, list) and any(str(f).lower() == "nodejs_compat" for f in flags):
            findings.append(Finding(
                "CFDOC-CONFIG-NODEJS-COMPAT",
                "low",
                "nodejs_compat enabled; confirm it is required",
                "best-practice drift / missed optimization",
                f"{label}: compatibility_flags includes nodejs_compat",
                "Node compatibility can be necessary, but unnecessary polyfills can increase bundle surface and hide runtime assumptions.",
                "Keep it if the code uses supported Node APIs; otherwise remove and prefer Web/Workers-native APIs.",
                "medium",
            ))

        cache_obj = data.get("cache")
        top_cache_on = isinstance(cache_obj, dict) and bool(cache_obj.get("enabled"))
        exports_obj = data.get("exports")
        cached_entrypoints: list[str] = []
        if isinstance(exports_obj, dict):
            for ep_name, ep_data in exports_obj.items():
                ep_cache = ep_data.get("cache") if isinstance(ep_data, dict) else None
                if isinstance(ep_cache, dict) and ep_cache.get("enabled"):
                    cached_entrypoints.append(str(ep_name))
        if top_cache_on or cached_entrypoints:
            where = f"exports: {', '.join(cached_entrypoints)}" if cached_entrypoints else "cache.enabled=true"
            findings.append(Finding(
                "CFDOC-COST-WORKERS-CACHE-BILLING",
                "low",
                "Workers Cache is enabled; verify billing surface and auth-entrypoint exclusion",
                "cost footgun / security",
                f"{label}: {where}",
                "Workers Cache serves hits without running the Worker (saving CPU) but still bills each hit as a request, and it makes normally-free traffic billable: static-asset requests and worker-to-worker invocations through service bindings or ctx.exports are charged at the standard request rate once caching is on. A cache hit also skips any auth/gateway logic on the cached entrypoint.",
                "Confirm the billing-surface change is intended; disable caching on auth/gateway entrypoints (`exports.<name>.cache.enabled = false`) and cache only inner entrypoints; carry tenant/authorization context in `ctx.props` so cached responses are not shared across tenants. Verify against current Workers Cache pricing/limits docs.",
                "low",
            ))

        vars_obj = data.get("vars")
        if isinstance(vars_obj, dict):
            for name, value in vars_obj.items():
                value_s = str(value)
                if SECRET_NAME_RE.search(name) or SECRET_VALUE_RE.search(value_s):
                    findings.append(Finding(
                        "CFDOC-SEC-SECRET-IN-CONFIG",
                        "high",
                        "Possible secret stored in Wrangler vars",
                        "security / misconfiguration",
                        f"{label}: vars.{name}",
                        "Wrangler `vars` are configuration values and can be visible in config/source. Credentials should be stored as secrets.",
                        "Rotate if exposed, move the value to Cloudflare secrets/CI secret storage, and keep only non-secret config in `vars`.",
                        "medium",
                    ))

        durable = data.get("durable_objects")
        has_do = bool(durable)
        inherited_migrations = bool(parent_data.get("migrations"))
        if has_do and not data.get("migrations") and not inherited_migrations:
            findings.append(Finding(
                "CFDOC-CONFIG-DO-NO-MIGRATIONS",
                "high",
                "Durable Object bindings without migrations in same config scope",
                "misconfiguration / reliability",
                label,
                "Durable Object class lifecycle is tracked through Wrangler migrations. Missing migrations can break deploys or class renames.",
                "Add/verify `migrations` entries for every new, renamed, or deleted Durable Object class in each relevant environment.",
                "medium",
            ))

        if data.get("d1_databases") and path not in d1_migrations_reported and not has_local_d1_migrations(path, data):
            d1_migrations_reported.add(path)
            findings.append(Finding(
                "CFDOC-CONFIG-D1-NO-MIGRATIONS",
                "medium",
                "D1 binding without local migration files detected",
                "misconfiguration / reliability",
                label,
                "D1 schema changes should be managed with checked-in migrations. A binding without nearby migration files can indicate dashboard-only schema drift or missing deploy steps.",
                "Verify the intended migration process; add checked-in D1 migrations or document the controlled schema-management path.",
                "low",
            ))

        consumers_missing_dlq = []
        for consumer in queue_consumers(data):
            has_dlq = any(isinstance(consumer.get(key), str) and consumer.get(key).strip() for key in ("dead_letter_queue", "dead_letter_queue_name"))
            if not has_dlq:
                consumers_missing_dlq.append(str(consumer.get("queue") or consumer.get("name") or "consumer"))
        if consumers_missing_dlq:
            findings.append(Finding(
                "CFDOC-REL-QUEUE-NO-DLQ",
                "medium",
                "Queue consumer has no dead-letter queue; verify terminal failure policy",
                "misconfiguration / reliability / cost footgun",
                f"{label}: {', '.join(consumers_missing_dlq)}",
                "Cloudflare Queues use at-least-once delivery and retry a failed message three times by default. After the configured retry limit, a message is permanently deleted unless a DLQ is configured; duplicates and retries can still repeat downstream side effects.",
                "Make the consumer idempotent, set retry/delay behavior intentionally, and configure a DLQ plus alerting/replay when permanent deletion is not acceptable.",
                "medium",
            ))

        routes = data.get("routes")
        route_values: list[str] = []
        if isinstance(routes, list):
            for r in routes:
                if isinstance(r, str):
                    route_values.append(r)
                elif isinstance(r, dict) and isinstance(r.get("pattern"), str):
                    route_values.append(r["pattern"])
        elif isinstance(routes, str):
            route_values.append(routes)
        for route in route_values:
            if route in {"*", "*/*"} or route.startswith("*") or route.count("*") >= 2:
                findings.append(Finding(
                    "CFDOC-COST-BROAD-ROUTE",
                    "medium",
                    "Broad Worker route should be verified",
                    "misconfiguration / cost footgun",
                    f"{label}: route {route!r}",
                    "Broad routes can intercept unintended traffic, bypass cache/origin assumptions, and increase Worker invocations.",
                    "Narrow the route to intended host/path or document why the catchall is required.",
                    "medium",
                ))

        triggers = data.get("triggers")
        if isinstance(triggers, dict) and isinstance(triggers.get("crons"), list):
            for cron in triggers["crons"]:
                if isinstance(cron, str) and re.match(r"^(\*|\*/1)\s", cron):
                    findings.append(Finding(
                        "CFDOC-COST-CRON-EVERY-MINUTE",
                        "medium",
                        "Cron trigger runs every minute",
                        "cost footgun / reliability",
                        f"{label}: cron {cron!r}",
                        "Every-minute cron schedules create constant Worker invocations and can amplify downstream storage/API costs, especially across environments.",
                        "Confirm the cadence is necessary; prefer event-driven Queues/Workflows or less frequent batching where possible.",
                        "high",
                    ))

        envs = data.get("env")
        binding_keys_present = [k for k in BINDING_KEYS if k in data]
        if not is_env and isinstance(envs, dict) and binding_keys_present:
            paid_or_stateful_keys = {
                "d1_databases", "r2_buckets", "durable_objects", "queues", "vectorize", "ai",
                "analytics_engine_datasets", "workflows", "images", "stream", "browser", "browser_rendering", "worker_loaders", "artifacts",
            }
            for env_name, env_data in envs.items():
                if isinstance(env_data, dict):
                    missing = [k for k in binding_keys_present if k not in env_data]
                    if missing:
                        findings.append(Finding(
                            "CFDOC-CONFIG-ENV-BINDING-PARITY",
                            "low",
                            "Environment binding parity needs verification",
                            "misconfiguration / reliability",
                            f"{label}: env.{env_name} missing explicit {', '.join(missing)}",
                            "Some Wrangler environment keys/bindings are non-inheritable or commonly drift between envs. Production-only binding drift is a common failure mode.",
                            "Verify inheritance for this Wrangler version and make production/staging bindings explicit where safety matters.",
                            "low",
                        ))
                    if re.search(r"preview|demo|workshop|branch|test", env_name, re.I):
                        env_paid = [k for k in paid_or_stateful_keys if k in env_data]
                        inherited_paid = [k for k in paid_or_stateful_keys if k in data and k not in env_data]
                        if env_paid or inherited_paid:
                            findings.append(Finding(
                                "CFDOC-COST-TEMP-ENV-PAID-BINDINGS",
                                "medium",
                                "Temporary/preview environment is connected to paid or stateful Cloudflare services",
                                "cost footgun / misconfiguration",
                                f"{label}: env.{env_name} uses {', '.join(sorted(set(env_paid + inherited_paid)))}",
                                "Preview, demo, workshop, and branch deployments can keep generating paid storage/compute/AI/browser/queue usage after their intended lifetime, especially when inherited bindings point at production resources.",
                                "Give temporary envs separate capped resources, disable routes/crons when idle, and remove demo/workshop deployments after use.",
                                "medium",
                            ))

        observability = data.get("observability")
        if isinstance(observability, dict):
            logs = observability.get("logs") if isinstance(observability.get("logs"), dict) else {}
            traces = observability.get("traces") if isinstance(observability.get("traces"), dict) else {}
            full_sampling = any(value == 1 or value == 1.0 for value in (
                observability.get("head_sampling_rate"), logs.get("head_sampling_rate"), traces.get("head_sampling_rate")
            ))
            if full_sampling:
                findings.append(Finding(
                    "CFDOC-COST-LOG-VOLUME",
                    "low",
                    "Observability is configured for full head sampling",
                    "cost review / observability",
                    f"{label}: head_sampling_rate=1",
                    "Full sampling can multiply retained log/trace volume, but repository config alone does not establish traffic, retention, plan, or cost materiality.",
                    "Measure invocation/log/trace volume and retention, confirm the current plan and billing meter, then lower sampling only if the evidence supports it.",
                    "high",
                ))

        if not is_env and not observability:
            findings.append(Finding(
                "CFDOC-CONFIG-NO-OBSERVABILITY",
                "low",
                "Wrangler observability not configured in this scope",
                "best-practice drift / reliability",
                label,
                "Without intentional observability/logging, regressions in CPU, errors, queue retries, or storage operations are harder to diagnose.",
                "Configure observability or document the external monitoring/logging path used for this Worker.",
                "low",
            ))

        if isinstance(envs, dict):
            for env_name, env_data in envs.items():
                if isinstance(env_data, dict):
                    inspect_one(path, text, env_data, f" [env.{env_name}]", is_env=True, parent_data=data)

    for path, text, data in configs:
        inspect_one(path, text, data)

    for path, error in parse_errors or []:
        findings.append(Finding(
            "CFDOC-CONFIG-UNPARSEABLE",
            "medium",
            "Could not parse Wrangler config",
            "misconfiguration",
            f"{rel(path, root)}: {error[:240]}",
            "The scanner could not parse this config, so product, binding, route, and environment checks for it are incomplete.",
            "Validate the config with Wrangler and fix the reported syntax error before relying on scanner results.",
            "high",
        ))


def static_string_symbols(files: list[tuple[Path, str]]) -> set[str]:
    """Resolve simple repo-visible constant/alias chains used as singleton keys."""
    definitions: dict[str, list[str]] = {}
    aliases: dict[str, list[str]] = {}
    for _, text in files:
        for match in re.finditer(r"(?m)^\s*(?:export\s+)?const\s+([A-Za-z_$][\w$]*)\s*=\s*([^;\n]+)", text):
            definitions.setdefault(match.group(1), []).append(match.group(2).strip())
        for match in re.finditer(r"(?m)^\s*import\s*\{([^}]+)\}\s*from\s*['\"][^'\"]+['\"]", text):
            for item in match.group(1).split(","):
                parts = re.split(r"\s+as\s+", item.strip())
                if parts and parts[0]:
                    aliases.setdefault(parts[-1], []).append(parts[0])

    static: set[str] = set()
    for _ in range(8):
        changed = False
        for name, expressions in definitions.items():
            # Ambiguous duplicate definitions are not safe to resolve globally.
            if len(set(expressions)) != 1:
                continue
            expr = expressions[0]
            stripped = re.sub(r"(['\"])(?:\\.|(?!\1).)*\1", "", expr)
            stripped = re.sub(r"`(?:\\.|[^`])*`", "", stripped)
            identifiers = re.findall(r"\b[A-Za-z_$][\w$]*\b", stripped)
            dynamic = [token for token in identifiers if token not in static and token not in {"env", "undefined"}]
            has_literal = bool(re.search(r"['\"`]", expr))
            alias_only = bool(re.fullmatch(r"[A-Za-z_$][\w$]*", expr))
            if (has_literal or alias_only) and not dynamic and name not in static:
                static.add(name)
                changed = True
        for local, imported_values in aliases.items():
            if len(set(imported_values)) == 1 and imported_values[0] in static and local not in static:
                static.add(local)
                changed = True
        if not changed:
            break
    return static


def stream_source_symbols(files: list[tuple[Path, str]]) -> set[str]:
    symbols: set[str] = set()
    for _, text in files:
        if not re.search(r"(?:cloudflarestream\.com|videodelivery\.net)", text, re.I):
            continue
        symbols.update(re.findall(r"(?m)^\s*export\s+(?:const|function|class)\s+([A-Za-z_$][\w$]*)", text))
    return symbols


def add_code_findings(
    root: Path,
    files: list[tuple[Path, str]],
    bindings: dict[str, set[str]],
    findings: list[Finding],
    queue_consumer_names: set[str] | None = None,
) -> None:
    queue_consumer_names = queue_consumer_names or set()
    kv_names = bindings.get("KV", set())
    static_symbols = static_string_symbols(files)
    stream_symbols = stream_source_symbols(files)
    project_has_stream_host = any(
        re.search(r"(?:cloudflarestream\.com|videodelivery\.net)", t, re.I) for _, t in files
    )
    d1_names = bindings.get("D1", set())
    r2_names = bindings.get("R2", set())
    ai_names = bindings.get("Workers AI", set()) or {"AI"}
    vectorize_names = bindings.get("Vectorize", set())
    dynamic_worker_names = bindings.get("Dynamic Workers", set()) or {"LOADER"}
    artifacts_names = bindings.get("Artifacts", set())

    source_files = [(path, text) for path, text in files if path.suffix in CODE_EXTS]
    project_text = "\n".join(text for _, text in source_files)
    webhook_shaped = any(
        "webhook" in path.as_posix().lower()
        or re.search(r"webhook|x-github-event|stripe-signature|svix-|x-signature", text, re.I)
        for path, text in source_files
    )
    has_webhook_side_effect = bool(re.search(
        r"Promise\.all|waitUntil|\.send\s*\(|\.put\s*\(|\.insert\s*\(|fetch\s*\([^)]*,\s*\{[^}]*method\s*:\s*['\"]POST",
        project_text,
        re.I | re.S,
    ))
    has_webhook_idempotency = bool(re.search(
        r"idempoten|dedup|delivery[_-]?id|event[_-]?id|x-github-delivery|webhook[_-]?id|alreadyProcessed|processedEvents",
        project_text,
        re.I,
    ))
    if webhook_shaped and has_webhook_side_effect and not has_webhook_idempotency:
        evidence_path, evidence_text = next(
            ((path, text) for path, text in source_files if re.search(r"webhook|request\.json\s*\(|Promise\.all|waitUntil", text, re.I)),
            source_files[0],
        )
        hit = line_for(evidence_text, re.compile(r"webhook|request\.json\s*\(|Promise\.all|waitUntil", re.I)) or (1, "")
        findings.append(Finding(
            "CFDOC-COST-WEBHOOK-NO-IDEMPOTENCY",
            "medium",
            "Webhook side effects lack obvious repo-visible idempotency",
            "cost footgun / reliability",
            f"{rel(evidence_path, root)}:{hit[0]}: {excerpt(hit[1])}",
            "Webhook providers can retry or duplicate deliveries. Without a stable delivery/event key, downstream writes, fan-out, Queues, or paid API calls can repeat.",
            "Verify signatures before side effects, persist a provider delivery/event idempotency key, make handlers replay-safe, and bound downstream retries/fan-out.",
            "low",
        ))

    for path, text in files:
        rpath = rel(path, root)
        if path.name in CONFIG_NAMES:
            continue

        # Obvious secret material. Evidence is redacted because scanner output often enters chat/CI logs.
        hit = line_for(text, SECRET_VALUE_RE)
        if hit:
            line_no, line = hit
            findings.append(Finding(
                "CFDOC-SEC-SECRET-VALUE",
                "critical",
                "Credential-shaped value appears in repository text",
                "security",
                f"{rpath}:{line_no}: {redacted_secret_line(line)}",
                "Committed credentials can lead to account compromise or data exposure. Cloudflare/API/R2/database credentials should never live in source.",
                "Rotate the credential, remove it from history if needed, move it to secrets storage, and add secret scanning.",
                "medium",
            ))
        for line_no, line in enumerate(text.splitlines(), 1):
            match = SECRET_ASSIGN_RE.search(line)
            if match and is_sensitive_assignment(match):
                findings.append(Finding(
                    "CFDOC-SEC-SECRET-ASSIGNMENT",
                    "high",
                    "Credential-like assignment appears in repository text",
                    "security",
                    f"{rpath}:{line_no}: {redacted_secret_line(line)}",
                    "Credentials in source, dotenv files, CI config, docs, or IaC can expose Cloudflare/API/database access and are often copied into deployments.",
                    "Rotate if real, move to Cloudflare secrets or CI secret storage, and keep only non-secret config in source.",
                    "medium",
                ))
                break

        is_source_like = path.suffix in CODE_EXTS or path.name in SPECIAL_SOURCE_NAMES
        if not is_source_like:
            continue

        if path.name == "_routes.json":
            try:
                routes_data = json.loads(strip_json_comments(text))
            except Exception:
                routes_data = {}
            includes = routes_data.get("include") if isinstance(routes_data, dict) else None
            excludes = routes_data.get("exclude") if isinstance(routes_data, dict) else None
            include_values = includes if isinstance(includes, list) else []
            exclude_values = excludes if isinstance(excludes, list) else []
            broad_include = any(str(v) in {"/*", "*", "/**"} for v in include_values)
            static_excluded = any(re.search(r"\.(?:css|js|mjs|png|jpe?g|gif|svg|webp|ico|woff2?)(?:\*|$)", str(v), re.I) for v in exclude_values)
            if broad_include and not static_excluded:
                findings.append(Finding(
                    "CFDOC-COST-PAGES-FUNCTION-ROUTES",
                    "medium",
                    "Pages _routes.json broadly invokes Functions without obvious static exclusions",
                    "cost footgun / missed optimization",
                    rpath,
                    "Broad Pages Function routing can send static asset traffic through Functions, increasing latency and billable invocations.",
                    "Exclude immutable/static asset paths in `_routes.json` or route only dynamic/API paths through Functions.",
                    "medium",
                ))

        # Expensive Cloudflare product patterns.
        ai_run_pattern = r"env\.(?:" + "|".join(re.escape(n) for n in sorted(ai_names)) + r")\.run\s*\("
        if re.search(ai_run_pattern, text):
            hit = line_for(text, ai_run_pattern) or (1, "")
            has_loop_or_retry = re.search(r"\b(for|while)\s*\(|retry|attempt|backoff|setTimeout|queue", text, re.I)
            has_idempotency = re.search(r"idempot|dedupe|cache|fingerprint|requestId|jobId", text, re.I)
            if has_loop_or_retry or not has_idempotency:
                findings.append(Finding(
                    "CFDOC-COST-AI-NO-IDEMPOTENCY",
                    "high" if has_loop_or_retry else "medium",
                    "Workers AI call lacks obvious idempotency/cache or is inside retry/loop-shaped code",
                    "cost footgun / reliability",
                    f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                    "Workers AI usage is metered separately from the Worker request. Loops, retries, Queue replays, or duplicate user actions can repeat paid inference/generation work.",
                    "Add an idempotency key and persistent result cache for each logical generation/embedding; bound retries and use AI Gateway/prompt caching where applicable.",
                    "medium",
                ))

        if vectorize_names:
            vector_pattern = r"env\.(?:" + "|".join(re.escape(n) for n in sorted(vectorize_names)) + r")\.query\s*\("
            hit = line_for(text, vector_pattern)
            if hit:
                findings.append(Finding(
                    "CFDOC-COST-VECTORIZE-DIMENSIONS",
                    "medium",
                    "Vectorize query path should account for queried dimensions and fan-out",
                    "cost footgun / missed optimization",
                    f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                    "Vectorize pricing can depend on queried and stored vector dimensions. High-dimensional indexes, large topK, namespace fan-out, or repeated embedding/query loops can hide cost behind one search call.",
                    "Verify index dimensions, topK, namespaces, embedding generation, and cache/dedupe strategy against current Vectorize pricing docs.",
                    "low",
                ))

        hit = line_for(text, re.compile(r"(/cdn-cgi/image/|cf\s*:\s*\{\s*image|\bimage\s*:\s*\{)", re.I | re.S))
        if hit:
            findings.append(Finding(
                "CFDOC-COST-MEDIA-VARIANT-EXPLOSION",
                "medium",
                "Image transformation path should bound variants and cache keys",
                "cost footgun / missed optimization",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "Cloudflare Images/Image Resizing transformations can multiply by width/height/format/DPR/quality variants. User-controlled variants can create unbounded transformed outputs and cache misses.",
                "Use predefined variants or strict allowlists, normalize transformation URLs/cache keys, and cache transformed outputs.",
                "medium",
            ))

        stream_linked = bool(
            re.search(r"(?:cloudflarestream\.com|videodelivery\.net|<stream|stream-player)", text, re.I)
            or any(re.search(r"\b" + re.escape(symbol) + r"\b", text) for symbol in stream_symbols)
        )
        if project_has_stream_host and stream_linked and re.search(r"preload\s*=\s*['\"]auto['\"]", text, re.I):
            hit = line_for(text, r"preload\s*=\s*['\"]auto['\"]") or (1, "")
            findings.append(Finding(
                "CFDOC-COST-MEDIA-VARIANT-EXPLOSION",
                "medium",
                "Stream player preloads video automatically",
                "cost footgun",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "Cloudflare Stream bills for delivered video minutes. Aggressive preload/autoplay can deliver video before a user intentionally watches, especially in feeds/background tabs.",
                "Use conservative preload settings for pay-sensitive embeds and measure delivered minutes by route/player.",
                "medium",
            ))

        if re.search(r"(puppeteer|playwright|Browser Run|env\.[A-Z0-9_]*BROWSER)", text, re.I) and re.search(r"(launch|connect|newPage|browser\()", text):
            if not re.search(r"\.close\s*\(", text):
                hit = line_for(text, re.compile(r"(puppeteer|playwright|Browser Run|env\.[A-Z0-9_]*BROWSER)", re.I)) or (1, "")
                findings.append(Finding(
                    "CFDOC-COST-BROWSER-NO-CLOSE",
                    "high",
                    "Browser Run session is opened without an obvious close path",
                    "cost footgun / reliability",
                    f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                    "Browser Run can be billed by browser/session time and concurrency. Sessions left open or retried blindly can dominate costs.",
                    "Close sessions/pages in `finally`, set timeouts/max retries, and prefer Quick Actions or non-browser primitives when sufficient.",
                    "medium",
                ))

        dynamic_loader_pattern = r"env\.(?:" + "|".join(re.escape(n) for n in sorted(dynamic_worker_names)) + r")\.(?:load|get)\s*\("
        hit = line_for(text, dynamic_loader_pattern)
        if hit:
            user_code_shaped = re.search(r"request\.|req\.|formData|json\s*\(\s*\)|prompt|code|source|script|llm|model", text, re.I)
            has_egress_policy = re.search(r"globalOutbound\s*:|egress|null|deny|allowlist|bindings\s*:", text, re.I)
            has_limits = re.search(r"limits\s*:|timeout|AbortController|max(?:Cpu|CPU|Requests|Duration|Unique|Depth|Steps)|budget|quota", text, re.I)
            if user_code_shaped and (not has_egress_policy or not has_limits):
                findings.append(Finding(
                    "DYNAMIC-WORKER-SANDBOX-CAPABILITIES",
                    "high",
                    "Dynamic Worker/code execution lacks obvious capability or resource bounds",
                    "security / cost footgun / reliability",
                    f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                    "Dynamic Workers can execute user- or LLM-provided code. If egress, bindings, secrets, custom limits, and audit logs are not explicit, sandboxed code can become a data-exfiltration or spend-amplification path.",
                    "Use deny-by-default egress/bindings, custom limits/timeouts, code hash auditing, bounded logs, and dedupe/reuse by stable IDs where safe.",
                    "medium",
                ))
            if ".load" in hit[1] and not re.search(r"\.get\s*\(|hash|digest|fingerprint|cache|dedupe|version", text, re.I):
                findings.append(Finding(
                    "CFDOC-COST-DYNAMIC-WORKER-DEDUPE",
                    "medium",
                    "Dynamic Worker load path lacks obvious stable ID/dedupe",
                    "cost footgun / missed optimization",
                    f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                    "Dynamic Worker cost and warm-isolate behavior can depend on requests, CPU time, and unique Dynamic Workers. Creating new workers for repeated identical work can hide cost behind a sandbox abstraction.",
                    "Use `loader.get()` or an equivalent stable code-hash/version key where reuse is safe, and emit per-run unique-worker/request/CPU proxies.",
                    "low",
                ))

        if re.search(r"\b(Agent|AIChatAgent|McpAgent|routeAgentRequest|getAgentByName|subAgent|startFiber|runFiber|scheduleTask|queueTask)\b", text):
            has_loop_or_tool = re.search(r"while\s*\(|for\s*\(|tool|browser|sandbox|subAgent|schedule|queueTask|retry|autonomous|continueLastTurn", text, re.I)
            has_agent_bounds = re.search(r"max(?:Steps|Iterations|Retries|Duration|Attempts)|AbortController|timeout|cancel|abort|idempot|backoff|jitter|budget|quota", text, re.I)
            if has_loop_or_tool and not has_agent_bounds:
                hit = line_for(text, re.compile(r"\b(Agent|AIChatAgent|McpAgent|subAgent|startFiber|runFiber|scheduleTask|queueTask)\b")) or (1, "")
                findings.append(Finding(
                    "AGENT-AUTONOMOUS-LOOP-COST",
                    "medium",
                    "Cloudflare Agent loop/tool path lacks obvious bounds or cancellation",
                    "cost footgun / reliability",
                    f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                    "Agents SDK workloads can combine Durable Object state, schedules, retries, tools, sub-agents, browser/sandbox sessions, and model calls. Autonomous loops without max steps and cancellation can repeat paid work.",
                    "Add max steps/attempts, cancellation, retry backoff, idempotency keys, and run summaries with model/tool/browser/sandbox cost proxies.",
                    "low",
                ))

        if artifacts_names:
            artifacts_pattern = r"env\.(?:" + "|".join(re.escape(n) for n in sorted(artifacts_names)) + r")\."
            hit = line_for(text, artifacts_pattern)
            if hit and not re.search(r"sign|signature|verify|rollback|token|namespace|tenant|environment|repo", text, re.I):
                findings.append(Finding(
                    "ARTIFACTS-UPDATE-SUPPLY-CHAIN",
                    "low",
                    "Artifacts-backed loader/update path needs token, signing, and rollback review",
                    "security / reliability / cost footgun",
                    f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                    "Artifacts can back app, repo, or firmware-like update flows. Without explicit token scope, namespace separation, signing, and rollback, a mutable artifact path can become a supply-chain or cleanup risk.",
                    "Verify repo/token scoping, signed artifact provenance, environment separation, lifecycle cleanup, and rollback/A-B update behavior.",
                    "low",
                ))

        hit = line_for(text, re.compile(r"\bconnect\s*\(.*(?:hostname|host|port)|from ['\"]cloudflare:sockets['\"]|node:net|\bnet\.Socket\b|createConnection\s*\(", re.I))
        if hit and not re.search(r"hyperdrive|pool|tls|secureTransport|timeout|AbortController|close\s*\(|end\s*\(|destroy\s*\(", text, re.I):
            findings.append(Finding(
                "WORKER-TCP-DB-FIT",
                "medium",
                "Worker TCP/external database path lacks obvious pooling/TLS/timeout controls",
                "reliability / cost footgun / security",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "Direct TCP/database connections from Workers can amplify connection churn, latency, and retry cost across edge locations if pooling, TLS, timeouts, and close/reuse semantics are unclear.",
                "Verify Hyperdrive/product fit for supported databases; otherwise add TLS, bounded concurrency, timeouts, retries with backoff, and explicit close/reuse behavior.",
                "low",
            ))

        hit = line_for(text, re.compile(r"Promise\.all\s*\([^\n;]*\.map\s*\(", re.I))
        if hit and not re.search(r"pLimit|limit|concurrency|batch|chunk|slice\s*\(|semaphore|queue", text, re.I):
            findings.append(Finding(
                "CFDOC-COST-UNBOUNDED-FANOUT",
                "medium",
                "Promise.all map fanout lacks an obvious concurrency cap",
                "cost footgun / reliability",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "Unbounded fanout can multiply Workers subrequests and downstream Cloudflare product usage in one user action or Queue job.",
                "Add max item counts, bounded concurrency, batching/backpressure, and per-tenant quotas; include fanout counts in run summaries.",
                "medium",
            ))

        retry_shaped = re.search(r"retry|retries|attempt|attempts|while\s*\(|for\s*\(", text, re.I)
        expensive_call = re.search(r"env\.[A-Za-z0-9_]+\.(run|query|send|sendBatch|put|list|prepare)\s*\(|fetch\s*\(|browser\.(launch|connect)|newPage\s*\(", text, re.I)
        has_resilience_controls = re.search(r"circuit|breaker|backoff|jitter|maxAttempts|max_retries|maxRetries|AbortController|timeout|killSwitch|disable|enabled", text, re.I)
        if retry_shaped and expensive_call and not has_resilience_controls:
            hit = line_for(text, re.compile(r"retry|retries|attempt|attempts|while\s*\(|for\s*\(", re.I)) or (1, "")
            findings.append(Finding(
                "CFDOC-COST-RETRY-AMPLIFY",
                "medium",
                "Retry/loop-shaped expensive path lacks obvious backoff or circuit breaker",
                "cost footgun / reliability",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "Hot retries into paid Cloudflare primitives or degraded dependencies can amplify spend and outages.",
                "Add bounded retries with exponential backoff/jitter, circuit breaker state, kill switch, and idempotency/result caching.",
                "low",
            ))

        # CORS wildcard + credentials in same file.
        if re.search(r"Access-Control-Allow-Origin['\"\s:,{]+\*", text) and re.search(r"Access-Control-Allow-Credentials['\"\s:,{]+true", text, re.I):
            hit = line_for(text, r"Access-Control-Allow-Origin") or (1, "")
            findings.append(Finding(
                "CFDOC-SEC-CORS-WILDCARD-CREDS",
                "high",
                "Wildcard CORS appears near credentialed responses",
                "security / misconfiguration",
                f"{rpath}:{hit[0]}: {hit[1][:160]}",
                "Credentialed browser requests cannot safely use arbitrary origins; sloppy CORS can expose APIs or break auth assumptions.",
                "Use an explicit origin allowlist and only enable credentials for trusted origins/routes.",
                "medium",
            ))

        # Trusting spoofable IP headers.
        hit = line_for(text, r"headers\.get\(['\"](x-forwarded-for|x-real-ip)['\"]\)")
        if hit:
            findings.append(Finding(
                "CFDOC-SEC-SPOOFABLE-IP-HEADER",
                "medium",
                "Code reads spoofable client-IP header",
                "security / best-practice drift",
                f"{rpath}:{hit[0]}: {hit[1][:160]}",
                "Client IP headers can be spoofed unless ingress is guaranteed through Cloudflare. Workers should prefer Cloudflare-provided request metadata/headers and account for trusted ingress.",
                "Use Cloudflare request metadata/`CF-Connecting-IP` only when direct origin bypass is impossible; enforce rate limiting before expensive work.",
                "medium",
            ))

        # KV list or counter/lock patterns.
        for name in kv_names:
            safe = re.escape(name)
            hit = line_for(text, rf"env\.{safe}\.list\s*\(")
            if hit:
                findings.append(Finding(
                    "CFDOC-COST-KV-LIST-HOTPATH",
                    "medium",
                    "KV list operation appears in application code",
                    "cost footgun / missed optimization",
                    f"{rpath}:{hit[0]}: {hit[1][:160]}",
                    "KV list/prefix scans in request paths can add latency and operation costs; KV is not a query engine.",
                    "If this is a hot path, keep a D1/KV manifest or cached index instead of listing per request.",
                    "medium",
                ))
            if re.search(rf"env\.{safe}\.get\s*\(", text) and re.search(rf"env\.{safe}\.put\s*\(", text) and re.search(r"counter|count|rate|limit|lock|nonce|inventory|balance", text, re.I):
                hit = line_for(text, rf"env\.{safe}\.(get|put)\s*\(") or (1, "")
                findings.append(Finding(
                    "CFDOC-FIT-KV-COORDINATION",
                    "high",
                    "KV read-modify-write smell for coordination/counters",
                    "wrong primitive / reliability",
                    f"{rpath}:{hit[0]}: {hit[1][:160]}",
                    "KV is eventually consistent and not a safe primitive for locks, counters, uniqueness, inventory, or rate-limit state that needs immediate correctness.",
                    "Use Durable Objects for per-key coordination/rate limits/counters, or D1 with constraints/transactions for relational state.",
                    "medium",
                ))

        # R2 list/buffering patterns.
        for name in r2_names:
            safe = re.escape(name)
            hit = line_for(text, rf"env\.{safe}\.list\s*\(")
            if hit:
                findings.append(Finding(
                    "CFDOC-COST-R2-LIST-HOTPATH",
                    "medium",
                    "R2 bucket list appears in application code",
                    "cost footgun / wrong primitive",
                    f"{rpath}:{hit[0]}: {hit[1][:160]}",
                    "R2 listing is a storage operation and a poor metadata query path at high request volume.",
                    "Maintain queryable metadata in D1/KV/search and cache list responses; use R2 for object bytes.",
                    "medium",
                ))
            if re.search(rf"env\.{safe}\.get\s*\(", text) and re.search(r"\.(arrayBuffer|text|json)\s*\(\s*\)", text):
                hit = line_for(text, rf"env\.{safe}\.get\s*\(") or (1, "")
                findings.append(Finding(
                    "CFDOC-PERF-R2-BUFFERING",
                    "medium",
                    "R2 object may be buffered instead of streamed",
                    "missed optimization / reliability",
                    f"{rpath}:{hit[0]}: {hit[1][:160]}",
                    "Buffering large R2 objects in a Worker increases memory/CPU pressure and delays first byte.",
                    "Return the R2 object's stream/body directly when possible and support range requests for large media/downloads.",
                    "low",
                ))

        # D1 query smells.
        if d1_names or ".prepare(" in text or ".batch(" in text:
            hit = line_for(text, re.compile(r"SELECT\s+\*", re.I))
            if hit:
                findings.append(Finding(
                    "CFDOC-PERF-D1-SELECT-STAR",
                    "low",
                    "D1 query uses SELECT *; review projection and bounds",
                    "missed optimization / schema coupling",
                    f"{rpath}:{hit[0]}: {hit[1][:160]}",
                    "SELECT * can widen transfer/decoding and couple callers to schema changes, but it does not by itself prove a full scan or increase D1 billed rows read; predicates, indexes, LIMIT, and the query plan determine rows scanned.",
                    "Select only needed columns where useful, and verify bounds/index use with EXPLAIN QUERY PLAN plus D1 rows_read metadata before making a billing claim.",
                    "medium",
                ))
            hit = line_for(text, re.compile(r"ORDER\s+BY\s+RANDOM\s*\(", re.I))
            if hit:
                findings.append(Finding(
                    "CFDOC-COST-D1-ORDER-RANDOM",
                    "high",
                    "D1 query orders by RANDOM()",
                    "cost footgun / missed optimization",
                    f"{rpath}:{hit[0]}: {hit[1][:160]}",
                    "Random ordering can force expensive scans/sorts and become costly or slow as the table grows.",
                    "Use indexed sampling, precomputed random keys, or a bounded candidate set.",
                    "high",
                ))
            if len(re.findall(r"\.prepare\s*\(", text)) >= 6:
                findings.append(Finding(
                    "CFDOC-PERF-D1-N-PLUS-ONE",
                    "low",
                    "Many D1 prepared statements in one file; check for N+1 queries",
                    "missed optimization / cost footgun",
                    rpath,
                    "Several sequential D1 queries on one request path can multiply latency and billed rows/operations.",
                    "Trace route-level query counts; batch, join, cache, or denormalize where appropriate.",
                    "low",
                ))

        # Durable Object / Workers RPC public-method reachability.
        rpc_boundary = re.search(r"\bclass\s+([A-Za-z_$][\w$]*)\s+extends\s+(?:[A-Za-z_$][\w$]*\.)?(DurableObject|WorkerEntrypoint|WorkflowEntrypoint|RpcTarget|Agent)\b", text)
        if rpc_boundary:
            runtime_hooks = {
                "constructor", "fetch", "scheduled", "queue", "tail", "trace", "email", "test",
                "alarm", "webSocketMessage", "webSocketClose", "webSocketError", "run",
                "onStart", "onConnect", "onMessage", "onClose", "onError", "onRequest",
                "onChatMessage", "onStateUpdate",
            }
            control_words = {"if", "for", "while", "switch", "catch", "function"}
            public_methods: list[str] = []
            method_rx = re.compile(
                r"^\s*(?!(?:private|protected|static)\b)(?:public\s+)?(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^;{}]*\)\s*(?::\s*[^;{]+)?\{",
                re.M,
            )
            for match in method_rx.finditer(text):
                name = match.group(1)
                if name not in runtime_hooks and name not in control_words and not name.startswith("_") and name not in public_methods:
                    public_methods.append(name)
            if public_methods:
                hit = line_for(text, re.compile(r"\bclass\s+" + re.escape(rpc_boundary.group(1)) + r"\s+extends\s+")) or (1, "")
                methods = ", ".join(public_methods[:5]) + ("…" if len(public_methods) > 5 else "")
                findings.append(Finding(
                    "CFDOC-REL-CROSS-BOUNDARY-RPC-DEAD",
                    "low",
                    "Cross-boundary public RPC methods need reachability review",
                    "reliability / security / maintainability",
                    f"{rpath}:{hit[0]}: {excerpt(hit[1])} (public methods: {methods})",
                    "Generic dead-code linters usually treat public methods on DurableObject, WorkerEntrypoint, WorkflowEntrypoint, RpcTarget, and Agent classes as live API surface. Stale RPC methods can accumulate as forgotten callable behavior, auth/schema bypass paths, or maintenance debt.",
                    "Optionally run a dead cross-boundary RPC analyzer such as `npx @acoyfellow/deadlint . --check dead-rpc --json` after explicit approval or from a pinned repo dependency; confirm dynamic/cross-repo callers before deleting methods.",
                    "low",
                ))

        # Durable Object hot spots, validation, lifecycle, storage, and hibernation smells.
        do_shaped = bool(re.search(r"DurableObject|durable_objects|idFrom(Name|String)\s*\(|acceptWebSocket|\.storage\.", text))
        if re.search(r"idFrom(Name|String)\s*\(|\.get\s*\([^\)]*\)\.fetch\s*\(", text):
            has_front_door_validation = re.search(r"auth|jwt|session|permission|tenant|validate|schema|zod|method|content-type|rate|turnstile|captcha", text, re.I)
            if not has_front_door_validation:
                hit = line_for(text, re.compile(r"idFrom(Name|String)\s*\(|\.get\s*\([^\)]*\)\.fetch\s*\(", re.I)) or (1, "")
                findings.append(Finding(
                    "CFDOC-COST-DO-FRONT-DOOR",
                    "medium",
                    "Durable Object call path lacks obvious front-door validation",
                    "cost footgun / security / reliability",
                    f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                    "Invalid, bot, oversized, or unauthenticated traffic should be rejected before it becomes Durable Object requests/duration or hot-spots a shard.",
                    "Validate method/auth/tenant/request size and apply rate limiting before constructing or calling DO stubs.",
                    "low",
                ))
        hit = line_for(text, re.compile(r"idFromName\s*\(\s*['\"](?:global|singleton|default|main|root|all|system|scheduler|broadcast|counter|idempotency)['\"]", re.I))
        if not hit:
            # Resolve bounded repo-visible constant/import/concatenation chains.
            ident = re.search(r"idFromName\s*\(\s*([A-Za-z_$][\w$]*)\s*\)", text)
            if ident and ident.group(1) in static_symbols:
                hit = line_for(text, re.compile(r"idFromName\s*\(\s*" + re.escape(ident.group(1)) + r"\s*\)"))
            else:
                hit = line_for(text, re.compile(r"idFromName\s*\(\s*env\.[A-Za-z0-9_]+\s*\)"))
        if hit:
            findings.append(Finding(
                "DO-SHARDING-HOTSPOT",
                "high",
                "Durable Object idFromName uses a global/singleton key",
                "wrong primitive / cost footgun / reliability",
                f"{rpath}:{hit[0]}: {hit[1][:160]}",
                "A low-cardinality Durable Object key can concentrate traffic into one object, causing hot-spot latency and duration/request amplification.",
                "Shard Durable Objects by tenant/user/room/resource key, or use D1/KV/R2 if coordination is not required.",
                "high",
            ))
        hit = line_for(text, re.compile(r"idFromName\s*\([^\)]*(idempot|requestId|request_id|eventId|event_id|messageId|message_id|nonce|randomUUID|Date\.now|crypto\.randomUUID)", re.I))
        if hit:
            findings.append(Finding(
                "DO-EPHEMERAL-IDEMPOTENCY-OBJECTS",
                "medium",
                "Durable Object key appears tied to an ephemeral id/request",
                "wrong primitive / cost footgun",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "One Durable Object per idempotency key, request ID, event ID, or nonce can create many mostly idle objects and storage cleanup work without much coordination benefit.",
                "Use bounded hash shards, time buckets with TTL cleanup, or KV/D1 for short-lived idempotency depending on consistency requirements.",
                "low",
            ))
        hit = line_for(text, re.compile(r"(?:this\.)?(?:ctx|state)\.storage\.list\s*\(|this\.storage\.list\s*\(", re.I))
        if hit:
            findings.append(Finding(
                "DO-STORAGE-LIST-HOTPATH",
                "medium",
                "Durable Object storage.list appears in code",
                "cost footgun / missed optimization",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "Durable Object storage list/prefix scans can be much more expensive and slower than fetching known keys when used on request or wake-up hot paths.",
                "Fetch known keys, compact related state into one object where safe, maintain a manifest, or cache loaded state intentionally.",
                "medium",
            ))
        if do_shaped:
            alarm_idx = re.search(r"\balarm\s*\([^)]*\)\s*(?::\s*[^\{=>]+)?\s*[\{=>]", text)
            alarm_window = text[alarm_idx.start():alarm_idx.start() + 1200] if alarm_idx else ""
            set_alarm = re.search(r"\bsetAlarm\s*\(", alarm_window, re.I)
            # Require guard terms inside an actual condition before rescheduling;
            # ordinary variables such as `nextRun` or `maxDelay` do not count.
            guard_prefix = alarm_window[:set_alarm.start()] if set_alarm else ""
            has_idle_guard = bool(re.search(
                r"\bif\s*\([^)]*(?:hasWork|pending|remaining|should|enabled|disabled|backoff|attempts?|maxAttempts?|next(?:Alarm|Run|Wake)|empty|queue|\.length|\.size)[^)]*\)",
                guard_prefix,
                re.I,
            ))
            if set_alarm and not has_idle_guard:
                hit = line_for(text, re.compile(r"\bsetAlarm\s*\(", re.I)) or (1, "")
                findings.append(Finding(
                    "DO-ALARM-RECURSION",
                    "medium",
                    "Alarm handler reschedules without obvious idle guard",
                    "cost footgun / reliability",
                    f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                    "A Durable Object alarm that always schedules another alarm can create recurring requests/duration even when no work remains.",
                    "Only set the next alarm when work remains; add max attempts/backoff, an idle stop condition, and a kill switch.",
                    "low",
                ))
            storage_puts = re.findall(r"(?:this\.)?(?:ctx|state)\.storage\.put\s*\(|this\.storage\.put\s*\(", text, re.I)
            put_in_loop = re.search(r"(?:for|while)\s*\([^)]*\)\s*{[^{}]{0,1000}(?:this\.)?(?:ctx|state|storage)\.?storage?\.put\s*\(", text, re.I | re.S)
            if len(storage_puts) >= 4 or put_in_loop:
                hit = line_for(text, re.compile(r"storage\.put\s*\(", re.I)) or (1, "")
                findings.append(Finding(
                    "DO-STORAGE-BATCHING",
                    "low",
                    "Multiple Durable Object storage.put calls need coalescing/transaction review",
                    "performance / cost review",
                    f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                    "Multiple writes may add latency or repeatedly rewrite the same logical state. Current Durable Objects pricing bills distinct keys/rows even when written with a multi-key API, so batching alone is not a proven billing reduction; backend and rows/units changed matter.",
                    "Coalesce redundant writes to the same logical state and use transaction/multi-key APIs for correctness or latency where appropriate; verify the storage backend and rows/units written before claiming savings.",
                    "low",
                ))
        if "WebSocketPair" in text and re.search(r"\.accept\s*\(\s*\)", text) and "acceptWebSocket" not in text:
            hit = line_for(text, r"\.accept\s*\(\s*\)") or (1, "")
            findings.append(Finding(
                "DO-WEBSOCKET-DURATION",
                "medium",
                "WebSocket handling may not use Durable Object hibernation",
                "cost footgun / missed optimization",
                f"{rpath}:{hit[0]}: {hit[1][:160]}",
                "Long-lived idle WebSockets can increase duration cost and reduce survivability if hibernation is not used where available.",
                "For Durable Object WebSockets, evaluate `ctx.acceptWebSocket` hibernation APIs and persistence model.",
                "low",
            ))
        if do_shaped and re.search(r"WebSocketPair|acceptWebSocket|\.accept\s*\(\s*\)", text) and not re.search(r"webSocketClose|webSocketError|addEventListener\s*\(\s*['\"]close|\.close\s*\(|clearTimeout|timeout|disconnect", text, re.I):
            hit = line_for(text, re.compile(r"WebSocketPair|acceptWebSocket|\.accept\s*\(\s*\)", re.I)) or (1, "")
            findings.append(Finding(
                "DO-SOCKET-CLOSE-HYGIENE",
                "medium",
                "WebSocket path lacks obvious close/error cleanup",
                "cost footgun / reliability",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "Durable Object WebSocket code without close/error/timeout cleanup can leave stale connection state and keep sessions alive longer than intended.",
                "Handle close/error callbacks, clear timers, remove connection state, and add idle timeouts/heartbeats where appropriate.",
                "low",
            ))
        if do_shaped and re.search(r"(?:event|ctx)\.waitUntil\s*\(", text, re.I):
            hit = line_for(text, re.compile(r"(?:event|ctx)\.waitUntil\s*\(", re.I)) or (1, "")
            severity = "medium" if "event.waitUntil" in hit[1] else "low"
            findings.append(Finding(
                "DO-WAITUNTIL-LIFECYCLE",
                severity,
                "Durable Object background work should be bounded and API-correct",
                "reliability / cost footgun",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "Background work in Durable Objects is a lifecycle and billing decision. The Worker entrypoint `event.waitUntil()` API is not the same as DO context APIs, and long work may need alarms, Queues, Workflows, or Agents durable execution.",
                "Verify the code uses the correct DO context API, has timeouts/retry visibility, and moves long or retryable work to a durable async primitive.",
                "low",
            ))
        if do_shaped and re.search(r"session|preference|prefs|config|cache|read[-_ ]?heavy|profile", text, re.I) and not re.search(r"WebSocketPair|acceptWebSocket|alarm\s*\(|lock|counter|rate|limit|coordination|serialize|transaction", text, re.I):
            hit = line_for(text, re.compile(r"\.storage\.(get|put)\s*\(", re.I)) or (1, "")
            findings.append(Finding(
                "KV-VS-DO-STORAGE-FIT",
                "low",
                "Durable Object storage used for possibly read-heavy data",
                "wrong primitive / cost footgun",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "Read-heavy, write-rare session/preference/config data may not need Durable Object coordination or duration costs if eventual consistency or SQL queries are acceptable.",
                "Recheck consistency and access pattern; compare KV, D1, R2, and DO storage with current docs before deciding.",
                "low",
            ))
        if do_shaped and re.search(r"Promise\.all\s*\([^\)]*(idFromName|idFromString|stub|\.fetch\s*\()", text, re.I | re.S) and not re.search(r"pLimit|limit|concurrency|batch|chunk|semaphore|backpressure|queue", text, re.I):
            hit = line_for(text, re.compile(r"Promise\.all", re.I)) or (1, "")
            findings.append(Finding(
                "DO-FANOUT-TAX",
                "medium",
                "Fan-out to Durable Objects lacks obvious backpressure",
                "cost footgun / reliability",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "One request or job that wakes many Durable Objects can concentrate latency, requests, and duration unless fan-out is capped and paced.",
                "Add concurrency limits, batch sizes, queues/backpressure, per-tenant quotas, and run summaries for DO calls/duration.",
                "low",
            ))

        # Cache/write hot path smells.
        hit = line_for(text, r"await\s+caches\.default\.put\s*\(")
        if hit:
            findings.append(Finding(
                "CFDOC-PERF-AWAITED-CACHE-PUT",
                "low",
                "Cache put awaited in request path",
                "missed optimization",
                f"{rpath}:{hit[0]}: {hit[1][:160]}",
                "Awaiting cache writes can add latency to the user response when the write does not need to complete first.",
                "Use `ctx.waitUntil(caches.default.put(...))` when correctness allows.",
                "medium",
            ))

        # Public service/origin fetch smells.
        hit = line_for(text, re.compile(r"fetch\s*\(\s*['\"]https://[^'\"]+\.(workers\.dev|pages\.dev|cloudflareworkers\.com)", re.I))
        if hit:
            findings.append(Finding(
                "CFDOC-PERF-PUBLIC-SERVICE-URL",
                "medium",
                "Public Cloudflare service URL fetch; consider service bindings",
                "missed optimization / security",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "Fetching another Cloudflare service through a public URL can add routing overhead and create avoidable auth/exposure ambiguity.",
                "Use service bindings for same-account Worker-to-Worker calls when applicable.",
                "medium",
            ))
        hit = line_for(text, re.compile(r"fetch\s*\(\s*['\"]https://[^'\"]+\.(vercel\.app|netlify\.app|railway\.app|onrender\.com|fly\.dev|herokuapp\.com|firebaseapp\.com|web\.app|supabase\.co)", re.I))
        if hit:
            findings.append(Finding(
                "CFDOC-COST-THIRD-PARTY-ORIGIN",
                "medium",
                "Worker fetches a public third-party/serverless origin hostname",
                "cost footgun / reliability / security",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "Cloudflare-fronted third-party origins can still bill on cache misses or direct default-hostname traffic. Public origin URLs may bypass Cloudflare WAF/cache/auth controls.",
                "Verify the origin is locked to Cloudflare or otherwise protected, cache safe responses before origin, and set origin-provider spend/scale controls.",
                "medium",
            ))
        queue_handler = line_for(text, re.compile(r"\basync\s+queue\s*\("))
        referenced_queues = set(re.findall(
            r"\b(?:batch|messages|messageBatch)\.(?:queue|queueName)\s*={2,3}\s*['\"]([^'\"]+)['\"]",
            text,
            re.I,
        ))
        missing_queue_config = sorted(referenced_queues - queue_consumer_names)
        if queue_handler and (not queue_consumer_names or missing_queue_config):
            detail = (
                "code-referenced queues missing config: " + ", ".join(missing_queue_config)
                if missing_queue_config else "no queue consumer config in repo"
            )
            findings.append(Finding(
                "CFDOC-REL-QUEUE-NO-DLQ",
                "medium",
                "Queue consumer handler without matching consumer config in repo",
                "misconfiguration / reliability / cost footgun",
                f"{rpath}:{queue_handler[0]}: {excerpt(queue_handler[1])} ({detail})",
                "A code-referenced Queue consumer is not matched by repository config, so retry and DLQ settings may be dashboard-managed or otherwise invisible. Cloudflare defaults to three retries and then deletes the message unless a DLQ is configured; the actual terminal policy is not inspectable here.",
                "Declare every consumer with intentional retry/delay/DLQ settings in Wrangler config, or supply the dashboard consumer settings as audit evidence; keep processing idempotent for at-least-once delivery.",
                "low",
            ))
        hit = line_for(text, re.compile(r"fetch\s*\(\s*(?:(?:request|req|event\.request)\.(?:url|clone\s*\(\s*\))|new\s+URL\s*\([^)]*,\s*(?:request|req|event\.request)\.url)", re.I))
        if not hit:
            self_url_vars = set(re.findall(
                r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:(?:request|req|event\.request)\.url|new\s+URL\s*\([^)]*,\s*(?:request|req|event\.request)\.url\s*\))",
                text,
                re.I,
            ))
            for _ in range(4):
                aliases = {
                    name for name, source in re.findall(
                        r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*([A-Za-z_$][\w$]*)\s*;?",
                        text,
                    ) if source in self_url_vars
                }
                if aliases <= self_url_vars:
                    break
                self_url_vars.update(aliases)
            if self_url_vars:
                hit = line_for(text, re.compile(
                    r"fetch\s*\(\s*(?:" + "|".join(re.escape(name) for name in sorted(self_url_vars)) + r")\b",
                    re.I,
                ))
        if hit:
            findings.append(Finding(
                "CFDOC-COST-ASYNC-LOOP",
                "medium",
                "Worker appears to fetch the incoming request URL",
                "cost footgun / reliability",
                f"{rpath}:{hit[0]}: {excerpt(hit[1])}",
                "Fetching the same URL/host handled by the Worker can create self-fetch loops, extra billable invocations, or Cloudflare 1019 loop errors depending on routing.",
                "Verify the target URL is an origin/service binding that cannot route back into this Worker; add tests and loop guards.",
                "low",
            ))

        # Node env assumptions.
        hit = line_for(text, r"process\.env\.[A-Za-z0-9_]+")
        if hit and path.suffix not in {".md"}:
            findings.append(Finding(
                "CFDOC-CONFIG-PROCESS-ENV",
                "low",
                "process.env reference in Worker-adjacent code",
                "misconfiguration / runtime compatibility",
                f"{rpath}:{hit[0]}: {hit[1][:160]}",
                "Workers receive environment bindings through the handler `env` object; `process.env` may be a build-time or Node-compat assumption.",
                "Confirm this code runs at build time or under intentional Node compatibility; otherwise use Worker bindings/secrets.",
                "low",
            ))

        # Terraform Cloudflare account smells.
        if path.suffix == ".tf":
            hit = line_for(text, re.compile(r"ssl\s*=\s*['\"]flexible['\"]", re.I))
            if hit:
                findings.append(Finding(
                    "CFDOC-SEC-TLS-FLEXIBLE",
                    "high",
                    "Terraform sets SSL/TLS mode to Flexible",
                    "security / misconfiguration",
                    f"{rpath}:{hit[0]}: {hit[1][:160]}",
                    "Flexible SSL leaves the Cloudflare-to-origin leg unencrypted and is usually inappropriate for production.",
                    "Use Full (strict) with a valid origin certificate unless a documented exception exists.",
                    "high",
                ))
            hit = line_for(text, re.compile(r"proxied\s*=\s*false", re.I))
            if hit:
                findings.append(Finding(
                    "CFDOC-SEC-DNS-UNPROXIED",
                    "medium",
                    "Terraform has unproxied DNS record; verify origin exposure",
                    "security / misconfiguration",
                    f"{rpath}:{hit[0]}: {hit[1][:160]}",
                    "Unproxied records bypass Cloudflare WAF/cache/Access protections and may expose origin infrastructure.",
                    "Confirm the record is intentionally DNS-only; otherwise enable proxying and restrict direct origin access.",
                    "medium",
                ))


def render(root: Path, configs: list[tuple[Path, str, dict[str, Any]]], bindings: dict[str, set[str]], findings: list[Finding], files_scanned: int) -> str:
    products = sorted(product for product, names in bindings.items() if names)
    config_paths = [rel(path, root) for path, _, _ in configs]
    out: list[str] = []
    out.append("# Cloudflare Doctor static scan")
    out.append("")
    out.append("This is a heuristic local scan. Confirm every finding with source context and current Cloudflare docs/pricing before treating it as true.")
    out.append("")
    out.append(f"- Scanner version: {SCANNER_VERSION}")
    out.append(f"- Root: `{root}`")
    out.append(f"- Files scanned: {files_scanned}")
    out.append(f"- Wrangler configs: {', '.join(config_paths) if config_paths else 'none detected'}")
    out.append(f"- Detected products/bindings: {', '.join(products) if products else 'none detected from parsed config'}")
    if products:
        for product in products:
            names = ", ".join(sorted(bindings[product])) or "(names not parsed)"
            out.append(f"  - {product}: {names}")
    out.append("")

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings_sorted = sorted(findings, key=lambda f: (severity_order.get(f.severity, 9), f.title, f.evidence))
    out.append(f"## Findings ({len(findings_sorted)})")
    if not findings_sorted:
        out.append("")
        out.append("No scanner findings. This does not mean the project is healthy; account/dashboard settings and access patterns still need audit.")
        return "\n".join(out) + "\n"

    for finding in findings_sorted:
        out.append("")
        out.append(f"### [{finding.check_id}] {finding.severity.capitalize()}: {finding.title}")
        out.append(f"- Category: {finding.category}")
        out.append(f"- Evidence: {finding.evidence}")
        out.append(f"- Why it matters: {finding.why}")
        out.append(f"- Fix: {finding.fix}")
        out.append(f"- Confidence: {finding.confidence}")
    out.append("")
    return "\n".join(out)


def split_evidence(evidence: str) -> tuple[str, int | None, str]:
    match = re.match(r"^(.*?):(\d+):\s?(.*)$", evidence)
    if match:
        return match.group(1), int(match.group(2)), match.group(3)
    head, _, rest = evidence.partition(": ")
    return re.sub(r"\s*\[env\.[^\]]*\]$", "", head), None, rest


def render_json(root: Path, bindings: dict[str, set[str]], findings: list[Finding]) -> str:
    products = sorted(product for product, names in bindings.items() if names)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings_sorted = sorted(findings, key=lambda f: (severity_order.get(f.severity, 9), f.check_id, f.evidence))
    items = []
    for finding in findings_sorted:
        path, line, exc = split_evidence(finding.evidence)
        items.append({
            "check_id": finding.check_id,
            "title": finding.title,
            "severity": finding.severity,
            "confidence": finding.confidence,
            "category": finding.category,
            "path": path,
            "line": line,
            "evidence": finding.evidence,
            "message": finding.why,
            "fix": finding.fix,
            "excerpt": exc,
        })
    counts: dict[str, int] = {"total": len(findings_sorted)}
    for sev in ("critical", "high", "medium", "low"):
        counts[sev] = sum(1 for f in findings_sorted if f.severity == sev)
    doc = {
        "scanner_version": SCANNER_VERSION,
        "scanned_root": str(root),
        "detected_products": products,
        "findings": items,
        "counts": counts,
    }
    return json.dumps(doc, indent=2, sort_keys=True)


def render_check_list() -> str:
    doc = {
        "scanner_version": SCANNER_VERSION,
        "checks": [{"check_id": cid, **CHECKS[cid]} for cid in sorted(CHECKS)],
    }
    return json.dumps(doc, indent=2, sort_keys=True)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Heuristic static scan for Cloudflare projects")
    parser.add_argument("root", nargs="?", default=".", help="Project root to scan")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report instead of the human report")
    parser.add_argument("--list-checks", action="store_true", help="Print the check registry as JSON and exit")
    parser.add_argument("--exclude", action="append", default=[], metavar="REL_PATH", help="Skip files whose root-relative POSIX path starts with this prefix (repeatable)")
    args = parser.parse_args(argv)

    if args.list_checks:
        print(render_check_list())
        return 0

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"error: root does not exist: {root}", file=sys.stderr)
        return 2

    excludes = [e[2:] if e.startswith("./") else e for e in args.exclude]
    file_texts: list[tuple[Path, str]] = []
    configs: list[tuple[Path, str, dict[str, Any]]] = []
    parse_errors: list[tuple[Path, str]] = []
    for path in iter_files(root):
        if excludes and any(Path(rel(path, root)).as_posix().startswith(e) for e in excludes):
            continue
        text = read_text(path)
        file_texts.append((path, text))
        if path.name in CONFIG_NAMES:
            try:
                configs.append((path, text, parse_config(path, text)))
            except ConfigParseError as exc:
                parse_errors.append((path, str(exc)))

    bindings = collect_bindings(configs)
    findings: list[Finding] = []
    add_config_findings(root, configs, findings, parse_errors)
    queue_consumer_names: set[str] = set()
    pending_configs = [data for _, _, data in configs if data]
    while pending_configs:
        data = pending_configs.pop()
        for consumer in queue_consumers(data):
            name = consumer.get("queue") or consumer.get("name")
            if isinstance(name, str) and name.strip():
                queue_consumer_names.add(name.strip())
        envs = data.get("env")
        if isinstance(envs, dict):
            pending_configs.extend(value for value in envs.values() if isinstance(value, dict))
    add_code_findings(root, file_texts, bindings, findings, queue_consumer_names=queue_consumer_names)
    if args.json:
        print(render_json(root, bindings, findings))
    else:
        print(render(root, configs, bindings, findings, len(file_texts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
