#!/usr/bin/env python3
"""Tests for tools/discover_org_repos.py using a fake org listing + fake inventory."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import discover_org_repos as disc  # noqa: E402


FAKE_ORG_REPOS = [
    {"name": "curated-in-yaml", "url": "https://x/1", "isArchived": False, "isFork": False},
    {"name": "curated-in-csv", "url": "https://x/2", "isArchived": False, "isFork": False},
    {"name": "severed-in-manifest", "url": "https://x/3", "isArchived": False, "isFork": False},
    {"name": "allowlisted-repo", "url": "https://x/4", "isArchived": False, "isFork": False},
    {"name": "an-archived-repo", "url": "https://x/5", "isArchived": True, "isFork": False},
    {"name": "a-fork-repo", "url": "https://x/6", "isArchived": False, "isFork": True},
    {"name": "brand-new-untriaged", "url": "https://x/7", "isArchived": False, "isFork": False},
    {"name": "another-untriaged", "url": "https://x/8", "isArchived": False, "isFork": False},
    # cross-org entry should never count toward SocioProphet curation
    {"name": "cross-org-only", "url": "https://x/9", "isArchived": False, "isFork": False},
]


def _write_fake_inventory(tmp_path: Path) -> dict[str, Path]:
    repos_yaml = tmp_path / "repos.yaml"
    repos_yaml.write_text(
        yaml.safe_dump(
            {
                "workspace_inventory_version": 1,
                "org": "SocioProphet",
                "repos": [
                    {"name": "curated-in-yaml", "kind": "service", "manifest": "WORKSPACE.yaml"},
                    # cross-org entry: same short name, different org -> not SocioProphet-curated
                    {"name": "cross-org-only", "org": "SociOS-Linux", "kind": "os", "manifest": "WORKSPACE.yaml"},
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    csv_path = tmp_path / "estate.csv"
    csv_path.write_text(
        "repo_full_name,owned_services,supporting_services,contract_services,canonical_status\n"
        "SocioProphet/curated-in-csv,-,-,-,primary\n"
        "SociOS-Linux/some-other-org-repo,-,-,-,primary\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "estate.json"
    manifest.write_text(
        json.dumps(
            {
                "repo_count": 1,
                "removed_from_go_forward": ["SocioProphet/severed-in-manifest"],
                "consolidation_candidates": [],
            }
        ),
        encoding="utf-8",
    )
    allowlist = tmp_path / "allowlist.yaml"
    allowlist.write_text(
        yaml.safe_dump(
            {
                "discovery_allowlist_version": 1,
                "org": "SocioProphet",
                "allowlist": [{"name": "allowlisted-repo", "reason": "test"}],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return {"repos_yaml": repos_yaml, "csv": csv_path, "manifest": manifest, "allowlist": allowlist}


def test_curated_sources_are_unioned(tmp_path):
    paths = _write_fake_inventory(tmp_path)
    curated = disc.load_curated_names(
        "SocioProphet",
        repos_yaml=paths["repos_yaml"],
        canonical_csv=paths["csv"],
        canonical_manifest=paths["manifest"],
    )
    assert curated == {"curated-in-yaml", "curated-in-csv", "severed-in-manifest"}
    # cross-org repo with same short name must not be pulled into SocioProphet curation
    assert "cross-org-only" not in curated


def test_find_untriaged_excludes_forks_archived_curated_allowlisted(tmp_path):
    paths = _write_fake_inventory(tmp_path)
    curated = disc.load_curated_names(
        "SocioProphet",
        repos_yaml=paths["repos_yaml"],
        canonical_csv=paths["csv"],
        canonical_manifest=paths["manifest"],
    )
    allowlist = disc.load_allowlist(paths["allowlist"], "SocioProphet")
    untriaged = disc.find_untriaged(FAKE_ORG_REPOS, curated, allowlist)
    names = [r["name"] for r in untriaged]
    # cross-org-only is not curated for SocioProphet, so it correctly surfaces as untriaged
    assert names == ["another-untriaged", "brand-new-untriaged", "cross-org-only"]
    assert all(":" not in n for n in names)  # sanity: bare names


def test_no_untriaged_when_all_known(tmp_path):
    curated = {"a", "b"}
    repos = [
        {"name": "a", "url": "u", "isArchived": False, "isFork": False},
        {"name": "b", "url": "u", "isArchived": False, "isFork": False},
    ]
    assert disc.find_untriaged(repos, curated, set()) == []


def test_missing_allowlist_is_empty(tmp_path):
    assert disc.load_allowlist(tmp_path / "nope.yaml", "SocioProphet") == set()


def test_main_exits_nonzero_on_gap(tmp_path, capsys, monkeypatch):
    paths = _write_fake_inventory(tmp_path)
    org_json = tmp_path / "org.json"
    org_json.write_text(json.dumps(FAKE_ORG_REPOS), encoding="utf-8")
    monkeypatch.setattr(disc, "REPOS_YAML", paths["repos_yaml"])
    monkeypatch.setattr(disc, "CANONICAL_CSV", paths["csv"])
    monkeypatch.setattr(disc, "CANONICAL_MANIFEST", paths["manifest"])
    backlog = tmp_path / "untriaged.yaml"
    rc = disc.main(
        [
            "--org", "SocioProphet",
            "--org-repos-json", str(org_json),
            "--allowlist", str(paths["allowlist"]),
            "--backlog", str(backlog),
            "--json",
        ]
    )
    assert rc == 1
    report = json.loads(capsys.readouterr().out)
    assert report["untriaged_count"] == 3
    written = yaml.safe_load(backlog.read_text(encoding="utf-8"))
    assert written["untriaged_count"] == 3
    assert {r["name"] for r in written["untriaged"]} == {
        "another-untriaged",
        "brand-new-untriaged",
        "cross-org-only",
    }


def test_main_exits_zero_when_clean(tmp_path, monkeypatch):
    paths = _write_fake_inventory(tmp_path)
    monkeypatch.setattr(disc, "REPOS_YAML", paths["repos_yaml"])
    monkeypatch.setattr(disc, "CANONICAL_CSV", paths["csv"])
    monkeypatch.setattr(disc, "CANONICAL_MANIFEST", paths["manifest"])
    org_json = tmp_path / "org.json"
    # only curated/allowlisted/archived/fork repos -> no gap
    org_json.write_text(
        json.dumps(
            [
                {"name": "curated-in-yaml", "url": "u", "isArchived": False, "isFork": False},
                {"name": "allowlisted-repo", "url": "u", "isArchived": False, "isFork": False},
                {"name": "a-fork-repo", "url": "u", "isArchived": False, "isFork": True},
            ]
        ),
        encoding="utf-8",
    )
    rc = disc.main(
        [
            "--org", "SocioProphet",
            "--org-repos-json", str(org_json),
            "--allowlist", str(paths["allowlist"]),
        ]
    )
    assert rc == 0
