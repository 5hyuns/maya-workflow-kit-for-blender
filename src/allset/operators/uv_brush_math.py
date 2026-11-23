# SPDX-License-Identifier: GPL-3.0-or-later
"""The UV Editor brush tools (Tools > Unfold, Optimize, Cut, Sew, Pin, Smear, Smudge), the maths (numpy, no bpy).

Everything works on "UV points": the UVs of a mesh as the UV Editor shows them (one point per vertex and UV
coordinate). ``U`` (n, 2) = their UVs, ``P`` (n, 3) = their 3D points, ``T`` (m, 3) = triangles over point indices.
The brush has a centre and a radius in UV space; a UV feels it with the falloff weight (1 at the centre, 0 at the
rim and outside), so a stroke fades out smoothly at the brush edge, like Maya's brushes.
"""

import numpy as np

from . import uv_optimize_math

RELAX_STEPS = {"UNFOLD": 3, "OPTIMIZE": 1}      # local / global steps per dab: Unfold flattens harder than Optimize


def falloff(d, r):
    """Brush weight at distance ``d`` from the centre for radius ``r``: 1 at the centre, a smooth curve to 0 at the
    rim, 0 outside."""
    d = np.asarray(d, float)
    if r <= 0:
        return np.zeros_like(d)
    t = np.clip(d / r, 0.0, 1.0)
    return 1.0 - t * t * (3.0 - 2.0 * t)


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
    """Smear: the UVs under the brush move along the stroke (``delta`` = how far the brush moved), each by its falloff
    weight times ``strength`` (0-1); ``held`` UVs (pinned) stay. Returns the new UVs."""
    U = np.array(U, float)
    w = falloff(distances(U, centre), r) * float(np.clip(strength, 0.0, 1.0))
    if held is not None:
        w[np.asarray(held, bool)] = 0.0
    U += w[:, None] * np.asarray(delta, float)[None, :]
    return U


def grab_weights(U, centre, r, held=None, only=None):
    """Smudge (Fixed): the weight each UV follows the brush with, taken once where the stroke starts. ``only`` (n,)
    bool limits it to those UVs (the selection)."""
    w = falloff(distances(U, centre), r)
    if held is not None:
        w[np.asarray(held, bool)] = 0.0
    if only is not None:
        w[~np.asarray(only, bool)] = 0.0
    return w


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


END_FRACTION = 0.15      # a cut stroke this near an edge end (a fraction of its length) doesn't take the edge: at a
                         # corner the side edges are as near as the next edge of the path


def cut_pick(p, a, b, sensitivity):
    """Cut brush: (k,) bool, the edges ``a`` - ``b`` (UV segments) the stroke point ``p`` takes. An edge is taken when
    the point is within ``sensitivity`` (Edge Select Sensitivity, a fraction of the edge's length) of it and not at
    one of its ends."""
    d, t = segment_distance(p, a, b)
    ln = np.hypot(*(np.asarray(b, float) - np.asarray(a, float)).T)
    return (d <= sensitivity * ln) & (t > END_FRACTION) & (t < 1.0 - END_FRACTION)


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
