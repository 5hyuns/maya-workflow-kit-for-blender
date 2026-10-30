"""View > Select Camera in a view that looks through no camera (#229): Maya selects the panel's own camera — persp
in a perspective view, top / front / side in those orthographic views — which a Maya scene always has."""

from importlib import import_module

import bpy
from mathutils import Euler

import kit
from test_step37_panel_menus import Ctx, _space

pm = import_module(kit.MODULE + ".ui.panel_menus")
sc = import_module(kit.MODULE + ".operators.startup_cameras")


def test_select_camera_picks_the_startup_camera_of_the_view():
    sc.ensure(bpy.context.scene, bpy.context.view_layer)
    space = _space()
    rv3d = space.region_3d
    ctx = Ctx(space)
    rv3d.view_perspective = 'PERSP'
    bpy.data.objects["Cube"].select_set(True)
    assert pm.apply(ctx, "SELECT_CAMERA")
    assert not bpy.data.objects["Cube"].select_get()
    lead = bpy.context.view_layer.objects.active
    assert lead is not None and lead.get(sc.MARK) == "persp", lead
    # top (looking down -Z), front (looking along +Y), side = right view (looking along -X)
    for name, rot in (("top", (0, 0, 0)), ("front", (90, 0, 0)), ("side", (90, 0, 90))):
        rv3d.view_perspective = 'ORTHO'
        rv3d.view_rotation = Euler([a * 3.141592653589793 / 180 for a in rot]).to_quaternion()
        assert pm.apply(ctx, "SELECT_CAMERA"), name
        lead = bpy.context.view_layer.objects.active
        assert lead.get(sc.MARK) == name, (name, lead.name)
        # the startup cameras are hidden (Maya Visibility off): Blender keeps them out of the selection, so the
        # camera is the lead (Channel Box) and nothing else stays selected
        selected = [o.name for o in bpy.context.view_layer.objects if o is not None and o.select_get()]
        assert selected in ([], [lead.name]), selected
    rv3d.view_perspective = 'PERSP'
