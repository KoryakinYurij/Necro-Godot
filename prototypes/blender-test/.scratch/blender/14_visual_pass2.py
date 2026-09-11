import bpy
import math
import mathutils
import os

scene = bpy.data.scenes["NecroHero_Asset"]
OUT_DIR = r"C:\Users\Fixed\Documents\NecroHero\renders"
camera = bpy.data.objects["NH_Preview_Cam"]
target = bpy.data.objects["NH_Cam_Target"]

# Colour management: PBR Neutral keeps albedo faithful instead of desaturating.
available = [item.identifier for item in
             scene.view_settings.bl_rna.properties["view_transform"].enum_items]
if "Khronos PBR Neutral" in available:
    scene.view_settings.view_transform = "Khronos PBR Neutral"
    scene.view_settings.look = "None"
elif "Standard" in available:
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
scene.view_settings.exposure = -0.1
print("view transform:", scene.view_settings.view_transform, "/", scene.view_settings.look,
      "| exposure:", scene.view_settings.exposure)

TWEAKS = {
    # cloth: sheen and specular were lifting the dark violet into lavender
    "NH_Robe": dict(base=(0.038, 0.016, 0.090), sheen=0.06, specular=0.30, rough=0.84),
    "NH_Robe_Light": dict(base=(0.085, 0.038, 0.175), sheen=0.08, specular=0.32, rough=0.80),
    "NH_Robe_Trim": dict(base=(0.150, 0.065, 0.250), sheen=0.06, specular=0.35, rough=0.66),
    # stylised gold: a pure metal goes black when the studio has little to reflect
    "NH_Gold": dict(base=(1.000, 0.800, 0.360), metallic=0.80, rough=0.35, coat=0.15),
    # bone: warm, not porcelain
    "NH_Bone": dict(base=(0.760, 0.690, 0.540), rough=0.52, coat=0.0, subsurface=0.10),
    "NH_Bone_High": dict(base=(0.860, 0.800, 0.650), rough=0.46, coat=0.10, subsurface=0.12),
    # soul matter: saturated green, translucent, not blown to white
    "NH_Soul": dict(base=(0.030, 0.220, 0.100), rough=0.35, alpha=0.50,
                    emission=(0.120, 0.850, 0.350), emission_strength=1.2),
    "NH_Soul_Core": dict(base=(0.200, 0.600, 0.300),
                         emission=(0.300, 1.000, 0.500), emission_strength=3.5),
    "NH_Rune": dict(base=(0.030, 0.140, 0.070),
                    emission=(0.080, 0.900, 0.320), emission_strength=1.2),
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
                        ("subsurface", "Subsurface Weight"),
                        ("specular", "Specular IOR Level")):
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
    print("%-14s %s" % (name, sorted(spec)))

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
