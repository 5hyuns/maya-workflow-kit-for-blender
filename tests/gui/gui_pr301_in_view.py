"""#301 In-View Editor in a real UI: top face -> Ctrl+E -> polyExtrudeFace1 with its first number row (Thickness)
selected -> a plain middle drag in an empty part of the view changes it (like Maya) -> Alt+middle drag pans and
changes nothing -> a middle drag over another row changes that row and selects it -> a middle click on a row only
selects it (no entry window; an On / Off row keeps its value) -> dragging the title moves the box (kept offset) -> a click on the drag-speed pie
slows the next middle drag down."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, px, run, setup, step, view3d, win  # noqa: E402

C = {}


def mod(name):
    return import_module(sys.modules["sim"].MODULE + name)


def iv():
    return mod(".ui.in_view")


def cube():
    return bpy.data.objects["Cube"]


def rec():
    return mod(".operators.extrude").active(bpy.context)[1]


def scale():
    return bpy.context.preferences.system.ui_scale


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def v3d_ctx():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region, space_data=area.spaces.active)


def box():
    """(layout in window px, region) of the In-View Editor of the view."""
    _area, region = view3d()
    with v3d_ctx():
        _r, lay = iv().current_layout(bpy.context)
    return lay, region


def row_point(field):
    lay, region = box()
    for f, x0, y0, x1, y1 in lay["rows"]:
        if f == field:
            return region.x + round((x0 + x1) / 2), region.y + round((y0 + y1) / 2)
    return None


def mmb_drag(x, y, dx, **mods):
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('MIDDLEMOUSE', 'PRESS', x=x, y=y, **mods)
    for i in range(1, 9):
        ev('MOUSEMOVE', 'NOTHING', x=x + dx * i // 8, y=y, **mods)
    ev('MIDDLEMOUSE', 'RELEASE', x=x + dx, y=y, **mods)


@step
def s_setup():
    C["x"], C["y"] = setup()
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    with v3d_ctx():
        bpy.ops.object.mode_set('EXEC_DEFAULT', True, mode='EDIT')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    bm = bmesh.from_edit_mesh(cube().data)
    for f in bm.faces:
        f.select_set(False)
    for f in bm.faces:
        if f.normal.z > 0.9:
            f.select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(cube().data)
    C["empty"] = (C["x"] - px(200), C["y"] - px(150))     # left of / below the cube, away from the box
    ev('MOUSEMOVE', 'NOTHING', x=C["empty"][0], y=C["empty"][1])
    redraw()


@step
def s_ctrl_e():
    ev('E', 'PRESS', ctrl=True)
    ev('E', 'RELEASE', ctrl=True)


@step
def s_shown():
    r = rec()
    lay, _region = box()
    hot = iv()._state["hot"]
    check(f"Ctrl+E: polyExtrudeFace1 and its In-View Editor ({r and r.name}, box {lay is not None})",
          r is not None and r.name == "polyExtrudeFace1" and lay is not None)
    check(f"its first number row is the selected one ({hot} = Thickness)",
          r is not None and r.spec.view_fields[hot] == "thickness")
    C["start"] = dict(r.params) if r else {}
    mmb_drag(*C["empty"], round(50 * scale()))


@step
def s_plain_mmb():
    r = rec()
    t = r.params["thickness"] if r else None
    check(f"a plain middle drag in an empty part of the view changes the selected row: Thickness 0 -> 0.5 ({t})",
          t is not None and abs(t - 0.5) < 0.02)
    C["t"] = t
    C["view"] = tuple(view3d()[0].spaces.active.region_3d.view_location)
    mmb_drag(*C["empty"], round(50 * scale()), alt=True)


@step
def s_alt_mmb():
    r = rec()
    view = tuple(view3d()[0].spaces.active.region_3d.view_location)
    check(f"Alt+middle drag pans the view and leaves the values ({r and r.params['thickness']}, view moved "
          f"{view != C['view']})", r is not None and r.params["thickness"] == C["t"] and view != C["view"])
    x, y = row_point("offset")
    C["offset0"] = r.params["offset"]
    mmb_drag(x, y, round(30 * scale()))


@step
def s_row_mmb():
    r = rec()
    hot = iv()._state["hot"]
    check(f"a middle drag over the Offset row changes Offset and selects that row ({C['offset0']} -> "
          f"{r and r.params['offset']}, selected {r and r.spec.view_fields[hot]})",
          r is not None and abs(r.params["offset"] - C["offset0"] - 0.3) < 0.02 and r.spec.view_fields[hot] == "offset"
          and abs(r.params["thickness"] - C["t"]) < 1e-6)
    cls = iv().ALLSET_OT_inview_type
    C["typed"], C["type_invoke"] = [], cls.__dict__["invoke"]

    def invoke(op, context, event):
        C["typed"].append(op.row)
        return C["type_invoke"](op, context, event)
    cls.invoke = invoke
    C["values"] = dict(r.params)
    x, y = row_point("divisions")
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('MIDDLEMOUSE', 'PRESS', x=x, y=y)
    ev('MIDDLEMOUSE', 'RELEASE', x=x, y=y)


@step
def s_mmb_click():
    iv().ALLSET_OT_inview_type.invoke = C["type_invoke"]
    r = rec()
    hot = iv()._state["hot"]
    check(f"a middle click on Divisions selects it, opens no entry window, changes nothing "
          f"({r and r.spec.view_fields[hot]}, typed {C['typed']})",
          r is not None and r.spec.view_fields[hot] == "divisions" and not C["typed"] and r.params == C["values"])
    x, y = row_point("keep_faces_together")
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('MIDDLEMOUSE', 'PRESS', x=x, y=y)
    ev('MIDDLEMOUSE', 'RELEASE', x=x, y=y)


@step
def s_mmb_switch():
    r = rec()
    hot = iv()._state["hot"]
    check(f"a middle click on Keep Faces Together selects it and leaves it as it was "
          f"({r and r.spec.view_fields[hot]}, {r and r.params['keep_faces_together']})",
          r is not None and r.spec.view_fields[hot] == "keep_faces_together" and r.params == C["values"])
    lay, region = box()
    x0, y0, x1, y1 = lay["title"]
    C["box0"] = lay["box"]
    x, y = region.x + round(x0 + 20 * scale()), region.y + round((y0 + y1) / 2)
    d = round(40 * scale())
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    for i in range(1, 9):
        ev('MOUSEMOVE', 'NOTHING', x=x + d * i // 8, y=y + d // 2 * i // 8)
    ev('LEFTMOUSE', 'RELEASE', x=x + d, y=y + d // 2)


@step
def s_title_drag():
    lay, _region = box()
    off = mod(".ui.in_view_settings").get_offset()
    moved = (lay["box"][0] - C["box0"][0], lay["box"][3] - C["box0"][3])
    check(f"dragging the title moves the box by the drag and keeps it as an offset (moved {moved}, offset {off})",
          abs(moved[0] - round(40 * scale())) <= 2 and abs(moved[1] - round(40 * scale()) // 2) <= 2
          and abs(off[0] - 40) <= 2 and abs(off[1] - 20) <= 2)
    r = rec()
    C["values"] = dict(r.params)
    cx, cy, rad = iv().fan_circle(lay, scale())
    _area, region = view3d()
    x, y = region.x + round(cx - rad * 0.6), region.y + round(cy)       # nine o'clock: a twelfth of the pie
    ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
    ev('LEFTMOUSE', 'PRESS', x=x, y=y)
    ev('LEFTMOUSE', 'RELEASE', x=x, y=y)


@step
def s_pie():
    sens = mod(".ui.in_view_settings").get_sensitivity()
    r = rec()
    check(f"a click at nine o'clock on the pie sets the drag speed to a twelfth ({sens:.3f}), values unchanged",
          abs(sens - 30 / 360) < 0.05 and r is not None and r.params == C["values"])
    C["sens"] = sens
    C["t"] = r.params["thickness"]
    x, y = row_point("thickness")
    mmb_drag(x, y, round(50 * scale()))


@step
def s_slow_drag():
    r = rec()
    t = r.params["thickness"] if r else None
    want = 0.5 * (0.02 + 0.98 * C["sens"])
    check(f"the next middle drag is that much slower: Thickness +{t - C['t']:.3f} (+{want:.3f}, full speed +0.5)",
          t is not None and abs((t - C["t"]) - want) < 0.02)
    settings = mod(".ui.in_view_settings")
    settings.set_sensitivity(1.0)
    settings.set_offset(0.0, 0.0)


run()
