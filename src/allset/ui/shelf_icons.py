# SPDX-License-Identifier: GPL-3.0-or-later
"""Kit-made colour shelf icons, drawn by code.

Decision 6: no Maya icons. Maya's shelf shows 32 px colour pictograms (,
ui_layout.md:219-222); here every button gets a small vector drawing in its shelf's colour: the
primitive's shape for creation buttons, a symbol for tools (arrow, knife, chain, bulb, key, ...),
two letters when nothing fits. Step 109 re-drew them in Maya's style: one
checked hue per shelf, tool parts light grey, flat two-tone shapes; greyed buttons are drawn faded. Shapes are rasterised with numpy (4x supersampled, no files, no bpy);
``texture()`` turns one into a GPU texture for ``ui/shelf.py``'s icon row.
"""

import math

import numpy as np

SIZE = 32
SS = 4                 # supersampling
N = SIZE * SS

# Shelf hues checked in Maya 2022's shelf grabs (*.png, most common
# saturated colour of the icon row, step 109): Curves / Surfaces #58a8d0, Poly Modeling and Sculpting #d89058,
# Rigging #a898d8, Animation #e07040, Rendering #c0b038, FX and FX Caching #d88070.
SHELF_COLOURS = {
    "CurvesSurfaces": (0x58 / 255, 0xa8 / 255, 0xd0 / 255), "Polygons": (0xd8 / 255, 0x90 / 255, 0x58 / 255),
    "Sculpting": (0xd8 / 255, 0x90 / 255, 0x58 / 255), "Rigging": (0xa8 / 255, 0x98 / 255, 0xd8 / 255),
    "Animation": (0xe0 / 255, 0x70 / 255, 0x40 / 255), "Rendering": (0xc0 / 255, 0xb0 / 255, 0x38 / 255),
    "FX": (0xd8 / 255, 0x80 / 255, 0x70 / 255), "FXCaching": (0xd8 / 255, 0x80 / 255, 0x70 / 255),
}
USER_COLOUR = (0.63, 0.63, 0.63)
GREYED_ALPHA = 0.35     # greyed (unmapped) buttons: grey and faded, like a disabled Maya control

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


LIGHT = (0xc0 / 255,) * 3      # Maya's light grey of tool parts (#c0c0c0, same grabs)
DARK = (0.16, 0.16, 0.16)


# --- glyphs -----------------------------------------------------------------------------------

# Maya's shelf pictograms (*.png, step 109): flat two-tone drawings —
# objects (primitives, lights, curves) filled with the shelf hue and a darker hue for the shaded side, tools in
# light grey #c0c0c0 with one part in the shelf hue. No white highlights, no gradients.

def g_cube(cv, c):
    cv.poly([(0.5, 0.12), (0.88, 0.30), (0.5, 0.48), (0.12, 0.30)], shade(c, 0.12))
    cv.poly([(0.12, 0.30), (0.5, 0.48), (0.5, 0.90), (0.12, 0.72)], c)
    cv.poly([(0.5, 0.48), (0.88, 0.30), (0.88, 0.72), (0.5, 0.90)], shade(c, -0.18))
    cv.polyline([(0.12, 0.30), (0.5, 0.48), (0.88, 0.30)], 0.03, shade(c, -0.45))
    cv.line((0.5, 0.48), (0.5, 0.90), 0.03, shade(c, -0.45))


def g_sphere(cv, c):
    cv.circle(0.5, 0.5, 0.38, c)
    cv.fill((((cv.x - 0.5) ** 2 + (cv.y - 0.5) ** 2) <= 0.38 ** 2) & (cv.x + cv.y > 1.12), shade(c, -0.18))
    for k in (-0.19, 0.0, 0.19):
        m = (np.abs((cv.y - 0.5) - k) < 0.016) & ((cv.x - 0.5) ** 2 + (cv.y - 0.5) ** 2 <= 0.37 ** 2)
        cv.fill(m, shade(c, -0.45))
    m = (np.abs(cv.x - 0.5) < 0.016) & ((cv.x - 0.5) ** 2 + (cv.y - 0.5) ** 2 <= 0.37 ** 2)
    cv.fill(m, shade(c, -0.45))


def g_cylinder(cv, c):
    cv.rect(0.20, 0.26, 0.80, 0.76, c)
    cv.ellipse(0.5, 0.76, 0.30, 0.10, c)
    cv.rect(0.56, 0.26, 0.80, 0.80, shade(c, -0.18))
    cv.ellipse(0.5, 0.26, 0.30, 0.10, shade(c, 0.12))
    m = (np.abs(((cv.x - 0.5) / 0.30) ** 2 + ((cv.y - 0.26) / 0.10) ** 2 - 1) < 0.12)
    cv.fill(m, shade(c, -0.45))


def g_cone(cv, c):
    cv.ellipse(0.5, 0.78, 0.32, 0.10, shade(c, -0.18))
    cv.poly([(0.5, 0.10), (0.82, 0.78), (0.18, 0.78)], c)
    cv.poly([(0.5, 0.10), (0.82, 0.78), (0.58, 0.86)], shade(c, -0.18))


def g_torus(cv, c):
    cv.ellipse(0.5, 0.5, 0.40, 0.28, c)
    cv.fill((((cv.x - 0.5) / 0.40) ** 2 + ((cv.y - 0.5) / 0.28) ** 2 <= 1) & (cv.y > 0.56), shade(c, -0.18))
    cv.px[((cv.x - 0.5) / 0.17) ** 2 + ((cv.y - 0.5) / 0.09) ** 2 <= 1] = 0


def g_plane(cv, c):
    cv.poly([(0.5, 0.16), (0.88, 0.5), (0.5, 0.84), (0.12, 0.5)], c)
    cv.line((0.31, 0.33), (0.69, 0.67), 0.03, shade(c, -0.45))
    cv.line((0.69, 0.33), (0.31, 0.67), 0.03, shade(c, -0.45))


def g_disc(cv, c):
    cv.ellipse(0.5, 0.54, 0.40, 0.20, shade(c, -0.18))
    cv.ellipse(0.5, 0.50, 0.40, 0.20, c)
    cv.line((0.14, 0.5), (0.86, 0.5), 0.03, shade(c, -0.45))


def g_platonic(cv, c):
    pts = [(0.5 + 0.38 * math.cos(math.radians(a)), 0.5 + 0.38 * math.sin(math.radians(a))) for a in range(-90, 270, 60)]
    cv.poly(pts, c)
    cv.poly([pts[1], pts[2], pts[3], (0.5, 0.5)], shade(c, -0.18))
    cv.polyline([pts[0], pts[2], pts[4], pts[0]], 0.03, shade(c, -0.45))


def g_curve(cv, c):
    pts = [(0.12 + 0.76 * t, 0.68 - 0.40 * math.sin(math.pi * t) + 0.12 * math.sin(3 * math.pi * t))
           for t in np.linspace(0, 1, 24)]
    cv.polyline(pts, 0.06, c)
    for p in (pts[0], pts[-1]):
        cv.rect(p[0] - 0.06, p[1] - 0.06, p[0] + 0.06, p[1] + 0.06, LIGHT)


def g_circle_outline(cv, c):
    cv.ring(0.5, 0.5, 0.30, 0.37, c)


def g_square_outline(cv, c):
    cv.rect(0.16, 0.16, 0.84, 0.84, c)
    cv.px[(cv.x > 0.23) & (cv.x < 0.77) & (cv.y > 0.23) & (cv.y < 0.77)] = 0


def g_arrow_up(cv, c, base=True):
    if base:
        cv.rect(0.16, 0.66, 0.84, 0.88, LIGHT)
    cv.poly([(0.5, 0.10), (0.80, 0.40), (0.61, 0.40), (0.61, 0.66), (0.39, 0.66), (0.39, 0.40), (0.20, 0.40)], c)


def g_bevel(cv, c):
    cv.poly([(0.16, 0.16), (0.60, 0.16), (0.84, 0.40), (0.84, 0.84), (0.16, 0.84)], LIGHT)
    cv.poly([(0.60, 0.16), (0.84, 0.40), (0.72, 0.40), (0.60, 0.28)], c)


def g_bridge(cv, c):
    cv.rect(0.10, 0.50, 0.30, 0.88, LIGHT)
    cv.rect(0.70, 0.50, 0.90, 0.88, LIGHT)
    pts = [(0.20 + 0.60 * t, 0.50 - 0.30 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 16)]
    cv.polyline(pts, 0.09, c)


def g_merge(cv, c):
    cv.circle(0.18, 0.5, 0.10, LIGHT)
    cv.circle(0.82, 0.5, 0.10, LIGHT)
    cv.line((0.30, 0.5), (0.40, 0.5), 0.06, LIGHT)
    cv.line((0.60, 0.5), (0.70, 0.5), 0.06, LIGHT)
    cv.circle(0.5, 0.5, 0.11, c)


def g_two_squares(cv, c):
    cv.rect(0.12, 0.12, 0.60, 0.60, LIGHT)
    cv.rect(0.40, 0.40, 0.88, 0.88, c)


def g_split_squares(cv, c):
    cv.rect(0.08, 0.30, 0.44, 0.70, LIGHT)
    cv.rect(0.56, 0.30, 0.92, 0.70, c)


def g_mirror(cv, c):
    cv.poly([(0.44, 0.18), (0.44, 0.82), (0.10, 0.66), (0.10, 0.34)], c)
    cv.poly([(0.56, 0.18), (0.56, 0.82), (0.90, 0.66), (0.90, 0.34)], LIGHT)
    for y in (0.08, 0.30, 0.52, 0.74):
        cv.line((0.5, y), (0.5, y + 0.12), 0.04, LIGHT)


def g_smooth(cv, c):
    cv.circle(0.5, 0.5, 0.36, c)
    cv.ring(0.5, 0.5, 0.40, 0.45, LIGHT)


def g_knife(cv, c):
    cv.rect(0.16, 0.36, 0.84, 0.86, c)
    cv.line((0.12, 0.22), (0.88, 0.62), 0.07, LIGHT)
    cv.poly([(0.06, 0.10), (0.30, 0.18), (0.22, 0.30)], LIGHT)


def g_grid(cv, c):
    cv.rect(0.14, 0.14, 0.86, 0.86, c)
    for t in (0.38, 0.62):
        cv.line((t, 0.14), (t, 0.86), 0.035, DARK)
        cv.line((0.14, t), (0.86, t), 0.035, DARK)


def g_dots_ring(cv, c):
    for k in range(8):
        a = 2 * math.pi * k / 8
        cv.circle(0.5 + 0.32 * math.cos(a), 0.5 + 0.32 * math.sin(a), 0.07, LIGHT if k % 2 else c)


def g_crosshair(cv, c):
    cv.ring(0.5, 0.5, 0.20, 0.27, c)
    cv.line((0.5, 0.06), (0.5, 0.94), 0.05, LIGHT)
    cv.line((0.06, 0.5), (0.94, 0.5), 0.05, LIGHT)


def g_x(cv, c):
    cv.rect(0.14, 0.14, 0.86, 0.86, c)
    cv.line((0.28, 0.28), (0.72, 0.72), 0.11, DARK)
    cv.line((0.72, 0.28), (0.28, 0.72), 0.11, DARK)


def g_asterisk(cv, c):
    for a, col in ((0, c), (60, LIGHT), (120, LIGHT)):
        r = math.radians(a)
        cv.line((0.5 - 0.38 * math.cos(r), 0.5 - 0.38 * math.sin(r)),
                (0.5 + 0.38 * math.cos(r), 0.5 + 0.38 * math.sin(r)), 0.09, col)


def g_checker(cv, c):
    for i in range(4):
        for j in range(4):
            cv.rect(0.12 + i * 0.19, 0.12 + j * 0.19, 0.31 + i * 0.19, 0.31 + j * 0.19,
                    c if (i + j) % 2 else LIGHT)


def g_locator(cv, c):
    cv.line((0.5, 0.08), (0.5, 0.92), 0.07, c)
    cv.line((0.08, 0.5), (0.92, 0.5), 0.07, c)
    cv.line((0.22, 0.78), (0.78, 0.22), 0.07, c)
    cv.line((0.22, 0.22), (0.78, 0.78), 0.07, c)


def g_joint(cv, c):
    cv.polyline([(0.78, 0.16), (0.30, 0.50), (0.70, 0.86)], 0.06, LIGHT)
    for p in ((0.78, 0.16), (0.30, 0.50), (0.70, 0.86)):
        cv.circle(*p, 0.09, c)


def g_ik(cv, c):
    cv.polyline([(0.16, 0.84), (0.5, 0.24), (0.84, 0.84)], 0.07, LIGHT)
    cv.line((0.16, 0.84), (0.84, 0.84), 0.04, c)
    for p in ((0.16, 0.84), (0.5, 0.24), (0.84, 0.84)):
        cv.circle(*p, 0.08, c)


def g_chain(cv, c):
    cv.rect(0.10, 0.50, 0.50, 0.70, LIGHT)
    cv.ring(0.68, 0.34, 0.07, 0.13, c)
    cv.ring(0.80, 0.22, 0.07, 0.13, c)


def g_key(cv, c):
    cv.line((0.18, 0.5), (0.82, 0.5), 0.06, LIGHT)
    cv.rect(0.42, 0.18, 0.58, 0.82, (0.88, 0.44, 0.25))       # Maya's key red-orange (#e07040)


def g_light(cv, c):
    for a in range(0, 360, 45):
        r = math.radians(a)
        cv.line((0.5 + 0.30 * math.cos(r), 0.5 + 0.30 * math.sin(r)),
                (0.5 + 0.44 * math.cos(r), 0.5 + 0.44 * math.sin(r)), 0.06, c)
    cv.circle(0.5, 0.5, 0.22, c)


def g_camera(cv, c):
    cv.rect(0.10, 0.30, 0.62, 0.74, c)
    cv.poly([(0.62, 0.52), (0.90, 0.32), (0.90, 0.72)], c)
    cv.line((0.62, 0.70), (0.92, 0.70), 0.04, LIGHT)
    cv.line((0.77, 0.56), (0.77, 0.86), 0.04, LIGHT)


def g_clapper(cv, c):
    cv.rect(0.12, 0.38, 0.88, 0.86, LIGHT)
    cv.poly([(0.12, 0.20), (0.84, 0.10), (0.88, 0.30), (0.16, 0.38)], c)
    for x in (0.3, 0.5, 0.7):
        cv.line((x, 0.17), (x + 0.06, 0.33), 0.05, DARK)


def g_brush(cv, c):
    cv.circle(0.5, 0.52, 0.34, c)
    cv.line((0.86, 0.10), (0.56, 0.44), 0.09, LIGHT)
    cv.circle(0.54, 0.47, 0.08, LIGHT)


def g_sculpt(cv, c, label):
    """Maya's sculpt tool icons: an orange ball, each with its own grey mark; here the mark's angle and size
    follow the label so the tools stay apart."""
    cv.circle(0.5, 0.52, 0.36, c)
    k = sum(map(ord, label))
    a = math.radians(45 * (k % 8) - 90)
    r = 0.10 + 0.02 * (k % 3)
    cx, cy = 0.5 + 0.30 * math.cos(a), 0.52 + 0.30 * math.sin(a)
    cv.circle(cx, cy, r, LIGHT)
    cv.line((0.5, 0.52), (cx, cy), 0.05, LIGHT)


def g_particles(cv, c):
    for k in range(8):
        a = 2 * math.pi * k / 8
        cv.circle(0.5 + 0.32 * math.cos(a), 0.5 + 0.32 * math.sin(a), 0.07, c)
    cv.circle(0.5, 0.5, 0.15, LIGHT)


def g_hair(cv, c):
    for k in range(3):
        x0 = 0.26 + 0.22 * k
        pts = [(x0 + 0.08 * math.sin(4 * t), 0.86 - 0.70 * t) for t in np.linspace(0, 1, 12)]
        cv.polyline(pts, 0.05, c)
    cv.rect(0.14, 0.84, 0.86, 0.92, LIGHT)


def g_cloth(cv, c):
    cv.poly([(0.30, 0.16), (0.40, 0.22), (0.60, 0.22), (0.70, 0.16), (0.90, 0.30), (0.80, 0.46), (0.72, 0.42),
             (0.72, 0.86), (0.28, 0.86), (0.28, 0.42), (0.20, 0.46), (0.10, 0.30)], c)


def g_cache(cv, c):
    cv.rect(0.14, 0.26, 0.86, 0.74, c)
    cv.rect(0.20, 0.36, 0.80, 0.64, LIGHT)
    for x in np.linspace(0.18, 0.78, 5):
        cv.rect(x, 0.28, x + 0.05, 0.33, DARK)
        cv.rect(x, 0.67, x + 0.05, 0.72, DARK)


def g_film(cv, c):
    cv.rect(0.10, 0.22, 0.90, 0.78, LIGHT)
    for x in np.linspace(0.16, 0.80, 5):
        cv.rect(x, 0.26, x + 0.05, 0.32, DARK)
        cv.rect(x, 0.68, x + 0.05, 0.74, DARK)
    cv.poly([(0.42, 0.38), (0.62, 0.5), (0.42, 0.62)], c)


def g_lattice(cv, c):
    cv.rect(0.14, 0.14, 0.86, 0.86, LIGHT)
    cv.px[(cv.x > 0.19) & (cv.x < 0.81) & (cv.y > 0.19) & (cv.y < 0.81)] = 0
    for t in (0.38, 0.62):
        cv.line((t, 0.14), (t, 0.86), 0.035, LIGHT)
        cv.line((0.14, t), (0.86, t), 0.035, LIGHT)
    for p in ((0.14, 0.14), (0.86, 0.14), (0.14, 0.86), (0.86, 0.86)):
        cv.circle(*p, 0.07, c)


def g_wave(cv, c):
    for k in range(3):
        pts = [(0.1 + 0.8 * t, 0.3 + 0.2 * k + 0.08 * math.sin(2 * math.pi * t + k)) for t in np.linspace(0, 1, 14)]
        cv.polyline(pts, 0.07, c if k == 1 else LIGHT)


def g_type(cv, c):
    cv.text("T", c, y0=0.22, cell=0.11)


def g_play(cv, c):
    cv.poly([(0.28, 0.16), (0.82, 0.5), (0.28, 0.84)], c)


def g_stop(cv, c):
    cv.rect(0.22, 0.22, 0.78, 0.78, c)


def g_window(cv, c):
    """An editor window (Maya's window buttons: UV Editor, Shape Editor, Content Browser ...)."""
    cv.rect(0.12, 0.16, 0.88, 0.84, LIGHT)
    cv.rect(0.16, 0.30, 0.84, 0.80, (0.28, 0.66, 0.72))        # Maya's window teal #48a8b8
    for x in (0.18, 0.26, 0.34):
        cv.rect(x, 0.20, x + 0.05, 0.25, DARK)


def g_fluid(cv, c):
    cv.rect(0.14, 0.14, 0.86, 0.86, LIGHT)
    cv.px[(cv.x > 0.19) & (cv.x < 0.81) & (cv.y > 0.19) & (cv.y < 0.81)] = 0
    pts = [(0.19 + 0.62 * t, 0.62 + 0.08 * math.sin(2 * math.pi * t)) for t in np.linspace(0, 1, 14)]
    cv.poly(pts + [(0.81, 0.81), (0.19, 0.81)], c)


# --- step 113: buttons that shared one picture (Poly Modeling's four orange balls, six identical checkers) ----------

def g_reduce(cv, c):
    cv.poly([(0.10, 0.86), (0.50, 0.14), (0.90, 0.86)], c)
    cv.line((0.30, 0.50), (0.70, 0.50), 0.05, LIGHT)
    cv.line((0.50, 0.50), (0.50, 0.86), 0.05, LIGHT)


def g_remesh(cv, c):
    cv.poly([(0.10, 0.86), (0.50, 0.14), (0.90, 0.86)], c)
    for k in (0.38, 0.62):
        cv.line((0.5 - 0.4 * k, 0.14 + 0.72 * k), (0.5 + 0.4 * k, 0.14 + 0.72 * k), 0.04, LIGHT)
    cv.line((0.30, 0.50), (0.50, 0.86), 0.04, LIGHT)
    cv.line((0.70, 0.50), (0.50, 0.86), 0.04, LIGHT)


def g_retopo(cv, c):
    cv.rect(0.12, 0.12, 0.88, 0.88, c)
    for k in (0.37, 0.62):
        cv.line((k, 0.12), (k, 0.88), 0.05, LIGHT)
        cv.line((0.12, k), (0.88, k), 0.05, LIGHT)


def g_merge_center(cv, c):
    for x, y in ((0.18, 0.18), (0.82, 0.18), (0.18, 0.82), (0.82, 0.82)):
        cv.circle(x, y, 0.08, LIGHT)
        cv.line((x, y), (0.5 + (x - 0.5) * 0.35, 0.5 + (y - 0.5) * 0.35), 0.05, LIGHT)
    cv.circle(0.5, 0.5, 0.13, c)


def g_collapse(cv, c):
    cv.poly([(0.10, 0.20), (0.90, 0.20), (0.58, 0.50), (0.42, 0.50)], c)
    cv.poly([(0.42, 0.50), (0.58, 0.50), (0.90, 0.80), (0.10, 0.80)], shade(c, -0.3))
    cv.circle(0.5, 0.5, 0.08, LIGHT)


def g_target_weld(cv, c):
    cv.circle(0.30, 0.66, 0.10, LIGHT)
    cv.line((0.38, 0.58), (0.66, 0.30), 0.06, LIGHT)
    cv.ring(0.72, 0.28, 0.10, 0.16, c)


def _checker_mask(cv, mask, c):
    cell = ((np.floor(cv.x / 0.19) + np.floor(cv.y / 0.19)) % 2).astype(bool)
    cv.fill(mask & cell, c)
    cv.fill(mask & ~cell, LIGHT)


def g_uv_planar(cv, c):
    _checker_mask(cv, (cv.x > 0.12) & (cv.x < 0.88) & (cv.y > 0.30) & (cv.y < 0.88), c)
    cv.line((0.5, 0.06), (0.5, 0.30), 0.06, LIGHT)
    cv.poly([(0.40, 0.20), (0.60, 0.20), (0.50, 0.32)], LIGHT)


def g_uv_cylinder(cv, c):
    _checker_mask(cv, (cv.x > 0.22) & (cv.x < 0.78) & (cv.y > 0.20) & (cv.y < 0.82), c)
    cv.ellipse(0.5, 0.20, 0.28, 0.08, shade(c, 0.3))
    cv.ellipse(0.5, 0.82, 0.28, 0.08, c)


def g_uv_sphere(cv, c):
    _checker_mask(cv, (cv.x - 0.5) ** 2 + (cv.y - 0.5) ** 2 <= 0.38 ** 2, c)


def g_uv_auto(cv, c):
    _checker_mask(cv, (cv.x > 0.14) & (cv.x < 0.62) & (cv.y > 0.38) & (cv.y < 0.86), c)
    cv.poly([(0.14, 0.38), (0.38, 0.14), (0.86, 0.14), (0.62, 0.38)], shade(c, 0.3))
    cv.poly([(0.62, 0.38), (0.86, 0.14), (0.86, 0.62), (0.62, 0.86)], shade(c, -0.3))


def g_uv_contour(cv, c):
    _checker_mask(cv, (cv.x > 0.12) & (cv.x < 0.88) & (cv.y > 0.12) & (cv.y < 0.88)
                  & ((cv.y - 0.5) ** 2 * 1.6 + (cv.x - 0.5) ** 2 * 0.4 <= 0.16), c)
    cv.polyline([(0.12, 0.30), (0.5, 0.18), (0.88, 0.30)], 0.05, LIGHT)
    cv.polyline([(0.12, 0.70), (0.5, 0.82), (0.88, 0.70)], 0.05, LIGHT)


def g_uv_grab(cv, c):
    _checker_mask(cv, (cv.x > 0.10) & (cv.x < 0.66) & (cv.y > 0.34) & (cv.y < 0.90), c)
    cv.circle(0.70, 0.30, 0.20, LIGHT)
    cv.circle(0.70, 0.30, 0.10, c)


def g_ambient(cv, c):
    cv.circle(0.5, 0.5, 0.30, c)
    cv.ring(0.5, 0.5, 0.36, 0.44, shade(c, 0.35))


def g_directional(cv, c):
    for y in (0.24, 0.50, 0.76):
        cv.line((0.10, y - 0.10), (0.70, y + 0.10), 0.07, c)
        cv.poly([(0.66, y + 0.18), (0.86, y + 0.16), (0.74, y + 0.01)], c)


def g_spot(cv, c):
    cv.poly([(0.40, 0.10), (0.60, 0.10), (0.92, 0.86), (0.08, 0.86)], c)
    cv.ellipse(0.5, 0.86, 0.42, 0.08, shade(c, 0.35))


def g_area(cv, c):
    cv.poly([(0.10, 0.34), (0.66, 0.20), (0.90, 0.66), (0.34, 0.80)], c)
    cv.line((0.50, 0.50), (0.62, 0.92), 0.05, LIGHT)


def g_volume_light(cv, c):
    cv.circle(0.5, 0.5, 0.40, shade(c, -0.35))
    cv.circle(0.5, 0.5, 0.16, c)


def badge(cv, text):
    """A small light tag at the lower right (step 113): tells apart buttons that still share a picture."""
    text = text[:2]
    cell = 0.042
    w = len(text) * 6 * cell + cell
    x0, y0 = 0.98 - w, 0.98 - 9 * cell
    cv.rect(x0, y0, 0.98, 0.98, DARK, 0.85)
    x = x0 + cell
    for ch in text:
        for k, bit in enumerate(FONT.get(ch.upper(), "")):
            if bit == "#":
                r, col = divmod(k, 5)
                cv.rect(x + col * cell, y0 + cell + r * cell, x + (col + 1) * cell, y0 + cell + (r + 1) * cell, LIGHT)
        x += 6 * cell


# Keyword -> glyph, first match wins (on the lower-case label).
GLYPHS = (
    (("reduce",), g_reduce), (("remesh",), g_remesh), (("retopolog",), g_retopo),
    (("merge to center",), g_merge_center), (("collapse",), g_collapse), (("target weld",), g_target_weld),
    (("planar mapping",), g_uv_planar), (("cylindrical mapping",), g_uv_cylinder),
    (("spherical mapping",), g_uv_sphere), (("automatic mapping",), g_uv_auto), (("contour stretch",), g_uv_contour),
    (("grab uv",), g_uv_grab),
    (("ambient light",), g_ambient), (("directional light",), g_directional), (("spot light",), g_spot),
    (("area light",), g_area), (("volume light",), g_volume_light),
    (("set key",), g_key), (("driven key",), g_key), (("material", "shading map", "background"), None),
    (("svg",), lambda cv, c: cv.text("SV", c)), (("sweep",), g_cylinder),
    (("editor", "browser", "base meshes", "uv editor"), g_window),
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
    (("render", "batch", "playblast"), g_clapper), (("type",), g_type),
    (("fluid",), g_fluid), (("emitter", "emit", "particle", "collide"), g_particles), (("hair", "follicle", "dynamic"), g_hair),
    (("cloth", "passive", "input mesh", "current mesh"), g_cloth), (("cache", "initial state", "position"), g_cache),
    (("motion trail", "bake", "sequence"), g_film), (("interactive playback",), g_play),
    (("revolve", "planar", "isoparm", "surface"), g_plane),
    (("sculpt", "tool", "grab", "pinch", "flatten", "foamy", "spray", "repeat", "imprint", "wax", "scrape",
      "fill", "smear", "bulge", "amplify", "paint"), g_brush),
)

# Maya's material buttons are shader balls in grey (same grabs); the ramp is the colourful one, Use Background /
# Surface Material light grey.
MATERIAL_COLOURS = {
    "lambert": (0.42, 0.42, 0.42), "blinn": (0.50, 0.50, 0.50), "phong": (0.46, 0.46, 0.46),
    "anisotropic": (0.36, 0.38, 0.55), "standard": (0.52, 0.52, 0.52), "layered": (0.44, 0.44, 0.44),
    "ramp": (0.85, 0.40, 0.25), "surface": (0.75, 0.75, 0.75), "shading map": (0.30, 0.30, 0.30),
    "background": (0.75, 0.75, 0.75),
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


_STOP = {"on", "to", "the", "with", "from", "and", "of", "a", "tool", "create", "new"}
_badges = {}


def badge_text(label, shelf):
    """Two letters for a button whose picture another button of the same shelf also uses: its first word that the
    others don't share (Parent / Point / Orient Constraint -> PA / PO / OR)."""
    if shelf is None:
        return ""
    if shelf not in _badges:
        from . import shelf_data
        buttons = next((b for name, _l, b in shelf_data.SHELVES if name == shelf), [])
        groups = {}
        for lab, _cmd in buttons:
            g = glyph_for(lab)
            if g is not None and not (shelf == "Sculpting" and lab.endswith(" Tool")):
                groups.setdefault(getattr(g, "__name__", "") + ("" if g.__name__ != "<lambda>" else lab), []).append(lab)
        tags = {}
        for labs in groups.values():
            if len(set(labs)) < 2:
                continue
            words = [[w for w in lab.replace("/", " ").replace("-", " ").lower().split() if w not in _STOP]
                     for lab in labs]
            for lab, ws in zip(labs, words):
                others = [o for o, l2 in zip(words, labs) if l2 != lab]
                pick = next((w for w in ws if all(w not in o for o in others)), ws[-1] if ws else "")
                tags[lab] = pick[:2].upper() if pick else ""
        _badges[shelf] = tags
    return _badges[shelf].get(label, "")


def draw(label, shelf=None, greyed=False):
    """32x32 RGBA (float, straight alpha) icon for a shelf button; ``greyed``: grey and faded."""
    colour = SHELF_COLOURS.get(shelf, USER_COLOUR)
    cv = Canvas()
    if shelf == "Sculpting" and label.endswith(" Tool"):
        glyph = lambda cv, c: g_sculpt(cv, c, label)   # noqa: E731 (one ball, its own mark)
    else:
        glyph = glyph_for(label)
    if glyph is None:
        cv.rect(0.08, 0.08, 0.92, 0.92, shade(colour, -0.35))
        cv.rect(0.12, 0.12, 0.88, 0.88, colour)
        cv.text(initials(label), DARK)
    else:
        glyph(cv, colour)
        tag = badge_text(label, shelf)
        if tag:
            badge(cv, tag)
    px = cv.result()
    if greyed:
        lum = px[..., :3] @ np.array([0.299, 0.587, 0.114], np.float32)
        px[..., :3] = (lum * 0.8)[..., None]
        px[..., 3] *= GREYED_ALPHA
    return px


# --- GPU textures -----------------------------------------------------------------------------

_textures = {}


def texture(label, shelf=None, greyed=False):
    """Cached GPU texture of a button's icon (needs a GPU context: call from a draw handler)."""
    key = (label, shelf, greyed)
    tex = _textures.get(key)
    if tex is None:
        import gpu
        px = draw(label, shelf, greyed)[::-1].copy()   # GPU rows go bottom-up
        # the palette is sRGB; the image editor draws in linear and converts for display
        rgb = px[..., :3]
        px[..., :3] = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
        buf = gpu.types.Buffer('FLOAT', SIZE * SIZE * 4, px.ravel().tolist())
        tex = _textures[key] = gpu.types.GPUTexture((SIZE, SIZE), format='RGBA32F', data=buf)
    return tex


def clear():
    _textures.clear()
