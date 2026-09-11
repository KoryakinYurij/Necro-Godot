import bpy, bmesh
from mathutils import Matrix, Vector
scene=bpy.data.scenes["NecroHero_Asset"]
body=bpy.data.objects["NH_Body"]
hand=bpy.data.objects["NH_Hand_Front"]
grip=bpy.data.objects["NH_Staff_Grip"]
WRIST=Vector((0.690,-0.131,1.193))

def bounds(o):
 p=[o.matrix_world@Vector(c) for c in o.bound_box]
 return min(v.x for v in p),max(v.x for v in p),min(v.y for v in p),max(v.y for v in p),min(v.z for v in p),max(v.z for v in p)

def cap(bm,a,b,r0,r1,seg=10):
 a,b=Vector(a),Vector(b); d=b-a
 if d.length<1e-6:return
 q=d.to_track_quat("Z","Y")
 m=Matrix.Translation((a+b)*0.5)@q.to_matrix().to_4x4()
 bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=seg,radius1=r0,radius2=r1,depth=d.length,matrix=m,calc_uvs=True)

def ell(bm,c,r,u=12,v=8):
 m=Matrix.Translation(Vector(c))@Matrix.Diagonal(Vector((r[0],r[1],r[2],1)))
 bmesh.ops.create_uvsphere(bm,u_segments=u,v_segments=v,radius=1,matrix=m,calc_uvs=True)

gb=bounds(grip); sx=(gb[0]+gb[1])*0.5; sy=(gb[2]+gb[3])*0.5
bm=bmesh.new()
# Compact back-of-hand mass plus heel; flatter than the previous spherical palm.
palm=Vector((sx-0.102,sy-0.056,1.216))
heel=Vector((sx-0.142,sy-0.036,1.202))
ell(bm,palm,(0.064,0.028,0.058),14,8)
ell(bm,heel,(0.040,0.030,0.046),12,7)
cap(bm,WRIST+Vector((0,-0.003,0.004)),heel+Vector((-0.022,0.016,-0.010)),0.038,0.043,10)

# Knuckle ridge remains visible on the outer side.
zs=[1.248,1.228,1.207,1.187]
for i,z in enumerate(zs):
 r=0.017-i*0.0007
 ell(bm,(sx-0.052,sy-0.060,z),(0.021-i*0.001,0.014,0.018),10,6)
 # Fingers live mostly behind the grip (+Y), with only tiny tips allowed to peek at its right edge.
 p0=Vector((sx-0.045,sy+0.018,z))
 p1=Vector((sx-0.005,sy+0.066,z-0.004))
 p2=Vector((sx+0.046,sy+0.058,z-0.007))
 p3=Vector((sx+0.067,sy+0.012,z-0.010))
 cap(bm,p0,p1,r,r*0.92,8)
 cap(bm,p1,p2,r*0.92,r*0.82,8)
 cap(bm,p2,p3,r*0.82,r*0.68,8)

# Short bent thumb on the near/front side: it should lock the grip, not span its whole face.
t0=Vector((sx-0.070,sy-0.064,1.246))
t1=Vector((sx-0.038,sy-0.088,1.239))
t2=Vector((sx-0.010,sy-0.082,1.224))
ell(bm,t0,(0.021,0.017,0.020),10,6)
cap(bm,t0,t1,0.018,0.016,9)
cap(bm,t1,t2,0.016,0.013,9)
ell(bm,t1,(0.017,0.015,0.015),9,6)
mesh=bpy.data.meshes.new("NH_Hand_Front_polished")
bm.to_mesh(mesh); bm.free()
old=hand.data; hand.data=mesh
mesh.materials.append(bpy.data.materials["NH_Bone_High"])
hand.parent=body; hand.matrix_parent_inverse=body.matrix_world.inverted(); hand.matrix_world=Matrix.Identity(4)
if old.users==0:bpy.data.meshes.remove(old)
bm2=bmesh.new(); bm2.from_mesh(mesh)
bmesh.ops.recalc_face_normals(bm2,faces=bm2.faces)
for f in bm2.faces:f.smooth=True
bm2.to_mesh(mesh); bm2.free(); mesh.validate(verbose=False)
bpy.context.view_layer.update()
print("hand",tuple(round(v,3) for v in bounds(hand)))
print("belt exists",bpy.data.objects.get("NH_Belt") is not None)
bpy.ops.wm.save_mainfile()
print("saved",bpy.data.filepath)
