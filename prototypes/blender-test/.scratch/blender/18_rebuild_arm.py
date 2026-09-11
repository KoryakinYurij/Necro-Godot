import bpy
import bmesh
import math
import mathutils
from mathutils import Matrix, Vector

scene = bpy.data.scenes["NecroHero_Asset"]
COLLECTION = bpy.data.collections["Agent_Generated_NecroHero"]
body = bpy.data.objects["NH_Body"]
root = bpy.data.objects["NH_Root"]

# ---------------------------------------------------------------- helpers
def object_world_bounds(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return (min(c.x for c in corners), max(c.x for c in corners),
            min(c.y for c in corners), max(c.y for c in corners),
            min(c.z for c in corners), max(c.z for c in corners))


def axis_endpoints(obj):
    """Farthest-apart vertex pair in world space = the shape's long axis."""
    matrix = obj.matrix_world
    points = [matrix @ v.co for v in obj.data.vertices]
    best = (0.0, points[0], points[0])
    for i, a in enumerate(points):
        for b in points[i + 1:]:
            distance = (a - b).length
            if distance > best[0]:
                best = (distance, a, b)
    return best[1], best[2]


def basis_from(normal, hint=(0.0, 0.0, 1.0)):
    """Right-handed basis whose third axis is `normal`."""
    n = Vector(normal).normalized()
    hint = Vector(hint)
    if abs(n.dot(hint)) > 0.95:
        hint = Vector((0.0, 1.0, 0.0))
    t1 = hint.cross(n).normalized()
    t2 = n.cross(t1).normalized()
    return Matrix((t1, t2, n)).transposed()


def ellipsoid(bm, center, basis, radii, u=16, v=10):
    matrix = (Matrix.Translation(center) @ basis.to_4x4()
              @ Matrix.Diagonal(Vector((radii[0], radii[1], radii[2], 1.0))))
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0,
                              matrix=matrix, calc_uvs=True)


def box(bm, center, basis, half):
    matrix = (Matrix.Translation(center) @ basis.to_4x4()
              @ Matrix.Diagonal(Vector((half[0], half[1], half[2], 1.0))))
    bmesh.ops.create_cube(bm, size=2.0, matrix=matrix, calc_uvs=True)


def capsule(bm, p0, p1, r0, r1, segments=10):
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
    """Smooth shading with hard edges over the angle, plus a box UV map."""
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


def replace_mesh(obj, bm, material):
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
        return replace_mesh(existing, bm, material)
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


# ------------------------------------------------------- measured geometry
staff = bpy.data.objects["NH_Staff"]
grip = bpy.data.objects["NH_Staff_Grip"]
staff_bounds = object_world_bounds(staff)
grip_bounds = object_world_bounds(grip)
st = Vector(((staff_bounds[0] + staff_bounds[1]) / 2, (staff_bounds[2] + staff_bounds[3]) / 2))
staff_radius = (staff_bounds[1] - staff_bounds[0]) / 2
grip_radius = (grip_bounds[1] - grip_bounds[0]) / 2
grip_z = (grip_bounds[4] + grip_bounds[5]) / 2

arm_front = bpy.data.objects["NH_Arm_Front"]
arm_back = bpy.data.objects["NH_Arm_Back"]
front_end_a, front_end_b = axis_endpoints(arm_front)
back_end_a, back_end_b = axis_endpoints(arm_back)
front_shoulder, front_wrist = ((front_end_a, front_end_b) if front_end_a.z > front_end_b.z
                               else (front_end_b, front_end_a))
back_shoulder, back_wrist = ((back_end_a, back_end_b) if back_end_a.z > back_end_b.z
                             else (back_end_b, back_end_a))
print("staff axis xy %s radius %.3f | grip radius %.3f grip z %.3f"
      % (tuple(round(v, 3) for v in st), staff_radius, grip_radius, grip_z))
print("front arm shoulder %s wrist %s"
      % (tuple(round(v, 3) for v in front_shoulder), tuple(round(v, 3) for v in front_wrist)))
print("back  arm shoulder %s wrist %s"
      % (tuple(round(v, 3) for v in back_shoulder), tuple(round(v, 3) for v in back_wrist)))

# ---------------------------------------------------------------- pauldron
# Three overlapping bone lames around the shoulder plus one claw, replacing the
# three interpenetrating spheres that used to sink into the chest.
arm_axis = (front_wrist - front_shoulder).normalized()
outward = arm_axis.cross(Vector((0.0, 1.0, 0.0))).normalized()
if outward.x < 0:
    outward = -outward
tangent = outward.cross(arm_axis).normalized()

bm = bmesh.new()
lame_specs = [(0.030, (0.150, 0.130, 0.042), 6.0),
              (0.115, (0.135, 0.118, 0.038), 22.0),
              (0.198, (0.115, 0.100, 0.032), 40.0)]
for offset, radii, tilt_deg in lame_specs:
    center = front_shoulder + arm_axis * offset + outward * 0.012
    tilt = Matrix.Rotation(math.radians(tilt_deg), 4, tangent)
    basis = (tilt @ basis_from(arm_axis).to_4x4()).to_3x3()
    ellipsoid(bm, center, basis, radii)
    print("lame at offset %.3f center %s radii %s" % (offset,
                                                      tuple(round(v, 3) for v in center), radii))
claw_base = front_shoulder + arm_axis * 0.015 + outward * 0.055
claw_tip = claw_base + outward * 0.085 + arm_axis * -0.045
capsule(bm, claw_base, claw_tip, 0.024, 0.004, segments=8)
pauldron = make_object("NH_Pauldron", bm, bpy.data.materials["NH_Bone_High"])

for name in ("NH_Bone_Shoulder_1", "NH_Bone_Shoulder_2", "NH_Bone_Shoulder_3"):
    obj = bpy.data.objects.get(name)
    if obj is not None:
        bpy.data.objects.remove(obj, do_unlink=True)
        print("removed old shoulder part:", name)

# ------------------------------------------------------------------- hands
def build_grip_hand(bm, staff_xy, wrap_radius, palm_z, palm_angle_deg):
    """Right hand closed around a vertical staff."""
    palm_angle = math.radians(palm_angle_deg)
    out = Vector((math.cos(palm_angle), math.sin(palm_angle), 0.0))
    palm_center = Vector((staff_xy.x, staff_xy.y, palm_z)) + out * (wrap_radius + 0.040)
    basis = basis_from(out)
    box(bm, palm_center, basis, (0.052, 0.060, 0.023))
    box(bm, palm_center - out * 0.045, basis, (0.042, 0.050, 0.024))

    finger_z = [palm_z + 0.036, palm_z + 0.012, palm_z - 0.012, palm_z - 0.036]
    finger_radii = [(0.022, 0.019), (0.021, 0.018), (0.020, 0.017), (0.019, 0.016)]
    for index, (z, radii) in enumerate(zip(finger_z, finger_radii)):
        start_angle = math.radians(200.0 + index * 2.0)
        steps = 3
        sweep = math.radians(47.0)
        previous = None
        for step in range(steps):
            a0 = start_angle + step * sweep
            a1 = a0 + sweep
            p0 = Vector((staff_xy.x + wrap_radius * math.cos(a0),
                         staff_xy.y + wrap_radius * math.sin(a0), z))
            p1 = Vector((staff_xy.x + wrap_radius * math.cos(a1),
                         staff_xy.y + wrap_radius * math.sin(a1), z))
            r0 = radii[0] + (radii[1] - radii[0]) * (step / steps)
            r1 = radii[0] + (radii[1] - radii[0]) * ((step + 1) / steps)
            capsule(bm, p0, p1, r0, r1, segments=8)
            ellipsoid(bm, p0, basis_from((0, 0, 1)), (r0 * 1.05, r0 * 1.05, r0 * 1.05), 10, 6)
            previous = p1
        ellipsoid(bm, previous, basis_from((0, 0, 1)), (radii[1], radii[1], radii[1]), 10, 6)
        ellipsoid(bm, palm_center + out * 0.012 + Vector((0, 0, z - palm_z)),
                  basis, (0.030, 0.026, 0.024), 12, 8)

    # thumb wraps the other way, above the fingers
    thumb_z = palm_z + 0.056
    for step in range(2):
        a0 = math.radians(168.0 - step * 45.0)
        a1 = math.radians(168.0 - (step + 1) * 45.0)
        p0 = Vector((staff_xy.x + wrap_radius * math.cos(a0),
                     staff_xy.y + wrap_radius * math.sin(a0), thumb_z))
        p1 = Vector((staff_xy.x + wrap_radius * math.cos(a1),
                     staff_xy.y + wrap_radius * math.sin(a1), thumb_z + 0.006))
        r0 = 0.027 - step * 0.005
        r1 = 0.027 - (step + 1) * 0.005
        capsule(bm, p0, p1, r0, r1, segments=8)
        ellipsoid(bm, p0, basis_from((0, 0, 1)), (r0, r0, r0), 10, 6)
    ellipsoid(bm, palm_center + out * 0.018 + Vector((0, 0, 0.026)), basis,
              (0.034, 0.030, 0.026), 12, 8)
    return palm_center, out


bm = bmesh.new()
palm_center, palm_out = build_grip_hand(bm, st, grip_radius + 0.012, grip_z, 180.0)
wrist_start = palm_center - palm_out * 0.052
capsule(bm, wrist_start, front_wrist + (front_wrist - front_shoulder).normalized() * -0.02,
        0.050, 0.042, segments=10)
replace_mesh(bpy.data.objects["NH_Hand_Front"], bm, bpy.data.materials["NH_Bone_High"])
print("front hand palm center %s" % (tuple(round(v, 3) for v in palm_center),))


def build_fist(bm, center, out, up_hint=(0.0, 0.0, 1.0)):
    basis = basis_from(out, up_hint)
    t1 = Vector(basis.col[0])
    t2 = Vector(basis.col[1])
    box(bm, center, basis, (0.050, 0.058, 0.026))
    for index in range(4):
        base = center + t1 * 0.050 + t2 * (0.036 - index * 0.030)
        mid = base + t1 * 0.030 - t2 * 0.030
        tip = mid + t1 * 0.006 - t2 * 0.042
        radius = 0.021 - index * 0.001
        capsule(bm, base, mid, radius, radius * 0.9, segments=8)
        capsule(bm, mid, tip, radius * 0.9, radius * 0.75, segments=8)
        ellipsoid(bm, mid, basis_from((0, 0, 1)), (radius * 1.1,) * 3, 10, 6)
        ellipsoid(bm, center + t1 * 0.055 + t2 * (0.036 - index * 0.030),
                  basis, (0.026, 0.022, 0.024), 12, 8)
    thumb_base = center + t1 * 0.010 - t2 * 0.050
    capsule(bm, thumb_base, thumb_base + t1 * 0.040 - t2 * 0.020, 0.024, 0.019, segments=8)
    capsule(bm, thumb_base + t1 * 0.040 - t2 * 0.020,
            thumb_base + t1 * 0.062 - t2 * 0.048, 0.019, 0.015, segments=8)


back_center = Vector(((-0.611 - 0.389) / 2, (-0.137 + 0.057) / 2, (1.001 + 1.261) / 2))
back_out = Vector((-0.45, -0.85, 0.25)).normalized()
bm = bmesh.new()
build_fist(bm, back_center, back_out)
back_wrist_dir = (back_wrist - back_shoulder).normalized()
capsule(bm, back_center - back_out * 0.045, back_wrist - back_wrist_dir * 0.02, 0.048, 0.040,
        segments=10)
replace_mesh(bpy.data.objects["NH_Hand_Back"], bm, bpy.data.materials["NH_Bone_High"])
print("back hand rebuilt at %s" % (tuple(round(v, 3) for v in back_center),))

# -------------------------------------------------------------------- arms
def rebuild_arm(name, shoulder, wrist, material, radius_shoulder, radius_wrist):
    axis = (wrist - shoulder).normalized()
    bm = bmesh.new()
    capsule(bm, shoulder - axis * 0.05, wrist, radius_shoulder, radius_wrist, segments=14)
    obj = replace_mesh(bpy.data.objects[name], bm, material)
    cuff = bmesh.new()
    capsule(cuff, wrist - axis * 0.075, wrist + axis * 0.025,
            radius_wrist * 1.32, radius_wrist * 1.55, segments=14)
    return obj, make_object(name + "_Cuff", cuff, bpy.data.materials["NH_Robe_Trim"])


rebuild_arm("NH_Arm_Front", front_shoulder, front_wrist,
            bpy.data.materials["NH_Robe_Light"], 0.098, 0.052)
rebuild_arm("NH_Arm_Back", back_shoulder, back_wrist,
            bpy.data.materials["NH_Robe"], 0.094, 0.050)
print("arms rebuilt with tapered profile and cuff rings")

# ------------------------------------------------------- glow / bloom tone
def tune(material_name, **values):
    material = bpy.data.materials[material_name]
    bsdf = next(n for n in material.node_tree.nodes
                if n.bl_idname == "ShaderNodeBsdfPrincipled")
    for key, value in values.items():
        socket = {"emission_strength": "Emission Strength", "emission": "Emission Color",
                  "base": "Base Color", "alpha": "Alpha"}[key]
        if socket in bsdf.inputs:
            if key in ("emission", "base"):
                colour = value
                bsdf.inputs[socket].default_value = (colour[0], colour[1], colour[2], 1.0)
            else:
                bsdf.inputs[socket].default_value = value
        if key == "base":
            material.diffuse_color = (value[0], value[1], value[2],
                                      bsdf.inputs["Alpha"].default_value)
    print("%-14s tuned %s" % (material_name, sorted(values)))


tune("NH_Soul_Core", emission_strength=1.3, emission=(0.100, 1.000, 0.280))
tune("NH_Soul", emission_strength=0.7, emission=(0.090, 0.750, 0.280), alpha=0.45)
tune("NH_Rune", emission_strength=0.8, emission=(0.060, 0.900, 0.240))

# smaller eye glow and pouch soul so they stop reading as glowing stickers
for name, factor in (("NH_EyeGlow_1", 0.68), ("NH_EyeGlow_-1", 0.68),
                     ("NH_Pouch_Soul", 0.6), ("NH_Wisp_Core_1", 0.8), ("NH_Wisp_Core_2", 0.8)):
    obj = bpy.data.objects[name]
    for index, axis in enumerate("xyz"):
        obj.scale[index] *= factor
    bpy.context.view_layer.update()
    print("%-16s scale %s" % (name, tuple(round(v, 3) for v in obj.scale)))

glare = next((n for n in scene.compositing_node_group.nodes
              if n.bl_idname == "CompositorNodeGlare"), None)
if glare is not None:
    for socket_name, value in (("Size", 4.0), ("Threshold", 1.15), ("Iterations", 2),
                               ("Strength", 0.65)):
        if socket_name in glare.inputs:
            glare.inputs[socket_name].default_value = value
    print("glare: size %.1f threshold %.2f strength %.2f"
          % (glare.inputs["Size"].default_value, glare.inputs["Threshold"].default_value,
             glare.inputs["Strength"].default_value))

# -------------------------------------------------------------- verification
robe_bounds = object_world_bounds(bpy.data.objects["NH_Ragged_Robe"])
print("\n=== verification ===")
for name in ("NH_Pauldron", "NH_Hand_Front", "NH_Hand_Back", "NH_Arm_Front",
             "NH_Arm_Front_Cuff", "NH_Arm_Back", "NH_Arm_Back_Cuff"):
    obj = bpy.data.objects[name]
    bounds = object_world_bounds(obj)
    verts_inside_robe = 0
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        if (robe_bounds[0] <= world.x <= robe_bounds[1]
                and robe_bounds[2] <= world.y <= robe_bounds[3]
                and robe_bounds[4] <= world.z <= robe_bounds[5]):
            verts_inside_robe += 1
    print("%-20s verts %4d tris %4d bbox x %.3f..%.3f z %.3f..%.3f | verts inside robe bbox: %d"
          % (name, len(obj.data.vertices),
             sum(len(p.vertices) - 2 for p in obj.data.polygons),
             bounds[0], bounds[1], bounds[4], bounds[5], verts_inside_robe))

tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
           for o in scene.objects if o.type == "MESH" and o.name.startswith("NH_")
           and not o.name.startswith("NH_Studio"))
root["nh_triangles"] = tris
print("scene triangles now:", tris)

bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
