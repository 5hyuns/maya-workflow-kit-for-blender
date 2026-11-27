"""#579 in the UV Editor with UV Sync Selection off: a click on one UV moves the Move tool's manipulator to that UV at
once (no move needed first), and with soft select on the UVs around the selection get the soft select colours."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, screenshot, setup, step, view3d, win  # noqa: E402

C = {}
SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")


def mod(name):
    return import_module(MODULE + name)


def cube():
    return bpy.data.objects["Cube"]


def uv_region():
    area = C["uv_area"]
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def uv_px(u, v):
    """Window pixels of UV (u, v)."""
    _area, region = uv_region()
    x, y = region.view2d.view_to_region(u, v, clip=False)
    return region.x + x, region.y + y


def in_uv(fn):
    area, region = uv_region()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        return fn()


def picked_uvs():
    bm = bmesh.from_edit_mesh(cube().data)
    return {tuple(round(c, 5) for c in l[bm.loops.layers.uv.active].uv)
            for f in bm.faces for l in f.loops if l.uv_select_vert}


@step
def s_setup():
    setup()
    bpy.context.view_layer.objects.active = cube()
    cube().select_set(True)
    area, region = view3d()
    with bpy.context.temp_override(window=win(), area=area, region=region):
        bpy.ops.object.mode_set('EXEC_DEFAULT', True, mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
    uv = max((a for a in win().screen.areas if a.type == 'PROPERTIES'), key=lambda a: a.height)
    uv.type = 'IMAGE_EDITOR'
    uv.ui_type = 'UV'
    C["uv_area"] = uv
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = False
    ts.uv_select_mode = 'VERTEX'
    mod(".operators.soft_select").set_on(False)


@step
def s_frame():
    in_uv(lambda: bpy.ops.image.view_all(fit_view=True))
    in_uv(lambda: bpy.ops.uv.select_all(action='SELECT'))
    in_uv(lambda: bpy.ops.wm.tool_set_by_id(name="builtin.move", space_type='IMAGE_EDITOR'))
    C["uv_area"].tag_redraw()


@step
def s_wait():
    C["uv_area"].tag_redraw()


@step
def s_all_check():
    _area, region = uv_region()
    got = mod(".ui.uv_manipulator").LAST.get(region.as_pointer())
    check(f"the manipulator is drawn for the whole selection ({got})", got is not None)
    # a corner UV of the unwrapped cube: the one with the largest u + v
    bm = bmesh.from_edit_mesh(cube().data)
    uv = bm.loops.layers.uv.active
    C["target"] = max((tuple(l[uv].uv) for f in bm.faces for l in f.loops), key=lambda p: p[0] + p[1])
    x, y = uv_px(*C["target"])
    C["click"] = (x, y)
    ev('MOUSEMOVE', 'NOTHING', x=int(x), y=int(y))


@step
def s_click():
    x, y = C["click"]
    ev('LEFTMOUSE', 'PRESS', x=int(x), y=int(y))
    ev('LEFTMOUSE', 'RELEASE', x=int(x), y=int(y))


@step
def s_click_wait():
    pass


@step
def s_click_check():
    t = tuple(round(c, 5) for c in C["target"])
    check(f"the click picks that one UV ({picked_uvs()})", picked_uvs() == {t})
    _area, region = uv_region()
    got = mod(".ui.uv_manipulator").LAST.get(region.as_pointer())
    want = region.view2d.view_to_region(*C["target"], clip=False)
    check(f"the manipulator moves to the picked UV at once ({got} vs {want})",
          got is not None and abs(got[0] - want[0]) <= 2 and abs(got[1] - want[1]) <= 2)

    x, y = C["click"]
    bpy.context.scene.tool_settings.proportional_size = 0.3
    ev('B', 'PRESS', x=int(x), y=int(y))
    ev('B', 'RELEASE', x=int(x), y=int(y))


@step
def s_soft_wait():
    C["uv_area"].tag_redraw()


@step
def s_soft_check():
    overlay = mod(".ui.uv_soft_overlay")
    check("B turned soft select on", mod(".operators.soft_select").is_on())
    sts = [st for st in overlay._cache.values() if st.w is not None]
    n = sum(int((st.w > 0).sum()) for st in sts)
    full = sum(int((st.w >= 1).sum()) for st in sts)
    check(f"the UV Editor draws soft select colours around the picked UV ({n} UVs, {full} at full weight)",
          n > full > 0 and any(len(st.seg) for st in sts))
    if SHOTS:
        screenshot(os.path.join(SHOTS, "gui_issue579_uv_soft.png"))


run()
