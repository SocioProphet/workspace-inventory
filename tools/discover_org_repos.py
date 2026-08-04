#!/usr/bin/env python3
"""Discover SocioProphet org repositories absent from the curated inventory.

Repository registration in this repo is fully manual/curated: `inventory/repos.yaml`
plus the canonical `exports/canonical-repo-estate.v1.0.csv` export are hand-maintained,
and nothing reconciles them against the live GitHub org. This tool closes that gap by
listing the live org repositories and diffing them against the curated inventory so
repos present in the org but absent from the inventory can be triaged (curated in, or
explicitly excluded via the discovery allowlist).

The tool is importable: the pure diff logic (`find_untriaged`) takes plain data so it
can be exercised with fake org listings and a fake inventory. Only `fetch_org_repos`
shells out to `gh`.

Exit codes:
    0  no un-triaged repos (or gh unavailable/unconfigured and no injected listing:
       skip-clean rather than fail-red)
    1  one or more un-triaged repos need triage
    2  usage/structure error
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # pyyaml
except Exception:  # pragma: no cover - dependency guard mirrors validate_inventory.py
    print("ERR: missing dependency pyyaml (pip install pyyaml)", file=sys.stderr)
    raise

DEFAULT_ORG = "SocioProphet"
# The SocioProphet org holds ~1.5k repos (mostly forks), so the discovery listing
# limit is set well above the true count; `gh repo list --limit 700` would silently
# truncate. `listing_possibly_truncated` stays as a dead-man's guard if the org grows
# past this ceiling.
DEFAULT_LIMIT = 2000
ROOT = Path(__file__).resolve().parents[1]
REPOS_YAML = ROOT / "inventory" / "repos.yaml"
CANONICAL_CSV = ROOT / "exports" / "canonical-repo-estate.v1.0.csv"
CANONICAL_MANIFEST = ROOT / "exports" / "canonical-repo-estate.v1.0.json"
DEFAULT_ALLOWLIST = ROOT / "inventory" / "discovery-allowlist.yaml"


def _short_name(full_or_name: str, org: str) -> str:
    """Return the bare repo name for either 'name' or 'org/name' (org-scoped only)."""
    owner, sep, name = full_or_name.partition("/")
    if not sep:
        return full_or_name.strip()
    return name.strip() if owner.strip() == org else ""


def load_curated_names(
    org: str,
    repos_yaml: Path | None = None,
    canonical_csv: Path | None = None,
    canonical_manifest: Path | None = None,
) -> set[str]:
    """Collect every org-scoped repo name the curated inventory already knows about.

    Sources (all treated as "triaged"):
      * inventory/repos.yaml entries whose effective org is `org`
      * canonical CSV rows owned by `org`
      * manifest removed_from_go_forward / consolidation_candidates owned by `org`
        (explicitly decided repos are triaged, not gaps)

    Path arguments default (when None) to the module-level canonical locations,
    resolved at call time so callers/tests can redirect them.
    """
    repos_yaml = repos_yaml if repos_yaml is not None else REPOS_YAML
    canonical_csv = canonical_csv if canonical_csv is not None else CANONICAL_CSV
    canonical_manifest = canonical_manifest if canonical_manifest is not None else CANONICAL_MANIFEST

    names: set[str] = set()

    if repos_yaml.exists():
        data = yaml.safe_load(repos_yaml.read_text(encoding="utf-8")) or {}
        default_org = str(data.get("org", org))
        for entry in data.get("repos", []) or []:
            if not isinstance(entry, dict):
                continue
            entry_org = str(entry.get("org", default_org))
            name = str(entry.get("name", "")).strip()
            if name and entry_org == org:
                names.add(name)

    if canonical_csv.exists():
        with canonical_csv.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                name = _short_name(row.get("repo_full_name", ""), org)
                if name:
                    names.add(name)

    if canonical_manifest.exists():
        manifest = json.loads(canonical_manifest.read_text(encoding="utf-8"))
        for key in ("removed_from_go_forward", "consolidation_candidates"):
            for full in manifest.get(key, []) or []:
                name = _short_name(str(full), org)
                if name:
                    names.add(name)

    return names


def load_allowlist(path: Path = DEFAULT_ALLOWLIST, org: str = DEFAULT_ORG) -> set[str]:
    """Load explicitly-excluded repo names from the discovery allowlist file.

    Missing file is treated as an empty allowlist (skip-clean, not an error).
    Entries may be either bare names or 'org/name'; each item is either a string
    or a mapping with a `name`/`repo` key (plus a human `reason`).
    """
    if not path.exists():
        return set()
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    names: set[str] = set()
    for item in doc.get("allowlist", []) or []:
        if isinstance(item, str):
            raw = item
        elif isinstance(item, dict):
            raw = str(item.get("name") or item.get("repo") or "")
        else:
            continue
        name = _short_name(raw, org)
        if name:
            names.add(name)
    return names


def fetch_org_repos(org: str, limit: int = DEFAULT_LIMIT) -> list[dict[str, Any]]:
    """List org repos via `gh repo list`. Raises RuntimeError if gh is unavailable."""
    if shutil.which("gh") is None:
        raise RuntimeError("gh CLI not found on PATH")
    cmd = [
        "gh", "repo", "list", org,
        "--limit", str(limit),
        "--json", "name,url,isArchived,isFork",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"gh repo list failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout or "[]")


def find_untriaged(
    org_repos: list[dict[str, Any]],
    curated: set[str],
    allowlist: set[str],
) -> list[dict[str, Any]]:
    """Pure diff: org repos that are not archived, not forks, not curated, not allowlisted.

    Returns a sorted list of {name, url} dicts. Deterministic and side-effect free so it
    can be exercised with fabricated inputs.
    """
    excluded = curated | allowlist
    untriaged: list[dict[str, Any]] = []
    for repo in org_repos:
        name = str(repo.get("name", "")).strip()
        if not name:
            continue
        if repo.get("isArchived") or repo.get("isFork"):
            continue
        if name in excluded:
            continue
        untriaged.append({"name": name, "url": repo.get("url", "")})
    untriaged.sort(key=lambda r: r["name"].lower())
    return untriaged


def render_backlog(org: str, untriaged: list[dict[str, Any]], truncated: bool) -> str:
    """Render the machine-owned triage backlog YAML document."""
    doc = {
        "discovery_backlog_version": 1,
        "org": org,
        "generated_by": "tools/discover_org_repos.py",
        "note": (
            "Machine-owned. Repos present in the GitHub org but absent from the curated "
            "inventory (repos.yaml + canonical CSV + manifest). Triage each: curate into "
            "inventory/repos.yaml (+ canonical export) or exclude via "
            "inventory/discovery-allowlist.yaml. Do not hand-edit; refreshed by "
            ".github/workflows/repo-discovery.yml."
        ),
        "listing_possibly_truncated": truncated,
        "untriaged_count": len(untriaged),
        "untriaged": untriaged,
    }
    return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False, allow_unicode=True)


def build_report(
    org: str,
    org_repos: list[dict[str, Any]],
    untriaged: list[dict[str, Any]],
    limit: int,
) -> dict[str, Any]:
    truncated = len(org_repos) >= limit
    active = [r for r in org_repos if not r.get("isArchived") and not r.get("isFork")]
    return {
        "org": org,
        "org_repo_total": len(org_repos),
        "active_non_fork": len(active),
        "listing_possibly_truncated": truncated,
        "untriaged_count": len(untriaged),
        "untriaged": untriaged,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--org", default=DEFAULT_ORG, help=f"GitHub org (default: {DEFAULT_ORG})")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"gh repo list limit (default: {DEFAULT_LIMIT})")
    parser.add_argument("--json", action="store_true", help="emit the report as JSON on stdout")
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST, help="discovery allowlist YAML path")
    parser.add_argument(
        "--org-repos-json",
        type=Path,
        default=None,
        help="read the org listing from this gh-shaped JSON file instead of calling gh",
    )
    parser.add_argument(
        "--backlog",
        type=Path,
        default=None,
        help="write the machine-owned triage backlog YAML to this path",
    )
    args = parser.parse_args(argv)

    if args.org_repos_json is not None:
        try:
            org_repos = json.loads(args.org_repos_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERR: could not read --org-repos-json {args.org_repos_json}: {exc}", file=sys.stderr)
            return 2
    else:
        try:
            org_repos = fetch_org_repos(args.org, args.limit)
        except RuntimeError as exc:
            # Unconfigured/unavailable gh: skip-clean rather than fail-red.
            print(f"SKIP: org discovery unavailable ({exc}); no listing to diff", file=sys.stderr)
            return 0

    curated = load_curated_names(args.org)
    allowlist = load_allowlist(args.allowlist, args.org)
    untriaged = find_untriaged(org_repos, curated, allowlist)
    report = build_report(args.org, org_repos, untriaged, args.limit)

    if args.backlog is not None:
        args.backlog.write_text(render_backlog(args.org, untriaged, report["listing_possibly_truncated"]), encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(
            f"org={report['org']} total={report['org_repo_total']} "
            f"active_non_fork={report['active_non_fork']} untriaged={report['untriaged_count']}"
        )
        if report["listing_possibly_truncated"]:
            print(f"WARN: org listing hit --limit {args.limit}; results may be truncated", file=sys.stderr)
        for repo in untriaged:
            print(f"  UNTRIAGED {args.org}/{repo['name']}  {repo['url']}")

    if untriaged:
        if not args.json:
            print(
                f"ERR: {len(untriaged)} org repo(s) absent from curated inventory need triage",
                file=sys.stderr,
            )
        return 1

    if not args.json:
        print("OK: every active non-fork org repo is present in the curated inventory or allowlist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
