# Agent-harness prior art

Checked 2026-07-23 against primary documentation and upstream repositories.

| Harness | Primary evidence | Transferable mechanism | Boundary for Bonsai |
|---|---|---|---|
| Codex | [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [configuration](https://learn.chatgpt.com/docs/config-file/config-reference) | Specialized inspectable threads, steering/waiting/closing, role/model/effort/concurrency configuration, inherited sandboxing, caution around parallel writes | A consolidated answer is not durable creative state. Per-shot privacy approval must be stronger than session inheritance. |
| OpenHands | [Agent](https://docs.openhands.dev/sdk/arch/agent), [events](https://docs.openhands.dev/sdk/arch/events), [condenser](https://docs.openhands.dev/sdk/arch/condenser), [runtime](https://docs.openhands.dev/openhands/usage/architecture/runtime) | Typed append-only events, separate tool and conversation errors, derived condensed views, sandboxed reproducible execution | A stateless reasoning step is not an artifact version graph. Context condensation cannot replace approved state. Docker is too heavy as the default for deterministic local media transforms. |
| Aider | [Modes](https://aider.chat/docs/usage/modes.html), [architect/editor rationale](https://aider.chat/2024/09/26/architect.html), [edit formats](https://aider.chat/docs/more/edit-formats.html) | Split semantic planning from realization into a strict format; allow different models for each responsibility | The Bonsai “editor” should normally be schema validation plus a deterministic adapter, not another free-form model. |
| SWE-agent | [ACI overview](https://swe-agent.com/latest/background/), [configuration](https://swe-agent.com/latest/config/), [tool bundles](https://swe-agent.com/latest/reference/bundle_config/), [trajectory replay](https://swe-agent.com/latest/usage/cli/) | Small typed commands, configurable tool bundles, explicit state, persisted trajectories, inspection and replay | Repository patches and shell state are not a multimodal creative graph. SWE-agent is maintenance-only; borrow the ACI principle, not the product shape. |
| Claude Code | [Subagents](https://code.claude.com/docs/en/sub-agents), [hooks](https://code.claude.com/docs/en/hooks), [permissions](https://code.claude.com/docs/en/permissions) | Declarative roles, tool/model/effort/turn policies, hooks, background execution, and worktree isolation | Fresh terminal-first contexts do not create shared artifact truth. Background approval behavior and parent permissions are insufficient for asset-specific remote-provider consent. |

## Changes made to RFC-0002

1. Added an append-only execution-event contract with causation, correlation,
   adapter version, asset hashes, and idempotency.
2. Added `director`, `producer`, `verifier`, and `composer` role/capability
   manifests.
3. Split semantic proposal from deterministic realization.
4. Added checkpoint, dry-run, replay, and nondeterministic reproduction
   semantics.
5. Made canonical artifact state independent of condensed agent context.
