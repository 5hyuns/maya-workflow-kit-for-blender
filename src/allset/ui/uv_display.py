# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya UV Editor display keys and Move UV Shell.

Maya 2022 UV Editor hotkeys ( context polyTexturePlacementPanel,
Maya-536; View menu ):

- 4 Wireframe / 5 Shaded (Display Mode radio) -> ``SpaceUVEditor.show_faces`` off / on (Shaded also sets
  ``uv_face_opacity`` 1). ``uv_face_opacity`` 0 alone still draws grey face fills (GUI shot, step 155): no wireframe.
- 6 UVEditor_ToggleUVTextureImage -> ``SpaceImageEditor.image`` = None / back (Blender has no "hide the image"
  flag; the image is remembered per editor, else the active material's image texture is shown).
- 8 UVEditor_ToggleUVShellBorder = ``polyOptions -displayShellBorder`` (hotkeys_default.json:8194): shell
  borders drawn in colour, width setting displayPolyBorderEdgeSize[1] = 3 px (
  options140/_options140.json:627). Colour not checked .
- 9 UVEditor_ToggleTextureBorder = ``ToggleTextureBorderDisplay`` (hotkeys_default.json:8217): Maya's "texture
  borders" are the UV shell border edges drawn thick (Select > Texture Borders selects the same edges; step 79
  cut_sew.py calls them that too), on in the Maya factory View menu (checked in the capture). Drawn 3 px in the
  theme's UV wire colour, i.e. the same edge, thicker.
- Ctrl+1 UVEditor_ToggleUVIsolateViewSelected (textureEditorToggleIsolateSelect) -> ``allset.uv_isolate``.

Shell borders follow the step-66 island rule (operators/uv_tools.islands: faces join where their UVs match at both
ends of an edge): an edge is a border on a face's side when no other shown face shares the same UVs across it.
They are drawn by an Image Editor WINDOW POST_PIXEL handler in UV space mapped through ``View2D.view_to_region``;
segments are cached per object and dropped on any depsgraph update of a mesh / object (like step 79).
"""

import bmesh
import bpy
import gpu
import numpy as np
from bpy.props import BoolProperty, EnumProperty
from gpu_extras.batch import batch_for_shader

from .. import results
from .. import compat
from ..operators import uv_tools

BORDER_PX = 3.0                        # setting displayPolyBorderEdgeSize (factory 3.0, 3.0)
SHELL_RGB = (0.25, 0.75, 1.0)          # Toggle Shell Borders colour : Maya's colour was not checked
MOVE_TOOL = "builtin.move"

MODES = (("WIREFRAME", "Wireframe", "Maya 4: UVs as wireframe (no shaded faces)"),
         ("SHADED", "Shaded", "Maya 5: UV faces shaded"),
         ("IMAGE", "Texture Image", "Maya 6: show / hide the texture image"),
         ("SHELL_BORDERS", "Shell Borders", "Maya 8: UV shell borders in colour"),
         ("TEXTURE_BORDERS", "Texture Borders", "Maya 9: UV shell borders drawn thick"))


# --- pure helpers (tests/test_step155_uv_display.py) -----------------------------------------------------

def shown_faces(bm, synced):
    """Faces the UV Editor draws: every unhidden face with UV Sync Selection, else only the selected ones."""
    return [f for f in bm.faces if not f.hide and (synced or f.select)]


def border_segments(bm, uv, faces):
    """UV segments ((u0, v0), (u1, v1)) of every shell border edge side among ``faces``."""
    shown = set(faces)
    out = []
    for f in faces:
        for loop in f.loops:
            e = loop.edge
            joined = False
            for g in e.link_faces:
                if g is f or g not in shown:
                    continue
                if all(uv_tools._same(uv_tools._uv_at(f, v, uv), uv_tools._uv_at(g, v, uv)) for v in e.verts):
                    joined = True
                    break
            if not joined:
                a, b = loop[uv].uv, loop.link_loop_next[uv].uv
                out.append(((a.x, a.y), (b.x, b.y)))
    return out


def to_region(points, p0, p1):
    """UV points (N x 2) to region pixels, given where UV (0, 0) and (1, 1) land."""
    pts = np.asarray(points, dtype=np.float32).reshape(-1, 2)
    scale = np.array((p1[0] - p0[0], p1[1] - p0[1]), dtype=np.float32)
    return pts * scale + np.array(p0, dtype=np.float32)


# --- drawing ---------------------------------------------------------------------------------------------

_cache = {}          # object pointer -> float32 array (2N x 2) of UV line points
_handle = []


def _edit_meshes(context):
    obs = getattr(context, "objects_in_mode_unique_data", None) or ()
    return [o for o in obs if o.type == 'MESH']


def segments_of(ob, synced):
    key = (ob.as_pointer(), synced)
    pts = _cache.get(key)
    if pts is None:
        bm = bmesh.from_edit_mesh(ob.data)
        uv = bm.loops.layers.uv.active
        segs = border_segments(bm, uv, shown_faces(bm, synced)) if uv is not None else []
        pts = np.array([p for s in segs for p in s], dtype=np.float32).reshape(-1, 2)
        _cache[key] = pts
    return pts


def _draw():
    context = bpy.context
    wm = context.window_manager
    if not (wm.allset_uv_shell_borders or wm.allset_uv_texture_borders):
        return
    space = context.space_data
    region = context.region
    try:
        if space is None or space.mode != 'UV' or context.mode != 'EDIT_MESH' or not space.uv_editor.show_uv:
            return
        v2d = region.view2d
        p0 = v2d.view_to_region(0.0, 0.0, clip=False)
        p1 = v2d.view_to_region(1.0, 1.0, clip=False)
        if p0[0] == p1[0] or p0[1] == p1[1]:
            return
        synced = context.scene.tool_settings.use_uv_select_sync
        pts = [segments_of(ob, synced) for ob in _edit_meshes(context)]
        pts = [p for p in pts if len(p)]
        if not pts:
            return
        px = to_region(np.concatenate(pts), p0, p1)
        scale = context.preferences.system.ui_scale or 1.0
        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        if wm.allset_uv_shell_borders:
            rgb = SHELL_RGB
        else:
            rgb = tuple(context.preferences.themes[0].image_editor.wire_edit)[:3]
        gpu.state.blend_set('ALPHA')
        shader.uniform_float("viewportSize", (region.width, region.height))
        shader.uniform_float("lineWidth", BORDER_PX * scale)
        shader.uniform_float("color", (*rgb, 1.0))
        batch_for_shader(shader, 'LINES', {"pos": px.tolist()}).draw(shader)
        gpu.state.blend_set('NONE')
    except (ReferenceError, AttributeError, ValueError):
        _cache.clear()


@bpy.app.handlers.persistent
def _invalidate(_scene=None, depsgraph=None):
    if depsgraph is not None and not any(isinstance(u.id, (bpy.types.Mesh, bpy.types.Object))
                                         for u in depsgraph.updates):
        return
    _cache.clear()


def redraw_uv_editors():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.tag_redraw()


def _redraw(_self, _context):
    redraw_uv_editors()


# --- texture image (6) -----------------------------------------------------------------------------------

_hidden_image = {}   # SpaceImageEditor pointer -> image name it showed before 6 hid it


def material_image(ob):
    """The image of the active material's active (else first) Image Texture node, or None."""
    mat = ob.active_material if ob is not None else None
    tree = mat.node_tree if mat is not None and mat.use_nodes else None
    if tree is None:
        return None
    node = tree.nodes.active
    if node is not None and node.type == 'TEX_IMAGE' and node.image is not None:
        return node.image
    return next((n.image for n in tree.nodes if n.type == 'TEX_IMAGE' and n.image is not None), None)


def toggle_image(space, ob):
    """Maya 6: hide the shown image (remembered), or show the remembered / material image. Returns the shown one."""
    key = space.as_pointer()
    if space.image is not None:
        _hidden_image[key] = space.image.name
        space.image = None
        return None
    img = bpy.data.images.get(_hidden_image.pop(key, "") or "") or material_image(ob)
    if img is not None:
        space.image = img
    return img


# --- operators -------------------------------------------------------------------------------------------

def _in_uv_editor(context):
    space = context.space_data
    return space is not None and space.type == 'IMAGE_EDITOR' and space.mode == 'UV'


class ALLSET_OT_uv_display(bpy.types.Operator):
    """Maya UV Editor display keys: 4 Wireframe, 5 Shaded, 6 texture image, 8 shell borders, 9 texture borders"""
    bl_idname = "allset.uv_display"
    bl_label = "UV Editor Display"
    bl_options = set()          # display only: no undo step, no redo panel

    mode: EnumProperty(items=MODES, name="Mode", default='SHELL_BORDERS', options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return _in_uv_editor(context)

    def execute(self, context):
        space = context.space_data
        wm = context.window_manager
        if self.mode == 'WIREFRAME':
            space.uv_editor.show_faces = False
        elif self.mode == 'SHADED':
            space.uv_editor.show_faces = True
            space.uv_editor.uv_face_opacity = 1.0
        elif self.mode == 'IMAGE':
            had = space.image is not None
            if toggle_image(space, context.view_layer.objects.active) is None and not had:
                results.result(self, "No texture image to show")
        elif self.mode == 'SHELL_BORDERS':
            wm.allset_uv_shell_borders = not wm.allset_uv_shell_borders
        else:
            wm.allset_uv_texture_borders = not wm.allset_uv_texture_borders
        redraw_uv_editors()
        return {'FINISHED'}


# --- isolate (Ctrl+1) ------------------------------------------------------------------------------------

_isolated = {}       # object name -> (synced, faces it hid / deselected, (vert, edge, face) selection before)


def _picked_faces(bm, uv, synced):
    if synced:
        return [f for f in bm.faces if f.select and not f.hide]
    shown = [f for f in bm.faces if f.select and not f.hide]
    full = [f for f in shown if all(compat.uv_vert_selected(l, uv) for l in f.loops)]
    return full or [f for f in shown if any(compat.uv_vert_selected(l, uv) for l in f.loops)]


def isolate(ob, synced):
    """Show only the faces of the selected UVs: with UV Sync Selection the others are hidden (Blender's hide, so
    the 3D View hides them too), without it they are deselected (the UV Editor then doesn't draw them).
    Returns how many faces stay shown (0 = nothing selected, nothing changed)."""
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    if uv is None:
        return 0
    keep = set(_picked_faces(bm, uv, synced))
    if not keep:
        return 0
    before = tuple([i for i, el in enumerate(seq) if el.select] for seq in (bm.verts, bm.edges, bm.faces))
    gone = [f.index for f in bm.faces if not f.hide and f not in keep and (synced or f.select)]
    bm.faces.ensure_lookup_table()
    for i in gone:
        if synced:
            bm.faces[i].hide_set(True)
        else:
            bm.faces[i].select_set(False)
    _restore_selection(bm, before)
    if not synced:
        for i in gone:
            bm.faces[i].select = False
    _isolated[ob.name] = (synced, gone, before, len(bm.faces))
    bmesh.update_edit_mesh(ob.data)
    return len(keep)


def _restore_selection(bm, before):
    for seq, idx in zip((bm.verts, bm.edges, bm.faces), before):
        on = set(idx)
        for i, el in enumerate(seq):
            el.select = i in on and not el.hide


def unisolate(ob):
    rec = _isolated.pop(ob.name, None)
    if rec is None:
        return False
    synced, gone, before, count = rec
    bm = bmesh.from_edit_mesh(ob.data)
    if len(bm.faces) != count:
        return False
    bm.faces.ensure_lookup_table()
    if synced:
        for i in gone:
            bm.faces[i].hide_set(False)
    _restore_selection(bm, before)
    bmesh.update_edit_mesh(ob.data)
    return True


class ALLSET_OT_uv_isolate(bpy.types.Operator):
    """Maya Ctrl+1 in the UV Editor: show only the selected UVs' faces; again = show all"""
    bl_idname = "allset.uv_isolate"
    bl_label = "Isolate Select (UV)"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        obs = _edit_meshes(context)
        wm = context.window_manager
        if any(ob.name in _isolated for ob in obs):
            for ob in obs:
                unisolate(ob)
            wm.allset_uv_isolate = False
        else:
            synced = context.scene.tool_settings.use_uv_select_sync
            if not sum(isolate(ob, synced) for ob in obs):
                self.report({'WARNING'}, "Select UVs to isolate")
                return {'CANCELLED'}
            wm.allset_uv_isolate = True
        _cache.clear()
        redraw_uv_editors()
        return {'FINISHED'}


# --- Move UV Shell (Tools menu) ------------------------------------------------------------------------

_shell_tool = {"on": False}


def _uv_tool_ids():
    out = []
    for win in bpy.context.window_manager.windows:
        tool = win.workspace.tools.from_space_image_mode('UV', create=False)
        out.append(tool.idname if tool is not None else "")
    return out


def _watch_shell_tool():
    """While Move UV Shell is on: another UV tool chosen -> back to UV (not shell) selection."""
    if not _shell_tool["on"]:
        return None
    try:
        ids = _uv_tool_ids()
    except (ReferenceError, AttributeError):
        return 0.25
    if ids and MOVE_TOOL not in ids:
        _shell_tool["on"] = False
        ts = bpy.context.scene.tool_settings
        if compat.uv_island_mode(ts):
            compat.set_uv_island_mode(ts, False)
        return None
    return 0.25


class ALLSET_OT_uv_move_shell(bpy.types.Operator):
    """Maya Tools > Move UV Shell: a click on a UV picks its whole shell, a drag moves it
    (Blender: UV shell selection + the Move tool; another UV tool goes back to UV selection)"""
    bl_idname = "allset.uv_move_shell"
    bl_label = "Move UV Shell"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        uv_tools.set_component(context, 'SHELL')
        if not bpy.app.background:
            bpy.ops.wm.tool_set_by_id(name=MOVE_TOOL, space_type='IMAGE_EDITOR')
            _shell_tool["on"] = True
            if not bpy.app.timers.is_registered(_watch_shell_tool):
                bpy.app.timers.register(_watch_shell_tool, first_interval=0.25)
        return {'FINISHED'}


@bpy.app.handlers.persistent
def _load_pre(*_args):
    _isolated.clear()
    _hidden_image.clear()
    _cache.clear()
    _shell_tool["on"] = False
    try:
        bpy.context.window_manager.allset_uv_isolate = False
    except (AttributeError, RuntimeError):
        pass


classes = (ALLSET_OT_uv_display, ALLSET_OT_uv_isolate, ALLSET_OT_uv_move_shell)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.types.WindowManager
    wm.allset_uv_shell_borders = BoolProperty(name="Shell Borders", default=False, update=_redraw,
                                              description="Maya UV Editor: UV shell borders in colour (8)")
    wm.allset_uv_texture_borders = BoolProperty(name="Texture Borders", default=True, update=_redraw,
                                                description="Maya UV Editor: UV shell borders drawn thick (9)")
    wm.allset_uv_isolate = BoolProperty(name="Isolate Select", default=False,
                                        description="Maya UV Editor: only the selected UVs' faces shown (Ctrl+1)")
    _handle.append(bpy.types.SpaceImageEditor.draw_handler_add(_draw, (), 'WINDOW', 'POST_PIXEL'))
    bpy.app.handlers.depsgraph_update_post.append(_invalidate)
    bpy.app.handlers.load_pre.append(_load_pre)


def unregister():
    if bpy.app.timers.is_registered(_watch_shell_tool):
        bpy.app.timers.unregister(_watch_shell_tool)
    _shell_tool["on"] = False
    for h, lst in ((_invalidate, bpy.app.handlers.depsgraph_update_post), (_load_pre, bpy.app.handlers.load_pre)):
        if h in lst:
            lst.remove(h)
    while _handle:
        bpy.types.SpaceImageEditor.draw_handler_remove(_handle.pop(), 'WINDOW')
    wm = bpy.types.WindowManager
    for name in ("allset_uv_isolate", "allset_uv_texture_borders", "allset_uv_shell_borders"):
        if hasattr(wm, name):
            delattr(wm, name)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    _cache.clear()
    _isolated.clear()
    _hidden_image.clear()
