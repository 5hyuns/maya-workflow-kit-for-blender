"""#349: in Maya mode a file browser that picks a texture for an empty image slot starts in the current project's
sourceimages folder, like Maya; Blender's own start folder stays when the folder is missing (it is not made), the
Textures file path was changed, the slot already has an image or Maya mode is off.
GUI (real Open buttons, both file browser kinds): tests/gui/gui_issue349_sourceimages.py."""

import os
import tempfile
from importlib import import_module

import bpy

import kit

project = import_module(kit.MODULE + ".operators.project")
preferences = import_module(kit.MODULE + ".preferences")
switch = import_module(kit.MODULE + ".switch")


def _project(sourceimages=True):
    """A new current project; with or without its sourceimages folder."""
    root = os.path.join(tempfile.mkdtemp(prefix="mk349_"), "proj")
    project.create_project(root)
    if not sourceimages:
        os.rmdir(os.path.join(root, "sourceimages"))
    project.set_current(root)
    return root


def _same(a, b):
    return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))


def _hook_on():
    funcs = getattr(bpy.types.FILEBROWSER_PT_directory_path.draw, "_draw_funcs", [])
    return any(getattr(f, "__qualname__", "") == "_texture_browser" for f in funcs)


def test_empty_slot_starts_in_sourceimages():
    root = _project()
    folder = os.path.join(root, "sourceimages")
    assert _same(project.sourceimages_dir(), folder)
    assert bpy.context.preferences.filepaths.texture_directory == "//"
    # image.open on an empty slot starts at the Textures path ("//"); the kit's own dialogs pass nothing
    assert _same(project.texture_folder(bpy.context, "//"), folder)
    assert _same(project.texture_folder(bpy.context), folder)
    assert _hook_on(), "every file browser's path bar watches for texture dialogs in Maya mode"


def test_missing_folder_keeps_blenders_start_and_is_not_made():
    root = _project(sourceimages=False)
    assert project.sourceimages_dir() == ""
    assert project.texture_folder(bpy.context, "//") == ""
    assert project.texture_folder(bpy.context) == ""
    assert not os.path.exists(os.path.join(root, "sourceimages")), "sourceimages is never made for a dialog"


def test_default_project_not_made_yet_keeps_blenders_start():
    prefs = preferences.get()
    prefs.project_root = ""
    root = project.current_root()
    assert _same(root, project.default_root())
    if not os.path.isdir(os.path.join(root, "sourceimages")):
        assert project.texture_folder(bpy.context, "//") == ""
        assert not os.path.isdir(os.path.join(root, "sourceimages"))


def test_changed_textures_path_keeps_blenders_start():
    _project()
    paths = bpy.context.preferences.filepaths
    old = paths.texture_directory
    other = tempfile.mkdtemp(prefix="mk349_tex_")
    try:
        paths.texture_directory = other
        assert project.texture_folder(bpy.context, other) == ""
        assert project.texture_folder(bpy.context) == ""
        paths.texture_directory = "//textures/"
        assert project.texture_folder(bpy.context, "//textures/") == ""
    finally:
        paths.texture_directory = old


def test_slot_with_an_image_keeps_blenders_start():
    root = _project()
    # Blender starts at the slot image's file (a path with a file name), or at "" for an image without a file
    assert project.texture_folder(bpy.context, "//textures/wood.png") == ""
    assert project.texture_folder(bpy.context, os.path.join(root, "sourceimages", "wood.png")) == ""
    assert project.texture_folder(bpy.context, "") == ""


def test_maya_mode_off_keeps_blenders_start():
    _project()
    switch.set_mode(False)
    try:
        assert project.texture_folder(bpy.context, "//") == ""
        assert not _hook_on(), "Maya mode off: Blender's file browsers are left alone"
    finally:
        switch.set_mode(True, layout=False)
    assert _hook_on()
