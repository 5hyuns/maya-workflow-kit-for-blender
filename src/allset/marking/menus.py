# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya marking menus as plain data (docs/steps/step_8.md 「계획」 1).

Positions and labels follow research/maya/marking_menus.json ``menus[<proc>]``
(Maya's shipped MEL; line numbers in the comments are that proc's file) and
research/maya/hotkeys_and_menus.md §5. Re-implemented: only labels, radial
positions and the Blender action (same value forms as ``ui/menu_map.py``:
``"op.id"``, ``("op.id", {props})``, ``("v3d", ...)``, ``("tool", id, edit)``,
``("menu", id)``; ``None`` = greyed out). A radial ``Sub`` is a nested marking
menu, a list ``Sub`` a plain submenu.

Kept free of Blender UI so the step-9 marking-menu engine can draw the same
definitions.
"""

RADIALS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
DIVIDER = "-"


class Sub:
    """A submenu: ``radial`` {pos: (label, action)}, ``items`` [(label, action) | "-"].

    ``options``: labels whose Maya item has an option box ``[]``
    (``option_box_command`` in research/maya/marking_menus.json).
    """

    def __init__(self, radial=None, items=(), options=()):
        self.radial = dict(radial or {})
        self.items = list(items)
        self.options = frozenset(options)


class MarkingMenu(Sub):
    def __init__(self, name, label, source, radial=None, items=(), options=()):
        super().__init__(radial, items, options)
        self.name = name        # id, also the research JSON proc for checks
        self.label = label
        self.source = source    # research citation


def _mod(kind):
    return ("object.modifier_add", {"type": kind})


def _create(kind):
    # Maya name and size in Maya units (operators/create.py, docs/steps/step_21.md).
    return ("allset.create", {"kind": kind})


def _orient(kind, slot=0):
    # Not transform.select_orientation: invoked from a menu it opens its own enum popup (GUI test).
    # W/E/R menus set their own tool's slot (1 move, 2 rotate, 3 scale): Maya keeps one axis mode
    # per tool, Move = World and Rotate/Scale = Object by default (pivot_snap.md P12, step 59).
    return ("wm.context_set_enum", {"data_path": f"scene.transform_orientation_slots[{slot}].type", "value": kind})


def _step(kind, mode='TOGGLE'):
    return ("allset.step_snap", {"kind": kind, "mode": mode})


def _comp(kind):
    return ("allset.mm_component", {"type": kind})


MULTI_CUT = ("tool", "allset.multi_cut_tool", True)     # step 129
MERGE_CENTER = ("mesh.merge", {"type": 'CENTER'})
TARGET_WELD = ("tool", "allset.target_weld_tool", True)   # step 64
CREASE = ("tool", "allset.crease_tool", True)
PRESERVE_UVS = ("wm.context_toggle", {"data_path": "scene.tool_settings.use_transform_correct_face_attributes"})
PRESERVE_CHILDREN = ("wm.context_toggle", {"data_path": "scene.tool_settings.use_transform_skip_children"})
TOOL_SETTINGS = ("allset.editor_toggle", {"editor": 'TOOL_SETTINGS'})
SMART_DUPLICATE = ("allset.manip_option", {"option": 'SMART_DUPLICATE'})  # step 22
SMART_EXTRUDE = ("allset.manip_option", {"option": 'SMART_EXTRUDE'})      # step 26


def _sym(mode):
    return ("allset.symmetry", {"mode": mode})


# commonReflectionOptionsPopup (marking_menus.json :35-77), called by the Move / Rotate / Scale
# option menus at N; every item is a check box (operators/symmetry.py, step 36).
SYMMETRY = ("Symmetry", Sub(radial={
    "N": ("Symmetry", _sym('ON')),
    "W": ("World", _sym('ABOUT_WORLD')),
    "E": ("Object", _sym('ABOUT_OBJECT')),
    "NE": ("Topology", _sym('TOPOLOGY')),
    "SW": ("X Axis", _sym('AXIS_X')),
    "S": ("Y Axis", _sym('AXIS_Y')),
    "SE": ("Z Axis", _sym('AXIS_Z')),
}))

# Material items at the end of the RMB object list (dagMenuProc.mel:2755-2764 -> buildShaderMenus,
# research/maya/hotkeys_and_menus.md:252; docs/steps/step_29.md). ``rmb``: with nothing selected
# they act on the object the menu was opened on, like Maya.
_FAVORITES = (("Lambert", 'LAMBERT'), ("Blinn", 'BLINN'), ("Phong", 'PHONG'),
              ("Standard Surface", 'STANDARD_SURFACE'))


def _material_items():
    """A fresh list per menu, so each menu gets its own submenu class."""
    favorites = [(label, ("allset.shelf_material", {"kind": kind, "rmb": True})) for label, kind in _FAVORITES]
    return [
        DIVIDER,
        ("Material Attributes...", ("allset.material_attributes", {"rmb": True})),
        DIVIDER,
        ("Assign New Material...", ("allset.assign_new_material", {"rmb": True})),
        ("Assign Favorite Material", Sub(items=favorites)),
        ("Assign Existing Material", ("menu", "ALLSET_MT_assign_existing_material_rmb")),
    ]


# --- RMB: dagMenuProc (hotkeys_and_menus.md §5.2, :246-252) --------------------------
# Mesh radials come from createSelectMenuItems' order (dagMenuProc.mel:885-892) and
# objectSelectMasks (:503-509); NE "Object Mode" (:1286-1289). [I] resolved by hand.

# The list under the ring, Maya 2022 order (dagMenuProc.mel:2582-2764 in research/maya/marking_menus.json
# menus.dagMenuProc; 14_marking_menu_object.png, docs/steps/step_52.md). The first row is the object's name
# (``OBJECT_TITLE`` is replaced by it when the menu opens). An empty ``Sub`` is a greyed submenu: Maya's
# dependency-graph / metadata / set editors have no Blender counterpart here.
OBJECT_TITLE = "<object>..."


def unavailable():
    """A greyed submenu (▸) whose Maya contents Blender doesn't have."""
    return Sub()


def is_unavailable(action):
    return isinstance(action, Sub) and not action.radial and not action.items


def _object_items():
    return [
        (OBJECT_TITLE, ("allset.object_attributes", {"rmb": True})),
        DIVIDER,
        ("Select", ("allset.mm_component", {"type": 'NONE'})),
        ("Select All", ("object.select_all", {"action": 'SELECT'})),
        ("Deselect All", ("object.select_all", {"action": 'DESELECT'})),
        ("Select Hierarchy", ("object.select_grouped", {"type": 'CHILDREN_RECURSIVE', "extend": True})),
        ("Invert Selection", ("object.select_all", {"action": 'INVERT'})),
        DIVIDER,
        ("Select Similar", ("object.select_grouped", {"type": 'TYPE', "extend": True})),
        DIVIDER,
        ("Make Live", None),
        DIVIDER,
        ("DG Traversal", unavailable()),
        ("Inputs", unavailable()),
        ("Outputs", unavailable()),
        ("Paint", Sub(items=[("Paint Skin Weights", ("paint.weight_paint_toggle", {}))])),
        ("Metadata", unavailable()),
        ("Actions", unavailable()),
        ("UV Sets", unavailable()),
        ("Color Sets", unavailable()),
        ("Time Editor", unavailable()),
        *_material_items(),
    ]


RMB_MESH = MarkingMenu(
    "dagMenuProc", "Object", "research/maya/hotkeys_and_menus.md:248-250",
    radial={
        "N": ("Edge", _comp('EDGE')),
        "W": ("Vertex", _comp('VERT')),
        "S": ("Face", _comp('FACE')),
        "E": ("UV", ("allset.uv_component", {"mode": 'UV'})),   # opens the UV Editor (step 66)
        "SW": ("Vertex Face", None),
        "SE": ("Multi", _comp('MULTI')),
        "NE": ("Object Mode", ("object.mode_set", {"mode": 'OBJECT'})),
    },
    items=_object_items(),
    options=("Select Similar",))

# Curve: N curve point, W CV, S edit point, E hull (dagMenuProc.mel:485-501). Blender
# curves edit control points only.
RMB_CURVE = MarkingMenu(
    "dagMenuProc_curve", "Curve", "research/maya/hotkeys_and_menus.md:251",
    radial={
        "N": ("Curve Point", None),
        "W": ("Control Vertex", _comp('CV')),
        "S": ("Edit Point", None),
        "E": ("Hull", None),
        "NE": ("Object Mode", ("object.mode_set", {"mode": 'OBJECT'})),
    },
    items=_object_items(),
    options=("Select Similar",))


def with_object_name(menu, name):
    """A copy of ``menu`` whose ``OBJECT_TITLE`` row shows ``name`` (Maya: "pCube1...")."""
    items = [(f"{name}...", e[1]) if e != DIVIDER and e[0] == OBJECT_TITLE else e for e in menu.items]
    if items == menu.items:
        return menu
    return MarkingMenu(menu.name, menu.label, menu.source, menu.radial, items, menu.options)


# Nothing under the cursor: Select All / Complete Tool (buildObjectMenuItemsNow.mel:126-150).
RMB_EMPTY = MarkingMenu(
    "buildObjectMenuItemsNow", "Select", "research/maya/hotkeys_and_menus.md:252",
    items=[("Select All", ("object.select_all", {"action": 'SELECT'})),
           ("Complete Tool", None)])

# Pivot edit (D / Insert): the $editMode branch of buildObjectMenuItemsNow (research/maya/marking_menus.json
# menus.buildObjectMenuItemsNow :69-115; interaction.md:81). Same proc as RMB_EMPTY, so a variant name like
# dagMenuProc_curve. Show Orientation Handle / Bake Pivot Orientation have no Blender counterpart (greyed).
def _pivot_option(option):
    return ("allset.pivot_option", {"option": option})


def _pivot_reset(position=True, orientation=True):
    return ("allset.pivot_reset", {"position": position, "orientation": orientation})


PIVOT_EDIT = MarkingMenu(
    "buildObjectMenuItemsNow_pivot", "Pivot", "research/maya/marking_menus.json buildObjectMenuItemsNow",
    radial={
        "N": ("Pin Component Pivot", _pivot_option("PIN")),                # :69
        "S": ("Reset Pivot", _pivot_reset()),                              # :75
        "NW": ("Snap Pivot Orientation", _pivot_option("SNAP_ORI")),       # :80
        "NE": ("Snap Pivot Position", _pivot_option("SNAP_POS")),          # :86
        "SW": ("Reset Pivot Orientation", _pivot_reset(position=False)),   # :92
        "SE": ("Reset Pivot Position", _pivot_reset(orientation=False)),   # :97
        "W": ("Show Orientation Handle", None),                            # :102
        "E": ("Exit", ("allset.pivot_exit", {})),                        # :108
    },
    items=[("Bake Pivot Orientation", None)])                              # :115

# --- Shift+RMB: contextPolyTools*MM (§5.3, :254-265) ---------------------------------

SOFT_HARD = Sub(radial={  # contextPolyToolsObjectMM.mel:127-169 / EdgeMM.mel:67-109
    "S": ("Toggle Soft Edge Display", None),
    "SE": ("Harden Edge", "mesh.mark_sharp"),
    "E": ("Soften/Harden", None),
    "NE": ("Soften Edge", ("mesh.mark_sharp", {"clear": True})),
}, options={"Soften/Harden"})

SHIFT_OBJECT = MarkingMenu(
    "contextPolyToolsObjectMM", "Object Tools", "research/maya/marking_menus.json contextPolyToolsObjectMM",
    radial={
        "S": ("Extrude", None),                                            # :26
        "SW": ("Insert Edge Loop Tool", ("tool", "builtin.loop_cut", True)),  # :34
        "E": ("Append to Polygon Tool", None),                             # :50
        "NE": ("Fill Holes", None),                                        # :66
        "N": ("Target Weld Tool", TARGET_WELD),                            # :74
        "W": ("Multi-Cut", MULTI_CUT),                                     # :89
        "NW": ("Sculpt Tool", ("object.mode_set", {"mode": 'SCULPT'})),    # :111
        "SE": ("Soften/Harden Edges", Sub(radial={                         # :127 (object level)
            "S": ("Toggle Soft Edge Display", None),
            "SE": ("Harden Edge", "object.shade_flat"),
            "E": ("Soften/Harden", "object.shade_auto_smooth"),
            "NE": ("Soften Edge", "object.shade_smooth"),
        }, options={"Soften/Harden"})),
    },
    items=[
        ("Smooth", _mod('SUBSURF')),                                       # :207
        ("Subdiv Proxy", _mod('SUBSURF')),                                 # :221
        ("Crease Tool", CREASE),
        DIVIDER,
        ("Mirror", "allset.mirror"),                                        # :280
        DIVIDER,
        ("Triangulate", _mod('TRIANGULATE')),                              # :303
        ("Quadrangulate", None),
        ("Reduce", _mod('DECIMATE')),                                      # :324
        DIVIDER,
        ("Separate", "allset.separate"),                # :380
        ("Combine", "allset.combine"),                                        # :387
        ("Booleans", Sub(items=[("Union", None), ("Difference", None), ("Intersection", None)],
                         options={"Union", "Difference", "Intersection"})),
        DIVIDER,
        ("Quad Draw Tool", ("tool", "builtin.poly_build", True)),          # :480
    ],
    options=['Append to Polygon Tool', 'Combine', 'Crease Tool', 'Insert Edge Loop Tool', 'Mirror', 'Multi-Cut', 'Quad Draw Tool', 'Quadrangulate', 'Reduce', 'Sculpt Tool', 'Smooth', 'Subdiv Proxy', 'Target Weld Tool'])

SHIFT_VERTEX = MarkingMenu(
    "contextPolyToolsVertexMM", "Vertex Tools", "research/maya/marking_menus.json contextPolyToolsVertexMM",
    radial={
        "S": ("Extrude Vertex", ("v3d", "mesh.extrude_vertices_move", {})),   # :27
        "E": ("Chamfer Vertex", ("v3d", "mesh.bevel", {"affect": 'VERTICES'})),  # :43
        "SW": ("Delete Vertex", "mesh.dissolve_verts"),                    # :59
        "SE": ("Vertex Normals", Sub(radial={                              # :68
            "S": ("Toggle Vertex Normal Display", None),
            "NE": ("Average Normals", "mesh.average_normals"),
            "E": ("Vertex Normal Edit Tool", None),
            "SE": ("Set Normals to Face", "mesh.set_normals_from_faces"),
        }, options={"Average Normals", "Set Normals to Face"})),
        "N": ("Merge Vertices", Sub(radial={                               # :127
            "NE": ("Merge Vertices", "mesh.remove_doubles"),
            "N": ("Merge Vertices To Center", MERGE_CENTER),
            "S": ("Target Weld Tool", TARGET_WELD),
        }, options={"Merge Vertices", "Target Weld Tool"})),
        "NE": ("Average Vertices", "mesh.vertices_smooth"),                # :176
        "W": ("Multi-Cut", MULTI_CUT),                                     # :184
        "NW": ("Paint Select Vertices", None),                             # :202
    },
    items=[
        ("Crease Tool", CREASE),
        ("Connect Components", "mesh.vert_connect_path"),                  # :225
        ("Detach Components", None),
        ("Connect Tool", MULTI_CUT),
        DIVIDER,
        ("Circularize Vertices", None),
        ("Reorder Vertices", None),
    ],
    options=['Chamfer Vertex', 'Circularize Vertices', 'Connect Components', 'Connect Tool', 'Crease Tool', 'Extrude Vertex', 'Multi-Cut'])

SHIFT_EDGE = MarkingMenu(
    "contextPolyToolsEdgeMM", "Edge Tools", "research/maya/marking_menus.json contextPolyToolsEdgeMM",
    radial={
        "S": ("Extrude Edge", ("v3d", "mesh.extrude_edges_move", {})),       # :27
        "SW": ("Delete Edge", "mesh.dissolve_edges"),                      # :43
        "E": ("Bevel Edge", ("v3d", "mesh.bevel", {})),                    # :51
        "SE": ("Soften/Harden Edges", SOFT_HARD),                          # :67
        "N": ("Merge/Collapse Edges", Sub(radial={                         # :119
            "NE": ("Merge Border Edges", "mesh.remove_doubles"),
            "S": ("Target Weld Tool", TARGET_WELD),
            "NW": ("Merge Edge Tool", None),
            "E": ("Collapse Edge", "mesh.edge_collapse"),
            "N": ("Merge Edges To Center", MERGE_CENTER),
        }, options={"Merge Border Edges", "Target Weld Tool", "Merge Edge Tool"})),
        "NE": ("Flip/Spin Edge", Sub(radial={                              # :199
            "N": ("Flip Triangle Edge", "mesh.edge_rotate"),
            "E": ("Spin Forward", ("mesh.edge_rotate", {"use_ccw": False})),
            "W": ("Spin Backward", ("mesh.edge_rotate", {"use_ccw": True})),
        })),
        "W": ("Multi-Cut", MULTI_CUT),                                     # :232
        "NW": ("Paint Select Edges", None),                                # :251
    },
    items=[
        ("Crease Tool", CREASE),
        ("Insert Edge Loop Tool", ("tool", "builtin.loop_cut", True)),     # :302
        ("Slide Edge Tool", ("tool", "builtin.edge_slide", True)),         # :316
        ("Circularize Components", None),
        ("Edit Edge Flow", None),
        DIVIDER,
        ("Add Divisions To Edge", "mesh.subdivide"),                       # :366
        ("Bridge", "mesh.bridge_edge_loops"),                              # :379
        ("Fill Hole", "mesh.fill_holes"),                                  # :392
        DIVIDER,
        ("Connect Components", "mesh.subdivide_edgering"),                 # :403
        ("Detach Components", "mesh.edge_split"),                          # :419
    ],
    options=['Add Divisions To Edge', 'Bevel Edge', 'Bridge', 'Circularize Components', 'Connect Components', 'Crease Tool', 'Edit Edge Flow', 'Extrude Edge', 'Insert Edge Loop Tool', 'Multi-Cut', 'Slide Edge Tool'])

SHIFT_FACE = MarkingMenu(
    "contextPolyToolsFaceMM", "Face Tools", "research/maya/marking_menus.json contextPolyToolsFaceMM",
    radial={
        "N": ("Merge Faces To Center", MERGE_CENTER),                      # :27
        "S": ("Extrude Face", ("v3d", "allset.extrude", {})),            # :35 (step 65)
        "SW": ("Wedge Face", None),                                        # :51
        "NE": ("Poke Face", "mesh.poke"),                                  # :68
        "E": ("Bevel Face", ("v3d", "mesh.bevel", {})),                    # :84
        "SE": ("Face Normals", Sub(radial={                                # :100
            "S": ("Toggle Face Normal Display", None),
            "NE": ("Reverse Propagate", None),
            "SE": ("Conform Normals", "mesh.normals_make_consistent"),
            "E": ("Reverse Normals", "mesh.flip_normals"),
        }, options={"Reverse Normals"})),
        "W": ("Multi-Cut", MULTI_CUT),                                     # :150
        "NW": ("Paint Select Faces", None),                                # :168
    },
    items=[
        ("Smooth Faces", ("mesh.subdivide", {"smoothness": 1.0})),         # :181
        ("Assign Invisible Faces", None),
        ("Add Divisions To Faces", "mesh.subdivide"),                      # :210
        ("Circularize Components", None),
        ("Triangulate Faces", "mesh.quads_convert_to_tris"),               # :263
        ("Quadrangulate Faces", "mesh.tris_convert_to_quads"),             # :270
        DIVIDER,
        ("Bridge Faces", "mesh.bridge_edge_loops"),                        # :309
        DIVIDER,
        ("Extract Faces", ("mesh.separate", {"type": 'SELECTED'})),        # :339
        ("Duplicate Face", ("v3d", "mesh.duplicate_move", {})),            # :353
        ("Target Weld Tool", TARGET_WELD),                                 # :396 (step 64)
    ],
    options=['Add Divisions To Faces', 'Assign Invisible Faces', 'Bevel Face', 'Bridge Faces', 'Circularize Components', 'Duplicate Face', 'Extract Faces', 'Extrude Face', 'Multi-Cut', 'Poke Face', 'Smooth Faces', 'Target Weld Tool', 'Wedge Face'])

SHIFT_DEFAULT = MarkingMenu(
    "contextPolyToolsDefaultMM", "Create", "research/maya/marking_menus.json contextPolyToolsDefaultMM",
    radial={
        "N": ("Create Polygon Tool", None),                                # :56
        "NE": ("Disc", _create('DISC')),  # :72
        "E": ("Sphere", _create('SPHERE')),                   # :89
        "SE": ("Torus", _create('TORUS')),                       # :105
        "S": ("Cube", _create('CUBE')),                          # :121
        "SW": ("Cone", _create('CONE')),                         # :137
        "W": ("Cylinder", _create('CYLINDER')),                  # :153
        "NW": ("Plane", _create('PLANE')),                       # :169
    },
    items=[
        ("Platonic Solid", _create('PLATONIC')),  # :185
        ("Pyramid", _create('PYRAMID')),         # :198
        ("Prism", _create('PRISM')),       # :212
        ("Pipe", None), ("Helix", None), ("Gear", None),
        DIVIDER,
        ("Type", _create('TEXT')),                                       # :308
        ("Quad Draw Tool", None),
    ],
    options=['Cone', 'Create Polygon Tool', 'Cube', 'Cylinder', 'Disc', 'Gear', 'Helix', 'Pipe', 'Plane', 'Platonic Solid', 'Prism', 'Pyramid', 'Quad Draw Tool', 'Sphere', 'Torus'])

# --- Ctrl+RMB: polyConvertMM (§5.4, :267-269) -------------------------------------------

CTRL_CONVERT = MarkingMenu(
    "polyConvertMM", "Convert Selection", "research/maya/marking_menus.json polyConvertMM",
    radial={
        "N": ("To Edges", Sub(radial={                                     # :43
            "N": ("To Edges", ("mesh.select_mode", {"type": 'EDGE', "use_expand": True})),
            "S": ("To Contained Edges", ("mesh.select_mode", {"type": 'EDGE'})),
            "NW": ("To Contiguous Edges", ("allset.select_loops", {"ring": False})),
            "NE": ("To Edge Perimeter", "mesh.region_to_loop"),
        }, options={"To Contiguous Edges"})),
        "NW": ("Shrink Selection", Sub(radial={                            # :88
            "NW": ("Shrink", "mesh.select_less"),
            "N": ("Shrink Selection Along Loop", None),
        })),
        "E": ("To UVs", Sub(radial={"E": ("To UVs", None), "NE": ("To UV Perimeter", None)})),  # :109
        "SE": ("Edge Loop Utilities", Sub(radial={                         # :134
            "SE": ("To Edge Loop", ("allset.select_loops", {"ring": False})),
            "NE": ("To Edge Loop and Delete", None),
            "SW": ("To Edge Loop and Duplicate", None),
        })),
        "SW": ("Edge Ring Utilities", Sub(radial={                         # :165
            "SW": ("To Edge Ring", ("allset.select_loops", {"ring": True})),
            "SE": ("To Edge Ring and Split", None),
            "NW": ("To Edge Ring and Collapse", None),
        })),
        "S": ("To Faces", Sub(radial={                                     # :198
            "S": ("To Faces", ("mesh.select_mode", {"type": 'FACE', "use_expand": True})),
            "N": ("To Contained Faces", ("mesh.select_mode", {"type": 'FACE'})),
            "SE": ("To Face Perimeter", "mesh.region_to_loop"),
        })),
        "W": ("To Vertices", Sub(radial={                                  # :229
            "W": ("To Vertices", ("mesh.select_mode", {"type": 'VERT'})),
            "NW": ("To Vertex Perimeter", None),
        })),
        "NE": ("Grow Selection", Sub(radial={                              # :254
            "NE": ("Grow", "mesh.select_more"),
            "N": ("Grow Along Loop", None),
        })),
    },
    items=[
        ("To Face Path", None),                                            # :276
        ("To UV Shell", None),
        ("To Shell", "mesh.select_linked"),                                # :288
        ("To Shell Border", None),
        DIVIDER,
        ("Selection Boundary", "mesh.region_to_loop"),                     # :310
    ])

# --- Tool options: q/w/e/r hold + LMB, Ctrl+Shift+RMB (§5.5, :271-276) -------------------
# Maya manip modes -> Blender transform orientations (Object = Local, Component = Normal).

OPT_MOVE = MarkingMenu(
    "translateMarkingMenuImpl", "Move Options", "research/maya/marking_menus.json translateMarkingMenuImpl",
    radial={
        "NE": ("Component", _orient('NORMAL', 1)),                         # :19
        "W": ("World", _orient('GLOBAL', 1)),                              # :27
        "NW": ("Object", _orient('LOCAL', 1)),                             # :35
        "SE": ("Keep Spacing", None),                                      # :43
        "N": SYMMETRY,                                                     # :104
        "E": ("Snap", Sub(radial={                                         # :116
            "E": ("Discrete Move", _step('TRANSLATE')),
            "SE": ("Vertex", ("allset.snap_toggle", {"snap": 'POINT'})),
            "SW": ("Face Center", None),
        })),
        "SW": ("Axis", Sub(radial={                                        # :152
            "NW": ("Normal", _orient('NORMAL', 1)),
            "W": ("Parent", _orient('PARENT', 1)),
            "NE": ("Along Rotation Axis", _orient('GIMBAL', 1)),
            "N": ("Live Object Axis", None),
            "SW": ("Custom", None),
        })),
    },
    items=[
        ("Smart Extrude", SMART_EXTRUDE), ("Smart Duplicate", SMART_DUPLICATE),
        DIVIDER,
        ("Preserve UVs", PRESERVE_UVS),                                    # :71
        ("Preserve Children", PRESERVE_CHILDREN),                          # :77
        DIVIDER,
        ("Move Options", TOOL_SETTINGS),                                   # :96
    ])

OPT_ROTATE = MarkingMenu(
    "rotateMarkingMenuImpl", "Rotate Options", "research/maya/marking_menus.json rotateMarkingMenuImpl",
    radial={
        "NW": ("Object", _orient('LOCAL', 2)),                             # :19
        "W": ("World", _orient('GLOBAL', 2)),                              # :24
        "SW": ("Custom", Sub(radial={"E": ("Custom", None), "NW": ("Reset", None)})),  # :29
        "SE": ("Discrete Rotate", _step('ROTATE')),                        # :66 (15 degrees, S3)
        "NE": ("Component", _orient('NORMAL', 2)),                         # :71
        "E": ("Gimbal", _orient('GIMBAL', 2)),                             # :77
        "N": SYMMETRY,                                                     # :86
    },
    items=[
        ("Smart Extrude", SMART_EXTRUDE), ("Smart Duplicate", SMART_DUPLICATE),
        DIVIDER,
        ("Preserve UVs", PRESERVE_UVS),                                    # :124
        ("Preserve Children", PRESERVE_CHILDREN),                          # :130
        DIVIDER,
        ("Rotate Options", TOOL_SETTINGS),                                 # :148
    ])

OPT_SCALE = MarkingMenu(
    "scaleMarkingMenuImpl", "Scale Options", "research/maya/marking_menus.json scaleMarkingMenuImpl",
    radial={
        "W": ("World", _orient('GLOBAL', 3)),                              # :18
        "NW": ("Object", _orient('LOCAL', 3)),                             # :24
        "NE": ("Component", _orient('NORMAL', 3)),                         # :30
        "SW": ("Axis", Sub(radial={                                        # :36
            "W": ("Parent", _orient('PARENT', 3)),
            "NW": ("Normal", _orient('NORMAL', 3)),
            "N": ("Live Object Axis", None),
            "NE": ("Along Rotation Axis", _orient('GIMBAL', 3)),
        })),
        "E": ("Snap Scale", _step('RESIZE')),                              # :101
        "SE": ("Relative", _step('RESIZE', 'RELATIVE')),                   # :107
        "N": SYMMETRY,                                                     # :117
    },
    items=[
        ("Smart Extrude", SMART_EXTRUDE), ("Smart Duplicate", SMART_DUPLICATE),
        DIVIDER,
        ("Preserve UVs", PRESERVE_UVS),                                    # :156
        ("Preserve Children", PRESERVE_CHILDREN),                          # :162
        DIVIDER,
        ("Scale Options", TOOL_SETTINGS),                                  # :175
    ])

OPT_SELECT = MarkingMenu(
    "selectMarkingMenuImpl", "Select Options", "research/maya/marking_menus.json selectMarkingMenuImpl",
    radial={
        "NW": ("Marquee", ("tool", "builtin.select_box", False)),         # :31
        "NE": ("Drag", ("tool", "builtin.select", False)),                # :36
        "E": ("Camera-Based Selection", None),                             # :41
        "SE": ("Clear Selection", "allset.mm_clear_selection"),          # :46
        "W": ("Paint Select", ("tool", "builtin.select_circle", False)),   # :50
        "SW": ("Lasso", ("tool", "builtin.select_lasso", False)),          # :54
    })

# --- A hold + LMB: buildSelectAllMM (interaction.md:194; marking_menus.json) -------------
# Inputs/outputs = history in Maya; the Blender history equivalent (modifiers) has no
# up/downstream selection, so W/E/N/S stay greyed (docs/steps/step_10.md 「계획」 9).

SELECT_ALL = MarkingMenu(
    "buildSelectAllMM", "Select All / History", "research/maya/marking_menus.json buildSelectAllMM",
    radial={
        "W": ("Select All Inputs", None),                                  # :40
        "E": ("Select All Outputs", None),                                 # :42
        "N": ("Enable All Outputs", None),                                 # :45
        "S": ("Disable All Outputs", None),                                # :47
        "NW": ("Delete History", "allset.delete_history"),               # :50
        "NE": ("Delete Non-Deformer History", ("allset.delete_history", {"non_deformer": True})),  # :52
        "SE": ("Freeze Transforms", "allset.freeze_transform"),          # :55, option box :58
    },
    options={"Freeze Transforms"})

# --- Shift+S hold + LMB: buildKeyframeTangentMM (marking_menus.json :284-571, hotkeySetup.mel:418) ------------
# Maya builds the same layout inside and outside the Graph Editor (:284-430 / :449-571); the actions pick the
# Graph Editor's selected keys or the current-time keys themselves (operators/graph_keys.py, step 70).

def _tan(kind):
    return ("allset.set_tangent", {"kind": kind})


def _key(action):
    return ("allset.key_edit", {"action": action})


KEY_TANGENT = MarkingMenu(
    "buildKeyframeTangentMM", "Keyframe / Tangents", "research/maya/marking_menus.json buildKeyframeTangentMM",
    radial={
        "W": ("Keys", Sub(radial={                                         # :284
            "N": ("Delete Keys", _key("DELETE")),                          # :291
            "NE": ("Convert to Key", _key("TO_KEY")),                      # :304
            "E": ("Paste Keys", _key("PASTE")),                            # :311
            "NW": ("Convert to Breakdown", _key("TO_BREAKDOWN")),          # :324
            "S": ("Copy Keys", _key("COPY")),                              # :331
            "SW": ("Remove Inbetween", _key("REMOVE_INBETWEEN")),          # :344
            "W": ("Cut Keys", _key("CUT")),                                # :351
            "SE": ("Add Inbetween", _key("ADD_INBETWEEN")),                # :364
        })),
        "E": ("Tangents", Sub(radial={                                     # :373
            "N": ("Spline", _tan("SPLINE")),                               # :381
            "E": ("Flat", _tan("FLAT")),                                   # :388
            "S": ("Linear", _tan("LINEAR")),                               # :395
            "W": ("Clamped", _tan("CLAMPED")),                             # :402
            "NW": ("Stepped", _tan("STEPPED")),                            # :409
            "SW": ("Stepped Next", _tan("STEPPED_NEXT")),                  # :416
            "SE": ("Plateau", _tan("PLATEAU")),                            # :423
            "NE": ("Fixed", _tan("FIXED")),                                # :430
        })),
    })

# --- Shift+Q / Alt+Q hold + LMB (hotkeySetup.mel:286-287; docs/steps/step_78.md) ---------------------------------
# doSelectComponentMM (buildSelectComponentMM.mel, popup :206 -sh) = the component pick mask; Blender's mask is the
# mesh select mode, so only Poly Vertices / Poly Edges / Faces / All Components on / Select Objects do something.
# doSelectPolygonMM (buildPolyMM.mel, popup :49 -alt) = F9 / F10 / F11 / F12.

def _mask(kind):
    return ("allset.component_mask", {"kind": kind})


SELECT_COMPONENT = MarkingMenu(
    "doSelectComponentMM", "Component Pick Mask", "research/maya/marking_menus.json doSelectComponentMM",
    radial={
        "N": ("Points", Sub(radial={                                       # :31
            "N": ("All Points", None),                                     # :32
            "E": ("CVs", None),                                            # :35
            "SE": ("Poly Vertices", _mask("VERT")),                        # :38
            "S": ("Lattice Points", None),                                 # :41
            "W": ("Particles", None),                                      # :44
            "SW": ("Subdiv Mesh Points", None),                            # :47
        })),
        "NE": ("Parm Points", Sub(radial={                                 # :55
            "NE": ("All Parm Points", None),                               # :56
            "E": ("Edit Points", None),                                    # :61
            "S": ("Curve Points", None),                                   # :64
            "W": ("Surface Points", None),                                 # :67
            "SW": ("Subdiv Mesh UVs", None),                               # :70
        })),
        "E": ("Lines", Sub(radial={                                        # :79
            "E": ("All Lines", None),                                      # :80
            "S": ("Poly Edges", _mask("EDGE")),                            # :85
            "W": ("Isoparms", None),                                       # :88
            "N": ("Trim Edges", None),                                     # :91
            "SE": ("Springs", None),                                       # :94
        })),
        "SE": ("Faces", _mask("FACE")),                                    # :103
        "S": ("Hulls", None),                                              # :111
        "SW": ("Pivots", Sub(radial={                                      # :119
            "SW": ("All Pivots", None),                                    # :120
            "NW": ("Rotate Pivots", None),                                 # :125
            "NE": ("Scale Pivots", None),                                  # :128
            "SE": ("Joint Pivots", None),                                  # :131
        })),
        "W": ("Handles", None),                                            # :140
        "NW": ("Misc.", Sub(radial={                                       # :147
            "NW": ("All Misc", None),
            "E": ("Local Rotation Axes", None),
            "S": ("Image Planes", None),
        })),
    },
    items=[("All Components on", _mask("ALL")), ("All Components off", None), DIVIDER,
           ("Save to shelf", None), DIVIDER, ("Select Objects", ("object.mode_set", {"mode": 'OBJECT'}))])


def _component(kind):
    return ("allset.component_mode", {"type": kind})


SELECT_POLYGON = MarkingMenu(
    "doSelectPolygonMM", "Polygon Components", "research/maya/marking_menus.json doSelectPolygonMM",
    radial={
        "N": ("Vertices", _component("VERT")),
        "E": ("Edges", _component("EDGE")),
        "S": ("Faces", _component("FACE")),
        "W": ("UVs", ("allset.uv_component", {"mode": 'UV'})),
    })

# --- Hotbox zones (hotkeys_and_menus.md §4 :207-214; marking_menus.json hotbox.zones) ------

def _pane(ui_type):
    return ("allset.hb_pane", {"ui_type": ui_type})


def _ui(element):
    return ("allset.hb_ui", {"element": element})


def _mask(preset):
    return ("allset.hb_mask", {"preset": preset})


def _view(view):
    return ("allset.hb_view", {"view": view})


SHADING_WS = ("allset.hb_workspace", {"name": "Shading"})
ANIMATION_WS = ("allset.hb_workspace", {"name": "Animation"})

HB_NORTH = MarkingMenu(
    "HotboxNorthMenu", "Panel Layouts", "research/maya/marking_menus.json hotbox.zones.N",
    radial={
        "N": ("Single Perspective", ("allset.hb_single", {})),          # HotboxNorthMenu.mel:36
        "NE": ("Hypershade/Render/Persp", SHADING_WS),                     # :39
        "SE": ("Hypershade/Outliner/Persp", SHADING_WS),                   # :42
        "E": ("Hypershade/Persp", SHADING_WS),                             # :45
        "S": ("Toggle Outliner", None),                                    # :47
        "SW": ("Persp/Graph/Outliner", ANIMATION_WS),                      # :49
        "W": ("Persp/Graph", ANIMATION_WS),                                # :52
        "NW": ("Persp/Relationship Editor", None),                         # :55
    })

HB_SOUTH = MarkingMenu(
    "HotboxSouthMenu", "Panel Types", "research/maya/marking_menus.json hotbox.zones.S",
    radial={
        "N": ("Outliner", _pane('OUTLINER')),                              # HotboxSouthMenu.mel:134
        "E": ("Graph Editor", _pane('FCURVES')),                           # :137
        "SE": ("Dope Sheet", _pane('DOPESHEET')),                          # :140
        "S": ("Hypergraph", None),                                         # :143
        "SW": ("Node Editor", _pane('ShaderNodeTree')),                    # :146
        "W": ("Hypershade", _pane('ShaderNodeTree')),                      # :149
        "NW": ("Render View", _pane('IMAGE_EDITOR')),                      # :152
        "NE": ("Set Editor", None),                                        # :155
    })

HB_EAST = MarkingMenu(
    "HotboxEastMenu", "UI Elements", "research/maya/marking_menus.json hotbox.zones.E",
    radial={
        "N": ("Help Line", _ui('HELP_LINE')),                              # HotboxEastMenu.mel:40
        "NE": ("Status Line", _ui('STATUS_LINE')),                         # :44
        "E": ("Attributes", Sub(radial={                                   # :48
            "E": ("Channel Box", _ui('CHANNEL_BOX')),
            "S": ("Layer Editor", _ui('CHANNEL_BOX')),
            "W": ("Attribute Editor", _ui('ATTRIBUTE')),
            "N": ("Tool Settings", _ui('TOOL_SETTINGS')),
        })),
        "SE": ("Tool Box", _ui('TOOLBOX')),
        "S": ("Time Slider", None),
        "SW": ("Range Slider", None),
        "W": ("Shelf", None),
        "NW": ("Command Line", _ui('COMMAND_LINE')),
    })

HB_WEST = MarkingMenu(
    "HotboxWestMenu", "Selection Masks", "research/maya/marking_menus.json hotbox.zones.W",
    radial={
        "N": ("NURBS Mask", _mask('NURBS')),
        "NE": ("Hierarchy", None),
        "E": ("Animation Mask", _mask('ANIMATION')),
        "SE": ("Deformations Mask", _mask('DEFORMATIONS')),
        "S": ("Dynamics Mask", None),
        "SW": ("Polygons Mask", _mask('POLYGONS')),
        "W": ("Rendering Mask", _mask('RENDERING')),
        "NW": ("Object/Components", "object.editmode_toggle"),
    },
    items=[("All Objects", _mask('ALL'))])

HB_CENTER = MarkingMenu(
    "HotboxCenterMenu", "Views", "research/maya/marking_menus.json hotbox.zones.C",
    radial={
        "N": ("Perspective View", _view('PERSP')),                         # HotboxCenterMenu.mel:143
        "E": ("Side View", _view('RIGHT')),                                # :146
        "S": ("Front View", _view('FRONT')),                               # :149
        "W": ("Top View", _view('TOP')),                                   # :152
        "NW": ("Left View", _view('LEFT')),                                # :155
        "SW": ("Back View", _view('BACK')),                                # :159
        "SE": ("Bottom View", _view('BOTTOM')),                            # :163
    },
    items=[("Hotbox Style", Sub(items=[                                    # :168
        ("Zones and Menu Rows", ("allset.hb_style", {"style": 'ALL'})),
        ("Zones Only", ("allset.hb_style", {"style": 'ZONES'})),
        ("Center Zone Only", ("allset.hb_style", {"style": 'CENTER'})),
    ]))])

HOTBOX_ZONES = {"N": HB_NORTH, "S": HB_SOUTH, "E": HB_EAST, "W": HB_WEST, "C": HB_CENTER}

# --- UV Editor (docs/steps/step_66.md 「계획」 2) ---------------------------------------------------

def _uvc(mode):
    return ("allset.uv_component", {"mode": mode})


UV_OPS = [("Cut UV Edges", "allset.uv_cut"), ("Sew UV Edges", "allset.uv_sew"),
          ("Unfold", "allset.uv_unfold"), ("Layout", "allset.uv_layout")]

# RMB in the UV Editor: texturePanelMenus.mel textureWindowCreatePopupRadialMenu (polygon version, :53-77, directions
# :34-42; research/maya/marking_menus.json, recorded in step 66). Maya puts a copy of the UV Editor menu bar under it:
# the kit lists the commands of this step instead.
UV_EDITOR_RMB = MarkingMenu(
    "textureWindowCreatePopupRadialMenu", "UV Editor", "research/maya/marking_menus.json textureWindowCreatePopupRadialMenu",
    radial={
        "S": ("Face", _uvc('FACE')),                                       # :53
        "N": ("Edge", _uvc('EDGE')),                                       # :58
        "E": ("UV", _uvc('UV')),                                           # :63
        "W": ("Vertex", _uvc('VERTEX')),                                   # :68
        "NW": ("UV Shell", _uvc('SHELL')),                                 # :73
    },
    items=[*UV_OPS, DIVIDER, ("Select All", ("uv.select_all", {"action": 'SELECT'})),
           ("Pin", "uv.pin"), ("Unpin", ("uv.pin", {"clear": True}))])

# Shift+RMB in the UV Editor: Maya's UV / UV Shell tool menus (contextPolyToolsUVMM.mel / contextPolyToolsUVShellMM.mel),
# Mapping = contextPolyToolsUVMappingMM.
UV_MAPPING = Sub(radial={
    "N": ("Planar", "allset.uv_planar"),
    "NE": ("Normal-Based", "allset.uv_planar"),
    "E": ("Camera-Based", ("v3d", "uv.project_from_view", {})),
    "SE": ("Cylindrical", ("v3d", "uv.cylinder_project", {})),
    "S": ("Best Plane", None),
    "SW": ("Spherical", ("v3d", "uv.sphere_project", {})),
    "W": ("Contour Stretch", None),
    "NW": ("Automatic", "uv.smart_project"),
})
_UV_TAIL = [("Texture Borders", None), DIVIDER, ("UV Editor", ("allset.uv_component", {"mode": 'OPEN'})),
            ("UV Set Editor", None)]

SHIFT_UV = MarkingMenu(
    "contextPolyToolsUVMM", "UV Tools", "research/maya/marking_menus.json contextPolyToolsUVMM",
    radial={
        "N": ("Mapping", UV_MAPPING),                                      # :25
        "NE": ("3D Grab UV Tool", None),                                   # :38
        "E": ("Sew UVs", "allset.uv_sew"),                               # :54
        "SE": ("Create UV Shell", None),                                   # :64
        "S": ("Merge UVs", "uv.weld"),                                     # :74
        "SW": ("Delete UVs", None),                                        # :89
        "W": ("Cut UVs", "allset.uv_cut"),                               # :99
        "NW": ("3D Cut and Sew UV Tool", "allset.cut_sew_tool_set"),     # :108 (step 79)
    },
    items=[("Auto Seams", None), *_UV_TAIL])

SHIFT_UV_SHELL = MarkingMenu(
    "contextPolyToolsUVShellMM", "UV Shell Tools", "research/maya/marking_menus.json contextPolyToolsUVShellMM",
    radial={
        "N": ("Mapping", UV_MAPPING),                                      # :25
        "NE": ("3D Grab UV Tool", None),                                   # :38
        "E": ("Optimize", "uv.minimize_stretch"),                          # :54
        "SE": ("Flip", ("transform.mirror", {"constraint_axis": (True, False, False)})),   # :69 (Flip U)
        "S": ("Auto Seams", None),                                         # :81
        "SW": ("Layout", "allset.uv_layout"),                            # :97
        "W": ("Unfold", "allset.uv_unfold"),                             # :112
        "NW": ("3D Cut and Sew UV Tool", "allset.cut_sew_tool_set"),     # :126 (step 79)
    },
    items=list(_UV_TAIL))

MENUS = {m.name: m for m in (RMB_MESH, RMB_CURVE, RMB_EMPTY, PIVOT_EDIT, SHIFT_OBJECT, SHIFT_VERTEX,
                             SHIFT_EDGE, SHIFT_FACE, SHIFT_DEFAULT, CTRL_CONVERT,
                             OPT_MOVE, OPT_ROTATE, OPT_SCALE, OPT_SELECT, SELECT_ALL,
                             HB_NORTH, HB_SOUTH, HB_EAST, HB_WEST, HB_CENTER,
                             UV_EDITOR_RMB, SHIFT_UV, SHIFT_UV_SHELL, KEY_TANGENT,
                             SELECT_COMPONENT, SELECT_POLYGON)}

# Active tool -> its options marking menu (buildToolOptionsMM.mel:29-49).
TOOL_OPTIONS = {"builtin.move": "translateMarkingMenuImpl", "builtin.rotate": "rotateMarkingMenuImpl",
                "builtin.scale": "scaleMarkingMenuImpl", "builtin.transform": "translateMarkingMenuImpl"}
SELECT_OPTIONS = "selectMarkingMenuImpl"


def walk(sub, path):
    """Yield (path, label, action) for every entry, depth first; Sub actions included."""
    for pos in RADIALS:
        if pos in sub.radial:
            label, action = sub.radial[pos]
            yield f"{path}/{pos}", label, action
            if isinstance(action, Sub):
                yield from walk(action, f"{path}/{pos}")
    for i, entry in enumerate(sub.items):
        if entry == DIVIDER:
            continue
        label, action = entry
        yield f"{path}/{i}", label, action
        if isinstance(action, Sub):
            yield from walk(action, f"{path}/{i}")
