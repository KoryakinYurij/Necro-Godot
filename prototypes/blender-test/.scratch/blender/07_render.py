import bpy
import math
import mathutils
import os

scene = bpy.data.scenes["NecroHero_Asset"]
OUT_DIR = r"C:\Users\Fixed\Documents\NecroHero\renders"
os.makedirs(OUT_DIR, exist_ok=True)

camera = bpy.data.objects["NH_Preview_Cam"]
target = bpy.data.objects["NH_Cam_Target"]

VIEWS = [
    dict(name="hero_front", azimuth=0.0, elevation=6.0, distance=7.0,
         center=(0.0, 0.0, 1.75), res=(1200, 1500)),
    dict(name="hero_three_quarter", azimuth=32.0, elevation=9.0, distance=7.0,
         center=(0.0, 0.0, 1.75), res=(1200, 1500)),
    dict(name="hero_head_detail", azimuth=22.0, elevation=4.0, distance=1.85,
         center=(0.0, 0.0, 2.55), res=(1100, 1100)),
    dict(name="hero_staff_detail", azimuth=18.0, elevation=2.0, distance=1.5,
         center=(0.78, -0.23, 3.25), res=(1100, 1100)),
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


written = []
for view in VIEWS:
    target.location = view["center"]
    place_azimuth(camera, view["distance"], view["azimuth"], view["elevation"], view["center"])
    scene.render.resolution_x, scene.render.resolution_y = view["res"]
    scene.render.filepath = os.path.join(OUT_DIR, view["name"] + ".png")
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    ok = os.path.exists(scene.render.filepath)
    written.append((view["name"], scene.render.filepath, ok))
    print("rendered %-20s -> %s (%s)"
          % (view["name"], scene.render.filepath, "ok" if ok else "MISSING"))

print("\n--- luminance statistics (linear, sample every 53rd pixel) ---")
for name, path, ok in written:
    if not ok:
        continue
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    pixels = image.pixels[:]
    step = 53 * 4
    samples = 0
    total = 0.0
    maximum = 0.0
    minimum = 1.0
    lit = 0
    clipped = 0
    for index in range(0, len(pixels) - 3, step):
        r, g, b = pixels[index], pixels[index + 1], pixels[index + 2]
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        total += luminance
        samples += 1
        maximum = max(maximum, luminance)
        minimum = min(minimum, luminance)
        if luminance > 0.02:
            lit += 1
        if luminance > 0.99:
            clipped += 1
    print("%-20s %dx%d mean=%.3f min=%.3f max=%.3f lit=%.1f%% clipped=%.2f%%"
          % (name, width, height, total / max(samples, 1), minimum, maximum,
             100.0 * lit / max(samples, 1), 100.0 * clipped / max(samples, 1)))
    bpy.data.images.remove(image)

print("\nfiles in renders dir:")
for entry in sorted(os.listdir(OUT_DIR)):
    print("  ", entry, os.path.getsize(os.path.join(OUT_DIR, entry)), "bytes")
