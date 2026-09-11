import bpy

scene = bpy.data.scenes["NecroHero_Asset"]
scene.use_nodes = True
tree = getattr(scene, "node_tree", None)
if tree is None:
    tree = getattr(scene, "compositing_node_group", None)
    if tree is None:
        tree = bpy.data.node_groups.new("NH_Compositor", "CompositorNodeTree")
        scene.compositing_node_group = tree
tree.nodes.clear()

# A compositor node group needs an explicit interface before its output node
# has sockets to link into. NodeTreeInterface exposes items_tree, not outputs.
existing_outputs = [item for item in tree.interface.items_tree
                    if getattr(item, "in_out", "") == "OUTPUT"]
if not existing_outputs:
    tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
print("interface outputs:", [(item.name, getattr(item, "socket_type", "?"))
                             for item in tree.interface.items_tree
                             if getattr(item, "in_out", "") == "OUTPUT"])

layers = tree.nodes.new("CompositorNodeRLayers")
layers.location = (-400, 0)
output = tree.nodes.new("NodeGroupOutput")
output.location = (400, 0)
print("output node inputs:", [s.name for s in output.inputs])
if not len(output.inputs):
    raise RuntimeError("output node still has no sockets")

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


for menu_value in ("BLOOM", "FOG_GLOW"):
    if set_input(glare, "Type", menu_value):
        print("glare type:", menu_value)
        break
set_input(glare, "Quality", "HIGH")
set_input(glare, "Threshold", 0.75)
set_input(glare, "Size", 7.0)
set_input(glare, "Iterations", 3)
set_input(glare, "Strength", 1.0)

tree.links.new(layers.outputs["Image"], glare.inputs["Image"])
tree.links.new(glare.outputs["Image"], output.inputs["Image"])
print("compositor:", tree.name, "nodes", len(tree.nodes), "links", len(tree.links),
      "| threshold", glare.inputs["Threshold"].default_value,
      "size", glare.inputs["Size"].default_value)

bpy.ops.wm.save_mainfile()
print("saved:", bpy.data.filepath)
