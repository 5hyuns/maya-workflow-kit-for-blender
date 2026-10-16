# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya viewport panel menu bar: View, Shading, Lighting, Show, Renderer, Panels.

Every Maya modelPanel has its own menu bar (research/maya/ui_layout.md:242-244). Menu contents
follow Maya 2022 ``createModelPanelMenu.mel`` (View :1381-1640, Shading :2159-2290, Lighting
:2488-2522, Show :2578-2741, Renderer :509-664) and ``buildPanelPopupMenu.mel:273-427``
(Panels); re-implemented, only labels and order. Design: docs/steps/step_37.md 「계획」.

Only the menu part of the 3D View header changes: ``VIEW3D_MT_editor_menus.draw_collapsible``
(inherited from ``bpy.types.Menu``, called once by ``VIEW3D_HT_header.draw``,
$S\\startup\\bl_ui\\space_view3d.py:915) is overridden while the add-on is enabled; the
mode selector and the right-hand buttons (Maya's panel icon bar) stay Blender's. Blender's
View / Select / Add / Object ... menus stay reachable under 「Blender ▸」.

Item forms (one tuple per row):
``("prop", owner, prop, label)`` check box on ``space`` / ``shading`` / ``overlay`` / ``inputs``;
``("set", key, label)`` ``maya_kit.panel_set`` (radio / toggle state from ``state``);
``("run", label, op, props)`` an operator run in this view's main region;
``("menu", label, idname)``; ``("grey", label)`` no Blender equivalent; ``("sep", label)``.
"""

import json

import bpy
from bpy.props import EnumProperty, StringProperty

GREY_OP = "maya_kit.menu_unavailable"


def _sep(label=""):
    return ("sep", label)


def _grey(label):
    return ("grey", label)


def _run(label, op, **props):
    return ("run", label, op, props)


def _view(label, view):
    return _run(label, "maya_kit.hb_view", view=view)


VIEW = [
    ("set", "SELECT_CAMERA", "Select Camera"),
    _grey("Lock Camera"),
    _sep(),
    _run("Undo View Change", "maya_kit.view_history", direction='UNDO'),
    _run("Redo View Change", "maya_kit.view_history", direction='REDO'),
    _sep("Tumble Behaviour"),
    ("set", "TUMBLE_SELECTION", "Around Most Recent Selection"),
    ("set", "TUMBLE_COI", "Around Center of Interest"),
    _sep("Change View"),
    _run("Align Camera To Polygon", "view3d.view_axis", type='TOP', align_active=True),
    _grey("Center View of Selection"),
    _run("Default View", "maya_kit.view_home"),
    _run("Frame All", "maya_kit.frame", selected=False),
    _run("Frame Selection", "maya_kit.frame", selected=True),
    ("menu", "View Along Axis", "MAYAKIT_MT_panel_view_axis"),
    _sep(),
    _grey("Camera Attribute Editor..."),
    ("menu", "Camera Tools", "MAYAKIT_MT_panel_camera_tools"),
    _sep(),
    _grey("View Sequence Time"),
]

# Maya viewSet -vx = seen from +X (createModelPanelMenu.mel:1169-1203); axis names as Blender's
# (X = X, Y = Y, Z = Z: decision 5, docs/steps/step_37.md).
VIEW_AXIS = [_view("X", 'RIGHT'), _view("Y", 'BACK'), _view("Z", 'TOP'),
             _view("-X", 'LEFT'), _view("-Y", 'FRONT'), _view("-Z", 'BOTTOM')]

CAMERA_TOOLS = [
    _grey("Tumble Tool"), _grey("Track Tool"), _grey("Dolly Tool"),
    _run("Zoom Tool", "view3d.zoom_border"),
    _grey("2D Pan/Zoom Tool"), _grey("Grease Pencil Tool"),
    _sep(),
    _run("Roll Tool", "view3d.view_roll", type='ANGLE', angle=0.2618),
    _grey("Azimuth Elevation Tool"), _grey("Yaw-Pitch Tool"),
    _run("Fly Tool", "view3d.fly"),
    _run("Walk Tool", "view3d.walk"),
]

SHADING = [
    ("set", "SHADE_WIRE", "Wireframe"),
    ("set", "SHADE_SMOOTH", "Smooth Shade All"),
    _grey("Smooth Shade Selected Items"),
    _grey("Flat Shade All"),
    _grey("Flat Shade Selected Items"),
    _grey("Bounding Box"),
    _grey("Points"),
    _sep(),
    ("set", "DEFAULT_MATERIAL", "Use Default Material"),
    ("prop", "overlay", "show_wireframes", "Wireframe on Shaded"),
    ("prop", "shading", "show_xray", "X-Ray"),
    ("prop", "overlay", "show_xray_bone", "X-Ray Joints"),
    _grey("X-Ray Active Components"),
    _sep(),
    _grey("Interactive Shading"),
    _sep(),
    ("prop", "shading", "show_backface_culling", "Backface Culling"),
    _grey("Smooth Wireframe"),
    _sep(),
    ("set", "HW_TEXTURE", "Hardware Texturing"),
    _grey("Hardware Fog"),
    ("prop", "shading", "use_dof", "Depth of Field"),
    _sep(),
    ("set", "APPLY_ALL", "Apply Current to All"),
]

LIGHTING = [
    ("set", "LIGHT_DEFAULT", "Use Default Lighting"),
    ("set", "LIGHT_ALL", "Use All Lights"),
    _grey("Use Selected Lights"),
    ("set", "LIGHT_FLAT", "Use Flat Lighting"),
    _grey("Use No Lights"),
    _sep(),
    _grey("Two Sided Lighting"),
    ("prop", "shading", "show_shadows", "Shadows"),
]

# Maya object type -> SpaceView3D.show_object_viewport_<type> (None = no Blender filter).
SHOW_TYPES = (
    ("Controllers", None), ("NURBS Curves", "curve"), ("NURBS Surfaces", "surf"),
    ("NURBS CVs", None), ("NURBS Hulls", None), ("Polygons", "mesh"), ("Subdiv Surfaces", None),
    ("Planes", None), ("Lights", "light"), ("Cameras", "camera"), ("Image Planes", None),
    ("Joints", "armature"), ("IK Handles", None), ("Deformers", "lattice"), ("Dynamics", None),
    ("Particle Instancers", None), ("Fluids", "volume"), ("Hair Systems", "curves"),
    ("Follicles", None), ("nCloths", None), ("nParticles", None), ("nRigids", None),
    ("Dynamic Constraints", None), ("Locators", "empty"), ("Dimensions", None),
    ("Pivots", "@show_object_origins"), ("Handles", None), ("Texture Placements", None),
    ("Strokes", None), ("Motion Trails", "@show_motion_paths"), ("Plugin Shapes", None),
    ("Clip Ghosts", None), ("Grease Pencil", "grease_pencil"),
)
ALL_TYPES = ("mesh", "curve", "surf", "meta", "font", "curves", "pointcloud", "volume", "armature",
             "lattice", "empty", "grease_pencil", "camera", "light", "speaker", "light_probe")


def _show_row(label, target):
    if target is None:
        return _grey(label)
    if target.startswith("@"):
        return ("prop", "overlay", target[1:], label)
    return ("prop", "space", f"show_object_viewport_{target}", label)


SHOW = [
    ("menu", "Isolate Select", "MAYAKIT_MT_panel_isolate"),
    _sep(),
    ("set", "SHOW_ALL", "All"),
    ("set", "SHOW_NONE", "None"),
    _sep(),
    *[_show_row(label, t) for label, t in SHOW_TYPES],
    _sep(),
    ("prop", "space", "show_gizmo", "Manipulators"),
    ("prop", "overlay", "show_floor", "Grid"),
    ("prop", "overlay", "show_text", "HUD"),
    _grey("Hold-Outs"),
    ("prop", "overlay", "show_outline_selected", "Selection Highlighting"),
]

ISOLATE = [
    _run("View Selected", "view3d.localview", frame_selected=False),
]

RENDERER = [
    ("set", "RENDER_VP2", "Viewport 2.0"),
    _grey("Legacy Default Viewport"),
    _grey("Legacy High Quality Viewport"),
    _sep(),
    ("set", "RENDER_ENGINE", "{engine}"),   # Maya lists render overrides here (Arnold)
]

PANELS = [
    ("menu", "Perspective", "MAYAKIT_MT_panel_perspective"),
    _grey("Stereo"),
    ("menu", "Orthographic", "MAYAKIT_MT_panel_orthographic"),
    _run("Look Through Selected", "view3d.object_as_camera"),
    _grey("Camera Set"),
    _sep(),
    ("menu", "Panel", "MAYAKIT_MT_panel_panel"),
    _grey("Hypergraph Panel"),
    ("menu", "Layouts", "MAYAKIT_MT_panel_layouts"),
    _grey("Saved Layouts"),
    _sep(),
    _run("Tear Off...", "maya_kit.open_editor", ui_type='VIEW_3D'),
    _run("Tear Off Copy...", "maya_kit.open_editor", ui_type='VIEW_3D'),
    _sep(),
    _grey("Panel Editor..."),
]

PANEL_TYPES = (("Outliner", 'OUTLINER'), ("Graph Editor", 'FCURVES'), ("Dope Sheet", 'DOPESHEET'),
               ("Node Editor", 'ShaderNodeTree'), ("UV Editor", 'UV'), ("Model Panel", 'VIEW_3D'),
               ("Script Editor", 'TEXT_EDITOR'))

LAYOUTS = [
    ("set", "LAYOUT_SINGLE", "Single Perspective View"),
    ("set", "LAYOUT_FOUR", "Four View"),
]

# The menu bar, in Maya's order (createModelPanelMenu.mel:1931-2086).
BAR = (("View", "MAYAKIT_MT_panel_view"), ("Shading", "MAYAKIT_MT_panel_shading"),
       ("Lighting", "MAYAKIT_MT_panel_lighting"), ("Show", "MAYAKIT_MT_panel_show"),
       ("Renderer", "MAYAKIT_MT_panel_renderer"), ("Panels", "MAYAKIT_MT_panel_panels"))


# --- state ---------------------------------------------------------------------------

def _space(context):
    space = context.space_data
    return space if space is not None and space.type == 'VIEW_3D' else None


def _owner(space, context, owner):
    return {"space": space, "shading": space.shading, "overlay": space.overlay,
            "inputs": context.preferences.inputs}[owner]


def _scene_camera_view(context):
    rv3d = context.region_data or getattr(_space(context), "region_3d", None)
    return rv3d is not None and rv3d.view_perspective == 'CAMERA'


def state(context, key):
    """On/off of a ``set`` row (None: plain command)."""
    space = _space(context)
    if space is None:
        return None
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
    if key == "LAYOUT_SINGLE":
        return not space.region_quadviews
    if key == "LAYOUT_FOUR":
        return bool(space.region_quadviews)
    return None


RADIO = {"SHADE_WIRE", "SHADE_SMOOTH", "LIGHT_DEFAULT", "LIGHT_ALL", "LIGHT_FLAT", "RENDER_VP2",
         "RENDER_ENGINE", "TUMBLE_SELECTION", "TUMBLE_COI", "LAYOUT_SINGLE", "LAYOUT_FOUR"}
SET_KEYS = [s[1] for menu in (VIEW, SHADING, LIGHTING, SHOW, RENDERER, LAYOUTS) for s in menu
            if s[0] == "set"]

# Shading / overlay values "Apply Current to All" copies (Maya: current panel's settings to all).
_COPY_SHADING = ("type", "light", "color_type", "show_xray", "show_backface_culling", "show_shadows",
                 "use_dof", "use_scene_lights", "use_scene_world")
_COPY_OVERLAY = ("show_wireframes", "show_xray_bone", "show_floor", "show_text",
                 "show_outline_selected", "show_object_origins", "show_motion_paths")


def main_region(area):
    """The area's WINDOW region whose view is ``space.region_3d`` (quad views: the user view)."""
    space = area.spaces.active
    wins = [r for r in area.regions if r.type == 'WINDOW']
    rv3d = getattr(space, "region_3d", None)
    return next((r for r in wins if r.data == rv3d), wins[-1] if wins else None)


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
        if sh.type == 'RENDERED':
            sh.type = 'SOLID'
    elif key == "RENDER_ENGINE":
        sh.type = 'RENDERED'
    elif key == "TUMBLE_SELECTION":
        context.preferences.inputs.use_rotate_around_active = True
    elif key == "TUMBLE_COI":
        context.preferences.inputs.use_rotate_around_active = False
    elif key in ("SHOW_ALL", "SHOW_NONE"):
        for t in ALL_TYPES:
            setattr(space, f"show_object_viewport_{t}", key == "SHOW_ALL")
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
        cam = context.scene.camera
        if cam is None or not _scene_camera_view(context):
            return False
        for ob in context.view_layer.objects:
            ob.select_set(ob == cam)
        context.view_layer.objects.active = cam
    elif key in ("LAYOUT_SINGLE", "LAYOUT_FOUR"):
        if bool(space.region_quadviews) != (key == "LAYOUT_FOUR"):
            area = context.area
            with context.temp_override(area=area, region=main_region(area)):
                bpy.ops.screen.region_quadview()
    else:
        return False
    return True


class MAYAKIT_OT_panel_set(bpy.types.Operator):
    """Maya panel menu item for this view"""
    bl_idname = "maya_kit.panel_set"
    bl_label = "Panel Menu Item"
    bl_options = {'INTERNAL', 'UNDO'}

    key: EnumProperty(items=[(k, k.title(), "") for k in
                             dict.fromkeys(SET_KEYS + ["SHOW_ALL", "SHOW_NONE"])])

    @classmethod
    def poll(cls, context):
        return _space(context) is not None

    def execute(self, context):
        if not apply(context, self.key):
            if self.key == "SELECT_CAMERA":
                self.report({'WARNING'}, "This view is not looking through a camera")
            return {'CANCELLED'}
        return {'FINISHED'}


class MAYAKIT_OT_panel_run(bpy.types.Operator):
    """Run a Blender operator in this view (Maya panel menu item)"""
    bl_idname = "maya_kit.panel_run"
    bl_label = "Run in This View"
    bl_options = {'INTERNAL'}

    op: StringProperty(options={'SKIP_SAVE'})
    props: StringProperty(default="{}", options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, props):
        try:
            mod, name = props.op.split(".")
            return getattr(getattr(bpy.ops, mod), name).get_rna_type().description
        except (ValueError, AttributeError, KeyError):
            return ""

    def execute(self, context):
        area = context.area
        if area is None or area.type != 'VIEW_3D':
            return {'CANCELLED'}
        mod, name = self.op.split(".")
        try:
            with context.temp_override(window=context.window, area=area, region=main_region(area)):
                getattr(getattr(bpy.ops, mod), name)('INVOKE_DEFAULT', **json.loads(self.props))
        except RuntimeError as ex:  # poll failed etc.
            self.report({'WARNING'}, str(ex).strip())
            return {'CANCELLED'}
        return {'FINISHED'}


# --- drawing --------------------------------------------------------------------------

def draw_rows(layout, context, rows):
    space = _space(context)
    for row in rows:
        kind = row[0]
        if kind == "sep":
            if row[1]:
                layout.separator(type='LINE')
                layout.label(text=row[1])
            else:
                layout.separator()
        elif kind == "grey":
            layout.operator(GREY_OP, text=row[1]).item = f"Panel menu/{row[1]}"
        elif kind == "prop":
            _k, owner, prop, label = row
            if space is not None:
                layout.prop(_owner(space, context, owner), prop, text=label)
        elif kind == "set":
            _k, key, label = row
            if key == "RENDER_ENGINE":
                label = context.engine.replace("BLENDER_", "").replace("_NEXT", "").title()
            on = state(context, key)
            if on is None:
                icon = 'NONE'
            elif key in RADIO:
                icon = 'RADIOBUT_ON' if on else 'RADIOBUT_OFF'
            else:
                icon = 'CHECKBOX_HLT' if on else 'CHECKBOX_DEHLT'
            layout.operator(MAYAKIT_OT_panel_set.bl_idname, text=label, icon=icon).key = key
        elif kind == "run":
            _k, label, op, props = row
            p = layout.operator(MAYAKIT_OT_panel_run.bl_idname, text=label)
            p.op, p.props = op, json.dumps(props)
        elif kind == "menu":
            layout.menu(row[2], text=row[1])


def _menu(idname, label, rows, doc):
    def draw(self, context):
        draw_rows(self.layout, context, rows)
    return type(idname, (bpy.types.Menu,), {"bl_idname": idname, "bl_label": label, "__doc__": doc,
                                            "draw": draw})


def _cameras(context, ortho):
    return [ob for ob in context.scene.objects
            if ob.type == 'CAMERA' and (ob.data.type == 'ORTHO') == ortho]


class MAYAKIT_OT_panel_look_through(bpy.types.Operator):
    """Look through this camera in this view"""
    bl_idname = "maya_kit.panel_look_through"
    bl_label = "Look Through Camera"
    bl_options = {'INTERNAL'}

    camera: StringProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        ob = context.scene.objects.get(self.camera)
        area = context.area
        if ob is None or area is None or area.type != 'VIEW_3D':
            return {'CANCELLED'}
        space = area.spaces.active
        space.camera = ob
        space.use_local_camera = ob != context.scene.camera
        space.region_3d.view_perspective = 'CAMERA'
        return {'FINISHED'}


def _draw_camera_list(layout, context, ortho):
    for ob in _cameras(context, ortho):
        layout.operator(MAYAKIT_OT_panel_look_through.bl_idname, text=ob.name,
                        icon='OUTLINER_OB_CAMERA').camera = ob.name


class MAYAKIT_MT_panel_perspective(bpy.types.Menu):
    """Maya Panels > Perspective: the persp view and perspective cameras"""
    bl_idname = "MAYAKIT_MT_panel_perspective"
    bl_label = "Perspective"

    def draw(self, context):
        draw_rows(self.layout, context, [_view("persp", 'PERSP')])
        _draw_camera_list(self.layout, context, False)


class MAYAKIT_MT_panel_orthographic(bpy.types.Menu):
    """Maya Panels > Orthographic: top, front, side and orthographic cameras"""
    bl_idname = "MAYAKIT_MT_panel_orthographic"
    bl_label = "Orthographic"

    def draw(self, context):
        draw_rows(self.layout, context, [_view("top", 'TOP'), _view("front", 'FRONT'), _view("side", 'RIGHT')])
        _draw_camera_list(self.layout, context, True)


class MAYAKIT_MT_panel_panel(bpy.types.Menu):
    """Maya Panels > Panel: turn this pane into another editor"""
    bl_idname = "MAYAKIT_MT_panel_panel"
    bl_label = "Panel"

    def draw(self, context):
        for label, ui_type in PANEL_TYPES:
            self.layout.operator("maya_kit.hb_pane", text=label).ui_type = ui_type


class MAYAKIT_MT_panel_blender(bpy.types.Menu):
    """Blender's own 3D View menus (View, Select, Add, Object ...)"""
    bl_idname = "MAYAKIT_MT_panel_blender"
    bl_label = "Blender"

    def draw(self, context):
        bpy.types.VIEW3D_MT_editor_menus.draw(self, context)


def draw_bar(layout, context):
    for label, idname in BAR:
        layout.menu(idname, text=label)
    layout.menu(MAYAKIT_MT_panel_blender.bl_idname, text="Blender")


class MAYAKIT_MT_panel_bar(bpy.types.Menu):
    """The Maya panel menus folded into one menu (header menus collapsed)"""
    bl_idname = "MAYAKIT_MT_panel_bar"
    bl_label = "Panel Menus"

    def draw(self, context):
        draw_bar(self.layout, context)


_generated = [
    _menu("MAYAKIT_MT_panel_view", "View", VIEW, "Maya panel View menu"),
    _menu("MAYAKIT_MT_panel_view_axis", "View Along Axis", VIEW_AXIS, "Look along a world axis"),
    _menu("MAYAKIT_MT_panel_camera_tools", "Camera Tools", CAMERA_TOOLS, "Maya camera tools"),
    _menu("MAYAKIT_MT_panel_shading", "Shading", SHADING, "Maya panel Shading menu"),
    _menu("MAYAKIT_MT_panel_lighting", "Lighting", LIGHTING, "Maya panel Lighting menu"),
    _menu("MAYAKIT_MT_panel_show", "Show", SHOW, "Maya panel Show menu"),
    _menu("MAYAKIT_MT_panel_isolate", "Isolate Select", ISOLATE, "Maya Isolate Select"),
    _menu("MAYAKIT_MT_panel_renderer", "Renderer", RENDERER, "Maya panel Renderer menu"),
    _menu("MAYAKIT_MT_panel_panels", "Panels", PANELS, "Maya panel Panels menu"),
    _menu("MAYAKIT_MT_panel_layouts", "Layouts", LAYOUTS, "Maya panel layouts"),
]

classes = (MAYAKIT_OT_panel_set, MAYAKIT_OT_panel_run, MAYAKIT_OT_panel_look_through,
           MAYAKIT_MT_panel_perspective, MAYAKIT_MT_panel_orthographic, MAYAKIT_MT_panel_panel,
           MAYAKIT_MT_panel_blender, MAYAKIT_MT_panel_bar, *_generated)


# --- header patch -----------------------------------------------------------------------

def _enabled(context):
    from .. import preferences
    try:
        return preferences.get(context).maya_panel_menus
    except KeyError:
        return False


def draw_collapsible(cls, context, layout):
    """Replaces Menu.draw_collapsible for VIEW3D_MT_editor_menus (bpy_types.py:1292-1299)."""
    if not _enabled(context):
        return _ORIG(cls, context, layout)
    if context.area.show_menus:
        draw_bar(layout.row(align=True), context)
    else:
        layout.menu(MAYAKIT_MT_panel_bar.bl_idname, text="", icon='COLLAPSEMENU')


def _ORIG(cls, context, layout):
    return bpy.types.Menu.draw_collapsible.__func__(cls, context, layout)


def patch_header():
    bpy.types.VIEW3D_MT_editor_menus.draw_collapsible = classmethod(draw_collapsible)


def unpatch_header():
    cls = bpy.types.VIEW3D_MT_editor_menus
    if "draw_collapsible" in cls.__dict__:
        del cls.draw_collapsible


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    patch_header()


def unregister():
    unpatch_header()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
