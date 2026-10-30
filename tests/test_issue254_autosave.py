"""Issue #254: project autosave — copies of the open scene in ``<project>/autosave`` every N minutes, numbered
``<scene>.NNNN.blend``, oldest removed past the limit, the open file's path and unsaved state untouched."""

import os
import tempfile
from importlib import import_module

import bpy

import kit

autosave = import_module(kit.MODULE + ".operators.autosave")
project = import_module(kit.MODULE + ".operators.project")
preferences = import_module(kit.MODULE + ".preferences")
prefs_data = import_module(kit.MODULE + ".ui.maya_prefs_data")


def _prefs():
    return preferences.get()


def _setup(root=None, interval=1.0, limit=False, count=3):
    p = _prefs()
    if root is None:
        root = os.path.join(tempfile.mkdtemp(prefix="as254_"), "proj")
        project.create_project(root)
    p.project_root = root
    p.autosave_destination = 'PROJECT'
    p.autosave_folder = ""
    p.autosave_enable = True
    p.autosave_interval = interval
    p.autosave_limit = limit
    p.autosave_count = count
    autosave.reset(0.0)
    return root


def _teardown():
    p = _prefs()
    for attr in ("autosave_enable", "autosave_interval", "autosave_limit", "autosave_count",
                 "autosave_destination", "autosave_folder", "project_root"):
        p.property_unset(attr)
    autosave.reset(None)
    autosave._state["last"] = None


def _edit():
    """A change to the scene: marks the file dirty and the kit's change flag."""
    bpy.ops.mesh.primitive_cube_add()
    bpy.context.view_layer.update()
    bpy.ops.ed.undo_push(message="edit")     # an undo step marks the file modified (as in the UI)
    autosave._state["changed"] = True
    assert bpy.data.is_dirty


def _tick(now):
    return autosave.tick(bpy.context, now=now, allow_background=True)


def test_registered_with_maya_mode():
    assert bpy.app.timers.is_registered(autosave._timer)
    assert autosave._on_change in bpy.app.handlers.depsgraph_update_post
    assert autosave._on_load_post in bpy.app.handlers.load_post


def test_off_writes_nothing():
    root = _setup()
    try:
        _prefs().autosave_enable = False
        _edit()
        path, _wait = _tick(10_000.0)
        assert path is None
        assert not os.listdir(os.path.join(root, "autosave"))
    finally:
        _teardown()


def test_untitled_scene_saved_into_project_autosave_folder():
    root = _setup(interval=1.0)
    try:
        assert bpy.data.filepath == ""
        _edit()
        assert _tick(30.0)[0] is None, "saved before the interval passed"
        path, _wait = _tick(61.0)
        assert path == os.path.join(root, "autosave", "untitled.0001.blend"), path
        assert os.path.isfile(path)
        # the open scene is untouched: still untitled and unsaved
        assert bpy.data.filepath == ""
        assert bpy.data.is_dirty
    finally:
        _teardown()


def test_unchanged_scene_is_not_saved_again():
    root = _setup(interval=1.0)
    try:
        _edit()
        assert _tick(61.0)[0] is not None
        assert _tick(130.0)[0] is None, "no change since the last autosave"
        _edit()
        assert _tick(150.0)[0] is None, "the interval starts again after a skipped check"
        path = _tick(200.0)[0]
        assert path is not None and path.endswith("untitled.0002.blend"), path
        assert len(autosave.copies(os.path.join(root, "autosave"), "untitled")) == 2
    finally:
        _teardown()


def test_limit_removes_oldest():
    root = _setup(interval=1.0, limit=True, count=2)
    try:
        t = 0.0
        for _i in range(4):
            _edit()
            t += 61.0
            assert _tick(t)[0] is not None
        left = autosave.copies(os.path.join(root, "autosave"), "untitled")
        assert [n for n, _p in left] == [3, 4], left
    finally:
        _teardown()


def test_follows_project_change_and_named_folder():
    root = _setup(interval=1.0)
    try:
        other = os.path.join(tempfile.mkdtemp(prefix="as254b_"), "other")
        project.create_project(other)
        _prefs().project_root = other
        _edit()
        path = _tick(61.0)[0]
        assert os.path.dirname(path) == os.path.join(other, "autosave"), path
        named = tempfile.mkdtemp(prefix="as254c_")
        _prefs().autosave_destination = 'FOLDER'
        _prefs().autosave_folder = named
        _edit()
        path = _tick(130.0)[0]
        assert os.path.dirname(path) == named, path
        assert not os.listdir(os.path.join(root, "autosave"))
    finally:
        _teardown()


def test_default_project_when_none_set():
    _setup(interval=1.0)
    try:
        _prefs().project_root = ""
        _edit()
        path = _tick(61.0)[0]
        assert os.path.dirname(path) == os.path.join(project.default_root(), "autosave"), path
        assert os.environ.get("ALLSET_PROJECTS_DIR"), "tests must run in the sandbox projects folder"
        os.remove(path)
    finally:
        _teardown()


def test_render_output_not_rewritten_by_autosave():
    _setup(interval=1.0)
    try:
        scene = bpy.context.scene
        scene.render.filepath = "/tmp\\"
        _edit()
        assert _tick(61.0)[0] is not None
        assert scene.render.filepath == "/tmp\\", scene.render.filepath
    finally:
        _teardown()


def test_background_session_never_autosaves():
    _setup(interval=1.0)
    try:
        _edit()
        path, _wait = autosave.tick(bpy.context, now=61.0)
        assert path is None
    finally:
        _teardown()


def test_naming_helpers():
    folder = tempfile.mkdtemp(prefix="as254d_")
    assert autosave.next_path(folder, "a") == os.path.join(folder, "a.0001.blend")
    for name in ("a.0001.blend", "a.0007.blend", "ab.0009.blend", "a.blend", "a.0002.blend1"):
        open(os.path.join(folder, name), "wb").close()
    assert [n for n, _p in autosave.copies(folder, "a")] == [1, 7]
    assert autosave.next_path(folder, "a").endswith("a.0008.blend")
    assert autosave.prune(folder, "a", 1) == [os.path.join(folder, "a.0001.blend")]
    assert os.path.isfile(os.path.join(folder, "ab.0009.blend"))
    assert autosave.scene_stem("") == "untitled"
    assert autosave.scene_stem("C:/x/shot_v2.blend") == "shot_v2"


def test_prefs_window_rows():
    rows = [r for _k, sec, r in prefs_data.rows() if sec == "AutoSave"]
    attrs = [r[1] for r in rows if r[0] == "pref"]
    assert attrs[:4] == ["autosave_enable", "autosave_interval", "autosave_limit", "autosave_count"], attrs
    for attr in attrs:
        assert hasattr(_prefs(), attr), attr


def test_saved_scene_named_after_its_file_and_keeps_its_path():
    root = _setup(interval=1.0)
    try:
        scene_path = os.path.join(root, "scenes", "shot.blend")
        bpy.ops.wm.save_as_mainfile(filepath=scene_path)
        autosave.reset(0.0)
        before = os.path.getmtime(scene_path)
        _edit()
        path = _tick(61.0)[0]
        assert path == os.path.join(root, "autosave", "shot.0001.blend"), path
        assert bpy.data.filepath == scene_path
        assert bpy.data.is_dirty, "the autosave copy cleared the scene's unsaved state"
        assert os.path.getmtime(scene_path) == before, "the scene's own file was written"
        # the copy opens as the scene with the new cube
        with bpy.data.libraries.load(path) as (src, _dst):
            assert "Cube" in src.objects
    finally:
        _teardown()


def test_disable_removes_timer_and_handlers():
    kit.disable()
    try:
        assert not bpy.app.timers.is_registered(autosave._timer)
        for name, fn in autosave._HANDLERS:
            assert fn not in getattr(bpy.app.handlers, name), name
    finally:
        kit.enable()
