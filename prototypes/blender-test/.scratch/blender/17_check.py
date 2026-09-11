import bpy
import math
import mathutils
import os
from bpy_extras.object_utils import world_to_camera_view

scene = bpy.data.scenes["NecroHero_Asset"]
CHECK_DIR = r"D:\Code AI\Games\Necro-Godot\prototypes\blender-test\.scratch\preview\checks"
os.makedirs(CHECK_DIR, exist_ok=True)
camera = bpy.data.objects["NH_Preview_Cam"]
target = bpy.data.objects["NH_Cam_Target"]

PARTIAL = ["NH_Pauldron", "NH_Upper_Mantle", "NH_Hood", "NH_Arm_Front", "NH_Arm_Front_Cuff",
           "NH_Arm_Back", "NH_Arm_Back_Cuff", "NH_Hand_Front", "NH_Hand_Back", "NH_Staff",
           "NH_Staff_Grip", "NH_Ragged_Robe", "NH_Belt"]

print("=== upper body geometry (world space) ===")
for name in PARTIAL:
    obj = bpy.data.objects.get(name)
    if obj is None:
        print(name, "MISSING")
        continue
    corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    material = obj.material_slots[0].material.name if obj.material_slots else "-"
    print("%-20s x %6.3f..%6.3f  y %6.3f..%6.3f  z %6.3f..%6.3f  %s"
          % (name, min(c.x for c in corners), max(c.x for c in corners),
             min(c.y for c in corners), max(c.y for c in corners),
             min(c.z for c in corners), max(c.z for c in corners), material))

VIEWS = [
    dict(name="_check_shoulder", objects=["NH_Pauldron", "NH_Upper_Mantle", "NH_Hood",
                                          "NH_Arm_Front", "NH_Arm_Front_Cuff",
                                          "NH_Hand_Front", "NH_Ragged_Robe"],
         azimuth=35.0, elevation=12.0, margin=0.06),
    dict(name="_check_neck", objects=["NH_Hood", "NH_Skull", "NH_Upper_Mantle", "NH_Ragged_Robe",
                                      "NH_Pauldron"],
         azimuth=20.0, elevation=2.0, margin=0.06),
    dict(name="_check_hand", objects=["NH_Hand_Front", "NH_Arm_Front", "NH_Arm_Front_Cuff",
                                      "NH_Staff", "NH_Staff_Grip"],
         azimuth=55.0, elevation=10.0, margin=0.12),
    dict(name="_check_hand_side", objects=["NH_Hand_Front", "NH_Staff", "NH_Staff_Grip",
                                           "NH_Ragged_Robe"],
         azimuth=150.0, elevation=6.0, margin=0.12),
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


def measure(distance, center, objects, azimuth, elevation):
    target.location = center
    place_azimuth(camera, distance, azimuth, elevation, center)
    bpy.context.view_layer.update()
    return project(objects)


def fit(objects, azimuth, elevation, margin):
    center = bbox_center(objects)
    distance = 2.5 * max(max(o.dimensions.z for o in objects), 0.4)
    allowed = 1.0 - 2.0 * margin
    for _ in range(40):
        u0, u1, v0, v1 = measure(distance, center, objects, azimuth, elevation)
        factor = max((u1 - u0) / allowed, (v1 - v0) / allowed)
        if abs(factor - 1.0) > 0.002:
            distance *= 1.0 + (factor - 1.0) * 0.9
        u0, u1, v0, v1 = measure(distance, center, objects, azimuth, elevation)
        cx, cy = (u0 + u1) / 2, (v0 + v1) / 2
        step = 0.05
        shifted_z = measure(distance, center + mathutils.Vector((0, 0, step)), objects,
                            azimuth, elevation)
        dcy_dz = ((shifted_z[2] + shifted_z[3]) / 2 - cy) / step
        shifted_x = measure(distance, center + mathutils.Vector((step, 0, 0)), objects,
                            azimuth, elevation)
        dcx_dx = ((shifted_x[0] + shifted_x[1]) / 2 - cx) / step
        if abs(dcy_dz) > 1e-6:
            center = center + mathutils.Vector((0, 0, (0.5 - cy) / dcy_dz * 0.9))
        if abs(dcx_dx) > 1e-6:
            center = center + mathutils.Vector(((0.5 - cx) / dcx_dx * 0.9, 0, 0))
        if abs(factor - 1.0) < 0.004 and abs(cx - 0.5) < 0.003 and abs(cy - 0.5) < 0.003:
            break
    return distance, center


print("\n=== check renders ===")
for view in VIEWS:
    objects = [bpy.data.objects[n] for n in view["objects"]]
    distance, center = fit(objects, view["azimuth"], view["elevation"], view["margin"])
    target.location = center
    place_azimuth(camera, distance, view["azimuth"], view["elevation"], center)
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.filepath = os.path.join(CHECK_DIR, view["name"] + ".png")
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)

    image = bpy.data.images.load(scene.render.filepath, check_existing=False)
    image.scale(700, 700)
    previous = (scene.render.image_settings.file_format, scene.render.image_settings.quality)
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 88
    image.filepath_raw = os.path.join(CHECK_DIR, view["name"] + ".jpg")
    image.file_format = "JPEG"
    image.save()
    scene.render.image_settings.file_format, scene.render.image_settings.quality = previous
    bpy.data.images.remove(image)
    print("check view %-18s distance %.2f center %s"
          % (view["name"], distance, tuple(round(v, 2) for v in center)))

print("\nchecks written to", CHECK_DIR)
