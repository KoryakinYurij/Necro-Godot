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
         res=(1200, 1500), note="full body, front"),
    dict(name="hero_three_quarter", objects=hero, azimuth=32.0, elevation=9.0, margin=0.04,
         res=(1200, 1500), note="full body, three quarter"),
    dict(name="hero_head_detail", objects=subset("NH_Hood", "NH_Skull", "NH_Face", "NH_Eye",
                                                 "NH_Nose", "NH_Jaw", "NH_Tooth"),
         azimuth=22.0, elevation=4.0, margin=0.07, res=(1100, 1100), note="hood and skull"),
    dict(name="hero_staff_lantern", objects=subset("NH_Staff_Skull", "NH_Staff_Jaw",
                                                   "NH_Staff_Eye", "NH_Staff_Cage",
                                                   "NH_Staff_Flame"),
         azimuth=18.0, elevation=3.0, margin=0.10, res=(1100, 1100), note="staff lantern"),
]


def bbox_center(objects):
    xs, ys, zs = [], [], []
    for obj in objects:
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            xs.append(world.x)
            ys.append(world.y)
            zs.append(world.z)
    return mathutils.Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2,
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


def measure(distance, center, objects, azimuth, elevation):
    target.location = center
    place_azimuth(camera, distance, azimuth, elevation, center)
    bpy.context.view_layer.update()
    return project(objects)


def numeric_offset(distance, center, objects, azimuth, elevation):
    u0, u1, v0, v1 = measure(distance, center, objects, azimuth, elevation)
    cx, cy = (u0 + u1) / 2, (v0 + v1) / 2
    step = 0.1
    shifted_z = measure(distance, center + mathutils.Vector((0, 0, step)), objects,
                        azimuth, elevation)
    dcy_dz = ((shifted_z[2] + shifted_z[3]) / 2 - cy) / step
    shifted_x = measure(distance, center + mathutils.Vector((step, 0, 0)), objects,
                        azimuth, elevation)
    dcx_dx = ((shifted_x[0] + shifted_x[1]) / 2 - cx) / step
    offset = mathutils.Vector((0.0, 0.0, 0.0))
    if abs(dcy_dz) > 1e-6:
        offset.z = (0.5 - cy) / dcy_dz
    if abs(dcx_dx) > 1e-6:
        offset.x = (0.5 - cx) / dcx_dx
    return offset, cx, cy


for view in VIEWS:
    azimuth, elevation, margin = view["azimuth"], view["elevation"], view["margin"]
    objects = view["objects"]
    scene.render.resolution_x, scene.render.resolution_y = view["res"]
    center = bbox_center(objects)
    span = max((max(o.dimensions.z for o in objects), 0.5))
    distance = 4.0 * span
    allowed = 1.0 - 2.0 * margin

    for iteration in range(40):
        u0, u1, v0, v1 = measure(distance, center, objects, azimuth, elevation)
        factor = max((u1 - u0) / allowed, (v1 - v0) / allowed)
        if abs(factor - 1.0) > 0.002:
            distance *= 1.0 + (factor - 1.0) * 0.9
        offset, cx, cy = numeric_offset(distance, center, objects, azimuth, elevation)
        center = center + offset * 0.9
        if abs(factor - 1.0) < 0.004 and abs(cx - 0.5) < 0.003 and abs(cy - 0.5) < 0.003:
            break

    u0, u1, v0, v1 = measure(distance, center, objects, azimuth, elevation)
    view["final"] = dict(distance=distance, center=center)
    print("%-20s %-24s iters=%2d distance=%.2f margins L%.1f%% R%.1f%% B%.1f%% T%.1f%%"
          % (view["name"], view["note"], iteration + 1, distance,
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
    print("rendered %-20s %8d bytes" % (view["name"], os.path.getsize(scene.render.filepath)))


def load_pixels(path):
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    buffer = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(buffer)
    bpy.data.images.remove(image)
    return buffer.reshape(height, width, 4)


print("\n=== hero pixel contribution ===")
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
    print("%-20s %dx%d hero covers %.1f%% of frame | peak diff %.3f"
          % (view["name"], width, height, 100.0 * mask.sum() / (width * height),
             float(difference.max())))
    os.remove(clean_path)

# --- refresh asset metadata with the post-polish numbers -------------------
root = bpy.data.objects["NH_Root"]
tris = 0
verts = 0
for obj in hero:
    verts += len(obj.data.vertices)
    tris += sum(len(p.vertices) - 2 for p in obj.data.polygons)
root["nh_triangles"] = tris
root["nh_vertices"] = verts
root["nh_parts"] = len(hero)
root["nh_render_views"] = ", ".join(v["name"] for v in VIEWS)
root["nh_render_dir"] = OUT_DIR
print("\nasset now: %d parts, %d verts, %d triangles" % (len(hero), verts, tris))

readme = bpy.data.texts["README_NH_Hero"]
text = readme.as_string()
text = text.replace("2818 triangles", "%d triangles" % tris)
text += ("\nPreview views\n"
         "-------------\n"
         "hero_front           full body, straight on\n"
         "hero_three_quarter   full body, 3/4 view (camera parks here)\n"
         "hero_head_detail     hood, skull and teeth\n"
         "hero_staff_lantern   staff skull lantern and flame\n"
         "Framing is auto-fitted from projected vertex extents, so no part is\n"
         "clipped: run 09/10-style fitting again after any silhouette change.\n")
readme.clear()
readme.write(text)

final = VIEWS[1]["final"]
target.location = final["center"]
place_azimuth(camera, final["distance"], VIEWS[1]["azimuth"], VIEWS[1]["elevation"],
              final["center"])
bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
for entry in sorted(os.listdir(OUT_DIR)):
    print("  ", entry, os.path.getsize(os.path.join(OUT_DIR, entry)), "bytes")
