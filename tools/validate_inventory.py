#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys, json

try:
    import yaml  # pyyaml
except Exception as e:
    print("ERR: missing dependency pyyaml (pip install pyyaml)", file=sys.stderr)
    raise

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    inv = root / "inventory" / "repos.yaml"
    schema = root / "inventory" / "schema.json"
    if not inv.exists():
        print("ERR: missing inventory/repos.yaml", file=sys.stderr)
        return 2
    if not schema.exists():
        print("ERR: missing inventory/schema.json", file=sys.stderr)
        return 2

    data = yaml.safe_load(inv.read_text(encoding="utf-8"))
    # minimal structural checks without jsonschema dependency
    for k in ["workspace_inventory_version", "org", "repos"]:
        if k not in data:
            print(f"ERR: inventory missing key: {k}", file=sys.stderr)
            return 2

    if not isinstance(data["repos"], list) or not data["repos"]:
        print("ERR: repos must be a non-empty list", file=sys.stderr)
        return 2

    bad = 0
    for r in data["repos"]:
        for k in ["name","kind","manifest"]:
            if k not in r:
                print(f"ERR: repo entry missing {k}: {r}", file=sys.stderr)
                bad += 1

    if bad:
        return 2

    print("OK: inventory structure valid")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
