"""Step 88: docs/manual_checks.md items of steps 59-79 that event simulation can prove, run in one MayaKit session.

Each check name starts with the item's id ``[M<step>-<n>]`` (n = its place in that step's list); an item is ticked in
manual_checks.md only when all of its checks pass. Keys, clicks and drags are simulated events; a few Enter-in-a-field
actions set the field's property (its setter is the Enter path; gui_step75 proves the typing itself).
Plan: docs/steps/step_88.md."""

import os
import sys
import tempfile
from importlib import import_module

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import MODULE, check, ev, run, setup, step, tap, view3d, win  # noqa: E402

C = {}


def mod(name):
    return import_module(f"{MODULE}.{name}")


def k():
    return mod("operators.units").maya_unit()


def ts():
    return bpy.context.scene.tool_settings


def key(type, **mods):
    names = {"alt": "LEFT_ALT", "ctrl": "LEFT_CTRL", "shift": "LEFT_SHIFT"}
    for m in mods:
        ev(names[m], 'PRESS')
    ev(type, 'PRESS', **mods)
    ev(type, 'RELEASE', **mods)
    for m in mods:
        ev(names[m], 'RELEASE')


def hover():
    _a, r = view3d()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)


def override():
    area, region = view3d()
    return bpy.context.temp_override(window=win(), area=area, region=region)


def tool_id():
    with override():
        t = bpy.context.workspace.tools.from_space_view3d_mode(bpy.context.mode, create=False)
    return t.idname if t else None


def select_only(*obs):
    for o in bpy.context.view_layer.objects:
        if o is not None:
            o.select_set(o in obs)
    bpy.context.view_layer.objects.active = obs[-1]


def create(kind):
    with override():
        bpy.ops.maya_kit.create(kind=kind)
    return bpy.context.view_layer.objects.active


def clear():
    if bpy.context.mode != 'OBJECT':
        with override():
            bpy.ops.object.mode_set(mode='OBJECT')
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    # Maya names count the shapes too (pCubeShape1): drop the data so each section starts at pCube1
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.armatures, bpy.data.cameras, bpy.data.actions):
        for d in list(coll):
            coll.remove(d)


def near(a, b, eps=1e-4):
    return (Vector(a) - Vector(b)).length < eps


def notice():
    return mod("ui.notices").current()


# --- setup ---------------------------------------------------------------------------------------------------

@step
def s_setup():
    setup()
    bpy.ops.maya_kit.layout_install()
    bpy.ops.wm.read_homefile(app_template="MayaKit")


@step
def s_keymap():
    bpy.ops.maya_kit.keymap_activate()
    hover()


# --- [M59-7] lead pivot / component bounding box --------------------------------------------------------------

@step
def m59_7_objects():
    a = create('CUBE')
    b = create('CUBE')
    b.location = (3 * k(), 0, 0)
    select_only(a, b)
    with override():
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
        centre, _f, _o = mod("ui.manipulator").pivot_frame(bpy.context, 'TRANSLATE')
    check(f"[M59-7] two objects: the manipulator at the lead's pivot ({tuple(round(v / k(), 2) for v in centre)} cm)",
          near(centre, b.matrix_world.translation))
    hover()
    tap('F9')


@step
def m59_7_components():
    with override():
        bpy.ops.mesh.select_all(action='SELECT')
    check(f"[M59-7] edit mode: Pivot = Bounding Box Center ({ts().transform_pivot_point})",
          bpy.context.mode == 'EDIT_MESH' and ts().transform_pivot_point == 'BOUNDING_BOX_CENTER')
    with override():
        centre, _f, _o = mod("ui.manipulator").pivot_frame(bpy.context, 'TRANSLATE')
    pts = [ob.matrix_world @ v.co for ob in bpy.context.objects_in_mode for v in ob.data.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    check("[M59-7] components: the manipulator at the selection's bounding box centre", near(centre, (lo + hi) / 2))
    tap('F8')


# --- [M63-5] Combine / Separate ----------------------------------------------------------------------------

@step
def m63_5_combine():
    clear()
    cube = create('CUBE')
    cube.location = (2 * k(), 0, 0)
    sphere = create('SPHERE')
    sphere.location = (-2 * k(), 0, 1 * k())
    bpy.context.view_layer.update()
    pts = [ob.matrix_world @ v.co for ob in (cube, sphere) for v in ob.data.vertices]
    C["bbox"] = (Vector([min(p[i] for p in pts) for i in range(3)]) + Vector([max(p[i] for p in pts) for i in range(3)])) / 2
    select_only(cube, sphere)
    with override():
        C["combine"] = bpy.ops.maya_kit.combine()


@step
def m63_5_combined():
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    ob = meshes[0] if len(meshes) == 1 else None
    check(f"[M63-5] Combine: one mesh pCube2 ({[o.name for o in meshes]})", ob is not None and ob.name == "pCube2")
    if ob is None:
        return
    check(f"[M63-5] Combine: Translate 0, pivot at the combined box centre ({tuple(ob.location)})",
          near(ob.location, (0, 0, 0)) and near(ob.matrix_world.translation, C["bbox"]))
    select_only(ob)
    with override():
        bpy.ops.maya_kit.separate()


@step
def m63_5_separated():
    group = bpy.data.objects.get("pCube2")
    kids = sorted(o.name for o in group.children) if group else []
    check(f"[M63-5] Separate: pCube2 group with polySurface1 / polySurface2 ({group and group.type}, {kids})",
          group is not None and group.type == 'EMPTY' and kids == ["polySurface1", "polySurface2"])
    check("[M63-5] Separate: pieces at Translate 0",
          all(near(bpy.data.objects[n].location, (0, 0, 0)) for n in kids))
    # edit mode Separate = Blender's mesh.separate (loose parts), no group, Blender names
    me = bpy.data.meshes.new("parts")
    bm = bmesh.new()
    for x in (0.0, 3.0):
        v = [bm.verts.new((x + a, b, 0)) for a, b in ((0, 0), (1, 0), (1, 1), (0, 1))]
        bm.faces.new(v)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("parts", me)
    bpy.context.scene.collection.objects.link(ob)
    select_only(ob)
    C["before_sep"] = len(bpy.data.objects)
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.maya_kit.separate()
        bpy.ops.object.mode_set(mode='OBJECT')
    new = sorted(o.name for o in bpy.data.objects if o.name.startswith("parts"))
    check(f"[M63-5] edit mode Separate = Blender's (loose parts, Blender names, no group: {new})",
          len(bpy.data.objects) == C["before_sep"] + 1 and new == ["parts", "parts.001"]
          and bpy.data.objects["parts.001"].parent is None)


# --- [M69-3] Ctrl+Alt+S increment and save -----------------------------------------------------------------

@step
def m69_3_save():
    d = tempfile.mkdtemp(prefix="maya_kit_sweep_")
    C["v001"] = os.path.join(d, "shot_v001.blend")
    bpy.ops.wm.save_as_mainfile(filepath=C["v001"])
    hover()
    key('S', ctrl=True, alt=True)


@step
def m69_3_check():
    want = os.path.join(os.path.dirname(C["v001"]), "shot_v001.0001.blend")
    check(f"[M69-3] Ctrl+Alt+S saves shot_v001.0001.blend and goes on in it ({os.path.basename(bpy.data.filepath)})",
          os.path.exists(want) and os.path.normcase(bpy.data.filepath) == os.path.normcase(want))
    check("[M69-3] the original file stays", os.path.exists(C["v001"]))


# --- [M70-3] Graph Editor G / D / F / A, 3D View G = repeat last ----------------------------------------------

def graph():
    return C["garea"], next(r for r in C["garea"].regions if r.type == 'WINDOW')


@step
def m70_3_setup():
    clear()
    cube = create('CUBE')
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 48
    sc.use_preview_range = False
    for f, x in ((5, 0.0), (20, 3.0), (30, -1.0)):
        cube.location.x = x * k()
        cube.keyframe_insert("location", index=0, frame=f)
    select_only(cube)
    a, _r = view3d()
    C["garea"] = a
    a.ui_type = 'FCURVES'


@step
def m70_3_hover():
    a, r = graph()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    a2, r2 = graph()
    with bpy.context.temp_override(window=win(), area=a2, region=r2):
        bpy.ops.graph.select_all(action='SELECT')
        for fc in bpy.context.visible_fcurves:
            for kp in fc.keyframe_points:
                kp.handle_left_type = kp.handle_right_type = 'VECTOR'
    tap('G')


@step
def m70_3_g():
    _a, r = graph()
    x0 = r.view2d.region_to_view(0, 0)[0]
    x1 = r.view2d.region_to_view(r.width, 0)[0]
    check(f"[M70-3] Graph Editor G frames the playback range 1-48 ({x0:.1f}..{x1:.1f})",
          -8 < x0 < 1.5 and 47 < x1 < 58)
    tap('D')


@step
def m70_3_d():
    fc = bpy.data.objects["pCube1"].animation_data.action.layers[0].strips[0].channelbags[0].fcurves[0]
    types = {(kp.handle_left_type, kp.handle_right_type, kp.interpolation) for kp in fc.keyframe_points}
    check(f"[M70-3] D = Auto tangents on the selected keys ({types})", types == {('AUTO_CLAMPED', 'AUTO_CLAMPED', 'BEZIER')})
    a, r = graph()
    with bpy.context.temp_override(window=win(), area=a, region=r):
        bpy.ops.graph.select_all(action='DESELECT')
        fc.keyframe_points[1].select_control_point = True
    tap('F')


@step
def m70_3_f():
    _a, r = graph()
    x0 = r.view2d.region_to_view(0, 0)[0]
    x1 = r.view2d.region_to_view(r.width, 0)[0]
    check(f"[M70-3] F frames the selected key (frame 20 in view {x0:.1f}..{x1:.1f}, narrower than the range)",
          x0 < 20 < x1 and (x1 - x0) < 40)
    C["fspan"] = x1 - x0
    tap('A')


@step
def m70_3_a():
    _a, r = graph()
    x0 = r.view2d.region_to_view(0, 0)[0]
    x1 = r.view2d.region_to_view(r.width, 0)[0]
    check(f"[M70-3] A frames all keys (5..30 in view {x0:.1f}..{x1:.1f})", x0 < 5 and x1 > 30)
    kc = bpy.context.window_manager.keyconfigs["Maya"]
    rep = [km.name for km in kc.keymaps for it in km.keymap_items
           if it.active and it.idname == "screen.repeat_last" and it.type == 'G' and not (it.shift or it.ctrl or it.alt)]
    v3d_g = [it.idname for km_name in ("3D View", "Object Mode", "3D View Generic")
             for it in kc.keymaps[km_name].keymap_items if it.active and it.type == 'G' and it.value == 'PRESS'
             and not (it.shift or it.ctrl or it.alt)]
    check(f"[M70-3] 3D View G stays Repeat Last ({rep}, 3D View G items {v3d_g})", "Screen" in rep and not v3d_g)
    C["garea"].ui_type = 'VIEW_3D'


# --- [M70-4] Maya Auto Key -----------------------------------------------------------------------------------

def curves(ob):
    ad = ob.animation_data
    if ad is None or ad.action is None:
        return set()
    bag = ad.action.layers[0].strips[0].channelbags[0]
    return {(fc.data_path, fc.array_index) for fc in bag.fcurves}


@step
def m70_4_on():
    clear()
    cube = create('CUBE')
    select_only(cube)
    sc = bpy.context.scene
    sc.frame_set(1)
    cube.keyframe_insert("location", frame=1)
    sc.frame_set(10)
    ts().use_keyframe_insert_auto = True
    prefs = bpy.context.preferences.addons[MODULE].preferences
    check("[M70-4] Maya Auto Key is on by default", prefs.use_maya_auto_key)
    with override():
        bpy.ops.transform.rotate(value=0.5, orient_axis='Z')
    bpy.context.scene.maya_kit_cb.rx_text = "30"
    c = curves(cube)
    check(f"[M70-4] rotating a cube with only Translate keys adds no rotate keys (manipulator or Channel Box) ({sorted(c)})",
          not any(p == "rotation_euler" for p, _i in c))
    prefs.use_maya_auto_key = False


@step
def m70_4_off():
    cube = bpy.data.objects["pCube1"]
    bpy.context.scene.frame_set(20)
    with override():
        bpy.ops.transform.rotate(value=0.5, orient_axis='Z')
    c = curves(cube)
    check(f"[M70-4] Maya Auto Key off: Blender keys every channel ({sorted(c)})",
          any(p == "rotation_euler" for p, _i in c))
    bpy.context.preferences.addons[MODULE].preferences.use_maya_auto_key = True
    ts().use_keyframe_insert_auto = False


# --- [M75-1..4] Status Line input line -----------------------------------------------------------------------

def inp():
    return bpy.context.scene.maya_kit_input


@step
def m75_1():
    clear()
    cube = create('CUBE')
    cube.location = (1 * k(), 2 * k(), 3 * k())
    select_only(cube)
    with override():
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    bpy.ops.ed.undo_push(message="sweep 75")
    inp().mode = 'ABS'
    inp().x = "10"
    check(f"[M75-1] Abs X 10 = x 10 cm, Y / Z kept ({tuple(round(v / k(), 3) for v in cube.location)})",
          near(cube.location, (10 * k(), 2 * k(), 3 * k())))
    with override():
        bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
    inp().z = "45"
    check(f"[M75-1] Rotate tool: Abs Z 45 = rotate Z 45 ({cube.rotation_euler.z:.4f})",
          abs(cube.rotation_euler.z - 0.785398) < 1e-4)
    with override():
        bpy.ops.wm.tool_set_by_id(name="builtin.scale")
    inp().y = "2"
    check(f"[M75-1] Scale tool: Abs Y 2 = scale Y 2 ({tuple(cube.scale)})", abs(cube.scale.y - 2) < 1e-6)
    with override():
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
        bpy.ops.ed.undo()
    cube = bpy.data.objects["pCube1"]
    check(f"[M75-1] Ctrl+Z once takes back the last entry (scale {tuple(cube.scale)})", abs(cube.scale.y - 1) < 1e-6)


@step
def m75_2():
    cube = bpy.data.objects["pCube1"]
    select_only(cube)
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(cube.data)
        for v in bm.verts:
            v.select_set(v.co.z > 0)
        bm.select_flush_mode()
        bmesh.update_edit_mesh(cube.data)
    inp().mode = 'ABS'
    inp().z = "0"
    zs = [round((cube.matrix_world @ v.co).z, 6) for v in cube.data.vertices]
    me = cube.data
    with override():
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
    sel = [cube.matrix_world @ v.co for v in me.vertices if v.select]
    check(f"[M75-2] edit mode Abs Z 0: the selected components' centre at z 0 ({sum(p.z for p in sel) / len(sel):.6f})",
          abs(sum(p.z for p in sel) / len(sel)) < 1e-6)
    before = [p.copy() for p in sel]
    inp().mode = 'REL'
    inp().x = "1"
    with override():
        bpy.ops.object.mode_set(mode='OBJECT')
    after = [cube.matrix_world @ v.co for v in me.vertices if v.select]
    check("[M75-2] Rel X 1 moves them 1 cm in x", all(abs((q - p).x - k()) < 1e-6 and abs((q - p).z) < 1e-6
                                                      for p, q in zip(before, after)))
    del zs


@step
def m75_3():
    clear()
    obs = [create('CUBE') for _ in range(3)]
    select_only(*obs)
    inp().mode = 'RENAME'
    check(f"[M75-3] Rename shows the lead's name ({inp().text})", inp().text == obs[-1].name)
    inp().text = "crate"
    names = sorted(o.name for o in bpy.context.selected_objects)
    shapes = sorted(o.data.name for o in bpy.context.selected_objects)
    check(f"[M75-3] Rename crate: crate, crate1, crate2 + crateShape… ({names}, {shapes})",
          names == ["crate", "crate1", "crate2"] and all(s.startswith("crateShape") for s in shapes))
    inp().text = "1x"
    e1 = notice()
    inp().text = "a-b"
    e2 = notice()
    check(f"[M75-3] '1x' and 'a-b' are refused with a Help Line message ({e1!r}, {e2!r})",
          e1 and e2 and sorted(o.name for o in bpy.context.selected_objects) == ["crate", "crate1", "crate2"])


@step
def m75_4():
    clear()
    create('CUBE')
    create('CUBE')
    create('SPHERE')
    inp().mode = 'SELECT'
    inp().text = "pCube*"
    s1 = sorted(o.name for o in bpy.context.selected_objects)
    inp().text = "p?phere1"
    s2 = sorted(o.name for o in bpy.context.selected_objects)
    check(f"[M75-4] Select by Name pCube* / p?phere1 ({s1}, {s2})", s1 == ["pCube1", "pCube2"] and s2 == ["pSphere1"])
    inp().text = "nothing*"
    check(f"[M75-4] a missing name: Help Line message, the text stays ({notice()!r}, {inp().text!r})",
          bool(notice()) and inp().text == "nothing*")
    il = mod("ui.input_line")
    um = mod("ui.menu_sets").MAYAKIT_OT_menu_unavailable
    props = type("P", (), {"item": il.HISTORY_PATH})()
    tip = um.description(bpy.context, props) or ""
    check(f"[M75-4] the grey History button's tooltip says Blender keeps no construction history ({tip[-80:]!r})",
          "no construction history" in tip.lower())
    inp().mode = 'ABS'


# --- [M77-2] Insert + D; Insert twice clears the pivot ----------------------------------------------------------

@step
def m77_2_setup():
    clear()
    cube = create('CUBE')
    select_only(cube)
    hover()
    tap('F9')


@step
def m77_2_insert():
    with override():
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    C["tool"] = tool_id()
    tap('INSERT')


@step
def m77_2_d():
    on = mod("operators.hold").COMPONENT.on
    check(f"[M77-2] Insert turns the pivot edit on ({on}, {tool_id()})", on and tool_id() == "builtin.cursor")
    tap('D')


@step
def m77_2_d_check():
    check(f"[M77-2] D while it is on turns it off ({mod('operators.hold').COMPONENT.on}, {tool_id()})",
          not mod("operators.hold").COMPONENT.on and tool_id() == C["tool"])
    tap('INSERT')


@step
def m77_2_twice():
    tap('INSERT')


@step
def m77_2_twice_check():
    with override():
        centre, _f, _o = mod("ui.manipulator").pivot_frame(bpy.context, 'TRANSLATE')
    cube = bpy.data.objects["pCube1"]
    pts = [cube.matrix_world @ v.co for v in cube.data.vertices]
    mid = (Vector([min(p[i] for p in pts) for i in range(3)]) + Vector([max(p[i] for p in pts) for i in range(3)])) / 2
    check(f"[M77-2] Insert twice without moving: no user pivot ({ts().transform_pivot_point}), manipulator at the bbox centre",
          ts().transform_pivot_point != 'CURSOR' and near(centre, mid) and not mod("operators.hold").COMPONENT.on)
    tap('F8')


# --- [M78-3] Ctrl+Alt+Left / Right spin an edge -------------------------------------------------------------

def strip_mesh():
    me = bpy.data.meshes.new("strip")
    bm = bmesh.new()
    v = [bm.verts.new(co) for co in ((0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0), (1, 1, 0), (2, 1, 0))]
    bm.faces.new((v[0], v[1], v[4], v[3]))
    bm.faces.new((v[1], v[2], v[5], v[4]))
    bm.to_mesh(me)
    bm.free()
    return me


def shared_edge(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    e = next(e for e in bm.edges if len(e.link_faces) == 2)
    return tuple(sorted(v.index for v in e.verts))


@step
def m78_3_setup():
    clear()
    ob = bpy.data.objects.new("strip", strip_mesh())
    bpy.context.scene.collection.objects.link(ob)
    select_only(ob)
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bm = bmesh.from_edit_mesh(ob.data)
        for e in bm.edges:
            e.select_set(len(e.link_faces) == 2)
        bmesh.update_edit_mesh(ob.data)
    C["e0"] = shared_edge(ob)
    hover()
    key('RIGHT_ARROW', ctrl=True, alt=True)


@step
def m78_3_right():
    ob = bpy.data.objects["strip"]
    C["e1"] = shared_edge(ob)
    check(f"[M78-3] Ctrl+Alt+Right spins the edge ({C['e0']} -> {C['e1']})", C["e1"] != C["e0"])
    key('LEFT_ARROW', ctrl=True, alt=True)


@step
def m78_3_left():
    e2 = shared_edge(bpy.data.objects["strip"])
    check(f"[M78-3] Ctrl+Alt+Left spins it the other way, back ({e2})", e2 == C["e0"])
    mm = mod("ui.menu_map").MAP
    kc = bpy.context.window_manager.keyconfigs["Maya"]
    keys = {it.type: bool(it.properties.use_ccw) for it in kc.keymaps["Mesh"].keymap_items
            if it.active and it.idname == "mesh.edge_rotate" and it.ctrl and it.alt}
    check(f"[M78-3] the keys spin like the menu (Right = Forward, Left = Backward: {keys})",
          keys.get('RIGHT_ARROW') == mm["Edit Mesh/Spin Edge Forward"][1]["use_ccw"]
          and keys.get('LEFT_ARROW') == mm["Edit Mesh/Spin Edge Backward"][1]["use_ccw"])
    tap('F8')


# --- [M78-6] Graph Editor 1 / 2 / 3 -------------------------------------------------------------------------

@step
def m78_6_setup():
    clear()
    cube = create('CUBE')
    for f in (1, 20):
        cube.location.z = f * 0.1 * k()
        cube.keyframe_insert("location", index=2, frame=f)
    select_only(cube)
    a, _r = view3d()
    C["garea"] = a
    a.ui_type = 'FCURVES'


@step
def m78_6_hover():
    _a, r = graph()
    ev('MOUSEMOVE', 'NOTHING', x=r.x + r.width // 2, y=r.y + r.height // 2)
    tap('THREE')


@step
def m78_6_three():
    sp = C["garea"].spaces.active
    check(f"[M78-6] 3 = normalized ({sp.use_normalization})", sp.use_normalization)
    tap('ONE')


@step
def m78_6_one():
    sp = C["garea"].spaces.active
    check(f"[M78-6] 1 = absolute ({sp.use_normalization})", not sp.use_normalization)
    tap('TWO')


@step
def m78_6_two():
    sp = C["garea"].spaces.active
    gk = mod("operators.graph_keys")
    # the notice is the operator's INFO report (status bar = Maya Help Line); Python can't read the report list,
    # so the check is: 2 ran the STACKED mode (normalized) and that mode reports the notice
    kc = bpy.context.window_manager.keyconfigs["Maya"]
    two = [it for it in kc.keymaps["Graph Editor"].keymap_items
           if it.active and it.type == 'TWO' and it.idname == "maya_kit.graph_view_mode"]
    check(f"[M78-6] 2 = Stacked mode: normalized + its 'no Stacked' report ({sp.use_normalization}, "
          f"{two and two[0].properties.mode}, {gk.STACKED_NOTICE!r})",
          sp.use_normalization and two and two[0].properties.mode == "STACKED" and "Stacked" in gk.STACKED_NOTICE)
    C["garea"].ui_type = 'VIEW_3D'


# --- [M79-3] Cut and Sew tool x / s / d, outside the tool X / D ------------------------------------------------

def shells(ob):
    return len(mod("operators.uv_tools").islands(bmesh.from_edit_mesh(ob.data), ob.data.uv_layers.active.name)) \
        if hasattr(mod("operators.uv_tools"), "islands") else None


@step
def m79_3_setup():
    clear()
    cube = create('CUBE')
    select_only(cube)
    hover()
    with override():
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bm = bmesh.from_edit_mesh(cube.data)
        top = max(v.co.z for v in bm.verts)
        for e in bm.edges:
            e.select_set(all(abs(v.co.z - top) < 1e-6 for v in e.verts))
        bmesh.update_edit_mesh(cube.data)
        bpy.ops.wm.tool_set_by_id(name=mod("operators.cut_sew").TOOL)
    C["uvs0"] = sum(1 for e in bmesh.from_edit_mesh(cube.data).edges if e.seam)


def seams():
    cube = bpy.data.objects["pCube1"]
    return sum(1 for e in bmesh.from_edit_mesh(cube.data).edges if e.seam)


@step
def m79_3_x():
    check(f"[M79-3] the Cut and Sew tool is active ({tool_id()})", tool_id() == mod("operators.cut_sew").TOOL)
    tap('X')


@step
def m79_3_s():
    check(f"[M79-3] x cuts the selected edges (seams {C['uvs0']} -> {seams()})", seams() == 4)
    tap('S')


@step
def m79_3_d():
    check(f"[M79-3] s sews them (seams {seams()})", seams() == 0)
    tap('D')


@step
def m79_3_d_check():
    cube = bpy.data.objects["pCube1"]
    bm = bmesh.from_edit_mesh(cube.data)
    uv = bm.loops.layers.uv.active
    co = [l[uv].uv for f in bm.faces for l in f.loops]
    ok = all(-1e-4 <= c.x <= 1 + 1e-4 and -1e-4 <= c.y <= 1 + 1e-4 for c in co)
    check(f"[M79-3] d = Unfold + Layout in 0-1 ({ok})", ok)
    with override():
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
    ev('X', 'PRESS')


@step
def m79_3_outside_x():
    check(f"[M79-3] outside the tool X = grid snap hold ({ts().use_snap}, {set(ts().snap_elements)})",
          ts().use_snap and 'GRID' in set(ts().snap_elements))
    ev('X', 'RELEASE')
    ev('D', 'PRESS')


@step
def m79_3_outside_d():
    check(f"[M79-3] outside the tool D = pivot edit hold ({mod('operators.hold').COMPONENT.on})",
          mod("operators.hold").COMPONENT.on)
    ev('D', 'RELEASE')
    C["seams_before_s"] = seams()


@step
def m79_3_outside_s():
    tap('S')


@step
def m79_3_outside_s_check():
    check(f"[M79-3] outside the tool S doesn't sew (seams {C['seams_before_s']} -> {seams()})",
          seams() == C["seams_before_s"])
    if bpy.context.window_manager.windows[0].modal_operators:
        ev('ESC', 'PRESS')
        ev('ESC', 'RELEASE')
    tap('F8')


run(interval=0.5)
