import bpy

scene = bpy.data.scenes["NecroHero_Asset"]

# NH_* -> stylised PBR spec. Only flat channels (colour/roughness/metallic/
# emission) are set as socket values so a glTF export keeps them intact.
PALETTE = {
    "NH_Robe": dict(
        base=(0.045, 0.020, 0.105), rough=0.86, sheen=0.35, sheen_tint=(0.35, 0.28, 0.52),
        detail="noise", detail_scale=34.0, detail_strength=0.22),
    "NH_Robe_Light": dict(
        base=(0.105, 0.050, 0.215), rough=0.80, sheen=0.42, sheen_tint=(0.40, 0.32, 0.60),
        detail="noise", detail_scale=30.0, detail_strength=0.20),
    "NH_Robe_Trim": dict(
        base=(0.190, 0.085, 0.300), rough=0.62, sheen=0.25, sheen_tint=(0.45, 0.35, 0.65),
        detail="noise", detail_scale=46.0, detail_strength=0.18),
    "NH_Leather": dict(
        base=(0.125, 0.075, 0.048), rough=0.58, coat=0.15,
        detail="voronoi", detail_scale=28.0, detail_strength=0.30),
    "NH_Wood": dict(
        base=(0.145, 0.068, 0.030), rough=0.72, anisotropic=0.25,
        detail="wave", detail_scale=9.0, detail_strength=0.28),
    "NH_Bone": dict(
        base=(0.620, 0.550, 0.420), rough=0.55, subsurface=0.10,
        subsurface_radius=(0.055, 0.040, 0.028),
        detail="noise", detail_scale=70.0, detail_strength=0.16),
    "NH_Bone_High": dict(
        base=(0.860, 0.800, 0.640), rough=0.38, coat=0.25, subsurface=0.14,
        subsurface_radius=(0.050, 0.038, 0.026),
        detail="noise", detail_scale=110.0, detail_strength=0.10),
    "NH_Gold": dict(
        base=(0.850, 0.640, 0.280), rough=0.26, metallic=1.0, coat=0.10,
        detail="noise", detail_scale=90.0, detail_strength=0.06),
    "NH_Black": dict(base=(0.010, 0.006, 0.016), rough=0.92),
    "NH_Soul": dict(
        base=(0.060, 0.420, 0.200), rough=0.32, alpha=0.72,
        emission=(0.140, 1.000, 0.420), emission_strength=4.5,
        detail="noise", detail_scale=24.0, detail_strength=0.18),
    "NH_Soul_Core": dict(
        base=(0.720, 1.000, 0.800), rough=0.15,
        emission=(0.620, 1.000, 0.760), emission_strength=14.0),
    "NH_Rune": dict(
        base=(0.030, 0.160, 0.080), rough=0.45,
        emission=(0.060, 0.620, 0.220), emission_strength=3.0),
}


def build_material(mat, spec):
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()

    output = tree.nodes.new("ShaderNodeOutputMaterial")
    output.name = output.label = "NH_Output"
    output.location = (620, 0)

    bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.name = bsdf.label = "NH_BSDF"
    bsdf.location = (240, 0)
    tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    inputs = bsdf.inputs
    base = spec.get("base", (0.8, 0.8, 0.8))
    inputs["Base Color"].default_value = (base[0], base[1], base[2], 1.0)
    inputs["Roughness"].default_value = spec.get("rough", 0.5)
    inputs["Metallic"].default_value = spec.get("metallic", 0.0)
    if "IOR" in inputs:
        inputs["IOR"].default_value = spec.get("ior", 1.45)
    if "Specular IOR Level" in inputs:
        inputs["Specular IOR Level"].default_value = spec.get("specular", 0.5)
    if "Sheen Weight" in inputs:
        inputs["Sheen Weight"].default_value = spec.get("sheen", 0.0)
        tint = spec.get("sheen_tint", (1.0, 1.0, 1.0))
        if "Sheen Tint" in inputs:
            inputs["Sheen Tint"].default_value = (tint[0], tint[1], tint[2], 1.0)
    if "Coat Weight" in inputs:
        inputs["Coat Weight"].default_value = spec.get("coat", 0.0)
        if "Coat Roughness" in inputs:
            inputs["Coat Roughness"].default_value = max(0.05, spec.get("rough", 0.5) * 0.6)
    if "Subsurface Weight" in inputs:
        inputs["Subsurface Weight"].default_value = spec.get("subsurface", 0.0)
        if "Subsurface Radius" in inputs and "subsurface_radius" in spec:
            inputs["Subsurface Radius"].default_value = spec["subsurface_radius"]
        if "Subsurface Scale" in inputs:
            inputs["Subsurface Scale"].default_value = 0.05
    if "Anisotropic" in inputs:
        inputs["Anisotropic"].default_value = spec.get("anisotropic", 0.0)
    if "Alpha" in inputs:
        inputs["Alpha"].default_value = spec.get("alpha", 1.0)

    emission = spec.get("emission")
    if emission and "Emission Color" in inputs:
        inputs["Emission Color"].default_value = (emission[0], emission[1], emission[2], 1.0)
        inputs["Emission Strength"].default_value = spec.get("emission_strength", 0.0)

    # Procedural surface break-up in object space, so it travels with the part.
    detail = spec.get("detail")
    if detail:
        texcoord = tree.nodes.new("ShaderNodeTexCoord")
        texcoord.name = texcoord.label = "NH_Object_Coords"
        texcoord.location = (-660, -220)

        if detail == "noise":
            texture = tree.nodes.new("ShaderNodeTexNoise")
            texture.name = texture.label = "NH_Noise"
            texture.location = (-440, -220)
            texture.inputs["Scale"].default_value = spec.get("detail_scale", 30.0)
            texture.inputs["Detail"].default_value = 4.0
            texture.inputs["Roughness"].default_value = 0.6
        elif detail == "voronoi":
            texture = tree.nodes.new("ShaderNodeTexVoronoi")
            texture.name = texture.label = "NH_Voronoi"
            texture.location = (-440, -220)
            texture.inputs["Scale"].default_value = spec.get("detail_scale", 30.0)
            texture.feature = "DISTANCE_TO_EDGE"
        else:
            texture = tree.nodes.new("ShaderNodeTexWave")
            texture.name = texture.label = "NH_Wave"
            texture.location = (-440, -220)
            texture.inputs["Scale"].default_value = spec.get("detail_scale", 10.0)
            texture.inputs["Distortion"].default_value = 3.0
            texture.inputs["Detail"].default_value = 2.0
        tree.links.new(texcoord.outputs["Object"], texture.inputs["Vector"])

        # First output is Fac for Noise/Wave, Distance for Voronoi.
        height_socket = texture.outputs[0]

        bump = tree.nodes.new("ShaderNodeBump")
        bump.name = bump.label = "NH_Bump"
        bump.location = (-160, -220)
        bump.inputs["Strength"].default_value = spec.get("detail_strength", 0.2)
        bump.inputs["Distance"].default_value = 0.02
        tree.links.new(height_socket, bump.inputs["Height"])
        tree.links.new(bump.outputs["Normal"], inputs["Normal"])

    # Viewport / solid-mode display so the asset reads correctly out of render.
    mat.diffuse_color = (base[0], base[1], base[2], spec.get("alpha", 1.0))
    mat.roughness = spec.get("rough", 0.5)
    mat.metallic = spec.get("metallic", 0.0)

    if spec.get("alpha", 1.0) < 1.0:
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        if hasattr(mat, "blend_method"):
            try:
                mat.blend_method = "BLEND"
            except TypeError:
                pass
        mat.show_transparent_back = False
    else:
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "DITHERED"
        if hasattr(mat, "blend_method"):
            try:
                mat.blend_method = "OPAQUE"
            except TypeError:
                pass
    return len(tree.nodes), len(tree.links)


for name, spec in PALETTE.items():
    mat = bpy.data.materials.get(name)
    if mat is None:
        print("MISSING MATERIAL:", name)
        continue
    nodes, links = build_material(mat, spec)
    print("%-14s nodes=%d links=%d metallic=%.2f rough=%.2f emission=%.1f alpha=%.2f"
          % (name, nodes, links, mat.metallic, mat.roughness,
             spec.get("emission_strength", 0.0), spec.get("alpha", 1.0)))

leftover = [m.name for m in bpy.data.materials if not m.name.startswith("NH_")]
print("non-NH materials left:", leftover)
print("total materials:", len(bpy.data.materials))

bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
