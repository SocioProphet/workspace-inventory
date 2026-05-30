# Estate Overlays

Status: draft  
Authority repo: `SocioProphet/workspace-inventory`

Estate overlays record repo-level estate-ledger state without requiring immediate mutation of the top-level `inventory/repos.yaml` file.

Use an overlay when:

- the top-level inventory is large and a narrow update should avoid unrelated churn;
- a tranche needs explicit estate state before it is folded into the canonical repo list;
- an authority repo is already known but adoption, drift, or validation fields are still stabilizing;
- a temporary or tranche-specific view should remain reviewable before canonicalization.

## Overlay contract

A valid overlay should include:

- `overlay_version`
- `status`
- `authority_repo`
- `subject_repo`
- `created`
- `purpose`
- `repo`
- `estate`
- `recovery`
- `adoption`
- `validation`
- `drift`
- `claim_boundary`

The `repo` block should mirror the shape of a single `inventory/repos.yaml` entry where practical. The estate, recovery, adoption, validation, and drift blocks follow the estate-ledger vocabulary in `docs/estate-ledger-v0.md`.

## Promotion path

An overlay may later be promoted into `inventory/repos.yaml` when:

1. the subject repo should be part of the canonical active inventory;
2. the estate fields have stabilized;
3. the validator covers the relevant enum and structural constraints;
4. the promotion can be reviewed without dropping unrelated inventory entries.

## Non-goal

Overlays are not a shadow inventory. They are temporary or tranche-specific estate-ledger records. The top-level inventory remains canonical for the base repo list.
