"""Step 52: hotbox and RMB marking menu as Maya 2022 shows them (,
14_marking_menu_object.png). ; GUI: tests/gui/gui_step52_hotbox_rmb.py."""

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

# Maya 2022 RMB list over pCube1 (14_marking_menu_object.png, Maya-2764), "-" = divider.
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
                    "Assign Existing Material"], tail                   # Maya-2764
    actions = {e[0]: e[1] for e in menu.items if e != mm.DIVIDER}
    # a Sub or a Blender menu (step 136: UV Sets / Color Sets list the mesh's sets) — both show ▸
    assert all(isinstance(actions[n], mm.Sub) or actions[n][0] == "menu" for n in SUBMENUS), "submenus show ▸"
    assert not mm.is_unavailable(actions["Paint"]) and mm.is_unavailable(actions["Metadata"])
    assert modal.poll_action(actions["Metadata"]) is False
    assert isinstance(actions["Inputs"], mm.NodeList) and modal.poll_action(actions["Inputs"])   # step 165
    assert actions["Make Live"] == ("allset.mm_object_item", {"item": "Modify/Make Live"})   # step 136
    assert "Select Similar" in menu.options, "Maya option box"
    assert mm.RMB_MESH.items[0][0] == mm.OBJECT_TITLE, "the shared definition keeps the placeholder"
    assert [e[0] for e in mm.RMB_CURVE.items[:7] if e != mm.DIVIDER] == [mm.OBJECT_TITLE, "Select", "Select All",
                                                                         "Deselect All", "Select Hierarchy",
                                                                         "Invert Selection"]


def test_rmb_list_under_the_ring():
    """Maya keeps the list in one column under the ring, always (): when it would
    run past the bottom the whole menu is drawn higher so the list ends ``list_gap`` above the window bottom; the
    pointer stays where it was pressed (step 184, replacing step 161's column beside the ring)."""
    b = (0.0, 0.0, 1600.0, 900.0)
    for origin in ((800.0, 600.0), (800.0, 450.0), (300.0, 380.0), (1500.0, 420.0), (800.0, 120.0)):
        s = engine.Session(mm.RMB_MESH, origin, 0.0, measure, None, None, b)
        rows = [it for it in s.layout.items if it.kind == "list"]
        assert len({round(it.rect[0], 3) for it in rows}) == 1, (origin, "one column")
        boxes = list(s.layout.radial.values())
        assert not any(r.rect[0] < x.rect[2] and x.rect[0] < r.rect[2] and r.rect[1] < x.rect[3] and
                       x.rect[1] < r.rect[3] for r in rows for x in boxes), (origin, "list over the ring")
        cx, cy = s.center
        absr = [(it.rect[0] + cx, it.rect[1] + cy, it.rect[2] + cx, it.rect[3] + cy) for it in rows]
        assert all(b[0] - 1e-6 <= r[0] and r[2] <= b[2] + 1e-6 and b[1] - 1e-6 <= r[1] and r[3] <= b[3] + 1e-6
                   for r in absr), origin
        top = max(rows, key=lambda it: it.rect[3])
        assert top.label == mm.OBJECT_TITLE, "the column starts with the title"
        ring_bottom = min(it.rect[1] for it in boxes)
        assert all(it.rect[3] <= ring_bottom for it in rows), (origin, "under the ring")
        assert s.press == origin and s.pos == origin and cx == origin[0], "the pointer is not moved"
        if origin[1] == 600.0:
            assert cy == origin[1], "room under the ring: the menu stays at the press point"
        if origin[1] in (450.0, 120.0):
            assert cy > origin[1], (origin, "no room: the whole menu is drawn higher")
            bottom = min(r[1] for r in absr)
            assert abs(bottom - (b[1] + s.params.list_gap)) < 1e-6, (origin, bottom)
            assert s.layout.lifted is not None
    # room for everything: one column centred under the ring
    s = engine.Session(mm.RMB_MESH, (800.0, 880.0), 0.0, measure, None, None, (0.0, -2000.0, 1600.0, 900.0))
    rows = [it for it in s.layout.items if it.kind == "list"]
    assert len({it.rect[0] for it in rows}) == 1 and abs(rows[0].rect[0] + rows[0].rect[2]) < 1e-6


def test_lifted_menu_picks_like_maya():
    """Maya, lifted menu (rmb_list_184.md B3 / B6 / B9): the highlight follows the pointer against the rows as drawn;
    under the ring no radial direction is picked (a release below the list without crossing the S box runs
    nothing); a quick click on the press point that lands on a row runs that row."""
    b = (0.0, 0.0, 1600.0, 900.0)
    s = engine.Session(mm.RMB_MESH, (800.0, 120.0), 0.0, measure, None, None, b)
    cx, cy = s.center
    rows = [it for it in s.layout.items if it.kind == "list" and it.enabled and it.sub is None]
    row = rows[len(rows) // 2]
    x, y = cx + (row.rect[0] + row.rect[2]) / 2, cy + (row.rect[1] + row.rect[3]) / 2
    s.move(x, y, 0.5)
    assert s.hover[0] is row, (s.hover, row.label)
    s.move(cx, 2.0, 0.6)                        # below the list, straight under the ring
    assert s.hover[0] is None, s.hover
    face = s.layout.radial["S"]
    s.move(cx, cy + (face.rect[1] + face.rect[3]) / 2, 0.7)    # on the drawn S box: Face
    assert s.hover[0] is face
    # a quick click (no drag) opens the menu in click mode even when a row lies under the press point
    s = engine.Session(mm.RMB_MESH, (800.0, 120.0), 0.0, measure, None, None, b)
    assert s.release(800.0, 120.0, 0.1) is None and s.mode == "CLICK"


def test_lifted_menu_marks_read_from_the_press():
    """Step 191: a mark (released before the menu is drawn) on a menu that would be drawn higher is read from the
    press point — the user never saw the lifted menu. After the show delay the drawn boxes count again."""
    b = (0.0, 0.0, 1600.0, 900.0)
    for key, (dx, dy) in (("N", (0.0, 70.0)), ("S", (0.0, -70.0)), ("W", (-70.0, 0.0))):
        s = engine.Session(mm.RMB_MESH, (800.0, 120.0), 0.0, measure, None, None, b)
        assert s.layout.lifted is not None and s.center[1] > 120.0
        s.move(800.0 + dx / 2, 120.0 + dy / 2, 0.03)
        res = s.release(800.0 + dx, 120.0 + dy, 0.06)
        assert res is not None and res[0] == "RUN" and res[1] is s.layout.radial[key], (key, res)
    # drawn (after the delay): straight up from the press is not the N box of the lifted ring
    s = engine.Session(mm.RMB_MESH, (800.0, 120.0), 0.0, measure, None, None, b)
    north = s.layout.radial["N"]
    s.move(800.0, 190.0, 0.5)
    assert s.hover[0] is not north, s.hover


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
