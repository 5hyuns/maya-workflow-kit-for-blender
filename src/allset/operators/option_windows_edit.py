# SPDX-License-Identifier: GPL-3.0-or-later
"""Step 140 Maya option windows: modeling, parenting and key commands (issues #33, #35).

Same spec as operators/option_windows.py (``F`` fields, ``Window`` = one ``allset.opt_<key>`` operator); labels and
factory defaults read from Maya 2022 (); what the values do was checked with
Maya (). option_windows.py appends ``WINDOWS`` to its own list, so this
module only imports ``F`` / ``Window`` / helpers from it. Maya fields Blender can't honour are listed in ``missing``
(drawn greyed), never as fields. Plan / decisions: , 
"""

import math

import bpy
from mathutils import Vector

from .option_windows import F, Window, _components, _k  # noqa: F401  (option_windows imports this module at its end)

# --- key commands (Key / Edit > Keys; ) -------------------------------

_OBJECTS = F("objects", "Objects:", "enum", "Selected", items=("Selected", "All"))


def _scope_fields(objects=True):
    """keySetOptionBoxCommon: the rows every key command window starts with (option_boxes_140.md:77-88)."""
    return ([_OBJECTS] if objects else []) + [
        F("hierarchy", "Hierarchy:", "enum", "Selected", items=("Selected", "Below")),
        F("channels", "Channels:", "enum", "All keyable", items=("All keyable", "From Channel Box")),
        F("driven", "Driven channels:", "bool", False),
        F("shapes", "Shapes:", "bool", True),
        F("time_range", "Time range:", "enum", "All", items=("All", "Start/End", "Time Slider")),
        F("start", "Start time:", "float", 0.0, lo=-1e6, hi=1e6),
        F("end", "End time:", "float", 10.0, lo=-1e6, hi=1e6)]


# Control points (keys on CVs / vertices) have no Blender counterpart: a mesh vertex isn't an animatable channel
_CONTROL_POINTS = "Control points (Blender animates no vertices: shape keys are the Shapes)"


def _tk():
    from . import time_keys
    return time_keys


def _scope(context, v):
    tk = _tk()
    scope = tk.KeyScope.of(v)
    if not tk.scope_nodes(context, scope):
        raise RuntimeError("Nothing selected.")
    return scope


def _done(context):
    for area in context.screen.areas if context.screen else ():
        area.tag_redraw()
    return {'FINISHED'}


def _run_delete(context, v):
    _tk().delete_scope(context, _scope(context, v), v["method"], v["adjustment"], v["connect"])
    return _done(context)


def _run_cut(context, v):
    _tk().delete_scope(context, _scope(context, v), v["method"], v["adjustment"], v["connect"], clipboard=True)
    return _done(context)


def _run_copy(context, v):
    _tk().copy_scope(context, _scope(context, v), v["method"])
    return _done(context)


def _run_paste(context, v):
    tk = _tk()
    if not tk._CLIPBOARD.get("nodes"):
        raise RuntimeError("The animation clipboard is empty: copy or cut keys first.")
    if not tk.nodes(context):
        raise RuntimeError("Nothing selected.")
    tk.paste_scope(context, time_range=v["time_range"], start=v["start"], end=v["end"], time_offset=v["time_offset"],
                   value_offset=v["value_offset"], copies=v["copies"], method=v["method"],
                   replace_region=v["replace_region"])
    return _done(context)


def _run_scale(context, v):
    _tk().scale_scope(context, _scope(context, v), v["method"], v["only_specified"], v["time_scale"], v["time_pivot"],
                      v["value_scale"], v["value_pivot"], v["new_start"], v["new_end"])
    return _done(context)


def _run_snap(context, v):
    _tk().snap_scope(context, _scope(context, v), v["snap"], v["time_multiple"], v["value_multiple"])
    return _done(context)


_DELETE_TAIL = [
    F("method", "Method:", "enum", "Keys", items=("Keys", "Segments")),
    F("adjustment", "Adjustment:", "enum", "None", items=("None", "Collapse")),
    F("connect", "Connect:", "bool", False)]

KEY_WINDOWS = [
    # option_boxes_140.md:77-90
    Window("delete_keys", "Delete Keys Options", "Delete Keys", None, _scope_fields() + _DELETE_TAIL, _run_delete,
           paths=("Key/Delete Keys", "Edit/Keys/Delete Keys"), missing=(_CONTROL_POINTS,)),
    # :92-95
    Window("cut_keys", "Cut Keys Options", "Cut Keys", None, _scope_fields(objects=False) + _DELETE_TAIL, _run_cut,
           paths=("Key/Cut Keys", "Edit/Keys/Cut Keys"),
           missing=(_CONTROL_POINTS, "Method: Range (Maya cutKey has no area option)")),
    # :97-99
    Window("copy_keys", "Copy Keys Options", "Copy Keys", None, _scope_fields(objects=False) + [
        F("method", "Method:", "enum", "Keys", items=("Keys", "Segments"))], _run_copy,
        paths=("Key/Copy Keys", "Edit/Keys/Copy Keys"),
        missing=(_CONTROL_POINTS, "Method: Range (Maya copyKey has no area option)")),
    # :101-113
    Window("paste_keys", "Paste Keys Options", "Paste Keys", None, [
        F("time_range", "Time range:", "enum", "Current", items=("Start", "Start/End", "Current", "Clipboard")),
        F("start", "Start time:", "float", 0.0, lo=-1e6, hi=1e6), F("end", "End time:", "float", 10.0, lo=-1e6, hi=1e6),
        F("time_offset", "Time offset:", "float", 0.0, lo=-1e6, hi=1e6),
        F("value_offset", "Value offset:", "float", 0.0, lo=-1e6, hi=1e6),
        F("copies", "Copies:", "int", 1, lo=1, hi=100),
        F("method", "Paste method:", "enum", "Merge", items=("Insert", "Replace", "Merge")),
        F("replace_region", "Replace region:", "enum", "Time range", items=("Time range", "Entire curve"))],
        _run_paste, paths=("Key/Paste Keys", "Edit/Keys/Paste Keys"),
        missing=("Selected keys override specified time range", "Clipboard adjustment: Scale / Fit (Preserve only)",
                 "Connect")),
    # :115-118
    Window("scale_keys", "Scale Keys Options", "Scale Keys", None, _scope_fields() + [
        F("method", "Method:", "enum", "Scale/Pivot", items=("Scale/Pivot", "Start/End")),
        F("only_specified", "", "bool", True, text="Only scale specified keys"),
        F("time_scale", "Time scale:", "float", 1.0, lo=-1e6, hi=1e6),
        F("time_pivot", "Time pivot:", "float", 0.0, lo=-1e6, hi=1e6),
        F("value_scale", "Value scale:", "float", 1.0, lo=-1e6, hi=1e6),
        F("value_pivot", "Value pivot:", "float", 0.0, lo=-1e6, hi=1e6),
        F("new_start", "New start time:", "float", 1.0, lo=-1e6, hi=1e6),
        F("new_end", "New end time:", "float", 10.0, lo=-1e6, hi=1e6)], _run_scale,
        paths=("Key/Scale Keys", "Edit/Keys/Scale Keys"), missing=(_CONTROL_POINTS,)),
    # :120-123
    Window("snap_keys", "Snap Keys Options", "Snap Keys", None, _scope_fields() + [
        F("snap", "Snap:", "enum", "Times", items=("Times", "Values", "Both")),
        F("time_multiple", "Snap times to multiple of:", "float", 1.0, lo=0.0, hi=1000.0),
        F("value_multiple", "Snap values to multiple of:", "float", 1.0, lo=0.0, hi=1000.0)], _run_snap,
        paths=("Key/Snap Keys", "Edit/Keys/Snap Keys"), missing=(_CONTROL_POINTS,)),
]


# --- Edit menu (option_boxes_140.md:62-75, :154-167) --------------------------------------------------------------

def _run_parent(context, v):
    return bpy.ops.allset.parent('EXEC_DEFAULT', preserve_position=v["preserve"])


def _run_unparent(context, v):
    return bpy.ops.allset.unparent('EXEC_DEFAULT', preserve_position=v["preserve"])


def _run_ungroup(context, v):
    if not any(ob.children for ob in context.selected_objects):
        raise RuntimeError("Select a group to ungroup.")
    return bpy.ops.allset.ungroup('EXEC_DEFAULT', under='WORLD' if v["under"] == "World" else 'PARENT',
                                  preserve_position=v["preserve"])


def _run_duplicate_special(context, v):
    if v["smart"]:
        # Smart transform: each copy repeats the transform between the last duplicate and its source (the kit's
        # Duplicate with Transform, Shift+D); the offsets below are Maya's for non-smart copies only
        res = {'CANCELLED'}
        for _i in range(max(1, v["copies"])):
            res = bpy.ops.allset.duplicate_with_transform('EXEC_DEFAULT')
            if res != {'FINISHED'}:
                break
        return res
    k = _k(context)
    return bpy.ops.allset.duplicate_special(
        'EXEC_DEFAULT', geometry_type=v["geometry_type"].upper(),
        group_under={"Parent": 'PARENT', "World": 'WORLD', "New group": 'NEW_GROUP'}[v["group_under"]],
        # Maya Y up: Maya Y -> Blender Z, Maya Z -> Blender -Y ( step 57)
        translate=Vector((v["translate"][0], -v["translate"][2], v["translate"][1])) * k,
        rotate=tuple(math.radians(a) for a in (v["rotate"][0], -v["rotate"][2], v["rotate"][1])),
        scale=(v["scale"][0], v["scale"][2], v["scale"][1]), copies=v["copies"])


_PRESERVE = F("preserve", "", "bool", True, text="Preserve position")

EDIT_WINDOWS = [
    Window("parent", "Parent Options", "Parent", ("allset.parent", {}), [_PRESERVE], _run_parent,
           paths=("Edit/Parent",), missing=("Parent method: Add instance (Blender objects have one parent)",)),
    Window("unparent", "Unparent Options", "Unparent", ("allset.unparent", {}), [_PRESERVE], _run_unparent,
           paths=("Edit/Unparent",), missing=("Unparent method: Remove instance",)),
    Window("ungroup", "Ungroup Options", "Ungroup", ("allset.ungroup", {}), [
        F("under", "Ungroup under:", "enum", "Parent", items=("Parent", "World")), _PRESERVE], _run_ungroup,
        paths=("Edit/Ungroup",)),
    # step 103's window (option_windows.py "duplicate_special") plus Smart transform, which the kit has
    # (option_boxes_140.md:154-167); the main loop deletes the old spec at merge
    Window("duplicate_special_maya", "Duplicate Special Options", "Duplicate Special", None, [
        F("geometry_type", "Geometry type:", "enum", "Copy", items=("Copy", "Instance")),
        F("group_under", "Group under:", "enum", "Parent", items=("Parent", "World", "New group")),
        F("smart", "", "bool", False, text="Smart transform"),
        F("translate", "Translate:", "vec3", (0.0, 0.0, 0.0)), F("rotate", "Rotate:", "vec3", (0.0, 0.0, 0.0)),
        F("scale", "Scale:", "vec3", (1.0, 1.0, 1.0)), F("copies", "Number of copies:", "int", 1, lo=1, hi=1000)],
        _run_duplicate_special, paths=("Edit/Duplicate Special",),
        missing=("Duplicate input graph", "Duplicate input connections", "Instance leaf nodes",
                 "Assign unique name to children nodes")),
]


# --- Edit Mesh / Mesh Tools (option_boxes_140.md:136-152, :239-256) ------------------------------------------------

def _edit_only(context):
    from .poly_maya import CONNECT_WARNING
    if context.mode != 'EDIT_MESH':
        raise RuntimeError(CONNECT_WARNING)       # Maya warns on an object (menu_map.OBJECT_MODE)


def _run_connect(context, v):
    _edit_only(context)
    return bpy.ops.allset.connect('EXEC_DEFAULT', insert_with_edge_flow=v["edge_flow"],
                                  adjust_edge_flow=v["adjust_edge_flow"])


def _run_connect_tool(context, v):
    _edit_only(context)
    return bpy.ops.allset.connect('EXEC_DEFAULT', segments=v["segments"], slide=v["slide"])


def _run_circularize(context, v):
    k = _k(context)
    return _components(context, "allset.circularize", 'VERT', normal_offset=v["normal_offset"] * k,
                       radial_offset=v["radial_offset"] * k, twist=math.radians(v["twist"]),
                       evenly_distribute=v["evenly"], divisions=v["divisions"])


def _run_make_hole(context, v):
    if context.mode != 'EDIT_MESH':
        raise RuntimeError("Select the face to cut, then the face whose shape makes the hole.")
    return bpy.ops.allset.make_hole('EXEC_DEFAULT', merge_mode=v["merge_mode"])


def loop_cut_options(context, v):
    """Put the Insert Edge Loop values on Blender's Loop Cut tool (the active edit-mesh tool): Multiple edge loops =
    Number of Cuts, Equal distance from edge = Edge Slide Even, Insert with edge flow = Loop Cut Smoothness
    (Adjust Edge Flow; delegated, ). Returns the tool's macro properties or None."""
    tool = context.workspace.tools.from_space_view3d_mode('EDIT_MESH', create=False)
    if tool is None or tool.idname != "builtin.loop_cut":
        return None
    props = tool.operator_properties("mesh.loopcut_slide")
    cut, slide = props.MESH_OT_loopcut, props.TRANSFORM_OT_edge_slide
    cut.number_cuts = v["loops"] if v["maintain"] == "Multiple edge loops" else 1
    cut.smoothness = v["adjust_edge_flow"] if v["edge_flow"] else 0.0
    slide.use_even = v["maintain"] == "Equal distance from edge"
    return props


def _run_insert_edge_loop(context, v):
    res = bpy.ops.allset.menu_tool('EXEC_DEFAULT', tool="builtin.loop_cut", edit=True)
    if res == {'FINISHED'}:
        loop_cut_options(context, v)
    return res


MESH_WINDOWS = [
    Window("connect", "Connect Components Options", "Connect", None, [
        F("edge_flow", "", "bool", False, text="Insert with edge flow"),
        F("adjust_edge_flow", "Adjust Edge Flow:", "float", 1.0, lo=-1.0, hi=2.0)], _run_connect,
        paths=("Edit Mesh/Connect",)),
    Window("connect_tool", "Connect Tool", "Connect", None, [
        F("slide", "Slide:", "float", 0.5, lo=0.0, hi=1.0), F("segments", "Segments:", "int", 1, lo=1, hi=10)],
        _run_connect_tool, paths=("Mesh Tools/Connect",),
        missing=("Pinch", "Active option (MMB drag) / Keyboard and mouse shortcuts")),
    Window("circularize", "Polygon Circularize Options", "Circularize", ("allset.circularize", {}), [
        F("normal_offset", "Normal Offset:", "length", 0.0, lo=-100.0, hi=100.0),
        F("radial_offset", "Radial Offset:", "length", 0.0, lo=-100.0, hi=100.0),
        F("twist", "Twist:", "float", 0.0, lo=-360.0, hi=360.0),
        F("evenly", "Evenly Distribute:", "bool", True),
        F("divisions", "Add Divisions:", "int", 0, lo=0, hi=50)], _run_circularize,
        paths=("Edit Mesh/Circularize",),
        missing=("Relax Interior", "Alignment: Automatic / Surface", "Smoothing Angle", "Supporting Edges")),
    Window("make_hole", "Make Hole Tool", "Make Hole", None, [
        F("merge_mode", "Merge mode:", "enum", "None",
          items=("First", "Middle", "Second", "Project First", "Project Middle", "Project Second", "None"))],
        _run_make_hole, paths=("Mesh Tools/Make Hole",)),
    Window("insert_edge_loop", "Insert Edge Loop Tool", "Insert Edge Loop", None, [
        F("maintain", "Maintain position:", "enum", "Relative distance from edge",
          items=("Relative distance from edge", "Equal distance from edge", "Multiple edge loops")),
        F("loops", "Number of edge loops:", "int", 2, lo=1, hi=100),
        F("edge_flow", "", "bool", False, text="Insert with edge flow"),
        F("adjust_edge_flow", "Adjust Edge Flow:", "float", 1.0, lo=0.0, hi=1.0)], _run_insert_edge_loop,
        paths=("Mesh Tools/Insert Edge Loop",),
        missing=("Use Equal Multiplier", "Auto complete", "Fix Quads", "Smoothing angle")),
]

WINDOWS = KEY_WINDOWS + EDIT_WINDOWS + MESH_WINDOWS
