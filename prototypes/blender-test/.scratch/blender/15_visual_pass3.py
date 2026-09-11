import bpy
import math
import mathutils
import os

scene = bpy.data.scenes["NecroHero_Asset"]
OUT_DIR = r"C:\Users\Fixed\Documents\NecroHero\renders"
camera = bpy.data.objects["NH_Preview_Cam"]
target = bpy.data.objects["NH_Cam_Target"]

# --- 1. View transform: try the faithful options, AgX is the last resort --
for candidate in ("Khronos PBR Neutral", "Standard", "AgX"):
    try:
        scene.view_settings.view_transform = candidate
        print("view transform set to:", candidate)
        break
    except TypeError as exc:
        print("view transform unavailable:", candidate, exc)
if scene.view_settings.view_transform != "AgX":
    try:
        scene.view_settings.look = "None"
    except TypeError:
        pass
scene.view_settings.exposure = 0.0
print("transform:", scene.view_settings.view_transform, "| look:", scene.view_settings.look)

# --- 2. Lighting: more contrast, rim keeps the silhouette readable -------
LIGHT_TUNING = {
    "NH_Key_Light": (360.0, (1.00, 0.92, 0.80), 2.4),
    "NH_Fill_Light": (48.0, (0.58, 0.70, 1.00), 4.0),
    "NH_Rim_Light": (900.0, (0.42, 0.96, 0.70), 2.0),
    "NH_Soul_Accent": (30.0, (0.30, 1.00, 0.50), 0.28),
}
for name, (energy, colour, size) in LIGHT_TUNING.items():
    light = bpy.data.objects[name]
    light.data.energy = energy
    light.data.color = colour
    if light.data.type == "AREA":
        light.data.size = size
    else:
        light.data.shadow_soft_size = size
    print("light %-16s %.0f W %s size %.2f" % (name, energy, colour, size))

world = bpy.data.worlds["NH_Studio_World"]
background = next(n for n in world.node_tree.nodes if n.bl_idname == "ShaderNodeBackground")
background.inputs["Strength"].default_value = 0.22

# --- 3. Luminous materials: saturated, dim enough not to clip to white ---
TWEAKS = {
    "NH_Soul": dict(base=(0.025, 0.180, 0.080), emission=(0.100, 0.800, 0.300),
                    emission_strength=0.9, alpha=0.48, rough=0.38),
    "NH_Soul_Core": dict(base=(0.120, 0.420, 0.200), emission=(0.120, 1.000, 0.300),
                         emission_strength=2.0),
    "NH_Rune": dict(base=(0.020, 0.100, 0.050), emission=(0.060, 0.900, 0.250),
                    emission_strength=1.0),
    "NH_Robe": dict(base=(0.030, 0.013, 0.075)),
    "NH_Gold": dict(base=(0.980, 0.760, 0.320), metallic=0.85, rough=0.32),
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
    if "emission" in spec:
        colour = spec["emission"]
        inputs["Emission Color"].default_value = (colour[0], colour[1], colour[2], 1.0)
    for key, socket in (("rough", "Roughness"), ("metallic", "Metallic"),
                        ("emission_strength", "Emission Strength"), ("alpha", "Alpha")):
        if key in spec and socket in inputs:
            inputs[socket].default_value = spec[key]
    material.roughness = spec.get("rough", material.roughness)
    material.metallic = spec.get("metallic", material.metallic)
    print("%-14s %s" % (name, sorted(spec)))

# --- 4. Compositor: soft bloom so the souls glow instead of clipping ------
# Blender 5.2 compositor: a node group on the scene, output is NodeGroupOutput,
# and the Glare node is configured through input sockets.
scene.use_nodes = True
tree = getattr(scene, "node_tree", None)
if tree is None:
    tree = getattr(scene, "compositing_node_group", None)
    if tree is None:
        tree = bpy.data.node_groups.new("NH_Compositor", "CompositorNodeTree")
        scene.compositing_node_group = tree
tree.nodes.clear()

layers = tree.nodes.new("CompositorNodeRLayers")
layers.location = (-400, 0)
try:
    output = tree.nodes.new("NodeGroupOutput")
except RuntimeError:
    output = tree.nodes.new("CompositorNodeComposite")
output.location = (400, 0)
glare = tree.nodes.new("CompositorNodeGlare")
glare.location = (0, 0)


def set_input(node, name, value):
    if name in node.inputs:
        try:
            node.inputs[name].default_value = value
            return True
        except (TypeError, ValueError):
            return False
    return False


for menu_value in ("BLOOM", "FOG_GLOW", "GLARE"):
    if set_input(glare, "Type", menu_value):
        print("glare type:", menu_value)
        break
set_input(glare, "Quality", "HIGH")
set_input(glare, "Threshold", 0.75)
set_input(glare, "Size", 7.0)
set_input(glare, "Iterations", 3)
set_input(glare, "Strength", 1.0)
print("glare threshold:", glare.inputs["Threshold"].default_value,
      "size:", glare.inputs["Size"].default_value)

tree.links.new(layers.outputs["Image"], glare.inputs["Image"])
tree.links.new(glare.outputs["Image"], output.inputs["Image"])
print("compositor tree:", tree.name, "| output node:", output.bl_idname,
      "| links:", len(tree.links))

# --- 5. Render ------------------------------------------------------------
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
