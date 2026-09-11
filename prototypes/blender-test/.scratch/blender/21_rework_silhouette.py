import bpy
import bmesh
import math
from mathutils import Matrix, Vector

scene = bpy.data.scenes["NecroHero_Asset"]
body = bpy.data.objects["NH_Body"]
root = bpy.data.objects["NH_Root"]

FRONT_SHOULDER = Vector((0.370, -0.109, 1.809))
FRONT_WRIST = Vector((0.690, -0.131, 1.193))


def reset_object(obj):
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    obj.parent = body
    obj.matrix_parent_inverse = body.matrix_world.inverted()
    obj.matrix_world = Matrix.Identity(4)


def replace_pydata(obj, verts, faces, material):
    reset_object(obj)
    mesh = bpy.data.meshes.new(obj.name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    old = obj.data
    obj.data = mesh
    mesh.materials.append(material)
    if old and old.users == 0:
        bpy.data.meshes.remove(old)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for face in bm.faces:
        face.smooth = True
    bm.to_mesh(mesh)
    bm.free()
    if not len(mesh.uv_layers):
        uv = mesh.uv_layers.new(name="UVMap")
        xs = [v.co.x for v in mesh.vertices] or [0.0, 1.0]
        zs = [v.co.z for v in mesh.vertices] or [0.0, 1.0]
        dx = max(max(xs) - min(xs), 1e-6)
        dz = max(max(zs) - min(zs), 1e-6)
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                co = mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv = ((co.x - min(xs)) / dx, (co.z - min(zs)) / dz)
    return obj


def radial_shell(rings, segments=12, cap_top=True, cap_bottom=True):
    verts, faces = [], []
    for z, rx, ry, cy in rings:
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            verts.append((rx * math.cos(a), cy + ry * math.sin(a), z))
    for r in range(len(rings) - 1):
        a0 = r * segments
        b0 = (r + 1) * segments
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((a0 + i, a0 + j, b0 + j, b0 + i))
    if cap_bottom:
        faces.append(tuple(reversed(range(segments))))
    if cap_top:
        start = (len(rings) - 1) * segments
        faces.append(tuple(start + i for i in range(segments)))
    return verts, faces


def prism_parts(parts):
    verts, faces = [], []
    for center, outline, depth in parts:
        base = len(verts)
        cx, cy, cz = center
        n = len(outline)
        for y in (cy - depth * 0.5, cy + depth * 0.5):
            for x, z in outline:
                verts.append((cx + x, y, cz + z))
        faces.append(tuple(base + i for i in reversed(range(n))))
        faces.append(tuple(base + n + i for i in range(n)))
        for i in range(n):
            j = (i + 1) % n
            faces.append((base + i, base + j, base + n + j, base + n + i))
    return verts, faces


def basis_from(normal, hint=(0.0, 0.0, 1.0)):
    n = Vector(normal).normalized()
    h = Vector(hint)
    if abs(n.dot(h)) > 0.95:
        h = Vector((0.0, 1.0, 0.0))
    t1 = h.cross(n).normalized()
    t2 = n.cross(t1).normalized()
    return Matrix((t1, t2, n)).transposed()


def ellipsoid(bm, center, radii, u=12, v=8):
    matrix = Matrix.Translation(center) @ Matrix.Diagonal(Vector((radii[0], radii[1], radii[2], 1.0)))
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0, matrix=matrix, calc_uvs=True)


def capsule(bm, p0, p1, r0, r1, segments=8):
    p0, p1 = Vector(p0), Vector(p1)
    delta = p1 - p0
    if delta.length < 1e-5:
        return
    quat = delta.to_track_quat("Z", "Y")
    matrix = Matrix.Translation((p0 + p1) * 0.5) @ quat.to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=r0, radius2=r1, depth=delta.length,
                          matrix=matrix, calc_uvs=True)


def replace_bmesh(obj, bm, material):
    reset_object(obj)
    mesh = bpy.data.meshes.new(obj.name)
    bm.to_mesh(mesh)
    bm.free()
    old = obj.data
    obj.data = mesh
    mesh.materials.append(material)
    if old and old.users == 0:
        bpy.data.meshes.remove(old)
    bm2 = bmesh.new()
    bm2.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces)
    for face in bm2.faces:
        face.smooth = True
    bm2.to_mesh(mesh)
    bm2.free()
    mesh.validate(verbose=False)
    mesh.update()
    return obj


# ---------------------------------------------------------------- robe
robe_rings = [
    (0.060, 0.690, 0.445, -0.010),
    (0.450, 0.665, 0.430, -0.010),
    (0.950, 0.610, 0.395, -0.005),
    (1.300, 0.545, 0.355, 0.000),
    (1.560, 0.490, 0.320, 0.005),
    (1.760, 0.435, 0.285, 0.010),
]
verts, faces = radial_shell(robe_rings, segments=14, cap_top=True, cap_bottom=True)
replace_pydata(bpy.data.objects["NH_Ragged_Robe"], verts, faces, bpy.data.materials["NH_Robe"])
print("robe rebuilt: coherent tapered shell")

# ----------------------------------------------------------- upper mantle
mantle_rings = [
    (1.475, 0.470, 0.305, 0.000),
    (1.610, 0.515, 0.335, -0.005),
    (1.735, 0.475, 0.305, 0.000),
]
verts, faces = radial_shell(mantle_rings, segments=14, cap_top=False, cap_bottom=False)
replace_pydata(bpy.data.objects["NH_Upper_Mantle"], verts, faces,
               bpy.data.materials["NH_Robe_Light"])
print("mantle rebuilt: short shoulder cape, no chest bulge")

# -------------------------------------------------------------- pauldron
plate_top = [
    (-0.135, -0.040), (-0.105, 0.055), (-0.015, 0.095),
    (0.105, 0.060), (0.145, -0.015), (0.085, -0.075),
    (-0.070, -0.078),
]
plate_lower = [
    (-0.115, -0.035), (-0.082, 0.048), (0.020, 0.072),
    (0.118, 0.025), (0.100, -0.058), (-0.020, -0.080),
]
parts = [
    ((0.392, -0.112, 1.845), plate_top, 0.165),
    ((0.455, -0.116, 1.710), plate_lower, 0.145),
]
verts, faces = prism_parts(parts)
replace_pydata(bpy.data.objects["NH_Pauldron"], verts, faces,
               bpy.data.materials["NH_Bone_High"])
print("pauldron rebuilt: two flat overlapping plates over shoulder joint")

# ------------------------------------------------------------ staff hand
staff = bpy.data.objects["NH_Staff"]
grip = bpy.data.objects["NH_Staff_Grip"]
def bounds(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return (min(p.x for p in pts), max(p.x for p in pts),
            min(p.y for p in pts), max(p.y for p in pts),
            min(p.z for p in pts), max(p.z for p in pts))

sb = bounds(staff)
gb = bounds(grip)
staff_x = (sb[0] + sb[1]) * 0.5
staff_y = (sb[2] + sb[3]) * 0.5
grip_z = (gb[4] + gb[5]) * 0.5
front_y = gb[2] - 0.010

palm_center = Vector((staff_x - 0.090, staff_y + 0.040, grip_z - 0.004))
bm = bmesh.new()
ellipsoid(bm, palm_center, (0.073, 0.055, 0.066), u=12, v=8)
# Wrist bridge follows the forearm into the palm instead of flipping away from it.
capsule(bm, FRONT_WRIST - Vector((0.010, 0.0, 0.000)),
        palm_center - Vector((0.035, 0.000, 0.000)), 0.043, 0.052, segments=10)

finger_z = [grip_z + 0.037, grip_z + 0.012, grip_z - 0.013, grip_z - 0.038]
for i, z in enumerate(finger_z):
    r = 0.019 - i * 0.001
    p0 = Vector((palm_center.x + 0.022, palm_center.y - 0.025, z))
    p1 = Vector((staff_x - 0.030, front_y, z - 0.002))
    p2 = Vector((staff_x + 0.034, front_y + 0.003, z - 0.006))
    capsule(bm, p0, p1, r, r * 0.92, segments=8)
    capsule(bm, p1, p2, r * 0.92, r * 0.78, segments=8)
    ellipsoid(bm, p1, (r * 1.05, r * 1.05, r * 1.05), u=8, v=5)

# Thumb crosses diagonally over the front of the grip, clearly opposite the fingers.
t0 = palm_center + Vector((-0.005, -0.025, 0.050))
t1 = Vector((staff_x - 0.025, front_y - 0.004, grip_z + 0.035))
t2 = Vector((staff_x + 0.030, front_y + 0.006, grip_z + 0.006))
capsule(bm, t0, t1, 0.024, 0.021, segments=8)
capsule(bm, t1, t2, 0.021, 0.016, segments=8)
ellipsoid(bm, t1, (0.022, 0.022, 0.022), u=8, v=5)

replace_bmesh(bpy.data.objects["NH_Hand_Front"], bm,
              bpy.data.materials["NH_Bone_High"])
print("front hand rebuilt around staff at", tuple(round(v, 3) for v in palm_center))

# ----------------------------------------------------------- verification
print("\n=== silhouette verification ===")
for name in ("NH_Ragged_Robe", "NH_Upper_Mantle", "NH_Pauldron", "NH_Arm_Front",
             "NH_Arm_Front_Cuff", "NH_Hand_Front", "NH_Staff_Grip"):
    obj = bpy.data.objects[name]
    b = bounds(obj)
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    print("%-20s tris %4d | x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f"
          % (name, tris, b[0], b[1], b[2], b[3], b[4], b[5]))

# Hand must bridge the wrist and overlap the staff grip in X/Z while staying in front.
hb = bounds(bpy.data.objects["NH_Hand_Front"])
print("hand/staff overlap x=%.3f z=%.3f; hand front y=%.3f grip front y=%.3f"
      % (max(0.0, min(hb[1], gb[1]) - max(hb[0], gb[0])),
         max(0.0, min(hb[5], gb[5]) - max(hb[4], gb[4])), hb[2], gb[2]))

scene_tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
                 for o in scene.objects if o.type == "MESH" and o.name.startswith("NH_")
                 and not o.name.startswith("NH_Studio"))
root["nh_triangles"] = scene_tris
root["nh_rework_note"] = "2026-09-11: staff hand, shoulder plates, mantle and robe silhouette rebuilt"
print("scene triangles:", scene_tris)

bpy.context.view_layer.update()
bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
