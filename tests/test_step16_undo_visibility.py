"""Step 16: Maya z / Shift+Z / Ctrl+Y undo-redo, h / Ctrl+H / Alt+H / Shift+H /
Ctrl+Shift+H visibility, Ctrl+1 isolate, Ctrl+Shift+I invert.
"""

from importlib import import_module

import bpy

import kit

visibility = import_module(kit.MODULE + ".operators.visibility")

KC = "Maya-style"


def _items(km, type, shift=False, ctrl=False, alt=False):
    km = bpy.context.window_manager.keyconfigs[KC].keymaps[km]
    return [(k.idname, dict(k.properties.items()) if k.properties else {}) for k in km.keymap_items
            if k.active and k.type == type and k.value == 'PRESS' and k.shift == shift
            and k.ctrl == ctrl and k.alt == alt and not k.oskey]


def test_undo_redo_keys_in_screen():
    assert ("ed.undo", {}) in _items("Screen", "Z")
    assert ("ed.redo", {}) in _items("Screen", "Z", shift=True)
    assert ("ed.redo", {}) in _items("Screen", "Y", ctrl=True)
    assert ("ed.undo", {}) in _items("Screen", "Z", ctrl=True), "Blender's Ctrl+Z kept"
    # Editor keymaps run first: nothing there may take plain z.
    for km in ("3D View", "View2D", "Image", "Node Editor", "Object Mode", "Mesh", "Outliner",
               "Graph Editor", "Dopesheet"):
        assert _items(km, "Z") == [], (km, _items(km, "Z"))


def _kmis(km, type, shift=False, ctrl=False, alt=False):
    km = bpy.context.window_manager.keyconfigs[KC].keymaps[km]
    return [k for k in km.keymap_items if k.active and k.type == type and k.value == 'PRESS'
            and k.shift == shift and k.ctrl == ctrl and k.alt == alt and not k.oskey]


def test_visibility_keys():
    want = {(False, False, False): "TOGGLE", (False, True, False): "HIDE",
            (False, False, True): "HIDE_UNSELECTED", (True, False, False): "SHOW_SELECTED",
            (True, True, False): "SHOW_LAST"}
    for (shift, ctrl, alt), action in want.items():
        got = _kmis("Object Mode", "H", shift=shift, ctrl=ctrl, alt=alt)
        assert [(k.idname, k.properties.action) for k in got] == [("allset.visibility", action)],             (shift, ctrl, alt, [k.idname for k in got])
    alt_h = _kmis("Mesh", "H", alt=True)
    assert [k.idname for k in alt_h] == ["mesh.hide"] and alt_h[0].properties.unselected
    for mods in ({"shift": True}, {"ctrl": True, "shift": True}, {"ctrl": True, "alt": True}):
        assert [k.idname for k in _kmis("Mesh", "H", **mods)] == ["mesh.reveal"], mods


def test_isolate_and_invert_keys():
    got = _items("3D View", "ONE", ctrl=True)
    assert [g[0] for g in got] == ["view3d.localview"], got
    km = bpy.context.window_manager.keyconfigs[KC].keymaps["3D View"]
    kmi = next(k for k in km.keymap_items if k.idname == "view3d.localview" and k.ctrl and k.type == 'ONE')
    assert kmi.properties.frame_selected is False, "isolate keeps the camera"
    assert _items("Mesh", "ONE", ctrl=True) == [], "Mesh Ctrl+1 vertex mode removed"
    assert [g[0] for g in _items("Object Mode", "I", ctrl=True, shift=True)] == ["object.select_all"]
    assert [g[0] for g in _items("Mesh", "I", ctrl=True, shift=True)] == ["mesh.select_all"]


# --- allset.visibility -------------------------------------------------------------

def _scene(names=("a", "b", "c")):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    obs = []
    for n in names:
        ob = bpy.data.objects.new(n, None)
        bpy.context.scene.collection.objects.link(ob)
        obs.append(ob)
    bpy.context.view_layer.update()
    return obs


def _select(*obs):
    for o in bpy.context.view_layer.objects:
        o.select_set(o in obs)
    if obs:
        bpy.context.view_layer.objects.active = obs[0]


def _vis(action):
    assert bpy.ops.allset.visibility(action=action) == {'FINISHED'}


def test_h_toggles_and_keeps_selection():
    a, b, c = _scene()
    _select(a, b)
    _vis('TOGGLE')
    assert a.hide_get() and b.hide_get() and not c.hide_get()
    _vis('TOGGLE')   # nothing visible selected: the kept selection comes back, selected
    assert not a.hide_get() and not b.hide_get()
    assert a.select_get() and b.select_get() and not c.select_get()
    assert visibility.KEPT not in a and visibility.KEPT not in b


def test_h_new_selection_replaces_kept():
    a, b, c = _scene()
    _select(a)
    _vis('TOGGLE')
    _select(b)
    _vis('TOGGLE')          # hides b; a is no longer the kept selection
    _vis('TOGGLE')          # shows b only
    assert not b.hide_get() and a.hide_get()


def test_hide_show_last_and_selected():
    a, b, c = _scene()
    _select(a)
    _vis('HIDE')
    assert a.hide_get() and not a.select_get()
    _select(b)
    _vis('HIDE_UNSELECTED')                 # hides c (a is already hidden)
    assert c.hide_get() and not b.hide_get()
    _vis('SHOW_LAST')                       # last hide = c only
    assert not c.hide_get() and a.hide_get() and c.select_get()
    bpy.context.view_layer.objects.active = a   # e.g. picked in the Outliner
    _vis('SHOW_SELECTED')
    assert not a.hide_get() and a.select_get()


def test_show_selected_uses_kept():
    a, b, c = _scene()
    _select(a, b)
    _vis('TOGGLE')
    _select(c)
    _vis('SHOW_SELECTED')
    assert not a.hide_get() and not b.hide_get()
