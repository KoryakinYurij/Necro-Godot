import bpy
import math
import bmesh

THRESHOLDS = (20.0, 25.0, 30.0, 35.0, 40.0, 45.0)

print("%-24s %5s %6s | %-28s | edges sharper than (deg)" % ("object", "verts", "polys", "face-angle med/max"))
print("%-24s %5s %6s | %-28s | %s" % ("", "", "", "", " ".join("%5.0f" % t for t in THRESHOLDS)))

summary = {t: 0 for t in THRESHOLDS}
for obj in sorted(bpy.context.scene.objects, key=lambda o: o.name):
    if obj.type != "MESH":
        continue
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    angles = []
    for edge in bm.edges:
        if len(edge.link_faces) == 2:
            angles.append(math.degrees(edge.calc_face_angle(0.0)))
    angles.sort()
    counts = [sum(1 for a in angles if a > t) for t in THRESHOLDS]
    for t, c in zip(THRESHOLDS, counts):
        summary[t] += c
    median = angles[len(angles) // 2] if angles else 0.0
    maximum = angles[-1] if angles else 0.0
    smooth = sum(1 for p in obj.data.polygons if p.use_smooth)
    print("%-24s %5d %6d | %-28s | %s  (smooth %d/%d)"
          % (obj.name, len(bm.verts), len(bm.faces),
             "%.1f / %.1f" % (median, maximum),
             " ".join("%5d" % c for c in counts), smooth, len(obj.data.polygons)))
    bm.free()

print("\ntotals:", " ".join("%.0f:%-6d" % (t, summary[t]) for t in THRESHOLDS))
