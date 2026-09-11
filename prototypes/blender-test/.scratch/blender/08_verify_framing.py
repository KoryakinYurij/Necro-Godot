import bpy
import math
import mathutils
import numpy as np
import os
from bpy_extras.object_utils import world_to_camera_view

scene = bpy.data.scenes["NecroHero_Asset"]
OUT_DIR = r"C:\Users\Fixed\Documents\NecroHero\renders"
camera = bpy.data.objects["NH_Preview_Cam"]
target = bpy.data.objects["NH_Cam_Target"]
hero_meshes = [o for o in scene.objects
               if o.type == "MESH" and o.name.startswith("NH_")
               and not o.name.startswith("NH_Studio")]


def place_azimuth(obj, distance, azimuth_deg, elevation_deg, center):
    azimuth = math.radians(azimuth_deg)
    elevation = math.radians(elevation_deg)
    offset = mathutils.Vector((
        math.sin(azimuth) * math.cos(elevation),
        -math.cos(azimuth) * math.cos(elevation),
        math.sin(elevation),
    )) * distance
    obj.location = mathutils.Vector(center) + offset


def load_pixels(path):
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    buffer = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(buffer)
    bpy.data.images.remove(image)
    return buffer.reshape(height, width, 4)


VIEWS = [
    dict(name="hero_front", azimuth=0.0, elevation=6.0, distance=7.0,
         center=(0.0, 0.0, 1.75), res=(1200, 1500)),
    dict(name="hero_three_quarter", azimuth=32.0, elevation=9.0, distance=7.0,
         center=(0.0, 0.0, 1.75), res=(1200, 1500)),
    dict(name="hero_head_detail", azimuth=22.0, elevation=4.0, distance=1.85,
         center=(0.0, 0.0, 2.55), res=(1100, 1100)),
    dict(name="hero_staff_detail", azimuth=18.0, elevation=2.0, distance=1.5,
         center=(0.78, -0.23, 3.25), res=(1100, 1100)),
]

print("=== projected hero extents (deterministic, every vertex) ===")
for view in VIEWS:
    target.location = view["center"]
    place_azimuth(camera, view["distance"], view["azimuth"], view["elevation"], view["center"])
    scene.render.resolution_x, scene.render.resolution_y = view["res"]
    bpy.context.view_layer.update()

    us, vs, behind = [], [], 0
    for obj in hero_meshes:
        matrix = obj.matrix_world
        for vertex in obj.data.vertices:
            projected = world_to_camera_view(scene, camera, matrix @ vertex.co)
            if projected.z <= 0.0:
                behind += 1
                continue
            us.append(projected.x)
            vs.append(projected.y)

    left, right = min(us), max(us)
    bottom, top = min(vs), max(vs)
    outside = int(left < 0.0 or right > 1.0 or bottom < 0.0 or top > 1.0)
    print("%-20s x %.3f..%.3f  y %.3f..%.3f | margins L%.1f%% R%.1f%% B%.1f%% T%.1f%% | "
          "behind-camera verts %d | clipped: %s"
          % (view["name"], left, right, bottom, top,
             100 * left, 100 * (1 - right), 100 * bottom, 100 * (1 - top),
             behind, "YES" if outside else "no"))

print("\n=== hero contribution to the rendered frame (diff vs clean plate) ===")
for view in VIEWS[:2] + VIEWS[2:]:
    if view["name"] not in ("hero_front", "hero_head_detail"):
        continue
    target.location = view["center"]
    place_azimuth(camera, view["distance"], view["azimuth"], view["elevation"], view["center"])
    scene.render.resolution_x, scene.render.resolution_y = view["res"]
    bpy.context.view_layer.update()

    for obj in hero_meshes:
        obj.hide_render = True
    clean_path = os.path.join(OUT_DIR, "_cleanplate.png")
    scene.render.filepath = clean_path
    bpy.ops.render.render(write_still=True)
    for obj in hero_meshes:
        obj.hide_render = False

    with_hero = load_pixels(os.path.join(OUT_DIR, view["name"] + ".png"))
    without = load_pixels(clean_path)
    height, width = with_hero.shape[0], with_hero.shape[1]
    difference = np.abs(with_hero[:, :, :3] - without[:, :, :3]).max(axis=2)
    mask = difference > 0.05
    coverage = 100.0 * mask.sum() / (width * height)
    print("%-20s changed pixels %.1f%% of frame | diff p50=%.4f p99=%.4f max=%.4f"
          % (view["name"], coverage,
             float(np.percentile(difference, 50)), float(np.percentile(difference, 99)),
             float(difference.max())))
    os.remove(clean_path)

print("\nrenders dir:")
for entry in sorted(os.listdir(OUT_DIR)):
    print("  ", entry, os.path.getsize(os.path.join(OUT_DIR, entry)), "bytes")
