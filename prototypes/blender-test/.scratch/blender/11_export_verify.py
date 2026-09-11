import bpy
import os

scene = bpy.data.scenes["NecroHero_Asset"]
root = bpy.data.objects["NH_Root"]

HERO_COLLECTION = "Agent_Generated_NecroHero"
studio_collection = bpy.data.collections["NH_Studio"]
hero_collection = bpy.data.collections.get(HERO_COLLECTION)

# --- 1. Every hero object (root, group empties, meshes) in one collection --
hero_objects = [o for o in scene.objects
                if o.name == "NH_Root" or o.name.startswith("NH_")]
hero_objects = [o for o in hero_objects if o.name not in {x.name for x in studio_collection.objects}]
moved = []
for obj in hero_objects:
    current = {c.name for c in obj.users_collection}
    if HERO_COLLECTION not in current:
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        hero_collection.objects.link(obj)
        moved.append(obj.name)
print("moved into %s: %s" % (HERO_COLLECTION, moved or "nothing"))
print("collection membership:")
for name in (HERO_COLLECTION, "NH_Studio"):
    collection = bpy.data.collections[name]
    print("  %-28s %d objects" % (name, len(collection.objects)))
stray = [o.name for o in scene.objects
         if not o.users_collection]
print("objects with no collection:", stray)

# --- 2. Drop the superseded render from the first framing pass ------------
stale = r"C:\Users\Fixed\Documents\NecroHero\renders\hero_staff_detail.png"
if os.path.exists(stale):
    os.remove(stale)
    print("removed stale render:", os.path.basename(stale))

# --- 3. Export a GLB of the character only --------------------------------
export_path = r"C:\Users\Fixed\Documents\NecroHero\necro_hero_prototype_v2.glb"
view_layer = bpy.context.view_layer
view_layer.active_layer_collection = view_layer.layer_collection.children[HERO_COLLECTION]

bpy.ops.export_scene.gltf(
    filepath=export_path,
    export_format="GLB",
    use_active_collection=True,
    use_selection=False,
    use_visible=False,
    export_apply=False,
    export_yup=True,
    export_materials="EXPORT",
    export_animations=False,
    export_cameras=False,
    export_lights=False,
    export_extras=True,
    export_normals=True,
    export_texcoords=True,
)
print("exported:", export_path, os.path.getsize(export_path), "bytes")

# --- 4. Final state report ------------------------------------------------
print("\n--- final per-object state ---")
smooth_flat = []
for obj in sorted(scene.objects, key=lambda o: o.name):
    if obj.type != "MESH":
        continue
    mesh = obj.data
    smooth = sum(1 for p in mesh.polygons if p.use_smooth)
    if smooth != len(mesh.polygons):
        smooth_flat.append((obj.name, smooth, len(mesh.polygons)))
    if len(mesh.uv_layers) == 0:
        print("  MISSING UV:", obj.name)
print("fully smooth-shaded: %d/%d meshes"
      % (len([o for o in scene.objects if o.type == "MESH"]) - len(smooth_flat),
         len([o for o in scene.objects if o.type == "MESH"])))
print("not fully smooth (expected only for hard-surface parts):", smooth_flat)

print("\nmaterials:", [m.name for m in bpy.data.materials])
print("scenes:", [s.name for s in bpy.data.scenes])
print("root custom props:", {k: root[k] for k in root.keys()})
print("frame range:", scene.frame_start, scene.frame_end, "fps", scene.render.fps)
print("images in file:", [(i.name, tuple(i.size)) for i in bpy.data.images])
print("text blocks:", [t.name for t in bpy.data.texts])

bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
