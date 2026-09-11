# Blender Test Workspace

This folder isolates Blender asset experiments from the Godot gameplay tree.

## Layout

- `.scratch/` — local working scripts, previews, backups, and temporary Blender evidence. It is intentionally ignored by Git.
- `research/` — durable findings that should survive across agents and sessions.

## Purpose

Use this workspace to prototype and review Necro art-production workflows before promoting any asset or process into the main game pipeline. Experimental Blender files and generated evidence do not define gameplay scope or architecture.

Project-wide scope still lives in GitHub Issues; canonical domain language stays in `CONTEXT.md`; hard-to-reverse decisions belong in `docs/adr/` only when an actual architectural trade-off has been accepted.
