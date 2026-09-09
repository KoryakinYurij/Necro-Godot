# JavaScript Behavioral Reference

The JavaScript game is an external behavioral reference for selected contracts. It is not copied into this repository and its architecture is not a migration template.

## Pinned baseline

- Repository: `KoryakinYurij/Necro-game`
- Baseline SHA: `c98313b2de66b921e44b011f233ee96db25103ab`
- Baseline date checked: 2026-09-09

At that baseline the JS Exploration chain reports #2–#5 closed. #6 Cursed Altar, #7 farther-route Danger/rewards, #8 reproducibility/measurement, and #9 human playtest remain open.

Those open issues are **not** the Godot execution queue. Their ideas may be reconsidered only when a Godot gate explicitly needs them.

## Contracts worth carrying

- World Description is reproducible from Expedition seed plus stable spatial identity and does not depend on visit order.
- Generated World Description and mutable Expedition State are separate concerns.
- Dormant Encounter content is not already-live global combat AI.
- Encounter activation can be left and revisited without duplicating completion XP or one-time rewards.
- Stale delayed spawn work from an obsolete activation cannot leak into a later activation/restart.
- Cleared Encounter/POI state stays Cleared for the rest of the Expedition.
- A new Expedition starts cleanly without stale run state.

## Known behavior that is not an oracle

A JS implementation being closed/green does not automatically make its exact behavior correct for Godot.

When Ruins enters Godot scope, independently verify these known review risks instead of reproducing them:

- Reward choice must have an explicit modal/pause/input contract; a fullscreen overlay alone is not a pause.
- Real last-kill XP/level-up interaction with the Ruins reward must be tested, not simulated by directly marking the final guard dead.
- Repeated input must not apply or claim a reward twice.
- Restart/new Expedition must invalidate any prior reward interaction; an old callback/modal must not mutate the fresh run.

Use the JS game to answer “what selected contract are we trying to preserve?”, never “what code structure should Godot copy?”.