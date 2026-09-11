# Blender Asset Production — lessons from Necro Hero

## Purpose

This note captures reusable lessons from the first Necro Hero Blender experiment. It is research evidence, not an ADR, gameplay scope, or a claim that the current prototype pipeline is final.

Use each lesson as: **situation → observed failure → rule → verification**. Prefer direct visual or runtime evidence over recollection.

## 1. Numeric correctness is not visual correctness

**Situation.** Checks such as `hand intersects staff`, bounding boxes, and object overlap were useful during the hero iterations.

**Observed failure.** A hand could technically intersect the staff while the palm, thumb, wrist, and finger wrap still formed an impossible grip. The same happened with the shoulder and pauldron: valid coordinates did not make the part look worn correctly.

**Rule.** Numeric QA is supporting evidence, not authority for anatomy, silhouette, or visual contact.

**Verification.** Inspect the contact zone from multiple diagnostic angles at close range. For a hand-held object explicitly verify palm orientation, wrist direction, thumb side, four-finger side, and the path of the grip.

## 2. Beauty renders hide construction defects

**Situation.** Full renders used lighting, bloom, material contrast, and the staff itself to compose an attractive image.

**Observed failure.** Incorrect hand and shoulder construction looked acceptable at normal presentation scale and became obvious only in close-up.

**Rule.** Every visually important asset needs diagnostic views separate from presentation renders.

**Verification.** Review neutral front/back/side/three-quarter views, the intended game camera/scale, and close-ups of every known problem area before approving polish.

## 3. Contact zones are one system

**Situation.** Arm, hand, staff, cuff, shoulder, and pauldron were edited as separate objects.

**Observed failure.** Each object could be locally plausible while the assembled pose was not.

**Rule.** Solve the construction of a contact zone before adding detail: shoulder → elbow → wrist → palm axis, contact surface, finger sides, and clearance between body, clothing, and prop.

**Verification.** Show the assembled zone from several angles with effects disabled. If the relationship cannot be explained spatially, it is not ready for detail.

## 4. Large-form changes require a dependency cleanup pass

**Situation.** The robe/body changed substantially while belt, sashes, and nearby accessories were inherited from an earlier shape.

**Observed failure.** The belt became buried in the robe and old pieces protruded as unexplained geometry; long sashes damaged the silhouette even though their objects were technically intact.

**Rule.** After changing a major form, re-check every dependent or adjacent detail before continuing.

**Verification.** Inspect clothing layers, belt, attachments, accessories, intersections, and silhouette. A part is either intentionally visible and seated correctly or intentionally absent/hidden.

## 5. Silhouette comes before decoration

**Situation.** Materials and effects could make the hero feel more finished while the large masses were still unresolved.

**Observed failure.** Decorative work did not compensate for weak robe shape, shoulder massing, or dangling elements.

**Rule.** Work in the order: large forms → silhouette → joints/contacts → motion/deformation → materials → decorative polish.

**Verification.** The character must read in a neutral material and at approximate game size before beauty work becomes a gate.

## 6. A successful export is not game readiness

**Situation.** A `.glb` can be structurally valid and still look or behave differently in Godot.

**Rule.** Treat Blender review, file validation, and target-engine review as different gates.

**Verification.** Validate the exported asset structurally when useful, then import the exact exported result into the target Godot scene and inspect scale, orientation, materials, skeleton/animation if present, and game-camera readability.

## 7. Keep working source separate from published game data

**Situation.** A `.blend` contains editing helpers, references, diagnostics, and other data that should not necessarily enter the game.

**Rule.** The editable `.blend` is the source; game-facing output is an explicit publication from that source. Direct `.blend` import may be technically possible, but it should not erase the distinction between working state and released asset state.

**Verification.** A reviewer can identify the current source, the exact published output, and which source revision produced it without guessing from Blender session state.

## 8. Historical scripts are evidence, not automatically a build recipe

**Situation.** Necro Hero accumulated many numbered scripts while specific defects were corrected.

**Observed failure risk.** A future agent could assume the numbering is a clean end-to-end generator and run stateful correction scripts in sequence against the wrong scene.

**Rule.** Classify scripts by purpose: historical iteration, asset-specific tool, or reusable operation. Only a procedure tested from its declared starting state may be called reproducible.

**Verification.** Run the documented publish/check path from a fresh Blender session using the saved source. Do not claim clean-scene reconstruction unless that separate path has also been executed successfully.

## 9. Test material transfer before material polish

**Situation.** Blender can represent material node setups that are not reproduced one-for-one by glTF and Godot.

**Rule.** For a 3D publication path, test representative material classes early (for example cloth, bone/skin, metal, emission) before investing in complex final shading.

**Verification.** Export a small representative sample through the real path and judge it under Godot lighting. Bake or replace unsupported effects deliberately instead of discovering the mismatch after final polish.

## External evidence

These project lessons are consistent with primary-source guidance:

- Blender Studio DOGWALK separated editable Blender work from an explicit glTF publishing step and warns that its custom Blender/Godot exchange code was an internal prototype, not a general product: https://studio.blender.org/blog/our-workflow-with-blender-and-godot/
- DOGWALK animation used a cyclic rough-blocking → Godot implementation test → polish loop, exposing export/rig problems during gameplay testing: https://studio.blender.org/blog/animations-for-dogwalk/
- Blender's glTF exporter constructs materials from supported/recognized material patterns rather than promising arbitrary node-tree equivalence: https://docs.blender.org/manual/en/5.2/addons/scene_gltf2.html
- Godot recommends glTF/GLB for 3D scene exchange and recommends judging lighting in Godot because engines can render it differently: https://docs.godotengine.org/en/4.7/tutorials/assets_pipeline/importing_3d_scenes/model_export_considerations.html
- Khronos glTF Validator checks glTF/GLB structural/spec correctness; it is not an artistic-quality gate: https://github.com/KhronosGroup/glTF-Validator

## How to add a future lesson

Add a lesson only when there is reusable evidence. Record the observed failure, the rule it changes, and the concrete check that would catch the same class of problem earlier next time. Prefer an error/fix image pair or runtime evidence over a long transcript.
