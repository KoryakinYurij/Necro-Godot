import bpy
import bmesh
from mathutils import Matrix, Vector

body = bpy.data.objects['NH_Body']
FRONT_WRIST = Vector((0.690, -0.131, 1.193))


def reset(obj):
    obj.parent = body
    obj.matrix_parent_inverse = body.matrix_world.inverted()
    obj.location = (0, 0, 0)
    obj.rotation_mode = 'XYZ'
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (1, 1, 1)
    obj.matrix_world = Matrix.Identity(4)


def replace_pydata(obj, verts, faces, mat):
    reset(obj)
    me = bpy.data.meshes.new(obj.name)
    me.from_pydata(verts, [], faces)
    me.update()
    old = obj.data
    obj.data = me
    me.materials.append(mat)
    if old and old.users == 0:
        bpy.data.meshes.remove(old)
    for p in me.polygons:
        p.use_smooth = False
    return obj


def capsule(bm, p0, p1, r0, r1, segments=8):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    if d.length < 1e-5:
        return
    q = d.to_track_quat('Z', 'Y')
    m = Matrix.Translation((p0 + p1) * 0.5) @ q.to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=r0, radius2=r1, depth=d.length, matrix=m, calc_uvs=True)


def ellipsoid(bm, center, radii, u=12, v=8):
    m = Matrix.Translation(center) @ Matrix.Diagonal(Vector((*radii, 1.0)))
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0, matrix=m, calc_uvs=True)


def replace_bmesh(obj, bm, mat):
    reset(obj)
    me = bpy.data.meshes.new(obj.name)
    bm.to_mesh(me)
    bm.free()
    old = obj.data
    obj.data = me
    me.materials.append(mat)
    if old and old.users == 0:
        bpy.data.meshes.remove(old)
    bm2 = bmesh.new(); bm2.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces)
    for f in bm2.faces: f.smooth = True
    bm2.to_mesh(me); bm2.free(); me.update()
    return obj

# One continuous bone plate: covers the joint and overlaps the upper arm.
outline = [
    (0.270, 1.800), (0.300, 1.885), (0.370, 1.940),
    (0.455, 1.920), (0.535, 1.855), (0.570, 1.775),
    (0.515, 1.700), (0.425, 1.715), (0.355, 1.760),
]
y0, y1 = -0.205, -0.055
verts = [(x, y0, z) for x, z in outline] + [(x, y1, z) for x, z in outline]
n = len(outline)
faces = [tuple(reversed(range(n))), tuple(n + i for i in range(n))]
for i in range(n):
    j = (i + 1) % n
    faces.append((i, j, n + j, n + i))
replace_pydata(bpy.data.objects['NH_Pauldron'], verts, faces, bpy.data.materials['NH_Bone_High'])
print('pauldron: one continuous shoulder plate')

# Rebuild gripping hand with a visible palm and staggered fingers.
grip = bpy.data.objects['NH_Staff_Grip']
pts = [grip.matrix_world @ Vector(c) for c in grip.bound_box]
gx0, gx1 = min(p.x for p in pts), max(p.x for p in pts)
gy0, gy1 = min(p.y for p in pts), max(p.y for p in pts)
gz0, gz1 = min(p.z for p in pts), max(p.z for p in pts)
gx, gy, gz = (gx0 + gx1) * 0.5, (gy0 + gy1) * 0.5, (gz0 + gz1) * 0.5
front_y = gy0 - 0.012
palm = Vector((gx - 0.095, gy + 0.018, gz - 0.002))

bm = bmesh.new()
ellipsoid(bm, palm, (0.078, 0.060, 0.073), 12, 8)
capsule(bm, FRONT_WRIST, palm - Vector((0.035, -0.005, 0.004)), 0.044, 0.054, 10)

zs = [gz + 0.040, gz + 0.014, gz - 0.014, gz - 0.043]
for i, z in enumerate(zs):
    r = 0.0195 - i * 0.0012
    p0 = Vector((palm.x + 0.026 - i * 0.003, palm.y - 0.026, z + i * 0.001))
    p1 = Vector((gx - 0.026, front_y, z - 0.003 - i * 0.002))
    p2 = Vector((gx + 0.026 - i * 0.004, front_y + 0.004, z - 0.008 - i * 0.003))
    capsule(bm, p0, p1, r, r * 0.90, 8)
    capsule(bm, p1, p2, r * 0.90, r * 0.74, 8)
    ellipsoid(bm, p1, (r, r, r), 8, 5)

# Thumb crosses the grip diagonally and makes handedness obvious.
t0 = palm + Vector((-0.006, -0.028, 0.052))
t1 = Vector((gx - 0.025, front_y - 0.004, gz + 0.036))
t2 = Vector((gx + 0.024, front_y + 0.006, gz + 0.006))
capsule(bm, t0, t1, 0.024, 0.021, 8)
capsule(bm, t1, t2, 0.021, 0.016, 8)
ellipsoid(bm, t1, (0.022, 0.022, 0.022), 8, 5)
replace_bmesh(bpy.data.objects['NH_Hand_Front'], bm, bpy.data.materials['NH_Bone_High'])
print('hand: larger palm + staggered wrap, palm', tuple(round(v, 3) for v in palm))

bpy.context.view_layer.update()
for name in ['NH_Pauldron','NH_Hand_Front']:
    o=bpy.data.objects[name]
    p=[o.matrix_world@Vector(c) for c in o.bound_box]
    print(name,'bounds',tuple(round(v,3) for v in (
        min(v.x for v in p),max(v.x for v in p),min(v.y for v in p),max(v.y for v in p),
        min(v.z for v in p),max(v.z for v in p))))

bpy.data.objects['NH_Root']['nh_rework_note'] = '2026-09-11: robe/mantle rebuilt; continuous shoulder plate; corrected staff grip hand'
bpy.ops.wm.save_mainfile()
print('saved', bpy.data.filepath)
