import bpy, os
from mathutils import Vector

scene=bpy.data.scenes["NecroHero_Asset"]
cam=bpy.data.objects["NH_Preview_Cam"]
target=bpy.data.objects["NH_Cam_Target"]
out=r"D:\Code AI\Games\Necro-Godot\prototypes\blender-test\.scratch\preview\checks"
os.makedirs(out,exist_ok=True)
keep={"NH_Hand_Front","NH_Arm_Front","NH_Arm_Front_Cuff","NH_Staff","NH_Staff_Grip"}
old={o.name:o.hide_render for o in scene.objects}
for o in scene.objects:
    if o.type in {"MESH","EMPTY"} and o.name.startswith("NH_") and o.name not in keep and o.name not in {"NH_Cam_Target"}:
        o.hide_render=True
scene.render.resolution_x=900; scene.render.resolution_y=900; scene.render.resolution_percentage=100
scene.camera=cam
target.location=Vector((0.72,-0.23,1.22))
views=[("_hand_close_front",Vector((0.72,-1.55,1.34))),
       ("_hand_close_threeq",Vector((1.55,-1.10,1.38))),
       ("_hand_close_back",Vector((0.72,1.05,1.34)))]
for name,pos in views:
    cam.location=pos
    bpy.context.view_layer.update()
    scene.render.filepath=os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
    print("rendered",name)
for o in scene.objects:
    if o.name in old: o.hide_render=old[o.name]
