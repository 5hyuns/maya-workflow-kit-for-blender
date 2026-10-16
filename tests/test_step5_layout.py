"""Step 5: Maya layout app template (install/remove/load) and Maya theme."""

import os
from importlib import import_module

import bpy

import kit

app_template = import_module(kit.MODULE + ".app_template")
theme = import_module(kit.MODULE + ".theme")

SANDBOX_SCRIPTS = os.environ["BLENDER_USER_SCRIPTS"]


def _theme():
    return bpy.context.preferences.themes[0]


def _close(a, b, tol=2e-3):
    return all(abs(x - y) < tol for x, y in zip(a, b))


# --- install / remove ----------------------------------------------------------------

def test_install_into_user_templates_in_sandbox():
    assert bpy.ops.maya_kit.layout_install() == {'FINISHED'}
    dst = app_template.installed_dir()
    assert os.path.normcase(dst).startswith(os.path.normcase(SANDBOX_SCRIPTS)), dst
    for name in ("startup.blend", "__init__.py", app_template.MARKER):
        assert os.path.isfile(os.path.join(dst, name)), name
    assert app_template.is_installed()
    assert bpy.ops.maya_kit.layout_install() == {'FINISHED'}, "reinstall over our own copy"


def test_remove_and_refuse_foreign_folder():
    assert bpy.ops.maya_kit.layout_remove() == {'FINISHED'}
    assert not os.path.exists(app_template.installed_dir())
    assert app_template.remove() is False  # nothing to remove
    foreign = app_template.installed_dir()
    os.makedirs(foreign)
    with open(os.path.join(foreign, "keep.txt"), "w") as fh:
        fh.write("not ours")
    try:
        for fn in (app_template.install, app_template.remove):
            try:
                fn()
            except RuntimeError:
                pass
            else:
                raise AssertionError(f"{fn.__name__} touched a folder it did not create")
        assert os.path.isfile(os.path.join(foreign, "keep.txt"))
    finally:
        os.remove(os.path.join(foreign, "keep.txt"))
        os.rmdir(foreign)


def test_bundled_template_files():
    src = app_template.SOURCE_DIR
    assert sorted(f for f in os.listdir(src) if not f.startswith("__pycache__")) == \
        ["__init__.py", "startup.blend"]


# --- theme --------------------------------------------------------------------------------

def test_theme_apply_and_restore():
    grad = _theme().view_3d.space.gradients
    default_top = tuple(grad.high_gradient)
    default_type = grad.background_type
    assert not theme.has_backup()
    assert bpy.ops.maya_kit.theme_apply() == {'FINISHED'}
    assert theme.has_backup()
    assert grad.background_type == 'LINEAR'
    assert _close(grad.high_gradient, (0.535, 0.617, 0.702))           # Maya backgroundTop
    assert _close(_theme().dopesheet_editor.keyframe[:3], (1.0, 0.0, 0.0))  # timeSliderKey
    assert _close(_theme().user_interface.wcol_regular.inner[:3], (0x5d / 255,) * 3)
    path = theme.backup_path()
    assert os.path.normcase(path).startswith(
        os.path.normcase(os.path.dirname(os.environ["BLENDER_USER_EXTENSIONS"]))), path
    assert bpy.ops.maya_kit.theme_restore() == {'FINISHED'}
    assert not theme.has_backup()
    assert grad.background_type == default_type and _close(grad.high_gradient, default_top)


def test_theme_backup_keeps_first_original():
    _theme().view_3d.grid = (0.9, 0.1, 0.1, 1.0)   # a "user" theme tweak
    bpy.ops.maya_kit.theme_apply()
    bpy.ops.maya_kit.theme_apply()                 # second apply must not overwrite the backup
    bpy.ops.maya_kit.theme_restore()
    assert _close(_theme().view_3d.grid, (0.9, 0.1, 0.1, 1.0))
    bpy.ops.preferences.reset_default_theme()


# --- loading the template (last: replaces the open file) -----------------------------------

def test_template_layout():
    bpy.ops.maya_kit.layout_install()
    bpy.ops.wm.read_homefile(app_template=app_template.TEMPLATE_ID)
    assert bpy.context.preferences.app_template == app_template.TEMPLATE_ID
    assert kit.is_enabled()
    ws = bpy.data.workspaces["General"]
    scr = ws.screens[0]
    types = sorted(a.type for a in scr.areas)
    assert types == ['DOPESHEET_EDITOR', 'OUTLINER', 'OUTLINER', 'PROPERTIES', 'VIEW_3D'], types
    outliners = [a.spaces.active for a in scr.areas if a.type == 'OUTLINER']
    main = [s for s in outliners if s.use_filter_object]
    layers = [s for s in outliners if not s.use_filter_object]
    assert len(main) == 1 and not main[0].use_filter_object_content, "DAG-only Outliner"
    assert len(layers) == 1, "Layer Editor = collections-only Outliner"
    v3d = next(a.spaces.active for a in scr.areas if a.type == 'VIEW_3D')
    # tool header shown since step 7: it holds the Maya Status Line
    assert v3d.show_region_ui and v3d.show_region_toolbar and v3d.show_region_tool_header
    assert abs(v3d.lens - 35.0) < 1e-6
    props = next(a.spaces.active for a in scr.areas if a.type == 'PROPERTIES')
    assert props.context in {'OBJECT', 'SCENE'}, props.context  # no object yet -> Scene

    scene = bpy.context.scene
    assert scene.unit_settings.length_unit == 'CENTIMETERS' and scene.unit_settings.scale_length == 1.0
    assert (scene.frame_start, scene.frame_end, scene.render.fps) == (1, 120, 24)
    assert len(bpy.data.objects) == 0, [o.name for o in bpy.data.objects]
    bpy.ops.maya_kit.layout_remove()
