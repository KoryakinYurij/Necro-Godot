import bpy
import math
import mathutils
import os
from bpy_extras.object_utils import world_to_camera_view

scene = bpy.data.scenes["NecroHero_Asset"]
OUT_DIR = r"C:\Users\Fixed\Documents\NecroHero\renders"
camera = bpy.data.objects["NH_Preview_Cam"]
target = bpy.data.objects["NH_Cam_Target"]

# --- 1. Lighting: dark, contrasty, rim-driven -----------------------------
world = bpy.data.worlds["NH_Studio_World"]
bg = next(n for n in world.node_tree.nodes if n.bl_idname == "ShaderNodeBackground")
bg.inputs["Strength"].default_value = 0.30

ramp = next(n for n in world.node_tree.nodes if n.bl_idname == "ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.004, 0.005, 0.009, 1.0)
ramp.color_ramp.elements[1].color = (0.026, 0.032, 0.048, 1.0)
for element in ramp.color_ramp.elements:
    if 0.3 < element.position < 0.5:
        element.color = (0.008, 0.010, 0.016, 1.0)

LIGHTS = {
    "NH_Key_Light": dict(energy=430.0, size=2.6, color=(1.00, 0.93, 0.82),
                         location=(2.9, -3.4, 3.6)),
    "NH_Fill_Light": dict(energy=70.0, size=4.0, color=(0.62, 0.74, 1.00),
                          location=(-3.6, -2.8, 1.9)),
    "NH_Rim_Light": dict(energy=760.0, size=2.2, color=(0.45, 0.95, 0.72),
                         location=(-2.2, 3.4, 3.3)),
    "NH_Soul_Accent": dict(energy=40.0, size=0.30, color=(0.35, 1.00, 0.55),
                           location=(0.78, -0.23, 3.35)),
}
for name, spec in LIGHTS.items():
    light = bpy.data.objects[name]
    light.data.energy = spec["energy"]
    light.data.color = spec["color"]
    if light.data.type == "AREA":
        light.data.size = spec["size"]
    else:
        light.data.shadow_soft_size = spec["size"]
    light.location = spec["location"]
    print("light %-16s energy=%-6.0f color=%s" % (name, spec["energy"], spec["color"]))

scene.view_settings.exposure = -0.35
scene.view_settings.look = "AgX - Medium High Contrast"

floor_mat = bpy.data.materials["NH_Studio_Floor"]
floor_bsdf = next(n for n in floor_mat.node_tree.nodes
                  if n.bl_idname == "ShaderNodeBsdfPrincipled")
floor_bsdf.inputs["Base Color"].default_value = (0.018, 0.017, 0.024, 1.0)
floor_bsdf.inputs["Roughness"].default_value = 0.62
print("floor albedo:", tuple(round(v, 3) for v in floor_bsdf.inputs["Base Color"].default_value))
print("world strength:", bg.inputs["Strength"].default_value,
      "| exposure:", scene.view_settings.exposure)

# --- 2. Material fixes driven by the render review -----------------------
TWEAKS = {
    "NH_Gold": dict(base=(1.000, 0.780, 0.350), rough=0.34, metallic=1.0, coat=0.15),
    "NH_Bone": dict(base=(0.800, 0.730, 0.580), rough=0.50, coat=0.0, subsurface=0.10),
    "NH_Bone_High": dict(base=(0.900, 0.850, 0.700), rough=0.45, coat=0.12, subsurface=0.12),
    "NH_Robe": dict(sheen=0.22),
    "NH_Robe_Light": dict(sheen=0.28),
    "NH_Soul": dict(base=(0.035, 0.300, 0.130), rough=0.35, alpha=0.60,
                    emission=(0.160, 1.000, 0.420), emission_strength=2.2),
    "NH_Soul_Core": dict(base=(0.550, 0.950, 0.650), emission=(0.550, 1.000, 0.720),
                         emission_strength=6.0),
    "NH_Rune": dict(emission=(0.070, 0.850, 0.300), emission_strength=1.6),
}

for name, spec in TWEAKS.items():
    material = bpy.data.materials[name]
    bsdf = next(n for n in material.node_tree.nodes
                if n.bl_idname == "ShaderNodeBsdfPrincipled")
    inputs = bsdf.inputs
    if "base" in spec:
        base = spec["base"]
        inputs["Base Color"].default_value = (base[0], base[1], base[2], 1.0)
        material.diffuse_color = (base[0], base[1], base[2], spec.get("alpha", 1.0))
    for key, socket in (("rough", "Roughness"), ("metallic", "Metallic"),
                        ("sheen", "Sheen Weight"), ("coat", "Coat Weight"),
                        ("subsurface", "Subsurface Weight")):
        if key in spec and socket in inputs:
            inputs[socket].default_value = spec[key]
    if "emission" in spec:
        colour = spec["emission"]
        inputs["Emission Color"].default_value = (colour[0], colour[1], colour[2], 1.0)
    if "emission_strength" in spec and "Emission Strength" in inputs:
        inputs["Emission Strength"].default_value = spec["emission_strength"]
    if "alpha" in spec and "Alpha" in inputs:
        inputs["Alpha"].default_value = spec["alpha"]
    material.roughness = spec.get("rough", material.roughness)
    material.metallic = spec.get("metallic", material.metallic)
    print("%-14s tuned: %s" % (name, sorted(spec)))

# --- 3. Re-render the four views -----------------------------------------
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

bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
