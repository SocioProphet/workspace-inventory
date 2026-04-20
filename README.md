# Workspace Inventory

This repo is the canonical index of repositories in the `SocioProphet` GitHub org
and the adjacent cross-org authorities needed to assemble the broader
SourceOS/SociOS platform graph.

It records repository roles, integration contracts (TriTRPC, MCP, CapD, OPA),
and how the workspace controller (`sociosphere`) should discover and wire those
repos without duplicating canonical ownership.

## Scope

This repo should answer:

- which repositories are part of the active ecosystem graph
- which repo is canonical for a given role or boundary
- which repos are cross-org authorities that still belong in the graph
- which repos are active, held, candidate, or deprecated
- which repo should be treated as optional vs required by a given layer

## Structure

- `inventory/repos.yaml` — repo list + metadata
- `inventory/schema.json` — JSON Schema for inventory entries
- `tools/validate_inventory.py` — validates `repos.yaml` structure

## Field notes

The root-level `org` is the default owner/org for entries that do not override it.
A repo entry may optionally set:

- `org` — explicit owner/org override for cross-org authorities
- `status` — `active`, `candidate`, `held`, or `deprecated`
- `authority_role` — canonical responsibility in the ecosystem
- `boundary_notes` — short repo-boundary statement
- `related_repos` — adjacent repositories commonly linked to this one
- `optional_layer` — whether the repo is optional rather than universally required
- `canonical_source_ref` — pointer to the canonical ownership namespace or source map

## Usage

```bash
python3 tools/validate_inventory.py
```
