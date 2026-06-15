#!/usr/bin/env python3
"""Link checker for cfdoctor citation URLs.

Extracts unique http(s) URLs from markdown files in README.md, skills/cloudflare-doctor/references/,
research/, docs/, and evals/ (recursive), checks each one over the network,
and classifies the result:

  ok                      2xx response, no redirect
  redirect-ok             2xx response after following one or more redirects
  unverifiable-automated  403/999 from domains known to block automated
                          clients (medium.com, reddit.com, old.reddit.com,
                          news.ycombinator.com, linkedin.com) -- these are
                          reported as "check manually", NOT as dead
  dead                    404/410, or DNS resolution failure
  error                   timeout, 5xx, TLS/connection failures, or other
                          unexpected statuses (e.g. 403 from a non-allowlisted
                          domain, 429) -- inconclusive, not proven dead

Checking strategy: HEAD first, falling back to GET on 405/403/501 (many
servers reject HEAD); redirects are followed; a browser-like User-Agent is
sent (many sites 403 the default python-urllib agent); 15s timeout per
request; concurrency capped at 8 workers; no retries, so we never hammer a
slow or struggling host.

CI policy: this script ALWAYS exits 0 by default, even when dead links are
found, because link checking depends on third-party network availability and
must never hard-fail CI on transient network flakiness. Pass --strict to exit
1 when at least one link is classified dead (404/410/DNS failure only --
timeouts and 5xx still do not fail strict mode).

Usage:
  python3 scripts/check_links.py [--root DIR] [--json PATH] [--strict]

Stdlib only (urllib.request, concurrent.futures).
"""

import argparse
import concurrent.futures
import datetime
import json
import re
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_TARGETS = ["README.md", "references", "research", "docs", "evals"]

# Domains that systematically 403/999 automated clients. A 403/999 from these
# means "cannot verify automatically", not "dead".
BOT_BLOCK_DOMAINS = {
    "medium.com",
    "reddit.com",
    "old.reddit.com",
    "news.ycombinator.com",
    "linkedin.com",
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

TIMEOUT = 15
MAX_WORKERS = 8

URL_RE = re.compile(r"https?://[^\s<>\"'`\\\)\]]+")

# Trailing characters that are almost always punctuation/markdown, not URL.
STRIP_TRAILING = ".,;:!?*_~"


def clean_url(url: str) -> str:
    """Strip trailing punctuation and markdown artifacts from a raw match."""
    while url and url[-1] in STRIP_TRAILING:
        url = url[:-1]
    # Balance parentheses: regex excludes ')' so closing parens inside URLs
    # (rare) are already cut; nothing further needed, but guard against a
    # stray trailing '(' from malformed markdown.
    while url.endswith("("):
        url = url[:-1]
    return url


def extract_urls(root: Path, targets) -> dict:
    """Return {url: [files containing it]} for unique cleaned URLs."""
    found = {}
    md_files = []
    for target in targets:
        path = root / target
        if path.is_file():
            md_files.append(path)
        elif path.is_dir():
            md_files.extend(sorted(path.rglob("*.md")))
    for md in md_files:
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(md.relative_to(root))
        for match in URL_RE.finditer(text):
            url = clean_url(match.group(0))
            if not url or "://" not in url:
                continue
            found.setdefault(url, [])
            if rel not in found[url]:
                found[url].append(rel)
    return found


def domain_of(url: str) -> str:
    host = urllib.parse.urlsplit(url).hostname or ""
    return host.lower()


def is_bot_block_domain(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in BOT_BLOCK_DOMAINS)


class _RedirectTracker(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.redirected = False

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirected = True
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _request(url: str, method: str):
    """Issue one request. Returns (status, final_url, redirected)."""
    tracker = _RedirectTracker()
    ctx = ssl.create_default_context()
    opener = urllib.request.build_opener(
        tracker, urllib.request.HTTPSHandler(context=ctx)
    )
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    resp = opener.open(req, timeout=TIMEOUT)
    try:
        status = resp.status
        final_url = resp.geturl()
    finally:
        resp.close()
    return status, final_url, tracker.redirected


def check_url(url: str) -> dict:
    """Check a single URL and return a result record."""
    host = domain_of(url)
    result = {
        "url": url,
        "status": None,
        "final_url": None,
        "classification": "error",
        "detail": "",
    }

    last_error = None
    for method in ("HEAD", "GET"):
        try:
            status, final_url, redirected = _request(url, method)
            result["status"] = status
            result["final_url"] = final_url
            if 200 <= status < 300:
                result["classification"] = (
                    "redirect-ok" if redirected or final_url != url else "ok"
                )
                result["detail"] = f"{method} {status}"
            else:
                result["detail"] = f"{method} {status}"
            return result
        except urllib.error.HTTPError as exc:
            code = exc.code
            exc.close()
            result["status"] = code
            result["detail"] = f"{method} {code}"
            if method == "HEAD" and code in (405, 403, 501):
                last_error = code
                continue  # retry once with GET
            if code in (404, 410):
                result["classification"] = "dead"
            elif code in (403, 999, 401, 429) and is_bot_block_domain(host):
                result["classification"] = "unverifiable-automated"
                result["detail"] += " (bot-blocked domain; check manually)"
            else:
                result["classification"] = "error"
            return result
        except urllib.error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, socket.gaierror):
                result["classification"] = "dead"
                result["detail"] = f"DNS failure: {reason}"
            elif isinstance(reason, (socket.timeout, TimeoutError)):
                result["classification"] = "error"
                result["detail"] = "timeout"
            else:
                result["classification"] = "error"
                result["detail"] = f"connection error: {reason}"
            return result
        except (socket.timeout, TimeoutError):
            result["classification"] = "error"
            result["detail"] = "timeout"
            return result
        except Exception as exc:  # noqa: BLE001 - report, never crash a worker
            result["classification"] = "error"
            result["detail"] = f"{type(exc).__name__}: {exc}"
            return result

    # HEAD got 405/403/501 and GET loop somehow did not return (defensive).
    if last_error in (403, 999) and is_bot_block_domain(host):
        result["classification"] = "unverifiable-automated"
    return result


ORDER = ["ok", "redirect-ok", "unverifiable-automated", "dead", "error"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Check citation URLs in cfdoctor markdown files."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root (default: parent of scripts/).",
    )
    parser.add_argument("--json", type=Path, help="Write JSON report to PATH.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if at least one dead link is found (default: always 0).",
    )
    args = parser.parse_args(argv)

    urls = extract_urls(args.root, DEFAULT_TARGETS)
    print(f"Checking {len(urls)} unique URLs from markdown files...\n")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(check_url, u): u for u in sorted(urls)}
        for fut in concurrent.futures.as_completed(futures):
            rec = fut.result()
            rec["files"] = urls[rec["url"]]
            results.append(rec)

    results.sort(key=lambda r: r["url"])
    by_class = {c: [r for r in results if r["classification"] == c] for c in ORDER}

    for cls in ORDER:
        group = by_class[cls]
        print(f"== {cls} ({len(group)}) ==")
        if cls == "ok":
            print("  (2xx, listed count only)")
        else:
            for rec in group:
                print(f"  {rec['url']}  [{rec['detail']}]")
                if cls in ("dead", "error", "unverifiable-automated"):
                    for f in rec["files"]:
                        print(f"      cited in: {f}")
        print()

    print("Summary:", ", ".join(f"{cls}={len(by_class[cls])}" for cls in ORDER))

    if args.json:
        report = {
            "checked_at": datetime.datetime.now()
            .astimezone()
            .isoformat(timespec="seconds"),
            "total": len(results),
            "counts": {cls: len(by_class[cls]) for cls in ORDER},
            "results": results,
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8"
        )
        print(f"JSON report written to {args.json}")

    if args.strict and by_class["dead"]:
        print(f"--strict: {len(by_class['dead'])} dead link(s) found", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
