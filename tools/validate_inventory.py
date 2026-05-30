#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

try:
    import yaml  # pyyaml
except Exception:
    print("ERR: missing dependency pyyaml (pip install pyyaml)", file=sys.stderr)
    raise

REPO_STATUSES = {"active", "candidate", "held", "deprecated"}
DOCTRINE_STATES = {"none", "draft", "provisional", "admitted", "superseded", "deprecated"}
VALIDATION_STATES = {"unknown", "none", "local", "ci", "release_gate"}
ADOPTION_STATES = {"none", "planned", "partial", "active", "mature", "deprecated"}
DRIFT_RISKS = {"low", "medium", "high", "unknown"}
RECOVERY_DISPOSITIONS = {
    "owner_repo_assigned",
    "archive_only",
    "frozen_with_return_condition",
    "intentionally_not_pursued",
    "blocked",
    "superseded",
}


def expect_mapping(value: object, label: str) -> bool:
    if isinstance(value, dict):
        return True
    print(f"ERR: {label} must be a mapping/object", file=sys.stderr)
    return False


def expect_list(value: object, label: str) -> bool:
    if isinstance(value, list):
        return True
    print(f"ERR: {label} must be a list", file=sys.stderr)
    return False


def check_enum(value: object, allowed: set[str], label: str) -> bool:
    if value is None:
        return True
    if value in allowed:
        return True
    print(f"ERR: {label} has invalid value {value!r}; allowed={sorted(allowed)}", file=sys.stderr)
    return False


def check_estate(repo_name: str, estate: object) -> int:
    if not expect_mapping(estate, f"{repo_name}.estate"):
        return 1
    assert isinstance(estate, dict)
    bad = 0
    bad += not check_enum(estate.get("doctrine_state"), DOCTRINE_STATES, f"{repo_name}.estate.doctrine_state")
    bad += not check_enum(estate.get("validation_state"), VALIDATION_STATES, f"{repo_name}.estate.validation_state")
    bad += not check_enum(estate.get("adoption_state"), ADOPTION_STATES, f"{repo_name}.estate.adoption_state")
    bad += not check_enum(estate.get("drift_risk"), DRIFT_RISKS, f"{repo_name}.estate.drift_risk")
    return int(bad)


def check_recovery(repo_name: str, recovery: object) -> int:
    if not expect_mapping(recovery, f"{repo_name}.recovery"):
        return 1
    assert isinstance(recovery, dict)
    bad = 0
    if "recovered_threads" in recovery and not expect_list(recovery["recovered_threads"], f"{repo_name}.recovery.recovered_threads"):
        bad += 1
    bad += not check_enum(recovery.get("disposition"), RECOVERY_DISPOSITIONS, f"{repo_name}.recovery.disposition")
    return int(bad)


def check_adoption(repo_name: str, adoption: object) -> int:
    if not expect_mapping(adoption, f"{repo_name}.adoption"):
        return 1
    assert isinstance(adoption, dict)
    bad = 0
    if "consumes" in adoption and not expect_list(adoption["consumes"], f"{repo_name}.adoption.consumes"):
        bad += 1
    if "consumed_by" in adoption and not expect_list(adoption["consumed_by"], f"{repo_name}.adoption.consumed_by"):
        bad += 1
    bad += not check_enum(adoption.get("adoption_state"), ADOPTION_STATES, f"{repo_name}.adoption.adoption_state")
    return int(bad)


def check_drift(repo_name: str, drift: object) -> int:
    if not expect_mapping(drift, f"{repo_name}.drift"):
        return 1
    assert isinstance(drift, dict)
    return int(not check_enum(drift.get("risk"), DRIFT_RISKS, f"{repo_name}.drift.risk"))


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
    # Minimal structural checks without jsonschema dependency.
    for k in ["workspace_inventory_version", "org", "repos"]:
        if k not in data:
            print(f"ERR: inventory missing key: {k}", file=sys.stderr)
            return 2

    if not isinstance(data["repos"], list) or not data["repos"]:
        print("ERR: repos must be a non-empty list", file=sys.stderr)
        return 2

    bad = 0
    seen: set[tuple[str, str]] = set()
    default_org = data["org"]

    for r in data["repos"]:
        if not isinstance(r, dict):
            print(f"ERR: repo entry must be a mapping/object: {r}", file=sys.stderr)
            bad += 1
            continue

        for k in ["name", "kind", "manifest"]:
            if k not in r:
                print(f"ERR: repo entry missing {k}: {r}", file=sys.stderr)
                bad += 1

        name = str(r.get("name", "<missing>"))
        org = str(r.get("org", default_org))
        key = (org, name)
        if key in seen:
            print(f"ERR: duplicate repo entry: {org}/{name}", file=sys.stderr)
            bad += 1
        seen.add(key)

        bad += not check_enum(r.get("status"), REPO_STATUSES, f"{org}/{name}.status")

        if "related_repos" in r and not expect_list(r["related_repos"], f"{org}/{name}.related_repos"):
            bad += 1
        if "provides" in r and not expect_list(r["provides"], f"{org}/{name}.provides"):
            bad += 1

        if "estate" in r:
            bad += check_estate(f"{org}/{name}", r["estate"])
        if "recovery" in r:
            bad += check_recovery(f"{org}/{name}", r["recovery"])
        if "adoption" in r:
            bad += check_adoption(f"{org}/{name}", r["adoption"])
        if "validation" in r and not expect_mapping(r["validation"], f"{org}/{name}.validation"):
            bad += 1
        if "drift" in r:
            bad += check_drift(f"{org}/{name}", r["drift"])

    if bad:
        return 2

    print(f"OK: inventory structure valid ({len(data['repos'])} repos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
