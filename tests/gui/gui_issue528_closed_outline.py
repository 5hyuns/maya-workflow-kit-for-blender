"""#528 in a real UI: closed outlines (marking menu option boxes, marquee / lattice frames, brush circles) draw every
side on every Blender version: the kit's closed-outline batch and the marking menu outline drawn off screen show all
four sides of a square, with the plain and the wide-line shader; Shift+RMB on an object shows the menu (screenshot)."""

import os
import sys
from importlib import import_module

import bpy
import gpu
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, run, screenshot, setup, step, tap, view3d, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
C = {}
SIZE = 64
LO, HI = 10, 50          # the square's corners, in pixels


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def _draw_off(draw):
    """Pixels (rows of RGBA) of ``draw()`` into a cleared SIZE x SIZE picture, one unit = one pixel."""
    off = gpu.types.GPUOffScreen(SIZE, SIZE)
    try:
        with off.bind():
            fb = gpu.state.active_framebuffer_get()
            fb.clear(color=(0.0, 0.0, 0.0, 0.0))
            with gpu.matrix.push_pop(), gpu.matrix.push_pop_projection():
                gpu.matrix.load_matrix(Matrix.Identity(4))
                gpu.matrix.load_projection_matrix(Matrix(((2.0 / SIZE, 0, 0, -1.0), (0, 2.0 / SIZE, 0, -1.0),
                                                          (0, 0, 1.0, 0), (0, 0, 0, 1.0))))
                draw()
            buf = fb.read_color(0, 0, SIZE, SIZE, 4, 0, 'FLOAT')
        buf.dimensions = SIZE * SIZE * 4
        flat = list(buf)
    finally:
        off.free()
    return [[flat[(y * SIZE + x) * 4 + 3] for x in range(SIZE)] for y in range(SIZE)]


def _sides(alpha):
    """Which sides of the square have ink along most of their length (a side within one pixel of its line)."""
    mid = range(LO + 5, HI - 5)

    def lit(cells):
        return sum(1 for c in cells if c > 0.3) >= len(mid) * 0.8

    def col(x):
        return [max(alpha[y][xx] for xx in (x - 1, x, x + 1)) for y in mid]

    def row(y):
        return [max(alpha[yy][x] for yy in (y - 1, y, y + 1)) for x in mid]
    return {"bottom": lit(row(LO)), "right": lit(col(HI)), "top": lit(row(HI)), "left": lit(col(LO))}


SQUARE = [(LO + 0.5, LO + 0.5), (HI + 0.5, LO + 0.5), (HI + 0.5, HI + 0.5), (LO + 0.5, HI + 0.5)]


def _plain(batch_of):
    def draw():
        sh = gpu.shader.from_builtin('UNIFORM_COLOR')
        sh.uniform_float("color", (1.0, 1.0, 1.0, 1.0))
        batch_of(sh).draw(sh)
    return draw


def _wide():
    def draw():
        sh = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        sh.uniform_float("viewportSize", (SIZE, SIZE))
        sh.uniform_float("lineWidth", 1.5)
        sh.uniform_float("color", (1.0, 1.0, 1.0, 1.0))
        mod(".compat").closed_line_batch(sh, SQUARE).draw(sh)
    return draw


@step
def s_setup():
    C["x"], C["y"] = setup()


@step
def s_offscreen():
    compat = mod(".compat")
    sides = _sides(_draw_off(_plain(lambda sh: compat.closed_line_batch(sh, SQUARE))))
    check(f"closed outline batch draws all four sides ({sides})", all(sides.values()))
    sides = _sides(_draw_off(_wide()))
    check(f"closed outline with the wide-line shader draws all four sides ({sides})", all(sides.values()))
    draw = mod(".marking.draw")
    sides = _sides(_draw_off(lambda: draw._outline((LO + 0.5, LO + 0.5, HI + 0.5, HI + 0.5), (1.0, 1.0, 1.0, 1.0))))
    check(f"marking menu outline (option box) draws all four sides ({sides})", all(sides.values()))
    from gpu_extras.batch import batch_for_shader
    loop = _sides(_draw_off(_plain(lambda sh: batch_for_shader(sh, 'LINE_LOOP', {"pos": SQUARE}))))
    print("GUI INFO Blender", bpy.app.version_string, "plain LINE_LOOP sides:", loop, flush=True)


@step
def s_object_menu():
    area, region = view3d()
    for ob in bpy.context.scene.objects:
        ob.select_set(False)
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.mesh.primitive_cube_add()
    ev('MOUSEMOVE', 'NOTHING', x=C["x"], y=C["y"])
    ev('LEFT_SHIFT', 'PRESS', x=C["x"], y=C["y"])
    ev('RIGHTMOUSE', 'PRESS', x=C["x"], y=C["y"], shift=True)


@step
def s_object_menu_open():
    s = mod(".marking.draw").ACTIVE.get("session")
    check("Shift+RMB on the object opens a marking menu", s is not None)
    shot("gui_issue528_object_menu.png")
    tap('ESC')
    ev('RIGHTMOUSE', 'RELEASE', x=C["x"], y=C["y"], shift=True)
    ev('LEFT_SHIFT', 'RELEASE', x=C["x"], y=C["y"])


run()
