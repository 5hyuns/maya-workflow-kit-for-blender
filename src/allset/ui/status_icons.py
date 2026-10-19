# SPDX-License-Identifier: GPL-3.0-or-later
"""Kit-drawn Maya-style icons for the Status Line, the menu bar and the viewport panel toolbar (docs/steps/step_113.md).

Decision 6: no Maya icons. Maya's Status Line and panel toolbar show flat light-grey glyphs with teal accents and no
button frame (research/maya/screens/top113/t02_top.png, w/status_*.png); Blender's own icons in embossed boxes read
as Blender. Here every glyph is a few vector shapes rasterised with numpy (4x supersampled, no files) and handed to
Blender as a ``bpy.utils.previews`` image, so layouts use them through ``icon_value``.
"""

import math

import numpy as np

SIZE = 32          # drawn size; Blender scales a button icon to 16 px x UI scale
SS = 4
GREY = (0.80, 0.80, 0.80)      # Maya's glyph grey (status line grabs, ~#cccccc)
DIM = (0.55, 0.55, 0.55)
TEAL = (0.29, 0.73, 0.82)      # snap magnets / selection accents (~#4abad1)
BLUE = (0.40, 0.62, 0.86)
ORANGE = (0.90, 0.58, 0.30)
DARK = (0.20, 0.20, 0.20)


class Canvas:
    """RGBA canvas in unit coordinates (0..1, y down), supersampled."""

    def __init__(self, size=SIZE):
        n = size * SS
        self.size = size
        c = (np.arange(n) + 0.5) / n
        self.x, self.y = np.meshgrid(c, c)
        self.px = np.zeros((n, n, 4), np.float32)

    def fill(self, mask, colour, alpha=1.0):
        a = mask.astype(np.float32) * alpha
        out = self.px
        oa = out[..., 3]
        na = a + oa * (1 - a)
        safe = np.where(na > 0, na, 1)
        for i in range(3):
            out[..., i] = (colour[i] * a + out[..., i] * oa * (1 - a)) / safe
        out[..., 3] = na

    def clear(self, mask):
        self.px[..., 3] *= 1 - mask.astype(np.float32)

    # shapes -----------------------------------------------------------------------------------------
    def rect(self, x0, y0, x1, y1, colour):
        self.fill((self.x >= x0) & (self.x <= x1) & (self.y >= y0) & (self.y <= y1), colour)

    def frame(self, x0, y0, x1, y1, w, colour):
        outer = (self.x >= x0) & (self.x <= x1) & (self.y >= y0) & (self.y <= y1)
        inner = (self.x > x0 + w) & (self.x < x1 - w) & (self.y > y0 + w) & (self.y < y1 - w)
        self.fill(outer & ~inner, colour)

    def seg_mask(self, ax, ay, bx, by, w):
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy or 1e-9
        t = np.clip(((self.x - ax) * dx + (self.y - ay) * dy) / L, 0, 1)
        return (self.x - ax - t * dx) ** 2 + (self.y - ay - t * dy) ** 2 <= (w / 2) ** 2

    def line(self, ax, ay, bx, by, w, colour):
        self.fill(self.seg_mask(ax, ay, bx, by, w), colour)

    def polyline(self, pts, w, colour):
        m = np.zeros_like(self.x, bool)
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            m |= self.seg_mask(ax, ay, bx, by, w)
        self.fill(m, colour)

    def circle(self, cx, cy, r, colour):
        self.fill((self.x - cx) ** 2 + (self.y - cy) ** 2 <= r * r, colour)

    def ring(self, cx, cy, r, w, colour, a0=None, a1=None):
        d = np.sqrt((self.x - cx) ** 2 + (self.y - cy) ** 2)
        m = np.abs(d - r) <= w / 2
        if a0 is not None:
            ang = np.degrees(np.arctan2(-(self.y - cy), self.x - cx)) % 360
            m &= ((ang - a0) % 360) <= ((a1 - a0) % 360)
        self.fill(m, colour)

    def poly_mask(self, pts):
        inside = np.zeros_like(self.x, bool)
        n = len(pts)
        for i in range(n):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
            cond = (y1 > self.y) != (y2 > self.y)
            with np.errstate(divide='ignore', invalid='ignore'):
                xi = (x2 - x1) * (self.y - y1) / ((y2 - y1) if y2 != y1 else 1e-9) + x1
            inside ^= cond & (self.x < xi)
        return inside

    def poly(self, pts, colour):
        self.fill(self.poly_mask(pts), colour)

    def pixels(self):
        """Flat RGBA floats, bottom row first (Blender image order), premultiplied box filter."""
        s = self.size
        p = self.px.reshape(s, SS, s, SS, 4)
        a = p[..., 3].mean(axis=(1, 3))
        rgb = (p[..., :3] * p[..., 3:4]).mean(axis=(1, 3)) / np.maximum(a, 1e-6)[..., None]
        out = np.concatenate([rgb, a[..., None]], axis=2)[::-1]
        return out.ravel()


# --- glyphs -----------------------------------------------------------------------------------------

def arrow_cursor(cv, x, y, s, colour=GREY):
    """Mouse pointer with its tip at (x, y), height s."""
    cv.poly([(x, y), (x, y + s), (x + s * 0.28, y + s * 0.75), (x + s * 0.5, y + s * 1.05),
             (x + s * 0.62, y + s * 0.98), (x + s * 0.42, y + s * 0.68), (x + s * 0.72, y + s * 0.68)], colour)


def magnet(cv, colour=TEAL):
    """Maya snap magnet: a U turned down-left."""
    cv.ring(0.40, 0.40, 0.24, 0.12, colour, 120, 330)
    cv.line(0.20, 0.53, 0.30, 0.64, 0.13, colour)
    cv.line(0.53, 0.20, 0.64, 0.30, 0.13, colour)


def g_bar(cv):
    cv.line(0.5, 0.15, 0.5, 0.85, 0.08, DIM)


def g_open(cv):
    cv.polyline([(0.38, 0.28), (0.64, 0.5), (0.38, 0.72), (0.38, 0.28)], 0.06, DIM)


def g_closed(cv):
    cv.poly([(0.36, 0.24), (0.68, 0.5), (0.36, 0.76)], DIM)


def g_new(cv):
    cv.poly([(0.22, 0.08), (0.60, 0.08), (0.80, 0.28), (0.80, 0.92), (0.22, 0.92)], GREY)
    cv.poly([(0.60, 0.08), (0.60, 0.28), (0.80, 0.28)], DIM)


def g_open_scene(cv):
    cv.poly([(0.08, 0.25), (0.38, 0.25), (0.46, 0.33), (0.86, 0.33), (0.86, 0.85), (0.08, 0.85)], DIM)
    cv.poly([(0.20, 0.47), (0.96, 0.47), (0.84, 0.85), (0.08, 0.85)], GREY)


def g_save(cv):
    cv.rect(0.12, 0.12, 0.88, 0.88, GREY)
    cv.rect(0.28, 0.12, 0.70, 0.38, DARK)
    cv.rect(0.58, 0.16, 0.66, 0.34, GREY)
    cv.rect(0.24, 0.55, 0.76, 0.88, DARK)


def _curl(cv, mirror):
    f = (lambda x: 1 - x) if mirror else (lambda x: x)
    cv.ring(0.52 if not mirror else 0.48, 0.55, 0.28, 0.12, GREY, *((270, 90) if not mirror else (90, 270)))
    cv.poly([(f(0.08), 0.27), (f(0.38), 0.05), (f(0.38), 0.49)], GREY)
    cv.line(f(0.36), 0.27, f(0.52), 0.27, 0.12, GREY)
    cv.line(f(0.52), 0.83, f(0.30), 0.83, 0.12, GREY)


def g_undo(cv):
    _curl(cv, False)


def g_redo(cv):
    _curl(cv, True)


def g_sel_hierarchy(cv):
    cv.rect(0.06, 0.06, 0.34, 0.30, GREY)
    cv.rect(0.40, 0.36, 0.66, 0.58, GREY)
    cv.line(0.20, 0.30, 0.20, 0.47, 0.06, GREY)
    cv.line(0.20, 0.47, 0.40, 0.47, 0.06, GREY)
    arrow_cursor(cv, 0.58, 0.50, 0.46, TEAL)


def g_sel_object(cv):
    cv.poly([(0.10, 0.30), (0.40, 0.10), (0.72, 0.30), (0.72, 0.60), (0.40, 0.80), (0.10, 0.60)], GREY)
    arrow_cursor(cv, 0.52, 0.46, 0.50, TEAL)


def g_sel_component(cv):
    for i in range(2):
        for j in range(2):
            cv.rect(0.06 + i * 0.32, 0.06 + j * 0.32, 0.32 + i * 0.32, 0.32 + j * 0.32, GREY)
    arrow_cursor(cv, 0.56, 0.50, 0.48, TEAL)


def g_mask_handles(cv):
    cv.line(0.5, 0.12, 0.5, 0.88, 0.10, GREY)
    cv.line(0.12, 0.5, 0.88, 0.5, 0.10, GREY)
    cv.circle(0.5, 0.5, 0.14, TEAL)


def g_mask_joints(cv):
    cv.ring(0.30, 0.70, 0.14, 0.08, GREY)
    cv.ring(0.70, 0.30, 0.14, 0.08, GREY)
    cv.poly([(0.38, 0.56), (0.70, 0.44), (0.56, 0.38), (0.44, 0.70)], GREY)


def g_mask_curves(cv):
    pts = [(0.10 + 0.8 * t, 0.5 - 0.32 * math.sin(t * 2 * math.pi)) for t in np.linspace(0, 1, 24)]
    cv.polyline(pts, 0.10, GREY)


def g_mask_surfaces(cv):
    cv.circle(0.5, 0.5, 0.38, GREY)
    cv.ring(0.5, 0.5, 0.20, 0.06, DARK, 200, 340)


def g_mask_deformers(cv):
    for k in (0.15, 0.5, 0.85):
        cv.line(k, 0.15, k, 0.85, 0.06, GREY)
        cv.line(0.15, k, 0.85, k, 0.06, GREY)


def g_mask_dynamics(cv):
    for x, y, r in ((0.25, 0.30, 0.10), (0.62, 0.22, 0.08), (0.45, 0.58, 0.12), (0.78, 0.66, 0.10),
                    (0.22, 0.78, 0.07)):
        cv.circle(x, y, r, GREY)


def g_mask_rendering(cv):
    cv.circle(0.5, 0.40, 0.26, GREY)
    cv.rect(0.38, 0.62, 0.62, 0.84, GREY)


def g_mask_misc(cv):
    cv.line(0.5, 0.10, 0.5, 0.90, 0.07, GREY)
    cv.line(0.10, 0.5, 0.90, 0.5, 0.07, GREY)
    cv.line(0.25, 0.75, 0.75, 0.25, 0.07, GREY)


def g_vertex(cv):
    cv.frame(0.18, 0.18, 0.82, 0.82, 0.05, DIM)
    for x, y in ((0.18, 0.18), (0.82, 0.18), (0.18, 0.82), (0.82, 0.82)):
        cv.circle(x, y, 0.11, TEAL)


def g_edge(cv):
    cv.frame(0.18, 0.18, 0.82, 0.82, 0.05, DIM)
    cv.line(0.18, 0.18, 0.18, 0.82, 0.12, TEAL)


def g_face(cv):
    cv.rect(0.18, 0.18, 0.82, 0.82, TEAL)
    cv.frame(0.18, 0.18, 0.82, 0.82, 0.05, DIM)


def _snap(target):
    def draw(cv):
        magnet(cv)
        target(cv)
    return draw


def _t_grid(cv):
    for k in (0.66, 0.84):
        cv.line(k, 0.56, k, 0.98, 0.05, GREY)
        cv.line(0.56, k, 0.98, k, 0.05, GREY)


def _t_curve(cv):
    cv.ring(0.90, 0.92, 0.32, 0.07, GREY, 90, 180)


def _t_point(cv):
    cv.circle(0.78, 0.78, 0.13, GREY)


def _t_projected(cv):
    cv.ring(0.78, 0.78, 0.16, 0.06, GREY)
    cv.circle(0.78, 0.78, 0.06, GREY)


def _t_plane(cv):
    cv.poly([(0.58, 0.78), (0.78, 0.60), (0.98, 0.78), (0.78, 0.96)], GREY)


def _t_live(cv):
    cv.rect(0.55, 0.80, 0.98, 0.92, GREY)


def g_history(cv):
    cv.rect(0.20, 0.14, 0.80, 0.86, GREY)
    for y in (0.32, 0.48, 0.64):
        cv.line(0.32, y, 0.68, y, 0.06, DARK)


def clapper(cv):
    cv.rect(0.10, 0.36, 0.90, 0.86, GREY)
    for i in range(4):
        x = 0.12 + i * 0.2
        cv.poly([(x, 0.14), (x + 0.12, 0.14), (x + 0.08, 0.30), (x - 0.04, 0.30)], GREY)


def g_render_view(cv):
    clapper(cv)
    cv.ring(0.5, 0.61, 0.15, 0.06, DARK)
    cv.circle(0.5, 0.61, 0.06, DARK)


def g_render(cv):
    clapper(cv)


def g_ipr(cv):
    clapper(cv)
    for i, ch in enumerate("IPR"):
        x = 0.24 + i * 0.2
        if ch == "I":
            cv.line(x + 0.04, 0.46, x + 0.04, 0.76, 0.06, DARK)
        elif ch == "P":
            cv.line(x, 0.46, x, 0.76, 0.06, DARK)
            cv.ring(x + 0.05, 0.55, 0.07, 0.05, DARK, 270, 90)
        else:
            cv.line(x, 0.46, x, 0.76, 0.06, DARK)
            cv.ring(x + 0.05, 0.55, 0.07, 0.05, DARK, 270, 90)
            cv.line(x + 0.04, 0.62, x + 0.11, 0.76, 0.05, DARK)


def gear(cv, cx, cy, r, colour):
    for k in range(8):
        a = k * math.pi / 4
        cv.line(cx + math.cos(a) * r * 0.6, cy + math.sin(a) * r * 0.6,
                cx + math.cos(a) * r, cy + math.sin(a) * r, r * 0.42, colour)
    cv.circle(cx, cy, r * 0.72, colour)
    cv.circle(cx, cy, r * 0.30, DARK)


def g_render_settings(cv):
    clapper(cv)
    gear(cv, 0.72, 0.72, 0.24, TEAL)


def g_hypershade(cv):
    cv.ring(0.5, 0.5, 0.30, 0.20, TEAL)
    cv.circle(0.42, 0.42, 0.08, (0.85, 0.95, 0.97))


def g_render_setup(cv):
    clapper(cv)
    cv.poly([(0.46, 0.74), (0.74, 0.60), (1.0, 0.74), (0.74, 0.88)], TEAL)


def g_light_editor(cv):
    cv.circle(0.36, 0.36, 0.22, GREY)
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        cv.line(0.36 + math.cos(a) * 0.27, 0.36 + math.sin(a) * 0.27,
                0.36 + math.cos(a) * 0.36, 0.36 + math.sin(a) * 0.36, 0.06, GREY)
    gear(cv, 0.72, 0.72, 0.22, TEAL)


def g_pause(cv):
    cv.rect(0.26, 0.18, 0.42, 0.82, GREY)
    cv.rect(0.58, 0.18, 0.74, 0.82, GREY)


def g_modeling_toolkit(cv):
    cv.poly([(0.10, 0.32), (0.45, 0.14), (0.80, 0.32), (0.45, 0.50)], GREY)
    cv.poly([(0.10, 0.32), (0.45, 0.50), (0.45, 0.90), (0.10, 0.72)], DIM)
    cv.poly([(0.45, 0.50), (0.80, 0.32), (0.80, 0.72), (0.45, 0.90)], GREY)
    cv.line(0.62, 0.92, 0.96, 0.58, 0.10, TEAL)


def g_character(cv):
    cv.circle(0.5, 0.18, 0.11, GREY)
    cv.rect(0.38, 0.32, 0.62, 0.62, GREY)
    cv.line(0.20, 0.36, 0.80, 0.36, 0.08, GREY)
    cv.line(0.42, 0.62, 0.36, 0.92, 0.08, GREY)
    cv.line(0.58, 0.62, 0.64, 0.92, 0.08, GREY)


def g_attribute_editor(cv):
    for y in (0.20, 0.42, 0.64, 0.86):
        cv.rect(0.10, y - 0.05, 0.28, y + 0.05, GREY)
        cv.frame(0.36, y - 0.07, 0.92, y + 0.07, 0.04, GREY)


def g_tool_settings(cv):
    for y in (0.22, 0.50, 0.78):
        cv.rect(0.10, y - 0.05, 0.24, y + 0.05, GREY)
        cv.line(0.32, y, 0.70, y, 0.06, GREY)
    cv.rect(0.74, 0.10, 0.90, 0.34, GREY)
    cv.line(0.82, 0.30, 0.82, 0.90, 0.07, GREY)


def g_channel_box(cv):
    for k, colour in enumerate((GREY, DIM, GREY)):
        y = 0.30 + k * 0.20
        cv.poly([(0.10, y), (0.50, y - 0.18), (0.90, y), (0.50, y + 0.18)], colour)


def g_live_surface(cv):
    magnet(cv)
    _t_live(cv)


def g_workspace(cv):
    cv.frame(0.10, 0.18, 0.90, 0.82, 0.06, GREY)
    cv.line(0.36, 0.18, 0.36, 0.82, 0.06, GREY)


GLYPHS = {
    "bar": g_bar, "open": g_open, "closed": g_closed,
    "new": g_new, "open_scene": g_open_scene, "save": g_save, "undo": g_undo, "redo": g_redo,
    "sel_hierarchy": g_sel_hierarchy, "sel_object": g_sel_object, "sel_component": g_sel_component,
    "mask_HANDLES": g_mask_handles, "mask_JOINTS": g_mask_joints, "mask_CURVES": g_mask_curves,
    "mask_SURFACES": g_mask_surfaces, "mask_DEFORMERS": g_mask_deformers, "mask_DYNAMICS": g_mask_dynamics,
    "mask_RENDERING": g_mask_rendering, "mask_MISC": g_mask_misc,
    "vertex": g_vertex, "edge": g_edge, "face": g_face,
    "snap_GRID": _snap(_t_grid), "snap_CURVE": _snap(_t_curve), "snap_POINT": _snap(_t_point),
    "snap_PROJECTED": _snap(_t_projected), "snap_PLANE": _snap(_t_plane), "snap_LIVE": _snap(_t_live),
    "history": g_history,
    "render_view": g_render_view, "render": g_render, "ipr": g_ipr, "render_settings": g_render_settings,
    "hypershade": g_hypershade, "render_setup": g_render_setup, "light_editor": g_light_editor, "pause": g_pause,
    "ed_MODELING_TOOLKIT": g_modeling_toolkit, "ed_CHARACTER": g_character, "ed_ATTRIBUTE": g_attribute_editor,
    "ed_TOOL_SETTINGS": g_tool_settings, "ed_CHANNEL_BOX": g_channel_box,
    "workspace": g_workspace,
}


def render(name, size=SIZE):
    cv = Canvas(size)
    GLYPHS[name](cv)
    return cv


# --- previews ---------------------------------------------------------------------------------------

_pcoll = []
EXTRA = {}     # name -> drawing function, added by other modules (panel toolbar glyphs) before first use


def _collection():
    if not _pcoll:
        import bpy.utils.previews
        _pcoll.append(bpy.utils.previews.new())
    return _pcoll[0]


def icon(name):
    """icon_value of glyph ``name`` (made on first use)."""
    pc = _collection()
    p = pc.get(name)
    if p is None:
        fn = GLYPHS.get(name) or EXTRA[name]
        cv = Canvas(SIZE)
        fn(cv)
        px = cv.pixels()
        p = pc.new(name)
        p.icon_size = (SIZE, SIZE)
        p.icon_pixels_float = px
        p.image_size = (SIZE, SIZE)
        p.image_pixels_float = px
    return p.icon_id


def make_all():
    """Create every glyph preview outside drawing (a timer after register): previews made while a header draws
    are avoided."""
    try:
        for name in list(GLYPHS) + list(EXTRA):
            icon(name)
    except Exception:   # never leave a timer raising
        pass
    return None


def register():
    import bpy
    if not bpy.app.background:
        bpy.app.timers.register(make_all, first_interval=0.0)


def unregister():
    import bpy
    if bpy.app.timers.is_registered(make_all):
        bpy.app.timers.unregister(make_all)
    if _pcoll:
        import bpy.utils.previews
        bpy.utils.previews.remove(_pcoll.pop())
