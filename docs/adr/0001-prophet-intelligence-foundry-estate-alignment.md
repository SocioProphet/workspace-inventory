# ADR 0001: Prophet Intelligence Foundry Estate Alignment

Status: Proposed
Date: 2026-05-04

## Context

The SourceOS/SociOS/SocioProphet estate now has enough separate control-plane, runtime, lab, operator, and model-governance repositories to support a first-class Prophet Intelligence Foundry program. The prior estate map correctly separated platform runtime, contracts, agent execution, model governance, boot/install, SourceOS shell, language intelligence, GAIA, web/packaging, and delivery governance. Recent live repository additions expand the estate with first-class local runtime and operator surfaces:

- `SourceOS-Linux/agent-machine`
- `SourceOS-Linux/TurtleTerm`
- `SourceOS-Linux/BearBrowser`
- `SourceOS-Linux/agent-term`
- `SourceOS-Linux/sourceos-devtools`
- `SourceOS-Linux/homebrew-tap`
- `SourceOS-Linux/librewolf-source-mirror`
- `SocioProphet/HolographMe`
- `SocioProphet/smart-tree`

The architecture correction is that Sociosphere/Socius must remain the workspace-state and actuation controller. It must not become the cognitive routing root. Prophet Intent Engine, Prophet Model Mesh, model-router, guardrail-fabric, AgentPlane, Policy Fabric, Agent Machine, SourceOS operator surfaces, and model-governance-ledger each own separate enforceable boundaries.

## Decision

Represent the Prophet Intelligence Foundry as a first-class estate program. Until a dedicated `SocioProphet/prophet-intelligence-foundry` repository exists, its contracts and implementation lanes must be routed through the existing canonical surfaces:

- `SocioProphet/functional-model-surfaces` for model, data, training, eval, release, routing, guardrail, tool, agent, and promotion contracts.
- `SocioProphet/model-governance-ledger` for evidence, factsheets, dataset/run/eval/promotion records, rollback records, and release decisions.
- `SocioProphet/model-router` for governed model and service routing across local vs hosted, small vs large, cost, latency, quality, privacy, fallback, and eval-confidence policy.
- `SocioProphet/guardrail-fabric` for reusable safety and runtime governance around models, agents, tools, RAG packages, knowledge bases, and runtime deployments.
- `SourceOS-Linux/sourceos-model-carry` for on-device AI service carriage, signed model references, launch profiles, cache policy, fallback references, ReleaseSet and BootReleaseSet bindings, and evidence collectors.
- `SourceOS-Linux/agent-machine` for machine-local runtime probing, inference provider lifecycle, model residency, cache-aware scheduling facts, AgentPod envelopes, placement facts, and AgentMachineReceipt evidence.
- `SocioProphet/agentplane` for governed run lifecycle, run capsules, validation, execution receipts, replay, and evidence capture.
- `SocioProphet/sociosphere` and this repository for workspace state, inventory, composition, leases, repo/worktree/task surfaces, and deterministic multi-repo materialization.

## Boundary rules

1. `sociosphere` owns workspace state and materialization. It must not own cognitive intent routing, model selection, or model governance.
2. `model-router` owns runtime model/service route decisions. It must not own training, release approval, or workspace mutation.
3. `agent-machine` owns local/cluster machine runtime facts and receipts. It must not replace AgentPlane, Policy Fabric, Agent Registry, or the model-router.
4. `TurtleTerm`, `BearBrowser`, `agent-term`, and `sourceos-devtools` are operator/runtime surfaces. They must emit evidence and preserve policy boundaries rather than becoming policy authority.
5. `smart-tree` remains a candidate inspection tool until its MCP, hook, and memory surfaces pass supply-chain and guardrail review.
6. `HolographMe` is the self-owned human digital twin governance plane for consent, capability proofs, delegated permissions, and mission-fit projection. It must not be reduced to a generic profile service.

## Required contract spine

The next contract PR must add or reserve the following contract families in `functional-model-surfaces`, with SourceOS-specific projections routed to `sourceos-spec` where applicable:

- `ModelSpec`
- `ModelFamilySpec`
- `AdapterSpec`
- `DatasetSpec`
- `DataManifest`
- `TrainingRun`
- `PostTrainingRun`
- `RewardModelSpec`
- `EvalSuite`
- `EvalReport`
- `SafetyReport`
- `InterpretabilityReport`
- `ModelReleaseDecision`
- `ReasoningRuntimePlan`
- `ModelRoutingDecision`
- `MemoryRoutingPlan`
- `ToolContract`
- `CapabilityGrant`
- `WorkspaceLease`
- `RunCapsule`
- `AgentMachineReceipt`
- `ModelResidency`
- `InferenceProvider`
- `ContextBundle`
- `VerifierQuorum`

## Consequences

This keeps the estate contract-first and prevents a god-object architecture. The Prophet Model Mesh becomes the runtime model composition layer, while the Prophet Intelligence Foundry becomes the lifecycle program for data, training, post-training, RL, evals, safety, distillation, promotion, and release governance.

Runtime implementation should not proceed until the contract spine has at least schema stubs, examples, and validation fixtures. Labs emit candidate service manifests; governance validates; SourceOS carries only approved references; Agent Machine executes only policy-admitted local or cluster runtime placements; AgentPlane records replayable run evidence.
