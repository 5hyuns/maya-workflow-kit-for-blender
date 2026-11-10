"""#252: in Maya mode, Render Settings (Blender's Properties > Render tab, which the kit's Render Settings opens) has
Maya's Common settings: Skip existing frames and Renderable Cameras (each camera's Renderable check). Plain Blender
(Maya mode off) shows nothing new; disabling the kit removes the panel."""

import types
from importlib import import_module

import bpy

import kit

PANEL = "ALLSET_PT_render_common"


def _panel():
    return getattr(bpy.types, PANEL, None)


def _clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    bpy.context.scene.camera = None


def _camera(name):
    ob = bpy.data.objects.new(name, bpy.data.cameras.new(name + "Shape"))
    bpy.context.scene.collection.objects.link(ob)
    return ob


class _Rec:
    """A layout that records prop() calls as (data, property, text)."""

    def __init__(self, seen):
        self.seen = seen
        self.use_property_split = self.use_property_decorate = self.enabled = False

    def prop(self, data, name, **kw):
        self.seen.append((data, name, kw.get("text")))

    def __getattr__(self, name):
        return lambda *a, **kw: self


def _drawn():
    seen = []
    _panel().draw(types.SimpleNamespace(layout=_Rec(seen)), bpy.context)
    return seen


def test_panel_is_in_the_render_tab():
    cls = _panel()
    assert cls is not None, "Render Settings panel registered"
    assert (cls.bl_space_type, cls.bl_region_type, cls.bl_context) == ('PROPERTIES', 'WINDOW', 'render')
    assert cls.bl_label == "Common", "Maya's Render Settings tab name"
    assert cls.bl_parent_id == "RENDER_PT_context", "right under Render Engine, whatever order the editor keeps"
    rs = import_module(kit.MODULE + ".ui.status_line")
    assert "'RENDER'" in __import__("inspect").getsource(rs.ALLSET_OT_render_settings.execute), \
        "the kit's Render Settings opens this tab"


def test_poll_is_maya_mode_only():
    sw = import_module(kit.MODULE + ".switch")
    cls = _panel()
    assert cls.poll(bpy.context)
    sw.set_mode(False, layout=False)
    try:
        assert not cls.poll(bpy.context), "plain Blender sees nothing new"
    finally:
        sw.set_mode(True, layout=False)
    assert cls.poll(bpy.context)


def test_panel_rows_toggle_the_camera_and_the_output_options():
    _clear()
    a, b = _camera("camA"), _camera("camB")
    scene = bpy.context.scene
    seen = _drawn()
    rows = {(name, text): data for data, name, text in seen}
    assert ("allset_skip_existing", "Skip existing frames") in rows, seen
    assert rows[("allset_renderable", "camA")] == a.data and rows[("allset_renderable", "camB")] == b.data, seen
    # the panel's checks are the same properties as the Attribute Editor / option window ones
    holder = rows[("allset_renderable", "camB")]
    setattr(holder, "allset_renderable", False)
    assert not b.data.allset_renderable and a.data.allset_renderable
    rc = import_module(kit.MODULE + ".operators.render_cameras")
    assert [o.name for o in rc.renderable_cameras(scene)] == ["camA"]
    setattr(holder, "allset_renderable", True)
    r = scene.render
    r.use_overwrite, r.use_placeholder = True, False
    setattr(rows[("allset_skip_existing", "Skip existing frames")], "allset_skip_existing", True)
    assert (r.use_overwrite, r.use_placeholder) == (False, True)
    setattr(rows[("allset_skip_existing", "Skip existing frames")], "allset_skip_existing", False)
    assert (r.use_overwrite, r.use_placeholder) == (True, False)


def test_startup_cameras_listed_in_maya_order():
    _clear()
    startup = import_module(kit.MODULE + ".operators.startup_cameras")
    startup.ensure(bpy.context.scene)
    _camera("shotCam")
    names = [text for data, name, text in _drawn() if name == "allset_renderable"]
    assert names == ["persp", "top", "front", "side", "shotCam"], names


def test_disable_removes_the_panel():
    kit.disable()
    try:
        assert _panel() is None
    finally:
        kit.enable()
    assert _panel() is not None
