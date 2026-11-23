# SPDX-License-Identifier: GPL-3.0-or-later
"""The UV Editor brush tools (Tools > Unfold, Optimize, Cut, Sew, Pin, Smear, Smudge), the maths (numpy, no bpy).

Everything works on "UV points": the UVs of a mesh as the UV Editor shows them (one point per vertex and UV
coordinate). ``U`` (n, 2) = their UVs, ``P`` (n, 3) = their 3D points, ``T`` (m, 3) = triangles over point indices.
The brush has a centre and a radius in UV space; a UV feels it with the falloff weight (1 at the centre, 0 at the
rim and outside), so a stroke fades out smoothly at the brush edge, like Maya's brushes.
"""

import math

import numpy as np

from . import uv_optimize_math

RELAX_STEPS = {"UNFOLD": 3, "OPTIMIZE": 1}      # local / global steps per dab: Unfold flattens harder than Optimize


def falloff(d, r):
    """Unfold / Optimize brush weight at distance ``d`` from the centre for radius ``r``: 1 at the centre, a smooth
    curve to 0 at the rim, 0 outside."""
    d = np.asarray(d, float)
    if r <= 0:
        return np.zeros_like(d)
    t = np.clip(d / r, 0.0, 1.0)
    return 1.0 - t * t * (3.0 - 2.0 * t)


def sculpt_falloff(d, r):
    """Smear brush weight: nearly flat over the inner half of the brush, then down to 0 at the rim, like Maya's
    sculpt brushes ((1 - t^3)^3 for t = distance / radius)."""
    d = np.asarray(d, float)
    if r <= 0:
        return np.zeros_like(d)
    t = np.clip(d / r, 0.0, 1.0)
    return (1.0 - t ** 3) ** 3


EXP_K = 5.0      # Smudge Exponential falloff: exp(-5 t^2), shifted to reach 0 at the rim


def smudge_falloff(d, r, kind="EXPONENTIAL"):
    """Smudge brush weight (Falloff type): Exponential = steep, the UV at the centre follows fully and one at two
    thirds of the radius about a tenth; Linear = straight down to the rim; Constant = 1 inside the brush."""
    d = np.asarray(d, float)
    if r <= 0:
        return np.zeros_like(d)
    t = np.clip(d / r, 0.0, 1.0)
    if kind == "LINEAR":
        return 1.0 - t
    if kind == "CONSTANT":
        return (d <= r).astype(float)
    floor = np.exp(-EXP_K)
    return (np.exp(-EXP_K * t * t) - floor) / (1.0 - floor)


def distances(U, centre):
    U = np.asarray(U, float)
    return np.hypot(U[:, 0] - centre[0], U[:, 1] - centre[1])


def in_brush(U, centre, r):
    """(n,) bool: the UVs inside the brush circle (the rim included)."""
    return distances(U, centre) <= r


def pin(pinned, U, centre, r, on=True):
    """Pin (``on``) or unpin the UVs inside the brush: returns the new (n,) pin flags."""
    out = np.array(pinned, bool)
    out[in_brush(U, centre, r)] = bool(on)
    return out


def smear(U, centre, r, delta, strength, held=None):
    """Smear: the UVs under the brush move along the stroke (``delta`` = how far the brush moved), each by its sculpt
    falloff weight times ``strength`` (no upper limit: above 1 the UVs run ahead of the brush, like Maya); ``held``
    UVs (pinned) stay. Returns the new UVs."""
    U = np.array(U, float)
    w = sculpt_falloff(distances(U, centre), r) * max(0.0, float(strength))
    if held is not None:
        w[np.asarray(held, bool)] = 0.0
    U += w[:, None] * np.asarray(delta, float)[None, :]
    return U


def grab_weights(U, centre, r, held=None, only=None, kind="EXPONENTIAL"):
    """Smudge (Fixed): the weight each UV follows the brush with, taken once where the stroke starts. ``only`` (n,)
    bool limits it to those UVs (the selection)."""
    w = smudge_falloff(distances(U, centre), r, kind)
    if held is not None:
        w[np.asarray(held, bool)] = 0.0
    if only is not None:
        w[~np.asarray(only, bool)] = 0.0
    return w


def smudge(U, centre, r, delta, pressure, held=None, only=None, kind="EXPONENTIAL"):
    """Smudge (Smudge effect), one mouse move: the ``only`` UVs (the selection) under the brush move along the move
    ``delta`` by their falloff weight times ``pressure``. Returns the new UVs."""
    U = np.array(U, float)
    w = grab_weights(U, centre, r, held, only, kind) * max(0.0, float(pressure))
    U += w[:, None] * np.asarray(delta, float)[None, :]
    return U


def relax(P, U, T, centre, r, strength, mode="OPTIMIZE", surfangle=1.0, held=None):
    """Unfold / Optimize brush dab: the UVs under the brush relax against the 3D surface (the Optimize solver, every
    UV outside the brush and every ``held`` UV fixed), each moving by its falloff weight times ``strength`` (0-1) of
    the way. Unfold flattens the surface (surface angle 1, more steps); Optimize uses ``surfangle``. Only the triangles
    under the brush are solved, so a dab costs the same on a small and on a big mesh. Returns the new UVs."""
    U = np.array(U, float)
    T = np.asarray(T, int)
    if not len(T):
        return U
    w = falloff(distances(U, centre), r) * float(np.clip(strength, 0.0, 1.0))
    free = w > 1e-6
    if held is not None:
        free &= ~np.asarray(held, bool)
    if not free.any():
        return U
    tri = free[T].any(axis=1)
    sub_t = T[tri]
    idx = np.unique(sub_t.ravel())
    local = -np.ones(len(U), int)
    local[idx] = np.arange(len(idx))
    sa = 1.0 if mode == "UNFOLD" else float(surfangle)
    new = uv_optimize_math.optimize(np.asarray(P, float)[idx], U[idx], local[sub_t], ~free[idx], iterations=1,
                                    surfangle=sa, prevent_flips=True, steps=RELAX_STEPS.get(mode, 1))
    k = w[idx][:, None]
    k[~free[idx]] = 0.0
    U[idx] = U[idx] + (new - U[idx]) * k
    return U


def segment_distance(p, a, b):
    """Distances from point ``p`` to the segments ``a`` - ``b`` ((k, 2) each) and where along each segment (0-1)."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    ab = b - a
    ll = np.einsum("ij,ij->i", ab, ab)
    t = np.where(ll > 1e-30, np.einsum("ij,ij->i", np.asarray(p, float)[None, :] - a, ab) / np.maximum(ll, 1e-30), 0.0)
    t = np.clip(t, 0.0, 1.0)
    q = a + ab * t[:, None]
    return np.hypot(q[:, 0] - p[0], q[:, 1] - p[1]), t


CUT_STEP = 0.002          # the Cut stroke is followed in steps this long (UV units)
CUT_WINDOW = 0.02         # the stroke direction at a point = the chord over this much of the stroke around it
CUT_MIN_STROKE = 0.12     # a Cut stroke this long or shorter cuts nothing
CUT_REACH = 0.1           # how far from the stroke edges are looked at
CUT_PARALLEL = math.cos(math.radians(45.0))      # an edge follows the stroke when it is within 45 degrees of it


class CutStroke:
    """A Cut stroke: its points every CUT_STEP along the drag, each with the stroke direction there."""

    def __init__(self, start):
        self.points = [np.asarray(start, float)]
        self.last = self.points[0]
        self.length = 0.0
        self._carry = 0.0
        self.taken = 0

    def add(self, p):
        p = np.asarray(p, float)
        seg = p - self.last
        ln = float(np.hypot(*seg))
        if ln <= 0.0:
            return
        k = CUT_STEP - self._carry
        while k <= ln + 1e-15:
            self.points.append(self.last + seg * (k / ln))
            k += CUT_STEP
        self._carry = ln - (k - CUT_STEP)
        self.length += ln
        self.last = p

    def take(self, final=False):
        """The points not handed out yet whose direction is known (all of them when ``final``): (S, D) arrays."""
        P = np.array(self.points)
        n = len(P)
        h = max(1, int(round(CUT_WINDOW * 0.5 / CUT_STEP)))
        end = n if final else max(self.taken, n - h)
        if end <= self.taken or n < 2:
            return np.zeros((0, 2)), np.zeros((0, 2))
        idx = np.arange(self.taken, end)
        D = P[np.minimum(idx + h, n - 1)] - P[np.maximum(idx - h, 0)]
        self.taken = end
        return P[idx], D


class CutPick:
    """The edges ``a`` - ``b`` ((k, 2) UV segments) a Cut stroke takes. Each stroke point snaps to the nearest edge
    that runs along the stroke (within 45 degrees), however far it is; an edge is taken when the stroke points
    snapped to it cover enough of it: the part left uncovered is at most the Edge Select Sensitivity. A stroke no
    longer than CUT_MIN_STROKE takes nothing."""

    def __init__(self, a, b):
        self.a = np.asarray(a, float).reshape(-1, 2)
        self.b = np.asarray(b, float).reshape(-1, 2)
        ab = self.b - self.a
        self.ln = np.hypot(ab[:, 0], ab[:, 1])
        self.dir = ab / np.maximum(self.ln, 1e-30)[:, None]
        self.lo = np.minimum(self.a, self.b)
        self.hi = np.maximum(self.a, self.b)
        self.tmin = np.full(len(self.a), np.inf)
        self.tmax = np.full(len(self.a), -np.inf)

    def update(self, S, D):
        """Snap the stroke points ``S`` (directions ``D``) to their edges."""
        if not len(S) or not len(self.a):
            return
        lo, hi = S.min(axis=0) - CUT_REACH, S.max(axis=0) + CUT_REACH
        near = np.nonzero((self.hi[:, 0] >= lo[0]) & (self.lo[:, 0] <= hi[0]) & (self.hi[:, 1] >= lo[1])
                          & (self.lo[:, 1] <= hi[1]) & (self.ln > 1e-12))[0]
        if not len(near):
            return
        a, ab, ln = self.a[near], self.b[near] - self.a[near], self.ln[near]
        dn = D / np.maximum(np.hypot(D[:, 0], D[:, 1]), 1e-30)[:, None]
        along = np.abs(dn @ self.dir[near].T) >= CUT_PARALLEL - 1e-9                    # (points, edges)
        rel = S[:, None, :] - a[None, :, :]
        t = np.clip(np.einsum("sej,ej->se", rel, ab) / (ln * ln)[None, :], 0.0, 1.0)
        q = a[None, :, :] + ab[None, :, :] * t[:, :, None]
        dist = np.hypot(q[..., 0] - S[:, None, 0], q[..., 1] - S[:, None, 1])
        dist = np.where(along, dist, np.inf)
        j = np.argmin(dist, axis=1)
        rows = np.arange(len(S))
        ok = np.isfinite(dist[rows, j])
        if not ok.any():
            return
        edge = near[j[ok]]
        tt = t[rows[ok], j[ok]]
        np.minimum.at(self.tmin, edge, tt)
        np.maximum.at(self.tmax, edge, tt)

    def picked(self, sensitivity, length):
        """(k,) bool: the edges taken by a stroke of ``length``."""
        if length <= CUT_MIN_STROKE + 1e-9:
            return np.zeros(len(self.a), bool)
        return (self.tmax - self.tmin) >= 1.0 - float(sensitivity) - 1e-9


def sew_pick(p, a, b, r):
    """Sew brush: (k,) bool, the border edges ``a`` - ``b`` (UV segments) the brush of radius ``r`` at ``p`` touches."""
    d, _t = segment_distance(p, a, b)
    return d <= r


def stroke_points(a, b, step):
    """Points from ``a`` (exclusive) to ``b`` (inclusive) at most ``step`` apart."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    n = max(1, int(np.hypot(*(b - a)) // max(step, 1e-12)) + 1)
    return [tuple(a + (b - a) * k / n) for k in range(1, n + 1)]


def spaced_points(a, b, step, carry):
    """Dab points on the move ``a`` - ``b``, ``step`` apart along the whole stroke: ``carry`` = how far the stroke
    went since the last dab. Returns (points, the new carry); a move shorter than what is left of a step gives none."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    ln = float(np.hypot(*(b - a)))
    step = max(step, 1e-12)
    pts = []
    k = step - carry
    while k <= ln + 1e-15:
        pts.append(tuple(a + (b - a) * (k / ln)))
        k += step
    return pts, (carry + ln) if not pts else ln - (k - step)
