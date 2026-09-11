import bpy, bmesh
from mathutils import Matrix, Vector

scene = bpy.data.scenes["NecroHero_Asset"]
body = bpy.data.objects["NH_Body"]
hand = bpy.data.objects["NH_Hand_Front"]
grip = bpy.data.objects["NH_Staff_Grip"]
FRONT_WRIST = Vector((0.690, -0.131, 1.193))


def bounds(obj):
    p = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return (min(v.x for v in p), max(v.x for v in p),
            min(v.y for v in p), max(v.y for v in p),
            min(v.z for v in p), max(v.z for v in p))


def capsule(bm, a, b, r0, r1, seg=10):
    a, b = Vector(a), Vector(b); d = b-a
    if d.length < 1e-6: return
    q = d.to_track_quat("Z", "Y")
    m = Matrix.Translation((a+b)*0.5) @ q.to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r0, radius2=r1, depth=d.length, matrix=m, calc_uvs=True)


def ellipsoid(bm, c, r, u=12, v=8):
    m = Matrix.Translation(Vector(c)) @ Matrix.Diagonal(Vector((r[0],r[1],r[2],1.0)))
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0, matrix=m, calc_uvs=True)

gb = bounds(grip); sx=(gb[0]+gb[1])*0.5; sy=(gb[2]+gb[3])*0.5
bm = bmesh.new()

# Flattened back of the hand on viewer/front side of the grip.
palm = Vector((sx-0.105, sy-0.060, 1.218))
ellipsoid(bm, palm, (0.075, 0.030, 0.067), 14, 8)

# Wrist enters the heel of the palm from the forearm.
capsule(bm, FRONT_WRIST + Vector((0.0,-0.004,0.004)),
        palm + Vector((-0.045,0.020,-0.024)), 0.041, 0.050, 10)

# Visible knuckles only; finger bodies turn immediately to the FAR side (+Y) of the staff.
zs=[1.252,1.230,1.207,1.185]
for i,z in enumerate(zs):
    k=Vector((sx-0.060, sy-0.067, z))
    rr=0.018-i*0.0007
    ellipsoid(bm,k,(0.023-i*0.001,0.016,0.019),10,6)
    p0=Vector((sx-0.050, sy-0.040, z))
    p1=Vector((sx-0.020, sy+0.025, z-0.003))
    p2=Vector((sx+0.035, sy+0.065, z-0.006))
    p3=Vector((sx+0.062, sy+0.015, z-0.010))
    capsule(bm,p0,p1,rr,rr*0.94,8)
    capsule(bm,p1,p2,rr*0.94,rr*0.84,8)
    capsule(bm,p2,p3,rr*0.84,rr*0.70,8)

# Thumb is the main visible digit on the near/front side.
t0=palm+Vector((0.030,-0.012,0.047))
t1=Vector((sx-0.028,sy-0.086,1.248))
t2=Vector((sx+0.022,sy-0.078,1.235))
capsule(bm,t0,t1,0.021,0.019,9)
capsule(bm,t1,t2,0.019,0.015,9)
ellipsoid(bm,t1,(0.021,0.017,0.018),9,6)

mesh=bpy.data.meshes.new("NH_Hand_Front_backhand")
bm.to_mesh(mesh); bm.free()
old=hand.data; hand.data=mesh
mesh.materials.append(bpy.data.materials["NH_Bone_High"])
hand.parent=body; hand.matrix_parent_inverse=body.matrix_world.inverted(); hand.matrix_world=Matrix.Identity(4)
if old.users==0: bpy.data.meshes.remove(old)

bm2=bmesh.new(); bm2.from_mesh(mesh)
bmesh.ops.recalc_face_normals(bm2,faces=bm2.faces)
for f in bm2.faces: f.smooth=True
bm2.to_mesh(mesh); bm2.free(); mesh.validate(verbose=False)
bpy.context.view_layer.update()

hb=bounds(hand)
print("corrected hand bounds",tuple(round(v,3) for v in hb))
print("fingers mostly behind staff center:", hb[3] > sy+0.05)
print("belt exists:", bpy.data.objects.get("NH_Belt") is not None)

tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons)
         for o in scene.objects if o.type=="MESH" and o.name.startswith("NH_")
         and not o.name.startswith("NH_Studio"))
bpy.data.objects["NH_Root"]["nh_triangles"]=tris
bpy.ops.wm.save_mainfile()
print("saved",bpy.data.filepath,"tris",tris)
