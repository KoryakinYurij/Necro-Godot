# Necro Hero — handoff

## Purpose

This file tells a future agent how to resume the original Necro Hero Blender experiment without treating the accumulated correction scripts as a clean generator.

## Current source and evidence

Canonical Windows project root:
`D:\Code AI\Games\Necro-Godot`

Current editable hero source:
`prototypes/blender-test/.scratch/blender/current/necro_hero_prototype.blend`

Current explicit 3D export from the experiment:
`prototypes/blender-test/.scratch/blender/current/necro_hero_prototype_v2.glb`

Review evidence:
`prototypes/blender-test/.scratch/preview/`

Pre-change checkpoints:
`prototypes/blender-test/.scratch/blender/backups/`

Historical scripts and diagnostic helpers:
`prototypes/blender-test/.scratch/blender/*.py`

## What the scripts mean

The numbered scripts document iterative work performed on a changing Blender scene: inspection, cleanup, shading, framing, visual passes, arm/shoulder/hand rebuilds, silhouette corrections, and grip fixes.

They are valuable audit evidence and can contain reusable techniques. They are **not** currently proven to reconstruct the final hero from an empty scene by running them sequentially.

## Resume procedure

1. Open the current `.blend` in a fresh Blender session on Windows.
2. Inspect the scene before changing it; identify the current object names, collections, transforms, and visible problem area.
3. Capture a diagnostic view of the area being changed.
4. Before a risky structural edit, save a new checkpoint in `backups/`.
5. Modify the saved source directly or use a narrowly scoped script whose starting assumptions you have verified.
6. Re-run neutral multi-angle and close-up review for the changed zone, plus a whole-character gameplay-scale view.
7. Re-check dependent geometry after any major form change.
8. Publish a fresh game-facing output from the saved source and verify that exact output in the target Godot context before calling it ready.

## Known lesson hotspots

The first test repeatedly exposed these failure classes:
- hand/wrist/finger orientation around the staff;
- shoulder/pauldron seating;
- robe silhouette and large cloth masses;
- belt/sash/accessory geometry left behind after body or clothing changes;
- presentation renders masking construction problems.

Read `asset-production-lessons.md` before another substantial hero revision.

## What this handoff does not promise

It does not claim that the current hero is production-final.

It does not claim that `necro_hero_prototype_v2.glb` defines the project's permanent runtime representation; that choice belongs to accepted project scope/ADR when made.

It does not claim a clean-scene full generator exists. If full reconstruction from nothing becomes valuable, make that a separate task and prove it from a clean Blender session rather than retroactively treating the history scripts as one.
