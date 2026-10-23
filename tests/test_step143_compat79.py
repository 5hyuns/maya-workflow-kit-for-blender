"""Step 143 / issue #79: Maya mode failed to switch on in Blender 5.2.3 with "'module' object is not iterable" —
ui/render_settings.registration_key read a render panel's module global ``classes`` and a third-party add-on's
module had a submodule there (``from . import classes``). Plan / cause: docs/steps/step_143_compat79.md."""

import types
from importlib import import_module

import bpy

import kit

AUTO_ENABLE = False

FAKE_MODULE = "fake79_addon.panels"


def _bound(func, module_name, classes):
    """``func`` with module globals as a third-party add-on module would have them."""
    globs = {"__name__": module_name, "classes": classes, "bpy": bpy}
    return types.FunctionType(func.__code__, globs, func.__name__)


def _poll(cls, context):
    return True


def _draw(self, context):
    self.layout.label(text="fake 79")


def _fake_panel(name, classes, module_name=FAKE_MODULE, register=False):
    cls = type(name, (bpy.types.Panel,), {
        "__module__": module_name,
        "bl_idname": name, "bl_label": name,
        "bl_space_type": 'PROPERTIES', "bl_region_type": 'WINDOW', "bl_context": "render",
        "poll": classmethod(_bound(_poll, module_name, classes)),
        "draw": _bound(_draw, module_name, classes),
    })
    return cls


def _weird_values():
    return [types.ModuleType("fake79_addon.classes"), 42, None, {"a": 1}, (c for c in ()), "classes", object()]


def test_registration_key_survives_non_sequence_classes():
    kit.enable(maya=False)
    try:
        rs = import_module(kit.MODULE + ".ui.render_settings")
        fakes = [_fake_panel(f"FAKE79_PT_bad{i}", v) for i, v in enumerate(_weird_values())]
        for cls in fakes:
            key = rs.registration_key(cls)        # raised TypeError for a module before the fix
            assert key == (1, 0, FAKE_MODULE, 0), (cls.__name__, key)
        # a well-formed tuple keeps its order
        good_a = _fake_panel("FAKE79_PT_good_a", ())
        good_b = _fake_panel("FAKE79_PT_good_b", ())
        tup = (good_b, good_a)
        good_a.poll = classmethod(_bound(_poll, FAKE_MODULE, tup))
        good_b.poll = classmethod(_bound(_poll, FAKE_MODULE, tup))
        assert rs.registration_key(good_b) < rs.registration_key(good_a)
        # bl_ui panels: the step 105 key, unchanged (module order, then the module's classes tuple)
        import bl_ui
        from bl_ui import properties_output
        order = list(getattr(bl_ui, "_modules", ()))
        for cls in properties_output.classes:
            if not issubclass(cls, bpy.types.Panel):
                continue
            seq = list(rs._module_names(cls).get("classes", ()) or ())     # the step 105 formula
            want = (0, order.index("properties_output") if "properties_output" in order else len(order), "",
                    seq.index(cls) if cls in seq else len(seq))
            assert rs.registration_key(cls) == want, (cls.__name__, rs.registration_key(cls), want)
        # sorting a mix: bl_ui first in their order, third-party after them, no exception
        mixed = fakes + [good_a, good_b] + [c for c in properties_output.classes if issubclass(c, bpy.types.Panel)]
        ordered = sorted(mixed, key=rs.registration_key)
        n_bl = sum(1 for c in mixed if c.__module__.startswith("bl_ui."))
        assert all(c.__module__.startswith("bl_ui.") for c in ordered[:n_bl])
        assert ordered.index(good_b) < ordered.index(good_a)
    finally:
        kit.disable()


def test_maya_mode_switches_on_with_a_bad_third_party_render_panel():
    """The issue's path: switch.set_mode(True) -> ui.render_settings.register -> wrap_panels with an add-on render
    panel whose module ``classes`` is a module."""
    bad = _fake_panel("FAKE79_PT_render", types.ModuleType("fake79_addon.classes"))
    bpy.utils.register_class(bad)
    try:
        kit.enable()                  # Maya mode on (raised "'module' object is not iterable" before the fix)
        try:
            switch = import_module(kit.MODULE + ".switch")
            rs = import_module(kit.MODULE + ".ui.render_settings")
            assert switch.is_on() and switch._registered[0], "Maya mode did not switch on"
            wrapped = [c for c, _raw, _kids in rs._wrapped]
            assert bad in wrapped and bad.is_registered
            names = [c.__name__ for c in wrapped]
            assert "RENDER_PT_context" in names
            # third-party panels come after Blender's
            assert names.index("FAKE79_PT_render") > names.index("RENDER_PT_context")
            assert bad.poll(bpy.context)           # outside the kit window: the add-on's own poll
        finally:
            kit.disable()
        assert bad.is_registered and "poll" in bad.__dict__
    finally:
        if bad.is_registered:
            bpy.utils.unregister_class(bad)
