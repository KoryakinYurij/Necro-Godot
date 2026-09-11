import bpy
import bmesh
import math
from mathutils import Matrix, Vector

scene = bpy.data.scenes["NecroHero_Asset"]
body = bpy.data.objects["NH_Body"]
root = bpy.data.objects["NH_Root"]

FRONT_SHOULDER = Vector((0.370, -0.109, 1.809))
FRONT_WRIST = Vector((0.690, -0.131, 1.193))

arm_axis = (FRONT_WRIST - FRONT_SHOULDER).normalized()
outward = arm_axis.cross(Vector((0.0, 1.0, 0.0))).normalized()
if outward.x < 0:
    outward = -outward
tangent = outward.cross(arm_axis).normalized()


def basis_from(normal, hint=(0.0, 0.0, 1.0)):
    n = Vector(normal).normalized()
    hint = Vector(hint)
    if abs(n.dot(hint)) > 0.95:
        hint = Vector((0.0, 1.0, 0.0))
    t1 = hint.cross(n).normalized()
    t2 = n.cross(t1).normalized()
    return Matrix((t1, t2, n)).transposed()


def dome(bm, center, basis, radii, cut=-0.12, u=20, v=12):
    """Open shell: a unit sphere with everything below `cut` deleted."""
    before = set(bm.verts)
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    fresh = [v for v in bm.verts if v not in before]
    faces = set()
    for vertex in fresh:
        for face in vertex.link_faces:
            faces.add(face)
    lower = [f for f in faces if f.calc_center_median().z < cut]
    if lower:
        bmesh.ops.delete(bm, geom=lower, context="FACES")
    remaining = [v for v in bm.verts if v not in before]
    matrix = (Matrix.Translation(center) @ basis.to_4x4()
              @ Matrix.Diagonal(Vector((radii[0], radii[1], radii[2], 1.0))))
    bmesh.ops.transform(bm, matrix=matrix, verts=remaining)


def ellipsoid(bm, center, basis, radii, u=16, v=10):
    matrix = (Matrix.Translation(center) @ basis.to_4x4()
              @ Matrix.Diagonal(Vector((radii[0], radii[1], radii[2], 1.0))))
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0,
                              matrix=matrix, calc_uvs=True)


def capsule(bm, p0, p1, r0, r1, segments=8):
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


# ------------------------------------------------------------- pauldron
bm = bmesh.new()

# 1. dome cap over the shoulder, rim sunk slightly into the mantle
dome_center = FRONT_SHOULDER + outward * -0.028 + arm_axis * -0.012
dome_basis = basis_from(outward, arm_axis)
dome(bm, dome_center, dome_basis, (0.205, 0.185, 0.130), cut=-0.10)

# 2. one lame below it, hugging the upper arm
lame_center = FRONT_SHOULDER + arm_axis * 0.155 + outward * -0.006
tilt = Matrix.Rotation(math.radians(26.0), 4, tangent)
lame_basis = (tilt @ basis_from(arm_axis).to_4x4()).to_3x3()
ellipsoid(bm, lame_center, lame_basis, (0.158, 0.138, 0.030))

# 3. claw off the top-outer edge of the dome
claw_base = dome_center + outward * 0.095 + arm_axis * -0.055
claw_tip = claw_base + outward * 0.055 + arm_axis * -0.105
capsule(bm, claw_base, claw_tip, 0.022, 0.003, segments=8)

pauldron = bpy.data.objects["NH_Pauldron"]
mesh = bpy.data.meshes.new("NH_Pauldron")
bm.to_mesh(mesh)
bm.free()
old = pauldron.data
pauldron.data = mesh
mesh.materials.clear()
mesh.materials.append(bpy.data.materials["NH_Bone_High"])
if old.users == 0:
    bpy.data.meshes.remove(old)
finish_mesh(pauldron)

corners = [pauldron.matrix_world @ Vector(c) for c in pauldron.bound_box]
print("pauldron verts %d tris %d | x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f"
      % (len(mesh.vertices), sum(len(p.vertices) - 2 for p in mesh.polygons),
         min(c.x for c in corners), max(c.x for c in corners),
         min(c.y for c in corners), max(c.y for c in corners),
         min(c.z for c in corners), max(c.z for c in corners)))

tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
           for o in scene.objects if o.type == "MESH" and o.name.startswith("NH_")
           and not o.name.startswith("NH_Studio"))
root["nh_triangles"] = tris
print("scene triangles:", tris)

bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
