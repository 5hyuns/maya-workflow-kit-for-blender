# SPDX-License-Identifier: GPL-3.0-or-later
"""Blender version differences in one place (step 118, docs/compat_5x.md).

The kit targets Blender 4.5 (decision 4) and runs on 5.0-5.2. Every check of "which Blender is this" lives
here; feature code calls these helpers and stays the same on every version. Each helper does the 4.5 thing
first, so 4.5 behaviour is unchanged.
"""

import bpy

VERSION = tuple(bpy.app.version[:2])
TARGET = (4, 5)
IS_TARGET = VERSION == TARGET


# Properties tab flags newer than 4.5 (measured, step 118): a 4.5-saved file (the Maya Workflow Kit template) opens in 5.x with
# them on, so they carry no meaning in a kit dock's role (ui/maya_dock.role).
LATER_PROPERTIES_TABS = frozenset({"show_properties_strip", "show_properties_strip_modifier"})


def has_op(module, name):
    """Does this Blender have the operator? (``bpy.ops.<mod>.<name>`` returns a wrapper for any name.)"""
    try:
        getattr(module, name).get_rna_type()
        return True
    except (AttributeError, KeyError):
        return False


def strips(sequence_editor):
    """The sequencer's top-level strips: ``strips`` (4.4+); 5.0 removed ``sequences``."""
    if hasattr(sequence_editor, "strips"):
        return sequence_editor.strips
    return sequence_editor.sequences


def fcurve_owners(action):
    """Collections holding the action's F-curves: every channelbag of a layered action (4.4+); 5.0 removed
    the legacy ``Action.fcurves`` / ``Action.groups``, which 4.5 still has as a proxy of the first slot."""
    owners = []
    for layer in getattr(action, "layers", ()):
        for strip in layer.strips:
            owners.extend(getattr(strip, "channelbags", ()))
    if not owners and hasattr(action, "fcurves"):
        owners.append(action)
    return owners


def action_fcurves(action, slot=None):
    """F-curves of the action for one slot (``slot`` None = every slot), a list."""
    if action is None:
        return []
    if slot is not None:
        bag = channelbag(action, slot)
        return list(bag.fcurves) if bag is not None else []
    return [fc for owner in fcurve_owners(action) for fc in owner.fcurves]


def channelbag(action, slot):
    """The channelbag of ``slot`` (None when the slot has no keys yet)."""
    try:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
    except ImportError:
        return None
    return action_get_channelbag_for_slot(action, slot)


def id_fcurves(anim_id):
    """F-curves the ID's animation_data plays (its action's assigned slot), a list."""
    ad = getattr(anim_id, "animation_data", None)
    if ad is None or ad.action is None:
        return []
    slot = getattr(ad, "action_slot", None)
    if slot is None:
        return list(getattr(ad.action, "fcurves", ()))
    return action_fcurves(ad.action, slot)


def id_fcurve_collection(anim_id):
    """The collection (with ``find`` / ``new`` / ``remove``) of the ID's slot F-curves, or None."""
    ad = getattr(anim_id, "animation_data", None)
    if ad is None or ad.action is None:
        return None
    slot = getattr(ad, "action_slot", None)
    if slot is None:
        return getattr(ad.action, "fcurves", None)
    bag = channelbag(ad.action, slot)
    return bag.fcurves if bag is not None else None


# --- Timeline ------------------------------------------------------------------------------
# Blender 5.x: the Timeline is a Dope Sheet mode and bl_ui.space_time has no TIME_HT_editor_buttons /
# TIME_MT_editor_menus; the timeline header is DOPESHEET_HT_editor_buttons.draw_header and
# DOPESHEET_MT_editor_menus with ``mode == 'TIMELINE'`` ($S52\startup\bl_ui\space_dopesheet.py:198-230, :395-412).

def _legacy_timeline():
    from bl_ui import space_time
    return hasattr(space_time, "TIME_HT_editor_buttons")


LEGACY_TIMELINE = _legacy_timeline()


def timeline_header_classes():
    """(class whose ``draw_header`` draws the timeline buttons, class whose ``draw_collapsible`` draws
    the timeline menus) of this Blender."""
    if LEGACY_TIMELINE:
        from bl_ui import space_time
        return space_time.TIME_HT_editor_buttons, space_time.TIME_MT_editor_menus
    from bl_ui import space_dopesheet
    return space_dopesheet.DOPESHEET_HT_editor_buttons, space_dopesheet.DOPESHEET_MT_editor_menus


# --- UV select mode -------------------------------------------------------------------------
# 4.5: uv_select_mode has 'ISLAND'; 5.x: uv_select_mode is VERTEX / EDGE / FACE and island selection is the
# separate ``use_uv_select_island`` (measured, step 118).

def uv_island_mode(ts):
    if hasattr(ts, "use_uv_select_island"):
        return ts.use_uv_select_island
    return ts.uv_select_mode == 'ISLAND'


def set_uv_island_mode(ts, island):
    """Island (Maya shell) selection on, or plain UV (vertex) selection."""
    if hasattr(ts, "use_uv_select_island"):
        if not island:
            ts.uv_select_mode = 'VERTEX'
        ts.use_uv_select_island = island
    else:
        ts.uv_select_mode = 'ISLAND' if island else 'VERTEX'


# --- Render output format -------------------------------------------------------------------
# 5.x: ImageFormatSettings.media_type (IMAGE / MULTI_LAYER_IMAGE / VIDEO) picks which file formats exist;
# 'FFMPEG' needs media_type 'VIDEO' first (measured, step 118). 4.5 has no media_type.
MEDIA_TYPE = "media_type" in bpy.types.ImageFormatSettings.bl_rna.properties


def set_file_format(image_settings, fmt):
    if MEDIA_TYPE:
        image_settings.media_type = ('VIDEO' if fmt == 'FFMPEG' else
                                     'MULTI_LAYER_IMAGE' if fmt == 'OPEN_EXR_MULTILAYER' else 'IMAGE')
    image_settings.file_format = fmt


# --- bmesh ----------------------------------------------------------------------------------
# 5.2 renamed pointmerge_facedata's ``vert_snap`` to ``vert_target`` (bmesh.ops docstring, measured, step 118).

def pointmerge_facedata(bm, verts, target):
    import bmesh
    key = "vert_target" if "vert_target" in (bmesh.ops.pointmerge_facedata.__doc__ or "") else "vert_snap"
    return bmesh.ops.pointmerge_facedata(bm, verts=verts, **{key: target})


# --- UV selection in bmesh ------------------------------------------------------------------
# 4.5: per UV layer, ``loop[uv].select`` / ``select_edge``; 5.x: one UV selection per loop,
# ``loop.uv_select_vert`` / ``uv_select_edge`` (BMLoopUV has only uv / pin_uv, measured, step 118).
def _loop_uv_select():
    import bmesh
    return hasattr(bmesh.types.BMLoop, "uv_select_vert")


LOOP_UV_SELECT = _loop_uv_select()


def uv_vert_selected(loop, uv):
    return loop.uv_select_vert if LOOP_UV_SELECT else loop[uv].select


def uv_edge_selected(loop, uv):
    return loop.uv_select_edge if LOOP_UV_SELECT else loop[uv].select_edge


def set_uv_vert_selected(loop, uv, value):
    if LOOP_UV_SELECT:
        loop.uv_select_vert = value
    else:
        loop[uv].select = value


def set_uv_edge_selected(loop, uv, value):
    if LOOP_UV_SELECT:
        loop.uv_select_edge = value
    else:
        loop[uv].select_edge = value


# --- Bone visibility ------------------------------------------------------------------------
# 4.5: a bone is hidden in pose / object mode by ``Bone.hide``; 5.x moved that to ``PoseBone.hide`` and
# ``Bone.hide`` only hides the edit bone (step 118, api notes).
POSE_BONE_HIDE = "hide" in bpy.types.PoseBone.bl_rna.properties


def bone_hidden(pb):
    return pb.hide if POSE_BONE_HIDE else pb.bone.hide


def set_bone_hidden(pb, hidden):
    if POSE_BONE_HIDE:
        pb.hide = hidden
    else:
        pb.bone.hide = hidden


def timeline_marker_menu():
    """The Timeline's Marker menu: TIME_MT_marker (4.5), DOPESHEET_MT_marker (5.x, $S52 space_dopesheet.py:573)."""
    return "TIME_MT_marker" if LEGACY_TIMELINE else "DOPESHEET_MT_marker"


def save_dialog_args(op):
    """Extra arguments Blender's own Ctrl+S / Ctrl+Shift+S items pass: 5.2 adds
    ``show_save_modified_images_dialog`` (IC keymap data, step 118); none in 4.5."""
    props = op.get_rna_type().properties
    return {"show_save_modified_images_dialog": True} if "show_save_modified_images_dialog" in props else {}


def read_region_row(fb, region, y):
    """One framebuffer row of the region (``read_color``), or None when ``y`` is outside it: 5.1+ raises on
    out-of-bounds reads where 4.5 returned garbage (step 118, api notes)."""
    y = int(y)
    if not 0 <= y < region.height or region.width <= 0:
        return None
    try:
        return fb.read_color(0, y, region.width, 1, 4, 0, 'UBYTE')
    except ValueError:
        return None


# --- Materials ------------------------------------------------------------------------------
# 5.0: every material uses nodes; ``Material.use_nodes`` is deprecated (prints a warning when set).
MATERIAL_ALWAYS_NODES = VERSION >= (5, 0)


def ensure_material_nodes(mat):
    if not MATERIAL_ALWAYS_NODES:
        mat.use_nodes = True


def material_uses_nodes(mat):
    return mat is not None and mat.node_tree is not None and (MATERIAL_ALWAYS_NODES or mat.use_nodes)


# --- Lights ---------------------------------------------------------------------------------
# 5.1: every light has a node tree; ``Light.use_nodes`` is deprecated (warns when read or set, measured step 137).
LIGHT_ALWAYS_NODES = VERSION >= (5, 1)


def ensure_light_nodes(light):
    """Turn the light's nodes on; True when this call turned them on (4.5 / 5.0)."""
    if LIGHT_ALWAYS_NODES or light.use_nodes:
        return False
    light.use_nodes = True
    return True


def release_light_nodes(light):
    """Turn off nodes ``ensure_light_nodes`` turned on (no-op where every light uses nodes)."""
    if not LIGHT_ALWAYS_NODES:
        light.use_nodes = False


def toolbar_back(theme):
    """The 3D View toolbar / sidebar background of the user's theme (read only — the kit never writes a theme,
    step 130): ``view_3d.space.button`` (4.5), ``regions.sidebars.back`` (5.0 theme migration table)."""
    regions = getattr(theme, "regions", None)
    if regions is not None and hasattr(regions, "sidebars"):
        return regions.sidebars.back
    return theme.view_3d.space.button


# --- GPU image shader -----------------------------------------------------------------------
# Kit textures (shelf icons) hold scene-linear colours. 4.5's builtin 'IMAGE' shader converts them for display;
# from 5.0 'IMAGE' draws the values as they are and the converting shader is
# 'IMAGE_SCENE_LINEAR_TO_REC709_SRGB' (5.0 Python API notes, GPU; seen as darker shelf icons, step 119).
LINEAR_IMAGE_SHADER = 'IMAGE' if VERSION < (5, 0) else 'IMAGE_SCENE_LINEAR_TO_REC709_SRGB'


# --- Unified paint settings -----------------------------------------------------------------
# 4.5: one ``ToolSettings.unified_paint_settings`` with ``unprojected_radius`` (a radius). 5.0+: each paint mode
# has its own (``tool_settings.weight_paint.unified_paint_settings``) and the scene size is ``unprojected_size``,
# a diameter (measured on 5.0.1 / 5.2.3: "Diameter of brush in Blender units", step 153, #90).
def unified_paint_settings(ts, paint="weight_paint"):
    """The unified paint settings that apply to paint mode ``paint`` (a ToolSettings member name)."""
    mode = getattr(ts, paint, None)
    ups = getattr(mode, "unified_paint_settings", None)
    return ups if ups is not None else ts.unified_paint_settings


def unprojected_radius(ups):
    """The brush radius in scene units."""
    if "unprojected_radius" in ups.bl_rna.properties:
        return ups.unprojected_radius
    return ups.unprojected_size / 2.0


def set_unprojected_radius(ups, radius):
    if "unprojected_radius" in ups.bl_rna.properties:
        ups.unprojected_radius = radius
    else:
        ups.unprojected_size = radius * 2.0


# --- Menus closing when the mouse leaves ----------------------------------------------------
# 4.5 closes a menu the mouse moved away from; 5.0 keeps menus and popups open until a click, with the preference
# ``PreferencesView.menu_close_leave`` (default off) for the old behaviour (5.0 release notes, user interface,
# 5953ff318c; measured on 5.2.3). Python has no call that closes a popup and the kit never writes preferences
# (step 130), so with the 5.x default a held option box can't close the Maya menu under it (step 153).
def menus_close_on_leave(prefs):
    return getattr(prefs.view, "menu_close_leave", True)
