---
name: godot-gameplay-qa
description: Use for routine gameplay verification in the live Godot editor: movement, encounters, rewards, pause/modal behavior, runtime state, screenshots, and fast post-change smoke tests. Exported Windows .exe black-box validation uses windows-export-playtest instead.
---

# Godot Gameplay QA

Use Godot AI as the default hands/eyes for routine gameplay QA. Keep the loop **tight**: test the changed behavior with the fewest independent observations that can actually prove it.

The active ticket/spec defines what must be proven. This skill chooses the cheapest trustworthy verification seam; it does not lower acceptance criteria.

## Fast path

1. **Warm reuse.** Check `editor_state` once. Reuse the current editor, MCP bridge, and running game when their state is valid for the scenario. Start/restart only when the scenario needs a fresh lifecycle.
2. **Drive once.** Express timed gameplay as one action-based `game_manage(op="input_sequence")` whenever possible. Put press/hold/release timing in that one sequence instead of paying one MCP round-trip per input event.
3. **Observe narrowly.** Read only the state needed for the acceptance criterion. Use known node paths directly; discover with `get_scene_tree` only when paths are unknown or structure changed.
4. **Capture intentionally.** Use `editor_screenshot(source="game")` at visual acceptance boundaries, not after every action. Runtime state proves state; the framebuffer proves appearance.
5. **Read errors once.** Read game/editor errors at the end of a successful smoke, or immediately when a command/behavior fails. Do not poll logs between healthy steps.
6. **Continue warm.** Run the next scenario against the same editor/game when isolation permits. Pay for a clean restart only when isolation or lifecycle semantics require it.

## Observation priority

Prefer the highest-level trustworthy seam already present in the game:

- For one or two concrete nodes, use `get_node_info`.
- For UI/modal criteria, use `get_ui_elements` plus a game framebuffer when appearance matters.
- For several related facts or a derived condition, use a **read-only** `game_eval` that returns one compact dictionary. Prefer an existing domain observation method such as a snapshot function when one already exists.
- Do not add gameplay APIs, debug flags, or scene changes solely to make MCP verification easier.

A setup operation may use an existing reset/setup method through `game_eval` when the reset itself is **not** under test. Immediately verify the resulting setup state. If restart, reward application, death recovery, input handling, or another bypassed path is the acceptance criterion, exercise that path normally instead.

## Evidence routing

- Deterministic logic and regressions → GUT/tests.
- Live gameplay state and transitions → Godot AI runtime observation.
- Timed gameplay actions → action-based `input_sequence`.
- Visual result → game framebuffer.
- Export/install/startup, physical Windows input, focus/lock behavior, or final `.exe` evidence → `.agents/skills/windows-export-playtest/SKILL.md`.

Godot AI evidence is instrumented gameplay evidence. Never label it as proof of the exported `.exe` or the physical Windows keyboard path.

## Trust guardrails

`game_eval` and direct runtime inspection are observation/setup tools, not shortcuts to a green result. Do not force the state being tested: do not kill an enemy, grant a reward, open/close a modal, revive the player, or write completion state when the corresponding behavior is the thing being verified.

Prefer action-based input because it is frame-timed and focus-independent. Use key/mouse synthesis only when key/mouse semantics themselves matter.

If the helper is not live, the framebuffer is stale, or runtime commands disagree with visible behavior, allow one bounded recovery/restart. Then diagnose the broken layer rather than layering more automation around it.

## Default smoke shape

For an ordinary gameplay change, aim for:

`tests → warm project → one input_sequence → one compact state assertion → framebuffer only if visual → logs/errors once`

Add steps only when an acceptance criterion requires independent evidence. Do not run the exported `.exe` merely to duplicate evidence already proven at the live-editor seam.

## Done

Gameplay QA is complete only when every changed acceptance criterion has direct evidence at an appropriate seam, the game reports no relevant runtime errors, and visual criteria have visual evidence. Report instrumented live-editor evidence separately from exported-build evidence.
