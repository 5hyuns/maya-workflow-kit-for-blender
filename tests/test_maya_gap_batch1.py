"""Maya items that were greyed or collapsed: Display > Hide / Show submenus and types, Time Slider Bookmarks, Mesh >
Booleans Slice / Hole Punch / Cut Out / Split Edges (results checked against Maya 2026 polyCBoolOp on the same cubes)."""

from importlib import import_module

import bmesh
import bpy

import kit

menu_map = import_module(kit.MODULE + ".ui.menu_map")
visibility = import_module(kit.MODULE + ".operators.visibility")


def _clear():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.context.scene.timeline_markers.clear()


def _add(name, data):
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _run(path):
    kind, target, props = menu_map.spec(path)
    mod, _, name = target.partition(".")
    return getattr(getattr(bpy.ops, mod), name)(**props)


def test_hide_show_submenus_draw_and_shelf_paths_still_resolve():
    assert menu_map.is_submenu("Display/Hide", [("x",)]) and menu_map.is_submenu("Display/Show", [("x",)])
    assert "Display/Hide" in menu_map.MAP and "Display/Show" in menu_map.MAP      # saved shelf buttons
    assert not menu_map.is_submenu("Display/Grid", None)


def test_hide_and_show_by_type():
    _clear()
    cube = _add("pCube1", bpy.data.meshes.new("m"))
    lamp = _add("pointLight1", bpy.data.lights.new("l", 'POINT'))
    rig = _add("joint1", bpy.data.armatures.new("a"))
    _run("Display/Hide/Lights")
    assert lamp.hide_viewport and not cube.hide_viewport and not rig.hide_viewport
    _run("Display/Hide/Hide Kinematics/Joints")
    assert rig.hide_viewport and not cube.hide_viewport
    _run("Display/Show/Lights")
    assert not lamp.hide_viewport and rig.hide_viewport
    _run("Display/Hide/Hide Geometry/Polygon Surfaces")
    assert cube.hide_viewport
    _run("Display/Show/All")
    assert not any(o.hide_viewport for o in (cube, lamp, rig))
    _run("Display/Hide/All")
    assert all(o.hide_viewport for o in (cube, lamp, rig))


def test_bookmark_menu_items():
    _clear()
    scene = bpy.context.scene
    for path in ("Create", "Next Bookmark", "Frame Bookmark", "Unframe", "Delete", "Delete All Bookmarks"):
        assert menu_map.spec(f"Visualize/Time Slider Bookmarks/{path}") is not None, path
    scene.timeline_markers.new("bookmark1", frame=10)
    scene.timeline_markers.new("bookmark2", frame=30)
    scene.frame_current = 12
    _run("Visualize/Time Slider Bookmarks/Delete")
    assert [m.name for m in scene.timeline_markers] == ["bookmark2"]
    _run("Visualize/Time Slider Bookmarks/Delete All Bookmarks")
    assert len(scene.timeline_markers) == 0


def _cubes():
    """Maya's test: A = 2-unit cube at the origin, B = 1-unit cube at x=1 (straddles A's +X face)."""
    _clear()
    obs = []
    for name, size, x in (("A", 2.0, 0.0), ("B", 1.0, 1.0)):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=size)
        bm.to_mesh(me)
        bm.free()
        ob = _add(name, me)
        ob.location.x = x
        obs.append(ob)
    a, b = obs
    for o in bpy.context.scene.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = b      # Blender's last pick = Maya's second
    bpy.context.view_layer.update()
    return a


def _stats(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    border = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    area = sum(f.calc_area() for f in bm.faces)
    shells, seen = 0, set()
    for f in bm.faces:
        if f.index in seen:
            continue
        shells += 1
        stack = [f]
        while stack:
            g = stack.pop()
            if g.index in seen:
                continue
            seen.add(g.index)
            stack.extend(h for e in g.edges for h in e.link_faces if h.index not in seen)
    xs = [v.co.x for v in bm.verts]
    bm.free()
    return shells, border, round(area, 4), round(min(xs), 4), round(max(xs), 4)


def _bool(label):
    a = _cubes()
    _run(f"Mesh/Booleans/{label}")
    assert "B" not in bpy.data.objects, "the cutter is used up (Maya with history off)"
    return _stats(a)


def test_boolean_slice():
    shells, border, area, lo, hi = _bool("Slice")
    assert (shells, border) == (2, 0)                     # Maya: 2 closed shells
    assert area == 30.0       # outside shell 23 + 3 of B's walls, inside shell 1 + the same 3 walls
    assert (lo, hi) == (-1.0, 1.0)                        # Maya bbox x: -1 .. 1


def test_boolean_hole_punch():
    shells, border, area, lo, hi = _bool("Hole Punch")
    assert shells == 1 and border == 4                    # Maya: open hole, 4 border edges
    assert area == 23.0 and (lo, hi) == (-1.0, 1.0)       # A's 24 minus the 1x1 patch inside B


def test_boolean_cut_out():
    shells, border, area, lo, hi = _bool("Cut Out")
    assert shells == 1 and border == 4                    # Maya: one open patch
    assert area == 1.0 and (lo, hi) == (1.0, 1.0)         # Maya bbox x: 1 .. 1


def test_boolean_split_edges():
    shells, border, area, lo, hi = _bool("Split Edges")
    assert (shells, border) == (1, 0)                     # Maya: closed, nothing removed
    assert area == 24.0 and (lo, hi) == (-1.0, 1.0)
