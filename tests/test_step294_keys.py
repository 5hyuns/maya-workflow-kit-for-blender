"""#215 #212: Ctrl-first drags on the Move manipulator, Shift+W / E / R in every editor, Attribute Editor key colours.
GUI: tests/gui/gui_step294_keys.py."""

import inspect
import types
from importlib import import_module

import bpy

import kit

patches = import_module(kit.MODULE + ".keymap.maya_patches")
time_keys = import_module(kit.MODULE + ".operators.time_keys")
cb = import_module(kit.MODULE + ".ui.channel_box")


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def test_215_gizmo_drag_allows_ctrl_and_shift():
    # a drag started with Ctrl (or Shift) held still reaches the handle's own drag (no box select)
    kc = kit.maya_kc()
    for km in patches.GIZMO_KEYMAPS:
        items = [k for k in kc.keymaps[km].keymap_items if k.active and k.idname == "gizmogroup.gizmo_tweak"
                 and k.type == 'LEFTMOUSE' and k.value == 'CLICK_DRAG']
        assert items, km
        assert all(k.ctrl == -1 and k.shift == -1 and not k.alt for k in items), \
            (km, [(k.ctrl, k.shift, k.alt) for k in items])
        first = [k for k in kc.keymaps[km].keymap_items if k.active and k.type == 'LEFTMOUSE' and k.value == 'PRESS'
                 and k.ctrl and not k.shift and not k.alt]
        assert first and first[0].idname == "allset.manip_ctrl", km


def test_212_shift_w_e_r_global():
    kc = kit.maya_kc()
    items = {(i.type, i.properties.channels) for i in kc.keymaps["Screen"].keymap_items
             if i.idname == "allset.set_key" and i.active and i.shift and not i.ctrl and not i.alt
             and i.properties.global_key}
    assert items == {("W", "TRANSLATE"), ("E", "ROTATE"), ("R", "SCALE")}, items
    # Blender's channel protect toggle no longer takes Shift+W in the Graph Editor / Dope Sheet channel list
    for i in kc.keymaps["Animation Channels"].keymap_items:
        if i.active and i.type == 'W' and i.shift and not i.ctrl and not i.alt:
            raise AssertionError(f"Animation Channels Shift+W still bound: {i.idname}")
    # no editor keymap between the editors and "Screen" takes plain Shift+W / E / R in the animation editors
    for km in ("Graph Editor", "Graph Editor Generic", "Dopesheet", "Dopesheet Generic", "Outliner",
               "Property Editor", "NLA Editor", "NLA Generic", "View2D", "View2D Buttons List", "Frames"):
        if km not in kc.keymaps:
            continue
        hits = [i.idname for i in kc.keymaps[km].keymap_items if i.active and i.type in {'W', 'E', 'R'}
                and i.value == 'PRESS' and i.shift and not i.ctrl and not i.alt and not i.oskey]
        assert not hits, (km, hits)


def _invoke(context, channels):
    calls = []
    me = types.SimpleNamespace(global_key=True, execute=lambda c: calls.append(c) or {'FINISHED'})
    return time_keys.ALLSET_OT_set_key.invoke(me, context, None), calls


def test_212_global_key_only_in_object_and_pose_mode():
    _clear()
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    assert time_keys.global_key_applies(bpy.context)
    res, calls = _invoke(bpy.context, "TRANSLATE")
    assert res == {'FINISHED'} and len(calls) == 1
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        assert not time_keys.global_key_applies(bpy.context)
        res, calls = _invoke(bpy.context, "TRANSLATE")
        assert res == {'PASS_THROUGH'} and not calls
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
    assert not kit.fcurves(ob)
    # the keys themselves: Shift+W keys Translate only
    assert bpy.ops.allset.set_key(channels="TRANSLATE", global_key=True) == {'FINISHED'}
    assert sorted({fc.data_path for fc in kit.fcurves(ob)}) == ["location"]


def test_212_ae_state_alert_matches_channel_box():
    _clear()
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    ob.keyframe_insert("location", index=2, frame=bpy.context.scene.frame_current)
    assert cb.channel_state(ob, "tz") == 'KEYED' and cb.state_alert('KEYED')
    assert cb.channel_state(ob, "tx") is None and not cb.state_alert(None)
    for state in ('ANIMATED', 'DRIVEN', 'MUTED'):
        assert cb.state_alert(state)
    assert not cb.state_alert('LAYERED')       # layer members: icon only, like the Channel Box


def test_212_ae_fields_use_the_channel_box_state():
    ae = import_module(kit.MODULE + ".ui.attribute_editor")
    src = inspect.getsource(ae._maya_number_rows)
    assert "channel_box.state_alert(channel_box.channel_state(ob, key))" in src
