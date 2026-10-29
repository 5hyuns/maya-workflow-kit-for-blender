"""Step 291: Display > Polygons is Maya's submenu (it opened Blender's edit-mode overlay popover). Its check items read
and set the overlays of the 3D View the menu acts on (the largest one when the menu is in the top bar); Normals Size...
is a small kit window whose slider is the overlay's Normal Size (live, open until OK); Reset Display is a kit
operator; the items without a Blender equivalent are greyed with a notice.
Kit: ui/menu_map.py, ui/status_line.view3d_space, ui/menu_sets.prop_owner, operators/poly_display.py, ui/notices.py."""

import inspect
import types
from importlib import import_module

import bpy

import kit

menu_data = import_module(kit.MODULE + ".ui.menu_data")
menu_map = import_module(kit.MODULE + ".ui.menu_map")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
notices = import_module(kit.MODULE + ".ui.notices")
status_line = import_module(kit.MODULE + ".ui.status_line")
poly_display = import_module(kit.MODULE + ".operators.poly_display")
marked_window = import_module(kit.MODULE + ".ui.marked_window")
window_places = import_module(kit.MODULE + ".ui.window_places")

POLYGONS = "Display/Polygons"


def _view():
    space = status_line.view3d_space(bpy.context)
    assert space is not None and space.type == 'VIEW_3D'
    return space


def _top_bar_context():
    """The context of a menu drawn in the top bar: its space has no overlays."""
    return types.SimpleNamespace(space_data=None, screen=bpy.context.screen)


def _children():
    display = next(it for it in menu_data.MENUS["mainDisplayMenu"][3] if it[0] == "Polygons")
    return display[1]


def _leaves(items, prefix):
    for it in items:
        if it[0] == "-":
            continue
        path = f"{prefix}/{it[0]}"
        if len(it) > 1:
            yield from _leaves(it[1], path)
        else:
            yield path


class _Layout:
    """Records what an item draws."""

    def __init__(self):
        self.log = []

    def prop(self, owner, attr, text="", **_kw):
        self.log.append(("prop", owner, attr, text))

    def prop_enum(self, owner, attr, value, text=""):
        self.log.append(("prop_enum", owner, attr, text))

    def operator(self, idname, text="", **_kw):
        props = types.SimpleNamespace()
        self.log.append(("op", idname, text, props))
        return props

    def label(self, text="", **_kw):
        self.log.append(("label", text))


def test_polygons_is_a_submenu_in_maya_order():
    assert POLYGONS not in menu_map.MAP            # a submenu now, not a leaf
    labels = [it[0] for it in _children() if it[0] != "-"]
    assert labels[:2] == ["Backface Culling", "Culling Options"]
    i = labels.index("Face Normals")
    assert labels[i:i + 4] == ["Face Normals", "Vertex Normals", "Tangents", "Normals Size..."]
    assert labels[-3:] == ["Reset Display", "Limit to Selected", "Custom Polygon Display"]
    assert f"{POLYGONS}/Custom Polygon Display" in menu_sets.OPTION_BOXES
    paths = {p for p, _it in menu_sets.iter_items()}
    assert f"{POLYGONS}/Face Normals" in paths


def test_every_leaf_mapped_or_noticed():
    for path in _leaves(_children(), POLYGONS):
        if path in menu_map.MAP:
            continue
        substitute, line = notices.NOTICES[path]          # its own notice, not the Display category
        assert substitute and "Blender" in line, (path, line)


def test_normals_are_check_boxes_of_the_main_view():
    for label, prop in (("Face Normals", "show_face_normals"), ("Vertex Normals", "show_vertex_normals")):
        assert menu_map.spec(f"{POLYGONS}/{label}") == ("prop", f"view3d.overlay.{prop}", {})
        owner, attr = menu_sets.prop_owner(_top_bar_context(), f"view3d.overlay.{prop}")
        assert owner == _view().overlay and attr == prop
    lay = _Layout()
    menu_sets.draw_item(lay, f"{POLYGONS}/Face Normals", "Face Normals")
    assert lay.log and lay.log[0][0] == "prop", lay.log
    assert lay.log[0][1] == _view().overlay and lay.log[0][2] == "show_face_normals"


def test_the_menu_s_own_view_wins():
    space = _view()
    ctx = types.SimpleNamespace(space_data=space, screen=None)
    owner, _attr = menu_sets.prop_owner(ctx, "view3d.shading.show_backface_culling")
    assert owner == space.shading


def test_greyed_without_a_3d_view():
    no_view = types.SimpleNamespace(space_data=None, screen=types.SimpleNamespace(areas=()))
    assert menu_sets.prop_owner(no_view, "view3d.overlay.show_face_normals")[0] is None
    assert menu_sets.set_prop(no_view, "view3d.overlay.show_face_normals", {}) == {'CANCELLED'}


def test_menu_item_toggles_the_overlay():
    overlay = _view().overlay
    overlay.show_face_normals = False
    assert bpy.ops.allset.menu_item(item=f"{POLYGONS}/Face Normals") == {'FINISHED'}
    assert overlay.show_face_normals is True
    bpy.ops.allset.menu_item(item=f"{POLYGONS}/Face Normals")
    assert overlay.show_face_normals is False
    shading = _view().shading
    shading.show_backface_culling = False
    bpy.ops.allset.menu_item(item=f"{POLYGONS}/Backface Culling")
    assert shading.show_backface_culling is True
    shading.show_backface_culling = False


def test_standard_and_soft_hard_edges_are_a_radio_pair():
    overlay = _view().overlay
    bpy.ops.allset.menu_item(item=f"{POLYGONS}/Standard Edges")
    assert overlay.show_edge_sharp is False
    bpy.ops.allset.menu_item(item=f"{POLYGONS}/Soft/Hard Edges")
    assert overlay.show_edge_sharp is True
    lay = _Layout()
    menu_sets.draw_item(lay, f"{POLYGONS}/Soft/Hard Edges", "Soft/Hard Edges")
    assert lay.log[0][0] == "op" and lay.log[0][1] == "allset.menu_set_value", lay.log


def test_normals_size_is_a_window_until_ok():
    # Maya's window stays open while the slider is dragged: a kit window, not a popup a click outside closes
    assert poly_display.KIND in marked_window.KINDS
    marks = [frozenset(v) for v in marked_window.KINDS.values()]
    assert len(marks) == len(set(marks)), "two marked windows share a flag pair"
    src = inspect.getsource(poly_display.ALLSET_OT_normals_size)
    assert "invoke_props_dialog" not in src and "open_window" in src
    assert menu_map.spec(f"{POLYGONS}/Normals Size...") == ("op", "allset.normals_size", {})
    assert poly_display.ALLSET_PT_normals_size.bl_category == "Tool"


def test_normals_size_slider_is_the_overlay_property():
    # the slider is the 3D View's own property: the normals follow it while it is dragged; OK closes the window.
    # Drawn in the kit window, whose screen has no 3D View: the main window's view is found
    ctx = types.SimpleNamespace(space_data=None, screen=types.SimpleNamespace(areas=()),
                                window_manager=bpy.context.window_manager)
    assert status_line.view3d_space(ctx) == _view()
    lay = _Layout()
    poly_display.draw(lay, ctx)
    assert ("prop", _view().overlay, "normals_length", "Normals Size") in lay.log, lay.log
    assert [e[1:3] for e in lay.log if e[0] == "op"] == [("allset.marked_window_close", "OK")]


def test_normals_size_opens_small_the_first_time():
    # seeded under the name the kit window is remembered by (else the first window copies the whole 3D View)
    assert poly_display.PLACE == f"marked:{poly_display.KIND}"
    assert 'f"marked:{kind}"' in inspect.getsource(marked_window.open_window)
    rect = poly_display.first_place(bpy.context)
    assert rect is not None
    window = bpy.context.window
    area = max(window.screen.areas, key=lambda a: a.width * a.height)
    scale = bpy.context.preferences.system.ui_scale or 1.0      # 0 in background
    assert rect[2:] == (int(poly_display.WINDOW_PX[0] * scale), int(poly_display.WINDOW_PX[1] * scale))
    rel = (rect[0] - window.x, rect[1] - window.y, rect[2], rect[3])
    bounds = (area.x, area.y, area.width, area.height)
    room = 2 * poly_display.WINDOW_MARGIN_PX
    if area.width > rect[2] + room and area.height > rect[3] + room:
        assert window_places.fit(rel, bounds) == rel          # inside the area: carved as it is


def test_reset_display_back_to_factory():
    space = _view()
    space.overlay.show_face_normals = space.overlay.show_vertex_normals = True
    space.overlay.normals_length = 1.5
    space.overlay.show_edge_sharp = False
    space.shading.show_backface_culling = True
    assert bpy.ops.allset.menu_item(item=f"{POLYGONS}/Reset Display") == {'FINISHED'}
    for owner, prop, value in poly_display.FACTORY:
        got = getattr(getattr(space, owner), prop)
        assert (abs(got - value) < 1e-6) if isinstance(value, float) else got == value, (prop, got)


def test_custom_polygon_display_is_the_overlay_popover():
    assert menu_map.spec(f"{POLYGONS}/Custom Polygon Display") == (
        "v3d", "wm.call_panel", {"name": "VIEW3D_PT_overlay_edit_mesh", "keep_open": True})
    assert hasattr(bpy.types, "VIEW3D_PT_overlay_edit_mesh")
    # vertex size / edge width are theme preferences: the items open them, they don't write them (#43)
    theme = bpy.context.preferences.themes[0].view_3d
    assert hasattr(theme, "vertex_size") and hasattr(theme, "edge_width")
    assert menu_map.spec(f"{POLYGONS}/Vertex Size...") == ("op", "screen.userpref_show", {"section": 'THEMES'})
    assert notices.tooltip(f"{POLYGONS}/Vertex Size...", mapped=True)


def test_a_place_cut_on_four_sides_still_counts_as_carved():
    # measured in Blender 5.2: the 340 x 120 place carved with four splits came out 338 x 116, 3 px higher; the old
    # 3 px slack took that for a failed carve and the window copied the whole 3D View
    rect = (62, 1163, 340, 120)
    assert window_places.carved((62, 1166, 338, 116), rect)
    assert not window_places.carved((403, 122, 1699, 1221), rect)
