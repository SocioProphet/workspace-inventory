#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "exports" / "canonical-repo-estate.v1.0.csv"
MANIFEST = ROOT / "exports" / "canonical-repo-estate.v1.0.json"
EXPECTED_REPO_COUNT = 125
EXPECTED_STATUS = "canonical-export"
EXPECTED_ARTIFACT_ID = "workspace_inventory.canonical_repo_estate.v1.0"
REQUIRED_COLUMNS = [
    "repo_full_name",
    "owned_services",
    "supporting_services",
    "contract_services",
    "canonical_status",
]


def fail(message: str) -> int:
    print(f"ERR: {message}")
    return 2


def main() -> int:
    if not EXPORT.exists():
        return fail(f"missing export: {EXPORT.relative_to(ROOT)}")
    if not MANIFEST.exists():
        return fail(f"missing manifest: {MANIFEST.relative_to(ROOT)}")

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail(f"invalid manifest JSON: {exc}")

    if manifest.get("artifact_id") != EXPECTED_ARTIFACT_ID:
        return fail(f"unexpected artifact_id: {manifest.get('artifact_id')!r}")
    if manifest.get("status") != EXPECTED_STATUS:
        return fail(f"unexpected status: {manifest.get('status')!r}")
    if manifest.get("export_path") != "exports/canonical-repo-estate.v1.0.csv":
        return fail(f"unexpected export_path: {manifest.get('export_path')!r}")
    if manifest.get("repo_count") != EXPECTED_REPO_COUNT:
        return fail(f"manifest repo_count {manifest.get('repo_count')!r} != {EXPECTED_REPO_COUNT}")

    with EXPORT.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REQUIRED_COLUMNS:
            return fail(f"unexpected columns: {reader.fieldnames!r}")
        rows = list(reader)

    if len(rows) != EXPECTED_REPO_COUNT:
        return fail(f"export row count {len(rows)} != {EXPECTED_REPO_COUNT}")

    seen: set[str] = set()
    for index, row in enumerate(rows, start=2):
        repo = row.get("repo_full_name", "").strip()
        if not repo or "/" not in repo:
            return fail(f"row {index} invalid repo_full_name: {repo!r}")
        if repo in seen:
            return fail(f"duplicate repo_full_name: {repo}")
        seen.add(repo)
        if row.get("canonical_status") != "primary":
            return fail(f"row {index} unexpected canonical_status: {row.get('canonical_status')!r}")

    print(f"OK: canonical repo estate export valid ({len(rows)} repos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
