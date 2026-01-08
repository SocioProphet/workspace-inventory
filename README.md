# Workspace Inventory

This repo is the canonical index of repositories in the `socioprophet/` GitHub org,
their integration contracts (triRPC, MCP, CapD, OPA), and how the workspace
controller (`sociosphere`) should discover and wire them.

## Structure
- `inventory/repos.yaml` — list of repos + metadata
- `inventory/schema.json` — JSON Schema for repo manifests
- `tools/validate_inventory.py` — validates `repos.yaml` and per-repo `WORKSPACE.yaml` format

## Usage
```bash
python3 tools/validate_inventory.py
```
