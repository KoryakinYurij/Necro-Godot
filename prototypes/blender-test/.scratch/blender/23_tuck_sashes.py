import bpy
from mathutils import Matrix
body=bpy.data.objects['NH_Body']
mat=bpy.data.materials['NH_Robe_Trim']

def replace_ribbon(name, outline, y0, y1):
    obj=bpy.data.objects[name]
    obj.parent=body
    obj.matrix_parent_inverse=body.matrix_world.inverted()
    obj.location=(0,0,0); obj.rotation_mode='XYZ'; obj.rotation_euler=(0,0,0); obj.scale=(1,1,1)
    obj.matrix_world=Matrix.Identity(4)
    n=len(outline)
    verts=[(x,y0,z) for x,z in outline]+[(x,y1,z) for x,z in outline]
    faces=[tuple(reversed(range(n))), tuple(n+i for i in range(n))]
    for i in range(n):
        j=(i+1)%n
        faces.append((i,j,n+j,n+i))
    me=bpy.data.meshes.new(name)
    me.from_pydata(verts,[],faces); me.update()
    old=obj.data; obj.data=me; me.materials.append(mat)
    if old and old.users==0: bpy.data.meshes.remove(old)
    for p in me.polygons: p.use_smooth=False
    print(name,'rebuilt',outline)

# Short, deliberate cloth tabs tucked behind the pouch instead of long boards.
replace_ribbon('NH_Sash_1', [(-0.34,1.29),(-0.24,1.31),(-0.28,0.74),(-0.38,0.70)], -0.420,-0.390)
replace_ribbon('NH_Sash_2', [(-0.26,1.23),(-0.18,1.24),(-0.21,0.88),(-0.29,0.85)], -0.414,-0.386)

bpy.context.view_layer.update()
bpy.data.objects['NH_Root']['nh_rework_note']='2026-09-11: robe/mantle, shoulder, hand and sash silhouette reworked'
bpy.ops.wm.save_mainfile()
print('saved',bpy.data.filepath)
