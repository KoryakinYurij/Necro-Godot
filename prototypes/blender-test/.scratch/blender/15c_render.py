import bpy
import math
import mathutils
import os

scene = bpy.data.scenes["NecroHero_Asset"]
OUT_DIR = r"C:\Users\Fixed\Documents\NecroHero\renders"
camera = bpy.data.objects["NH_Preview_Cam"]
target = bpy.data.objects["NH_Cam_Target"]

VIEWS = [
    ("hero_front", 0.0, 6.0, 7.19, (0.0, 0.0, 1.83), (1200, 1500)),
    ("hero_three_quarter", 32.0, 9.0, 7.21, (0.0, 0.0, 1.83), (1200, 1500)),
    ("hero_head_detail", 22.0, 4.0, 2.27, (0.0, -0.02, 2.62), (1100, 1100)),
    ("hero_staff_lantern", 18.0, 3.0, 1.81, (0.78, -0.23, 3.30), (1100, 1100)),
]


def place_azimuth(obj, distance, azimuth_deg, elevation_deg, center):
    azimuth = math.radians(azimuth_deg)
    elevation = math.radians(elevation_deg)
    offset = mathutils.Vector((
        math.sin(azimuth) * math.cos(elevation),
        -math.cos(azimuth) * math.cos(elevation),
        math.sin(elevation),
    )) * distance
    obj.location = mathutils.Vector(center) + offset


for name, azimuth, elevation, distance, center, resolution in VIEWS:
    target.location = center
    place_azimuth(camera, distance, azimuth, elevation, center)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.filepath = os.path.join(OUT_DIR, name + ".png")
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    print("rendered %-20s %8d bytes" % (name, os.path.getsize(scene.render.filepath)))

final = VIEWS[1]
target.location = final[4]
place_azimuth(camera, final[3], final[1], final[2], final[4])
bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
