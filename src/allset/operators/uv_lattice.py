# SPDX-License-Identifier: GPL-3.0-or-later
"""UV Editor > Tools > Lattice, like Maya's Lattice UV Tool: a lattice of Columns x Rows points around the selected
UVs (all shown UVs when none is selected); LMB drag a lattice point to bend the UVs inside it. The lattice follows a
change of the selection or an undo: it is rebuilt around the UVs whenever they are not where it left them.

Settings: ``Scene.allset_uv_brush.lattice_columns`` / ``lattice_rows``.
"""

import time

import bmesh
import bpy
import gpu
import numpy as np
from gpu_extras.batch import batch_for_shader

from . import uv_brush

TOOL = "allset.uv_lattice"
PICK_PX = 10.0
CHECK_S = 0.3
LINE_RGB = (0.85, 0.35, 0.85)
POINT_RGB = (1.0, 1.0, 1.0)
HOT_RGB = (1.0, 0.85, 0.1)


# --- maths (numpy) -----------------------------------------------------------------------------------

def grid(rect, cols, rows):
    """(rows, cols, 2) lattice points evenly over ``rect`` = (u0, v0, u1, v1)."""
    u = np.linspace(rect[0], rect[2], cols)
    v = np.linspace(rect[1], rect[3], rows)
    return np.stack(np.meshgrid(u, v), axis=-1)


def params(U, rect):
    """Each UV's place in ``rect`` as (s, t) 0-1."""
    w = max(rect[2] - rect[0], 1e-12)
    h = max(rect[3] - rect[1], 1e-12)
    return np.stack(((U[:, 0] - rect[0]) / w, (U[:, 1] - rect[1]) / h), axis=1)


def deform(pts, st):
    """The UVs at lattice places ``st`` for the (rows, cols, 2) lattice points ``pts``: bilinear in each cell."""
    rows, cols = pts.shape[:2]
    s = np.clip(st[:, 0], 0.0, 1.0) * (cols - 1)
    t = np.clip(st[:, 1], 0.0, 1.0) * (rows - 1)
    i = np.minimum(s.astype(int), cols - 2)
    j = np.minimum(t.astype(int), rows - 2)
    fs = (s - i)[:, None]
    ft = (t - j)[:, None]
    p00, p10 = pts[j, i], pts[j, i + 1]
    p01, p11 = pts[j + 1, i], pts[j + 1, i + 1]
    return (p00 * (1 - fs) + p10 * fs) * (1 - ft) + (p01 * (1 - fs) + p11 * fs) * ft


def bounds(U):
    lo, hi = U.min(axis=0), U.max(axis=0)
    pad = np.maximum((hi - lo) * 1e-3, 1e-6)       # a lattice on one row / column of UVs still has an area
    lo, hi = lo - pad, hi + pad
    return (float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1]))


# --- the live lattice --------------------------------------------------------------------------------

_state = {"lattice": None, "hot": None}
_handle = []


class Lattice:
    """The lattice and the UVs it bends: per mesh the target UV point indices and their lattice places."""

    def __init__(self, meshes, cols, rows):
        self.targets = []
        allu = []
        for m in meshes:
            idx = np.nonzero(m.selected)[0] if m.selected.any() else np.arange(len(m.U))
            self.targets.append(idx)
            allu.append(m.U[idx])
        U = np.concatenate(allu) if allu else np.zeros((0, 2))
        self.ok = len(U) > 0
        self.rect = bounds(U) if self.ok else (0.0, 0.0, 1.0, 1.0)
        self.pts = grid(self.rect, cols, rows)
        self.shape = (rows, cols)
        self.st = [params(m.U[idx], self.rect) for m, idx in zip(meshes, self.targets)]
        self.names = [m.ob.name for m in meshes]
        self.last = [m.U[idx].copy() for m, idx in zip(meshes, self.targets)]

    def matches(self, meshes, cols, rows):
        """Whether the UVs are still where this lattice left them (no undo, no new selection, same size)."""
        if (rows, cols) != self.shape or [m.ob.name for m in meshes] != self.names:
            return False
        for m, idx, last in zip(meshes, self.targets, self.last):
            sel = np.nonzero(m.selected)[0] if m.selected.any() else np.arange(len(m.U))
            if len(sel) != len(idx) or not np.array_equal(sel, idx) or not np.allclose(m.U[idx], last, atol=1e-7):
                return False
        return True

    def apply(self, meshes):
        changed = False
        for k, (m, idx) in enumerate(zip(meshes, self.targets)):
            U = m.U.copy()
            U[idx] = deform(self.pts, self.st[k])
            changed |= m.write(U)
            self.last[k] = U[idx].copy()
        return changed


def lattice_for(context, meshes):
    s = uv_brush.settings(context)
    lat = _state["lattice"]
    if lat is None or not lat.matches(meshes, s.lattice_columns, s.lattice_rows):
        lat = _state["lattice"] = Lattice(meshes, s.lattice_columns, s.lattice_rows)
    return lat


def tool_active(context):
    return uv_brush.active_tool(context) == TOOL


def _pick(region, lat, xy):
    v2d = region.view2d
    best, bd = None, PICK_PX * PICK_PX
    rows, cols = lat.shape
    for j in range(rows):
        for i in range(cols):
            x, y = v2d.view_to_region(*lat.pts[j, i], clip=False)
            d = (x - xy[0]) ** 2 + (y - xy[1]) ** 2
            if d <= bd:
                best, bd = (j, i), d
    return best


def _draw():
    context = bpy.context
    try:
        lat = _state["lattice"]
        if lat is None or not lat.ok or not uv_brush._uv_region(context) or not tool_active(context):
            return
        region = context.region
        v2d = region.view2d
        rows, cols = lat.shape
        px = [[v2d.view_to_region(*lat.pts[j, i], clip=False) for i in range(cols)] for j in range(rows)]
        lines = []
        for j in range(rows):
            for i in range(cols - 1):
                lines += [px[j][i], px[j][i + 1]]
        for i in range(cols):
            for j in range(rows - 1):
                lines += [px[j][i], px[j + 1][i]]
        scale = context.preferences.system.ui_scale or 1.0
        gpu.state.blend_set('ALPHA')
        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("viewportSize", (region.width, region.height))
        shader.uniform_float("lineWidth", 1.5 * scale)
        shader.uniform_float("color", (*LINE_RGB, 1.0))
        batch_for_shader(shader, 'LINES', {"pos": lines}).draw(shader)
        pts = gpu.shader.from_builtin('POINT_UNIFORM_COLOR')     # sized on Vulkan / Metal too
        gpu.state.point_size_set(7.0 * scale)
        flat = [px[j][i] for j in range(rows) for i in range(cols)]
        pts.uniform_float("color", (*POINT_RGB, 1.0))
        batch_for_shader(pts, 'POINTS', {"pos": flat}).draw(pts)
        hot = _state["hot"]
        if hot is not None:
            pts.uniform_float("color", (*HOT_RGB, 1.0))
            batch_for_shader(pts, 'POINTS', {"pos": [px[hot[0]][hot[1]]]}).draw(pts)
        gpu.state.point_size_set(1.0)
        gpu.state.blend_set('NONE')
    except (ReferenceError, AttributeError, IndexError):
        pass


class ALLSET_OT_uv_lattice_hover(bpy.types.Operator):
    """Show the lattice around the UVs and the point under the mouse (Lattice UV Tool)"""
    bl_idname = "allset.uv_lattice_hover"
    bl_label = "UV Lattice Hover"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        if not uv_brush._uv_region(context):
            return {'PASS_THROUGH'}
        now = time.monotonic()
        if _state["lattice"] is None or now - _state.get("checked", 0.0) > CHECK_S:
            _state["checked"] = now            # a selection change / undo shows on the next look, not every move
            lattice_for(context, uv_brush.stroke_meshes(context))
        lat = _state["lattice"]
        hot = _pick(context.region, lat, (event.mouse_region_x, event.mouse_region_y)) if lat.ok else None
        if hot != _state["hot"]:
            _state["hot"] = hot
            context.area.tag_redraw()
        return {'PASS_THROUGH'}


class ALLSET_OT_uv_lattice_drag(bpy.types.Operator):
    """Drag a lattice point to bend the UVs inside the lattice (Maya Lattice UV Tool)"""
    bl_idname = "allset.uv_lattice_drag"
    bl_label = "Lattice UV Drag"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return uv_brush._uv_region(context)

    def invoke(self, context, event):
        self._meshes = uv_brush.stroke_meshes(context)
        lat = lattice_for(context, self._meshes)
        if not lat.ok:
            return {'CANCELLED'}
        xy = (event.mouse_region_x, event.mouse_region_y)
        self._point = _pick(context.region, lat, xy)
        if self._point is None:
            context.area.tag_redraw()
            return {'CANCELLED'}
        self._start = context.region.view2d.region_to_view(*xy)
        self._p0 = lat.pts[self._point].copy()
        self._pts0 = lat.pts.copy()
        _state["hot"] = self._point
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        lat = _state["lattice"]
        region = context.region
        if lat is None or region is None:
            return {'CANCELLED'}
        if event.type == 'ESC' and event.value == 'PRESS':
            lat.pts[:] = self._pts0
            lat.apply(self._meshes)
            for m in self._meshes:
                bmesh.update_edit_mesh(m.ob.data, loop_triangles=False, destructive=False)
            context.area.tag_redraw()
            return {'CANCELLED'}
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            uv = region.view2d.region_to_view(event.mouse_x - region.x, event.mouse_y - region.y)
            lat.pts[self._point] = self._p0 + np.array((uv[0] - self._start[0], uv[1] - self._start[1]))
            if lat.apply(self._meshes):
                for m in self._meshes:
                    bmesh.update_edit_mesh(m.ob.data, loop_triangles=False, destructive=False)
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            for m in self._meshes:
                bmesh.update_edit_mesh(m.ob.data)
            context.area.tag_redraw()
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


classes = (ALLSET_OT_uv_lattice_hover, ALLSET_OT_uv_lattice_drag)


def register_extra():
    if not _handle:
        _handle.append(bpy.types.SpaceImageEditor.draw_handler_add(_draw, (), 'WINDOW', 'POST_PIXEL'))


def unregister_extra():
    while _handle:
        bpy.types.SpaceImageEditor.draw_handler_remove(_handle.pop(), 'WINDOW')
    _state.update(lattice=None, hot=None)
