"""Step 63 in a real UI (research/maya/workflows/modeling.md modeling_02 / 14): Status Line MTK icon -> the
Modeling Toolkit in the dock -> Face mode icon -> a face selected -> Extrude button -> more faces; cube + sphere
-> Combine button -> one pCube2 -> Separate button -> two pieces. Screenshots (vs shots/modeling_03.png)."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, px, run, screenshot, setup, step, view3d, win  # noqa: E402

SHOTS = os.environ.get("MAYA_KIT_GUI_SHOTS", "")
C = {"tries": 0}

# Measured in gui_step63_explore*.png (1600 x 900, scale 1.25, sidebar UI region (971, 94, 350, 709)):
# (px left of the sidebar's right edge, px below the top of its content).
FACE_ICON, OBJECT_ICON = (188, 90), (310, 90)
COMBINE, SEPARATE = (248, 457), (106, 457)          # object mode
EXTRUDE_EDIT = (248, 582)                            # edit mode: the "N faces selected" row adds 31 px
MTK_ICON_FROM_LEFT = 1190   # Status Line (3D View tool header, laid out from the left; it overflows at 1.25)


def shot(name):
    if SHOTS:
        screenshot(os.path.join(SHOTS, name))


def region(kind):
    return next(r for r in view3d()[0].regions if r.type == kind)


def redraw():
    for a in win().screen.areas:
        a.tag_redraw()


def point(spot):
    dx, dy = spot
    r = region('UI')
    top = r.view2d.view_to_region(0, 0, clip=False)[1]
    return r.x + r.width - px(dx), r.y + top - px(dy)


def scroll(spot):
    def s_scroll():
        r = region('UI')
        _x, y = point(spot)
        if not (r.y + 10 < y < r.y + r.height - 10) and C["tries"] < 40:
            C["tries"] += 1
            kind = 'WHEELDOWNMOUSE' if y < r.y else 'WHEELUPMOUSE'
            ev(kind, 'PRESS', x=r.x + r.width // 2, y=r.y + r.height // 2)
            sys.modules["sim"]._steps.insert(0, s_scroll)
            return
        C["tries"] = 0
        redraw()
    return s_scroll


def click_at(get_xy):
    """Hover in one tick, press in the next (a Blender button activates on hover)."""
    def s_hover():
        x, y = get_xy()
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)
        redraw()

    def s_press():
        x, y = get_xy()
        ev('LEFTMOUSE', 'PRESS', x=x, y=y)
        ev('LEFTMOUSE', 'RELEASE', x=x, y=y)
    return [s_hover, s_press]


def click(spot):
    return [scroll(spot), *click_at(lambda: point(spot))]


def steps(*fns):
    for fn in fns:
        for f in (fn if isinstance(fn, list) else [fn]):
            step(f)


def meshes():
    return sorted(o.name for o in bpy.context.scene.objects if o.type == 'MESH')


def s_setup():
    setup()
    bpy.data.objects["Cube"].name = "pCube1"
    view3d()[0].spaces.active.show_region_ui = True
    bpy.context.window_manager.maya_kit_dock = 'CHANNEL_BOX'
    redraw()


def mtk_icon():
    r = region('TOOL_HEADER')
    return r.x + px(MTK_ICON_FROM_LEFT), r.y + r.height // 2


def s_check_dock():
    wm = bpy.context.window_manager
    check(f"Status Line MTK icon -> Modeling Toolkit in the dock (got {wm.maya_kit_dock})",
          wm.maya_kit_dock == 'MODELING_TOOLKIT')
    redraw()


def s_check_face_mode():
    ts = bpy.context.scene.tool_settings
    check(f"MTK Face icon -> edit mode, face selection (got {bpy.context.mode}, {tuple(ts.mesh_select_mode)})",
          bpy.context.mode == 'EDIT_MESH' and tuple(ts.mesh_select_mode) == (False, False, True))
    import bmesh
    bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
    for f in bm.faces:
        f.select_set(f.index == 0)
    bmesh.update_edit_mesh(bpy.context.active_object.data)
    redraw()


def s_shot_edit():
    shot("gui_step63_mtk_edit.png")


def s_check_extrude():
    ob = bpy.context.active_object
    ob.update_from_editmode()
    n = len(ob.data.polygons)
    check(f"MTK Extrude: one face extruded, 6 -> {n} faces", n == 10)
    check(f"... and the Move manipulator is on (tool {bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname})",
          bpy.context.workspace.tools.from_space_view3d_mode('EDIT_MESH').idname == "builtin.move")


def s_check_object_mode():
    check(f"MTK Object icon -> object mode (got {bpy.context.mode})", bpy.context.mode == 'OBJECT')
    bpy.ops.maya_kit.create(kind='SPHERE')
    sphere = bpy.context.active_object
    sphere.location.x = 3.0
    cube = bpy.data.objects["pCube1"]
    cube.select_set(True)
    sphere.select_set(True)
    bpy.context.view_layer.objects.active = sphere
    redraw()


def s_check_combine():
    check(f"MTK Combine: one mesh pCube2 (got {meshes()})", meshes() == ["pCube2"])
    redraw()


def s_check_separate():
    grp = bpy.data.objects.get("pCube2")
    kids = sorted(c.name for c in grp.children) if grp else []
    check(f"MTK Separate: pCube2 group with two pieces (got {kids})",
          grp is not None and grp.type == 'EMPTY' and kids == ["polySurface1", "polySurface2"])
    redraw()


def s_shot_end():
    shot("gui_step63_mtk_object.png")
    area, win_region = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=win_region.x + win_region.width // 2, y=win_region.y + win_region.height // 2)
    from importlib import import_module
    modal = import_module(sys.modules["sim"].MODULE + ".marking.modal")
    menu_map = import_module(sys.modules["sim"].MODULE + ".ui.menu_map")
    with bpy.context.temp_override(window=win(), area=area, region=win_region):
        C["mirror"] = modal.run_action(bpy.context, menu_map.MAP["Mesh/Mirror"], option=True)   # Mesh > Mirror □


def s_wait_dialog():
    redraw()


def s_shot_dialog():
    shot("gui_step63_mirror_options.png")
    check(f"Mesh > Mirror option box opens the Mirror Options dialog (got {C.get('mirror')})",
          C.get("mirror") == {'RUNNING_MODAL'})
    ev('ESC', 'PRESS')
    ev('ESC', 'RELEASE')


steps(s_setup, *click_at(mtk_icon), s_check_dock,
      click(FACE_ICON), s_check_face_mode, s_shot_edit,
      click(EXTRUDE_EDIT), s_check_extrude,
      click(OBJECT_ICON), s_check_object_mode,
      click(COMBINE), s_check_combine,
      click(SEPARATE), s_check_separate, s_shot_end, s_wait_dialog, s_shot_dialog)

run()
