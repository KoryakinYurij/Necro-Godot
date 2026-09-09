# Godot Agent Toolchain

This file defines how Godot-specific tools support the project without replacing the Matt workflow or the active GitHub gate.

## Authority order

1. Active GitHub spec/ticket and accepted project ADRs define scope.
2. Matt engineering skills define the development process: shape → spec → tracer tickets → implement/TDD → review.
3. Official Godot documentation is the primary technical reference for engine behavior and APIs.
4. Installed GD-Agentic-Skills provide on-demand Godot expert patterns and implementation guidance.
5. Godot AI MCP provides hands/eyes on the live editor; it never decides product scope or architecture by itself.

When sources disagree, escalate upward in this order. A Godot skill pattern must not expand a G ticket or override a project decision.

## Engine

- Installed/recommended trial engine: Godot `4.7.2.stable.official.ed1daf0bf`.
- Windows executable root: `D:\Tools\Godot\4.7.2\`.
- Matching `4.7.2.stable` export templates are installed under the user's Godot export-template directory.
- Godot 4.7.1 remains installed as rollback/reference; do not remove it during the trial.
- G0 must still explicitly approve the 4.7.2 baseline before G1 implementation begins.

## GD-Agentic-Skills

Installed globally on Windows for both Codex and Claude Code. Canonical copies live under `C:\Users\Fixed\.agents\skills\godot-*`; Claude discovery links are managed by the skills CLI.

Do not use `--all`. Load `godot-master` only as a router, then load the smallest relevant Domain Skill set for the active ticket.
Curated installed skills for G1–G3:

- `godot-master`
- `godot-project-foundations`
- `godot-gdscript-mastery`
- `godot-input-handling`
- `godot-2d-physics`
- `godot-camera-systems`
- `godot-combat-system`
- `godot-scene-management`
- `godot-resource-data-patterns`
- `godot-testing-patterns`
- `godot-debugging-profiling`
- `godot-performance-optimization`
- `godot-procedural-generation`
- `godot-export-builds`

Persona/orchestrator skills from that library do not replace Matt or the G0–G3 gate flow unless a ticket explicitly asks for a bounded experiment with one.

## Automated tests

Project test framework: GUT `9.7.1`, pinned because it targets Godot 4.7.x.

- Addon path: `addons/gut/`.
- Tests should prove externally meaningful behavior at the highest practical seam; do not assert scene-tree internals merely because GUT can access them.
- GUT complements Matt `/tdd`; it does not replace the ticket acceptance criteria or real playable-build evidence.

## Live editor MCP

Primary MCP: Godot AI `4.0.3`, pinned project addon under `addons/godot_ai/`.

The Python bridge is prewarmed with `godot-ai==4.0.3`. On this Windows machine, `uv` managed Python hit an untrusted-mount error, so user-level `UV_PYTHON` is pinned to the installed trusted CPython 3.12 at `C:\Users\Fixed\AppData\Local\Programs\Python\Python312\python.exe`.
Activation/configuration rule:

- Keep the plugin files installed and version-pinned before G1.
- Do not invent MCP client entries manually. Godot AI v4 expects `godot-ai attach` with the plugin-matched version/ports/capability handling.
- When G1 creates the first real `project.godot`, enable Godot AI and GUT in that project, launch Godot 4.7.2 from the repository directory, and use the Godot AI dock's Configure action for Codex/Claude Code.
- Prefer project-scoped MCP configuration for Necro-Godot so this experimental editor bridge does not silently attach unrelated Godot projects.
- After configuration, smoke-test: inspect scene hierarchy, run the project, read debugger output, and capture one screenshot before relying on MCP for implementation evidence.

Fallback MCP: `Coding-Solo/godot-mcp` is not installed initially. Use it only if Godot AI blocks G1 after a bounded troubleshooting pass; do not run two editor MCPs concurrently by default.

## Evidence rule

Godot-specific automation reduces manual work but does not lower acceptance. For each implementation gate keep automated test results, real editor/build launch evidence, and human-playable artifacts distinct.