# Blender Test Workspace

This workspace isolates Blender asset experiments from the Godot gameplay tree while keeping reviewable art-production evidence next to the project.

## Start here

For Blender character work, use these documents in this order:

1. `research/character-workflow.md` — reusable creation/review/export loop for a new character.
2. `research/asset-production-lessons.md` — lessons learned from the Necro Hero test and why the gates exist.
3. The asset-specific README or handoff — current source, known weak spots, and how to resume that asset.

For the original hero, read `research/necro-hero-handoff.md`.

## Layout

- `.scratch/blender/current/` — current Necro Hero working `.blend` and explicit export output.
- `.scratch/blender/backups/` — checkpoints before risky hero changes.
- `.scratch/blender/*.py` — historical iterations and diagnostics from the first hero experiment.
- `.scratch/preview/` — review renders and close-up QA evidence for the hero.
- `research/` — reusable workflow, lessons, and handoffs.
- Per-asset prototype folders may keep their own `scripts/`, `current/`, `preview/`, README, and journal while the workflow is still being validated.

## Important distinction

The numbered Necro Hero scripts are an audit trail of how that asset evolved. Their numbering does **not** mean that running `01` through the last script reconstructs the character from an empty Blender scene.

The saved `.blend` is a valid working source. Publishing from that source and rebuilding from nothing are different capabilities; documentation must never imply the second unless a complete generator actually exists and has been tested from a clean session.

## Working rule

Use Blender on the canonical Windows checkout. Keep the source editable, perform diagnostic review before beauty polish, publish an explicit game-facing result, and verify the published result in its target Godot context before calling it game-ready.

Do not promote prototype conventions into project architecture by accident. A durable choice such as 3D runtime assets versus prerendered 2D belongs in the active scope/ADR process once the project actually commits to it.
