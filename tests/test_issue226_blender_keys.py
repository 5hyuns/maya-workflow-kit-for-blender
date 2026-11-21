"""#226: "Keep Blender Keys" in the add-on preferences (off by default) keeps a few Blender keys next to the Maya keys
in the 3D View: Tab = Edit Mode toggle, Alt+E = Local View. Off = the Maya keys exactly as before; the keys come
and go with the preference, the Keyboard choice and Maya mode; other editors keep their Tab."""

from importlib import import_module

import bpy

import kit

keymap = import_module(kit.MODULE + ".keymap")
switch = import_module(kit.MODULE + ".switch")
ic_data = import_module(kit.MODULE + ".keymap.ic_data")
maya_patches = import_module(kit.MODULE + ".keymap.maya_patches")


def _prefs():
    return bpy.context.preferences.addons[kit.MODULE].preferences


def _value(v):
    """A keymap item property as plain data (a nested operator's properties by their own values)."""
    if isinstance(v, bpy.types.bpy_struct):
        return tuple(sorted((p, _value(getattr(v, p))) for p in v.keys()))
    return str(v)


def _signature():
    """Every add-on keyconfig item as plain data (keymap, operator, event, properties)."""
    kc = bpy.context.window_manager.keyconfigs.addon
    out = []
    for km in kc.keymaps:
        for k in km.keymap_items:
            props = tuple(sorted((p, _value(getattr(k.properties, p)))
                                 for p in (k.properties.keys() if k.properties else ())))
            out.append((km.name, km.space_type, k.idname, k.type, k.value, k.shift, k.ctrl, k.alt, k.oskey,
                        k.active, props))
    return sorted(out)


def _items(km_name, type, alt=False, ctrl=False, shift=False):
    kc = bpy.context.window_manager.keyconfigs.addon
    return [k for km in kc.keymaps if km.name == km_name for k in km.keymap_items
            if k.type == type and k.value == 'PRESS' and k.alt == alt and k.ctrl == ctrl and k.shift == shift
            and not k.oskey and k.active]


def _ids(km_name, type, **mods):
    return [k.idname for k in _items(km_name, type, **mods)]


def _tab_edit(km_name="Object Non-modal"):
    return [k for k in _items(km_name, 'TAB') if k.idname == "object.mode_set"
            and k.properties.mode == 'EDIT' and k.properties.toggle]


def _set(on, tab=True, local_view=True):
    p = _prefs()
    p.blender_key_tab = tab
    p.blender_key_local_view = local_view
    p.keep_blender_keys = on


# editors whose Tab must not change (the UV Editor, Graph Editor, Outliner, Properties ...)
_OTHER_TAB = ("UV Editor", "Graph Editor", "Outliner", "Property Editor", "Dopesheet Generic", "Image Generic")


def test_off_by_default_maya_keys_unchanged():
    p = _prefs()
    assert not p.keep_blender_keys and p.blender_key_tab and p.blender_key_local_view
    assert keymap.blender_keys() == ()
    assert not _tab_edit(), "no Tab edit toggle while the preference is off"
    assert _ids("3D View", 'TAB') == ["wm.search_menu"]
    assert "view3d.localview" not in _ids("3D View", 'E', alt=True)
    assert _ids("Object Mode", 'E', alt=True) == ["object.rotation_clear"]
    # the data the kit builds with no Blender keys is the plain Maya keymap
    plain = maya_patches.apply(ic_data.generate())
    assert maya_patches.apply(ic_data.generate(), ()) == plain


def test_on_adds_tab_and_alt_e_and_off_restores_exactly():
    before = _signature()
    other = {km: _ids(km, 'TAB') for km in _OTHER_TAB}
    _set(True)
    try:
        assert keymap.is_applied()
        assert keymap.blender_keys() == ("TAB", "LOCAL_VIEW")
        assert len(_tab_edit()) == 1, _ids("Object Non-modal", 'TAB')
        assert "wm.search_menu" not in _ids("3D View", 'TAB'), "the 3D View search on Tab gives way"
        assert _ids("Screen", 'F', ctrl=True) == ["wm.search_menu"], "the search stays on Ctrl+F"
        assert _ids("3D View", 'E', alt=True) == ["view3d.localview"]
        assert _ids("Object Mode", 'E', alt=True) == [] and _ids("Pose", 'E', alt=True) == []
        # Maya keys of the same keys stay
        assert _ids("Object Non-modal", 'TAB', ctrl=True) == ["object.posemode_toggle"]
        assert {km: _ids(km, 'TAB') for km in _OTHER_TAB} == other, "other editors keep their Tab"
        assert _ids("Outliner", 'E', alt=True) == ["outliner.collection_exclude_clear"]
    finally:
        _set(False)
    after = _signature()
    assert after == before, ("off again = the Maya keys exactly as before",
                             sorted(set(before) - set(after))[:10], sorted(set(after) - set(before))[:10])


def test_each_key_on_its_own():
    before = _signature()
    try:
        _set(True, tab=True, local_view=False)
        assert keymap.blender_keys() == ("TAB",)
        assert len(_tab_edit()) == 1 and "view3d.localview" not in _ids("3D View", 'E', alt=True)
        _set(True, tab=False, local_view=True)
        assert keymap.blender_keys() == ("LOCAL_VIEW",)
        assert not _tab_edit() and _ids("3D View", 'TAB') == ["wm.search_menu"]
        assert _ids("3D View", 'E', alt=True) == ["view3d.localview"]
        _set(True, tab=False, local_view=False)
        assert keymap.blender_keys() == ()
        assert _signature() == before
    finally:
        _set(False)
    assert _signature() == before


def test_blender_keyboard_and_maya_mode_off_take_them_out():
    _set(True)
    p = _prefs()
    try:
        p.keymap_set = 'BLENDER'
        try:
            assert not keymap.is_applied() and not _tab_edit()
            assert "view3d.localview" not in _ids("3D View", 'E', alt=True)
        finally:
            p.keymap_set = 'MAYA'
        assert len(_tab_edit()) == 1
        switch.set_mode(False, layout=False)
        try:
            assert not keymap.is_applied() and not _tab_edit()
            assert not [k for km in bpy.context.window_manager.keyconfigs.addon.keymaps for k in km.keymap_items
                        if k.idname in ("object.mode_set", "view3d.localview")]
            # changing the choice in Blender mode adds nothing
            p.keep_blender_keys = False
            p.keep_blender_keys = True
            assert not _tab_edit()
        finally:
            switch.set_mode(True, layout=False)
        assert len(_tab_edit()) == 1 and _ids("3D View", 'E', alt=True) == ["view3d.localview"]
    finally:
        _set(False)
    assert not _tab_edit()


def test_taken_out_on_disable():
    _set(True)
    try:
        kit.disable()
        assert not [k for km in bpy.context.window_manager.keyconfigs.addon.keymaps for k in km.keymap_items
                    if k.idname in ("object.mode_set", "view3d.localview")]
        kit.enable()
        _set(True)
        assert len(_tab_edit()) == 1 and _ids("3D View", 'E', alt=True) == ["view3d.localview"]
    finally:
        _set(False)
    assert not _tab_edit()
