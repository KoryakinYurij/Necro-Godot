import bpy
import math
import mathutils
import os
from bpy_extras.object_utils import world_to_camera_view

scene = bpy.data.scenes["NecroHero_Asset"]
OUT_DIR = r"C:\Users\Fixed\Documents\NecroHero\renders"
EXPORT = r"C:\Users\Fixed\Documents\NecroHero\necro_hero_prototype_v2.glb"
camera = bpy.data.objects["NH_Preview_Cam"]
target = bpy.data.objects["NH_Cam_Target"]
root = bpy.data.objects["NH_Root"]
hero = [o for o in scene.objects
        if o.type == "MESH" and o.name.startswith("NH_") and not o.name.startswith("NH_Studio")]


def subset(*prefixes):
    return [o for o in hero if o.name.startswith(prefixes)]


# The head shot now frames the face itself (no hood peak) so the skull is
# centred instead of pushed to the lower edge.
VIEWS = [
    dict(name="hero_front", objects=hero, azimuth=0.0, elevation=6.0, margin=0.04,
         res=(1200, 1500)),
    dict(name="hero_three_quarter", objects=hero, azimuth=32.0, elevation=9.0, margin=0.04,
         res=(1200, 1500)),
    dict(name="hero_head_detail", objects=subset("NH_Skull", "NH_Jaw", "NH_Face", "NH_Eye",
                                                 "NH_Nose", "NH_Tooth", "NH_Hood_Gold_Trim"),
         azimuth=22.0, elevation=3.0, margin=0.06, res=(1100, 1100)),
    dict(name="hero_staff_lantern", objects=subset("NH_Staff_Skull", "NH_Staff_Jaw",
                                                   "NH_Staff_Eye", "NH_Staff_Cage",
                                                   "NH_Staff_Flame"),
         azimuth=18.0, elevation=3.0, margin=0.10, res=(1100, 1100)),
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


def fit(view):
    objects = view["objects"]
    azimuth, elevation, margin = view["azimuth"], view["elevation"], view["margin"]
    scene.render.resolution_x, scene.render.resolution_y = view["res"]
    center = bbox_center(objects)
    distance = 4.0 * max(max(o.dimensions.z for o in objects), 0.5)
    allowed = 1.0 - 2.0 * margin
    for _ in range(40):
        u0, u1, v0, v1 = measure(distance, center, objects, azimuth, elevation)
        factor = max((u1 - u0) / allowed, (v1 - v0) / allowed)
        if abs(factor - 1.0) > 0.002:
            distance *= 1.0 + (factor - 1.0) * 0.9
        u0, u1, v0, v1 = measure(distance, center, objects, azimuth, elevation)
        cx, cy = (u0 + u1) / 2, (v0 + v1) / 2
        step = 0.1
        shifted_z = measure(distance, center + mathutils.Vector((0, 0, step)),
                            objects, azimuth, elevation)
        dcy_dz = ((shifted_z[2] + shifted_z[3]) / 2 - cy) / step
        shifted_x = measure(distance, center + mathutils.Vector((step, 0, 0)),
                            objects, azimuth, elevation)
        dcx_dx = ((shifted_x[0] + shifted_x[1]) / 2 - cx) / step
        if abs(dcy_dz) > 1e-6:
            center = center + mathutils.Vector((0, 0, (0.5 - cy) / dcy_dz * 0.9))
        if abs(dcx_dx) > 1e-6:
            center = center + mathutils.Vector(((0.5 - cx) / dcx_dx * 0.9, 0, 0))
        if abs(factor - 1.0) < 0.004 and abs(cx - 0.5) < 0.003 and abs(cy - 0.5) < 0.003:
            break
    u0, u1, v0, v1 = measure(distance, center, objects, azimuth, elevation)
    view["final"] = (distance, center)
    print("%-20s distance %.2f margins L%.1f%% R%.1f%% B%.1f%% T%.1f%%"
          % (view["name"], distance, 100 * u0, 100 * (1 - u1), 100 * v0, 100 * (1 - v1)))


print("=== framing ===")
for view in VIEWS:
    fit(view)

print("\n=== rendering ===")
for view in VIEWS:
    distance, center = view["final"]
    target.location = center
    place_azimuth(camera, distance, view["azimuth"], view["elevation"], center)
    scene.render.resolution_x, scene.render.resolution_y = view["res"]
    scene.render.filepath = os.path.join(OUT_DIR, view["name"] + ".png")
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    print("rendered %-20s %8d bytes" % (view["name"], os.path.getsize(scene.render.filepath)))

# --- metadata ------------------------------------------------------------
verts = sum(len(o.data.vertices) for o in hero)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in hero)
root["nh_triangles"] = tris
root["nh_vertices"] = verts
root["nh_parts"] = len(hero)
root["nh_look"] = ("dark violet cloth, warm bone, saturated green soul emission with "
                   "bloom, stylised gold; PBR Neutral view transform, 96 EEVEE samples")
print("\nasset: %d parts, %d verts, %d tris" % (len(hero), verts, tris))

readme = bpy.data.texts["README_NH_Hero"]
text = readme.as_string()
for old in ("2818 triangles", "4036 triangles"):
    text = text.replace(old, "%d triangles" % tris)
if "Preview views" in text:
    text = text.split("Preview views")[0]
text += ("Preview views\n"
         "-------------\n"
         "hero_front           full body, straight on\n"
         "hero_three_quarter   full body, 3/4 view (camera parks here)\n"
         "hero_head_detail     skull, teeth, glowing eyes and gold trim\n"
         "hero_staff_lantern   staff skull lantern and flame\n"
         "Framing is auto-fitted from projected vertex extents, so nothing is\n"
         "clipped; refit after any silhouette change.\n"
         "\nLook\n"
         "----\n"
         "* Dark violet cloth with sheen and procedural weave bump, warm bone with\n"
         "  subsurface, saturated green soul emission (translucent), stylised gold\n"
         "  at metallic 0.85 so it still reads as gold under a dark studio world.\n"
         "* Studio: EEVEE, 96 samples, bloom glare in the compositor, camera parks\n"
         "  on the three-quarter view. PBR Neutral view transform keeps albedo\n"
         "  faithful instead of desaturating it.\n")
readme.clear()
readme.write(text)

# --- export -------------------------------------------------------------
view_layer = bpy.context.view_layer
view_layer.active_layer_collection = view_layer.layer_collection.children[
    "Agent_Generated_NecroHero"]
bpy.ops.export_scene.gltf(filepath=EXPORT, export_format="GLB", use_active_collection=True,
                          use_selection=False, use_visible=False, export_apply=False,
                          export_yup=True, export_materials="EXPORT", export_animations=False,
                          export_cameras=False, export_lights=False, export_extras=True,
                          export_normals=True, export_texcoords=True)
print("exported:", EXPORT, os.path.getsize(EXPORT), "bytes")

final = VIEWS[1]["final"]
target.location = final[1]
place_azimuth(camera, final[0], VIEWS[1]["azimuth"], VIEWS[1]["elevation"], final[1])
bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
