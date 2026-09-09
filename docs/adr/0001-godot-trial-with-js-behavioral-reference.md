---
status: accepted
---

# Run a bounded Godot trial with JavaScript as behavioral reference

Necro will try Godot in a separate lightweight repository. The existing JavaScript game remains intact and is pinned as a behavioral reference for selected observable contracts.

This is not approval for a full migration. The Godot trial should reimplement only what its G0–G3 gates require and should not translate the legacy JS architecture, old Arena orchestration, large generated artifacts, or unrelated backlog.

## Consequences

- Godot work can diverge architecturally when that better fits the engine and the Exploration direction.
- The JS reference is evidence for behavior, not a code-port checklist.
- A broader migration requires an explicit decision after the trial evidence and human playtest.