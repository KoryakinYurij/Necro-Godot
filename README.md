# Necro-Godot

Experimental Godot Exploration prototype for Necro.

This repository is a **trial**, not an approved full migration. The existing JavaScript game remains the behavioral reference; this repo reimplements only contracts that the trial deliberately chooses to prove.

## Current phase

- G0 — define and approve the trial contract.
- G1 — first playable combat build.
- G2 — Exploration loop with Encounter and Ruins reward.
- G3 — representative load/content variation and human playtest.

Broad migration begins only after the trial is accepted.

## Environment

Primary Godot development and real-run verification happen on the Windows machine.

- Godot: `4.7.2.stable.official.ed1daf0bf`
- Language: typed GDScript
- Trial repository working path: `D:\Code AI\Games\Necro-Godot`
- JavaScript reference repo: `KoryakinYurij/Necro-game`
- Reference baseline SHA: `c98313b2de66b921e44b011f233ee96db25103ab`

Read `AGENTS.md` before planning or implementation. Godot tooling is pinned and documented in `docs/agents/godot-toolchain.md`. Current executable scope lives in GitHub Issues; docs record durable context and decisions.