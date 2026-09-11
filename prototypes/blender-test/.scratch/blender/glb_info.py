"""Print the structure of a .glb without any Blender dependency.

Usage: python .scratch/blender/glb_info.py <path.glb>
"""

import json
import struct
import sys


def read_glb(path):
    with open(path, "rb") as handle:
        magic, version, length = struct.unpack("<4sII", handle.read(12))
        if magic != b"glTF":
            raise SystemExit("not a glb: %s" % magic)
        chunk_length, chunk_type = struct.unpack("<I4s", handle.read(8))
        payload = json.loads(handle.read(chunk_length))
    return version, length, payload


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    version, length, gltf = read_glb(sys.argv[1])
    accessors = gltf.get("accessors", [])
    triangles = 0
    for mesh in gltf.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            if primitive.get("mode", 4) == 4 and "indices" in primitive:
                triangles += accessors[primitive["indices"]]["count"] // 3
    print("glTF version:", version, "| bytes:", length)
    print("asset:", gltf.get("asset"))
    print("extensionsUsed:", gltf.get("extensionsUsed"))
    print("scenes: %d | nodes: %d | meshes: %d | materials: %d | images: %d"
          % (len(gltf.get("scenes", [])), len(gltf.get("nodes", [])),
             len(gltf.get("meshes", [])), len(gltf.get("materials", [])),
             len(gltf.get("images", []))))
    print("skins: %d | animations: %d | cameras: %d | lights: %d"
          % (len(gltf.get("skins", [])), len(gltf.get("animations", [])),
             len(gltf.get("cameras", [])),
             len(gltf.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", []))))
    print("triangles:", triangles)
    for index, scene in enumerate(gltf.get("scenes", [])):
        roots = [gltf["nodes"][i].get("name") for i in scene.get("nodes", [])]
        print("scene %d roots (%d): %s" % (index, len(roots), roots[:12]))
    print("materials:", sorted(m.get("name") for m in gltf.get("materials", [])))
    print("node names:", sorted(n.get("name") for n in gltf.get("nodes", []))[:60])
    extras = [n.get("extras") for n in gltf.get("nodes", []) if n.get("extras")]
    print("nodes carrying extras:", len(extras))
    for material in gltf.get("materials", []):
        pbr = material.get("pbrMetallicRoughness", {})
        print("  %-14s base=%s metallic=%.2f rough=%.2f emissive=%s strength=%s alpha=%s"
              % (material.get("name"),
                 [round(v, 3) for v in pbr.get("baseColorFactor", [1, 1, 1, 1])],
                 pbr.get("metallicFactor", 1.0), pbr.get("roughnessFactor", 1.0),
                 [round(v, 3) for v in material.get("emissiveFactor", [0, 0, 0])],
                 material.get("extensions", {})
                 .get("KHR_materials_emissive_strength", {}).get("emissiveStrength"),
                 material.get("alphaMode", "OPAQUE")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
