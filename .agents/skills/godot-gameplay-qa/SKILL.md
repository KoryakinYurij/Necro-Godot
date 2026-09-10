---
name: godot-gameplay-qa
description: Use for routine gameplay verification in the live Godot editor: movement, encounters, rewards, pause/modal behavior, runtime state, screenshots, and fast post-change smoke tests. Exported Windows .exe black-box validation uses windows-export-playtest instead.
---

# Godot Gameplay QA

Use Godot AI as the default hands/eyes for routine gameplay QA. Keep the loop **tight**: test the changed behavior with the fewest independent observations that can actually prove it.

The active ticket/spec defines what must be proven. This skill chooses the cheapest trustworthy verification seam; it does not lower acceptance criteria.

## Fast path

1. **Scenario first.** Before starting/restarting the game, define the initial state, action sequence, assertions, and required visual evidence. Do not spend live gameplay time discovering the tree unless structure is the thing under test.
2. **Warm reuse.** Check `editor_state` once. Reuse the current editor, MCP bridge, and running game when their state is valid for the scenario. Start/restart only when the scenario needs a fresh lifecycle.
3. **Drive once.** For polling-based actions, express timed gameplay as one `game_manage(op="input_sequence")`. Put press/hold/release timing in that one sequence instead of paying one MCP round-trip per input event.
4. **Observe narrowly.** Read only the state needed for the acceptance criterion. Use known node paths directly; discover with `get_scene_tree` only when paths are unknown or structure changed.
5. **Capture intentionally.** Use `editor_screenshot(source="game")` at visual acceptance boundaries, not after every action. Runtime state proves state; the framebuffer proves appearance.
6. **Read current-run errors once.** Check the current run's game log at the end of a successful smoke, or immediately on failure. Follow any `editor_errors_hint`; boot/load errors can predate the live helper.
7. **Continue warm.** Run the next scenario against the same editor/game when isolation permits. Pay for a clean restart only when isolation or lifecycle semantics require it.

## Input semantics

Choose delivery by how the game consumes input:

- Polling code such as `Input.get_vector()` / `Input.is_action_pressed()` → `input_sequence` / action-state input.
- Event handlers such as `_input()` / `_unhandled_input()` → an event-producing operation such as `input_key`, `input_mouse`, or `input_gamepad`, which routes through `Input.parse_input_event()`.
- `input_sequence` uses `Input.action_press/release`; it does **not** prove an event-driven handler. For this project, death → restart must exercise the `R` event path before the new run is accepted.

After every `input_sequence`, require `completed=true` and `actions_pressed_at_end=[]`. A successful command is not enough when the gameplay assertion did not change as expected.

Qualify each event-delivery path once before treating it as routine evidence. For the current restart path, run `natural death → input_key R press/release → generation increments → movement` twice without manual adjustment and record total duration. Repeat this qualification only when the input map, event handler, engine/tool version, or delivery implementation changes.

## Observation priority

Prefer the highest-level trustworthy seam already present in the game:

- For one or two concrete nodes, use `get_node_info`.
- For UI/modal criteria, use `get_ui_elements` plus a game framebuffer when appearance matters.
- For several related facts or a derived condition, use a **read-only** `game_eval` that returns one compact dictionary. Prefer an existing domain observation method such as a snapshot function when one already exists.
- Do not add gameplay APIs, debug flags, or scene changes solely to make MCP verification easier.

A setup operation may use an existing reset/setup method through `game_eval` when the reset itself is **not** under test. Immediately verify the resulting setup state. If restart, reward application, death recovery, input handling, or another bypassed path is the acceptance criterion, exercise that path normally instead.

## Evidence routing

Use only the layers the acceptance criterion needs; do not run all three by default.

- Deterministic rules, states, rewards, and regressions → GUT/tests.
- Live subsystem interaction, gameplay state, UI, and visual behavior → Godot AI.
- Export/install/startup, physical Windows input, focus/lock behavior, or final `.exe` evidence → `.agents/skills/windows-export-playtest/SKILL.md`.

Godot AI evidence is instrumented gameplay evidence. Never label it as proof of the exported `.exe` or the physical Windows keyboard path.

## Trust guardrails

`game_eval` and direct runtime inspection are observation/setup tools, not shortcuts to a green result. Do not force the state being tested: do not kill an enemy, grant a reward, open/close a modal, revive the player, or write completion state when the corresponding behavior is the thing being verified.

Match delivery to the consumer: action-state input for polling code, event-producing input for event handlers. Physical Windows input remains a separate exported-build concern.

If the helper is not live, the framebuffer is stale, or runtime commands disagree with visible behavior, allow one bounded recovery/restart. Then diagnose the broken layer rather than layering more automation around it.

## Default smoke shape

For an ordinary gameplay change, aim for:

`tests → scenario ready → warm project → minimal matching input path → one compact state assertion → framebuffer only if visual → current-run errors once`

Add steps only when an acceptance criterion requires independent evidence. Do not run the exported `.exe` merely to duplicate evidence already proven at the live-editor seam.

## Result record

Keep the routine report compact: SHA, scenario, validated initial state, assertions/result, elapsed time, and one framebuffer only when visual evidence is required. Full scene trees and extended logs belong to diagnosis. For logs, keep the current `run_id`; never treat a stale run or an empty game log with an `editor_errors_hint` as clean evidence.

## Done

Gameplay QA is complete only when every changed acceptance criterion has direct evidence at an appropriate seam, the game reports no relevant current-run errors, and visual criteria have visual evidence. Report instrumented live-editor evidence separately from exported-build evidence.
