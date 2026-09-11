import bpy
import bmesh
import math
from mathutils import Matrix, Vector

scene = bpy.data.scenes["NecroHero_Asset"]
COLLECTION = bpy.data.collections["Agent_Generated_NecroHero"]
body = bpy.data.objects["NH_Body"]
root = bpy.data.objects["NH_Root"]

# Joint frames measured from the original arm meshes (world space). Hardcoded so
# the rebuild is idempotent whatever transforms the objects currently carry.
FRONT_SHOULDER = Vector((0.370, -0.109, 1.809))
FRONT_WRIST = Vector((0.690, -0.131, 1.193))
BACK_SHOULDER = Vector((-0.279, 0.076, 1.729))
BACK_WRIST = Vector((-0.561, -0.116, 1.193))

# --- 0. Meshes are authored in world space, so transforms must be identity --
for name in ("NH_Hand_Front", "NH_Hand_Back", "NH_Arm_Front", "NH_Arm_Back",
             "NH_Pauldron", "NH_Arm_Front_Cuff", "NH_Arm_Back_Cuff"):
    obj = bpy.data.objects.get(name)
    if obj is None:
        continue
    if tuple(round(v, 6) for v in obj.location) != (0.0, 0.0, 0.0):
        print("resetting transform on", name, tuple(round(v, 3) for v in obj.location),
              tuple(round(v, 3) for v in obj.scale))
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    obj.delta_location = (0.0, 0.0, 0.0)
    obj.delta_rotation_euler = (0.0, 0.0, 0.0)
    obj.delta_rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    obj.delta_scale = (1.0, 1.0, 1.0)
    obj.parent = body
    obj.matrix_parent_inverse = body.matrix_world.inverted()
    obj.matrix_world = Matrix.Identity(4)

# --- helpers --------------------------------------------------------------
def object_world_bounds(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return (min(c.x for c in corners), max(c.x for c in corners),
            min(c.y for c in corners), max(c.y for c in corners),
            min(c.z for c in corners), max(c.z for c in corners))


def basis_from(normal, hint=(0.0, 0.0, 1.0)):
    n = Vector(normal).normalized()
    hint = Vector(hint)
    if abs(n.dot(hint)) > 0.95:
        hint = Vector((0.0, 1.0, 0.0))
    t1 = hint.cross(n).normalized()
    t2 = n.cross(t1).normalized()
    return Matrix((t1, t2, n)).transposed()


def ellipsoid(bm, center, basis, radii, u=10, v=6):
    matrix = (Matrix.Translation(center) @ basis.to_4x4()
              @ Matrix.Diagonal(Vector((radii[0], radii[1], radii[2], 1.0))))
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0,
                              matrix=matrix, calc_uvs=True)


def box(bm, center, basis, half):
    matrix = (Matrix.Translation(center) @ basis.to_4x4()
              @ Matrix.Diagonal(Vector((half[0], half[1], half[2], 1.0))))
    bmesh.ops.create_cube(bm, size=2.0, matrix=matrix, calc_uvs=True)


def capsule(bm, p0, p1, r0, r1, segments=6):
    p0, p1 = Vector(p0), Vector(p1)
    delta = p1 - p0
    length = delta.length
    if length < 1e-5:
        return
    quat = delta.to_track_quat("Z", "Y")
    matrix = Matrix.Translation((p0 + p1) / 2) @ quat.to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=r0, radius2=r1, depth=length, matrix=matrix, calc_uvs=True)


def finish_mesh(obj, split_angle=math.radians(40.0)):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for face in bm.faces:
        face.smooth = True
    sharp = [e for e in bm.edges
             if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > split_angle]
    if sharp:
        bmesh.ops.split_edges(bm, edges=sharp)
    bm.to_mesh(mesh)
    bm.free()
    mesh.validate(verbose=False)
    if not len(mesh.uv_layers):
        layer = mesh.uv_layers.new(name="UVMap")
        for poly in mesh.polygons:
            axis = max(range(3), key=lambda i: abs(poly.normal[i]))
            for loop_index in poly.loop_indices:
                co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
                uv = (co.y, co.z) if axis == 0 else (co.x, co.z) if axis == 1 else (co.x, co.y)
                layer.data[loop_index].uv = uv


def write_mesh(obj, bm, material):
    mesh = bpy.data.meshes.new(obj.name)
    bm.to_mesh(mesh)
    bm.free()
    old = obj.data
    obj.data = mesh
    mesh.materials.clear()
    mesh.materials.append(material)
    if old.users == 0:
        bpy.data.meshes.remove(old)
    finish_mesh(obj)
    return obj


def make_object(name, bm, material):
    existing = bpy.data.objects.get(name)
    if existing is not None:
        return write_mesh(existing, bm, material)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    COLLECTION.objects.link(obj)
    obj.parent = body
    obj.matrix_parent_inverse = body.matrix_world.inverted()
    obj.matrix_world = Matrix.Identity(4)
    finish_mesh(obj)
    return obj


# --- measured staff ------------------------------------------------------
staff_bounds = object_world_bounds(bpy.data.objects["NH_Staff"])
grip_bounds = object_world_bounds(bpy.data.objects["NH_Staff_Grip"])
staff_xy = Vector(((staff_bounds[0] + staff_bounds[1]) / 2, (staff_bounds[2] + staff_bounds[3]) / 2))
grip_radius = (grip_bounds[1] - grip_bounds[0]) / 2
grip_z = (grip_bounds[4] + grip_bounds[5]) / 2
print("staff xy %s grip radius %.3f grip z %.3f"
      % (tuple(round(v, 3) for v in staff_xy), grip_radius, grip_z))

# --- pauldron ------------------------------------------------------------
arm_axis = (FRONT_WRIST - FRONT_SHOULDER).normalized()
outward = arm_axis.cross(Vector((0.0, 1.0, 0.0))).normalized()
if outward.x < 0:
    outward = -outward
tangent = outward.cross(arm_axis).normalized()

bm = bmesh.new()
for offset, radii, tilt_deg in ((0.028, (0.150, 0.130, 0.042), 6.0),
                                (0.112, (0.134, 0.116, 0.038), 22.0),
                                (0.194, (0.114, 0.098, 0.032), 40.0)):
    center = FRONT_SHOULDER + arm_axis * offset + outward * 0.012
    tilt = Matrix.Rotation(math.radians(tilt_deg), 4, tangent)
    basis = (tilt @ basis_from(arm_axis).to_4x4()).to_3x3()
    ellipsoid(bm, center, basis, radii, u=16, v=10)
claw_base = FRONT_SHOULDER + arm_axis * 0.012 + outward * 0.058
capsule(bm, claw_base, claw_base + outward * 0.080 + arm_axis * -0.040, 0.023, 0.004,
        segments=8)
pauldron = make_object("NH_Pauldron", bm, bpy.data.materials["NH_Bone_High"])
for name in ("NH_Bone_Shoulder_1", "NH_Bone_Shoulder_2", "NH_Bone_Shoulder_3"):
    obj = bpy.data.objects.get(name)
    if obj is not None:
        bpy.data.objects.remove(obj, do_unlink=True)
        print("removed old shoulder sphere:", name)

# --- gripping hand -------------------------------------------------------
WRAP = grip_radius + 0.012
PALM_ANGLE = math.radians(180.0)
palm_out = Vector((math.cos(PALM_ANGLE), math.sin(PALM_ANGLE), 0.0))
palm_center = Vector((staff_xy.x, staff_xy.y, grip_z)) + palm_out * (grip_radius + 0.026)
palm_basis = basis_from(palm_out)

bm = bmesh.new()
box(bm, palm_center, palm_basis, (0.052, 0.060, 0.023))
box(bm, palm_center - palm_out * 0.046, palm_basis, (0.040, 0.050, 0.024))

finger_z = [grip_z + 0.036, grip_z + 0.012, grip_z - 0.012, grip_z - 0.036]
for index, z in enumerate(finger_z):
    radius = 0.022 - index * 0.001
    start = math.radians(200.0 + index * 2.0)
    sweep = math.radians(47.0)
    previous = None
    for step in range(3):
        a0, a1 = start + step * sweep, start + (step + 1) * sweep
        p0 = Vector((staff_xy.x + WRAP * math.cos(a0), staff_xy.y + WRAP * math.sin(a0), z))
        p1 = Vector((staff_xy.x + WRAP * math.cos(a1), staff_xy.y + WRAP * math.sin(a1), z))
        r0 = radius * (1.0 - 0.10 * step)
        r1 = radius * (1.0 - 0.10 * (step + 1))
        capsule(bm, p0, p1, r0, r1, segments=6)
        if step:
            ellipsoid(bm, p0, basis_from((0, 0, 1)), (r0 * 1.06,) * 3, 8, 5)
        previous = p1
    ellipsoid(bm, previous, basis_from((0, 0, 1)), (radius * 0.82,) * 3, 8, 5)
    ellipsoid(bm, palm_center + palm_out * 0.014 + Vector((0, 0, z - grip_z)), palm_basis,
              (0.030, 0.026, 0.023), 10, 6)

thumb_z = grip_z + 0.058
for step in range(2):
    a0 = math.radians(168.0 - step * 46.0)
    a1 = math.radians(168.0 - (step + 1) * 46.0)
    p0 = Vector((staff_xy.x + WRAP * math.cos(a0), staff_xy.y + WRAP * math.sin(a0), thumb_z))
    p1 = Vector((staff_xy.x + WRAP * math.cos(a1), staff_xy.y + WRAP * math.sin(a1),
                 thumb_z + 0.005))
    r0, r1 = 0.027 - step * 0.006, 0.027 - (step + 1) * 0.006
    capsule(bm, p0, p1, r0, r1, segments=6)
    if step:
        ellipsoid(bm, p0, basis_from((0, 0, 1)), (r0 * 1.06,) * 3, 8, 5)
ellipsoid(bm, palm_center + palm_out * 0.020 + Vector((0, 0, 0.024)), palm_basis,
          (0.032, 0.028, 0.024), 10, 6)
wrist_start = palm_center - palm_out * 0.055
capsule(bm, wrist_start, FRONT_WRIST - (FRONT_WRIST - FRONT_SHOULDER).normalized() * 0.015,
        0.050, 0.043, segments=10)
write_mesh(bpy.data.objects["NH_Hand_Front"], bm, bpy.data.materials["NH_Bone_High"])
print("front hand palm %s wrap radius %.3f" % (tuple(round(v, 3) for v in palm_center), WRAP))

# --- resting fist --------------------------------------------------------
back_center = Vector((-0.500, -0.040, 1.131))
back_out = Vector((-0.45, -0.85, 0.25)).normalized()
basis = basis_from(back_out)
t1 = Vector(basis.col[0])
t2 = Vector(basis.col[1])
bm = bmesh.new()
box(bm, back_center, basis, (0.048, 0.056, 0.026))
for index in range(4):
    lateral = 0.034 - index * 0.029
    base = back_center + t1 * 0.048 + t2 * lateral
    mid = base + t1 * 0.028 - t2 * 0.028
    tip = mid + t1 * 0.004 - t2 * 0.040
    radius = 0.021 - index * 0.001
    capsule(bm, base, mid, radius, radius * 0.9, segments=6)
    capsule(bm, mid, tip, radius * 0.9, radius * 0.75, segments=6)
    ellipsoid(bm, mid, basis_from((0, 0, 1)), (radius * 1.05,) * 3, 8, 5)
    ellipsoid(bm, back_center + t1 * 0.052 + t2 * lateral, basis, (0.026, 0.022, 0.024), 10, 6)
thumb_base = back_center + t1 * 0.008 - t2 * 0.048
capsule(bm, thumb_base, thumb_base + t1 * 0.038 - t2 * 0.018, 0.024, 0.019, segments=6)
capsule(bm, thumb_base + t1 * 0.038 - t2 * 0.018, thumb_base + t1 * 0.058 - t2 * 0.044,
        0.019, 0.015, segments=6)
back_dir = (BACK_WRIST - BACK_SHOULDER).normalized()
capsule(bm, back_center - back_out * 0.046, BACK_WRIST - back_dir * 0.015, 0.048, 0.041,
        segments=10)
write_mesh(bpy.data.objects["NH_Hand_Back"], bm, bpy.data.materials["NH_Bone_High"])

# --- arms with cuffs ----------------------------------------------------
def rebuild_arm(name, shoulder, wrist, material_name, r_shoulder, r_wrist):
    axis = (wrist - shoulder).normalized()
    bm = bmesh.new()
    capsule(bm, shoulder - axis * 0.05, wrist, r_shoulder, r_wrist, segments=14)
    write_mesh(bpy.data.objects[name], bm, bpy.data.materials[material_name])
    cuff = bmesh.new()
    capsule(cuff, wrist - axis * 0.078, wrist + axis * 0.022, r_wrist * 1.30, r_wrist * 1.52,
            segments=14)
    make_object(name + "_Cuff", cuff, bpy.data.materials["NH_Robe_Trim"])


rebuild_arm("NH_Arm_Front", FRONT_SHOULDER, FRONT_WRIST, "NH_Robe_Light", 0.098, 0.052)
rebuild_arm("NH_Arm_Back", BACK_SHOULDER, BACK_WRIST, "NH_Robe", 0.094, 0.050)

# --- luminous bits: absolute values so this script stays idempotent ------
def tune(material_name, emission=None, strength=None, alpha=None):
    material = bpy.data.materials[material_name]
    bsdf = next(n for n in material.node_tree.nodes
                if n.bl_idname == "ShaderNodeBsdfPrincipled")
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (emission[0], emission[1], emission[2], 1.0)
    if strength is not None:
        bsdf.inputs["Emission Strength"].default_value = strength
    if alpha is not None:
        bsdf.inputs["Alpha"].default_value = alpha
    print("%-14s emission %s strength %s alpha %s"
          % (material_name, emission, strength, alpha))


tune("NH_Soul_Core", emission=(0.100, 1.000, 0.280), strength=1.3)
tune("NH_Soul", emission=(0.090, 0.750, 0.280), strength=0.7, alpha=0.45)
tune("NH_Rune", emission=(0.060, 0.900, 0.240), strength=0.8)

for name, scale in (("NH_EyeGlow_1", (0.024, 0.012, 0.029)),
                    ("NH_EyeGlow_-1", (0.024, 0.012, 0.029)),
                    ("NH_Pouch_Soul", (0.039, 0.017, 0.045)),
                    ("NH_Wisp_Core_1", (0.036, 0.020, 0.044)),
                    ("NH_Wisp_Core_2", (0.036, 0.020, 0.044))):
    obj = bpy.data.objects[name]
    obj.scale = scale
    print("%-16s scale %s" % (name, scale))

# --- verification -------------------------------------------------------
print("\n=== verification ===")
total = 0
for name in ("NH_Pauldron", "NH_Hand_Front", "NH_Hand_Back", "NH_Arm_Front",
             "NH_Arm_Front_Cuff", "NH_Arm_Back", "NH_Arm_Back_Cuff"):
    obj = bpy.data.objects[name]
    bounds = object_world_bounds(obj)
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    total += tris
    print("%-20s verts %4d tris %4d | x %6.3f..%6.3f y %6.3f..%6.3f z %6.3f..%6.3f"
          % (name, len(obj.data.vertices), tris, bounds[0], bounds[1], bounds[2], bounds[3],
             bounds[4], bounds[5]))
print("new parts tris:", total)

scene_tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
                 for o in scene.objects if o.type == "MESH" and o.name.startswith("NH_")
                 and not o.name.startswith("NH_Studio"))
root["nh_triangles"] = scene_tris
print("scene triangles:", scene_tris)

bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
