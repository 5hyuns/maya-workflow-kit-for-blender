# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya's extrude manipulator, In-View Editor and the INPUTS rows of the last extrusion
(step 65).

- Visible while the active edit object's last kit extrusion is valid and its extruded faces are the selection
  (operators/extrude.py). Maya swaps the Move manipulator for the extrude one: the kit Move/Scale manipulator
  (ui/manipulator.py) hides meanwhile.
- The manipulator is a Python gizmo group (Blender's C transform gizmo can't be extended). Step 151:
  Maya's polyExtrudeFace manipulator in the faces' local frame - three
  arrows (Local Translate X red / Y green / Z blue = the normal), a cube past each cone (Local Scale X / Y / Z), three
  plane handles (two Local Translate values) and a light-blue centre square (uniform Local Scale). Every handle runs
  ``allset.extrude_drag`` with its ``handle``; release = one undo step (``extrude.set_params``). Edge / vertex
  extrusions and bevels keep the single arrow of their ``Spec.arrow``. No Blender tooltips (Maya manipulators have
  none).
- The In-View Editor box is drawn by a POST_PIXEL handler; 2D gizmos only pick its rows (the shelf's way, step 51).
  Dragging a row sideways changes the value, a click without a drag types it, Keep Faces Together toggles.
- Channel Box INPUTS: the node and five rows (WindowManager text proxies: a UI edit of a WM property pushes no
  undo step, the edit itself is one, step 38) + the "only the last one" notice.
"""

import blf
import bmesh
import bpy
import gpu
import time
from bpy.props import FloatProperty, IntProperty, PointerProperty, StringProperty
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector, geometry

from . import cb_entry, manipulator
from ..operators import bevel_maya, extrude, units   # bevel_maya: registers the polyBevel spec (step 139)
from ..operators import uv_tools  # noqa: F401  registers the polyAutoProj spec (step 257)

ROW_H = 16          # px at UI scale 1 (Maya In-View rows)
WIDTH = 180
GAP = (150, -6)     # box top-left from the manipulator centre on screen: right of the X / Y handles (step 151;
                    # Maya: past the manipulator, 250 px from its centre at a 100 px rotate ring)
FLOAT_STEP = 0.01   # Maya units per px of a sideways drag
DIV_PX = 20         # px per division
KINDS = {"thickness": "NONE", "local_translate_z": "NONE", "offset": "NONE", "divisions": "INT",
         "keep_faces_together": "BOOL"}
# every field of every recorded node (Channel Box text proxies, step 139: edge / vertex extrusion, bevel)
ALL_FIELDS = tuple(dict.fromkeys(f for spec in extrude.SPECS.values() for f in spec.fields))
MAX_ROWS = max(len(spec.fields) for spec in extrude.SPECS.values())
BOOL_FIELDS = {f for spec in extrude.SPECS.values() for f, k in spec.kinds.items() if k == "BOOL"}
INT_FIELDS = {f for spec in extrude.SPECS.values() for f, k in spec.kinds.items() if k == "INT"}
RANGES = {"fraction": (0.0, 1.0), "depth": (-1.0, 1.0), "planes": (3, 12), "optimize": (0.0, 1.0),
          "percentage_space": (0.0, 5.0)}
_ = bevel_maya
BG = (0.22, 0.22, 0.22, 0.92)
TITLE_BG = (0.30, 0.30, 0.30, 0.95)
TEXT = (0.62, 0.62, 0.62, 1.0)        # unselected grey-white
LIT = (1.0, 1.0, 1.0, 1.0)            # hover pure white
HOT = (1.0, 0.83, 0.25, 1.0)          # selected/active gold
YELLOW = (1.0, 1.0, 0.0)
VALUE_BG = (0.10, 0.10, 0.10, 1.0)     # dark field behind the value (Maya)

# Solid sensitivity fan (Maya percentage): 0% at 8 o'clock, 360-degree sweep.
from math import radians as _radians, cos as _cos, sin as _sin
FAN_START = _radians(210)
FAN_SWEEP = _radians(360)
FAN_R = 8.0
VALUE_W = 56.0       # fixed dark value-field width (px at UI scale 1)
# Maya's percentage control is a light-blue solid pie (0% at 8 o'clock,
# full 360-degree clockwise sweep).
FAN_BLUE = (0.45, 0.72, 1.0, 1.0)
FAN_TRACK = (0.45, 0.72, 1.0, 0.45)

_state = {"hot": 0, "hover": -1, "sensitivity": 1.0, "handle": None,
          "fan_drag": False, "active_record_key": None}
_global_mmb_timer = None
_global_mmb_enabled = False
_global_mmb_area_ptrs = set()
_global_mmb_idle_since = {}
_global_mmb_expired_area_ptrs = set()
HUD_LISTENER_IDLE_TIMEOUT = 600.0


def _sens_multiplier():
    from . import in_view_settings as shared
    _state["sensitivity"] = shared.get_sensitivity()
    return 0.02 + 0.98 * _state["sensitivity"]


def _fan_fraction_at(cx, cy, x, y):
    """Map a point on the circular fan to 0..1, clockwise from 8 o'clock."""
    from math import atan2, tau
    dx, dy = x - cx, y - cy
    if dx * dx + dy * dy < 0.25:
        return 0.0
    return ((FAN_START - atan2(dy, dx)) % tau) / tau


def _event_region_xy(context, event):
    """Convert window mouse coordinates to the invoking View3D WINDOW region.

    A persistent modal operator can receive events while Blender's active
    region context differs from the region that originally started it.
    mouse_region_x/y may then describe the wrong region; window coordinates
    minus Region.x/y remain tied to the modal operator's owning region.
    """
    region = getattr(context, "region", None)
    if region is None:
        return (event.mouse_region_x, event.mouse_region_y)
    return (event.mouse_x - region.x, event.mouse_y - region.y)


def _panel_hit(context, x, y):
    """Return ('FAN', center), ('ROW', index), 'PANEL', or None in region pixels."""
    _rec, lay = current_layout(context)
    if lay is None:
        return None
    bx0, by0, bx1, by1 = lay["box"]
    if not (bx0 <= x <= bx1 and by0 <= y <= by1):
        return None

    tx0, ty0, tx1, ty1 = lay["title"]
    scale = _scale()
    cx = tx1 - (FAN_R + 5.0 * scale)
    cy = (ty0 + ty1) / 2.0
    radius = FAN_R * scale
    if (x - cx) ** 2 + (y - cy) ** 2 <= radius * radius * 1.6:
        return ("FAN", (cx, cy))

    for index, (_field, x0, y0, x1, y1) in enumerate(lay["rows"]):
        if x0 <= x <= x1 and y0 <= y <= y1:
            return ("ROW", index)
    return "PANEL"


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
    if rec is None or rec.dismissed or not rec.spec.in_view or not extrude.caps_selected(ob, rec):
        return None, None
    return ob, rec


def manip_visible(context):
    return record(context)[1] is not None


def arrow_visible(context):
    rec = record(context)[1]
    return rec is not None and rec.spec.arrow is not None


def _pre_direction(rec):
    """Arrow direction of an edge / vertex extrusion or a bevel, from the mesh before it (cached)."""
    d = getattr(rec, "arrow_dir", None)
    if d is not None:
        return d
    pre = rec.pre
    d = Vector()
    if pre is not None:
        pre.normal_update()
        if rec.spec.kind == 'VERTEX':
            for v in pre.verts:
                if v.select:
                    d += sum((f.normal for f in v.link_faces), Vector()).normalized()
        else:
            for e in pre.edges:
                if e.select:
                    d += extrude.edge_frame(e)[2]
    rec.arrow_dir = d
    return d


def cap_frame(ob, rec):
    """(world centre, world unit normal, world length of one local unit along it) of the extruded faces (edge /
    vertex extrusion: the selection it left, the mean edge / vertex normal; bevel: the bevel's vertices)."""
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    verts = [bm.verts[i] for i in rec.cap_verts if i < len(bm.verts)]
    if rec.spec is not extrude.FACE:
        verts = [v for v in bm.verts if v.select] or verts
    faces = [bm.faces[i] for i in rec.cap_faces if i < len(bm.faces)]
    if not verts:
        return None
    centre = sum((v.co for v in verts), Vector()) / len(verts)
    n = sum((f.normal for f in faces), Vector()) if rec.spec is extrude.FACE else _pre_direction(rec).copy()
    n = n.normalized() if n.length > 1e-9 else Vector((0, 0, 1))
    mw = ob.matrix_world
    nw = mw.to_3x3() @ n
    k = nw.length or 1.0
    return mw @ centre, nw / k, k


def layout(region, anchor, scale, fields=extrude.FIELDS, fixed_position=False):
    """Box geometry in region pixels: {"box", "title", "rows": [(field, x0, y0, x1, y1)]}."""
    # Preserve the accepted fixed HUD footprint. Percentages are used only
    # for the default position anchor, not panel dimensions.
    w, h = WIDTH * scale, ROW_H * scale
    n = len(fields) + 1
    if fixed_position:
        x0, top = anchor
    else:
        x0 = anchor[0] + GAP[0] * scale
        top = anchor[1] + GAP[1] * scale
    x0 = max(4 * scale, min(x0, region.width - w - 4 * scale))
    top = max(n * h + 4 * scale, min(top, region.height - 4 * scale))
    rows = []
    for i, field in enumerate(fields):
        y1 = top - (i + 1) * h
        rows.append((field, x0, y1 - h, x0 + w, y1))
    return {"box": (x0, top - n * h, x0 + w, top), "title": (x0, top - h, x0 + w, top), "rows": rows}


def anchor(context, ob, rec):
    frame = cap_frame(ob, rec)
    if frame is None:
        return None
    p = view3d_utils.location_3d_to_region_2d(context.region, context.region_data, frame[0])
    return (p.x, p.y) if p is not None else None


def _first_adjustable_field_index(rec):
    """First non-boolean parameter row; bool-only tools fall back to row zero."""
    fields = tuple(getattr(getattr(rec, "spec", None), "fields", ()) or ())
    for index, field in enumerate(fields):
        if field not in BOOL_FIELDS:
            return index
    return 0 if fields else -1


def _sync_active_record(rec):
    """Select the first adjustable row whenever a new operation appears."""
    key = id(rec) if rec is not None else None
    if key != _state.get("active_record_key"):
        _state["active_record_key"] = key
        # The compact Maya HUD opens ready for MMB adjustment. Do not require
        # an initial click on a row; use the first non-boolean parameter.
        _state["hot"] = _first_adjustable_field_index(rec) if rec is not None else 0
        _state["hover"] = -1


def current_layout(context):
    ob, rec = record(context)
    if rec is None or context.region is None or context.region.type != 'WINDOW' or context.region_data is None:
        return None, None
    _sync_active_record(rec)
    from . import in_view_settings as shared
    position = shared.get_position("maya_inview_hud", context.region)
    if position is None:
        position = shared.default_position(context.region)
    lay = layout(context.region, position, _scale(), rec.spec.fields,
                 fixed_position=True)
    return rec, lay


def value_text(rec, field):
    v = rec.params[field]
    if field in BOOL_FIELDS:
        return "On" if v else "Off"
    if field in INT_FIELDS:
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


def _fan_geometry(cx, cy, r, fraction):
    points = [(cx, cy)]
    sweep = FAN_SWEEP * max(0.0, min(1.0, fraction))
    steps = max(2, int(round(48 * max(0.0, min(1.0, fraction)))))
    for i in range(steps + 1):
        # Decreasing angle draws clockwise on screen (y-up pixel space).
        ang = FAN_START - sweep * (i / steps)
        points.append((cx + r * _cos(ang), cy + r * _sin(ang)))
    tris = [(0, i, i + 1) for i in range(1, len(points) - 1)]
    return points, tris


def _fan_track(cx, cy, r):
    return [(cx + r * _cos(FAN_START - FAN_SWEEP * (i / 48)),
             cy + r * _sin(FAN_START - FAN_SWEEP * (i / 48)))
            for i in range(49)]


def _draw_fan(cx, cy, r, fraction):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    track = _fan_track(cx, cy, r)
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": track})
    shader.uniform_float("color", FAN_TRACK)
    batch.draw(shader)
    points, tris = _fan_geometry(cx, cy, r, fraction)
    batch = batch_for_shader(shader, 'TRIS', {"pos": points}, indices=tris)
    shader.uniform_float("color", FAN_BLUE)
    batch.draw(shader)


def draw_box():
    """POST_PIXEL of 3D View WINDOW regions: the In-View Editor next to the extrude manipulator."""
    from . import in_view_settings as shared
    _state["sensitivity"] = shared.get_sensitivity()
    context = bpy.context
    rec, lay = current_layout(context)
    if rec is None:
        return
    from ..marking import draw as marking_draw
    if marking_draw.menu_up():   # Maya's hotbox / marking menus cover the In-View Editor (step 197)
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
    # Solid sensitivity fan at the title's right side.
    fan_cx = x1 - (FAN_R + pad)
    fan_cy = (y0 + y1) / 2
    _draw_fan(fan_cx, fan_cy, FAN_R * s, _state["sensitivity"])
    _state["fan_rect"] = (fan_cx - FAN_R * s, fan_cy - FAN_R * s,
                          fan_cx + FAN_R * s, fan_cy + FAN_R * s)
    for i, (field, rx0, ry0, rx1, ry1) in enumerate(lay["rows"]):
        if i == _state["hot"]:
            name_colour = HOT
        elif i == _state["hover"]:
            name_colour = LIT
        else:
            name_colour = TEXT
        _text(rx0 + pad, ry0 + 4 * s, rec.spec.labels[field], name_colour, size)
        v = value_text(rec, field)
        blf.size(0, size)
        vw = blf.dimensions(0, v)[0]
        vx1 = rx1 - pad
        # Fixed-width dark value field, identical for every row.
        vx0 = vx1 - VALUE_W * s
        vy0 = ry0 + 3 * s
        vy1 = ry1 - 2 * s
        _rect(vx0, vy0 - 1 * s, vx1 + 3 * s, vy1 + 1 * s, VALUE_BG)
        value_colour = HOT if i == _state["hot"] else TEXT
        # Right-align the number inside the fixed field.
        _text(vx1 - vw - 3 * s, ry0 + 4 * s, v, value_colour, size)
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
        if lay is None or self.row >= len(lay["rows"]):
            return -1
        _f, x0, y0, x1, y1 = lay["rows"][self.row]
        if x0 <= location[0] <= x1 and y0 <= location[1] <= y1:
            # Hover only lights the row white; gold is set on click/drag.
            if _state["hover"] != self.row:
                _state["hover"] = self.row
                context.region.tag_redraw()
            return 0
        if _state["hover"] == self.row:
            _state["hover"] = -1
        return -1


class ALLSET_GT_fan(bpy.types.Gizmo):
    """Picking for the solid sensitivity fan (drawn by draw_box)."""
    bl_idname = "ALLSET_GT_fan"

    def draw(self, context):
        pass

    def test_select(self, context, location):
        rect = _state.get("fan_rect")
        if rect is None:
            return -1
        x0, y0, x1, y1 = rect
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        r = (x1 - x0) / 2
        # Precise circular hit (the drawn pie), not the bounding square.
        dist = ((location[0] - cx) ** 2 + (location[1] - cy) ** 2) ** 0.5
        return 0 if dist <= r else -1


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
        # Fan first so its title-area pick wins over any overlapping row.
        fan = self.gizmos.new(ALLSET_GT_fan.bl_idname)
        fan.target_set_operator(ALLSET_OT_fan_drag.bl_idname)
        for i in range(MAX_ROWS):
            gz = self.gizmos.new(ALLSET_GT_in_view_row.bl_idname)
            gz.row = i
            gz.target_set_operator(ALLSET_OT_inview_drag.bl_idname).row = i


# --- the extrude manipulator (3D gizmo, step 151) --------------------------------------------------

# Maya 2022 polyExtrudeFace manipulator (top face of a cube,
# local mode): lengths in "arrow units" (centre -> scale cube = 1): cone 0.64 -> 0.86 (radius 0.05), cube half 0.07,
# plane handles centred 0.5 / 0.5 between two axes (half 0.08, translucent with a full-colour rim), hollow centre square
# half 0.12 (20 px at an 83 px Z arrow) in #64dcff, screen facing. Axis colours = the kit Move manipulator's Maya
# colours (manipulator.MAYA_AXIS). Not drawn: Maya's cyan rotate ring (polyExtrudeFace Local Rotate - the
# kit doesn't model it) and its world / local toggle icon (world mode drives Translate / Rotate / Scale, not modelled).
CONE_BASE, CONE_TIP, CONE_R = 0.64, 0.86, 0.05
CUBE_AT, CUBE_HALF = 1.0, 0.07
PLANE_AT, PLANE_HALF = 0.5, 0.08
PLANE_FILL = 0.25
CENTER_HALF = 0.12
CENTER_COLOUR = (0x64 / 255, 0xdc / 255, 1.0)
SCALE_PX = 100.0          # px of mouse travel along a scale handle that doubles the scale
# the extrude manipulator is drawn smaller than the Move one: Z arrow to cube 83 px at a ~27 deg persp elevation
# = ~93 px against the Move Y arrow's 108 px (manipulator.ARROW_PX)
SIZE = 0.86

# handle -> (role, axis or plane, the values it drives)
HANDLES = {
    "TX": ('ARROW', 'X', ("local_translate_x",)),
    "TY": ('ARROW', 'Y', ("local_translate_y",)),
    "TZ": ('ARROW', 'Z', ("local_translate_z",)),
    "SX": ('CUBE', 'X', ("local_scale_x",)),
    "SY": ('CUBE', 'Y', ("local_scale_y",)),
    "SZ": ('CUBE', 'Z', ("local_scale_z",)),
    "PXY": ('PLANE', 'XY', ("local_translate_x", "local_translate_y")),
    "PYZ": ('PLANE', 'YZ', ("local_translate_y", "local_translate_z")),
    "PXZ": ('PLANE', 'XZ', ("local_translate_x", "local_translate_z")),
    "S": ('CENTER', None, ("local_scale_x", "local_scale_y", "local_scale_z")),
}
AXIS_INDEX = {'X': 0, 'Y': 1, 'Z': 2}


def handle_fields(rec, handle):
    """The values ``handle`` drives on ``rec`` (edge / vertex extrusion, bevel: only "TZ" = their arrow field)."""
    if rec is None or handle not in HANDLES:
        return ()
    if rec.spec is not extrude.FACE:
        return (rec.spec.arrow,) if handle == "TZ" and rec.spec.arrow is not None else ()
    return HANDLES[handle][2]


def manip_frame(ob, rec):
    """(world centre, 3x3 world unit axes (columns X, Y, Z), world lengths of one mesh unit along X / Y / Z) of the
    extrude manipulator: Z = the faces' normal, X / Y = polyExtrudeFace's local axes of that normal (world X projected
    into the face plane, extrude.face_axes). None when there is nothing to show."""
    frame = cap_frame(ob, rec)
    if frame is None:
        return None
    centre, nw, kz = frame
    mw3 = ob.matrix_world.to_3x3()
    inv = mw3.inverted_safe()
    n_obj = (inv @ nw)
    n_obj = n_obj.normalized() if n_obj.length > 1e-12 else Vector((0, 0, 1))
    axes = extrude.mesh_axes(ob)
    x_obj, y_obj = extrude.face_axes(n_obj, axes["direction"], axes["fallback"])
    xw, yw = mw3 @ x_obj, mw3 @ y_obj
    kx, ky = xw.length or 1.0, yw.length or 1.0
    xw, yw = xw / kx, yw / ky
    return centre, Matrix((xw, yw, nw)).transposed(), (kx, ky, kz)


def unit_px(context):
    """Screen px of one arrow unit (wm_gizmo: scale_basis x gizmo_size x UI scale at use_draw_scale)."""
    return (manipulator.scale_basis(context) * SIZE * context.preferences.view.gizmo_size
            * (context.preferences.system.ui_scale or 1.0))


def handles_hit(context, region, rv3d, mouse, reach):
    """True when ``mouse`` (region px) is within ``reach`` px of a shown handle of the extrude manipulator: the
    pre-selection gizmo (operators/preselect.py, a 2D test_select that would win over these 3D-picked handles)
    declines there, like it does on the Move manipulator (step 97)."""
    ob, rec = record(context)
    frame = manip_frame(ob, rec) if rec is not None else None
    if frame is None:
        return False
    centre, axes, _k = frame
    c2 = view3d_utils.location_3d_to_region_2d(region, rv3d, centre)
    if c2 is None:
        return False
    w = view3d_utils.region_2d_to_location_3d(region, rv3d, c2 + Vector((1.0, 0.0)), centre) - centre
    unit = unit_px(context) * w.length          # world length of one arrow unit at the centre
    m = Vector(mouse)

    def at(vec):
        p = view3d_utils.location_3d_to_region_2d(region, rv3d, centre + vec * unit)
        return p if p is not None else c2

    for handle in HANDLES:
        if not handle_fields(rec, handle):
            continue
        role, data, _f = HANDLES[handle]
        if role == 'ARROW':
            a, b = c2, at(axes.col[AXIS_INDEX[data]] * CONE_TIP)
            ab = b - a
            t = 0.0 if ab.length_squared < 1e-9 else max(0.0, min(1.0, (m - a).dot(ab) / ab.length_squared))
            if (a + ab * t - m).length <= reach:
                return True
        elif role == 'CUBE':
            if (at(axes.col[AXIS_INDEX[data]] * CUBE_AT) - m).length <= reach + CUBE_HALF * unit_px(context):
                return True
        elif role == 'PLANE':
            i, j = AXIS_INDEX[data[0]], AXIS_INDEX[data[1]]
            if (at((axes.col[i] + axes.col[j]) * PLANE_AT) - m).length <= reach + PLANE_HALF * unit_px(context):
                return True
        elif (c2 - m).length <= reach + CENTER_HALF * unit_px(context):
            return True
    return False


def handle_shapes(role):
    """(draw shapes [(type, verts, fill)], pick shape (type, verts)) of a handle in arrow units: arrows / cubes point
    along local +Z, plane handles lie in the local XY plane, the centre square faces +Z. Pure (tests run it headless)."""
    m = manipulator
    if role == 'ARROW':
        return ([('LINES', [(0, 0, 0), (0, 0, CONE_BASE)], False), ('TRIS', m._cone(CONE_BASE, CONE_TIP, CONE_R), False)],
                ('TRIS', m._bar(CENTER_HALF, CONE_BASE, 0.04) + m._cone(CONE_BASE, CONE_TIP, CONE_R * 1.6)))
    if role == 'CUBE':
        return ([('LINES', [(0, 0, CONE_TIP), (0, 0, CUBE_AT - CUBE_HALF)], False),
                 ('TRIS', m._box((0, 0, CUBE_AT), CUBE_HALF), False)],
                ('TRIS', m._box((0, 0, CUBE_AT), CUBE_HALF * 1.6)))
    if role == 'PLANE':
        rim = [(x + PLANE_AT, y + PLANE_AT, z) for x, y, z in m._square_outline(PLANE_HALF)]
        return ([('TRIS', m._square(PLANE_AT, PLANE_AT, PLANE_HALF), True), ('LINES', rim, False)],
                ('TRIS', m._square(PLANE_AT, PLANE_AT, PLANE_HALF * 1.3)))
    if role == 'CENTER':
        return ([('LINES', m._square_outline(CENTER_HALF), False)], ('TRIS', m._square(0, 0, CENTER_HALF * 1.3)))
    raise ValueError(role)


class ALLSET_GT_extrude_handle(bpy.types.Gizmo):
    """One handle of the Maya extrude manipulator (custom shapes; plane handles: translucent fill + rim)."""
    bl_idname = "ALLSET_GT_extrude_handle"
    __slots__ = ("draw_shapes", "pick_shape", "handle")

    def build(self, handle):
        self.handle = handle
        draw, pick = handle_shapes(HANDLES[handle][0])
        self.draw_shapes = [(self.new_custom_shape(t, v), fill) for t, v, fill in draw]
        self.pick_shape = self.new_custom_shape(*pick)

    def draw(self, context):
        colour = self.color_highlight if self.is_highlight else self.color
        alpha = self.alpha_highlight if self.is_highlight else self.alpha
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(self.line_width)
        for (batch, shader), fill in getattr(self, "draw_shapes", ()):
            shader.bind()
            shader.uniform_float("color", (*colour, alpha * PLANE_FILL if fill else alpha))
            with gpu.matrix.push_pop():
                gpu.matrix.multiply_matrix(self.matrix_world)
                batch.draw(shader)
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set('NONE')

    def draw_select(self, context, select_id):
        sh = getattr(self, "pick_shape", None)
        if sh is not None:
            self.draw_custom_shape(sh, select_id=select_id)


def _no_tooltip(gz):
    """Maya manipulators have no tooltips; Blender would show the target operator's description (#98)."""
    if hasattr(gz, "use_tooltip"):
        gz.use_tooltip = False


class ALLSET_GGT_extrude(bpy.types.GizmoGroup):
    bl_idname = "ALLSET_GGT_extrude"
    bl_label = "Maya Extrude Manipulator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and space.type == 'VIEW_3D' and space.show_gizmo and arrow_visible(context)

    def setup(self, context):
        self.handles = {}
        for handle in HANDLES:
            gz = self.gizmos.new(ALLSET_GT_extrude_handle.bl_idname)
            gz.build(handle)
            gz.target_set_operator(ALLSET_OT_extrude_drag.bl_idname).handle = handle
            gz.color_highlight = YELLOW
            gz.alpha = gz.alpha_highlight = 1.0
            gz.line_width = 1.5
            gz.use_draw_scale = True
            gz.use_draw_modal = True
            _no_tooltip(gz)
            self.handles[handle] = gz
        self.arrow = self.handles["TZ"]

    def draw_prepare(self, context):
        ob, rec = record(context)
        if rec is None:
            return
        frame = manip_frame(ob, rec)
        rv3d = context.region_data
        view = rv3d.view_rotation.to_matrix() if rv3d is not None else Matrix.Identity(3)
        colours = manipulator.axis_colours()
        s = manipulator.scale_basis(context) * SIZE
        for handle, gz in self.handles.items():
            gz.hide = frame is None or not handle_fields(rec, handle)
            if gz.hide:
                continue
            centre, axes, _k = frame
            role, data, _fields = HANDLES[handle]
            gz.scale_basis = s
            if role in ('ARROW', 'CUBE'):
                rot = axes @ manipulator._axis_rot(data)
                gz.color = colours[data]
            elif role == 'PLANE':
                _c, normal, local = manipulator.PLANES[data]
                rot = axes @ local
                gz.color = colours[normal]
            else:
                rot = view
                gz.color = CENTER_COLOUR
            gz.matrix_basis = Matrix.Translation(centre) @ rot.to_4x4()


# --- operators ---------------------------------------------------------------------------------------

def _redraw(context):
    for area in context.screen.areas if context.screen else ():
        if area.type == 'VIEW_3D':
            area.tag_redraw()


class ALLSET_OT_fan_drag(bpy.types.Operator):
    """Drag the sensitivity fan: right raises, left lowers global drag speed"""
    bl_idname = "allset.fan_drag"
    bl_label = "Sensitivity"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return extrude.active(context)[1] is not None

    def invoke(self, context, event):
        _rec, lay = current_layout(context)
        if lay is None:
            return {'CANCELLED'}
        _tx0, ty0, tx1, ty1 = lay["title"]
        self._fan_cx = tx1 - (FAN_R + 5.0 * _scale())
        self._fan_cy = (ty0 + ty1) / 2.0
        self._start = _state["sensitivity"]
        self._moved = False
        # Clicking any point on the pie sets its exact percentage immediately.
        _state["sensitivity"] = _fan_fraction_at(
            self._fan_cx, self._fan_cy,
            event.mouse_region_x, event.mouse_region_y)
        from . import in_view_settings as shared
        shared.set_sensitivity(_state["sensitivity"])
        _redraw(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            if (abs(event.mouse_region_x - self._fan_cx) > 0
                    or abs(event.mouse_region_y - self._fan_cy) > 0):
                self._moved = True
            if self._moved:
                _state["sensitivity"] = _fan_fraction_at(
                    self._fan_cx, self._fan_cy,
                    event.mouse_region_x, event.mouse_region_y)
                from . import in_view_settings as shared
                shared.set_sensitivity(_state["sensitivity"])
                _redraw(context)
            return {'RUNNING_MODAL'}
        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
            _state["sensitivity"] = self._start
            from . import in_view_settings as shared
            shared.set_sensitivity(_state["sensitivity"])
            _redraw(context)
            return {'CANCELLED'}
        if event.type in {'LEFTMOUSE', 'MIDDLEMOUSE'} and event.value == 'RELEASE':
            _redraw(context)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


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
        if self.row >= len(rec.spec.fields):
            return {'CANCELLED'}
        _sync_active_record(rec)
        field = rec.spec.fields[self.row]
        _state["hot"] = self.row
        if field in BOOL_FIELDS:
            extrude.set_params(context, **{field: not rec.params[field]})
            _redraw(context)
            return {'FINISHED'}
        # LMB on the label text only activates the row (no popup, no drag).
        # MMB, or a press on the value field, proceeds to the drag/click logic.
        if event.type == 'LEFTMOUSE':
            _rec, lay = current_layout(context)
            if lay is not None and self.row < len(lay["rows"]):
                _f, rx0, ry0, rx1, ry1 = lay["rows"][self.row]
                mx = getattr(event, "mouse_region_x", event.mouse_x)
                if mx < (rx0 + rx1) / 2:
                    _redraw(context)
                    return {'FINISHED'}
        self._ob, self._rec, self._field = ob, rec, field
        self._start = dict(rec.params)
        self._x0, self._moved = event.mouse_x, False
        self._button = event.type if event.type in {'LEFTMOUSE', 'MIDDLEMOUSE'} else 'LEFTMOUSE'
        self._unit = units.maya_unit(context.scene)
        self._cursor_set = False
        self._cursor_window = None
        if self._button == 'MIDDLEMOUSE':
            self._set_modal_cursor(context, True)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _set_modal_cursor(self, context, enable):
        """Use Blender Window's modal cursor API (WindowManager has no cursor property)."""
        if enable:
            if self._cursor_set:
                return
            window = getattr(context, "window", None)
            if window is None:
                return
            try:
                window.cursor_modal_set('MOVE_X')
            except (AttributeError, ReferenceError, RuntimeError):
                return
            self._cursor_window = window
            self._cursor_set = True
            return

        if not self._cursor_set:
            return
        window = getattr(self, "_cursor_window", None)
        try:
            if window is not None:
                window.cursor_modal_restore()
        except (AttributeError, ReferenceError, RuntimeError):
            pass
        finally:
            self._cursor_window = None
            self._cursor_set = False

    def _restore_cursor(self, context):
        self._set_modal_cursor(context, False)

    def cancel(self, context):
        self._restore_cursor(context)

    def _value(self, event):
        s = _scale()
        dx = (event.mouse_x - self._x0) / s
        start = self._start[self._field]
        mult = _sens_multiplier()
        if self._field in INT_FIELDS:
            return max(1, int(start + round(dx / DIV_PX * mult)))
        # Sensitivity fan scales the drag; Ctrl/Shift still fine/coarse-tune.
        step = FLOAT_STEP * mult * (0.1 if event.ctrl else 10.0 if event.shift else 1.0)
        return clamp(self._field, round(start + dx * step, 4))

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
            self._restore_cursor(context)
            _redraw(context)
            return {'CANCELLED'}
        if event.type == self._button and event.value == 'RELEASE':
            if self._moved:
                extrude.set_params(context, **{self._field: self._value(event)})
            elif self._button == 'LEFTMOUSE':
                # Preserve the existing LMB click-to-type behaviour.
                bpy.ops.allset.inview_type('INVOKE_DEFAULT', row=self.row)
            # An MMB click only activates the row; it must never open a dialog.
            self._restore_cursor(context)
            _redraw(context)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


def _global_mmb_running(window=None, area_ptr=None):
    """Check whether this window/3D View already owns an MMB listener."""
    wm = bpy.context.window_manager
    if wm is None:
        return False

    windows = (window,) if window is not None else tuple(wm.windows)
    found_global = False

    for win in windows:
        for op in getattr(win, "modal_operators", ()):
            try:
                # Blender exposes the modal operator's class identifier here
                # (ALLSET_OT_global_mmb), not always its RNA bl_idname.
                # Operator instances do not support IDProperty-style .get().
                op_id = getattr(op, "bl_idname", "")
                if op_id not in (
                    ALLSET_OT_global_mmb.bl_idname,
                    ALLSET_OT_global_mmb.__name__,
                ):
                    continue

                found_global = True
                op_area = getattr(op, "owner_area", None)

                if area_ptr is None:
                    return True

                if op_area is not None and int(op_area) == int(area_ptr):
                    return True

            except (AttributeError, ReferenceError, TypeError, ValueError):
                continue

    if area_ptr is not None:
        area_ptr = int(area_ptr)

        # Fallback for Blender versions that do not expose the RNA
        # StringProperty through window.modal_operators.
        if not found_global:
            _global_mmb_area_ptrs.discard(area_ptr)
            return False

        return area_ptr in _global_mmb_area_ptrs

    return found_global



def _find_owner_view(window, area_ptr):
    """Resolve the listener's original View3D area and WINDOW region safely."""
    screen = getattr(window, "screen", None)
    if screen is None:
        return None, None
    for area in screen.areas:
        try:
            if area.as_pointer() != area_ptr:
                continue
            if area.type != 'VIEW_3D':
                return None, None
            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            return area, region
        except (ReferenceError, AttributeError):
            return None, None
    return None, None


def _mouse_in_region(event, region):
    if region is None:
        return False
    return (region.x <= event.mouse_x < region.x + region.width
            and region.y <= event.mouse_y < region.y + region.height)


class ALLSET_OT_global_mmb(bpy.types.Operator):
    """Per-View3D MMB listener for Maya In-View parameter editing.

    Each View3D area owns one listener. It resolves the pointer against that
    area's WINDOW region before hit-testing, so a listener started in another
    viewport (or a different editor) cannot steal or mis-map the MMB event.
    """
    bl_idname = "allset.global_mmb"
    bl_label = "Global MMB Adjust"
    bl_options = {'INTERNAL'}

    owner_area: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def invoke(self, context, event):
        if context.area is None or context.area.type != 'VIEW_3D':
            return {'CANCELLED'}
        self.owner_area = str(context.area.as_pointer())
        _global_mmb_area_ptrs.add(int(self.owner_area))
        self._dragging = False
        self._fan_dragging = False
        self._moving = False
        self._move_start = None
        self._move_mouse = None
        self._cursor_set = False
        self._cursor_window = None
        self._cursor_shape = None
        self._hot = _state["hot"]
        self._region_x = context.region.x if context.region else 0
        self._region_y = context.region.y if context.region else 0
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        self._set_cursor_shape(context, None)
        try:
            _global_mmb_area_ptrs.discard(int(getattr(self, "owner_area", "0")))
        except (TypeError, ValueError):
            pass

    def _set_cursor_shape(self, context, shape):
        """Switch modal cursor shapes without leaving a stale cursor behind."""
        current = getattr(self, "_cursor_shape", None)
        if current == shape:
            return

        # cursor_modal_set() restores the cursor that was active before the
        # modal override. Restore before switching from title-hover to drag.
        if current is not None:
            window = getattr(self, "_cursor_window", None)
            try:
                if window is not None:
                    window.cursor_modal_restore()
            except (AttributeError, ReferenceError, RuntimeError):
                pass
            self._cursor_shape = None
            self._cursor_window = None
            self._cursor_set = False

        if shape is None:
            return

        window = getattr(context, "window", None)
        if window is None:
            return
        try:
            window.cursor_modal_set(shape)
        except (AttributeError, ReferenceError, RuntimeError, TypeError, ValueError):
            return
        self._cursor_window = window
        self._cursor_shape = shape
        self._cursor_set = True

    def _set_cursor(self, context, on):
        """Cursor used while an MMB parameter drag is active."""
        self._set_cursor_shape(context, 'MOVE_X' if on else None)

    def _set_title_cursor(self, context, on):
        """Four-direction move cursor while hovering the compact HUD title."""
        # Never replace the cursor belonging to an active value drag.
        if getattr(self, "_cursor_shape", None) == 'MOVE_X':
            return
        self._set_cursor_shape(context, 'SCROLL_XY' if on else None)

    def _begin(self, context, event, visible_record=None):
        # The caller passes a record resolved under this listener's own
        # View3D override; do not re-query a possibly unrelated active region.
        ob, rec = visible_record if visible_record is not None else record(context)
        if rec is None or self._hot < 0 or self._hot >= len(rec.spec.fields):
            return False
        field = rec.spec.fields[self._hot]
        if field in BOOL_FIELDS:
            extrude.set_params(context, **{field: not rec.params[field]})
            _redraw(context)
            return False
        self._ob, self._rec, self._field = ob, rec, field
        self._start = dict(rec.params)
        self._x0 = event.mouse_x
        self._unit = units.maya_unit(context.scene)
        self._moved = False
        self._set_cursor(context, True)
        return True

    def _value(self, event):
        s = _scale()
        dx = (event.mouse_x - self._x0) / s
        start = self._start[self._field]
        mult = _sens_multiplier()
        if self._field in INT_FIELDS:
            return max(1, int(start + round(dx / DIV_PX * mult)))
        step = FLOAT_STEP * mult
        return clamp(self._field, round(start + dx * step, 4))

    def modal(self, context, event):
        window = context.window
        if window is None:
            self.cancel(context)
            return {'CANCELLED'}
        area_ptr = int(self.owner_area)
        area, region = _find_owner_view(window, area_ptr)
        if area is None or region is None:
            self.cancel(context)
            return {'CANCELLED'}
        if area_ptr in _global_mmb_expired_area_ptrs:
            self.cancel(context)
            _global_mmb_expired_area_ptrs.discard(area_ptr)
            _global_mmb_idle_since.pop(area_ptr, None)
            return {'CANCELLED'}

        # The listener is per area. Ignore events outside its WINDOW region;
        # the listener belonging to the hovered View3D (if any) handles them.
        if (not self._dragging and not self._fan_dragging and not self._moving
                and not _mouse_in_region(event, region)):
            if getattr(self, "_cursor_shape", None) == 'SCROLL_XY':
                self._set_title_cursor(context, False)
            return {'PASS_THROUGH'}

        screen = window.screen
        mx = event.mouse_x - region.x
        my = event.mouse_y - region.y
        with context.temp_override(window=window, screen=screen, area=area, region=region):
            # The title bar is the HUD's move handle. Update the cursor on every
            # hover move, independently of the MMB drag state. The fan remains
            # its own control and therefore keeps the normal cursor.
            if (event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}
                    and not self._dragging and not self._fan_dragging and not self._moving):
                _rec, hover_layout = current_layout(context)
                over_title = False
                if hover_layout is not None:
                    tx0, ty0, tx1, ty1 = hover_layout["title"]
                    if tx0 <= mx <= tx1 and ty0 <= my <= ty1:
                        fan_cx = tx1 - (FAN_R + 5.0 * _scale())
                        fan_cy = (ty0 + ty1) / 2.0
                        fan_r = FAN_R * _scale()
                        over_fan = ((mx - fan_cx) ** 2 + (my - fan_cy) ** 2
                                    <= fan_r * fan_r * 1.6)
                        over_title = not over_fan
                self._set_title_cursor(context, over_title)

            # ESC/Q dismiss the Maya In-View HUD for the current operation.
            # Keep the key available to Blender/Maya keymaps; this listener only
            # owns HUD cleanup and must not swallow the user's cancel/tool key.
            if event.type in {'ESC', 'Q'} and event.value == 'PRESS':
                _ob, active_rec = extrude.active(context)
                if self._dragging:
                    rec = getattr(self, "_rec", None) or active_rec
                    if rec is not None and getattr(self, "_start", None) is not None:
                        try:
                            extrude.preview(
                                getattr(self, "_ob", context.edit_object),
                                rec, self._start, getattr(self, "_unit", units.maya_unit(context.scene)))
                            rec.live = False
                        except (ReferenceError, RuntimeError, AttributeError):
                            pass
                    self._dragging = False
                    self._set_cursor(context, False)
                if self._fan_dragging:
                    _state["sensitivity"] = getattr(self, "_fan_start", _state["sensitivity"])
                    from . import in_view_settings as shared
                    shared.set_sensitivity(_state["sensitivity"])
                    self._fan_dragging = False
                self._moving = False
                # The HUD may disappear while the pointer is still over its
                # title. Always release the hover cursor on dismissal.
                self._set_cursor_shape(context, None)
                if active_rec is not None:
                    active_rec.dismissed = True
                _redraw(context)
                return {'PASS_THROUGH'}

            if self._moving:
                if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
                    from . import in_view_settings as shared
                    dx = event.mouse_x - self._move_mouse[0]
                    dy = event.mouse_y - self._move_mouse[1]
                    lay = current_layout(context)[1]
                    if lay is not None:
                        scale = _scale()
                        x0, top = self._move_start
                        x = max(4 * scale, min(x0 + dx, region.width - WIDTH * scale - 4 * scale))
                        panel_h = lay["box"][3] - lay["box"][1]
                        y = max(panel_h + 4 * scale, min(top + dy, region.height - 4 * scale))
                        shared.set_position("maya_inview_hud", x, y, region)
                    _redraw(context)
                    return {'RUNNING_MODAL'}
                if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                    self._moving = False
                    _redraw(context)
                    return {'RUNNING_MODAL'}
                if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
                    self._moving = False
                    _redraw(context)
                    return {'RUNNING_MODAL'}
                return {'RUNNING_MODAL'}

            if self._fan_dragging:
                if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
                    _state["sensitivity"] = _fan_fraction_at(
                        self._fan_cx, self._fan_cy, mx, my)
                    from . import in_view_settings as shared
                    shared.set_sensitivity(_state["sensitivity"])
                    _redraw(context)
                    return {'RUNNING_MODAL'}
                if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
                    _state["sensitivity"] = self._fan_start
                    from . import in_view_settings as shared
                    shared.set_sensitivity(_state["sensitivity"])
                    self._fan_dragging = False
                    _redraw(context)
                    return {'RUNNING_MODAL'}
                if event.type == 'MIDDLEMOUSE' and event.value == 'RELEASE':
                    from . import in_view_settings as shared
                    shared.set_sensitivity(_state["sensitivity"])
                    self._fan_dragging = False
                    _redraw(context)
                    return {'RUNNING_MODAL'}
                return {'RUNNING_MODAL'}

            if not self._dragging:
                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    _rec, lay = current_layout(context)
                    if lay is not None:
                        tx0, ty0, tx1, ty1 = lay["title"]
                        if tx0 <= mx <= tx1 and ty0 <= my <= ty1:
                            # The fan remains a dedicated control; the rest of
                            # the title bar is the persistent panel move handle.
                            fan_cx = tx1 - (FAN_R + 5.0 * _scale())
                            fan_cy = (ty0 + ty1) / 2.0
                            fan_r = FAN_R * _scale()
                            if (mx - fan_cx) ** 2 + (my - fan_cy) ** 2 > fan_r * fan_r * 1.6:
                                from . import in_view_settings as shared
                                saved = shared.get_position("maya_inview_hud", region)
                                self._move_start = saved or (lay["box"][0], lay["box"][3])
                                self._move_mouse = (event.mouse_x, event.mouse_y)
                                self._moving = True
                                return {'RUNNING_MODAL'}
                    return {'PASS_THROUGH'}
                if event.type == 'MIDDLEMOUSE' and event.value == 'PRESS':
                    hit = _panel_hit(context, mx, my)
                    if hit and hit[0] == 'FAN':
                        self._fan_cx, self._fan_cy = hit[1]
                        self._fan_start = _state["sensitivity"]
                        _state["sensitivity"] = _fan_fraction_at(
                            self._fan_cx, self._fan_cy, mx, my)
                        self._fan_dragging = True
                        _redraw(context)
                        return {'RUNNING_MODAL'}

                    visible_record = record(context)
                    if visible_record[1] is not None:
                        _sync_active_record(visible_record[1])
                    # Pull the active row after record synchronization. It is
                    # -1 until a row is explicitly activated by the user.
                    self._hot = _state["hot"]
                    if hit and hit[0] == 'ROW':
                        # Both label and value zones activate the same row.
                        self._hot = hit[1]
                        _state["hot"] = self._hot
                    elif hit == 'PANEL':
                        # The title area (outside the fan) has no other control:
                        # MMB there adjusts the currently active parameter, just
                        # like the shared Tool Parameter HUD.
                        self._hot = _state["hot"]
                    else:
                        self._hot = _state["hot"]

                    if self._begin(context, event, visible_record):
                        self._dragging = True
                        return {'RUNNING_MODAL'}
                    if hit and hit[0] == 'ROW':
                        _redraw(context)
                        return {'RUNNING_MODAL'}
                return {'PASS_THROUGH'}

            if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
                if abs(event.mouse_x - self._x0) > 3 * _scale():
                    self._moved = True
                if self._moved:
                    params = dict(self._start, **{self._field: self._value(event)})
                    extrude.preview(self._ob, self._rec, params, self._unit)
                    _redraw(context)
                return {'RUNNING_MODAL'}
            if event.type == 'ESC' and event.value == 'PRESS':
                extrude.preview(self._ob, self._rec, self._start, self._unit)
                self._rec.live = False
                self._dragging = False
                self._set_cursor(context, False)
                _redraw(context)
                return {'RUNNING_MODAL'}
            if event.type == 'MIDDLEMOUSE' and event.value == 'RELEASE':
                if self._moved:
                    extrude.set_params(context, **{self._field: self._value(event)})
                self._dragging = False
                self._set_cursor(context, False)
                _redraw(context)
                return {'RUNNING_MODAL'}
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

    def _field(self, context):
        _ob, rec = extrude.active(context)
        if rec is None or self.row >= len(rec.spec.fields):
            return rec, None
        return rec, rec.spec.fields[self.row]

    def invoke(self, context, event):
        rec, field = self._field(context)
        if field is None:
            return {'CANCELLED'}
        if field in INT_FIELDS:
            self.count = int(rec.params[field])
        else:
            self.number = float(rec.params[field])
        return context.window_manager.invoke_props_dialog(self, title=f"{rec.name}: {rec.spec.labels[field]}")

    def draw(self, context):
        rec, field = self._field(context)
        if field is not None:
            self.layout.prop(self, "count" if field in INT_FIELDS else "number", text=rec.spec.labels[field])

    def execute(self, context):
        _rec, field = self._field(context)
        if field is None:
            return {'CANCELLED'}
        value = self.count if field in INT_FIELDS else clamp(field, self.number)
        res = extrude.set_params(context, **{field: value})
        _redraw(context)
        return res


class ALLSET_OT_extrude_drag(bpy.types.Operator):
    """Drag a handle of the extrude manipulator (Maya polyExtrudeFace Local Translate / Local Scale; Local
    Translate Z of an edge extrusion, Length of a vertex extrusion)"""
    bl_idname = "allset.extrude_drag"
    bl_label = "Extrude Manipulator"
    bl_options = {'INTERNAL'}

    handle: StringProperty(default="TZ", options={'SKIP_SAVE', 'HIDDEN'})

    @classmethod
    def poll(cls, context):
        rec = extrude.active(context)[1]
        return rec is not None and rec.spec.arrow is not None and context.region_data is not None

    def _ray(self, context, event):
        region, rv3d = context.region, context.region_data
        co = (event.mouse_region_x, event.mouse_region_y)
        return (view3d_utils.region_2d_to_origin_3d(region, rv3d, co),
                view3d_utils.region_2d_to_vector_3d(region, rv3d, co))

    def _along(self, context, event, axis):
        o, d = self._ray(context, event)
        hit = geometry.intersect_line_line(self._c, self._c + axis, o, o + d)
        return None if hit is None else (hit[0] - self._c).dot(axis)

    def _on_plane(self, context, event, normal):
        o, d = self._ray(context, event)
        return geometry.intersect_line_plane(o, o + d, self._c, normal)

    def _screen_dir(self, context, axis):
        region, rv3d = context.region, context.region_data
        p0 = view3d_utils.location_3d_to_region_2d(region, rv3d, self._c)
        p1 = view3d_utils.location_3d_to_region_2d(region, rv3d, self._c + axis * 1e-3)
        if p0 is None or p1 is None or (p1 - p0).length < 1e-9:
            return Vector((1.0, 0.0))
        return (p1 - p0).normalized()

    def invoke(self, context, event):
        # The persistent global MMB listener is the single owner of MMB row
        # interaction. Keep this gizmo target for LMB only; passing MMB through
        # prevents two modal operators competing for the same drag/release.
        if event.type == 'MIDDLEMOUSE':
            return {'PASS_THROUGH'}
        ob, rec = extrude.active(context)
        fields = handle_fields(rec, self.handle)
        frame = manip_frame(ob, rec) if fields else None
        if frame is None:
            return {'CANCELLED'}
        self._ob, self._rec, self._fields = ob, rec, fields
        self._c, axes, self._k = frame
        self._axes = [axes.col[i].copy() for i in range(3)]
        self._role, data, _f = HANDLES[self.handle]
        self._idx = [AXIS_INDEX[a] for a in data] if data else []
        self._start = dict(extrude.DEFAULTS, **rec.params)
        self._unit = units.maya_unit(context.scene)
        self._mouse0 = Vector((event.mouse_region_x, event.mouse_region_y))
        if self._role == 'ARROW':
            self._t0 = self._along(context, event, self._axes[self._idx[0]])
        elif self._role == 'PLANE':
            normal = self._axes[self._idx[0]].cross(self._axes[self._idx[1]])
            self._normal = normal
            self._h0 = self._on_plane(context, event, normal)
        elif self._role == 'CUBE':
            self._sdir = self._screen_dir(context, self._axes[self._idx[0]])
        self._last = {}
        self._button = event.type if event.type in {'LEFTMOUSE', 'MIDDLEMOUSE'} else 'LEFTMOUSE'
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def values(self, context, event):
        """{field: value} for the mouse at ``event`` (the press values while the drag has no reading yet)."""
        start, out = self._start, {}
        if self._role == 'ARROW':
            i = self._idx[0]
            t = self._along(context, event, self._axes[i])
            if t is None or self._t0 is None:
                return dict(self._last)
            out[self._fields[0]] = round(start[self._fields[0]] + (t - self._t0) / self._k[i] / self._unit, 4)
        elif self._role == 'PLANE':
            h = self._on_plane(context, event, self._normal)
            if h is None or self._h0 is None:
                return dict(self._last)
            d = h - self._h0
            for field, i in zip(self._fields, self._idx):
                out[field] = round(start[field] + d.dot(self._axes[i]) / self._k[i] / self._unit, 4)
        else:
            mouse = Vector((event.mouse_region_x, event.mouse_region_y))
            if self._role == 'CUBE':
                dist = (mouse - self._mouse0).dot(self._sdir)
            else:   # centre: Maya's uniform scale follows the horizontal drag
                dist = mouse.x - self._mouse0.x
            factor = 1.0 + dist / (SCALE_PX * (_scale() or 1.0))      # ui_scale reads 0 in background
            for field in self._fields:
                out[field] = round(start[field] * factor, 4)
        self._last = out
        return dict(out)

    def modal(self, context, event):
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            params = dict(self._rec.params, **self.values(context, event))
            extrude.preview(self._ob, self._rec, params, self._unit)
            if self._fields[0] in self._rec.spec.fields:
                _state["hot"] = self._rec.spec.fields.index(self._fields[0])
            _redraw(context)
            return {'RUNNING_MODAL'}
        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
            extrude.preview(self._ob, self._rec, {k: self._start[k] for k in self._rec.params}, self._unit)
            self._rec.live = False
            _redraw(context)
            return {'CANCELLED'}
        if event.type == self._button and event.value == 'RELEASE':
            changes = self.values(context, event)
            if changes:
                extrude.set_params(context, **changes)
            else:
                extrude.preview(self._ob, self._rec, {k: self._start[k] for k in self._rec.params}, self._unit)
                self._rec.live = False
            _redraw(context)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


# --- Channel Box INPUTS ------------------------------------------------------------------------------

def cb_record(context, ob):
    """The lead object's last extrusion for Channel Box INPUTS (any selection), or None."""
    if ob is None:
        return None
    if ob is not getattr(context, "edit_object", None):
        return extrude.object_record(ob)        # a node editable in object mode (UV > Automatic, step 257)
    return extrude.current(ob)


def _lead(context):
    return getattr(context, "edit_object", None) or getattr(context, "active_object", None)


def clamp(field, value):
    lo, hi = RANGES.get(field, (None, None))
    if lo is not None:
        value = max(lo, value)
    if hi is not None:
        value = min(hi, value)
    return value


def _text_get(field):
    def get(_self):
        rec = cb_record(bpy.context, _lead(bpy.context))
        if rec is None or field not in rec.params:
            return ""
        return cb_entry.format_value(rec.params[field], rec.spec.kinds[field], bpy.context.scene)
    return get


def _text_set(field):
    def set_(_self, text):
        context = bpy.context
        rec = cb_record(context, _lead(context))
        if rec is None or field not in rec.params:
            return
        try:
            value = cb_entry.parse_entry(text, rec.params[field], rec.spec.kinds[field], context.scene)
        except (ValueError, TypeError, SyntaxError, NameError):
            return
        if field in INT_FIELDS:
            value = max(1, int(value))
        elif field not in BOOL_FIELDS:
            value = clamp(field, value)
        if value != rec.params[field]:
            extrude.set_params(context, **{field: value})
    return set_


class ALLSET_PG_history(bpy.types.PropertyGroup):
    __annotations__ = {f"{f}_text": StringProperty(name=next(s.labels[f] for s in extrude.SPECS.values()
                                                             if f in s.fields),
                                                   get=_text_get(f), set=_text_set(f), options={'SKIP_SAVE'})
                       for f in ALL_FIELDS}


HISTORY_TIP = "Blender keeps no edit-mode history: only the last operation can be changed here."


def draw_cb_node(layout, context, rec):
    """The polyExtrudeFace node in Channel Box INPUTS; the Blender notice is the node name's
    tooltip (step 106: no Blender sentences in Maya windows). Collapsed until its name is clicked, like Maya
    (step 135)."""
    from . import channel_box
    lines = channel_box.as_lines(layout)
    ob = channel_box.lead(context)
    _row, opened = channel_box.node_row(lines, ob, channel_box.history_node(rec.name), rec.name, tip=HISTORY_TIP)
    if not opened:
        return
    hist = context.window_manager.allset_history
    for field in rec.spec.fields:
        row = lines.row()
        if row is None:
            continue
        split = row.split(factor=0.5, align=True)
        split.label(text=rec.spec.labels[field])
        split.prop(hist, f"{field}_text", text="")


classes = (ALLSET_PG_history, ALLSET_GT_in_view_row, ALLSET_GT_fan, ALLSET_GGT_in_view, ALLSET_GT_extrude_handle,
           ALLSET_GGT_extrude,
           ALLSET_OT_fan_drag, ALLSET_OT_inview_drag, ALLSET_OT_global_mmb,
           ALLSET_OT_inview_type, ALLSET_OT_extrude_drag)


def register():
    global _global_mmb_timer, _global_mmb_enabled
    from . import in_view_settings as shared
    _state["sensitivity"] = shared.get_sensitivity()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.allset_history = PointerProperty(type=ALLSET_PG_history)
    _state["handle"] = bpy.types.SpaceView3D.draw_handler_add(draw_box, (), 'WINDOW', 'POST_PIXEL')
    _global_mmb_enabled = True

    def _start_global_mmb():
        if not _global_mmb_enabled:
            return None
        wm = bpy.context.window_manager
        if wm is None:
            return 0.75

        now = time.monotonic()
        live_ptrs = set()
        for window in tuple(wm.windows):
            screen = window.screen
            if screen is None:
                continue
            for area in tuple(screen.areas):
                if area.type != 'VIEW_3D':
                    continue
                area_ptr = area.as_pointer()
                live_ptrs.add(area_ptr)
                region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                if region is None:
                    continue

                # The global MMB listener is needed only while this View3D
                # has a valid Maya In-View HUD record. Do not create listeners
                # merely because a View3D area exists.
                hud_active = False
                try:
                    with bpy.context.temp_override(
                        window=window, screen=screen, area=area, region=region
                    ):
                        hud_active = record(bpy.context)[1] is not None
                except (RuntimeError, TypeError, ReferenceError, AttributeError):
                    hud_active = False

                running = _global_mmb_running(window, area_ptr)
                if hud_active:
                    _global_mmb_idle_since.pop(area_ptr, None)
                    _global_mmb_expired_area_ptrs.discard(area_ptr)
                    if not running:
                        try:
                            with bpy.context.temp_override(
                                window=window, screen=screen, area=area, region=region
                            ):
                                bpy.ops.allset.global_mmb(
                                    'INVOKE_DEFAULT', owner_area=str(area_ptr))
                        except (RuntimeError, TypeError, ReferenceError):
                            continue
                elif running:
                    idle_since = _global_mmb_idle_since.setdefault(area_ptr, now)
                    if now - idle_since >= HUD_LISTENER_IDLE_TIMEOUT:
                        # Modal operators cannot be synchronously removed from
                        # window.modal_operators. Mark them for cancellation;
                        # their next event performs normal cursor/state cleanup.
                        _global_mmb_expired_area_ptrs.add(area_ptr)
                else:
                    _global_mmb_idle_since.pop(area_ptr, None)
                    _global_mmb_expired_area_ptrs.discard(area_ptr)

        # Remove state belonging to areas that no longer exist.
        _global_mmb_area_ptrs.intersection_update(live_ptrs)
        for area_ptr in tuple(_global_mmb_idle_since):
            if area_ptr not in live_ptrs:
                _global_mmb_idle_since.pop(area_ptr, None)
                _global_mmb_expired_area_ptrs.discard(area_ptr)
        _global_mmb_expired_area_ptrs.intersection_update(live_ptrs)

        return 0.75 if _global_mmb_enabled else None

    _global_mmb_timer = _start_global_mmb
    if not bpy.app.timers.is_registered(_global_mmb_timer):
        bpy.app.timers.register(_global_mmb_timer, first_interval=0.1)


def unregister():
    global _global_mmb_timer, _global_mmb_enabled
    _global_mmb_enabled = False
    _global_mmb_area_ptrs.clear()
    _global_mmb_idle_since.clear()
    _global_mmb_expired_area_ptrs.clear()
    if _global_mmb_timer is not None:
        try:
            if bpy.app.timers.is_registered(_global_mmb_timer):
                bpy.app.timers.unregister(_global_mmb_timer)
        except (ValueError, RuntimeError):
            pass
        _global_mmb_timer = None
    if _state["handle"] is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_state["handle"], 'WINDOW')
        _state["handle"] = None
    del bpy.types.WindowManager.allset_history
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
