# Necro-Godot Context

Necro is an Exploration / Action Roguelite about a necromancer choosing routes, risks, fights, and places of power inside procedural expeditions.

## Language

**Expedition** — one playable run through a generated world, from spawn until death or a future successful exit condition.
_Avoid_: arena round, wave session.

**Exploration Loop** — choose a direction, discover a meaningful opportunity or threat, decide whether to engage, resolve it, receive a reward, then choose what to pursue next.
_Avoid_: survival loop, wave loop.

**Encounter** — a local combat opportunity tied to a place in the expedition. It can be dormant, active, and cleared.
_Avoid_: global wave.

**Point of Interest (POI)** — a meaningful place that creates a route, risk, interaction, or reward decision. It is gameplay content, not decoration.

**Ruins** — the first trial POI: a local guarded place that can become Cleared and offer one current-expedition build choice.

**Cleared** — a run-local terminal state: the Encounter or POI is complete and its one-time completion reward cannot be earned again in that Expedition.

**Behavioral Reference** — the pinned JavaScript Necro revision used to compare selected observable gameplay contracts. It is not a source architecture for Godot.

**World Description** — deterministic content derived from Expedition seed plus stable spatial identity: what opportunities exist and where. It must not change because areas were visited in a different order.

**Expedition State** — mutable run-local facts about a World Description: discovered, active, cleared, reward claimed, and similar progress. It is separate from generated description data.

**Autonomous Minion** — a player-allied unit that follows/positions and chooses combat targets without direct attack commands from the player.

**Build Progression** — power or playstyle changes that affect only the current Expedition.
_Avoid_: meta progression.

**Danger** — spatially communicated risk of an Encounter, POI, or route. It is not elapsed-time pressure.

**Trial Gate** — an evidence boundary G0–G3. Passing a gate means its stated questions were answered; it does not imply approval of a full migration.

**Playable Build** — an exported Windows build that can be launched independently of the Godot editor and is tied to a Git commit SHA.

**Clean Restart** — starting a new Expedition after death/restart with no stale enemies, timers, reward state, delayed spawns, or prior run state leaking into the new run.