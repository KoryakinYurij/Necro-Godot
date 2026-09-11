import bpy
import math
import mathutils
import numpy as np
import os
from bpy_extras.object_utils import world_to_camera_view

scene = bpy.data.scenes["NecroHero_Asset"]
OUT_DIR = r"C:\Users\Fixed\Documents\NecroHero\renders"
os.makedirs(OUT_DIR, exist_ok=True)
camera = bpy.data.objects["NH_Preview_Cam"]
target = bpy.data.objects["NH_Cam_Target"]
hero = [o for o in scene.objects
        if o.type == "MESH" and o.name.startswith("NH_") and not o.name.startswith("NH_Studio")]


def subset(*prefixes):
    return [o for o in hero if o.name.startswith(prefixes)]


VIEWS = [
    dict(name="hero_front", objects=hero, azimuth=0.0, elevation=6.0, margin=0.04,
         res=(1200, 1500)),
    dict(name="hero_three_quarter", objects=hero, azimuth=32.0, elevation=9.0, margin=0.04,
         res=(1200, 1500)),
    dict(name="hero_head_detail", objects=subset("NH_Hood", "NH_Skull", "NH_Face", "NH_Eye",
                                                 "NH_Nose", "NH_Jaw", "NH_Tooth"),
         azimuth=22.0, elevation=4.0, margin=0.07, res=(1100, 1100)),
    dict(name="hero_staff_detail", objects=subset("NH_Staff"), azimuth=18.0, elevation=2.0,
         margin=0.07, res=(1100, 1100)),
]


def bbox_center(objects):
    xs, ys, zs = [], [], []
    for obj in objects:
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            xs.append(world.x)
            ys.append(world.y)
            zs.append(world.z)
    return mathutils.Vector(((min(xs) + max(xs)) / 2,
                             (min(ys) + max(ys)) / 2,
                             (min(zs) + max(zs)) / 2))


def place_azimuth(obj, distance, azimuth_deg, elevation_deg, center):
    azimuth = math.radians(azimuth_deg)
    elevation = math.radians(elevation_deg)
    offset = mathutils.Vector((
        math.sin(azimuth) * math.cos(elevation),
        -math.cos(azimuth) * math.cos(elevation),
        math.sin(elevation),
    )) * distance
    obj.location = mathutils.Vector(center) + offset


def project(objects):
    us, vs = [], []
    for obj in objects:
        matrix = obj.matrix_world
        for vertex in obj.data.vertices:
            point = world_to_camera_view(scene, camera, matrix @ vertex.co)
            if point.z > 0.0:
                us.append(point.x)
                vs.append(point.y)
    return min(us), max(us), min(vs), max(vs)


def measure(distance, center, objects):
    target.location = center
    place_azimuth(camera, distance, azimuth, elevation, center)
    bpy.context.view_layer.update()
    return project(objects)


for view in VIEWS:
    azimuth = view["azimuth"]
    elevation = view["elevation"]
    margin = view["margin"]
    objects = view["objects"]
    scene.render.resolution_x, scene.render.resolution_y = view["res"]

    center = bbox_center(objects)
    size = max(objects[0].dimensions.z, 1.0)
    distance = 6.0 * size
    for iteration in range(12):
        u0, u1, v0, v1 = measure(distance, center, objects)
        span_u, span_v = max(u1 - u0, 1e-6), max(v1 - v0, 1e-6)
        allowed = 1.0 - 2.0 * margin
        factor = max(span_u / allowed, span_v / allowed)
        distance *= factor
        u0, u1, v0, v1 = measure(distance, center, objects)
        # Re-centre both axes using a numeric derivative in world units.
        step = 0.15
        _, _, _, v1_z = measure(distance, center + mathutils.Vector((0, 0, step)), objects)
        cy = (v0 + v1) / 2
        cy_z = (v0 + v1_z) / 2
        dcy_dz = (cy_z - cy) / step
        u0_x, u1_x, _, _ = measure(distance, center + mathutils.Vector((step, 0, 0)), objects)
        cx = (u0 + u1) / 2
        cx_x = (u0_x + u1_x) / 2
        dcx_dx = (cx_x - cx) / step
        if abs(dcy_dz) > 1e-6:
            center = center + mathutils.Vector((0, 0, (0.5 - cy) / dcy_dz))
        if abs(dcx_dx) > 1e-6:
            center = center + mathutils.Vector(((0.5 - cx) / dcx_dx, 0, 0))
        if abs(cy - 0.5) < 0.002 and abs(cx - 0.5) < 0.002 and abs(factor - 1.0) < 0.01:
            break

    u0, u1, v0, v1 = measure(distance, center, objects)
    view["final"] = dict(distance=distance, center=center, extents=(u0, u1, v0, v1),
                         iterations=iteration + 1)
    print("%-20s fitted in %d iters | distance %.2f | x %.3f..%.3f y %.3f..%.3f | margins "
          "L%.1f%% R%.1f%% B%.1f%% T%.1f%%"
          % (view["name"], iteration + 1, distance, u0, u1, v0, v1,
             100 * u0, 100 * (1 - u1), 100 * v0, 100 * (1 - v1)))

print("\n=== rendering ===")
for view in VIEWS:
    final = view["final"]
    target.location = final["center"]
    place_azimuth(camera, final["distance"], view["azimuth"], view["elevation"], final["center"])
    scene.render.resolution_x, scene.render.resolution_y = view["res"]
    scene.render.filepath = os.path.join(OUT_DIR, view["name"] + ".png")
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    print("rendered", view["name"], os.path.getsize(scene.render.filepath), "bytes")


def load_pixels(path):
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    buffer = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(buffer)
    bpy.data.images.remove(image)
    return buffer.reshape(height, width, 4)


print("\n=== hero pixel contribution (render diff vs clean plate) ===")
for view in VIEWS:
    final = view["final"]
    target.location = final["center"]
    place_azimuth(camera, final["distance"], view["azimuth"], view["elevation"], final["center"])
    scene.render.resolution_x, scene.render.resolution_y = view["res"]
    bpy.context.view_layer.update()
    for obj in hero:
        obj.hide_render = True
    clean_path = os.path.join(OUT_DIR, "_cleanplate.png")
    scene.render.filepath = clean_path
    bpy.ops.render.render(write_still=True)
    for obj in hero:
        obj.hide_render = False

    with_hero = load_pixels(os.path.join(OUT_DIR, view["name"] + ".png"))
    without = load_pixels(clean_path)
    height, width = with_hero.shape[0], with_hero.shape[1]
    difference = np.abs(with_hero[:, :, :3] - without[:, :, :3]).max(axis=2)
    mask = difference > 0.05
    coverage = 100.0 * mask.sum() / (width * height)
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    bbox = (int(cols[0]), int(cols[-1]), int(rows[0]), int(rows[-1])) if len(rows) and len(cols) else None
    print("%-20s %dx%d changed=%.1f%% | silhouette bbox (l,r,b,t)=%s | max diff %.3f"
          % (view["name"], width, height, coverage, bbox, float(difference.max())))
    os.remove(clean_path)

# Leave the file parked on the three-quarter body view.
final = VIEWS[1]["final"]
target.location = final["center"]
place_azimuth(camera, final["distance"], VIEWS[1]["azimuth"], VIEWS[1]["elevation"],
              final["center"])
camera["nh_view"] = "three_quarter"
scene.render.filepath = os.path.join(OUT_DIR, "hero_three_quarter.png")
bpy.ops.wm.save_mainfile()
print("\nsaved:", bpy.data.filepath)
for entry in sorted(os.listdir(OUT_DIR)):
    print("  ", entry, os.path.getsize(os.path.join(OUT_DIR, entry)), "bytes")
