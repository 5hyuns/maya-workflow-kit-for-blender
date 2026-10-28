"""Step 152 (#101) main: Maya option windows of Render > Render Sequence ❒ / Batch Render ❒ and Maya's warning for
Render Current Frame ❒."""

from importlib import import_module

import bpy

import kit

ow = import_module(kit.MODULE + ".operators.option_windows")
owr = import_module(kit.MODULE + ".operators.option_windows_render")
render_batch = import_module(kit.MODULE + ".operators.render_batch")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")


def _w(key):
    return next(w for w in ow.WINDOWS if w.key == key)


def test_render_sequence_window_is_maya():
    w = _w("render_sequence")
    assert (w.title, w.action, w.apply_text) == ("Render Sequence (Current Frame)", "Render Sequence and Close",
                                                "Render Sequence")
    assert [(f.name, f.label, f.default) for f in w.fields] == [
        ("camera", "Current Camera:", "persp"), ("output", "Alternate Output File Location:", "")]
    assert "Render Region" in w.missing and "All Render-Enabled Cameras" in w.missing
    assert menu_sets.option_kind("Render/Render Sequence") == "window"
    assert hasattr(bpy.ops.allset, "opt_render_sequence")


def test_batch_render_window_and_threads():
    w = _w("batch_render")
    assert (w.title, w.action, w.apply_text) == ("Batch Render Frame", "Batch render and close", "Batch render")
    assert [(f.name, f.default) for f in w.fields] == [("all_processors", True), ("processors", 0)]
    assert menu_sets.option_kind("Render/Batch Render") == "window"
    cmd = render_batch.command("c.blend", "out", ["-a"], threads=4)
    assert cmd[1:] == ["-b", "c.blend", "-t", "4", "-o", "out", "-a"], cmd
    assert "-t" not in render_batch.command("c.blend", "out", ["-a"])


def test_render_current_frame_box_is_maya_warning():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    assert owr.no_options_text("Render/Render Current Frame", scene) == \
        'Renderer "Cycles" does not provide render options.'
    assert owr.no_options_text("Render/IPR Render Current Frame", scene).endswith("does not provide IPR options.")
    assert owr.no_options_text("Render/Render Sequence", scene) is None
    assert menu_sets.option_kind("Render/Render Current Frame") == "generic"
    # the generic option box reports the warning and opens nothing (its invoke; in -b INVOKE runs execute)
    import inspect
    assert "no_options_text" in inspect.getsource(ow.ALLSET_OT_option_generic.invoke)


def test_render_sequence_camera_choice():
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    cam.name = "shotCam"
    items = [i[0] for i in owr._cameras(None, bpy.context)]
    assert items[0] == "persp" and "shotCam" in items
