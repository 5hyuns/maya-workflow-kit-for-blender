"""#422 in a real UI, more cases: selection inside Isolate Select (Ctrl+1) works like Maya after F11 into face mode,
with the Lasso and Paint (circle) select tools, after Ctrl+1 pressed twice, after H / Shift+H, on meshes with a
Subdivision Surface, a Mirror or an Armature modifier, on a linked duplicate, on the child of an isolated group, on a
collection instance, and in a file saved while isolated and opened again.
ALLSET_422_LAYOUT=maya: the Maya layout; ALLSET_422_PRESET=ic: the Industry Compatible keymap active;
ALLSET_422_SELECT=RIGHT: Select With Right Mouse."""

import math
import os
import sys
import tempfile
from importlib import import_module

import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, load_maya_layout, run, setup, step, win  # noqa: E402

MAYA_LAYOUT = os.environ.get("ALLSET_422_LAYOUT", "") == "maya"
PRESET = os.environ.get("ALLSET_422_PRESET", "")
SELECT = os.environ.get("ALLSET_422_SELECT", "")
C = {"u": 1.0}


def mod(name):
    return import_module(MODULE + name)


def windows():
    return list(bpy.context.window_manager.windows)


def view3d(window=None):
    window = window or win()
    area = max((a for a in window.screen.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height)
    return area, next(r for r in area.regions if r.type == 'WINDOW')


def space():
    return view3d()[0].spaces.active


def override(window=None):
    window = window or win()
    area, region = view3d(window)
    return bpy.context.temp_override(window=window, screen=window.screen, area=area, region=region)


def wev(window, type, value, **kw):
    window.event_simulate(type=type, value=value, **kw)


def key(k, **mods):
    ev(k, 'PRESS', **mods)
    ev(k, 'RELEASE', **mods)


def mkey(k, ctrl=False, shift=False):
    """A key with its modifier keys pressed and released around it (a modifier flag alone stays held)."""
    held = (['LEFT_CTRL'] if ctrl else []) + (['LEFT_SHIFT'] if shift else [])
    for m in held:
        ev(m, 'PRESS')
    key(k, ctrl=ctrl, shift=shift)
    for m in reversed(held):
        ev(m, 'RELEASE')


def ctrl_one():
    """Ctrl+1 with the Ctrl key itself pressed and released, the mouse over the viewport."""
    _a, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + int(r.height * 0.92))
    ev('LEFT_CTRL', 'PRESS')
    key('ONE', ctrl=True)
    ev('LEFT_CTRL', 'RELEASE')


def park():
    _a, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + int(r.height * 0.92))


def screen_xy(co, window=None):
    area, region = view3d(window)
    p = view3d_utils.location_3d_to_region_2d(region, area.spaces.active.region_3d, Vector(co) * C["u"])
    return region.x + int(round(p.x)), region.y + int(round(p.y))


def click(xy, **mods):
    ev('MOUSEMOVE', 'NOTHING', x=xy[0], y=xy[1])
    ev('LEFTMOUSE', 'PRESS', x=xy[0], y=xy[1], **mods)
    ev('LEFTMOUSE', 'RELEASE', x=xy[0], y=xy[1], **mods)


def drag_path(points):
    a = points[0]
    ev('MOUSEMOVE', 'NOTHING', x=a[0], y=a[1])
    ev('LEFTMOUSE', 'PRESS', x=a[0], y=a[1])
    for p, q in zip(points, points[1:]):
        for i in range(1, 7):
            ev('MOUSEMOVE', 'NOTHING', x=p[0] + (q[0] - p[0]) * i // 6, y=p[1] + (q[1] - p[1]) * i // 6)
    b = points[-1]
    ev('LEFTMOUSE', 'RELEASE', x=b[0], y=b[1])


def box_around(center, half=1.3):
    cx, cy, cz = center
    pts = [screen_xy((cx + dx, cy + dy, cz + dz)) for dx in (-half, half) for dy in (-half, half) for dz in (-half, half)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs) - 25, max(ys) + 25), (max(xs) + 25, min(ys) - 25)


def rel(fx, fy):
    _a, r = view3d()
    return r.x + int(r.width * fx), r.y + int(r.height * fy)


def selected():
    return sorted(o.name for o in bpy.context.scene.objects if o.select_get())


def picked_faces():
    ob = bpy.context.edit_object
    if ob is None:
        return None
    bm = bmesh.from_edit_mesh(ob.data)
    return sorted(f.index for f in bm.faces if f.select)


def clear_faces():
    for ob in bpy.context.objects_in_mode or ():
        if ob.type == 'MESH':
            bm = bmesh.from_edit_mesh(ob.data)
            for f in bm.faces:
                f.select_set(False)
            bm.select_flush(False)
            bmesh.update_edit_mesh(ob.data)


def to_object_mode():
    with override():
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')


def leave_isolate():
    sp = space()
    if sp.local_view is not None:
        with override():
            bpy.ops.view3d.localview(frame_selected=False)


def pick_only(*names):
    for o in bpy.context.scene.objects:
        if o is not None:
            o.select_set(o.name in names)
    bpy.context.view_layer.objects.active = bpy.data.objects[names[0]] if names else None


def cube(name, x, y=0.0, size=2.0):
    u = C["u"]
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size * u)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = (x * u, y * u, 0)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def idle(n=1):
    for _ in range(n):
        step(lambda: None)


def act(fn):
    step(fn)
    idle()


# --- setup --------------------------------------------------------------------------------------------------------

@step
def s_setup():
    setup()
    if MAYA_LAYOUT:
        load_maya_layout()


idle()


@step
def s_prefs():
    if PRESET == "ic":
        path = os.path.join(bpy.utils.system_resource('SCRIPTS'), "presets", "keyconfig", "Industry_Compatible.py")
        with override():
            bpy.ops.preferences.keyconfig_activate(filepath=path)
    if SELECT == "RIGHT":
        kc = bpy.context.window_manager.keyconfigs.active
        prefs = getattr(kc, "preferences", None)
        if prefs is not None and hasattr(prefs, "select_mouse"):
            prefs.select_mouse = 'RIGHT'


idle(4)        # the kit's keymap watch re-applies to the new keyconfig


@step
def s_scene():
    check(f"keymap preset ({bpy.context.window_manager.keyconfigs.active.name})", True)
    check("Maya keymap applied", mod(".keymap").is_applied())
    if SELECT == "RIGHT":
        prefs = getattr(bpy.context.window_manager.keyconfigs.active, "preferences", None)
        check(f"Select With Right ({getattr(prefs, 'select_mouse', None)})",
              getattr(prefs, "select_mouse", None) == 'RIGHT')
    for ob in list(bpy.data.objects):
        if ob.type in {'MESH', 'ARMATURE', 'EMPTY'}:
            bpy.data.objects.remove(ob)
    sc = bpy.context.scene
    C["u"] = mod(".operators.units").maya_unit(sc)
    for name, x in (("pCube1", -3.0), ("pCube2", 0.0), ("pCube3", 3.0)):
        cube(name, x)
    area, _region = view3d()
    rv3d = area.spaces.active.region_3d
    rv3d.view_perspective = 'PERSP'
    rv3d.view_rotation = Euler((math.radians(70), 0, math.radians(20))).to_quaternion()
    rv3d.view_location = (0, 0, 0)
    rv3d.view_distance = 16.0 * C["u"]
    pick_only("pCube2")
    park()


idle()


# --- 1. Object Mode Ctrl+1, then F11 face mode; click / marquee / lasso / circle ------------------------------

act(ctrl_one)


@step
def s_tab():
    check(f"1 Ctrl+1 on pCube2 = Isolate Select ({space().local_view is not None})", space().local_view is not None)
    park()
    key('F11')


idle()


@step
def s_tab_face():
    check(f"1 F11 = Edit Mode ({bpy.context.mode})", bpy.context.mode == 'EDIT_MESH')
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    clear_faces()
    click(screen_xy((0, 0, 1)))


idle()


@step
def s_tab_click():
    f = picked_faces()
    check(f"1 ... a click picks the top face ({f})", f == [5])
    clear_faces()
    drag_path(list(box_around((0, 0, 0))))


idle()


@step
def s_tab_marquee():
    f = picked_faces()
    check(f"1 ... a marquee picks the cube's front faces ({f})", f is not None and len(f) >= 3)
    clear_faces()
    with override():
        bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
    a, b = box_around((0, 0, 0), 0.6)
    drag_path([(a[0], a[1]), (b[0], a[1]), (b[0], b[1]), (a[0], b[1]), (a[0], a[1] - 2)])


idle()


@step
def s_tab_lasso():
    f = picked_faces()
    check(f"1 ... the Lasso tool picks faces ({f})", f is not None and len(f) >= 1)
    clear_faces()
    with override():
        bpy.ops.wm.tool_set_by_id(name="builtin.select_circle")
    c = screen_xy((0, 0, 1))
    drag_path([c, (c[0] + 3, c[1] + 2), (c[0] - 2, c[1] - 2)])


idle()


@step
def s_tab_circle():
    f = picked_faces()
    check(f"1 ... the Paint (circle) select tool picks faces ({f})", f is not None and len(f) >= 1)
    clear_faces()
    with override():
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    park()
    key('F8')


idle()


@step
def s_tab_back():
    check(f"1 F8 = Object Mode, still isolated ({bpy.context.mode}, {space().local_view is not None})",
          bpy.context.mode == 'OBJECT' and space().local_view is not None)
    pick_only()
    drag_path([rel(0.03, 0.97), rel(0.97, 0.03)])


idle()


@step
def s_obj_marquee():
    check(f"1 ... a marquee over everything picks pCube2 only ({selected()})", selected() == ["pCube2"])
    pick_only()
    with override():
        bpy.ops.wm.tool_set_by_id(name="builtin.select_lasso")
    a, b = rel(0.03, 0.97), rel(0.97, 0.03)
    drag_path([a, (b[0], a[1]), b, (a[0], b[1]), (a[0], a[1] - 2)])


idle()


@step
def s_obj_lasso():
    check(f"1 ... a lasso over everything picks pCube2 only ({selected()})", selected() == ["pCube2"])
    with override():
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
    pick_only("pCube1", "pCube2")
    park()


idle()


# --- 2. Ctrl+1 twice (leave), again (isolate the new selection) ------------------------------------------------------

act(ctrl_one)


@step
def s_twice():
    check(f"2 Ctrl+1 again leaves Isolate Select ({space().local_view is None})", space().local_view is None)
    ctrl_one()


idle()


@step
def s_twice_iso():
    sp = space()
    shown = sorted(o.name for o in bpy.context.scene.objects if sp.local_view is not None and o.local_view_get(sp))
    check(f"2 Ctrl+1 a third time isolates pCube1 + pCube2 ({shown})", shown == ["pCube1", "pCube2"])
    pick_only()
    click(screen_xy((-3, 0, 1)))


idle()


@step
def s_twice_click():
    check(f"2 ... a click picks pCube1 ({selected()})", selected() == ["pCube1"])
    park()
    mkey('H', ctrl=True)      # Maya Ctrl+H: hide the selection


idle()


# --- 3. H / Shift+H while isolated ----------------------------------------------------------------------------------

@step
def s_hidden():
    ob = bpy.data.objects["pCube1"]
    check(f"3 Ctrl+H hides pCube1 ({ob.visible_get()})", not ob.visible_get())
    pick_only()
    drag_path([rel(0.03, 0.97), rel(0.97, 0.03)])


idle()


@step
def s_hidden_marquee():
    check(f"3 ... a marquee picks pCube2 only ({selected()})", selected() == ["pCube2"])
    park()
    mkey('H', ctrl=True, shift=True)    # Maya Ctrl+Shift+H: show last hidden


idle()


@step
def s_shown():
    ob = bpy.data.objects["pCube1"]
    check(f"3 Ctrl+Shift+H shows pCube1 again ({ob.visible_get()})", ob.visible_get())
    pick_only()
    drag_path([rel(0.03, 0.97), rel(0.97, 0.03)])


idle()


@step
def s_shown_marquee():
    check(f"3 ... a marquee picks pCube1 + pCube2 ({selected()})", selected() == ["pCube1", "pCube2"])
    leave_isolate()
    pick_only()


idle()


# --- 4. modifiers: Subdivision (on cage too), Mirror, Armature ----------------------------------------------------

def modifier_case(tag, setup_fn, at=(0, 0, 1)):
    def s_prep():
        to_object_mode()
        leave_isolate()
        for name in ("pCube2",):
            ob = bpy.data.objects[name]
            for m in list(ob.modifiers):
                ob.modifiers.remove(m)
        setup_fn(bpy.data.objects["pCube2"])
        pick_only("pCube2")
        park()
    act(s_prep)

    def s_ctl_mode():
        key('F11')
    act(s_ctl_mode)

    def s_ctl_click():
        clear_faces()
        click(screen_xy(at))
    act(s_ctl_click)

    def s_ctl_done():
        C["control"] = picked_faces()
        check(f"4{tag} without Isolate Select a face click picks ({C['control']})", True)
        to_object_mode()
        pick_only("pCube2")
        park()
    act(s_ctl_done)
    act(ctrl_one)

    def s_iso():
        check(f"4{tag} Ctrl+1 = Isolate Select ({space().local_view is not None})", space().local_view is not None)
        pick_only()
        click(screen_xy(at))
    act(s_iso)

    def s_obj_click():
        check(f"4{tag} ... a click picks pCube2 ({selected()})", selected() == ["pCube2"])
        park()
        key('F11')
    act(s_obj_click)

    def s_face():
        check(f"4{tag} ... F11 = face mode ({bpy.context.mode})", bpy.context.mode == 'EDIT_MESH')
        clear_faces()
        click(screen_xy(at))
    act(s_face)

    def s_face_click():
        f = picked_faces()
        check(f"4{tag} ... a click picks what it picks without Isolate Select ({f}, {C['control']})",
              f is not None and f == C["control"])
        clear_faces()
        drag_path(list(box_around((0, 0, 0))))
    act(s_face_click)

    def s_face_box():
        f = picked_faces()
        check(f"4{tag} ... a marquee picks faces ({f})", f is not None and len(f) >= 3)
        to_object_mode()
        leave_isolate()
    act(s_face_box)


def _subsurf(ob):
    m = ob.modifiers.new("subdiv", 'SUBSURF')
    m.levels = 2


def _subsurf_cage(ob):
    m = ob.modifiers.new("subdiv", 'SUBSURF')
    m.levels = 2
    m.show_on_cage = True


def _mirror(ob):
    m = ob.modifiers.new("mirror", 'MIRROR')
    m.use_axis = (False, False, True)
    m.mirror_offset_u = 0.0


def _armature(ob):
    arm = bpy.data.armatures.new("rig")
    rig = bpy.data.objects.new("joint1", arm)
    bpy.context.scene.collection.objects.link(rig)
    with override():
        bpy.context.view_layer.objects.active = rig
        pick_only("joint1")
        bpy.ops.object.mode_set(mode='EDIT')
        b = arm.edit_bones.new("b")
        b.head, b.tail = (0, 0, -1 * C["u"]), (0, 0, 1 * C["u"])
        bpy.ops.object.mode_set(mode='OBJECT')
    ob.parent = rig
    m = ob.modifiers.new("skin", 'ARMATURE')
    m.object = rig
    vg = ob.vertex_groups.new(name="b")
    vg.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')


modifier_case("a subdivision", _subsurf)
modifier_case("b subdivision on cage", _subsurf_cage)
modifier_case("c mirror", _mirror)
modifier_case("d armature", _armature)


@step
def s_clean_mods():
    to_object_mode()
    leave_isolate()
    ob = bpy.data.objects["pCube2"]
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    mw = ob.matrix_world.copy()
    ob.parent = None
    ob.matrix_world = mw
    rig = bpy.data.objects.get("joint1")
    if rig is not None:
        bpy.data.objects.remove(rig)
    # 5. a linked duplicate of pCube3 at y = 4
    dup = bpy.data.objects.new("pCube4", bpy.data.objects["pCube3"].data)
    dup.location = (3 * C["u"], 4 * C["u"], 0)
    bpy.context.scene.collection.objects.link(dup)
    pick_only("pCube4")
    park()


idle()


# --- 5. linked duplicate -----------------------------------------------------------------------------------------

act(ctrl_one)


@step
def s_dup_iso():
    sp = space()
    check(f"5 Ctrl+1 on the linked duplicate pCube4 ({sp.local_view is not None})", sp.local_view is not None)
    pick_only()
    click(screen_xy((3, 4, 1)))


idle()


@step
def s_dup_click():
    check(f"5 ... a click picks pCube4 ({selected()})", selected() == ["pCube4"])
    park()
    key('F11')


idle()


@step
def s_dup_face():
    clear_faces()
    click(screen_xy((3, 4, 1)))


idle()


@step
def s_dup_face_click():
    f = picked_faces()
    check(f"5 ... in face mode a click picks its top face ({bpy.context.edit_object and bpy.context.edit_object.name}, "
          f"{f})", f == [5])
    to_object_mode()
    leave_isolate()
    # 6. a group: Ctrl+1 on group1 shows its child, a click picks the child
    grp = bpy.data.objects.new("group1", None)
    bpy.context.scene.collection.objects.link(grp)
    child = bpy.data.objects["pCube1"]
    child.parent = grp
    pick_only("group1")
    park()


idle()

act(ctrl_one)


@step
def s_group_iso():
    sp = space()
    shown = sorted(o.name for o in bpy.context.scene.objects if sp.local_view is not None and o.local_view_get(sp))
    check(f"6 Ctrl+1 on group1 shows group1 and pCube1 ({shown})", shown == ["group1", "pCube1"])
    pick_only()
    click(screen_xy((-3, 0, 1)))


idle()


@step
def s_group_click():
    check(f"6 ... a click picks pCube1 ({selected()})", selected() == ["pCube1"])
    pick_only()
    drag_path([rel(0.03, 0.97), rel(0.97, 0.03)])


idle()


@step
def s_group_marquee():
    check(f"6 ... a marquee picks pCube1 (and the group) only ({selected()})",
          "pCube1" in selected() and not {"pCube2", "pCube3", "pCube4"} & set(selected()))
    leave_isolate()
    # 7. a collection instance
    coll = bpy.data.collections.new("inst_src")
    src = cube("pInst", 0.0, -5.0)
    for c in list(src.users_collection):
        c.objects.unlink(src)
    coll.objects.link(src)
    inst = bpy.data.objects.new("instance1", None)
    inst.instance_type = 'COLLECTION'
    inst.instance_collection = coll
    inst.location = (0, 0, 0)
    bpy.context.scene.collection.objects.link(inst)
    pick_only("instance1")
    park()


idle()

act(ctrl_one)


@step
def s_inst_iso():
    check(f"7 Ctrl+1 on a collection instance ({space().local_view is not None})", space().local_view is not None)
    pick_only()
    click(screen_xy((0, -5, 1)))


idle()


@step
def s_inst_click():
    check(f"7 ... a click on the instanced cube picks the instance ({selected()})", selected() == ["instance1"])
    leave_isolate()
    bpy.data.objects.remove(bpy.data.objects["instance1"])
    pick_only("pCube2")
    park()


idle()


# --- 8. a file saved while isolated, opened again -----------------------------------------------------------------
# Maya mode opens a file in the Maya layout (the UI doesn't come from the file, like Maya): a file saved in Blender's
# layout shows a view that isn't isolated, one saved in the Maya layout shows its view still isolated. Either way a
# marquee picks what the view shows, and Ctrl+1 (leaving first when isolated) isolates there as usual.

act(ctrl_one)


@step
def s_save():
    check(f"8 Ctrl+1 on pCube2 ({space().local_view is not None})", space().local_view is not None)
    C["path"] = os.path.join(tempfile.gettempdir(), "allset_gui_422_cases.blend")
    with override():
        bpy.ops.wm.save_as_mainfile(filepath=C["path"], copy=True)
        bpy.ops.wm.open_mainfile(filepath=C["path"], load_ui=True)


idle(4)


@step
def s_reopened():
    C["shown"] = sorted(o.name for o in bpy.context.scene.objects if o.type == 'MESH'
                        and o.visible_get(viewport=space()))
    pick_only()
    drag_path([rel(0.03, 0.97), rel(0.97, 0.03)])


idle()


@step
def s_reopened_marquee():
    s = [n for n in selected() if bpy.data.objects[n].type == 'MESH']
    check(f"8 after the file is opened a marquee picks every cube the view shows ({s}, {C['shown']})",
          s == C["shown"] and "pCube2" in s)
    C["iso_open"] = space().local_view is not None
    check(f"8 ... isolated after the open only when saved in the Maya layout ({C['iso_open']})",
          C["iso_open"] == MAYA_LAYOUT)
    park()


idle()


@step
def s_reopened_leave():
    if C["iso_open"]:
        ctrl_one()


idle()


@step
def s_reopened_pick():
    check(f"8 ... not isolated now ({space().local_view is None})", space().local_view is None)
    pick_only("pCube2")
    park()


idle()

act(ctrl_one)


@step
def s_reopened_iso():
    check(f"8 ... Ctrl+1 on pCube2 isolates it ({space().local_view is not None})", space().local_view is not None)
    pick_only()
    drag_path([rel(0.03, 0.97), rel(0.97, 0.03)])


idle()


@step
def s_reopened_iso_marquee():
    check(f"8 ... a marquee picks pCube2 only ({selected()})", selected() == ["pCube2"])
    park()
    key('F11')


idle()


@step
def s_reopened_face():
    check(f"8 ... F11 = face mode ({bpy.context.mode})", bpy.context.mode == 'EDIT_MESH')
    clear_faces()
    click(screen_xy((0, 0, 1)))


idle()


@step
def s_reopened_face_click():
    f = picked_faces()
    check(f"8 ... a click picks the top face ({f})", f == [5])
    to_object_mode()
    try:
        os.remove(C["path"])
    except OSError:
        pass


idle()

run()
