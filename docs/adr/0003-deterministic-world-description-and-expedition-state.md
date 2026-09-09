---
status: accepted
---

# Separate deterministic World Description from mutable Expedition State

For a given Expedition seed and stable spatial identity, generated world content must be reproducible and independent of visit order.

The description of what exists is separate from run-local mutable facts such as discovered, active, cleared, and reward-claimed state.

## Consequences

- Replaying a seed can reproduce the same opportunities without reproducing combat randomness.
- Leaving and returning cannot regenerate a completed Encounter or POI.
- Cleared/claimed state remains terminal for the Expedition.
- Live combat entities are runtime realizations of active content, not the persistent world description itself.