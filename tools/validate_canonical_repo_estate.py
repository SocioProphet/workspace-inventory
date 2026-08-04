#!/usr/bin/env python3
"""Validate the canonical repo estate export."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "exports" / "canonical-repo-estate.v1.0.csv"
MANIFEST_PATH = ROOT / "exports" / "canonical-repo-estate.v1.0.json"
EXPECTED_REPO_COUNT = 121


def main() -> int:
    if not CSV_PATH.exists():
        print(f"ERROR: missing {CSV_PATH.relative_to(ROOT)}")
        return 1
    if not MANIFEST_PATH.exists():
        print(f"ERROR: missing {MANIFEST_PATH.relative_to(ROOT)}")
        return 1

    rows = list(csv.DictReader(CSV_PATH.open(newline="", encoding="utf-8")))
    if len(rows) != EXPECTED_REPO_COUNT:
        print(f"ERROR: repo count {len(rows)} != expected {EXPECTED_REPO_COUNT}")
        return 1

    repos = [row.get("repo_full_name", "").strip() for row in rows]
    if any(not repo or "/" not in repo for repo in repos):
        print("ERROR: every row must have repo_full_name in owner/name form")
        return 1
    duplicates = sorted({repo for repo in repos if repos.count(repo) > 1})
    if duplicates:
        print(f"ERROR: duplicate repos: {duplicates}")
        return 1

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("repo_count") != EXPECTED_REPO_COUNT:
        print(f"ERROR: manifest repo_count {manifest.get('repo_count')} != expected {EXPECTED_REPO_COUNT}")
        return 1
    if manifest.get("export_path") != "exports/canonical-repo-estate.v1.0.csv":
        print("ERROR: manifest export_path does not point to stable CSV export")
        return 1

    print(f"OK: canonical repo estate export rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
