# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya's extrude manipulator, In-View Editor and the INPUTS rows of the last extrusion
.

- Visible while the active edit object's last kit extrusion is valid and its extruded faces are the selection
  (operators/extrude.py). Maya swaps the Move manipulator for the extrude one: the kit Move/Scale manipulator
  (ui/manipulator.py) hides meanwhile.
- The manipulator is a Python gizmo group (Blender's C transform gizmo can't be extended, :10): a blue
  arrow along the faces' normal whose drag (``allset.extrude_drag``) sets Local Translate Z.
- The In-View Editor box is drawn by a POST_PIXEL handler; 2D gizmos only pick its rows (the shelf's way, step 51).
  Dragging a row sideways changes the value, a click without a drag types it, Keep Faces Together toggles.
- Channel Box INPUTS: the node and five rows (WindowManager text proxies: a UI edit of a WM property pushes no
  undo step, the edit itself is one,  step 38) + the "only the last one" notice.
"""

import blf
import bmesh
import bpy
import gpu
from bpy.props import FloatProperty, IntProperty, PointerProperty, StringProperty
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector, geometry

from . import cb_entry
from ..operators import extrude, units

ROW_H = 16          # px at UI scale 1 (Maya In-View rows, modeling_03.png)
WIDTH = 180
GAP = (70, -6)      # box top-left from the manipulator centre on screen
FLOAT_STEP = 0.01   # Maya units per px of a sideways drag
DIV_PX = 20         # px per division
KINDS = {"thickness": "NONE", "local_translate_z": "NONE", "offset": "NONE", "divisions": "INT",
         "keep_faces_together": "BOOL"}
BG = (0.22, 0.22, 0.22, 0.92)
TITLE_BG = (0.30, 0.30, 0.30, 0.95)
TEXT = (0.86, 0.86, 0.86, 1.0)
HOT = (1.0, 1.0, 0.35, 1.0)        # Maya's highlighted attribute name (modeling_03.png)
ARROW_BLUE = (0.05, 0.25, 1.0)
YELLOW = (1.0, 1.0, 0.0)

_state = {"hot": 0, "handle": None}


def _scale():
    return bpy.context.preferences.system.ui_scale


# --- what is shown -----------------------------------------------------------------------------------

def record(context):
    """(object, record) when the manipulator / In-View Editor show in this 3D View, else (None, None)."""
    space = getattr(context, "space_data", None)
    if space is None or space.type != 'VIEW_3D':
        return None, None
    from .toolbox import is_toolbox
    if is_toolbox(space):
        return None, None
    ob, rec = extrude.active(context)
    if rec is None or not extrude.caps_selected(ob, rec):
        return None, None
    return ob, rec


def manip_visible(context):
    return record(context)[1] is not None


def cap_frame(ob, rec):
    """(world centre, world unit normal, world length of one local unit along it) of the extruded faces."""
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    verts = [bm.verts[i] for i in rec.cap_verts if i < len(bm.verts)]
    faces = [bm.faces[i] for i in rec.cap_faces if i < len(bm.faces)]
    if not verts:
        return None
    centre = sum((v.co for v in verts), Vector()) / len(verts)
    n = sum((f.normal for f in faces), Vector())
    n = n.normalized() if n.length > 1e-9 else Vector((0, 0, 1))
    mw = ob.matrix_world
    nw = mw.to_3x3() @ n
    k = nw.length or 1.0
    return mw @ centre, nw / k, k


def layout(region, anchor, scale):
    """Box geometry in region pixels: {"box", "title", "rows": [(field, x0, y0, x1, y1)]}."""
    w, h = WIDTH * scale, ROW_H * scale
    n = len(extrude.FIELDS) + 1
    x0 = anchor[0] + GAP[0] * scale
    top = anchor[1] + GAP[1] * scale
    x0 = max(4 * scale, min(x0, region.width - w - 4 * scale))
    top = max(n * h + 4 * scale, min(top, region.height - 4 * scale))
    rows = []
    for i, field in enumerate(extrude.FIELDS):
        y1 = top - (i + 1) * h
        rows.append((field, x0, y1 - h, x0 + w, y1))
    return {"box": (x0, top - n * h, x0 + w, top), "title": (x0, top - h, x0 + w, top), "rows": rows}


def anchor(context, ob, rec):
    frame = cap_frame(ob, rec)
    if frame is None:
        return None
    p = view3d_utils.location_3d_to_region_2d(context.region, context.region_data, frame[0])
    return (p.x, p.y) if p is not None else None


def current_layout(context):
    ob, rec = record(context)
    if rec is None or context.region is None or context.region.type != 'WINDOW' or context.region_data is None:
        return None, None
    a = anchor(context, ob, rec)
    if a is None:
        return None, None
    return rec, layout(context.region, a, _scale())


def value_text(rec, field):
    v = rec.params[field]
    if field == "keep_faces_together":
        return "On" if v else "Off"
    if field == "divisions":
        return str(int(v))
    return cb_entry.fmt_number(v)


# --- drawing -----------------------------------------------------------------------------------------

def _rect(x0, y0, x1, y1, colour):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]},
                             indices=[(0, 1, 2), (0, 2, 3)])
    shader.uniform_float("color", colour)
    batch.draw(shader)


def _text(x, y, s, colour, size):
    blf.size(0, size)
    blf.color(0, *colour)
    blf.position(0, x, y, 0)
    blf.draw(0, s)


def draw_box():
    """POST_PIXEL of 3D View WINDOW regions: the In-View Editor next to the extrude manipulator."""
    context = bpy.context
    rec, lay = current_layout(context)
    if rec is None:
        return
    s = _scale()
    size = 11 * s
    pad = 5 * s
    gpu.state.blend_set('ALPHA')
    _rect(*lay["box"], BG)
    _rect(*lay["title"], TITLE_BG)
    x0, y0, x1, y1 = lay["title"]
    blf.size(0, size)
    tw = blf.dimensions(0, rec.name)[0]
    _text((x0 + x1 - tw) / 2, y0 + 4 * s, rec.name, TEXT, size)
    for i, (field, rx0, ry0, rx1, ry1) in enumerate(lay["rows"]):
        _text(rx0 + pad, ry0 + 4 * s, extrude.LABELS[field], HOT if i == _state["hot"] else TEXT, size)
        v = value_text(rec, field)
        blf.size(0, size)
        _text(rx1 - pad - blf.dimensions(0, v)[0], ry0 + 4 * s, v, TEXT, size)
    gpu.state.blend_set('NONE')


# --- In-View picking (2D gizmos) -------------------------------------------------------------------

class ALLSET_GT_in_view_row(bpy.types.Gizmo):
    """Row ``row`` of the In-View Editor: picking only (drawn by ``draw_box``)."""
    bl_idname = "ALLSET_GT_in_view_row"
    __slots__ = ("row",)

    def setup(self):
        self.row = 0

    def draw(self, context):
        pass

    def test_select(self, context, location):
        _rec, lay = current_layout(context)
        if lay is None:
            return -1
        _f, x0, y0, x1, y1 = lay["rows"][self.row]
        if x0 <= location[0] <= x1 and y0 <= location[1] <= y1:
            if _state["hot"] != self.row:
                _state["hot"] = self.row
                context.region.tag_redraw()
            return 0
        return -1


class ALLSET_GGT_in_view(bpy.types.GizmoGroup):
    bl_idname = "ALLSET_GGT_in_view"
    bl_label = "Maya In-View Editor"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        return manip_visible(context)

    def setup(self, context):
        for i in range(len(extrude.FIELDS)):
            gz = self.gizmos.new(ALLSET_GT_in_view_row.bl_idname)
            gz.row = i
            gz.target_set_operator(ALLSET_OT_inview_drag.bl_idname).row = i


# --- the extrude manipulator (3D gizmo) -----------------------------------------------------------

def _arrow_matrix(frame):
    centre, n, _k = frame
    rot = Vector((0, 0, 1)).rotation_difference(n).to_matrix().to_4x4()
    return Matrix.Translation(centre) @ rot


class ALLSET_GGT_extrude(bpy.types.GizmoGroup):
    bl_idname = "ALLSET_GGT_extrude"
    bl_label = "Maya Extrude Manipulator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and space.type == 'VIEW_3D' and space.show_gizmo and manip_visible(context)

    def setup(self, context):
        gz = self.gizmos.new("GIZMO_GT_arrow_3d")
        gz.target_set_operator(ALLSET_OT_extrude_drag.bl_idname)
        gz.color = ARROW_BLUE
        gz.color_highlight = YELLOW
        gz.alpha = gz.alpha_highlight = 1.0
        gz.line_width = 2.0
        gz.use_draw_modal = True
        self.arrow = gz

    def draw_prepare(self, context):
        ob, rec = record(context)
        if rec is None:
            return
        frame = cap_frame(ob, rec)
        if frame is not None:
            self.arrow.matrix_basis = _arrow_matrix(frame)


# --- operators ---------------------------------------------------------------------------------------

def _redraw(context):
    for area in context.screen.areas if context.screen else ():
        if area.type == 'VIEW_3D':
            area.tag_redraw()


class ALLSET_OT_inview_drag(bpy.types.Operator):
    """In-View Editor: drag sideways to change the value (Ctrl: finer, Shift: coarser), click to type it"""
    bl_idname = "allset.inview_drag"
    bl_label = "In-View Editor"
    bl_options = {'INTERNAL'}

    row: IntProperty(options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return extrude.active(context)[1] is not None

    def invoke(self, context, event):
        ob, rec = extrude.active(context)
        field = extrude.FIELDS[self.row]
        _state["hot"] = self.row
        if field == "keep_faces_together":
            extrude.set_params(context, keep_faces_together=not rec.params[field])
            _redraw(context)
            return {'FINISHED'}
        self._ob, self._rec, self._field = ob, rec, field
        self._start = dict(rec.params)
        self._x0, self._moved = event.mouse_x, False
        self._button = event.type if event.type in {'LEFTMOUSE', 'MIDDLEMOUSE'} else 'LEFTMOUSE'
        self._unit = units.maya_unit(context.scene)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _value(self, event):
        s = _scale()
        dx = (event.mouse_x - self._x0) / s
        start = self._start[self._field]
        if self._field == "divisions":
            return max(1, int(start + round(dx / DIV_PX)))
        step = FLOAT_STEP * (0.1 if event.ctrl else 10.0 if event.shift else 1.0)
        return round(start + dx * step, 4)

    def modal(self, context, event):
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            if abs(event.mouse_x - self._x0) > 3 * _scale():
                self._moved = True
            if self._moved:
                params = dict(self._start, **{self._field: self._value(event)})
                extrude.preview(self._ob, self._rec, params, self._unit)
                _redraw(context)
            return {'RUNNING_MODAL'}
        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
            if self._moved:
                extrude.preview(self._ob, self._rec, self._start, self._unit)
                self._rec.live = False
            _redraw(context)
            return {'CANCELLED'}
        if event.type == self._button and event.value == 'RELEASE':
            if self._moved:
                extrude.set_params(context, **{self._field: self._value(event)})
            else:
                bpy.ops.allset.inview_type('INVOKE_DEFAULT', row=self.row)
            _redraw(context)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


class ALLSET_OT_inview_type(bpy.types.Operator):
    """Type a value of the last extrusion (In-View Editor)"""
    bl_idname = "allset.inview_type"
    bl_label = "In-View Editor"
    bl_options = {'INTERNAL'}

    row: IntProperty(options={'SKIP_SAVE'})
    number: FloatProperty(name="Value")
    count: IntProperty(name="Divisions", min=1)

    @classmethod
    def poll(cls, context):
        return extrude.active(context)[1] is not None

    def invoke(self, context, event):
        _ob, rec = extrude.active(context)
        field = extrude.FIELDS[self.row]
        if field == "divisions":
            self.count = int(rec.params[field])
        else:
            self.number = float(rec.params[field])
        return context.window_manager.invoke_props_dialog(self, title=f"{rec.name}: {extrude.LABELS[field]}")

    def draw(self, context):
        field = extrude.FIELDS[self.row]
        self.layout.prop(self, "count" if field == "divisions" else "number", text=extrude.LABELS[field])

    def execute(self, context):
        field = extrude.FIELDS[self.row]
        value = self.count if field == "divisions" else self.number
        res = extrude.set_params(context, **{field: value})
        _redraw(context)
        return res


class ALLSET_OT_extrude_drag(bpy.types.Operator):
    """Drag the extrude manipulator: Local Translate Z of the last extrusion (Maya polyExtrudeFace)"""
    bl_idname = "allset.extrude_drag"
    bl_label = "Extrude Manipulator"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return extrude.active(context)[1] is not None and context.region_data is not None

    def _along(self, context, event):
        region, rv3d = context.region, context.region_data
        co = (event.mouse_region_x, event.mouse_region_y)
        o = view3d_utils.region_2d_to_origin_3d(region, rv3d, co)
        d = view3d_utils.region_2d_to_vector_3d(region, rv3d, co)
        hit = geometry.intersect_line_line(self._c, self._c + self._n, o, o + d)
        return 0.0 if hit is None else (hit[0] - self._c).dot(self._n)

    def invoke(self, context, event):
        ob, rec = extrude.active(context)
        frame = cap_frame(ob, rec)
        if frame is None:
            return {'CANCELLED'}
        self._ob, self._rec = ob, rec
        self._c, self._n, self._k = frame
        self._start = dict(rec.params)
        self._unit = units.maya_unit(context.scene)
        self._t0 = self._along(context, event)
        self._button = event.type if event.type in {'LEFTMOUSE', 'MIDDLEMOUSE'} else 'LEFTMOUSE'
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _ltz(self, context, event):
        dt = self._along(context, event) - self._t0
        return round(self._start["local_translate_z"] + dt / self._k / self._unit, 4)

    def modal(self, context, event):
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            params = dict(self._start, local_translate_z=self._ltz(context, event))
            extrude.preview(self._ob, self._rec, params, self._unit)
            _state["hot"] = 1
            _redraw(context)
            return {'RUNNING_MODAL'}
        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
            extrude.preview(self._ob, self._rec, self._start, self._unit)
            self._rec.live = False
            _redraw(context)
            return {'CANCELLED'}
        if event.type == self._button and event.value == 'RELEASE':
            extrude.set_params(context, local_translate_z=self._ltz(context, event))
            _redraw(context)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


# --- Channel Box INPUTS ------------------------------------------------------------------------------

def cb_record(context, ob):
    """The lead object's last extrusion for Channel Box INPUTS (any selection), or None."""
    if ob is None or ob is not getattr(context, "edit_object", None):
        return None
    return extrude.current(ob)


def _text_get(field):
    def get(_self):
        rec = cb_record(bpy.context, bpy.context.edit_object)
        if rec is None:
            return ""
        return cb_entry.format_value(rec.params[field], KINDS[field], bpy.context.scene)
    return get


def _text_set(field):
    def set_(_self, text):
        context = bpy.context
        rec = cb_record(context, context.edit_object)
        if rec is None:
            return
        try:
            value = cb_entry.parse_entry(text, rec.params[field], KINDS[field], context.scene)
        except (ValueError, TypeError, SyntaxError, NameError):
            return
        if value != rec.params[field]:
            extrude.set_params(context, **{field: value})
    return set_


class ALLSET_PG_history(bpy.types.PropertyGroup):
    __annotations__ = {f"{f}_text": StringProperty(name=extrude.LABELS[f], get=_text_get(f), set=_text_set(f),
                                                   options={'SKIP_SAVE'})
                       for f in extrude.FIELDS}


HISTORY_TIP = "Blender keeps no edit-mode history: only the last operation can be changed here."


def draw_cb_node(layout, context, rec):
    """The polyExtrudeFace node in Channel Box INPUTS (modeling_04.png); the Blender notice is the node name's
    tooltip (step 106: no Blender sentences in Maya windows). Collapsed until its name is clicked, like Maya
    (, step 135)."""
    from . import channel_box
    lines = channel_box.as_lines(layout)
    ob = channel_box.lead(context)
    _row, opened = channel_box.node_row(lines, ob, channel_box.history_node(rec.name), rec.name, tip=HISTORY_TIP)
    if not opened:
        return
    hist = context.window_manager.allset_history
    for field in extrude.FIELDS:
        row = lines.row()
        if row is None:
            continue
        split = row.split(factor=0.5, align=True)
        split.label(text=extrude.LABELS[field])
        split.prop(hist, f"{field}_text", text="")


classes = (ALLSET_PG_history, ALLSET_GT_in_view_row, ALLSET_GGT_in_view, ALLSET_GGT_extrude,
           ALLSET_OT_inview_drag, ALLSET_OT_inview_type, ALLSET_OT_extrude_drag)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.allset_history = PointerProperty(type=ALLSET_PG_history)
    _state["handle"] = bpy.types.SpaceView3D.draw_handler_add(draw_box, (), 'WINDOW', 'POST_PIXEL')


def unregister():
    if _state["handle"] is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_state["handle"], 'WINDOW')
        _state["handle"] = None
    del bpy.types.WindowManager.allset_history
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
