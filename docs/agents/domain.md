# Domain Docs

This repository uses a single domain context.

## Before planning or implementation

1. Read root `CONTEXT.md` for canonical game vocabulary.
2. Read accepted ADRs in `docs/adr/` that touch the active gate.
3. Read the active GitHub issue and its blockers/comments.
4. Read `docs/reference/js-reference.md` only when the issue carries behavior from the JavaScript game.

## Writing rules

- `CONTEXT.md` is a glossary, not an implementation plan.
- ADRs record hard-to-reverse, non-obvious decisions after a real trade-off.
- Current implementation scope belongs in GitHub issues.
- Execution evidence belongs on the relevant issue/PR or release artifact.
- Historical JS issues/reviews are reference material only.
- If new scope conflicts with an accepted ADR, surface the conflict explicitly rather than silently overriding it.