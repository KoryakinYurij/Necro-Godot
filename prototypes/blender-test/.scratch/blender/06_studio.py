import bpy
import math
import mathutils

scene = bpy.data.scenes["NecroHero_Asset"]

# --- 1. Studio world: dark gradient backdrop -------------------------------
world = bpy.data.worlds.get("NH_Studio_World") or bpy.data.worlds.new("NH_Studio_World")
world.use_nodes = True
tree = world.node_tree
tree.nodes.clear()

out = tree.nodes.new("ShaderNodeOutputWorld")
out.location = (500, 0)
bg = tree.nodes.new("ShaderNodeBackground")
bg.location = (280, 0)
bg.inputs["Strength"].default_value = 0.9
tree.links.new(bg.outputs["Background"], out.inputs["Surface"])

coords = tree.nodes.new("ShaderNodeTexCoord")
coords.location = (-600, 0)
separate = tree.nodes.new("ShaderNodeSeparateXYZ")
separate.location = (-420, 0)
ramp = tree.nodes.new("ShaderNodeValToRGB")
ramp.location = (-60, 0)
ramp.color_ramp.elements[0].position = 0.0
ramp.color_ramp.elements[0].color = (0.010, 0.012, 0.020, 1.0)
ramp.color_ramp.elements[1].position = 1.0
ramp.color_ramp.elements[1].color = (0.075, 0.090, 0.130, 1.0)
mid = ramp.color_ramp.elements.new(0.42)
mid.color = (0.030, 0.035, 0.055, 1.0)
tree.links.new(coords.outputs["Generated"], separate.inputs["Vector"])
tree.links.new(separate.outputs["Z"], ramp.inputs["Fac"])
tree.links.new(ramp.outputs["Color"], bg.inputs["Color"])
scene.world = world
print("world:", world.name, "nodes:", len(tree.nodes))

# --- 2. Studio collection --------------------------------------------------
studio = bpy.data.collections.get("NH_Studio")
if studio is None:
    studio = bpy.data.collections.new("NH_Studio")
    scene.collection.children.link(studio)
studio["nh_export_exclude"] = True
studio["nh_purpose"] = "Preview camera, light rig, backdrop. Not part of the character."


def link(obj, collection):
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def track_to(obj, target, axis="TRACK_NEGATIVE_Z"):
    for constraint in list(obj.constraints):
        obj.constraints.remove(constraint)
    constraint = obj.constraints.new("TRACK_TO")
    constraint.name = "NH_Track_Target"
    constraint.target = target
    constraint.track_axis = axis
    constraint.up_axis = "UP_Y"
    return constraint


# --- 3. Camera target, camera ---------------------------------------------
TARGET = mathutils.Vector((0.0, 0.0, 1.75))
target = bpy.data.objects.get("NH_Cam_Target")
if target is None:
    target = bpy.data.objects.new("NH_Cam_Target", None)
    target.empty_display_type = "SPHERE"
    target.empty_display_size = 0.08
    link(target, studio)
target.location = TARGET

camera = bpy.data.objects.get("NH_Preview_Cam")
if camera is None:
    camera_data = bpy.data.cameras.new("NH_Preview_Cam")
    camera = bpy.data.objects.new("NH_Preview_Cam", camera_data)
    link(camera, studio)
camera.data.lens = 60.0
camera.data.sensor_width = 36.0
camera.data.dof.use_dof = False
track_to(camera, target)


def place_azimuth(obj, distance, azimuth_deg, elevation_deg, center):
    azimuth = math.radians(azimuth_deg)
    elevation = math.radians(elevation_deg)
    offset = mathutils.Vector((
        math.sin(azimuth) * math.cos(elevation),
        -math.cos(azimuth) * math.cos(elevation),
        math.sin(elevation),
    )) * distance
    obj.location = center + offset


place_azimuth(camera, 7.0, 28.0, 8.0, TARGET)
scene.camera = camera
print("camera:", camera.name, "at", tuple(round(v, 2) for v in camera.location))

# --- 4. Three-point light rig + soul accent -------------------------------
LIGHTS = {
    "NH_Key_Light": dict(kind="AREA", energy=600.0, size=3.0, color=(1.00, 0.94, 0.85),
                         location=(3.6, -4.2, 4.4)),
    "NH_Fill_Light": dict(kind="AREA", energy=180.0, size=4.0, color=(0.70, 0.80, 1.00),
                          location=(-4.2, -3.2, 2.2)),
    "NH_Rim_Light": dict(kind="AREA", energy=520.0, size=2.5, color=(0.55, 0.95, 0.80),
                         location=(-1.8, 4.2, 3.6)),
    "NH_Soul_Accent": dict(kind="POINT", energy=90.0, size=0.35, color=(0.35, 1.00, 0.55),
                           location=(0.78, -0.23, 3.35)),
}

for name, spec in LIGHTS.items():
    obj = bpy.data.objects.get(name)
    if obj is None:
        data = bpy.data.lights.new(name, type=spec["kind"])
        obj = bpy.data.objects.new(name, data)
        link(obj, studio)
    obj.data.type = spec["kind"]
    obj.data.energy = spec["energy"]
    obj.data.color = spec["color"]
    if spec["kind"] == "AREA":
        obj.data.shape = "DISK"
        obj.data.size = spec["size"]
        track_to(obj, target if name != "NH_Soul_Accent" else target)
    else:
        obj.data.shadow_soft_size = spec["size"]
    obj.location = spec["location"]
    print("light %-16s %-6s energy=%-6.0f at %s"
          % (name, spec["kind"], spec["energy"], tuple(round(v, 2) for v in obj.location)))

# --- 5. Backdrop floor ----------------------------------------------------
floor = bpy.data.objects.get("NH_Studio_Floor")
if floor is None:
    mesh = bpy.data.meshes.new("NH_Studio_Floor")
    mesh.from_pydata([(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)],
                     [], [(0, 1, 2, 3)])
    mesh.update()
    floor = bpy.data.objects.new("NH_Studio_Floor", mesh)
    link(floor, studio)

floor_mat = bpy.data.materials.get("NH_Studio_Floor")
if floor_mat is None:
    floor_mat = bpy.data.materials.new("NH_Studio_Floor")
floor_mat.use_nodes = True
floor_nodes = floor_mat.node_tree.nodes
floor_bsdf = next((n for n in floor_nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
if floor_bsdf is None:
    floor_bsdf = floor_mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
floor_bsdf.inputs["Base Color"].default_value = (0.030, 0.028, 0.040, 1.0)
floor_bsdf.inputs["Roughness"].default_value = 0.55
floor_mat.diffuse_color = (0.030, 0.028, 0.040, 1.0)
floor.data.materials.clear()
floor.data.materials.append(floor_mat)
floor.hide_render = False
print("floor:", floor.name, "material:", floor_mat.name)

# --- 6. Render settings: reproducible previews ---------------------------
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1200
scene.render.resolution_y = 1500
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.use_persistent_data = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.compression = 15
scene.view_settings.view_transform = "AgX"
try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
scene.view_settings.exposure = 0.2

eevee = getattr(scene, "eevee", None)
if eevee is not None:
    for attr, value in (("taa_render_samples", 96), ("use_raytracing", True),
                        ("use_shadows", True), ("use_volumetric_lights", True)):
        if hasattr(eevee, attr):
            setattr(eevee, attr, value)
    if hasattr(eevee, "shadow_ray_count"):
        eevee.shadow_ray_count = 2
print("render:", scene.render.engine, scene.render.resolution_x, "x", scene.render.resolution_y,
      "| view transform:", scene.view_settings.view_transform, "/", scene.view_settings.look)

print("studio collection objects:", sorted(o.name for o in studio.objects))

bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
