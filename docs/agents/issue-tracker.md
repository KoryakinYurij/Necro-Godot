# Issue tracker: GitHub

Specs, gates, and implementation tickets live in GitHub Issues for `KoryakinYurij/Necro-Godot`. Use `gh` from a repository clone.

## Conventions

- A spec is the parent/context source for the bounded Godot trial.
- G0 is a human approval gate, not an implementation ticket.
- `/to-tickets` produces narrow, demoable tracer-bullet implementation issues.
- Every ticket lists genuine blockers; work only an issue whose blockers are resolved.
- Use `ready-for-agent` only when the issue is self-contained and actionable.
- Use `ready-for-human` for unresolved product/gate decisions.
- Use `needs-info` for a prepared issue that still depends on unresolved input.
- Do not triage tickets created by `/to-tickets`.
- PRs are not an incoming triage surface.

## Source of truth

GitHub issues define current executable work. `docs/reference/` records evidence and historical context; it does not turn old JS work into Godot scope.