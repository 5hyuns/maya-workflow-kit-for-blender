# SPDX-License-Identifier: GPL-3.0-or-later
"""On / off state and action of the panel menu and panel toolbar ``set`` keys of one 3D View (``state``, ``apply``):
shading, lighting, renderer, Show filters, camera display toggles, colour management, Isolate, layouts; their key
tables (``TIPS``, ``FAILS``, ``TOGGLE_OFF``, ``CAMERA_KEYS``, ``RADIO``, ``SET_KEYS``, ``TOOLBAR_KEYS``) and
``main_region``. Rows: ``panel_menu_data``; the operator that runs a key: ``panel_menus.ALLSET_OT_panel_set``."""

import bpy

from ..operators import view as view_ops
from . import camera_bookmarks
from .panel_cameras import _space, camera_locked, panel_camera, view_camera
from .panel_menu_data import ALL_TYPES, LAYOUTS, LIGHTING, RENDERER, SHADING, SHOW, VIEW


# Maya camera display toggles (Maya panel toolbar) -> Blender camera data.
# Blender draws title and action safe areas together (one flag).
CAMERA_DATA = {"FILM_GATE": "show_sensor", "GATE_MASK": "show_passepartout",
               "SAFE_ACTION": "show_safe_areas", "SAFE_TITLE": "show_safe_areas"}
CAMERA_KEYS = {"CAMERA_LOCK", *CAMERA_DATA}

# Toolbar toggles whose Maya off state is another mode (Maya panel toolbar):
# Wireframe off = smooth shaded, Smooth Shade All off = wireframe, Use All Lights off = default lighting.
TOGGLE_OFF = {"SHADE_WIRE": "SHADE_SMOOTH", "SHADE_SMOOTH": "SHADE_WIRE", "LIGHT_ALL": "LIGHT_DEFAULT"}

# Maya colour management icons (Maya panel toolbar: exposure / gamma icon = toggle between the
# default and the last other value, view transform check box = colour management on / off). Blender keeps these per
# scene (view settings); the last values live in Scene ID properties.
EXPOSURE_LAST, GAMMA_LAST, TRANSFORM_LAST = "allset_exposure_last", "allset_gamma_last", "allset_view_transform_last"
RAW = 'Raw'

FAILS = {
    "SELECT_CAMERA": "This view has no camera: Select Camera works in a perspective view, the top / front / side "
                     "views and a view that looks through a camera",
    "CAMERA_LOCK": "Look through a camera first (Panels > Perspective): Blender's persp view has no camera",
    "ISOLATE": "Select the objects to isolate",
    "BOOKMARK": camera_bookmarks.NO_CAMERA,
}
for _k in CAMERA_DATA:
    FAILS[_k] = FAILS["CAMERA_LOCK"]

TIPS = {
    "TUMBLE_SELECTION": "Tumble around the selection: Blender's Orbit Around Selection preference "
                        "(opens Preferences > Navigation; the kit doesn't change preferences)",
    "TUMBLE_COI": "Tumble around the center of interest: Orbit Around Selection off "
                  "(opens Preferences > Navigation; the kit doesn't change preferences)",
    "SELECT_CAMERA": "Select camera: the camera this view looks through",
    "CAMERA_LOCK": "Lock Camera: the camera this view looks through can't be moved (Blender: its location and "
                   "rotation channels are locked)",
    "FILM_GATE": "Film gate (Blender: camera sensor frame)",
    "GATE_MASK": "Gate mask (Blender: passepartout)",
    "SAFE_ACTION": "Safe action (Blender draws the action and title safe areas together)",
    "SAFE_TITLE": "Safe title (Blender draws the action and title safe areas together)",
    "BOOKMARK": "Bookmarks: bookmark this view (the camera's place and lens). Right-click: the camera's bookmarks, "
                "Create 2D Bookmark, Edit 2D Bookmarks",
    "PAN_ZOOM": "2D Pan/Zoom: off shows the view without its 2D pan / zoom (a camera view: the camera's whole frame), "
                "on brings it back; the camera doesn't move. Tap \\ to switch it; hold \\ and middle-drag to pan, "
                "right-drag to zoom. Right-click: the 2D bookmarks",
    "GRID": "Grid",
    "SHOW_IMAGE_PLANES": "Image planes (Blender image empties: shown or hidden in every view, like Alt+4)",
    "SELECTION_HILITE": "Selection highlighting in this view (the Maya selection wire, and Blender's outline "
                        "where it was on)",
    "SHOW_NURBS_CURVES": "NURBS curves: curve objects in this view, and rig controls drawn as bone shapes "
                         "(their bones are shown or hidden in every view)",
    "SHOW_IK_HANDLES": "IK handles (the empties IK constraints follow: shown or hidden in every view)",
    "SHADE_WIRE": "Wireframe",
    "SHADE_SMOOTH": "Smooth shade all",
    "DEFAULT_MATERIAL": "Use default material",
    "HW_TEXTURE": "Textured",
    "LIGHT_ALL": "Use all lights",
    "ISOLATE": "Isolate select",
    "EXPOSURE": "Exposure: switch between 0 and the last exposure",
    "GAMMA": "Gamma: switch between 1 and the last gamma",
    "CM_ENABLE": "Colour management on / off (off = Blender's Raw view transform)",
    "LAYOUT_FOUR": "Four View: top, persp, front and side. " + view_ops.FOUR_VIEW_NOTE,
}


SHOW_HIDDEN = "allset_hidden_by_show"   # IK handles the Show menu hid (view-layer hide; only these come back)


def show_ik_handles(context, on):
    """Maya Show > IK Handles: Blender has no view filter for these empties, so the kit hides them in
    the view layer (every view) and marks them; showing again un-hides only marked ones."""
    from ..operators import by_type
    for ob in by_type.ik_handles(context.scene):
        try:
            if on and ob.get(SHOW_HIDDEN):
                ob.hide_set(False)
                del ob[SHOW_HIDDEN]
            elif not on and not ob.hide_get():
                ob.hide_set(True)
                ob[SHOW_HIDDEN] = True
        except RuntimeError:       # not in the view layer
            pass


def state(context, key):
    """On/off of a ``set`` row (None: plain command)."""
    space = _space(context)
    if space is None:
        return None
    if key in CAMERA_KEYS:
        ob = view_camera(context)
        if ob is None:
            return False
        if key == "CAMERA_LOCK":
            return camera_locked(ob)
        return ob.type == 'CAMERA' and bool(getattr(ob.data, CAMERA_DATA[key]))
    if key == "ISOLATE":
        return space.local_view is not None
    if key == "PAN_ZOOM":
        return camera_bookmarks.pan_zoom_on(context.region_data or space.region_3d)
    if key == "CM_ENABLE":
        return context.scene.view_settings.view_transform != RAW
    sh = space.shading
    if key == "SHADE_WIRE":
        return sh.type == 'WIREFRAME'
    if key == "SHADE_SMOOTH":
        return sh.type != 'WIREFRAME'
    if key == "DEFAULT_MATERIAL":
        return sh.color_type == 'SINGLE'
    if key == "HW_TEXTURE":
        return sh.color_type == 'TEXTURE'
    if key == "LIGHT_DEFAULT":
        return sh.type in ('SOLID', 'WIREFRAME') and sh.light != 'FLAT'
    if key == "LIGHT_ALL":
        return (sh.type == 'MATERIAL' and sh.use_scene_lights) or \
            (sh.type == 'RENDERED' and sh.use_scene_lights_render)
    if key == "LIGHT_FLAT":
        return sh.type in ('SOLID', 'WIREFRAME') and sh.light == 'FLAT'
    if key == "RENDER_VP2":
        return sh.type != 'RENDERED'
    if key == "RENDER_ENGINE":
        return sh.type == 'RENDERED'
    if key == "TUMBLE_SELECTION":
        return context.preferences.inputs.use_rotate_around_active
    if key == "TUMBLE_COI":
        return not context.preferences.inputs.use_rotate_around_active
    if key == "GRID":
        from . import maya_grid
        return maya_grid.visible(space)
    if key == "SHOW_IMAGE_PLANES":
        from ..operators import global_keys4
        planes = global_keys4.image_planes(context.scene)
        return not planes or any(getattr(o, f) for o in planes for f in global_keys4.IMAGE_FLAGS)
    if key == "SHOW_NURBS_CURVES":
        return space.show_object_viewport_curve
    if key == "SELECTION_HILITE":
        from . import selection_wire
        return selection_wire.highlighting(context)
    if key == "SHOW_IK_HANDLES":
        from ..operators import by_type
        return not any(o.get(SHOW_HIDDEN) for o in by_type.ik_handles(context.scene))
    if key in ("LAYOUT_SINGLE", "LAYOUT_FOUR"):
        from . import four_view                 # four real panels
        four = four_view.is_four(context.screen) if context.screen is not None else False
        return four == (key == "LAYOUT_FOUR")
    return None


RADIO = {"SHADE_WIRE", "SHADE_SMOOTH", "LIGHT_DEFAULT", "LIGHT_ALL", "LIGHT_FLAT", "RENDER_VP2",
         "RENDER_ENGINE", "TUMBLE_SELECTION", "TUMBLE_COI", "LAYOUT_SINGLE", "LAYOUT_FOUR"}
SET_KEYS = [s[1] for menu in (VIEW, SHADING, LIGHTING, SHOW, RENDERER, LAYOUTS) for s in menu
            if s[0] == "set"]
# keys only the panel toolbar uses (ui/panel_toolbar.py)
TOOLBAR_KEYS = ["FILM_GATE", "GATE_MASK", "SAFE_ACTION", "SAFE_TITLE", "ISOLATE", "EXPOSURE", "GAMMA", "CM_ENABLE",
                "BOOKMARK", "PAN_ZOOM"]

# Shading / overlay values "Apply Current to All" copies (Maya: current panel's settings to all).
_COPY_SHADING = ("type", "light", "color_type", "show_xray", "show_backface_culling", "show_shadows",
                 "use_dof", "use_scene_lights", "use_scene_world")
_COPY_OVERLAY = ("show_wireframes", "show_xray_bone", "show_floor", "show_ortho_grid", "grid_lines", "show_text",
                 "show_outline_selected", "show_object_origins", "show_motion_paths")


def main_region(area):
    """The area's WINDOW region whose view is ``space.region_3d`` (quad views: the user view)."""
    space = area.spaces.active
    wins = [r for r in area.regions if r.type == 'WINDOW']
    rv3d = getattr(space, "region_3d", None)
    return next((r for r in wins if r.data == rv3d), wins[-1] if wins else None)


_before_render = {}   # 3D View space pointer -> shading type before Rendered (IPR / Renderer menu)


def enter_rendered(space):
    sh = space.shading
    if sh.type != 'RENDERED':
        _before_render[space.as_pointer()] = sh.type
        sh.type = 'RENDERED'


def leave_rendered(space):
    """Back to the shading the view had before Rendered (Maya: stopping IPR keeps the panel's mode, #24)."""
    sh = space.shading
    if sh.type == 'RENDERED':
        sh.type = _before_render.pop(space.as_pointer(), 'SOLID')


def apply(context, key):
    space = _space(context)
    if space is None:
        return False
    sh = space.shading
    if key == "SHADE_WIRE":
        sh.type = 'WIREFRAME'
    elif key == "SHADE_SMOOTH":
        sh.type = 'SOLID'
    elif key == "DEFAULT_MATERIAL":
        sh.color_type = 'MATERIAL' if sh.color_type == 'SINGLE' else 'SINGLE'
    elif key == "HW_TEXTURE":
        sh.color_type = 'MATERIAL' if sh.color_type == 'TEXTURE' else 'TEXTURE'
    elif key == "LIGHT_DEFAULT":
        if sh.type not in ('SOLID', 'WIREFRAME'):
            sh.type = 'SOLID'
        sh.light = 'STUDIO'
    elif key == "LIGHT_ALL":
        sh.type = 'MATERIAL'
        sh.use_scene_lights = True
        sh.use_scene_world = False
    elif key == "LIGHT_FLAT":
        if sh.type not in ('SOLID', 'WIREFRAME'):
            sh.type = 'SOLID'
        sh.light = 'FLAT'
    elif key == "RENDER_VP2":
        leave_rendered(space)
    elif key == "RENDER_ENGINE":
        enter_rendered(space)
    elif key in ("TUMBLE_SELECTION", "TUMBLE_COI"):
        # Blender's Orbit Around Selection is a user preference, which the kit never writes:
        # the items show it and open Preferences > Navigation to change it.
        try:
            bpy.ops.screen.userpref_show('INVOKE_DEFAULT', section='NAVIGATION')
        except RuntimeError:      # no window (background)
            return False
    elif key == "GRID":
        from . import maya_grid
        maya_grid.toggle(space)
    elif key == "SHOW_IMAGE_PLANES":
        from ..operators import global_keys4
        global_keys4.toggle_show(space, context.scene, 'IMAGE_PLANES')
    elif key == "SHOW_IK_HANDLES":
        show_ik_handles(context, not state(context, key))
    elif key == "SELECTION_HILITE":
        from . import selection_wire
        selection_wire.set_highlighting(context, not selection_wire.highlighting(context))
    elif key == "SHOW_NURBS_CURVES":
        # #173: the view's curve filter + the curve-shaped bone controls (ui/curve_controls.py)
        from . import curve_controls
        space.show_object_viewport_curve = not space.show_object_viewport_curve
        curve_controls.sync(space, context.scene)
    elif key in ("SHOW_ALL", "SHOW_NONE"):
        for t in ALL_TYPES:
            setattr(space, f"show_object_viewport_{t}", key == "SHOW_ALL")
        from . import curve_controls
        curve_controls.sync(space, context.scene)
    elif key == "APPLY_ALL":
        for screen in bpy.data.screens:
            for area in screen.areas:
                for other in area.spaces:
                    if other.type != 'VIEW_3D' or other == space:
                        continue
                    for name in _COPY_SHADING:
                        setattr(other.shading, name, getattr(sh, name))
                    for name in _COPY_OVERLAY:
                        setattr(other.overlay, name, getattr(space.overlay, name))
    elif key == "SELECT_CAMERA":
        cam = panel_camera(context, make=True)
        if cam is None:
            return False
        for ob in context.view_layer.objects:
            if ob is not None and ob.select_get():
                ob.select_set(False)
        try:
            cam.select_set(True)
        except RuntimeError:
            pass
        context.view_layer.objects.active = cam
    elif key in CAMERA_KEYS:
        ob = view_camera(context)
        if ob is None or (key != "CAMERA_LOCK" and ob.type != 'CAMERA'):
            return False
        if key == "CAMERA_LOCK":
            on = not camera_locked(ob)
            ob.lock_location = (on,) * 3
            ob.lock_rotation = (on,) * 3
        else:
            prop = CAMERA_DATA[key]
            setattr(ob.data, prop, not getattr(ob.data, prop))
    elif key == "ISOLATE":
        area = context.area
        if area is None or area.type != 'VIEW_3D':
            return False
        if space.local_view is None and not any(ob.select_get() for ob in context.view_layer.objects if ob):
            return False
        with context.temp_override(area=area, region=main_region(area)):
            bpy.ops.allset.isolate()        # isolating a group shows its children
    elif key in ("EXPOSURE", "GAMMA", "CM_ENABLE"):
        _toggle_colour(context.scene, key)
    elif key == "BOOKMARK":
        return camera_bookmarks.add(context) is not None
    elif key == "PAN_ZOOM":
        return camera_bookmarks.toggle_pan_zoom(context)
    elif key in ("LAYOUT_SINGLE", "LAYOUT_FOUR"):
        # Issue #148: Maya's layouts = four real panels (ui/four_view.py); Single Perspective View keeps
        # the persp panel, Four View puts every panel back with its own settings
        from . import four_view
        from ..operators import view
        # any editor can be one of the panels: the four view is never split again, one panel never joined again
        area, window = context.area, context.window
        got = four_view.set_layout(context, window, key == "LAYOUT_FOUR", area)
        if key == "LAYOUT_SINGLE":
            area = got or area
            if area.type == 'VIEW_3D':
                view.ensure_persp(area, area.spaces.active)     # Maya: Single Perspective is the persp camera (#8)
    else:
        return False
    return True


def _toggle_colour(scene, key):
    vs = scene.view_settings
    if key == "CM_ENABLE":
        if vs.view_transform != RAW:
            scene[TRANSFORM_LAST] = vs.view_transform
            vs.view_transform = RAW
        else:
            try:
                vs.view_transform = scene.get(TRANSFORM_LAST, 'Standard')
            except TypeError:       # a transform of another colour config
                vs.view_transform = 'Standard'
        return
    prop, default, last = ("exposure", 0.0, EXPOSURE_LAST) if key == "EXPOSURE" else ("gamma", 1.0, GAMMA_LAST)
    value = getattr(vs, prop)
    if abs(value - default) > 1e-6:
        scene[last] = value
        setattr(vs, prop, default)
    else:
        setattr(vs, prop, scene.get(last, default))
