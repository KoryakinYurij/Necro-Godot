import bpy
import json
import mathutils

print("filepath:", bpy.data.filepath)
print("is_dirty:", bpy.data.is_dirty)
print("blender:", bpy.app.version_string)
print("scenes:", [s.name for s in bpy.data.scenes])
print("collections:", [(c.name, len(c.objects)) for c in bpy.data.collections])
print("scene root children:", [c.name for c in bpy.context.scene.collection.children])
print("datablocks: meshes=%d materials=%d images=%d worlds=%d actions=%d armatures=%d node_groups=%d"
      % (len(bpy.data.meshes), len(bpy.data.materials), len(bpy.data.images),
         len(bpy.data.worlds), len(bpy.data.actions), len(bpy.data.armatures),
         len(bpy.data.node_groups)))
print("scene frame range:", bpy.context.scene.frame_start, bpy.context.scene.frame_end,
      "fps", bpy.context.scene.render.fps)
print("render engine:", bpy.context.scene.render.engine,
      "res:", bpy.context.scene.render.resolution_x, "x", bpy.context.scene.render.resolution_y,
      "%", bpy.context.scene.render.resolution_percentage)
print("world assigned:", bpy.context.scene.world)
print("unit system:", bpy.context.scene.unit_settings.system,
      "scale_length:", bpy.context.scene.unit_settings.scale_length)

print("\n--- MATERIAL USERS ---")
for m in bpy.data.materials:
    users = [o.name for o in bpy.data.objects
             if m.name in [s.material.name for s in o.material_slots if s.material]]
    print(f"{m.name!r} users={m.users} objects={len(users)} use_nodes={m.use_nodes}")

print("\n--- MATERIAL NODE GRAPHS ---")
for m in bpy.data.materials:
    if not m.use_nodes:
        print(f"{m.name}: NO NODES, viewport color {tuple(round(v, 3) for v in m.diffuse_color)}")
        continue
    nodes = []
    for n in m.node_tree.nodes:
        info = n.bl_idname
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            vals = {}
            for key in ("Base Color", "Metallic", "Roughness", "IOR", "Alpha",
                        "Emission Color", "Emission Strength", "Specular IOR Level",
                        "Sheen Weight", "Coat Weight", "Subsurface Weight"):
                if key in n.inputs:
                    sock = n.inputs[key]
                    if sock.is_linked:
                        vals[key] = "<-%s" % sock.links[0].from_node.bl_idname
                    else:
                        dv = sock.default_value
                        try:
                            vals[key] = [round(float(x), 3) for x in dv]
                        except TypeError:
                            vals[key] = round(float(dv), 3)
            info += " " + json.dumps(vals)
        nodes.append(info)
    print(f"{m.name}: " + " | ".join(nodes))
    print("    outputs -> %s" % [l.to_node.bl_idname for l in m.node_tree.links
                                 if l.from_node.bl_idname == "ShaderNodeOutputMaterial"])

print("\n--- OBJECT DETAIL ---")
for obj in sorted(bpy.context.scene.objects, key=lambda o: o.name):
    if obj.type != "MESH":
        print(f"{obj.name}: {obj.type} parent={obj.parent.name if obj.parent else None} "
              f"parent_type={obj.parent_type}")
        continue
    me = obj.data
    uv = [l.name for l in me.uv_layers]
    smooth = sum(1 for p in me.polygons if p.use_smooth)
    zs = [(obj.matrix_world @ mathutils.Vector(c)).z for c in obj.bound_box]
    print(f"{obj.name}: data={me.name} verts={len(me.vertices)} polys={len(me.polygons)} "
          f"smooth={smooth}/{len(me.polygons)} uv={uv} vgroups={len(obj.vertex_groups)} "
          f"mods={[(md.name, md.type) for md in obj.modifiers]}")
    print(f"    dims={tuple(round(v, 3) for v in obj.dimensions)} "
          f"world_z=({round(min(zs), 3)},{round(max(zs), 3)}) "
          f"scale={tuple(round(v, 3) for v in obj.scale)} "
          f"rot={tuple(round(v, 3) for v in obj.rotation_euler)} "
          f"parent={obj.parent.name if obj.parent else None} data_users={me.users}")

print("\n--- SCENE BOUNDS ---")
xs, ys, zs = [], [], []
tris = 0
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    for c in obj.bound_box:
        w = obj.matrix_world @ mathutils.Vector(c)
        xs.append(w.x)
        ys.append(w.y)
        zs.append(w.z)
    tris += sum(len(p.vertices) - 2 for p in obj.data.polygons)
print("x:", round(min(xs), 3), round(max(xs), 3))
print("y:", round(min(ys), 3), round(max(ys), 3))
print("z:", round(min(zs), 3), round(max(zs), 3))
print("triangles (pre-modifier):", tris)
print("materials in file:", [m.name for m in bpy.data.materials])
print("images in file:", [(i.name, i.source, tuple(i.size), i.users) for i in bpy.data.images])
print("text blocks:", [t.name for t in bpy.data.texts])
print("node_groups in file:", [g.name for g in bpy.data.node_groups])
