# Agent Guidance

Necro-Godot is a bounded Godot trial for the Exploration / Action Roguelite direction. Treat the JavaScript game as a behavioral reference, not as architecture to translate.

## Read before changing the project

Before planning or implementation, read in this order:

1. `CONTEXT.md` for canonical domain vocabulary.
2. Relevant accepted records in `docs/adr/`.
3. The active GitHub spec/ticket, including blockers and comments.
4. `docs/reference/js-reference.md` when behavior is being carried from the JS game.
5. `docs/agents/issue-tracker.md` when creating, resolving, or linking work.

Current GitHub issues define executable scope. Historical JS tickets and reviews are evidence only; they never silently become Godot work.

## Development environment

Godot implementation, real gameplay runs, exports, and performance evidence must run on the Windows machine. The canonical working path is `D:\Code AI\Games\Necro-Godot`.

The verified trial engine is Godot `4.7.2.stable.official.ed1daf0bf` with typed GDScript. A different engine version requires an explicit project decision before implementation continues.

The VPS may be used for documentation, GitHub coordination, review, or lightweight repository inspection. VPS results are not evidence for Godot runtime performance.

For Godot-specific skills, tests, MCP, pinned versions, and authority rules, read `docs/agents/godot-toolchain.md` before touching Godot project/tooling files.

For black-box validation of an exported Windows `.exe`—launch, screenshots, held gameplay input, restart input, recording, focus/lock aborts, or release evidence—read `.agents/skills/windows-export-playtest/SKILL.md` before choosing an automation path.

## Matt engineering skills

Use the installed global skills as process source of truth; do not copy or edit them inside this repository.

- Windows engineering skills root: `C:\Users\Fixed\.agents\skills\engineering\`
- VPS engineering skills root: `/home/fixedius/.agents/skills/`
- When routing is unclear, read `ask-matt/SKILL.md` from the active machine's engineering skills root.

Route work through the Matt flow:

- product/design shaping in this repo → `/grill-with-docs`
- stable multi-session scope → `/to-spec`, then `/to-tickets`
- implementation-ready tracer bullet → `/implement` using `/tdd` where possible, then `/code-review`
- difficult regression → `/diagnosing-bugs`
- runnable design question → `/prototype`
- external/primary-source investigation → `/research`
- agent-facing instructions → `/writing-for-agents`

Do not triage tickets produced by `/to-tickets`; they are already agent-shaped. Respect blocking edges and work only from the current frontier.

## Human decision support

The owner decides product direction, feel, priorities, and hard-to-reverse trade-offs. Agents own discoverable engineering facts and process navigation. Read `docs/agents/human-decisions.md` before asking the owner a product or architecture question.

## Trial guardrails

Build the smallest vertical slice that answers the current gate. Prefer concrete gameplay over frameworks or reusable abstractions made only for hypothetical future content.

Carry contracts, not legacy implementation. In particular preserve deterministic world description, run-local completion state, idempotent rewards/XP, Encounter activation ownership, clean restart, and modal/pause correctness where the active gate needs them.

Do not copy known JS reward-flow defects: explicitly test reward modal interaction with XP/level-up, repeated activation/clicks, and application after restart when Ruins enters scope.

For every implementation gate report separately: commit/PR SHA, exact Godot version, commands actually run and their results, accessible exported build, real gameplay recording, and the machine/conditions used for any load claim. Never present an unexecuted check as evidence.

## Agent skills

### Issue tracker

Specs and tickets live in GitHub Issues for `KoryakinYurij/Necro-Godot`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the canonical Matt triage labels mapped one-to-one in GitHub. See `docs/agents/triage-labels.md`.

### Domain docs

This repository uses a single domain context with root `CONTEXT.md` and accepted decisions under `docs/adr/`. See `docs/agents/domain.md`.