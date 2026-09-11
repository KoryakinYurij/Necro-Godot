import bpy
import mathutils
import time

# --- 0. Snapshot the live (unsaved) session so nothing is lost -------------
stamp = time.strftime("%Y%m%d-%H%M%S")
snapshot = r"C:\Users\Fixed\Documents\NecroHero\necro_hero_prototype.live-snapshot-%s.blend" % stamp
try:
    bpy.ops.wm.save_as_mainfile(filepath=snapshot, copy=True, compress=False)
    print("live snapshot written:", snapshot)
except Exception as exc:
    print("snapshot failed (continuing):", exc)

# --- undo bookmark so the whole polish pass can be reverted with Ctrl+Z ----
try:
    bpy.ops.ed.undo_push(message="NH: hero polish")
    print("undo bookmark pushed")
except Exception as exc:
    print("undo_push skipped:", exc)

# NOTE: inside a bpy.app.timers callback bpy.context has no `windows`/`window`,
# so window access goes through the window managers instead.
windows = [w for wm in bpy.data.window_managers for w in wm.windows]

# --- 1. Drop the leftover default scene (Cube/Camera/Light leftovers) ------
if "Scene" in bpy.data.scenes and "NecroHero_Asset" in bpy.data.scenes:
    junk = bpy.data.scenes["Scene"]
    leftovers = [o.name for o in junk.objects]
    bpy.data.scenes.remove(junk)
    print("removed leftover scene 'Scene', objects:", leftovers)

scene = bpy.data.scenes["NecroHero_Asset"]
for window in windows:
    if window.scene != scene:
        window.scene = scene
print("scenes now:", [s.name for s in bpy.data.scenes], "| windows on scene:", len(windows))

try:
    print("orphans purged:", bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True,
                                                    do_recursive=True))
except Exception as exc:
    print("orphan purge failed:", exc)


def world_bounds(objects):
    xs, ys, zs = [], [], []
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            w = obj.matrix_world @ mathutils.Vector(corner)
            xs.append(w.x)
            ys.append(w.y)
            zs.append(w.z)
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def tri_count(objects):
    total = 0
    for obj in objects:
        if obj.type == "MESH":
            total += sum(len(p.vertices) - 2 for p in obj.data.polygons)
    return total


# --- 2. Ground the asset, keeping the pivot at the feet --------------------
root = bpy.data.objects["NH_Root"]
meshes = [o for o in scene.objects if o.type == "MESH"]
(_, _), (_, _), (z_before, _) = world_bounds(meshes)
if abs(z_before) > 1e-4:
    shift = mathutils.Matrix.Translation((0.0, 0.0, -z_before))
    for obj in meshes:
        obj.matrix_world = shift @ obj.matrix_world
    bpy.context.view_layer.update()
(x0, x1), (y0, y1), (z0, z1) = world_bounds(meshes)
print("grounded: shift %.4f | bounds x(%.3f..%.3f) y(%.3f..%.3f) z(%.3f..%.3f)"
      % (-z_before, x0, x1, y0, y1, z0, z1))
print("root origin:", tuple(round(v, 3) for v in root.matrix_world.translation))
print("total height incl. staff: %.3f | triangles: %d" % (z1 - z0, tri_count(meshes)))

# --- 3. Group rigid parts under semantic empties ---------------------------
def ensure_empty(name, parent):
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        scene.collection.objects.link(obj)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.25
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = parent.matrix_world.copy()
    return obj


def reparent(child, parent):
    world = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    child.matrix_world = world


body = ensure_empty("NH_Body", root)
staff = ensure_empty("NH_Staff_Root", root)
wisps = ensure_empty("NH_Wisps_Root", root)
wisp1 = ensure_empty("NH_Wisp_1_Root", wisps)
wisp2 = ensure_empty("NH_Wisp_2_Root", wisps)

WISP_1 = ("NH_Wisp_1", "NH_Wisp_Core_1", "NH_Wisp_Tail_1")
WISP_2 = ("NH_Wisp_2", "NH_Wisp_Core_2", "NH_Wisp_Tail_2")

moved = {"body": [], "staff": [], "wisp_1": [], "wisp_2": []}
for obj in meshes:
    if obj.name.startswith("NH_Staff"):
        reparent(obj, staff)
        moved["staff"].append(obj.name)
    elif obj.name in WISP_1:
        reparent(obj, wisp1)
        moved["wisp_1"].append(obj.name)
    elif obj.name in WISP_2:
        reparent(obj, wisp2)
        moved["wisp_2"].append(obj.name)
    else:
        reparent(obj, body)
        moved["body"].append(obj.name)
for group, names in moved.items():
    print("group %-7s %2d parts" % (group, len(names)))

# --- 4. Name mesh datablocks after their objects ---------------------------
renamed = 0
for obj in scene.objects:
    if obj.type == "MESH" and obj.data.name != obj.name:
        obj.data.name = obj.name
        renamed += 1
print("mesh datablocks renamed:", renamed)

# --- 5. Asset custom properties -------------------------------------------
body_meshes = [o for o in scene.objects if o.type == "MESH" and not o.name.startswith("NH_Staff")]
(_, _), (_, _), (_, body_top) = world_bounds(body_meshes)
parts = len(meshes)
tris = tri_count(meshes)
props = {
    "nh_asset": "Necro Hero",
    "nh_asset_version": "2.0",
    "nh_units": "meters (unit scale 1.0)",
    "nh_total_height_units": round(z1 - z0, 3),
    "nh_character_height_units": round(body_top, 3),
    "nh_facing": "-Y front / +Z up",
    "nh_parts": parts,
    "nh_triangles": tris,
    "nh_export_note": "Exclude collection 'NH_Studio' (camera, lights, floor) from game exports.",
}
for key, value in props.items():
    root[key] = value
print("custom props on NH_Root:", props)

# --- 6. Embedded documentation -------------------------------------------
readme = bpy.data.texts.get("README_NH_Hero") or bpy.data.texts.new("README_NH_Hero")
readme.clear()
readme.write(
    "NECRO HERO - character asset (built in Blender %s)\n"
    "================================================\n\n"
    "Hierarchy (root object: NH_Root, pivot at ground contact, z = 0)\n"
    "  NH_Body          robe, mantle, belt, sashes, arms, hands, shoulders,\n"
    "                   hood, skull/face, teeth, gold trim, pouch, runes\n"
    "  NH_Staff_Root    staff, grip, skull lantern, cage, flame\n"
    "  NH_Wisps_Root\n"
    "    NH_Wisp_1_Root wisp body + core + tail\n"
    "    NH_Wisp_2_Root wisp body + core + tail\n\n"
    "Collection NH_Studio holds the preview camera, the 3-point light rig, the\n"
    "camera target and the backdrop floor. It is not part of the character -\n"
    "exclude it from game exports (disable the collection in the view layer, or\n"
    "export visible-only).\n\n"
    "Facts\n"
    "-----\n"
    "* %d mesh parts, %d triangles, rigid-parented to the empties above: this is a\n"
    "  prop-assembled low-poly build, not a deforming character.\n"
    "* Facing -Y, up +Z, 1 unit = 1 m. Height and triangle count are stored as\n"
    "  custom properties on NH_Root.\n"
    "* Materials are stylised PBR with procedural micro-detail (noise / voronoi\n"
    "  bump). Procedural node detail does NOT survive a glTF export - only base\n"
    "  colour, metallic, roughness and emission do. Bake to textures if the\n"
    "  engine needs the detail.\n"
    "* Shading is smooth with sharp edges by angle (30 deg), baked into the mesh\n"
    "  so Blender, glTF and the engine agree.\n"
    "* Preview stills: Documents/NecroHero/renders, shot with camera\n"
    "  NH_Preview_Cam, which tracks the empty NH_Cam_Target.\n"
    % (bpy.app.version_string, parts, tris)
)
print("README_NH_Hero written (%d chars)" % len(readme.as_string()))

bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
