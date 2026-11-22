"""#458 in a real UI: the Maya layout's panels keep what the user set across a Maya | Blender round trip and across
saving and opening the file again. The user's steps: the viewport background set to a colour of their own, the grid
off, the viewport split into two panels (perspective + side). Cases: a Blender file in Maya mode, the file saved in
Blender mode and opened again, the file saved in Maya mode and opened again, a new Maya scene, and the Four View."""

import os
import sys
from importlib import import_module

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, load_maya_layout, run, setup, step, win  # noqa: E402

TMP = bpy.app.tempdir or os.environ.get("TEMP", ".")
SAVED_BLENDER = os.path.join(TMP, "gui_issue458_blender_mode.blend")
SAVED_MAYA = os.path.join(TMP, "gui_issue458_maya_mode.blend")
BLUE = (0.2, 0.3, 0.6)
C = {}


def mod(name):
    return import_module(MODULE + "." + name)


def sw():
    return mod("switch")


def panes():
    """The Maya layout's panels (3D Views, the Tool Box column left out), left to right."""
    return sorted(mod("ui.four_view").panes(win().screen), key=lambda a: (a.x, -a.y))


def look():
    """What the user set, per panel: width share, background, grid shown, perspective / ortho."""
    ps = panes()
    total = sum(a.width for a in ps) or 1
    grid = mod("ui.maya_grid")
    out = []
    for a in ps:
        space = a.spaces.active
        rv3d = space.region_3d
        out.append({"share": round(a.width / total, 2), "bg": space.shading.background_type,
                    "color": [round(c, 3) for c in space.shading.background_color],
                    "grid": grid.visible(space), "view": rv3d.view_perspective if rv3d else None})
    return out


def same(a, b):
    if len(a) != len(b):
        return False
    for p, q in zip(a, b):
        if abs(p["share"] - q["share"]) > 0.03 or any(p[k] != q[k] for k in ("bg", "color", "grid", "view")):
            return False
    return True


def split_main():
    """Background of the user's own colour in every view, grid off, the viewport split in two (the new panel on the
    right)."""
    mod("operators.key_batch3").apply_background("CUSTOM", BLUE)
    main = max(panes(), key=lambda a: a.width * a.height)
    mod("ui.maya_grid").set_grid(main.spaces.active, False)
    new = mod("ui.four_view")._split(bpy.context, win(), main, 'VERTICAL', 0.6)
    check("the viewport splits in two", new is not None)


def side_panel():
    """The right panel shows the side view, grid off."""
    fv = mod("ui.four_view")
    right = panes()[-1]
    space = right.spaces.active
    rv3d = space.region_3d
    rv3d.view_perspective = 'ORTHO'
    rv3d.view_rotation = fv.AXIS["side"]
    mod("ui.maya_grid").set_grid(space, False)
    for a in panes():
        a.tag_redraw()


def expect(name, key="set"):
    now = look()
    check(f"{name}: the panels as the user set them ({C[key]} -> {now})", same(now, C[key]))


@step
def s_setup():
    setup()
    win().workspace = bpy.data.workspaces["Layout"]
    sw().set_mode(True)


@step
def s_maya():
    check(f"Maya layout ({win().workspace.name})", sw().is_maya_workspace(win().workspace))
    main = max(panes(), key=lambda a: a.width * a.height)
    mod("ui.four_view").set_layout(bpy.context, win(), True, main)


@step
def s_wait0():
    pass


@step
def s_four():
    check(f"the Four View ({len(panes())} panels)", mod("ui.four_view").is_four(win().screen))
    C["four"] = look()
    sw().set_mode(False)


@step
def s_four_blender():
    sw().set_mode(True)


@step
def s_wait_f1():
    pass


@step
def s_wait_f2():
    pass


@step
def s_wait_f3():
    pass


@step
def s_four_again():
    check(f"after Blender and back: the Four View again ({len(panes())} panels)",
          mod("ui.four_view").is_four(win().screen))
    expect("the Four View after Blender and back", "four")
    mod("ui.four_view").set_layout(bpy.context, win(), False)


@step
def s_wait_f4():
    pass


@step
def s_one():
    check(f"one panel again ({len(panes())})", len(panes()) == 1)
    split_main()


@step
def s_side():
    side_panel()


@step
def s_record():
    C["set"] = look()
    check(f"two panels, user's background, grid off ({C['set']})",
          len(C["set"]) == 2 and all(p["bg"] == 'VIEWPORT' and not p["grid"] for p in C["set"]))
    sw().set_mode(False)


@step
def s_blender():
    check(f"Blender mode ({win().workspace.name})", not sw().is_maya_workspace(win().workspace))
    sw().set_mode(True)


@step
def s_wait1():
    pass


@step
def s_wait2():
    pass


@step
def s_round_trip():
    check(f"Maya layout again ({win().workspace.name})", sw().is_maya_workspace(win().workspace))
    expect("after Blender and back")
    sw().set_mode(False)


@step
def s_save_blender():
    check(f"no Maya workspace among Blender's tabs ({[w.name for w in bpy.data.workspaces]})",
          not any(sw().is_maya_workspace(w) for w in bpy.data.workspaces if w != win().workspace))
    bpy.ops.wm.save_as_mainfile(filepath=SAVED_BLENDER)
    bpy.ops.wm.open_mainfile(filepath=SAVED_BLENDER)


@step
def s_opened_blender():
    check(f"the file saved in Blender mode opens in Blender ({win().workspace.name})",
          not sw().is_maya_workspace(win().workspace))
    sw().set_mode(True)


@step
def s_wait3():
    pass


@step
def s_wait4():
    pass


@step
def s_after_blender_save():
    check(f"Maya layout ({win().workspace.name})", sw().is_maya_workspace(win().workspace))
    expect("saved in Blender mode, opened and back to Maya")
    bpy.ops.wm.save_as_mainfile(filepath=SAVED_MAYA)
    bpy.ops.wm.open_mainfile(filepath=SAVED_MAYA)


@step
def s_wait5():
    pass


@step
def s_wait6():
    pass


@step
def s_after_maya_save():
    check(f"the file saved in Maya mode opens in the Maya layout ({win().workspace.name})",
          sw().is_maya_workspace(win().workspace))
    expect("saved in Maya mode and opened")
    load_maya_layout()                     # File > New Scene in Maya mode


@step
def s_new_scene():
    check(f"a new Maya scene ({win().workspace.name}, {bpy.data.filepath!r})",
          sw().is_maya_workspace(win().workspace) and not bpy.data.filepath)
    C["new"] = look()
    split_main()


@step
def s_new_side():
    side_panel()


@step
def s_new_record():
    C["set"] = look()
    sw().set_mode(False)


@step
def s_new_blender():
    check(f"Blender mode, no Maya workspace left ({[w.name for w in bpy.data.workspaces]})",
          not any(sw().is_maya_workspace(w) for w in bpy.data.workspaces if w != win().workspace))
    sw().set_mode(True)


@step
def s_wait12():
    pass


@step
def s_wait13():
    pass


@step
def s_new_again():
    expect("a new Maya scene after Blender and back")
    for path in (SAVED_BLENDER, SAVED_MAYA):
        if os.path.exists(path):
            os.remove(path)


run()
