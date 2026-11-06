"""#321: moving UV shells in the UV Editor (UV Shell selection, Tools > Move UV Shell) keeps Blender running, moves
the shell and keeps it selected. Drags here: the Select Tool (q) from a shell, two Move Tool (w)
drags, Tools > Move UV Shell, Ctrl+Z. A crash ends the run without results (the runner reports it)."""

import os
import sys
from importlib import import_module

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, run, setup, step, load_maya_layout  # noqa: E402

GUI_TIMEOUT = 240
C = {"pos": {}}


def uv_window():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type == 'IMAGE_EDITOR' and a.ui_type == 'UV':
                return w, a, next(r for r in a.regions if r.type == 'WINDOW')
    return None, None, None


def uev(type, value, x=None, y=None, **kw):
    w, _a, _r = uv_window()
    p = C["pos"].setdefault(w.as_pointer(), [0, 0])
    if x is not None:
        p[:] = [int(x), int(y)]
    w.event_simulate(type=type, value=value, x=p[0], y=p[1], **kw)


def uv_px(u, v):
    _w, _a, r = uv_window()
    x, y = r.view2d.view_to_region(u, v, clip=False)
    return r.x + x, r.y + y


def face_centre(k):
    bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
    bm.faces.ensure_lookup_table()
    uv = bm.loops.layers.uv.active
    f = bm.faces[k]
    return uv_px(sum(l[uv].uv.x for l in f.loops) / len(f.loops), sum(l[uv].uv.y for l in f.loops) / len(f.loops))


def selected_faces():
    return {f.index for f in bmesh.from_edit_mesh(bpy.context.edit_object.data).faces if f.select}


def uv_sum():
    bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
    uv = bm.loops.layers.uv.active
    return sum(l[uv].uv.x + l[uv].uv.y for f in bm.faces for l in f.loops)


def uv_op(idname, **props):
    w, a, r = uv_window()
    mod, name = idname.split(".")
    with bpy.context.temp_override(window=w, area=a, region=r):
        return getattr(getattr(bpy.ops, mod), name)('EXEC_DEFAULT', **props)


def tool(idname):
    w, a, r = uv_window()
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.wm.tool_set_by_id(name=idname, space_type='IMAGE_EDITOR')


def add(fn, name):
    fn.__name__ = name
    step(fn)


@step
def s_setup():
    setup()
    load_maya_layout()


@step
def s_cube():
    from sim import view3d
    area, r = view3d()
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0], area=area, region=r):
        bpy.ops.allset.create(kind='CUBE')
        bpy.ops.object.mode_set(mode='EDIT')
        uvt = import_module(MODULE + ".operators.uv_tools")
        ob = bpy.context.edit_object
        bm = bmesh.from_edit_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        uvt.cut(bm, bm.loops.layers.uv.active, list(bm.faces[1].edges))     # the top face = a shell of its own
        bmesh.update_edit_mesh(ob.data)
        bpy.ops.mesh.select_all(action='DESELECT')
    check("cube in edit mode", bpy.context.mode == 'EDIT_MESH')


@step
def s_workspace():
    sw = import_module(MODULE + ".switch")
    C["ws"] = sw.append_workspace(bpy.context.window_manager.windows[0], "UV Editing")
    check("Maya UV Editing workspace", C["ws"] is not None)


@step
def s_wait_ws():
    pass


@step
def s_frame():
    w, a, r = uv_window()
    check("a UV Editor in the main window", w is not None)
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.image.view_all(fit_view=True)
    uv_op("allset.uv_component", mode='SHELL')


def pick_shell(tag, face):
    add(lambda: uev('MOUSEMOVE', 'NOTHING', *face_centre(face)), f"{tag}_hover")
    add(lambda: uev('LEFTMOUSE', 'PRESS'), f"{tag}_press")
    add(lambda: uev('LEFTMOUSE', 'RELEASE'), f"{tag}_release")
    add(lambda: C.update(shell=selected_faces()), f"{tag}_keep")


def drag(tag, start, dx, dy, button='LEFTMOUSE', n=8, moves=True):
    box = {}
    add(lambda: (box.update(p=start()), uev('MOUSEMOVE', 'NOTHING', *box["p"])), f"{tag}_hover")
    add(lambda: (box.update(sum=uv_sum()), uev(button, 'PRESS')), f"{tag}_press")
    for k in range(n):
        add(lambda k=k: uev('MOUSEMOVE', 'NOTHING', box["p"][0] + dx * (k + 1) / n, box["p"][1] + dy * (k + 1) / n),
            f"{tag}_move{k}")
    for k in range(4):              # the move still runs: let the kit's timers tick meanwhile
        add(lambda: None, f"{tag}_hold{k}")
    add(lambda: uev(button, 'RELEASE'), f"{tag}_release")
    add(lambda: None, f"{tag}_settle")
    add(lambda: None, f"{tag}_settle2")
    if moves:
        add(lambda: check(f"{tag}: the shell moved, Blender alive, selection kept "
                          f"({len(selected_faces())} faces)",
                          abs(uv_sum() - box["sum"]) > 1e-4 and selected_faces() == C["shell"]), f"{tag}_check")
    else:
        add(lambda: check(f"{tag}: Blender alive", True), f"{tag}_check")


pick_shell("pick", 0)
add(lambda: check(f"a shell is selected ({sorted(C['shell'])})", C["shell"] == {0, 4, 5}), "s_picked")
add(lambda: tool("builtin.move"), "w_tool")
drag("w_drag", lambda: face_centre(0), -40, 25)
drag("w_drag_again", lambda: face_centre(0), 30, -20)
add(lambda: tool("builtin.select_box"), "q_tool")
drag("q_drag", lambda: face_centre(0), 50, 20, moves=False)
add(lambda: uv_op("allset.uv_move_shell"), "move_shell_tool")
pick_shell("pick_tool", 0)
drag("move_shell_tool_drag", lambda: face_centre(0), 30, -20)


@step
def s_undo():
    w, a, r = uv_window()
    before = uv_sum()
    with bpy.context.temp_override(window=w, area=a, region=r):
        bpy.ops.ed.undo()
    check("Ctrl+Z undoes the last move", abs(uv_sum() - before) > 1e-4)


run()
