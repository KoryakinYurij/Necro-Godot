import bmesh
from mathutils import Matrix
for name in ("create_uvsphere", "create_cone", "create_cube", "bisect_plane", "transform"):
    op = getattr(bmesh.ops, name)
    doc = (op.__doc__ or "").strip().splitlines()
    print("==", name, "==")
    for line in doc[:12]:
        print("   ", line.strip())
bm = bmesh.new()
try:
    res = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=4, radius=0.5)
    print("uvsphere radius= OK verts", len(res["verts"]))
except TypeError as exc:
    print("uvsphere radius= FAIL", exc)
try:
    res = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=6,
                                radius1=0.1, radius2=0.05, depth=0.2)
    print("cone radius1/2 OK verts", len(res["verts"]))
except TypeError as exc:
    print("cone FAIL", exc)
try:
    res = bmesh.ops.create_cube(bm, size=0.2)
    print("cube OK verts", len(res["verts"]))
except TypeError as exc:
    print("cube FAIL", exc)
print("verts now:", len(bm.verts), "faces:", len(bm.faces))
bm.free()
