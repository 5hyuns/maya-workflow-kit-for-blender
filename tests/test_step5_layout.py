"""Step 5: Maya layout app template (install/remove/load); no theme since step 130."""

import os
from importlib import import_module

import bpy

import kit

app_template = import_module(kit.MODULE + ".app_template")

SANDBOX_SCRIPTS = os.environ["BLENDER_USER_SCRIPTS"]


# --- install / remove ----------------------------------------------------------------

def test_install_into_user_templates_in_sandbox():
    assert bpy.ops.allset.layout_install() == {'FINISHED'}
    dst = app_template.installed_dir()
    assert os.path.normcase(dst).startswith(os.path.normcase(SANDBOX_SCRIPTS)), dst
    for name in ("startup.blend", app_template.MARKER):
        assert os.path.isfile(os.path.join(dst, name)), name
    assert app_template.is_installed()
    assert bpy.ops.allset.layout_install() == {'FINISHED'}, "reinstall over our own copy"


def test_remove_and_refuse_foreign_folder():
    assert bpy.ops.allset.layout_remove() == {'FINISHED'}
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
        ["splash.png", "splash_2x.png", "startup.blend"]   # data only, no code outside the extension (step 115)


# --- theme --------------------------------------------------------------------------------

def test_no_theme_in_the_kit():
    """Step 130 (#40): the kit ships no theme and has no theme operators; the user's theme is never written."""
    import importlib.util
    assert importlib.util.find_spec(kit.MODULE + ".theme") is None
    assert not hasattr(bpy.types, "ALLSET_OT_theme_apply") and not hasattr(bpy.types, "ALLSET_OT_theme_restore")
    root = os.path.dirname(import_module(kit.MODULE).__file__)
    xml = [os.path.join(d, f) for d, _s, fs in os.walk(root) for f in fs if f.endswith(".xml")]
    assert not xml, xml


# --- loading the template (last: replaces the open file) -----------------------------------

def test_template_layout():
    bpy.ops.allset.layout_install()
    bpy.ops.wm.read_homefile(app_template=app_template.TEMPLATE_ID)
    assert bpy.context.preferences.app_template == app_template.TEMPLATE_ID
    assert kit.is_enabled()
    ws = bpy.data.workspaces["General"]
    scr = ws.screens[0]
    types = sorted(a.type for a in scr.areas)
    # Maya General (step 49): Status Line row, Shelf row, Tool Box (narrow 3D View), Outliner, view,
    # Time + Range Slider (timeline); CB/LE, AE and MTK are Maya's right tab stack, its own Properties area (step 116).
    assert types == ['DOPESHEET_EDITOR', 'IMAGE_EDITOR', 'IMAGE_EDITOR', 'OUTLINER', 'PROPERTIES', 'VIEW_3D',
                     'VIEW_3D'], types
    outliners = [a.spaces.active for a in scr.areas if a.type == 'OUTLINER']
    assert outliners[0].use_filter_object and not outliners[0].use_filter_object_content, "DAG-only Outliner"
    v3d = max((a for a in scr.areas if a.type == 'VIEW_3D'), key=lambda a: a.width * a.height).spaces.active
    # no sidebar (the Maya panels are their own areas, step 116); the Tool Box column replaces the toolbar (step 49);
    # the tool header row is Maya's panel toolbar (step 113)
    assert not v3d.show_region_ui and not v3d.show_region_toolbar and v3d.show_region_tool_header
    # Maya persp angle (35 mm on 36 mm film) = Blender viewport lens 70 (72 mm sensor; step 81)
    assert abs(v3d.lens - 70.0) < 1e-6
    for area in scr.areas:
        if area.type == 'VIEW_3D':
            assert abs(area.spaces.active.lens - 70.0) < 1e-6, area

    scene = bpy.context.scene
    assert scene.unit_settings.length_unit == 'CENTIMETERS' and scene.unit_settings.scale_length == 1.0
    # step 20: Maya animation range 1-200 = frame range, playback 1-120 = preview range
    assert (scene.frame_start, scene.frame_end, scene.render.fps) == (1, 200, 24)
    assert scene.use_preview_range and (scene.frame_preview_start, scene.frame_preview_end) == (1, 120)
    assert len(bpy.data.objects) == 0, [o.name for o in bpy.data.objects]
    bpy.ops.allset.layout_remove()
