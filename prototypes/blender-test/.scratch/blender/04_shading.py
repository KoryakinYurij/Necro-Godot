import bpy
import bmesh
import math

SPLIT_ANGLE = math.radians(40.0)

scene = bpy.data.scenes["NecroHero_Asset"]
depsgraph = bpy.context.evaluated_depsgraph_get()


def bake_modifiers(obj):
    """Apply the whole modifier stack (solidify/bevel) into the mesh."""
    if not len(obj.modifiers):
        return False
    depsgraph.update()
    eval_obj = obj.evaluated_get(depsgraph)
    baked = bpy.data.meshes.new_from_object(eval_obj, preserve_all_data_layers=True,
                                            depsgraph=depsgraph)
    old = obj.data
    old_name = old.name
    obj.modifiers.clear()
    obj.data = baked
    if old.users == 0:
        bpy.data.meshes.remove(old)
    baked.name = old_name
    return True


def box_project_uvs(obj):
    """Deterministic box projection so every part has a UV map."""
    mesh = obj.data
    if len(mesh.uv_layers):
        return False
    layer = mesh.uv_layers.new(name="UVMap")
    matrix = obj.matrix_world
    for poly in mesh.polygons:
        normal = poly.normal
        axis = max(range(3), key=lambda i: abs(normal[i]))
        for loop_index in poly.loop_indices:
            world = matrix @ mesh.vertices[mesh.loops[loop_index].vertex_index].co
            if axis == 0:
                uv = (world.y, world.z)
            elif axis == 1:
                uv = (world.x, world.z)
            else:
                uv = (world.x, world.y)
            layer.data[loop_index].uv = uv
    return True


def smooth_and_sharpen(obj):
    """Smooth shading everywhere, hard corners above SPLIT_ANGLE baked in."""
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for face in bm.faces:
        face.smooth = True
    sharp = []
    for edge in bm.edges:
        if len(edge.link_faces) == 2 and edge.calc_face_angle(0.0) > SPLIT_ANGLE:
            sharp.append(edge)
    if sharp:
        bmesh.ops.split_edges(bm, edges=sharp)
    bm.to_mesh(mesh)
    bm.free()
    mesh.validate(verbose=False)
    return len(sharp)


print("%-24s %-8s %6s %6s %8s %6s" % ("object", "baked", "verts", "polys", "split", "uv_new"))
totals = {"baked": 0, "split": 0, "uv": 0}
for obj in sorted(scene.objects, key=lambda o: o.name):
    if obj.type != "MESH":
        continue
    before = (len(obj.data.vertices), len(obj.data.polygons))
    baked = bake_modifiers(obj)
    uv_new = box_project_uvs(obj)
    split = smooth_and_sharpen(obj)
    totals["baked"] += int(baked)
    totals["split"] += split
    totals["uv"] += int(uv_new)
    print("%-24s %-8s %4d->%-4d %4d->%-4d %8d %6s"
          % (obj.name, "yes" if baked else "-",
             before[0], len(obj.data.vertices), before[1], len(obj.data.polygons),
             split, "yes" if uv_new else "-"))
print("totals:", totals)
print("modifiers left in scene:", [(o.name, [m.type for m in o.modifiers])
                                   for o in scene.objects if len(o.modifiers)])

bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
