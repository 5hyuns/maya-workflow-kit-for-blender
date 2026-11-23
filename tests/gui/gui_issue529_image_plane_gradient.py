"""#529 in a real UI: with the Maya gradient background, an image plane stays drawn in wireframe and shaded display,
orthographic and perspective, also where a mesh overlaps it (before, the gradient covered the image except where a mesh
was in front of it)."""

import os
import sys
import tempfile
from importlib import import_module
from math import radians

import bpy
from mathutils import Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
OUT = tempfile.mkdtemp(prefix="i529_")
C = {}


def mod(name):
    return import_module(MODULE + name)


def _middle(path, test):
    _area, region = view3d()
    img = bpy.data.images.load(path)
    w, _h = img.size
    px = img.pixels[:]
    n = hit = 0
    cx, cy = region.x + region.width // 2, region.y + region.height // 2
    for y in range(cy - region.height // 4, cy + region.height // 4, 3):
        for x in range(cx - region.width // 4, cx + region.width // 4, 3):
            i = (y * w + x) * 4
            n += 1
            hit += bool(test(px[i:i + 3]))
    bpy.data.images.remove(img)
    return hit / max(n, 1)


def red_fraction(path):
    """Part of the 3D View's middle (where the image plane is) drawn in the image's red."""
    _area, region = view3d()
    img = bpy.data.images.load(path)
    w, _h = img.size
    px = img.pixels[:]
    n = red = 0
    cx, cy = region.x + region.width // 2, region.y + region.height // 2
    for y in range(cy - region.height // 4, cy + region.height // 4, 3):
        for x in range(cx - region.width // 4, cx + region.width // 4, 3):
            i = (y * w + x) * 4
            n += 1
            if px[i] > 0.7 and px[i + 1] < 0.35 and px[i + 2] < 0.35:
                red += 1
    bpy.data.images.remove(img)
    return red / max(n, 1)


def measure(name):
    for _ in range(3):
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    p = os.path.join(OUT, name + ".png")
    screenshot(p)
    if SHOTS:
        screenshot(os.path.join(SHOTS, f"gui_issue529_{name}.png"))
    f = red_fraction(p)
    print("GUI INFO", name, "red", round(f, 3), flush=True)
    return f


def display(mode):
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.allset.display_mode(mode=mode)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_scene():
    img = bpy.data.images.new("ref529", 64, 32)
    img.pixels[:] = [1.0, 0.0, 0.0, 1.0] * (64 * 32)
    p = os.path.join(OUT, "ref529.png")
    img.filepath_raw = p
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    for ob in list(bpy.data.objects):
        if ob.type == 'MESH':
            bpy.data.objects.remove(ob)
    ob = bpy.data.objects.new("imagePlane1", None)
    ob.empty_display_type = 'IMAGE'
    ob.data = bpy.data.images.load(p)
    ob.empty_display_size = 8.0
    ob.rotation_euler = (radians(90), 0.0, radians(90))     # faces +X
    bpy.context.scene.collection.objects.link(ob)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.0, 0.0, 0.0))
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = Euler((radians(90), 0.0, radians(90))).to_quaternion()   # looking -X at the plane
    rv3d.view_location = (0.0, 0.0, 0.0)
    rv3d.view_distance = 8.0
    mod(".operators.key_batch3").apply_background("GRADIENT")
    check("the view shows the Maya gradient", mod(".operators.key_batch3").is_gradient(area.spaces.active.shading))


@step
def s_measure():
    rv3d = view3d()[0].spaces.active.region_3d
    for persp in ('ORTHO', 'PERSP'):
        rv3d.view_perspective = persp
        display('SHADED')
        solid = measure(f"{persp.lower()}_shaded")
        display('WIREFRAME')
        wire = measure(f"{persp.lower()}_wire")
        check(f"{persp}: the image plane is drawn shaded ({solid:.2f})", solid > 0.8)
        check(f"{persp}: the image plane is drawn in wireframe as shaded ({wire:.2f} / {solid:.2f})", wire > 0.8)
    # a plane Blender doesn't draw in this view (perspective off) leaves the gradient whole, no flat patch
    plane = bpy.data.objects["imagePlane1"]
    plane.show_empty_image_perspective = False
    rv3d.view_perspective = 'PERSP'
    base = mod(".operators.key_batch3").GRADIENT_BASE

    def flat_part(name):
        p = os.path.join(OUT, name + ".png")
        for _ in range(3):
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        screenshot(p)
        return _middle(p, lambda c: all(abs(a - b) < 0.012 for a, b in zip(c, base)))
    flat = flat_part("not_drawn")
    plane.hide_viewport = True
    ref = flat_part("no_plane")
    plane.hide_viewport = False
    check(f"a plane not drawn in this view leaves the gradient as without it ({flat:.2f} / {ref:.2f})",
          abs(flat - ref) < 0.03)
    plane.show_empty_image_perspective = True
    display('SHADED')
    rv3d.view_perspective = 'ORTHO'


run()
