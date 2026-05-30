# Estate Ledger v0

Status: draft  
Authority repo: `SocioProphet/workspace-inventory`  
Consumer: `SocioProphet/sociosphere`  
Scope: repo-level estate state, ownership, recovery disposition, adoption state, and drift visibility

## Purpose

This document extends `workspace-inventory` from a repository index into an estate-ledger authority surface.

The existing inventory answers which repositories exist, what role they serve, who owns the canonical boundary, and how Sociosphere should discover them. The estate ledger adds a second question: what is the current governance state of each repo and recovered workstream?

The goal is not to duplicate GitHub issues, PRs, CI, or repo-local manifests. The goal is to provide an estate-level ledger that records durable state needed for cross-repo coordination.

## Relationship to existing inventory

The existing `inventory/repos.yaml` remains the canonical repo list.

The estate-ledger layer should be additive. It should not replace these existing fields:

- `name`
- `org`
- `kind`
- `manifest`
- `status`
- `authority_role`
- `boundary_notes`
- `related_repos`
- `optional_layer`
- `canonical_source_ref`
- `provides`

Future ledger fields may be added to `inventory/repos.yaml` or placed in separate ledger files if the top-level inventory becomes too large.

## Ledger responsibilities

The estate ledger should track:

- ownership and authority surface;
- recovery disposition for lost work;
- adoption state across related repos;
- CI / validation posture;
- doctrine and schema capture state;
- dependency and consumer relationships;
- branch / PR / issue state where it matters to estate governance;
- drift risk and review cadence;
- supersession and deprecation status.

## Non-goals

The estate ledger is not a replacement for GitHub, Sociosphere manifests, repo-local CI, issue trackers, dependency files, or release artifacts.

It should not become a manual duplicate of every branch, PR, or issue. It should capture only estate-governance facts that matter across repo boundaries.

## Estate ledger objects

### EstateRepoRecord

A repo-level record extending the existing inventory entry with governance state.

Minimum fields:

```yaml
estate:
  owner_plane: ""
  authority_surface: ""
  doctrine_state: none | draft | provisional | admitted | superseded | deprecated
  validation_state: unknown | none | local | ci | release_gate
  adoption_state: none | planned | partial | active | mature | deprecated
  drift_risk: low | medium | high | unknown
  review_cadence: ""
```

### RecoveryDisposition

A record of what happened to recovered lost work.

Allowed dispositions:

```text
owner_repo_assigned
archive_only
frozen_with_return_condition
intentionally_not_pursued
blocked
superseded
```

Minimum fields:

```yaml
recovery:
  recovered_threads: []
  disposition: owner_repo_assigned | archive_only | frozen_with_return_condition | intentionally_not_pursued | blocked | superseded
  authority_artifact: ""
  tracking_ref: ""
  return_condition: ""
```

### AdoptionState

A record of whether a doctrine, schema, protocol, or recovered thread has been adopted by related repos.

Minimum fields:

```yaml
adoption:
  consumes: []
  consumed_by: []
  adoption_state: none | planned | partial | active | mature | deprecated
  compatibility_ref: ""
  dependency_pin: ""
```

### ValidationState

A record of the repo's validation posture as it matters to estate governance.

Minimum fields:

```yaml
validation:
  ci_ref: ""
  local_validator: ""
  release_gate: ""
  known_gap: ""
```

### DriftReview

A record of estate-level drift risk and reobservation requirements.

Minimum fields:

```yaml
drift:
  risk: low | medium | high | unknown
  review_cadence: ""
  review_trigger: ""
  last_reviewed: ""
```

## Lost-work recovery rule

A recovered thread may not remain as unowned memory.

It must resolve into exactly one of:

1. owner repo assigned with authority artifact;
2. archive-only with provenance notes;
3. frozen with return condition and named prerequisite;
4. intentionally not pursued with rationale;
5. blocked with blocker reference;
6. superseded by a newer authority surface.

This rule aligns with `SocioProphet/sociosphere:docs/strategy/lost-work-recovery-map.md` and `SocioProphet/systems-learning-loops:kb/patterns/institutional-amnesia.md`.

## Sociosphere integration

Sociosphere should consume the estate ledger to answer:

- Which repos are active authorities?
- Which repos are optional or held?
- Which recovered threads have no authority surface?
- Which repos have doctrine but no validation?
- Which repos are downstream consumers of an authority surface?
- Which repos need review because drift risk is high?

The estate ledger should remain source-controlled and reviewable. Any generated projection into Sociosphere manifests or locks should cite the inventory commit SHA.

## First implementation path

The first implementation should be conservative:

1. add this doctrine document;
2. extend `inventory/schema.json` with optional `estate`, `recovery`, `adoption`, `validation`, and `drift` blocks;
3. add one or two example annotations to `inventory/repos.yaml` for `workspace-inventory`, `sociosphere`, and `ontogenesis`;
4. update `tools/validate_inventory.py` only if needed for structural checks;
5. avoid generated ledgers until the shape stabilizes.

## Claim boundary

The estate ledger records coordination state. It does not prove repository health, product readiness, theorem progress, security posture, or CI correctness. Repo-local artifacts and validation remain authoritative for those claims.
