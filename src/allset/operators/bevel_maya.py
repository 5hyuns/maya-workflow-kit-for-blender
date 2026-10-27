# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya polyBevel3 (Edit Mesh > Bevel, Ctrl+B) at once, as an editable history node like step 65's extrusion
(#16,  「계획」; checked : -4).

- Factory values: Fraction 0.5, Offset As Fraction on, Offset 0.2, Segments 1, Depth 1 (Chamfer on, Mitering auto).
- Fraction is relative to one length for the whole selection: the shortest "slide" edge (an edge touching an end of a
  beveled edge), halved when both of its ends are used (two shells of different size get the same width). The width
  Maya applies is 0.9999 x that (both modes, checked).
- The profile is Blender's superellipse with ``profile = t^2``, t = 0.5 + Depth x (sqrt(1/2) - 1/2): Depth 1 = the
  round arc (0.5), 0 = straight, -1 = the arc mirrored over the chord (exact for 2 segments, checked).
- Zero-length slide edges don't count, and what the bevel makes is merged within 0.0001 (Merge Vertices): the
  cap of a zero-length extrusion bevels into an inset (12/20/10, cap at 0.25), Fraction 1 merges (6/9/5).
- Faces bevel their edges; Maya leaves nothing selected afterwards. Vertex mode = Chamfer Vertex (performBevelOrChamfer
  -> polyChamfer, 0.25 of each edge, no editable node here).
"""

import math

import bmesh

from . import extrude

MERGE = 1e-4          # polyBevel3 Merge Vertices on, tolerance 0.0001 (factory, checked)
ZERO = 1e-6           # zero-length slide edges (a zero-length extrusion) don't limit the fraction (checked,)
FIT = 0.9999          # Maya's bevel width = 0.9999 x the asked width (offset 0.1 -> 0.09999, fraction 0.5 -> 0.49995)
CHAMFER = 25.0        # Chamfer Vertex: 0.25 of each edge (unit cube and 4 x 1 x 2 box, checked)


def slide_limit(edges):
    """Maya's fraction base (a perpendicular width): min over slide edges of length x sin(angle to the beveled edge)
    / (number of their ends a bevel slides along).

    Another beveled edge is a slide only where it shares a face with this one (the cube's top loop: the corner slides
    inside the top face along it). Step 239 (#124, Maya audit230/maya/first_hour239.py): a cylinder cap's border ring
    has no face holding two ring edges, so Maya slides along the side / cap fan edges (length 1) — and the width is
    perpendicular, so the fan edges at 81 degrees to the ring give 0.49995 x sin 81 = 0.49379 (the side ring lands at
    y 1.5062, the cap ring at radius 0.5). The ring neighbours had given 0.078. Cube cases are all at 90 degrees."""
    sel = set(edges)
    used = {}
    for e in edges:
        faces = set(e.link_faces)
        d = (e.verts[1].co - e.verts[0].co).normalized()
        for v in e.verts:
            for s in v.link_edges:
                if s is e or (s in sel and not faces.intersection(s.link_faces)):
                    continue
                t = (s.other_vert(v).co - v.co)
                sin = t.normalized().cross(d).length if t.length > ZERO else 0.0
                key = s
                ent = used.setdefault(key, [set(), 1.0])
                ent[0].add(v)
                ent[1] = min(ent[1], sin)
    caps = [s.calc_length() * sin / len(ends) for s, (ends, sin) in used.items() if s.calc_length() > ZERO]
    if caps:
        return min(caps)
    return min((e.calc_length() for e in sel), default=0.0)


def profile(depth):
    t = 0.5 + max(-1.0, min(1.0, depth)) * (math.sqrt(0.5) - 0.5)
    return max(0.0, min(1.0, t * t))


def width(edges, fraction=0.5, offset_as_fraction=True, offset=0.2, unit=1.0):
    if offset_as_fraction:
        return max(0.0, min(1.0, fraction)) * slide_limit(edges) * FIT
    return max(0.0, offset) * unit * FIT


def bevel_edges(bm, edges, fraction=0.5, offset_as_fraction=True, offset=0.2, segments=1, depth=1.0, unit=1.0,
                **_unused):
    """polyBevel3 on ``edges`` (bmesh). Returns the vertices the bevel made (empty: nothing done)."""
    edges = [e for e in edges if e.is_valid]
    w = width(edges, fraction, offset_as_fraction, offset, unit)
    if not edges or w <= 0.0:
        return []
    verts = {v for e in edges for v in e.verts}
    ret = bmesh.ops.bevel(bm, geom=list(edges) + list(verts), offset=w, offset_type='OFFSET',
                          segments=max(1, int(segments)), profile=profile(depth), affect='EDGES',
                          clamp_overlap=False, loop_slide=True)
    made = [v for v in ret["verts"] if v.is_valid]
    near = set(made)
    for v in made:
        near.update(e.other_vert(v) for e in v.link_edges)
    # Maya merges what the bevel made onto coincident vertices (a zero-length extrusion's sides, Fraction 1), at
    # their midpoint (Fraction 1: 0.49995 between 0.5 and 0.4999, checked)
    pairs = bmesh.ops.find_doubles(bm, verts=list(near), dist=MERGE * 1.001)["targetmap"]
    for v, target in pairs.items():
        target.co = (v.co + target.co) / 2
    if pairs:
        bmesh.ops.weld_verts(bm, targetmap=pairs)
    extrude.deselect_all(bm)
    bm.select_flush_mode()
    bm.normal_update()
    return [v for v in near if v.is_valid]


def chamfer_vertices(bm, verts):
    """Maya Chamfer Vertex (Ctrl+B in vertex mode): a face where each vertex was, 0.25 of each edge in."""
    verts = [v for v in verts if v.is_valid]
    if not verts:
        return []
    ret = bmesh.ops.bevel(bm, geom=verts, offset=CHAMFER, offset_type='PERCENT', segments=1, profile=0.5,
                          affect='VERTICES', clamp_overlap=False)
    extrude.deselect_all(bm)      # Maya selects only the polyChamfer node (checked)
    bm.select_flush_mode()
    bm.normal_update()
    return list(ret["verts"])


def _build(bm, params, unit):
    return bevel_edges(bm, [e for e in bm.edges if e.select], unit=unit, **params)


BEVEL = extrude.add_spec(extrude.Spec(
    'BEVEL', "polyBevel", ("fraction", "offset_as_fraction", "offset", "segments", "depth"),
    {"fraction": "Fraction", "offset_as_fraction": "Offset As Fraction", "offset": "Offset", "segments": "Segments",
     "depth": "Depth"},
    {"fraction": 0.5, "offset_as_fraction": True, "offset": 0.2, "segments": 1, "depth": 1.0},
    {"fraction": "NONE", "offset_as_fraction": "BOOL", "offset": "NONE", "segments": "INT", "depth": "NONE"},
    None, "bevel_edit", _build, node_type="polyBevel3"))
