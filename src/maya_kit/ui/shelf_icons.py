# SPDX-License-Identifier: GPL-3.0-or-later
"""Kit-made colour shelf icons, drawn by code.

Decision 6: no Maya icons. Maya's shelf shows 32 px colour pictograms (,
ui_layout.md:219-222); here every button gets a small vector drawing in its shelf's colour: the
primitive's shape for creation buttons, a symbol for tools (arrow, knife, chain, bulb, key, ...),
two letters when nothing fits. Shapes are rasterised with numpy (4x supersampled, no files, no bpy);
``texture()`` turns one into a GPU texture for ``ui/shelf.py``'s icon row.
"""

import math

import numpy as np

SIZE = 32
SS = 4                 # supersampling
N = SIZE * SS

# Shelf colours (kit's own palette, one hue per shelf like Maya's colour-coded shelves).
SHELF_COLOURS = {
    "CurvesSurfaces": (0.36, 0.63, 0.90), "Polygons": (0.91, 0.60, 0.29), "Sculpting": (0.36, 0.78, 0.63),
    "Rigging": (0.48, 0.83, 0.30), "Animation": (0.88, 0.38, 0.38), "Rendering": (0.94, 0.78, 0.31),
    "FX": (0.31, 0.79, 0.91), "FXCaching": (0.69, 0.53, 0.88),
}
USER_COLOUR = (0.63, 0.63, 0.63)

# 5x7 capitals and digits for the letter fallback.
FONT = {
    "A": ".###.#...##...########...##...##...#", "B": "####.#...#####.#...##...##...#####.",
    "C": ".####.#....#....#....#....#.....####", "D": "####.#...##...##...##...##...#####.",
    "E": "######....####.#....#....#....#####", "F": "######....####.#....#....#....#....",
    "G": ".####.#....#..###...##...##...#.####", "H": "#...##...#######...##...##...##...#",
    "I": "#####..#....#....#....#....#..#####", "J": "....#....#....#....##...##...#.###.",
    "K": "#...##..#.###..#..#.#...##...##...#", "L": "#....#....#....#....#....#....#####",
    "M": "#...###.###.#.##...##...##...##...#", "N": "#...###..##.#.##..###...##...##...#",
    "O": ".###.#...##...##...##...##...#.###.", "P": "####.#...##...#####.#....#....#....",
    "Q": ".###.#...##...##...##.#.##..#..##.#", "R": "####.#...##...#####.#.#..#..#.#...#",
    "S": ".#####.....###.....#....#....######", "T": "#####..#....#....#....#....#....#..",
    "U": "#...##...##...##...##...##...#.###.", "V": "#...##...##...##...#.#.#..#.#...#..",
    "W": "#...##...##...##.#.##.#.###.###...#", "X": "#...#.#.#...#...#.#.#...##...##...#",
    "Y": "#...#.#.#...#....#....#....#....#..", "Z": "#####....#...#...#...#...#....#####",
    "0": ".###.#..###.#.###..#.###.#..#..###.", "1": "..#..##....#....#....#....#...#####",
    "2": ".###.#...#....#...#...#...#...#####", "3": "####.....#..##.....#....#....#####.",
    "4": "#...##...##...######....#....#....#", "5": "######....####.....#....#....#####.",
    "6": ".###.#....####.#...##...##...#.###.", "7": "#####....#...#...#....#....#....#..",
    "8": ".###.#...#.###.#...##...##...#.###.", "9": ".###.#...##...#.####....#....#.###.",
}


# --- canvas -----------------------------------------------------------------------------------

class Canvas:
    """RGBA float canvas in icon units (0..1, y down), supersampled."""

    def __init__(self):
        self.px = np.zeros((N, N, 4), np.float32)
        c = (np.arange(N) + 0.5) / N
        self.x, self.y = np.meshgrid(c, c)

    def fill(self, mask, colour, alpha=1.0):
        r, g, b = colour[:3]
        a = mask.astype(np.float32) * alpha
        src = np.array([r, g, b], np.float32)
        out = self.px
        oa = out[..., 3]
        na = a + oa * (1 - a)
        safe = np.where(na > 0, na, 1)
        for i in range(3):
            out[..., i] = (src[i] * a + out[..., i] * oa * (1 - a)) / safe
        out[..., 3] = na

    # shapes ---------------------------------------------------------------------------------
    def circle(self, cx, cy, r, colour, alpha=1.0):
        self.fill((self.x - cx) ** 2 + (self.y - cy) ** 2 <= r * r, colour, alpha)

    def ellipse(self, cx, cy, rx, ry, colour, alpha=1.0):
        self.fill(((self.x - cx) / rx) ** 2 + ((self.y - cy) / ry) ** 2 <= 1, colour, alpha)

    def ring(self, cx, cy, r0, r1, colour, alpha=1.0):
        d = (self.x - cx) ** 2 + (self.y - cy) ** 2
        self.fill((d <= r1 * r1) & (d >= r0 * r0), colour, alpha)

    def rect(self, x0, y0, x1, y1, colour, alpha=1.0):
        self.fill((self.x >= x0) & (self.x <= x1) & (self.y >= y0) & (self.y <= y1), colour, alpha)

    def poly(self, pts, colour, alpha=1.0):
        inside = np.zeros((N, N), bool)
        n = len(pts)
        for i in range(n):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
            cond = (self.y >= min(y0, y1)) & (self.y < max(y0, y1))
            if y1 != y0:
                xi = x0 + (self.y - y0) * (x1 - x0) / (y1 - y0)
                inside ^= cond & (self.x < xi)
        self.fill(inside, colour, alpha)

    def line(self, p0, p1, w, colour, alpha=1.0):
        (x0, y0), (x1, y1) = p0, p1
        dx, dy = x1 - x0, y1 - y0
        ll = dx * dx + dy * dy or 1e-9
        t = np.clip(((self.x - x0) * dx + (self.y - y0) * dy) / ll, 0, 1)
        d = (self.x - x0 - t * dx) ** 2 + (self.y - y0 - t * dy) ** 2
        self.fill(d <= (w / 2) ** 2, colour, alpha)

    def polyline(self, pts, w, colour, alpha=1.0):
        for a, b in zip(pts, pts[1:]):
            self.line(a, b, w, colour, alpha)

    def text(self, s, colour, x0=None, y0=0.27, cell=0.066):
        s = s[:2]
        width = len(s) * 6 * cell - cell
        x = (1 - width) / 2 if x0 is None else x0
        for ch in s:
            bits = FONT.get(ch.upper(), "")
            for k, bit in enumerate(bits):
                if bit == "#":
                    r, c = divmod(k, 5)
                    self.rect(x + c * cell, y0 + r * cell, x + (c + 1) * cell, y0 + (r + 1) * cell, colour)
            x += 6 * cell

    def result(self):
        return self.px.reshape(SIZE, SS, SIZE, SS, 4).mean(axis=(1, 3))


def shade(colour, k):
    """Lighter (k > 0) or darker (k < 0) version of a colour."""
    if k >= 0:
        return tuple(c + (1 - c) * k for c in colour[:3])
    return tuple(c * (1 + k) for c in colour[:3])


WHITE = (0.95, 0.95, 0.95)
DARK = (0.16, 0.16, 0.16)


# --- glyphs -----------------------------------------------------------------------------------

def g_cube(cv, c):
    top = [(0.5, 0.14), (0.86, 0.32), (0.5, 0.5), (0.14, 0.32)]
    cv.poly(top, shade(c, 0.35))
    cv.poly([(0.14, 0.32), (0.5, 0.5), (0.5, 0.88), (0.14, 0.70)], c)
    cv.poly([(0.5, 0.5), (0.86, 0.32), (0.86, 0.70), (0.5, 0.88)], shade(c, -0.35))


def g_sphere(cv, c):
    cv.circle(0.5, 0.52, 0.36, shade(c, -0.35))
    cv.circle(0.46, 0.48, 0.30, c)
    cv.circle(0.40, 0.40, 0.14, shade(c, 0.45))


def g_cylinder(cv, c):
    cv.rect(0.2, 0.26, 0.8, 0.76, c)
    cv.rect(0.5, 0.26, 0.8, 0.76, shade(c, -0.25))
    cv.ellipse(0.5, 0.76, 0.3, 0.1, shade(c, -0.25))
    cv.ellipse(0.5, 0.26, 0.3, 0.1, shade(c, 0.35))


def g_cone(cv, c):
    cv.ellipse(0.5, 0.78, 0.32, 0.1, shade(c, -0.3))
    cv.poly([(0.5, 0.12), (0.82, 0.78), (0.18, 0.78)], c)
    cv.poly([(0.5, 0.12), (0.82, 0.78), (0.5, 0.86)], shade(c, -0.25))


def g_torus(cv, c):
    cv.ellipse(0.5, 0.52, 0.40, 0.28, shade(c, -0.25))
    cv.ellipse(0.5, 0.48, 0.38, 0.25, c)
    m = ((cv.x - 0.5) / 0.17) ** 2 + ((cv.y - 0.5) / 0.09) ** 2 <= 1
    cv.px[m] = 0


def g_plane(cv, c):
    cv.poly([(0.30, 0.30), (0.92, 0.30), (0.70, 0.72), (0.08, 0.72)], c)
    cv.polyline([(0.40, 0.30), (0.19, 0.72)], 0.025, shade(c, -0.4))
    cv.polyline([(0.61, 0.30), (0.40, 0.72)], 0.025, shade(c, -0.4))
    cv.polyline([(0.19, 0.51), (0.81, 0.51)], 0.025, shade(c, -0.4))


def g_disc(cv, c):
    cv.ellipse(0.5, 0.56, 0.40, 0.2, shade(c, -0.3))
    cv.ellipse(0.5, 0.52, 0.40, 0.2, c)


def g_platonic(cv, c):
    pts = [(0.5 + 0.38 * math.cos(math.radians(a)), 0.5 + 0.38 * math.sin(math.radians(a))) for a in range(-90, 270, 60)]
    cv.poly(pts, c)
    cv.poly([pts[0], pts[2], pts[4]], shade(c, 0.3))


def g_curve(cv, c):
    pts = [(0.1 + 0.8 * t, 0.7 - 0.45 * math.sin(math.pi * t) + 0.1 * math.sin(3 * math.pi * t))
           for t in np.linspace(0, 1, 24)]
    cv.polyline(pts, 0.07, c)
    cv.circle(0.1, 0.7, 0.06, WHITE)
    cv.circle(0.9, 0.7, 0.06, WHITE)


def g_circle_outline(cv, c):
    cv.ring(0.5, 0.5, 0.28, 0.36, c)


def g_square_outline(cv, c):
    cv.rect(0.18, 0.18, 0.82, 0.82, c)
    cv.px[(cv.x > 0.26) & (cv.x < 0.74) & (cv.y > 0.26) & (cv.y < 0.74)] = 0


def g_arrow_up(cv, c, base=True):
    if base:
        cv.rect(0.16, 0.66, 0.84, 0.86, shade(c, -0.25))
    cv.poly([(0.5, 0.10), (0.78, 0.40), (0.60, 0.40), (0.60, 0.66), (0.40, 0.66), (0.40, 0.40), (0.22, 0.40)], c)


def g_bevel(cv, c):
    cv.poly([(0.16, 0.16), (0.62, 0.16), (0.84, 0.38), (0.84, 0.84), (0.16, 0.84)], c)
    cv.poly([(0.62, 0.16), (0.84, 0.38), (0.70, 0.38), (0.62, 0.30)], shade(c, 0.4))


def g_bridge(cv, c):
    cv.rect(0.10, 0.50, 0.28, 0.86, c)
    cv.rect(0.72, 0.50, 0.90, 0.86, c)
    pts = [(0.19 + 0.62 * t, 0.50 - 0.30 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 16)]
    cv.polyline(pts, 0.09, shade(c, 0.3))


def g_merge(cv, c):
    cv.circle(0.18, 0.5, 0.1, c)
    cv.circle(0.82, 0.5, 0.1, c)
    cv.line((0.3, 0.5), (0.42, 0.5), 0.06, WHITE)
    cv.line((0.58, 0.5), (0.7, 0.5), 0.06, WHITE)
    cv.circle(0.5, 0.5, 0.1, shade(c, 0.4))


def g_two_squares(cv, c):
    cv.rect(0.12, 0.12, 0.62, 0.62, shade(c, -0.25))
    cv.rect(0.38, 0.38, 0.88, 0.88, c)


def g_split_squares(cv, c):
    cv.rect(0.08, 0.30, 0.42, 0.70, c)
    cv.rect(0.58, 0.30, 0.92, 0.70, shade(c, 0.3))
    cv.line((0.5, 0.12), (0.5, 0.88), 0.04, WHITE)


def g_mirror(cv, c):
    cv.poly([(0.46, 0.18), (0.46, 0.82), (0.12, 0.66), (0.12, 0.34)], c)
    cv.poly([(0.54, 0.18), (0.54, 0.82), (0.88, 0.66), (0.88, 0.34)], c, 0.45)
    for y in (0.1, 0.3, 0.5, 0.7):
        cv.line((0.5, y), (0.5, y + 0.12), 0.04, WHITE)


def g_smooth(cv, c):
    g_sphere(cv, c)
    cv.ring(0.5, 0.5, 0.40, 0.44, WHITE, 0.8)


def g_knife(cv, c):
    cv.rect(0.16, 0.30, 0.84, 0.86, c)
    cv.line((0.10, 0.20), (0.90, 0.62), 0.07, WHITE)
    cv.poly([(0.06, 0.10), (0.30, 0.18), (0.22, 0.30)], WHITE)


def g_grid(cv, c):
    cv.rect(0.14, 0.14, 0.86, 0.86, c)
    for t in (0.38, 0.62):
        cv.line((t, 0.14), (t, 0.86), 0.035, DARK)
        cv.line((0.14, t), (0.86, t), 0.035, DARK)


def g_dots_ring(cv, c):
    for k in range(8):
        a = 2 * math.pi * k / 8
        cv.circle(0.5 + 0.32 * math.cos(a), 0.5 + 0.32 * math.sin(a), 0.07, c)


def g_crosshair(cv, c):
    cv.ring(0.5, 0.5, 0.22, 0.29, c)
    cv.line((0.5, 0.06), (0.5, 0.94), 0.05, WHITE)
    cv.line((0.06, 0.5), (0.94, 0.5), 0.05, WHITE)


def g_x(cv, c):
    cv.rect(0.12, 0.12, 0.88, 0.88, shade(c, -0.3))
    cv.line((0.26, 0.26), (0.74, 0.74), 0.11, WHITE)
    cv.line((0.74, 0.26), (0.26, 0.74), 0.11, WHITE)


def g_asterisk(cv, c):
    for a in (0, 60, 120):
        r = math.radians(a)
        cv.line((0.5 - 0.38 * math.cos(r), 0.5 - 0.38 * math.sin(r)),
                (0.5 + 0.38 * math.cos(r), 0.5 + 0.38 * math.sin(r)), 0.09, c)


def g_checker(cv, c):
    for i in range(4):
        for j in range(4):
            cv.rect(0.12 + i * 0.19, 0.12 + j * 0.19, 0.31 + i * 0.19, 0.31 + j * 0.19,
                    c if (i + j) % 2 else WHITE)


def g_locator(cv, c):
    cv.line((0.5, 0.08), (0.5, 0.92), 0.08, c)
    cv.line((0.08, 0.5), (0.92, 0.5), 0.08, c)
    cv.line((0.22, 0.78), (0.78, 0.22), 0.08, shade(c, 0.3))


def g_joint(cv, c):
    cv.line((0.28, 0.72), (0.72, 0.28), 0.12, shade(c, -0.2))
    cv.circle(0.28, 0.72, 0.15, c)
    cv.circle(0.72, 0.28, 0.15, c)


def g_ik(cv, c):
    cv.polyline([(0.14, 0.82), (0.5, 0.24), (0.86, 0.82)], 0.09, c)
    cv.line((0.14, 0.82), (0.86, 0.82), 0.04, WHITE)
    for p in ((0.14, 0.82), (0.5, 0.24), (0.86, 0.82)):
        cv.circle(*p, 0.09, shade(c, 0.4))


def g_chain(cv, c):
    cv.ellipse(0.36, 0.42, 0.24, 0.14, c)
    cv.px[((cv.x - 0.36) / 0.15) ** 2 + ((cv.y - 0.42) / 0.06) ** 2 <= 1] = 0
    cv.ellipse(0.64, 0.58, 0.24, 0.14, shade(c, 0.3))
    cv.px[((cv.x - 0.64) / 0.15) ** 2 + ((cv.y - 0.58) / 0.06) ** 2 <= 1] = 0


def g_key(cv, c):
    cv.poly([(0.5, 0.1), (0.86, 0.5), (0.5, 0.9), (0.14, 0.5)], (0.9, 0.25, 0.22))
    cv.poly([(0.5, 0.24), (0.72, 0.5), (0.5, 0.76), (0.28, 0.5)], (1.0, 0.55, 0.5))


def g_light(cv, c):
    for a in range(0, 360, 45):
        r = math.radians(a)
        cv.line((0.5 + 0.3 * math.cos(r), 0.44 + 0.3 * math.sin(r)),
                (0.5 + 0.44 * math.cos(r), 0.44 + 0.44 * math.sin(r)), 0.05, c)
    cv.circle(0.5, 0.44, 0.22, shade(c, 0.4))
    cv.rect(0.42, 0.62, 0.58, 0.82, shade(c, -0.4))


def g_camera(cv, c):
    cv.rect(0.10, 0.30, 0.62, 0.74, c)
    cv.poly([(0.62, 0.52), (0.90, 0.32), (0.90, 0.72)], shade(c, -0.25))
    cv.circle(0.28, 0.22, 0.09, shade(c, 0.3))
    cv.circle(0.48, 0.22, 0.09, shade(c, 0.3))


def g_clapper(cv, c):
    cv.rect(0.12, 0.38, 0.88, 0.86, shade(c, -0.3))
    cv.poly([(0.12, 0.20), (0.84, 0.10), (0.88, 0.30), (0.16, 0.38)], c)
    for x in (0.3, 0.5, 0.7):
        cv.line((x, 0.17), (x + 0.06, 0.33), 0.05, DARK)


def g_brush(cv, c):
    pts = [(0.08 + 0.84 * t, 0.66 + 0.1 * math.sin(2 * math.pi * t)) for t in np.linspace(0, 1, 20)]
    cv.polyline(pts, 0.12, c)
    cv.line((0.62, 0.12), (0.44, 0.52), 0.1, shade(c, 0.35))
    cv.circle(0.42, 0.56, 0.08, WHITE)


def g_particles(cv, c):
    rng = np.random.default_rng(7)
    for _ in range(9):
        x, y = rng.uniform(0.15, 0.85, 2)
        cv.circle(x, y, rng.uniform(0.04, 0.08), c)
    cv.rect(0.38, 0.80, 0.62, 0.92, shade(c, -0.3))


def g_hair(cv, c):
    for k in range(4):
        x0 = 0.2 + 0.2 * k
        pts = [(x0 + 0.06 * math.sin(4 * t), 0.88 - 0.7 * t) for t in np.linspace(0, 1, 12)]
        cv.polyline(pts, 0.05, c)
    cv.rect(0.12, 0.84, 0.88, 0.92, shade(c, -0.3))


def g_cloth(cv, c):
    top = [(0.12 + 0.76 * t, 0.2 + 0.06 * math.sin(6 * t)) for t in np.linspace(0, 1, 10)]
    bot = [(0.88 - 0.76 * t, 0.82 + 0.08 * math.sin(5 * t)) for t in np.linspace(0, 1, 10)]
    cv.poly(top + bot, c)
    cv.line((0.3, 0.26), (0.28, 0.8), 0.03, shade(c, -0.3))
    cv.line((0.6, 0.24), (0.62, 0.84), 0.03, shade(c, -0.3))


def g_cache(cv, c):
    for k, y in enumerate((0.70, 0.50, 0.30)):
        cv.ellipse(0.5, y + 0.06, 0.34, 0.12, shade(c, -0.3))
        cv.ellipse(0.5, y, 0.34, 0.12, shade(c, 0.15 * k))


def g_film(cv, c):
    cv.rect(0.10, 0.20, 0.90, 0.80, c)
    for x in np.linspace(0.16, 0.80, 5):
        cv.rect(x, 0.24, x + 0.05, 0.30, DARK)
        cv.rect(x, 0.70, x + 0.05, 0.76, DARK)
    cv.poly([(0.42, 0.38), (0.62, 0.5), (0.42, 0.62)], WHITE)


def g_lattice(cv, c):
    g_grid(cv, shade(c, -0.1))
    for p in ((0.14, 0.14), (0.86, 0.14), (0.14, 0.86), (0.86, 0.86), (0.5, 0.5)):
        cv.circle(*p, 0.07, WHITE)


def g_wave(cv, c):
    for k in range(3):
        pts = [(0.1 + 0.8 * t, 0.3 + 0.2 * k + 0.08 * math.sin(2 * math.pi * t + k)) for t in np.linspace(0, 1, 14)]
        cv.polyline(pts, 0.07, shade(c, 0.15 * k))


def g_type(cv, c):
    cv.text("T", c, y0=0.22, cell=0.11)


def g_play(cv, c):
    cv.poly([(0.28, 0.16), (0.82, 0.5), (0.28, 0.84)], c)


def g_stop(cv, c):
    cv.rect(0.22, 0.22, 0.78, 0.78, c)


# Keyword -> glyph, first match wins (on the lower-case label).
GLYPHS = (
    (("set key",), g_key), (("driven key",), g_key), (("material", "shading map"), None),
    (("light",), g_light), (("camera",), g_camera), (("sphere",), g_sphere), (("cube",), g_cube),
    (("cylinder",), g_cylinder), (("cone",), g_cone), (("torus",), g_torus), (("plane",), g_plane),
    (("disc",), g_disc), (("platonic", "super shape"), g_platonic), (("circle", "arc"), g_circle_outline),
    (("square",), g_square_outline), (("curve", "pencil", "knot", "cvs"), g_curve),
    (("extrude",), g_arrow_up), (("bevel",), g_bevel), (("bridge", "birail", "loft"), g_bridge),
    (("merge", "weld", "collapse", "attach", "combine"), g_merge), (("mirror",), g_mirror),
    (("extract", "detach", "separate"), g_split_squares), (("duplicate",), g_two_squares),
    (("smooth", "relax", "reduce", "remesh", "retopo"), g_smooth),
    (("multi-cut", "knife", "trim", "cut"), g_knife), (("quad draw",), g_grid),
    (("circularize",), g_dots_ring), (("pivot",), g_crosshair), (("history", "remove", "delete", "cancel"), g_x),
    (("freeze",), g_asterisk), (("uv", "mapping", "stretch"), g_checker), (("locator",), g_locator),
    (("joint", "skin", "rig", "human ik"), g_joint), (("ik handle", "pole vector"), g_ik),
    (("constraint",), g_chain), (("lattice", "cluster"), g_lattice),
    (("blend shape", "shape editor", "pose editor", "target"), g_wave),
    (("render", "batch", "playblast"), g_clapper), (("type", "svg"), g_type),
    (("emitter", "emit", "fluid", "particle", "collide"), g_particles), (("hair", "follicle", "dynamic"), g_hair),
    (("cloth", "passive", "mesh"), g_cloth), (("cache", "initial state", "position"), g_cache),
    (("motion trail", "bake", "sequence"), g_film), (("interactive playback",), g_play),
    (("revolve", "planar", "isoparm", "surface"), g_plane),
    (("sculpt", "tool", "grab", "pinch", "flatten", "foamy", "spray", "repeat", "imprint", "wax", "scrape",
      "fill", "smear", "bulge", "amplify", "paint"), g_brush),
)

MATERIAL_COLOURS = {
    "lambert": (0.55, 0.55, 0.60), "blinn": (0.45, 0.60, 0.85), "phong": (0.85, 0.55, 0.45),
    "anisotropic": (0.80, 0.75, 0.45), "standard": (0.75, 0.75, 0.80), "layered": (0.60, 0.80, 0.55),
    "ramp": (0.90, 0.45, 0.70), "surface": (0.95, 0.60, 0.30), "shading map": (0.55, 0.45, 0.85),
}


def initials(label):
    words = [w for w in label.replace("/", " ").replace("-", " ").split() if w[0].isalnum()]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def glyph_for(label):
    low = label.lower()
    for keys, glyph in GLYPHS:
        if any(k in low for k in keys):
            if glyph is None:   # materials: a sphere in the shader's typical colour
                colour = next((v for k, v in MATERIAL_COLOURS.items() if k in low), (0.7, 0.7, 0.7))
                return lambda cv, c: g_sphere(cv, colour)
            return glyph
    return None


def draw(label, shelf=None):
    """32x32 RGBA (float, straight alpha) icon for a shelf button."""
    colour = SHELF_COLOURS.get(shelf, USER_COLOUR)
    cv = Canvas()
    glyph = glyph_for(label)
    if glyph is None:
        cv.rect(0.08, 0.08, 0.92, 0.92, shade(colour, -0.35))
        cv.rect(0.12, 0.12, 0.88, 0.88, colour)
        cv.text(initials(label), DARK)
    else:
        glyph(cv, colour)
    return cv.result()


# --- GPU textures -----------------------------------------------------------------------------

_textures = {}


def texture(label, shelf=None):
    """Cached GPU texture of a button's icon (needs a GPU context: call from a draw handler)."""
    key = (label, shelf)
    tex = _textures.get(key)
    if tex is None:
        import gpu
        px = draw(label, shelf)[::-1].copy()   # GPU rows go bottom-up
        # the palette is sRGB; the image editor draws in linear and converts for display
        rgb = px[..., :3]
        px[..., :3] = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
        buf = gpu.types.Buffer('FLOAT', SIZE * SIZE * 4, px.ravel().tolist())
        tex = _textures[key] = gpu.types.GPUTexture((SIZE, SIZE), format='RGBA32F', data=buf)
    return tex


def clear():
    _textures.clear()
