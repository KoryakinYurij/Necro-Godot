import bpy
import os

SRC = r"C:\Users\Fixed\Documents\NecroHero\renders"
DST = r"D:\Code AI\Games\Necro-Godot\prototypes\blender-test\.scratch\preview"
os.makedirs(DST, exist_ok=True)

TARGETS = {
    "hero_front": (760, 950),
    "hero_three_quarter": (760, 950),
    "hero_head_detail": (760, 760),
    "hero_staff_lantern": (760, 760),
}

for name, (width, height) in TARGETS.items():
    source = os.path.join(SRC, name + ".png")
    image = bpy.data.images.load(source, check_existing=False)
    image.scale(width, height)
    scene = bpy.data.scenes["NecroHero_Asset"]
    previous = (
        scene.render.image_settings.file_format,
        scene.render.image_settings.quality,
        scene.render.image_settings.color_mode,
    )
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 88
    scene.render.image_settings.color_mode = "RGB"
    destination = os.path.join(DST, name + ".jpg")
    image.filepath_raw = destination
    image.file_format = "JPEG"
    image.save()
    (
        scene.render.image_settings.file_format,
        scene.render.image_settings.quality,
        scene.render.image_settings.color_mode,
    ) = previous
    bpy.data.images.remove(image)
    print("%-20s -> %s (%d bytes)" % (name, destination, os.path.getsize(destination)))

print("done")
