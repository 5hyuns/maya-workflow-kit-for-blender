# SPDX-License-Identifier: GPL-3.0-or-later
"""Kit-drawn pictures beside the UV Toolkit's buttons (#494): like Maya's toolkit, every command button shows a small
picture of what it does, its text left-aligned after it, and Align is a row of six pictures.

The pictures are the kit's own drawings in the shelf vocabulary (``shelf_icons``: UV green shells, light grey tool
parts, a dark outline); buttons that are also UV menu items reuse that item's picture (``menu_icons``). They are made
into ``bpy.utils.previews`` images at the size Blender draws a button icon, a few per timer tick; until they are all
made the toolkit draws its buttons without pictures. Pure numpy drawing, previews only in ``icon``.
"""

import time

from .menu_drawings import RED
from .menu_drawings_mesh import vsq
from .shelf_icons import GREEN, LIGHT, Canvas, arrow, curved_arrow, face_grid, plus

UVG = GREEN
DIM = (0.42, 0.62, 0.52)
DRAWINGS = {}       # key -> fn(cv)
# toolkit key -> UV menu item whose picture the button shows (menu_icons)
MENU_PICTURES = {
    "Automatic": "UV/Automatic", "Best Plane": "UV/Best Plane", "Camera-based": "UV/Camera-based",
    "Contour Stretch": "UV/Contour Stretch", "Cylindrical": "UV/Cylindrical", "Normal-based": "UV/Normal-Based",
    "Planar": "UV/Planar", "Spherical": "UV/Spherical", "Auto Seams": "UV/Auto Seams", "Cut": "UV/Cut UV Edges",
    "Split": "UV/Split UVs", "Sew": "UV/Sew UV Edges", "Merge": "UV/Merge UVs",
    "3D Cut and Sew Tool": "UV/3D Cut and Sew UV Tool",
}


def drawing(key):
    def deco(fn):
        DRAWINGS[key] = fn
        return fn
    return deco


def shell(cv, x0, y0, x1, y1, col=UVG, grid=0):
    """A UV shell: a green square with a dark outline (``grid`` inner lines)."""
    cv.rect(x0, y0, x1, y1, col, ol=True)
    if grid:
        face_grid(cv, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], grid + 1, (0.2, 0.32, 0.26), border=False)


# --- Align (bars of shells against a line) ------------------------------------------------------------------------

def _align_u(cv, where):
    xs = {"MIN": 5, "AVG": 16, "MAX": 27}[where]
    rows = ((5, 11, 14), (13, 19, 22), (21, 27, 10))      # y0, y1, width
    for y0, y1, w in rows:
        x0 = xs if where == "MIN" else xs - w if where == "MAX" else xs - w / 2
        shell(cv, x0, y0, x0 + w, y1)
    cv.line((xs, 2), (xs, 30), 1.6, LIGHT, ol=True)


def _align_v(cv, where):
    ys = {"MIN": 27, "AVG": 16, "MAX": 5}[where]
    cols = ((5, 11, 14), (13, 19, 22), (21, 27, 10))
    for x0, x1, h in cols:
        y0 = ys - h if where == "MIN" else ys if where == "MAX" else ys - h / 2
        shell(cv, x0, y0, x1, y0 + h)
    cv.line((2, ys), (30, ys), 1.6, LIGHT, ol=True)


for _w in ("MIN", "AVG", "MAX"):
    DRAWINGS[f"Align U {_w}"] = (lambda w: lambda cv: _align_u(cv, w))(_w)
    DRAWINGS[f"Align V {_w}"] = (lambda w: lambda cv: _align_v(cv, w))(_w)


# --- Cut and Sew ---------------------------------------------------------------------------------------------------

@drawing("Create Shell")
def d_create_shell(cv):
    shell(cv, 4, 8, 22, 28)
    plus(cv, 24, 8, s=5, w=2.6)


@drawing("Create Shell (Grid)")
def d_create_shell_grid(cv):
    shell(cv, 4, 8, 22, 28, grid=2)
    plus(cv, 24, 8, s=5, w=2.6)


@drawing("Move and Sew")
def d_move_sew(cv):
    shell(cv, 3, 6, 13, 26)
    shell(cv, 21, 10, 29, 22, DIM)
    arrow(cv, (27, 16), (15, 16), w=2.4, head=5)


@drawing("Stitch Together")
def d_stitch(cv):
    shell(cv, 3, 5, 14, 27)
    shell(cv, 18, 5, 29, 27)
    for y in (9, 16, 23):
        cv.line((11, y - 2), (21, y + 2), 1.6, RED)


# --- Unfold --------------------------------------------------------------------------------------------------------

@drawing("Unfold")
def d_unfold(cv):
    cv.poly([(9, 9), (23, 7), (21, 25), (11, 23)], UVG, ol=True)
    for a, b in (((9, 9), (3, 3)), ((23, 7), (29, 3)), ((21, 25), (29, 29)), ((11, 23), (3, 29))):
        arrow(cv, a, b, w=1.8, head=3.5)


@drawing("Optimize")
def d_optimize(cv):
    shell(cv, 4, 6, 24, 26, grid=2)
    for x, y in ((9, 12), (17, 20)):
        vsq(cv, x, y, 2.0, LIGHT)
    curved_arrow(cv, 24, 9, 5, 200, 20, w=1.8, head=3.5)


@drawing("Unfold Along")
def d_unfold_along(cv):
    shell(cv, 9, 6, 23, 26, grid=1)
    arrow(cv, (9, 16), (2, 16), w=2.2, head=4)
    arrow(cv, (23, 16), (30, 16), w=2.2, head=4)


@drawing("Straighten UVs")
def d_straighten_uvs(cv):
    cv.polyline([(3, 10), (9, 6), (15, 11), (21, 6), (29, 10)], 1.6, DIM)
    cv.line((3, 22), (29, 22), 2.0, UVG, ol=True)
    for x in (3, 11, 19, 27):
        vsq(cv, x + 1, 22, 2.0, LIGHT)
    arrow(cv, (16, 12), (16, 19), w=1.8, head=3.5, ol=False)


@drawing("Straighten Shell")
def d_straighten_shell(cv):
    cv.poly([(5, 8), (27, 5), (25, 27), (7, 25)], DIM, ol=True)
    cv.frame(7, 8, 25, 25, 1.8, LIGHT, ol=True)


@drawing("Straighten Border")
def d_straighten_border(cv):
    shell(cv, 5, 6, 27, 26, grid=2)
    cv.frame(5, 6, 27, 26, 2.0, RED)


# --- Align and Snap ------------------------------------------------------------------------------------------------

@drawing("Linear Align")
def d_linear_align(cv):
    cv.line((4, 27), (28, 5), 1.6, LIGHT, ol=True)
    for x, y in ((7, 24), (13, 19), (19, 13), (25, 8)):
        vsq(cv, x, y, 2.4, UVG)


@drawing("Match Grid")
def d_match_grid(cv):
    for v in (6, 16, 26):
        cv.line((3, v), (29, v), 1.0, LIGHT)
        cv.line((v, 3), (v, 29), 1.0, LIGHT)
    arrow(cv, (12, 21), (16, 17), w=1.8, head=3.5, ol=False)
    vsq(cv, 16, 16, 2.8, UVG)


@drawing("Match UVs")
def d_match_uvs(cv):
    for p in ((7, 9), (25, 9), (16, 26)):
        arrow(cv, p, (16, 16), w=1.6, head=3.2, ol=False)
        vsq(cv, p[0], p[1], 2.2, DIM)
    vsq(cv, 16, 16, 3.0, UVG)


@drawing("Snap Together")
def d_snap_together(cv):
    shell(cv, 3, 8, 14, 24)
    shell(cv, 19, 14, 29, 28, DIM)
    arrow(cv, (19, 14), (15, 10), w=2.0, head=4)


@drawing("Snap and Stack")
def d_snap_stack(cv):
    shell(cv, 6, 10, 20, 26, DIM)
    shell(cv, 11, 5, 25, 21)
    arrow(cv, (29, 29), (22, 22), w=2.0, head=4)


# --- Arrange and Layout --------------------------------------------------------------------------------------------

@drawing("Layout")
def d_layout(cv):
    cv.frame(3, 3, 29, 29, 1.2, LIGHT)
    shell(cv, 5, 5, 16, 16)
    shell(cv, 18, 5, 27, 12)
    shell(cv, 18, 14, 27, 27)
    shell(cv, 5, 18, 16, 27)


@drawing("Distribute")
def d_distribute(cv):
    for x in (3, 13, 23):
        shell(cv, x, 10, x + 6, 22)
    for x in (9, 19):
        cv.line((x + 1, 16), (x + 3, 16), 1.6, LIGHT)


@drawing("Gather Shells")
def d_gather(cv):
    shell(cv, 11, 11, 21, 21)
    for p, q in (((3, 3), (9, 9)), ((29, 3), (23, 9)), ((3, 29), (9, 23)), ((29, 29), (23, 23))):
        arrow(cv, p, q, w=1.8, head=3.5)


@drawing("Layout Along")
def d_layout_along(cv):
    for x, h in ((3, 12), (12, 8), (21, 14)):
        shell(cv, x, 26 - h, x + 8, 26)
    arrow(cv, (3, 7), (29, 7), w=1.8, head=4)


@drawing("Normalize")
def d_normalize(cv):
    cv.frame(3, 3, 29, 29, 1.4, LIGHT, ol=True)
    shell(cv, 6, 6, 26, 26, grid=1)


@drawing("Orient Shells")
def d_orient(cv):
    cv.poly([(8, 12), (20, 6), (25, 18), (13, 24)], UVG, ol=True)
    curved_arrow(cv, 16, 16, 13, 300, 210, w=1.8, head=3.5)


@drawing("Orient to Edges")
def d_orient_edges(cv):
    cv.poly([(8, 12), (20, 6), (25, 18), (13, 24)], UVG, ol=True)
    cv.line((8, 12), (20, 6), 2.2, RED)
    curved_arrow(cv, 16, 16, 13, 300, 210, w=1.8, head=3.5)


@drawing("Randomize")
def d_randomize(cv):
    for x, y, s in ((4, 5, 7), (19, 3, 6), (12, 14, 8), (22, 20, 7), (4, 22, 6)):
        shell(cv, x, y, x + s, y + s)


@drawing("Stack")
def d_stack(cv):
    shell(cv, 5, 11, 21, 27, DIM)
    shell(cv, 11, 5, 27, 21)


@drawing("Stack and Orient")
def d_stack_orient(cv):
    shell(cv, 5, 11, 19, 25, DIM)
    cv.poly([(11, 9), (22, 5), (26, 17), (15, 21)], UVG, ol=True)
    curved_arrow(cv, 18, 16, 12, 320, 240, w=1.6, head=3.2)


@drawing("Stack Similar")
def d_stack_similar(cv):
    shell(cv, 4, 12, 18, 26, DIM)
    shell(cv, 10, 6, 24, 20)
    cv.line((24, 25), (30, 25), 1.6, LIGHT)
    cv.line((24, 29), (30, 29), 1.6, LIGHT)


@drawing("Unstack")
def d_unstack(cv):
    shell(cv, 3, 14, 15, 26, DIM)
    shell(cv, 17, 4, 29, 16)
    arrow(cv, (14, 15), (19, 18), w=1.6, head=3.2, ol=False)


@drawing("Unitize")
def d_unitize(cv):
    for x, y in ((3, 3), (17, 3), (3, 17), (17, 17)):
        shell(cv, x, y, x + 12, y + 12)


def picture(key, n):
    """(n, n, 4) RGBA (top row first) of toolkit picture ``key``."""
    if key in MENU_PICTURES:
        from . import menu_icon_data, menu_icons
        return menu_icons.picture(menu_icon_data.ICONS[MENU_PICTURES[key]], n)
    cv = Canvas(n)
    DRAWINGS[key](cv)
    return cv.result()


KEYS = tuple(sorted({*DRAWINGS, *MENU_PICTURES}))

# --- previews ------------------------------------------------------------------------------------------------------

_pcoll = []
_ready = [0]
_todo = []
BUDGET = 0.02


def _make(key, n):
    import bpy.utils.previews
    if not _pcoll:
        _pcoll.append(bpy.utils.previews.new())
    name = f"{key}@{n}"
    pv = _pcoll[0].get(name)
    if pv is None:
        flat = picture(key, n)[::-1].ravel()
        pv = _pcoll[0].new(name)
        pv.icon_size = (n, n)
        pv.icon_pixels_float = flat
        pv.image_size = (n, n)
        pv.image_pixels_float = flat
    return pv


def icon(key, context=None):
    """icon_value of toolkit picture ``key`` (0 until the pictures of this size are made)."""
    import bpy
    from .menu_icons import icon_px
    if key not in DRAWINGS and key not in MENU_PICTURES:
        return 0
    n = icon_px(context)
    if bpy.app.background:
        return _make(key, n).icon_id
    if _ready[0] != n:
        if not bpy.app.timers.is_registered(_tick):
            bpy.app.timers.register(_tick, first_interval=0.0)
        return 0
    return _make(key, n).icon_id


def _tick():
    try:
        from .menu_icons import icon_px
        n = icon_px()
        if not _todo:
            _todo[:] = [(k, n) for k in KEYS]
        t0 = time.perf_counter()
        while _todo and time.perf_counter() - t0 < BUDGET:
            _make(*_todo.pop())
        if _todo:
            return 0.01
        _ready[0] = n
        import bpy
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    area.tag_redraw()
    except Exception:       # a timer that raises is dropped: the toolkit stays without pictures
        _todo.clear()
    return None


def unregister():
    import bpy
    if bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)
    _todo.clear()
    _ready[0] = 0
    if _pcoll:
        import bpy.utils.previews
        bpy.utils.previews.remove(_pcoll.pop())
