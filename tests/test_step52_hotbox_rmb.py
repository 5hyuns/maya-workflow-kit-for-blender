"""Step 52: hotbox and RMB marking menu as Maya 2022 shows them (research/maya/screens/13_hotbox.png,
14_marking_menu_object.png). Plan: docs/steps/step_52.md; GUI: tests/gui/gui_step52_hotbox_rmb.py."""

from importlib import import_module

import bpy

import kit

engine = import_module(kit.MODULE + ".marking.engine")
mm = import_module(kit.MODULE + ".marking.menus")
modal = import_module(kit.MODULE + ".marking.modal")
draw = import_module(kit.MODULE + ".marking.draw")

# Maya 2022 hotbox rows read off 13_hotbox.png (top to bottom). MASH is a plug-in menu (no kit data).
MAYA_ABOVE = [["File", "Edit", "Create", "Select", "Modify", "Display", "Windows", "Cache", "Help"],
              ["View", "Shading", "Lighting", "Show", "Renderer", "Panels"]]
MAYA_SIDES = ["Recent Commands", "Hotbox Controls"]
MAYA_BELOW = [["Mesh", "Edit Mesh", "Mesh Tools", "Mesh Display", "Curves", "Surfaces", "Deform", "UV", "Generate"],
              ["Skeleton", "Skin", "Deform", "Constrain", "Control"],
              ["Key", "Playback", "Audio", "Visualize", "Deform", "Constrain", "MASH"],
              ["nParticles", "Fluids", "nCloth", "nHair", "nConstraint", "nCache", "Fields/Solvers", "Effects", "MASH"],
              ["Lighting/Shading", "Texturing", "Render", "Toon", "Stereo"]]
PLUGIN = {"MASH"}

# Maya 2022 RMB list over pCube1 (14_marking_menu_object.png, dagMenuProc.mel:2582-2764), "-" = divider.
MAYA_RMB = ["pCube1...", "-", "Select", "Select All", "Deselect All", "Select Hierarchy", "Invert Selection", "-",
            "Select Similar", "-", "Make Live", "-", "DG Traversal", "Inputs", "Outputs", "Paint", "Metadata",
            "Actions", "UV Sets", "Color Sets", "Time Editor"]
SUBMENUS = {"DG Traversal", "Inputs", "Outputs", "Paint", "Metadata", "Actions", "UV Sets", "Color Sets",
            "Time Editor"}


def measure(text):
    return 7.0 * len(text)


def _labels(row):
    return [label for _key, label in row]


def test_hotbox_rows_are_maya_rows():
    above, sides, below = modal.hotbox_rows(bpy.context, area_type='VIEW_3D')
    assert [_labels(r) for r in above] == MAYA_ABOVE
    assert [label for _k, label in sides] == MAYA_SIDES
    assert [_labels(r) for r in below] == [[m for m in row if m not in PLUGIN] for row in MAYA_BELOW]
    # outside a 3D View there are no panel menus (Maya's pane-specific row)
    assert len(modal.hotbox_rows(bpy.context, area_type='OUTLINER')[0]) == 1


def test_hotbox_layout_like_maya():
    above, sides, below = modal.hotbox_rows(bpy.context, area_type='VIEW_3D')
    c = (800.0, 450.0)
    lay = engine.HotboxLayout(above, c, measure, below=below, side=sides, bounds=(0, 0, 1600, 900))
    assert lay.title == "Maya Workflow Kit" and abs((lay.center_rect[1] + lay.center_rect[3]) / 2 - c[1]) < 1e-6
    rows = {}
    for rect, _key, label in lay.labels:
        rows.setdefault(rect[1], []).append((rect[0], label))
    ys = sorted(rows, reverse=True)                      # top first
    order = [[label for _x, label in sorted(rows[y])] for y in ys]
    want = MAYA_ABOVE + [MAYA_SIDES] + [[m for m in row if m not in PLUGIN] for row in MAYA_BELOW]
    assert order == want, order
    pitch = [round(a - b, 3) for a, b in zip(ys, ys[1:])]
    assert set(pitch) == {35.0}, pitch                   # Maya: 26 px boxes, 9 px apart
    left, right = (r for r, k, _l in lay.labels if k in ("RECENT", "CONTROLS"))
    assert left[2] < lay.center_rect[0] and right[0] > lay.center_rect[2], "beside the centre box"
    assert len(lay.bands) == len(MAYA_ABOVE) + 2 + len(MAYA_BELOW)
    # four diagonal zone lines outside the rows
    assert len(lay.zone_lines) == 4
    top = max(r[3] for r, _k, _l in lay.labels)
    bottom = min(r[1] for r, _k, _l in lay.labels)
    for (x0, y0), (x1, y1) in lay.zone_lines:
        assert abs(abs(x0 - c[0]) - abs(y0 - c[1])) < 1e-6 and abs(abs(x1 - x0) - abs(y1 - y0)) < 1e-6
        assert min(y0, y1) > top or max(y0, y1) < bottom
    # zones still split on the diagonals
    assert lay.zone(c[0], c[1] + 300) == "N" and lay.zone(c[0] - 300, c[1]) == "W"


def test_hotbox_rows_near_edges_stay_inside():
    above, sides, below = modal.hotbox_rows(bpy.context, area_type='VIEW_3D')
    b = (0, 0, 1600, 900)
    for c in ((800.0, 860.0), (800.0, 40.0), (40.0, 450.0), (1560.0, 450.0)):
        lay = engine.HotboxLayout(above, c, measure, below=below, side=sides, bounds=b)
        rects = [r for r, k, _l in lay.labels if k not in ("RECENT", "CONTROLS")]
        assert all(b[0] - 1e-6 <= r[0] and r[2] <= b[2] + 1e-6 and b[1] - 1e-6 <= r[1] and r[3] <= b[3] + 1e-6
                   for r in rects), c
        assert not any(r[0] < lay.center_rect[2] and lay.center_rect[0] < r[2] and r[1] < lay.center_rect[3]
                       and lay.center_rect[1] < r[3] for r in rects), ("rows clear of the centre box", c)


def test_rmb_list_is_maya_2022():
    menu = mm.with_object_name(mm.RMB_MESH, "pCube1")
    got = ["-" if e == mm.DIVIDER else e[0] for e in menu.items][:len(MAYA_RMB)]
    assert got == MAYA_RMB, got
    tail = [e[0] for e in menu.items[len(MAYA_RMB):] if e != mm.DIVIDER]
    assert tail == ["Material Attributes...", "Assign New Material...", "Assign Favorite Material",
                    "Assign Existing Material"], tail                   # dagMenuProc.mel:2755-2764
    actions = {e[0]: e[1] for e in menu.items if e != mm.DIVIDER}
    assert all(isinstance(actions[n], mm.Sub) for n in SUBMENUS), "submenus show ▸"
    assert not mm.is_unavailable(actions["Paint"]) and mm.is_unavailable(actions["Inputs"])
    assert modal.poll_action(actions["Inputs"]) is False and actions["Make Live"] is None
    assert "Select Similar" in menu.options, "Maya option box"
    assert mm.RMB_MESH.items[0][0] == mm.OBJECT_TITLE, "the shared definition keeps the placeholder"
    assert [e[0] for e in mm.RMB_CURVE.items[:7] if e != mm.DIVIDER] == [mm.OBJECT_TITLE, "Select", "Select All",
                                                                         "Deselect All", "Select Hierarchy",
                                                                         "Invert Selection"]


def test_rmb_list_under_the_ring():
    """The list stays under the ring (Maya); rows that don't fit continue in more columns."""
    b = (0.0, 0.0, 1600.0, 900.0)
    for origin in ((800.0, 600.0), (800.0, 450.0), (300.0, 380.0), (1500.0, 420.0)):
        s = engine.Session(mm.RMB_MESH, origin, 0.0, measure, None, None, b)
        rows = [it for it in s.layout.items if it.kind == "list"]
        ring_bottom = min(it.rect[1] for it in s.layout.radial.values())
        assert all(it.rect[3] <= ring_bottom for it in rows), origin
        absr = [(it.rect[0] + origin[0], it.rect[1] + origin[1], it.rect[2] + origin[0], it.rect[3] + origin[1])
                for it in rows]
        assert all(b[0] - 1e-6 <= r[0] and r[2] <= b[2] + 1e-6 and r[1] >= b[1] - 1e-6 for r in absr), origin
        firsts = [it for it in rows if it.rect[3] == max(r.rect[3] for r in rows)]
        assert firsts[0].label == mm.OBJECT_TITLE, "the first column starts with the title"
    # room for everything: one column centred under the ring
    s = engine.Session(mm.RMB_MESH, (800.0, 880.0), 0.0, measure, None, None, (0.0, -2000.0, 1600.0, 900.0))
    rows = [it for it in s.layout.items if it.kind == "list"]
    assert len({it.rect[0] for it in rows}) == 1 and abs(rows[0].rect[0] + rows[0].rect[2]) < 1e-6


def test_window_bounds_and_cover_handlers():
    region = type("R", (), {"x": 300, "y": 100, "width": 800, "height": 600})()
    area = lambda x, y, w, h: type("A", (), {"x": x, "y": y, "width": w, "height": h})()  # noqa: E731
    screen = type("S", (), {"areas": [area(0, 30, 300, 840), area(300, 30, 1300, 840)]})()
    window = type("W", (), {"screen": screen})()
    assert draw.window_bounds(window, region) == (-300, -70, 1300, 770)
    spaces = {space for space, _r, _h in draw._handles}
    assert {bpy.types.SpaceView3D, bpy.types.SpaceOutliner, bpy.types.SpaceProperties} <= spaces
    assert {r for space, r, _h in draw._handles if space is bpy.types.SpaceView3D} >= {'WINDOW', 'UI', 'TOOLS',
                                                                                       'HEADER'}


def test_object_attributes_operator():
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.window_manager.allset_mm_target = ob.name
    try:
        assert bpy.ops.allset.object_attributes.poll()
    finally:
        bpy.context.window_manager.allset_mm_target = ""


def test_submenu_arrow_measured_without_the_glyph():
    """A UI font without "▸" (Segoe UI, Maya Font) made blf report millions of px: the RMB list spanned the
    view (step 41 shot). The arrow is a drawn triangle of fixed width."""
    w = draw.measure("Inputs")
    assert abs(draw.measure("Inputs" + draw.ARROW) - (w + draw._arrow_w())) < 1e-6
    assert draw.measure("Assign Existing Material" + draw.ARROW) < 400
