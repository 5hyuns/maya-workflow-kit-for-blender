"""#370: Create > Measure Tools > Distance Tool makes Maya's locators and distance dimension.

Two points -> locator1, locator2 (kit locators) and distanceDimension1 (an empty the Outliner lists) whose drawn
number is the distance in Maya units; moving a locator changes it; a measurement from an existing locator's point uses
that locator; one measurement is one undo step; save / reload keeps it. The drawing's screen geometry (dimension line
set off to one side, arrowheads, dotted lines) is checked as plain numbers; tests/gui/gui_issue370_distance_tool.py
clicks the tool in a real view."""

import os
from importlib import import_module

import bpy
from mathutils import Vector

import kit


def m(name):
    return import_module(f"{kit.MODULE}.{name}")


def _dt():
    return m("operators.distance_tool")


def _u():
    return m("operators.units").maya_unit(bpy.context.scene)


def _clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)


def _measure(start, end):
    return bpy.ops.allset.distance_click('EXEC_DEFAULT', True, start=start, end=end)


def test_label_like_maya():
    label = _dt().label
    assert label(10.0) == "10"
    assert label(5.0) == "5"
    assert label(10.001243303301477) == "10.001243"
    assert label(13.4571449409172) == "13.457145"
    assert label(8.005224489796152) == "8.005224"
    assert label(1.7320508075688772) == "1.732051"
    assert label(13.4571449409172, 3) == "13.457"
    assert label(0.0) == "0"


def test_measure_names_distance_selection_undo():
    _clear()
    dt, u = _dt(), _u()
    bpy.ops.ed.undo_push(message="start")
    assert _measure((0, 0, 0), (3, 4, 0)) == {'FINISHED'}
    names = sorted(ob.name for ob in bpy.data.objects)
    assert names == ["distanceDimension1", "locator1", "locator2"], names
    dd = bpy.data.objects["distanceDimension1"]
    a, b = dt.ends(dd)
    assert (a.name, b.name) == ("locator1", "locator2"), (a, b)
    assert all(dt.is_locator(ob) and abs(ob.empty_display_size - u) < 1e-9 for ob in (a, b))
    assert (b.location - Vector((3 * u, 4 * u, 0))).length < 1e-6, b.location
    assert dd.type == 'EMPTY' and dd.empty_display_size < 1e-3 and dd.location.length == 0.0, dd.empty_display_size
    assert dd.users_collection, "listed in the Outliner (in a collection)"
    assert abs(dt.distance(dd) - 5.0) < 1e-6, dt.distance(dd)
    assert dt.label(dt.distance(dd)) == "5"
    sel = sorted(ob.name for ob in bpy.context.selected_objects)
    assert sel == ["distanceDimension1", "locator2"] and bpy.context.view_layer.objects.active == dd, sel

    # moving a locator changes the distance
    b.location = (6 * u, 8 * u, 0)
    bpy.context.view_layer.update()
    assert abs(dt.distance(dd) - 10.0) < 1e-6, dt.distance(dd)
    bpy.ops.ed.undo_push(message="move locator2")

    # a measurement from locator2's point measures from locator2
    assert _measure((6, 8, 0), (6, 8, 10)) == {'FINISHED'}
    dd2 = bpy.data.objects["distanceDimension2"]
    a2, b2 = dt.ends(dd2)
    assert (a2.name, b2.name) == ("locator2", "locator3"), (a2, b2)
    assert len([ob for ob in bpy.data.objects if dt.is_locator(ob)]) == 3
    assert abs(dt.distance(dd2) - 10.0) < 1e-6

    # one undo takes the whole measurement back
    bpy.ops.ed.undo()
    names = sorted(ob.name for ob in bpy.data.objects)
    assert names == ["distanceDimension1", "locator1", "locator2"], names
    dd = bpy.data.objects["distanceDimension1"]
    assert abs(_dt().distance(dd) - 10.0) < 1e-6
    bpy.ops.ed.undo()                                   # the move (an undo step of its own here)
    bpy.ops.ed.undo()                                   # the first measurement
    assert not [ob for ob in bpy.data.objects], [ob.name for ob in bpy.data.objects]


def test_save_and_reload():
    _clear()
    dt = _dt()
    _measure((0, 0, 0), (0, 0, 7))
    path = os.path.join(os.path.dirname(os.path.abspath(bpy.utils.user_resource('CONFIG'))), "issue370.blend")
    assert "tmp" in path.replace("\\", "/").split("/"), path
    bpy.ops.wm.save_as_mainfile(filepath=path)
    try:
        bpy.ops.wm.open_mainfile(filepath=path)
        dt = _dt()
        dd = bpy.data.objects["distanceDimension1"]
        assert dt.is_dimension(dd)
        a, b = dt.ends(dd)
        assert (a.name, b.name) == ("locator1", "locator2"), (a, b)
        assert abs(dt.distance(dd) - 7.0) < 1e-6, dt.distance(dd)
    finally:
        os.remove(path)


def test_same_point_twice_is_nothing():
    _clear()
    bpy.ops.ed.undo_push(message="start")
    assert _measure((1, 1, 1), (1, 1, 1)) == {'CANCELLED'}
    assert not bpy.data.objects


def test_deleting_a_locator_deletes_its_dimensions():
    _clear()
    _measure((0, 0, 0), (2, 0, 0))
    _measure((2, 0, 0), (2, 3, 0))                      # distanceDimension2 from locator2
    for ob in bpy.context.view_layer.objects:
        ob.select_set(ob.name == "locator1")
    assert bpy.ops.allset.delete() == {'FINISHED'}      # Maya Delete
    names = sorted(ob.name for ob in bpy.data.objects)
    assert names == ["distanceDimension2", "locator2", "locator3"], names


def test_screen_geometry():
    dd = m("ui.distance_dimensions")
    # region y up (height 698): for a line drawn from upper left to lower right on screen, the dimension line is
    # set off down and to the left, like Maya
    a, b = Vector((352, 698 - 236)), Vector((522, 698 - 463))
    a2, b2 = dd.dimension_line(a, b)
    assert abs((a2 - a).length - dd.OFFSET_PX) < 1e-3
    assert a2.x < a.x and a2.y < a.y, a2               # left, and down on screen
    assert abs((a2 - a).normalized().dot((b - a).normalized())) < 1e-4, "at right angles to the line between the points"
    assert (b2 - b - (a2 - a)).length < 1e-3, "both ends set off the same"
    # a line drawn straight up the screen: the dimension line is to its right
    a2, _b2 = dd.dimension_line((522, 100), (522, 400))
    assert abs(a2.x - (522 + dd.OFFSET_PX)) < 1e-3 and abs(a2.y - 100) < 1e-3, a2
    # the same direction turned round: the other side
    a2, _b2 = dd.dimension_line((522, 400), (522, 100))
    assert a2.x < 522
    tip, c1, c2 = dd.arrowhead((0, 0), (100, 0))
    assert tip == Vector((0, 0)) and c1.x == c2.x == dd.ARROW_PX and abs(c1.y + c2.y) < 1e-9
    segs = dd.dots((0, 0), (20, 0))
    assert len(segs) == 5 and segs[0][0] == Vector((0, 0)) and segs[-1][1].x <= 20, segs
    assert dd.segment_distance_px((5, 3), (0, 0), (10, 0)) == 3.0
    assert dd.segment_distance_px((-4, 3), (0, 0), (10, 0)) == 5.0


def test_menu_item_and_tool():
    assert m("ui.menu_map").MAP["Create/Measure Tools/Distance Tool"] == ("tool", "allset.distance_tool", False)
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active

    def flat(items):
        for it in items:
            if type(it) is tuple:           # a group of tools (a ToolDef is a named tuple: not this)
                yield from flat(it)
            elif it is not None and not callable(it):
                yield getattr(it, "idname", None)
    for mode in ('OBJECT', 'EDIT_MESH'):
        assert "allset.distance_tool" in set(flat(VIEW3D_PT_tools_active._tools[mode])), mode


def test_maya_mode_off_takes_it_out():
    _clear()
    _measure((0, 0, 0), (1, 0, 0))
    dd = m("ui.distance_dimensions")
    assert dd._handle
    m("switch").set_mode(False, layout=False)
    try:
        assert not dd._handle and not dd._DIMS
        assert not _op_exists("allset.distance_click")
        from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active
        assert "allset.distance_tool" not in repr(VIEW3D_PT_tools_active._tools['OBJECT'])
        # the measurement stays in the file (objects of the scene)
        assert {"locator1", "locator2", "distanceDimension1"} <= {ob.name for ob in bpy.data.objects}
    finally:
        m("switch").set_mode(True, layout=False)


def _op_exists(idname):
    mod, name = idname.split(".")
    try:
        getattr(getattr(bpy.ops, mod), name).get_rna_type()
        return True
    except (AttributeError, KeyError):
        return False
