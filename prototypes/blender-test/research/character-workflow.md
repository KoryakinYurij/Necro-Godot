# Character Asset Workflow

## Purpose

Reusable Blender → review → game-check loop for character prototypes. This is intentionally small: it standardizes the order of work and evidence without introducing an asset-management framework.

Before starting, read the active issue/spec and any accepted ADR that actually chooses the target representation. Do not infer a permanent 3D-versus-prerendered-2D decision from one prototype.

## Gate 0 — Brief and target

**Input:** active scope plus the intended gameplay use.

Record only what changes the asset work:
- target representation/output for this experiment;
- gameplay camera and approximate on-screen size;
- required poses/actions/animations;
- identifying silhouette/material features;
- references for anatomy, clothing, props, and difficult contacts.

**Done when:** another agent can tell what must be visible and testable in game without inventing requirements.

**Return when:** the target representation or required gameplay use is genuinely undecided and changes the work substantially.

## Gate 1 — Neutral blockout

Build the major masses first: head, torso, limbs, clothing mass, major prop/weapon. Use neutral materials and minimal effects.

Capture front, back, both sides, three-quarter, and the intended gameplay camera/scale.

**Done when:** proportions and large silhouette work without material polish.

**Return when:** the character identity depends on hiding a weak form with lighting, bloom, texture detail, or camera tricks.

## Gate 2 — Silhouette and contact construction

Before detail, solve joints and interactions as systems. For held props verify shoulder/elbow/wrist/palm alignment, grip direction, thumb/finger sides, and clothing/prop clearance.

After any large-form edit, run a dependency cleanup over clothing, belts, attachments, accessories, and nearby geometry.

**Done when:** the silhouette and all important contacts survive multi-angle diagnostic review.

**Return when:** a relation is only plausible from one camera or only because intersecting geometry hides it.

## Gate 3 — Motion/deformation proof

If the target needs rigging or animation, test representative poses or a rough required action before final material/detail work. Use the actual intended skeleton/export path where practical.

**Done when:** the critical joints deform acceptably and a rough motion survives a round-trip into the target context.

**Return when:** implementation/export changes the pose, bone behavior, orientation, or timing enough to invalidate the Blender-only review.

## Gate 4 — Material transfer proof

For a 3D path, test a small representative set of actual material classes through the real export/import route before complex polish. Typical probes include cloth/skin, bone, metal, transparency if needed, and emission.

**Done when:** the Godot result is understood and any unsupported effect has an explicit replacement/bake strategy.

**Return when:** a look depends on Blender-only node behavior that is lost or materially changed after export.

## Gate 5 — Polish

Add final materials, secondary forms, decorative elements, and presentation only after the construction gates pass.

Keep diagnostic views available. A beauty render supplements them; it never replaces them.

**Done when:** polish improves an already-correct asset without reintroducing silhouette, intersection, or readability defects.

## Gate 6 — Publish from the saved source

Start from the declared current `.blend`, not from accidental Blender UI state. The publish/check procedure should use project-relative paths where possible and should not accumulate duplicates or silently mutate the working source.

Produce the game-facing file(s) and review evidence from the same source state. If a structural glTF check is useful, use Khronos glTF Validator rather than creating a project-specific validator.

**Done when:** source and output are unambiguous and publishing can be repeated from a fresh Blender session.

## Gate 7 — Verify the published result in Godot

Test the **exported result**, not only the Blender scene. Check the properties relevant to its target: scale, orientation, ground/pivot, material appearance, silhouette at gameplay size, rig/animation, and any import warnings.

**Done when:** the game-facing output works in its target Godot context and the evidence identifies what was actually tested.

## Handoff

Record the current source, published output, review evidence, known limitations, and the next meaningful action. Keep asset-specific details in the asset handoff/README; keep reusable failures and rules in `asset-production-lessons.md`.

Do not build extra pipeline infrastructure just because a manual step exists. Promote a repeated pain point into reusable tooling only after the same need has appeared across multiple assets or is already blocking reliable publication.
