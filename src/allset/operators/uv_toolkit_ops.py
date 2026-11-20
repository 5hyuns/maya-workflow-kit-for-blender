# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya UV Toolkit commands the UV Editor menus don't have as such.

- Align Min / Avg / Max U / V: the selected UVs go to the left / centre / right (bottom / centre / top) of their
  bounding box; with the UV Shell mask whole shells move, each shell's box to the box of all selected shells.
- Straighten UVs: selected UV edges within the angle tolerance of the U (V) axis are lined up, each connected run
  of them on the centre of its bounding box.
- Unfold Along U / V: the shells are relaxed along one axis only; the other coordinate of every UV stays.
- Straighten Shell: the selected UV edge loop becomes a straight line along U or V (its UV length kept, its UVs spaced
  like their mesh edges) and the rest of its shell is unfolded around it (Blender Unwrap, Angle Based, with the line
  pinned), so a ribbon shell becomes a straight strip. Like Maya, a line that crosses a ribbon of two or more faces
  moves the strip's width only part of the way from what it was (``limited_width``).
- Randomize Shells: every selected shell is moved, turned and scaled by a random amount in the given ranges.

All of them work on every mesh in edit mode at once, like Maya works on the whole selection.
"""

import math
import random

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty
from mathutils import Vector

from .. import compat, i18n, results, undo_steps
from . import uv_tools
from .uv_modify import all_points, selected_ids
from .uv_shells import _index_loops, _meshes, _poll, owner_map

AXES = (('U', "U", ""), ('V', "V", ""))
STRAIGHTEN_TOLERANCE = 30.0          # degrees
RANDOM_TRANSLATE = 0.1               # UV units
RANDOM_ROTATE = 22.5                 # degrees
RANDOM_SCALE = 10.0                  # percent


def _shell_mode(context):
    """The UV Shell mask (or Blender's UV island selection) is on: commands move whole shells."""
    from . import uv_shell_select
    ts = context.scene.tool_settings
    return uv_shell_select.active(context) or (not ts.use_uv_select_sync and compat.uv_island_mode(ts))


def _picked_islands(context, bm, uv):
    return uv_tools.target_islands(bm, uv, uv_tools.sync(context), fallback=False)


def _island_box(island, uv):
    return uv_tools.uv_bounds(island, uv)


def _loops(island):
    return [l for f in island for l in f.loops]


# --- Align Min / Avg / Max ----------------------------------------------------------------------------------

@undo_steps.no_redo_panel
class ALLSET_OT_uv_align_to(bpy.types.Operator):
    """Line the selected UVs up on the left, centre or right (bottom, centre or top) of their bounding box; with the
    UV Shell mask whole shells move (Maya UV Toolkit Align)"""
    bl_idname = "allset.uv_align_to"
    bl_label = "Align UVs"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(items=AXES, default='U', options={'SKIP_SAVE'})
    where: EnumProperty(items=(('MIN', "Min", ""), ('AVG', "Avg", ""), ('MAX', "Max", "")), default='MIN',
                        options={'SKIP_SAVE'})

    poll = classmethod(lambda cls, context: _poll(context))

    def execute(self, context):
        synced = uv_tools.sync(context)
        shells = _shell_mode(context)
        k = 0 if self.axis == 'U' else 1
        found = []          # (object, bmesh, uv, items)
        for ob in _meshes(context):
            bm = bmesh.from_edit_mesh(ob.data)
            uv = bm.loops.layers.uv.verify()
            _index_loops(bm)
            if shells:
                items = _picked_islands(context, bm, uv)
            else:
                pts, _where = all_points(bm, uv)
                items = [pts[i] for i in selected_ids(bm, uv, synced, pts)]
            if items:
                found.append((ob, bm, uv, items))
        if not found:
            self.report({'WARNING'}, "Select UVs to align")
            return {'CANCELLED'}
        # one bounding box over every mesh
        if shells:
            boxes = [_island_box(isl, uv) for _o, _b, uv, items in found for isl in items]
            lo, hi = min(b[0][k] for b in boxes), max(b[1][k] for b in boxes)
        else:
            vals = [g[0][uv].uv[k] for _o, _b, uv, items in found for g in items]
            lo, hi = min(vals), max(vals)
        for ob, bm, uv, items in found:
            if shells:
                for isl in items:
                    blo, bhi = _island_box(isl, uv)
                    d = {'MIN': lo - blo[k], 'MAX': hi - bhi[k]}.get(
                        self.where, 0.5 * (lo + hi) - 0.5 * (blo[k] + bhi[k]))
                    for l in _loops(isl):
                        l[uv].uv[k] += d
            else:
                target = {'MIN': lo, 'MAX': hi}.get(self.where, 0.5 * (lo + hi))
                for g in items:
                    for l in g:
                        l[uv].uv[k] = target
            bmesh.update_edit_mesh(ob.data)
        return {'FINISHED'}


# --- Straighten UVs -------------------------------------------------------------------------------------------

def _angle(a, b):
    """Angle of the UV edge a-b against the U axis, -90 .. 90 degrees, taken from its left end."""
    left, right = (a, b) if a.x <= b.x else (b, a)
    du, dv = right.x - left.x, right.y - left.y
    if du <= 0.0:
        return 90.0 if dv else 0.0
    return math.degrees(math.atan2(dv, du))


def _runs(pairs):
    """Connected runs of UV edges (pairs of UV ids) — the UV ids of each run."""
    link = {}
    for a, b in pairs:
        link.setdefault(a, set()).add(b)
        link.setdefault(b, set()).add(a)
    seen, out = set(), []
    for start in link:
        if start in seen:
            continue
        run, stack = [], [start]
        seen.add(start)
        while stack:
            i = stack.pop()
            run.append(i)
            for j in link[i]:
                if j not in seen:
                    seen.add(j)
                    stack.append(j)
        out.append(run)
    return out


def straighten_points(bm, uv, pts, where, chosen, axis='UV', tolerance=STRAIGHTEN_TOLERANCE):
    """Line up the UV edges between ``chosen`` UVs that lie within ``tolerance`` degrees of the U (V) axis: every
    connected run of them goes onto the centre of its bounding box. Returns the number of runs moved."""
    chosen = set(chosen)
    pairs = set()
    for f in bm.faces:
        if f.hide:
            continue
        for l in f.loops:
            a, b = where.get(l), where.get(l.link_loop_next)
            if a is None or b is None or a == b or a not in chosen or b not in chosen:
                continue
            pairs.add((min(a, b), max(a, b)))
    along_u, along_v = [], []
    for a, b in sorted(pairs):
        ang = abs(_angle(pts[a][0][uv].uv, pts[b][0][uv].uv))
        if ang <= tolerance:
            along_u.append((a, b))
        elif ang >= 90.0 - tolerance:
            along_v.append((a, b))
    moved = 0
    for runs_axis, edges, k in (('U', along_u, 1), ('V', along_v, 0)):
        if axis not in ('UV', runs_axis):
            continue
        for run in _runs(edges):
            vals = [pts[i][0][uv].uv[k] for i in run]
            c = 0.5 * (min(vals) + max(vals))
            for i in run:
                for l in pts[i]:
                    l[uv].uv[k] = c
            moved += 1
    return moved


@undo_steps.no_redo_panel
class ALLSET_OT_uv_straighten_uvs(bpy.types.Operator):
    """Line up the selected UV edges that run nearly along U or V (within the angle tolerance): each connected run
    becomes straight (Maya Straighten UVs)"""
    bl_idname = "allset.uv_straighten_uvs"
    bl_label = "Straighten UVs"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(items=(('UV', "UV", ""), *AXES), default='UV', options={'SKIP_SAVE'})
    tolerance: FloatProperty(name="Angle Tolerance", default=STRAIGHTEN_TOLERANCE, min=0.0, max=90.0,
                             options={'SKIP_SAVE'})

    poll = classmethod(lambda cls, context: _poll(context))

    def execute(self, context):
        synced = uv_tools.sync(context)
        moved = 0
        for ob in _meshes(context):
            bm = bmesh.from_edit_mesh(ob.data)
            uv = bm.loops.layers.uv.verify()
            _index_loops(bm)
            pts, where = all_points(bm, uv)
            n = straighten_points(bm, uv, pts, where, selected_ids(bm, uv, synced, pts), self.axis, self.tolerance)
            if n:
                moved += n
                bmesh.update_edit_mesh(ob.data)
        if not moved:
            self.report({'WARNING'}, "Select UV edges that run nearly along U or V")
            return {'CANCELLED'}
        return {'FINISHED'}


# --- Unfold Along U / V ---------------------------------------------------------------------------------------

ALONG_ITERATIONS = 200


def unfold_along(bm, uv, island, axis, iterations=ALONG_ITERATIONS):
    """Relax one shell along ``axis`` only: each mesh edge wants its UV length to be its 3D length times the shell's
    UV-per-3D scale; the other coordinate of every UV stays, and so does the shell's mean on ``axis``."""
    k = 0 if axis == 'U' else 1
    o = 1 - k
    pts, where = {}, {}
    for f in island:
        for l in f.loops:
            p = l[uv].uv
            key = (l.vert.index, round(p.x, 6), round(p.y, 6))
            where[l] = pts.setdefault(key, len(pts))
    n = len(pts)
    if n < 2:
        return False
    pos = [[0.0, 0.0] for _ in range(n)]
    for l, i in where.items():
        pos[i] = [l[uv].uv.x, l[uv].uv.y]
    edges = {}
    for f in island:
        for l in f.loops:
            a, b = where[l], where[l.link_loop_next]
            if a != b:
                edges[(min(a, b), max(a, b))] = (l.vert.co - l.link_loop_next.vert.co).length
    uva = sum(abs(uv_tools._uv_area(f, uv)) for f in island)
    wa = sum(f.calc_area() for f in island)
    if wa <= 1e-12 or uva <= 1e-12 or not edges:
        return False
    s = math.sqrt(uva / wa)
    mean0 = sum(p[k] for p in pos) / n
    nbrs = [[] for _ in range(n)]
    for (a, b), length in edges.items():
        want = s * length
        dv = pos[a][o] - pos[b][o]
        du = math.sqrt(max(want * want - dv * dv, 0.0))
        sign = 1.0 if pos[a][k] >= pos[b][k] else -1.0
        nbrs[a].append((b, sign * du))
        nbrs[b].append((a, -sign * du))
    x = [p[k] for p in pos]
    for _ in range(iterations):
        x = [sum(x[j] + d for j, d in nb) / len(nb) if nb else x[i] for i, nb in enumerate(nbrs)]
    shift = mean0 - sum(x) / n
    for l, i in where.items():
        l[uv].uv[k] = x[i] + shift
    return True


@undo_steps.no_redo_panel
class ALLSET_OT_uv_unfold_along(bpy.types.Operator):
    """Unfold the selected UV shells (all when none are selected) along U or V only: the other coordinate of every
    UV stays (Maya UV Toolkit Unfold Along U / V)"""
    bl_idname = "allset.uv_unfold_along"
    bl_label = "Unfold Along"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(items=AXES, default='U', options={'SKIP_SAVE'})

    poll = classmethod(lambda cls, context: _poll(context))

    def execute(self, context):
        fallback = not uv_tools.picked_anywhere(context)
        done = 0
        for ob in _meshes(context):
            bm = bmesh.from_edit_mesh(ob.data)
            uv = bm.loops.layers.uv.verify()
            bm.verts.index_update()
            got = sum(unfold_along(bm, uv, isl, self.axis)
                      for isl in uv_tools.target_islands(bm, uv, uv_tools.sync(context), fallback))
            if got:
                done += got
                bmesh.update_edit_mesh(ob.data)
        if not done:
            return {'CANCELLED'}
        results.result(self, uv_tools.NOTICE_UNFOLD)
        return {'FINISHED'}


# --- Straighten Shell -------------------------------------------------------------------------------------------

FEW_UVS = i18n.mark("At least two UVs must be selected to perform this operation")
NOT_A_LOOP = i18n.mark("Select one edge loop (a line of UV edges) on the shell to straighten")


def uv_chain(ids, island, where):
    """The UVs ``ids`` of one shell in order along the UV edges between them, from the lower UV index; None when they
    are not one open line (a branch, a closed loop, or apart)."""
    link = {i: set() for i in ids}
    for f in island:
        for l in f.loops:
            a, b = where[l], where[l.link_loop_next]
            if a != b and a in link and b in link:
                link[a].add(b)
                link[b].add(a)
    ends = [i for i, nb in link.items() if len(nb) == 1]
    if len(ends) != 2 or any(len(nb) > 2 for nb in link.values()):
        return None
    order, prev = [min(ends)], None
    while True:
        nxt = [j for j in link[order[-1]] if j != prev]
        if not nxt:
            break
        prev = order[-1]
        order.append(nxt[0])
    return order if len(order) == len(link) else None


def straight_line(points, uv):
    """Where the UVs ``points`` (a line, in order) go: on a line along the nearer of U and V to the direction from the
    first to the last, through the middle of those two, as long as the UV line was, each UV as far along as its mesh
    edges are."""
    p = [pt[0][uv].uv.copy() for pt in points]
    steps = [(points[k + 1][0].vert.co - points[k][0].vert.co).length for k in range(len(points) - 1)]
    total = sum(steps)
    if total <= 1e-12:
        return None
    length = sum((p[k + 1] - p[k]).length for k in range(len(p) - 1)) or total     # UVs on one spot: 3D length
    chord = p[-1] - p[0]
    if abs(chord.x) >= abs(chord.y):
        d = Vector((math.copysign(1.0, chord.x), 0.0))
    else:
        d = Vector((0.0, math.copysign(1.0, chord.y)))
    centre = (p[0] + p[-1]) / 2
    out, run = [], 0.0
    for k in range(len(p)):
        out.append(centre + d * (length * run / total - length / 2))
        if k < len(steps):
            run += steps[k]
    return out


def mark_uv_cuts(faces, uv):
    """Seams on the edges of ``faces`` whose UVs are cut apart inside one shell (a cylinder side cut along one edge
    line), so the unwrap keeps the cut open."""
    for f in faces:
        for l in f.loops:
            other = l.link_loop_radial_next
            if other is l or l.edge.seam:
                continue
            mine = {l.vert: l[uv].uv, l.link_loop_next.vert: l.link_loop_next[uv].uv}
            theirs = {other.vert: other[uv].uv, other.link_loop_next.vert: other.link_loop_next[uv].uv}
            if any((mine[v] - theirs[v]).length > 1e-6 for v in mine):
                l.edge.seam = True


def straighten_shells(context, ob, synced):
    """Maya Straighten Shell on ``ob``: in every shell whose selected UVs form one line, that line is straightened
    and pinned, the shell is unfolded around it (Blender Unwrap, Angle Based, the shell's border as seams) and the
    line's pins go back to what they were. Returns (selected UVs, shells straightened)."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    _index_loops(bm)
    bm.faces.index_update()
    pts, where = all_points(bm, uv)
    chosen = selected_ids(bm, uv, synced, pts)
    if not chosen:
        return 0, 0
    groups = uv_tools.islands(bm, uv, [f for f in bm.faces if not f.hide])
    owner = owner_map(groups)
    per = {}
    for i in chosen:
        per.setdefault(owner[pts[i][0].face], []).append(i)
    faces, old_pins, lines = [], {}, []
    for k, ids in per.items():
        order = uv_chain(ids, groups[k], where) if len(ids) > 1 else None
        targets = straight_line([pts[i] for i in order], uv) if order else None
        if targets is None:
            continue
        shell = set(groups[k])
        faces += groups[k]
        along_v = abs(targets[-1].x - targets[0].x) < abs(targets[-1].y - targets[0].y)
        lines.append(([f.index for f in groups[k]], signed_area(groups[k], uv), along_v,
                      targets[0].x if along_v else targets[0].y,
                      across_extent(groups[k], uv, [pts[i][0][uv].uv for i in order]), len(order) - 1,
                      (targets[-1] - targets[0]).length))
        for i, q in zip(order, targets):
            for l in pts[i]:
                if l.face in shell:
                    old_pins.setdefault(l, l[uv].pin_uv)
                    l[uv].uv = q
                    l[uv].pin_uv = True
    if not faces:
        return len(chosen), 0
    restore = [(f.index, n, old_pins[l]) for f in faces for n, l in enumerate(f.loops) if l in old_pins]
    shells = len({owner[f] for f in faces})
    uv_tools.mark_shell_borders(bm, uv, faces)
    mark_uv_cuts(faces, uv)
    bmesh.update_edit_mesh(ob.data)
    uv_tools._with_faces(context, ob, faces, lambda: bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.0))
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()
    for fi, n, pin in restore:
        bm.faces[fi].loops[n][uv].pin_uv = pin
    for ids, area, along_v, at, was, steps, length in lines:
        shell = [bm.faces[fi] for fi in ids]
        flip = -1.0 if area * signed_area(shell, uv) < 0 else 1.0     # the unwrap mirrored it: back over the line
        across = [l[uv].uv.x if along_v else l[uv].uv.y for f in shell for l in f.loops]
        now = max(across) - min(across)
        factor = flip * limited_width(was, now, steps, length) / now if now > 1e-12 else flip
        if factor != 1.0:
            for f in shell:
                for l in f.loops:
                    p = l[uv].uv
                    if along_v:
                        l[uv].uv = (at + (p.x - at) * factor, p.y)
                    else:
                        l[uv].uv = (p.x, at + (p.y - at) * factor)
    bmesh.update_edit_mesh(ob.data)
    return len(chosen), shells


# How far Straighten Shell moves a shell's width across the line from its old layout toward its 3D proportions when
# the line crosses the shell (it is shorter than the shell is wide): the share of the way for a line of two edges and
# for a longer line, and for the longer line a limit on widening (times line length squared over the old width).
SHARE_TWO_EDGES = 0.64
SHARE_MANY_EDGES = 0.185
WIDEN_LIMIT = 0.48


def across_extent(faces, uv, line):
    """How wide ``faces`` are in UV space across the line through the UVs ``line`` (first to last)."""
    d = line[-1] - line[0]
    if d.length <= 1e-12:
        return 0.0
    n = Vector((-d.y, d.x)) / d.length
    across = [l[uv].uv.dot(n) for f in faces for l in f.loops]
    return max(across) - min(across)


def limited_width(was, now, steps, length):
    """The width across the line Straighten Shell gives a shell that was ``was`` wide and unfolds to ``now`` (its 3D
    proportions), for a line of ``steps`` edges and UV length ``length``. Like Maya, the shell is unfolded from its
    own layout with a limited effort: when the line crosses the shell, a line of two or more edges moves the shell's
    width only part of the way; otherwise the shell gets its 3D proportions."""
    if steps < 2 or now <= length or was <= 1e-12:
        return now
    if steps == 2:
        return was + SHARE_TWO_EDGES * (now - was)
    return was + min(SHARE_MANY_EDGES * (now - was), WIDEN_LIMIT * length * length / was)


def signed_area(faces, uv):
    """The UV area of ``faces`` with its sign: negative when the faces are mirrored in UV space."""
    total = 0.0
    for f in faces:
        p = [l[uv].uv for l in f.loops]
        total += sum(p[i - 1].x * p[i].y - p[i].x * p[i - 1].y for i in range(len(p)))
    return total / 2


@undo_steps.no_redo_panel
class ALLSET_OT_uv_straighten_shell(bpy.types.Operator):
    """Straighten the selected UV edge loop along U or V and unfold the rest of its shell around it, so a ribbon
    shell becomes a straight strip (Maya Straighten Shell)"""
    bl_idname = "allset.uv_straighten_shell"
    bl_label = "Straighten Shell"
    bl_options = {'REGISTER', 'UNDO'}

    poll = classmethod(lambda cls, context: _poll(context))

    def execute(self, context):
        synced = uv_tools.sync(context)
        picked = done = 0
        for ob in _meshes(context):
            n, got = straighten_shells(context, ob, synced)
            picked += n
            done += got
        if picked < 2:
            self.report({'WARNING'}, i18n.tip(FEW_UVS))
            return {'CANCELLED'}
        if not done:
            self.report({'WARNING'}, i18n.tip(NOT_A_LOOP))
            return {'CANCELLED'}
        return {'FINISHED'}


# --- Randomize Shells -------------------------------------------------------------------------------------------

def randomize_shell(island, uv, rng, translate_u=True, translate_v=True, translate=RANDOM_TRANSLATE,
                    rotate_cw=False, rotate_ccw=False, rotate=RANDOM_ROTATE,
                    scale_up=False, scale_down=False, scale=RANDOM_SCALE):
    """Move / turn / scale one shell by random amounts in the ranges (Maya Randomize Shells); turn and scale
    about the shell's bounding-box centre."""
    loops = _loops(island)
    du = rng.uniform(-translate, translate) if translate_u else 0.0
    dv = rng.uniform(-translate, translate) if translate_v else 0.0
    if rotate_cw and rotate_ccw:
        ang = rng.uniform(-rotate, rotate)
    elif rotate_cw:
        ang = rng.uniform(-rotate, 0.0)
    elif rotate_ccw:
        ang = rng.uniform(0.0, rotate)
    else:
        ang = 0.0
    up, down = 1.0 + scale / 100.0, 1.0 - scale / 100.0
    if scale_up and scale_down:
        f = rng.uniform(down, up)
    elif scale_up:
        f = rng.uniform(1.0, up)
    elif scale_down:
        f = rng.uniform(down, 1.0)
    else:
        f = 1.0
    lo, hi = _island_box(island, uv)
    c = (lo + hi) * 0.5
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for l in loops:
        p = l[uv].uv - c
        p = Vector((ca * p.x - sa * p.y, sa * p.x + ca * p.y)) * f
        l[uv].uv = c + p + Vector((du, dv))


@undo_steps.no_redo_panel
class ALLSET_OT_uv_randomize(bpy.types.Operator):
    """Move, turn and scale each selected UV shell by a random amount (Maya Randomize Shells)"""
    bl_idname = "allset.uv_randomize"
    bl_label = "Randomize Shells"
    bl_options = {'REGISTER', 'UNDO'}

    translate_u: BoolProperty(name="U", default=True, options={'SKIP_SAVE'})
    translate_v: BoolProperty(name="V", default=True, options={'SKIP_SAVE'})
    translate: FloatProperty(name="Units", default=RANDOM_TRANSLATE, min=0.0, soft_max=1.0, options={'SKIP_SAVE'})
    rotate_cw: BoolProperty(name="Clockwise", default=False, options={'SKIP_SAVE'})
    rotate_ccw: BoolProperty(name="Counter-clockwise", default=False, options={'SKIP_SAVE'})
    rotate: FloatProperty(name="Degrees", default=RANDOM_ROTATE, min=0.0, max=180.0, options={'SKIP_SAVE'})
    scale_up: BoolProperty(name="Up", default=False, options={'SKIP_SAVE'})
    scale_down: BoolProperty(name="Down", default=False, options={'SKIP_SAVE'})
    scale: FloatProperty(name="Percent", default=RANDOM_SCALE, min=0.0, max=100.0, options={'SKIP_SAVE'})
    seed: IntProperty(name="Seed", default=0, min=0, options={'SKIP_SAVE'},
                      description="0 = a new random result every time")

    poll = classmethod(lambda cls, context: _poll(context))

    def execute(self, context):
        rng = random.Random(self.seed or None)
        done = 0
        for ob in _meshes(context):
            bm = bmesh.from_edit_mesh(ob.data)
            uv = bm.loops.layers.uv.verify()
            islands = _picked_islands(context, bm, uv)
            for isl in islands:
                randomize_shell(isl, uv, rng, self.translate_u, self.translate_v, self.translate, self.rotate_cw,
                                self.rotate_ccw, self.rotate, self.scale_up, self.scale_down, self.scale)
            if islands:
                done += len(islands)
                bmesh.update_edit_mesh(ob.data)
        if not done:
            self.report({'WARNING'}, "Select UVs or faces of the shells to randomize")
            return {'CANCELLED'}
        return {'FINISHED'}


# --- toolkit settings ------------------------------------------------------------------------------------------

class ALLSET_PG_uv_toolkit(bpy.types.PropertyGroup):
    straighten_tolerance: FloatProperty(name="Angle Tolerance", default=STRAIGHTEN_TOLERANCE, min=0.0, max=90.0,
                                        description="Straighten UVs: UV edges this close (degrees) to U or V are "
                                                    "lined up")
    straighten_u: BoolProperty(name="U", default=True, description="Straighten UVs: line up edges along U")
    straighten_v: BoolProperty(name="V", default=True, description="Straighten UVs: line up edges along V")


def straighten_axis(context):
    s = context.scene.allset_uv_toolkit
    return 'UV' if s.straighten_u == s.straighten_v else ('U' if s.straighten_u else 'V')


classes = (ALLSET_PG_uv_toolkit, ALLSET_OT_uv_align_to, ALLSET_OT_uv_straighten_uvs, ALLSET_OT_uv_unfold_along,
           ALLSET_OT_uv_straighten_shell, ALLSET_OT_uv_randomize)


def register_props():
    bpy.types.Scene.allset_uv_toolkit = bpy.props.PointerProperty(type=ALLSET_PG_uv_toolkit)


def unregister_props():
    del bpy.types.Scene.allset_uv_toolkit
