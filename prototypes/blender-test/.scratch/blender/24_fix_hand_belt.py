import bpy, bmesh, math
from mathutils import Matrix, Vector

scene = bpy.data.scenes["NecroHero_Asset"]
body = bpy.data.objects["NH_Body"]
FRONT_WRIST = Vector((0.690, -0.131, 1.193))

# Remove the half-buried leather belt: it only showed as brown spikes through the robe.
belt = bpy.data.objects.get("NH_Belt")
if belt is not None:
    bpy.data.objects.remove(belt, do_unlink=True)
    print("removed NH_Belt")


def capsule(bm, p0, p1, r0, r1, segments=10):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    if d.length < 1e-6:
        return
    q = d.to_track_quat("Z", "Y")
    m = Matrix.Translation((p0 + p1) * 0.5) @ q.to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=r0, radius2=r1, depth=d.length,
                          matrix=m, calc_uvs=True)


def ellipsoid(bm, center, radii, segments=12, rings=8):
    m = Matrix.Translation(Vector(center)) @ Matrix.Diagonal(Vector((radii[0], radii[1], radii[2], 1.0)))
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings,
                              radius=1.0, matrix=m, calc_uvs=True)

def finish_mesh(obj):
    mesh = obj.data
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(mesh); bm.free(); mesh.validate(verbose=False)


def write_mesh(obj, bm, material):
    mesh = bpy.data.meshes.new(obj.name + "_corrected")
    bm.to_mesh(mesh); bm.free()
    old = obj.data
    obj.data = mesh
    mesh.materials.clear(); mesh.materials.append(material)
    obj.parent = body
    obj.matrix_parent_inverse = body.matrix_world.inverted()
    obj.matrix_world = Matrix.Identity(4)
    if old.users == 0:
        bpy.data.meshes.remove(old)
    finish_mesh(obj)


def bounds(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return (min(p.x for p in pts), max(p.x for p in pts),
            min(p.y for p in pts), max(p.y for p in pts),
            min(p.z for p in pts), max(p.z for p in pts))

grip = bpy.data.objects["NH_Staff_Grip"]
gb = bounds(grip)
sx = (gb[0] + gb[1]) * 0.5
sy = (gb[2] + gb[3]) * 0.5
print("staff grip center", round(sx, 3), round(sy, 3))

# Rebuild a right hand with the BACK of the hand facing the viewer and the palm toward the staff.
# Camera/front is roughly negative Y. Fingers therefore start on the near side and curl behind the grip.
bm = bmesh.new()
palm = Vector((sx - 0.100, sy - 0.055, 1.220))
ellipsoid(bm, palm, (0.080, 0.040, 0.070), 14, 9)

# Wrist flows into the heel of the palm rather than entering its visible face.
capsule(bm, FRONT_WRIST + Vector((0.0, -0.010, 0.005)),
        palm + Vector((-0.045, 0.018, -0.025)), 0.044, 0.055, 10)

# Four knuckles on the outside/back of the hand.
zs = [1.255, 1.232, 1.208, 1.184]
for i, z in enumerate(zs):
    k = Vector((sx - 0.068, sy - 0.082, z))
    ellipsoid(bm, k, (0.024 - i*0.0015, 0.018, 0.021), 10, 6)

    # Finger curls around the cylinder: front-left -> front-right -> far side.
    p0 = Vector((sx - 0.060, sy - 0.072, z))
    p1 = Vector((sx - 0.008, sy - 0.083, z - 0.004))
    p2 = Vector((sx + 0.050, sy - 0.045, z - 0.008))
    p3 = Vector((sx + 0.055, sy + 0.030, z - 0.012))
    r = 0.0175 - i * 0.0008
    capsule(bm, p0, p1, r, r*0.94, 8)
    capsule(bm, p1, p2, r*0.94, r*0.86, 8)
    capsule(bm, p2, p3, r*0.86, r*0.72, 8)
    ellipsoid(bm, p1, (r*1.05, r*0.95, r*0.95), 8, 5)
    ellipsoid(bm, p2, (r*0.95, r*0.90, r*0.90), 8, 5)

# Thumb crosses the near side of the grip and locks the four fingers.
t0 = palm + Vector((0.030, -0.025, 0.050))
t1 = Vector((sx - 0.020, sy - 0.090, 1.252))
t2 = Vector((sx + 0.030, sy - 0.078, 1.238))
capsule(bm, t0, t1, 0.021, 0.019, 9)
capsule(bm, t1, t2, 0.019, 0.015, 9)
ellipsoid(bm, t1, (0.021, 0.018, 0.018), 9, 6)

hand = bpy.data.objects["NH_Hand_Front"]
write_mesh(hand, bm, bpy.data.materials["NH_Bone_High"])
bpy.context.view_layer.update()

hb = bounds(hand)
print("hand bounds", tuple(round(v, 3) for v in hb))
print("grip bounds", tuple(round(v, 3) for v in gb))
print("frontmost hand y", round(hb[2], 3), "frontmost grip y", round(gb[2], 3))
print("finger curl reaches behind grip:", hb[3] > sy)

tris = sum(sum(len(p.vertices)-2 for p in o.data.polygons)
           for o in scene.objects if o.type == "MESH" and o.name.startswith("NH_")
           and not o.name.startswith("NH_Studio"))
bpy.data.objects["NH_Root"]["nh_triangles"] = tris
print("scene triangles", tris)

bpy.ops.wm.save_mainfile()
print("saved", bpy.data.filepath)
