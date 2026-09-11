# Blender Test Workspace

This folder isolates Blender asset experiments from the Godot gameplay tree while keeping the reviewable art-production history next to the project.

## Layout

- `.scratch/blender/` — tracked Blender scripts, scene checkpoints, current `.blend`/`.glb`, and reproducible modeling/render helpers.
- `.scratch/preview/` — tracked review boards, final renders, and close-up QA views used to judge silhouette, anatomy, contacts, and presentation.
- Other files directly under `.scratch/` remain ignored because they are unrelated Windows/Godot runner leftovers rather than Blender evidence.
- `research/` — durable findings and process lessons that should survive across agents and sessions.

## Review purpose

A reviewer should be able to reconstruct how the asset evolved, inspect the current scene/export, compare checkpoints, and audit the exact scripts and visual checks that produced each iteration. The Blender evidence is intentionally versioned even though the rest of `.scratch` remains local-only.

Project-wide gameplay scope still lives in GitHub Issues; canonical domain language stays in `CONTEXT.md`; hard-to-reverse decisions belong in `docs/adr/` only when an actual architectural trade-off has been accepted.
