# SPDX-License-Identifier: GPL-3.0-or-later
"""UV Editor > Tools > Unfold, Optimize, Cut, Sew, Pin, Smear and Smudge as brush tools, like Maya.

Choosing one in the Tools menu makes it the UV Editor's active tool (ui/uv_brush_tools.py); an LMB drag applies it
under the brush, the brush circle follows the mouse, B + LMB drag left / right sets the brush size, M + LMB drag up /
down its strength, and Q / W / E / R leave it like any tool. One stroke = one undo step.

- Unfold / Optimize: the UVs under the brush relax against the 3D surface (operators/uv_brush_math.relax); UVs
  outside the brush and pinned UVs stay. Unfold flattens; Optimize keeps the Surface Angle balance.
- Cut: the edges the stroke runs along (within Edge Select Sensitivity of them) are cut on release; Ctrl+drag sews.
- Sew: the shell border edges under the brush are sewn on release (the smaller shell moves onto the other);
  Ctrl+drag cuts.
- Pin: the UVs under the brush are pinned; Ctrl+drag unpins them.
- Smear: the UVs under the brush are pushed along the stroke.
- Smudge: the selected UVs under the brush where the stroke starts follow it (fading out at the brush edge).
Settings live in ``Scene.allset_uv_brush``.
"""

import math

import bmesh
import bpy
import gpu
import numpy as np
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty
from gpu_extras.batch import batch_for_shader

from .. import live_refs, results
from . import taphold, uv_brush_math, uv_tools
from .uv_islands import sync
from .uv_shells import _loop_selected

PREFIX = "allset.uv_brush_"
MODES = ("UNFOLD", "OPTIMIZE", "CUT", "SEW", "PIN", "SMEAR", "SMUDGE")
TOOL_IDS = {m: PREFIX + m.lower() for m in MODES}
MODE_OF_TOOL = {v: k for k, v in TOOL_IDS.items()}
# mode -> (size property, strength property) in Scene.allset_uv_brush; Unfold and Optimize share one brush like Maya
BRUSH_PROPS = {"UNFOLD": ("relax_size", "relax_strength"), "OPTIMIZE": ("relax_size", "relax_strength"),
               "CUT": (None, None), "SEW": ("sew_size", None), "PIN": ("pin_size", "pin_strength"),
               "SMEAR": ("smear_size", "smear_strength"), "SMUDGE": ("smudge_size", "smudge_pressure")}
SPACING = 0.25            # a dab every quarter brush radius along the stroke
CIRCLE_RGB = (0.9, 0.9, 0.9)
CIRCLE_SEGMENTS = 48
STROKE_RGB = (1.0, 0.85, 0.1)       # the edges a Cut / Sew stroke collected (Maya draws the path yellow)


class ALLSET_PG_uv_brush(bpy.types.PropertyGroup):
    relax_size: FloatProperty(name="Size", default=0.1, min=0.0, max=100.0, soft_max=2.0, precision=3,
                              description="Brush radius in UV space (b + drag left / right)")
    relax_strength: FloatProperty(name="Strength", default=0.5, min=0.0, max=1.0, precision=3,
                                  description="How far the UVs move each dab (m + drag up / down)")
    surfangle: FloatProperty(name="Surface Angle", default=1.0, min=0.0, max=1.0, precision=3,
                             description="Optimize: keeping the surface area (1) against keeping only the angles (0)")
    cut_sensitivity: FloatProperty(name="Edge Select Sensitivity", default=0.2, min=0.1, max=0.5, precision=3,
                                   description="How near the stroke must pass an edge to cut it, as a part of the "
                                               "edge's length")
    sew_size: FloatProperty(name="Size", default=0.04, min=0.00001, max=1.0, precision=3,
                            description="Sew brush radius in UV space (b + drag left / right)")
    pin_size: FloatProperty(name="Size", default=0.1, min=0.0, max=10000.0, soft_max=1.0, precision=3,
                            description="Brush radius in UV space (b + drag left / right)")
    pin_strength: FloatProperty(name="Strength", default=100.0, min=0.0, max=100000.0, soft_max=100.0, precision=3,
                                description="Pin strength (m + drag up / down)")
    smear_size: FloatProperty(name="Size", default=0.1, min=0.0, max=10000.0, soft_max=1.0, precision=3,
                              description="Brush radius in UV space (b + drag left / right)")
    smear_strength: FloatProperty(name="Strength", default=0.05, min=0.0, max=100000.0, soft_max=100.0, precision=3,
                                  description="How strongly the UVs follow the stroke (m + drag up / down)")
    smudge_size: FloatProperty(name="Smudge size", default=0.1, min=0.0, max=10.0, soft_max=1.0, precision=3,
                               description="Brush radius in UV space (b + drag left / right)")
    smudge_pressure: FloatProperty(name="Pressure", default=0.5, min=0.0, max=1.0, precision=3,
                                   description="Smudge effect: how strongly the UVs follow the stroke")
    smudge_effect: EnumProperty(name="Effect type", default='FIXED', items=(
        ('FIXED', "Fixed", "The UVs under the brush where the stroke starts follow it"),
        ('SMUDGE', "Smudge", "The UVs the brush passes over are pushed along with the pressure")))
    show_ring: BoolProperty(name="Show brush ring during stroke", default=True)
    lattice_columns: IntProperty(name="Columns", default=4, min=2, max=20,
                                 description="Lattice points across the selected UVs")
    lattice_rows: IntProperty(name="Rows", default=4, min=2, max=20, description="Lattice points up the selected UVs")


def settings(context):
    return context.scene.allset_uv_brush


def size_of(context, mode):
    prop = BRUSH_PROPS[mode][0]
    return getattr(settings(context), prop) if prop else 0.0


def strength_of(context, mode):
    """The brush strength as a 0-1 factor of one dab."""
    s = settings(context)
    if mode in {"UNFOLD", "OPTIMIZE"}:
        return s.relax_strength
    if mode == "SMEAR":
        return min(1.0, s.smear_strength * 10.0)       # the default 0.05 pushes the UVs half the stroke
    if mode == "SMUDGE":
        return s.smudge_pressure
    return 1.0


# --- the UV Editor's active tool -----------------------------------------------------------------------

def active_tool(context):
    try:
        tool = context.workspace.tools.from_space_image_mode('UV', create=False)
    except (AttributeError, TypeError, RuntimeError):
        return ""
    return tool.idname if tool is not None else ""


def active_mode(context):
    return MODE_OF_TOOL.get(active_tool(context))


def _uv_region(context):
    space = getattr(context, "space_data", None)
    region = context.region
    return (context.mode == 'EDIT_MESH' and space is not None and space.type == 'IMAGE_EDITOR'
            and space.mode == 'UV' and region is not None and region.type == 'WINDOW')


# --- one mesh's UVs as numpy arrays for a stroke ------------------------------------------------------

class MeshUVs:
    """The UV points (one per vertex and UV coordinate) of the faces the UV Editor shows, for one stroke."""

    def __init__(self, ob, synced):
        self.ob = ob
        self.bm = bm = bmesh.from_edit_mesh(ob.data)
        self.uv = uv = bm.loops.layers.uv.verify()
        bm.verts.index_update()
        bm.edges.index_update()
        self.faces = faces = [f for f in bm.faces if not f.hide and (synced or f.select)]
        keys, loops, U, P, pins, sel = {}, [], [], [], [], []
        mw = ob.matrix_world
        point_of = {}
        for f in faces:
            for l in f.loops:
                c = l[uv].uv
                k = (l.vert.index, round(c.x, 6), round(c.y, 6))
                i = keys.get(k)
                if i is None:
                    i = keys[k] = len(loops)
                    loops.append([])
                    U.append((c.x, c.y))
                    P.append(tuple(mw @ l.vert.co))
                    pins.append(False)
                    sel.append(False)
                loops[i].append(l)
                pins[i] = pins[i] or l[uv].pin_uv
                sel[i] = sel[i] or _loop_selected(l, uv, synced)
                point_of[l] = i
        self.loops = loops
        self.U = np.array(U, float).reshape(-1, 2)
        self.U0 = self.U.copy()
        self.P = np.array(P, float).reshape(-1, 3)
        self.pinned = np.array(pins, bool)
        self.selected = np.array(sel, bool)
        self.point_of = point_of
        shown = set(faces)
        tris = [[point_of[l] for l in tri] for tri in bm.calc_loop_triangles() if tri[0].face in shown]
        self.T = np.array(tris, int).reshape(-1, 3)
        self._edges = None

    def edges(self):
        """(a, b, edge index, kind) per UV edge: ``a`` / ``b`` the point indices; kind 0 = inside a shell, 1 = a shell
        border between two faces (listed once per side), 2 = an open edge (one face)."""
        if self._edges is None:
            seen = {}
            for f in self.faces:
                for l in f.loops:
                    a, b = self.point_of[l], self.point_of[l.link_loop_next]
                    seen.setdefault((min(a, b), max(a, b), l.edge.index), 0)
                    seen[(min(a, b), max(a, b), l.edge.index)] += 1
            per_edge = {}
            for (a, b, e), _n in seen.items():
                per_edge.setdefault(e, []).append((a, b))
            rows = []
            for e, pairs in per_edge.items():
                kind = 1 if len(pairs) > 1 else 2 if seen[(*pairs[0], e)] == 1 else 0
                for a, b in pairs:
                    rows.append((a, b, e, kind))
            self._edges = rows
        return self._edges

    def edge_arrays(self):
        """``edges()`` as numpy columns (a, b, edge, kind)."""
        if getattr(self, "_edge_arrays", None) is None:
            rows = self.edges()
            self._edge_arrays = {k: np.array([r[c] for r in rows], int).reshape(-1)
                                 for c, k in enumerate(("a", "b", "edge", "kind"))}
        return self._edge_arrays

    def segments(self, picked):
        """The UV segments of the ``picked`` edge indices (the stroke drawing)."""
        arr = self.edge_arrays()
        if not picked or not len(arr["edge"]):
            return []
        on = np.isin(arr["edge"], np.fromiter(picked, int))
        return [(tuple(self.U[a]), tuple(self.U[b])) for a, b in zip(arr["a"][on], arr["b"][on])]

    def write(self, U):
        """Set the UVs that changed; returns whether any did."""
        moved = np.nonzero(np.any(np.abs(U - self.U) > 1e-12, axis=1))[0]
        uv = self.uv
        for i in moved:
            u, v = float(U[i, 0]), float(U[i, 1])
            for l in self.loops[i]:
                l[uv].uv = (u, v)
        self.U = np.array(U, float)
        return len(moved) > 0

    def write_pins(self, pins):
        changed = np.nonzero(pins != self.pinned)[0]
        uv = self.uv
        for i in changed:
            for l in self.loops[i]:
                l[uv].pin_uv = bool(pins[i])
        self.pinned = np.array(pins, bool)
        return len(changed) > 0

    def restore(self):
        self.write(self.U0)


def stroke_meshes(context):
    synced = sync(context)
    return [MeshUVs(ob, synced) for ob in context.objects_in_mode_unique_data or () if ob.type == 'MESH']


def apply_dab(mode, mesh, centre, r, strength, *, invert=False, delta=(0.0, 0.0), surfangle=1.0, weights=None):
    """One dab of ``mode`` on ``mesh`` (a MeshUVs) at UV ``centre`` with radius ``r``; returns whether anything
    changed. Cut / Sew only collect edges (``collect_edges``)."""
    if mode == "PIN":
        return mesh.write_pins(uv_brush_math.pin(mesh.pinned, mesh.U, centre, r, on=not invert))
    if mode in {"UNFOLD", "OPTIMIZE"}:
        return mesh.write(uv_brush_math.relax(mesh.P, mesh.U, mesh.T, centre, r, strength, mode, surfangle,
                                              held=mesh.pinned))
    if mode == "SMEAR":
        return mesh.write(uv_brush_math.smear(mesh.U, centre, r, delta, strength, held=mesh.pinned))
    if mode == "SMUDGE" and weights is not None:
        return mesh.write(mesh.U + weights[:, None] * np.asarray(delta, float)[None, :])
    return False


def collect_edges(mode, mesh, p, r, sensitivity, picked):
    """Cut / Sew stroke point ``p``: adds the edge indices it takes to the set ``picked``."""
    rows = mesh.edges()
    if not rows:
        return
    arr = mesh.edge_arrays()
    a, b = mesh.U[arr["a"]], mesh.U[arr["b"]]
    if mode == "CUT":
        hit = uv_brush_math.cut_pick(p, a, b, sensitivity) & (arr["kind"] == 0)    # a border is already cut
    else:
        hit = uv_brush_math.sew_pick(p, a, b, r) & (arr["kind"] == 1)    # only borders between two shells sew
    picked.update(int(e) for e in arr["edge"][hit])


def finish_edges(mode, mesh, picked):
    """Cut / sew the collected edges of ``mesh``; returns how many changed."""
    if not picked:
        return 0
    bm = mesh.bm
    bm.edges.ensure_lookup_table()
    edges = [bm.edges[i] for i in sorted(picked) if i < len(bm.edges)]
    if mode == "CUT":
        uv_tools.cut(bm, mesh.uv, edges)
        return len(edges)
    return uv_tools.sew(bm, mesh.uv, edges, move=True)


# --- drawing: the brush circle and the Cut / Sew stroke ------------------------------------------------

_hover = {"area": 0, "pos": None, "lock": False}
_recent = []          # the brush modes used, the latest last (the brush marking menu's Last Tool)
_stroke = {"area": 0, "segments": []}       # UV segments of the edges a Cut / Sew stroke collected
_handle = []


def _circle(cx, cy, rad):
    return [(cx + rad * math.cos(2 * math.pi * k / CIRCLE_SEGMENTS),
             cy + rad * math.sin(2 * math.pi * k / CIRCLE_SEGMENTS)) for k in range(CIRCLE_SEGMENTS)]


def _draw():
    context = bpy.context
    area, region = context.area, context.region
    try:
        if area is None or not _uv_region(context):
            return
        mode = active_mode(context)
        if mode is None:
            return
        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("viewportSize", (region.width, region.height))
        scale = context.preferences.system.ui_scale or 1.0
        gpu.state.blend_set('ALPHA')
        v2d = region.view2d
        if _stroke["area"] == area.as_pointer() and _stroke["segments"]:
            pts = [v2d.view_to_region(u, v, clip=False) for seg in _stroke["segments"] for (u, v) in seg]
            shader.uniform_float("lineWidth", 3.0 * scale)
            shader.uniform_float("color", (*STROKE_RGB, 1.0))
            batch_for_shader(shader, 'LINES', {"pos": pts}).draw(shader)
        pos = _hover["pos"]
        r = size_of(context, mode)
        if pos is not None and _hover["area"] == area.as_pointer() and r > 0:
            u, v = v2d.region_to_view(*pos)
            x1 = v2d.view_to_region(u + r, v, clip=False)[0]
            rad = abs(x1 - pos[0])
            shader.uniform_float("lineWidth", 1.5 * scale)
            shader.uniform_float("color", (*CIRCLE_RGB, 0.9))
            batch_for_shader(shader, 'LINE_LOOP', {"pos": _circle(pos[0], pos[1], rad)}).draw(shader)
        gpu.state.blend_set('NONE')
    except (ReferenceError, AttributeError):
        pass


def _redraw(context):
    if context.area is not None:
        context.area.tag_redraw()


# --- operators ---------------------------------------------------------------------------------------

class ALLSET_OT_uv_brush_hover(bpy.types.Operator):
    """The brush circle follows the mouse (UV Editor brush tools)"""
    bl_idname = "allset.uv_brush_hover"
    bl_label = "UV Brush Hover"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        if not _hover["lock"] and context.area is not None:
            _hover["area"] = context.area.as_pointer()
            _hover["pos"] = (event.mouse_region_x, event.mouse_region_y)
            context.area.tag_redraw()
        return {'PASS_THROUGH'}


class ALLSET_OT_uv_brush_stroke(bpy.types.Operator):
    """Drag to apply the UV brush under the circle (Maya UV Editor brush tools)"""
    bl_idname = "allset.uv_brush_stroke"
    bl_label = "UV Brush Stroke"
    bl_options = {'UNDO', 'INTERNAL'}

    mode: EnumProperty(name="Mode", items=[(m, m.title(), "") for m in MODES], options={'SKIP_SAVE'})
    invert: BoolProperty(name="Invert", default=False, options={'SKIP_SAVE'},
                         description="Ctrl: Pin unpins, Cut sews, Sew cuts")

    @classmethod
    def poll(cls, context):
        return _uv_region(context)

    def _mode(self):
        if self.invert and self.mode in {"CUT", "SEW"}:
            return "SEW" if self.mode == "CUT" else "CUT"
        return self.mode

    def invoke(self, context, event):
        self._meshes = stroke_meshes(context)
        if not self._meshes:
            return {'CANCELLED'}
        if self.mode in _recent:
            _recent.remove(self.mode)
        _recent.append(self.mode)
        self._area = context.area.as_pointer()
        self._xy = (event.mouse_region_x, event.mouse_region_y)
        self._uv = context.region.view2d.region_to_view(*self._xy)
        self._start = self._uv
        self._picked = [set() for _ in self._meshes]
        self._changed = False
        mode = self._mode()
        s = settings(context)
        if mode == "SMUDGE":
            r = s.smudge_size
            self._weights = [uv_brush_math.grab_weights(m.U, self._uv, r, held=m.pinned,
                                                        only=m.selected if m.selected.any() else None)
                             * (1.0 if s.smudge_effect == 'FIXED' else 0.0) for m in self._meshes]
        else:
            self._weights = None
        self._dab(context, self._uv, (0.0, 0.0))
        self._show()
        _hover["area"], _hover["pos"] = self._area, self._xy
        context.window_manager.modal_handler_add(self)
        _redraw(context)
        return {'RUNNING_MODAL'}

    def _dab(self, context, p, delta):
        mode = self._mode()
        s = settings(context)
        r = size_of(context, mode)
        k = strength_of(context, mode)
        for i, m in enumerate(self._meshes):
            if mode in {"CUT", "SEW"}:
                collect_edges(mode, m, p, r, s.cut_sensitivity, self._picked[i])
            elif mode == "SMUDGE" and s.smudge_effect == 'SMUDGE':
                self._changed |= m.write(uv_brush_math.smear(m.U, p, r, delta, k, held=m.pinned))
            else:
                w = None if self._weights is None else self._weights[i]
                self._changed |= apply_dab(mode, m, p, r, k, invert=self.invert, delta=delta,
                                           surfangle=s.surfangle, weights=w)

    def _show(self):
        """After the dabs of one mouse move: the collected Cut / Sew edges, or the moved UVs, on screen."""
        if self._mode() in {"CUT", "SEW"}:
            _stroke["area"] = self._area
            _stroke["segments"] = [seg for m, p in zip(self._meshes, self._picked) for seg in m.segments(p)]
        elif self._changed:
            for m in self._meshes:
                bmesh.update_edit_mesh(m.ob.data, loop_triangles=False, destructive=False)

    def modal(self, context, event):
        if event.type == 'ESC' and event.value == 'PRESS':
            for m in self._meshes:
                m.restore()
                bmesh.update_edit_mesh(m.ob.data, loop_triangles=False, destructive=False)
            _stroke["segments"] = []
            _redraw(context)
            return {'CANCELLED'}
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            region = context.region
            xy = (event.mouse_x - region.x, event.mouse_y - region.y) if region is not None else self._xy
            uv = region.view2d.region_to_view(*xy) if region is not None else self._uv
            mode = self._mode()
            r = size_of(context, mode)
            step = max(r * SPACING, 1e-4) if mode != "CUT" else 0.005
            prev = self._uv
            if mode == "SMUDGE" and settings(context).smudge_effect == 'FIXED':
                self._dab(context, uv, (uv[0] - prev[0], uv[1] - prev[1]))
            else:
                last = prev
                for p in uv_brush_math.stroke_points(prev, uv, step):
                    self._dab(context, p, (p[0] - last[0], p[1] - last[1]))
                    last = p
            self._show()
            self._uv, self._xy = uv, xy
            _hover["area"], _hover["pos"] = self._area, xy
            _redraw(context)
            return {'RUNNING_MODAL'}
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            return self._finish(context)
        return {'RUNNING_MODAL'}

    def _finish(self, context):
        mode = self._mode()
        _stroke["segments"] = []
        done = 0
        if mode in {"CUT", "SEW"}:
            for m, picked in zip(self._meshes, self._picked):
                n = finish_edges(mode, m, picked)
                done += n
                if n:
                    bmesh.update_edit_mesh(m.ob.data)
            if not done and mode == "SEW" and any(self._picked):
                results.result(self, "No UV shells to sew along these edges")
        else:
            done = self._changed
            for m in self._meshes:
                bmesh.update_edit_mesh(m.ob.data)
        _redraw(context)
        return {'FINISHED'} if done else {'CANCELLED'}


class ALLSET_OT_uv_invert_pin(bpy.types.Operator):
    """Pin the unpinned UVs and unpin the pinned ones (Maya Invert Pin)"""
    bl_idname = "allset.uv_invert_pin"
    bl_label = "Invert Pin"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        for m in stroke_meshes(context):
            m.write_pins(~m.pinned)
            bmesh.update_edit_mesh(m.ob.data)
        return {'FINISHED'}


def last_mode(context):
    """The brush used before the active one (or the latest one when no brush is active)."""
    current = active_mode(context)
    for m in reversed(_recent):
        if m != current:
            return m
    return None


class ALLSET_OT_uv_brush_last(bpy.types.Operator):
    """Go back to the UV brush tool used before this one (Maya's Last Tool in the brush marking menu)"""
    bl_idname = "allset.uv_brush_last"
    bl_label = "Last Tool"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        mode = last_mode(context)
        if mode is None:
            self.report({'INFO'}, "No other UV brush tool used yet")
            return {'CANCELLED'}
        bpy.ops.wm.tool_set_by_id(name=TOOL_IDS[mode], space_type='IMAGE_EDITOR')
        return {'FINISHED'}


# --- B / M + drag: brush size and strength -----------------------------------------------------------

def _header(context, text):
    area = live_refs.area(_hover["area"]) if _hover["area"] else None
    if area is not None:
        area.header_text_set(text)
        area.tag_redraw()


class _BrushDrag(taphold.TapHoldBinding):
    prop_index = 0

    def _prop(self, context):
        mode = active_mode(context)
        return None if mode is None else BRUSH_PROPS[mode][self.prop_index]

    def click(self, context, event):
        self._name = self._prop(context)
        if self._name is None:
            return None
        s = settings(context)
        self._start = getattr(s, self._name)
        _hover["lock"] = True
        self._show(context)
        return 'DRAG'

    def drag_end(self, context):
        _hover["lock"] = False
        _header(context, None)

    def drag_cancel(self, context):
        setattr(settings(context), self._name, self._start)
        self.drag_end(context)

    def _show(self, context):
        s = settings(context)
        label = s.bl_rna.properties[self._name].name
        _header(context, f"{label}: {getattr(s, self._name):.3f}  (Esc cancel)")


class UVBrushSizeBinding(_BrushDrag):
    """B + LMB drag left / right: the UV brush size (Maya)."""
    name = "uv_brush_size"
    label = "UV Brush Size"
    prop_index = 0

    def drag(self, context, event, start):
        s = settings(context)
        hard = s.bl_rna.properties[self._name].hard_max
        setattr(s, self._name, min(hard, taphold.radius_from_drag(max(self._start, 1e-3), event.mouse_x - start[0])))
        self._show(context)


class UVBrushStrengthBinding(_BrushDrag):
    """M + LMB drag up / down: the UV brush strength (Maya)."""
    name = "uv_brush_strength"
    label = "UV Brush Strength"
    prop_index = 1

    def drag(self, context, event, start):
        s = settings(context)
        p = s.bl_rna.properties[self._name]
        span = p.soft_max - p.soft_min
        value = self._start + (event.mouse_y - start[1]) / 200.0 * span
        setattr(s, self._name, min(p.hard_max, max(p.hard_min, value)))
        self._show(context)


BINDINGS = (UVBrushSizeBinding, UVBrushStrengthBinding)
classes = (ALLSET_PG_uv_brush, ALLSET_OT_uv_brush_hover, ALLSET_OT_uv_brush_stroke, ALLSET_OT_uv_invert_pin,
           ALLSET_OT_uv_brush_last)


def register_extra():
    bpy.types.Scene.allset_uv_brush = PointerProperty(type=ALLSET_PG_uv_brush)
    for cls in BINDINGS:
        taphold.register_binding(cls())
    if not _handle:
        _handle.append(bpy.types.SpaceImageEditor.draw_handler_add(_draw, (), 'WINDOW', 'POST_PIXEL'))


def unregister_extra():
    while _handle:
        bpy.types.SpaceImageEditor.draw_handler_remove(_handle.pop(), 'WINDOW')
    for cls in BINDINGS:
        taphold.unregister_binding(cls.name)
    if hasattr(bpy.types.Scene, "allset_uv_brush"):
        del bpy.types.Scene.allset_uv_brush
    _hover.update(area=0, pos=None, lock=False)
    _stroke["segments"] = []
    _recent.clear()
