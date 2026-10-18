# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Modify > Align: Snap Align Objects, Snap Together Tool, Make Live, Match
Transformations (docs/steps/step_59.md 「계획」 4).

Measured in Maya 2022 (research/maya/workflows/pivot_snap.md):

- S9 Point to Point: the object owning the first point moves (no rotation) so that point
  lands on the last one.
- S10/S11 2 / 3 Points to 2 / 3 Points: move + rotate so the points line up (first on first,
  the rest give the direction / plane).
- S11 Align Objects (factory options): world X only, mid, to the average.
- S12 Snap Together Tool: click a surface point on the object to move, then a point on the
  target: the object moves there and turns so the two normals face each other.
- S13 Make Live: a live surface the moves snap onto; "No Live Surface" in the Status Line.

Points: in object mode the pivots (Blender origins) of the selected objects, the active
one (Maya's last selected) being the target; in mesh edit mode each mesh's selected
vertices in selection order (``select_history``), the active object's being the target.
"""

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, PointerProperty
from bpy_extras import view3d_utils
from mathutils import Matrix, Vector

EPS = 1e-9


# --- maths (bpy-free apart from mathutils) -------------------------------------------------------

def _frame(points):
    """Orthonormal frame (3x3, columns) of 2 or 3 points: X along p0->p1, Z = plane normal."""
    x = points[1] - points[0]
    if x.length < EPS:
        return None
    x = x.normalized()
    if len(points) > 2:
        z = x.cross(points[2] - points[0])
        if z.length < EPS:
            z = None
        else:
            z = z.normalized()
    else:
        z = None
    if z is None:
        helper = Vector((0, 0, 1)) if abs(x.z) < 0.9 else Vector((0, 1, 0))
        z = x.cross(helper).cross(x).normalized()
        z = -z if z.dot(helper) < 0 else z
    y = z.cross(x).normalized()
    return Matrix((x, y, z)).transposed()


def points_transform(src, dst):
    """World matrix that takes ``src`` points onto ``dst`` (1: move, 2: move + aim, 3: + plane)."""
    n = min(len(src), len(dst))
    if n == 0:
        return Matrix.Identity(4)
    if n == 1:
        return Matrix.Translation(dst[0] - src[0])
    fs, fd = _frame(src[:n]), _frame(dst[:n])
    if fs is None or fd is None:
        return Matrix.Translation(dst[0] - src[0])
    if n == 2:
        # 2 points: only turn the p0->p1 direction onto the target direction (shortest arc)
        a = (src[1] - src[0]).normalized()
        b = (dst[1] - dst[0]).normalized()
        rot = a.rotation_difference(b).to_matrix()
    else:
        rot = fd @ fs.transposed()
    m = rot.to_4x4()
    return Matrix.Translation(dst[0]) @ m @ Matrix.Translation(-src[0])


def bbox_world(ob):
    corners = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector(tuple(min(c[i] for c in corners) for i in range(3)))
    hi = Vector(tuple(max(c[i] for c in corners) for i in range(3)))
    return lo, hi


# --- selections ---------------------------------------------------------------------------------

def _ordered_verts(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    hist = [e for e in bm.select_history if isinstance(e, bmesh.types.BMVert)]
    rest = [v for v in bm.verts if v.select and v not in hist]
    return [ob.matrix_world @ v.co for v in hist + rest]


def point_sets(context):
    """(movers [(object, points)], target points) or None."""
    active = context.view_layer.objects.active
    if context.mode == 'EDIT_MESH':
        obs = [ob for ob in context.objects_in_mode_unique_data if ob.type == 'MESH']
        target = [ob for ob in obs if ob == active]
        movers = [ob for ob in obs if ob != active]
        if not target or not movers:
            return None
        return [(ob, _ordered_verts(ob)) for ob in movers], _ordered_verts(target[0])
    sel = [ob for ob in context.selected_objects]
    if active is None or active not in sel or len(sel) < 2:
        return None
    return ([(ob, [ob.matrix_world.translation.copy()]) for ob in sel if ob != active],
            [active.matrix_world.translation.copy()])


def snap_points(context, count):
    """Snap Align Objects > Point to Point / 2 Points / 3 Points. Returns the moved count."""
    sets = point_sets(context)
    if sets is None:
        return 0
    movers, target = sets
    done = 0
    for ob, pts in movers:
        n = min(count, len(pts), len(target))
        if n == 0:
            continue
        m = points_transform(pts[:n], target[:n])
        if ob.parent is None or ob.parent not in [o for o, _p in movers]:
            ob.matrix_world = m @ ob.matrix_world
            done += 1
    return done


def align_objects(context, axes=(True, False, False), mode='MID'):
    """Snap Align Objects > Align Objects with Maya's factory options (S11): along world
    ``axes``, the bounding boxes' min / mid / max lined up at their average."""
    obs = list(context.selected_objects)
    if len(obs) < 2:
        return 0
    boxes = {ob: bbox_world(ob) for ob in obs}

    def key(bb, i):
        lo, hi = bb
        return lo[i] if mode == 'MIN' else hi[i] if mode == 'MAX' else (lo[i] + hi[i]) / 2

    for i, on in enumerate(axes):
        if not on:
            continue
        avg = sum(key(bb, i) for bb in boxes.values()) / len(obs)
        for ob, bb in boxes.items():
            d = Vector((0, 0, 0))
            d[i] = avg - key(bb, i)
            ob.matrix_world = Matrix.Translation(d) @ ob.matrix_world
    return len(obs)


# --- Match Transformations ------------------------------------------------------------------------

def match_transform(context, translate=True, rotate=True, scale=True):
    lead = context.view_layer.objects.active
    others = [ob for ob in context.selected_objects if ob is not lead]
    if lead is None or not others:
        return 0
    lt, lr, ls = lead.matrix_world.decompose()
    for ob in others:
        t, r, s = ob.matrix_world.decompose()
        ob.matrix_world = Matrix.LocRotScale(lt if translate else t, lr if rotate else r, ls if scale else s)
    return len(others)


class _ObjOp:
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode in ('OBJECT', 'EDIT_MESH')


class MAYAKIT_OT_snap_points(_ObjOp, bpy.types.Operator):
    """Move (and turn) the first selected object so its points land on the last selected
    object's points (Maya Modify > Snap Align Objects > Point to Point / 2 / 3 Points)"""
    bl_idname = "maya_kit.snap_points"
    bl_label = "Snap Points"

    count: IntProperty(name="Points", default=1, min=1, max=3)

    @classmethod
    def description(cls, context, props):
        return {1: "Point to Point: move the object so its point lands on the target point",
                2: "2 Points to 2 Points: move and turn so two points line up",
                3: "3 Points to 3 Points: move and turn so three points line up"}[props.count]

    def execute(self, context):
        n = snap_points(context, self.count)
        if not n:
            self.report({'WARNING'}, "Select points on the object to move, then on the target (last)")
            return {'CANCELLED'}
        return {'FINISHED'}


class MAYAKIT_OT_align_objects(bpy.types.Operator):
    """Line the selected objects up along world X at the middle of their bounding boxes
    (Maya Modify > Snap Align Objects > Align Objects, factory options)"""
    bl_idname = "maya_kit.align_objects"
    bl_label = "Align Objects"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(name="Align Mode", items=(('MIN', "Min", ""), ('MID', "Mid", ""), ('MAX', "Max", "")),
                       default='MID')
    axis_x: BoolProperty(name="World X", default=True)
    axis_y: BoolProperty(name="World Y", default=False)
    axis_z: BoolProperty(name="World Z", default=False)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        if not align_objects(context, (self.axis_x, self.axis_y, self.axis_z), self.mode):
            self.report({'WARNING'}, "Select two or more objects")
            return {'CANCELLED'}
        return {'FINISHED'}


class MAYAKIT_OT_match_transform(bpy.types.Operator):
    """Match the transforms of the selected objects to the last selected one
    (Maya Modify > Match Transformations)"""
    bl_idname = "maya_kit.match_transform"
    bl_label = "Match Transformations"
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(items=(('ALL', "All Transforms", ""), ('TRANSLATE', "Translation", ""),
                              ('ROTATE', "Rotation", ""), ('SCALE', "Scaling", "")), default='ALL')

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        k = self.kind
        n = match_transform(context, k in ('ALL', 'TRANSLATE'), k in ('ALL', 'ROTATE'), k in ('ALL', 'SCALE'))
        if not n:
            self.report({'WARNING'}, "Select the objects, then the target last")
            return {'CANCELLED'}
        return {'FINISHED'}


# --- Make Live (S13) ------------------------------------------------------------------------------

def make_live(context, ob):
    ts = context.scene.tool_settings
    context.scene.maya_kit_live = ob
    elements = set(ts.snap_elements)
    if ob is not None:
        ts.snap_elements = elements | {'FACE_PROJECT'}
        ts.use_snap = True
        ts.use_snap_align_rotation = False
    else:
        elements.discard('FACE_PROJECT')
        if elements:
            ts.snap_elements = elements
        if not elements or elements == {'INCREMENT'}:
            ts.use_snap = False
    for area in context.screen.areas if context.screen else ():
        area.tag_redraw()


class MAYAKIT_OT_make_live(bpy.types.Operator):
    """Make the selected surface live: moves snap onto it. With nothing selected the live
    surface is cleared (Maya Modify > Make Live)"""
    bl_idname = "maya_kit.make_live"
    bl_label = "Make Live"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        ob = context.view_layer.objects.active
        if ob is not None and (not ob.select_get() or ob.type != 'MESH'):
            ob = None
        make_live(context, ob)
        self.report({'INFO'}, f"Live surface: {ob.name}" if ob else "No Live Surface")
        from ..ui import view_message
        # Maya statusLine.mel:1891-1900 (topCenter).
        view_message.show(context, f"{ob.name} is <hl>live</hl>." if ob else "Make Live is <hl>off</hl>.",
                          'TOP_CENTER')
        return {'FINISHED'}


# --- Snap Together Tool (S12) ------------------------------------------------------------------

def surface_hit(context, region, rv3d, coord):
    origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    depsgraph = context.evaluated_depsgraph_get()
    ok, loc, normal, _i, ob, _m = context.scene.ray_cast(depsgraph, origin, direction)
    if not ok:
        return None
    return ob.original if hasattr(ob, "original") else ob, loc, normal.normalized()


def snap_together_matrix(src_point, src_normal, dst_point, dst_normal, orient=True):
    """World matrix that puts ``src_point`` on ``dst_point`` with the normals facing each other."""
    if not orient:
        return Matrix.Translation(dst_point - src_point)
    rot = src_normal.rotation_difference(-dst_normal).to_matrix().to_4x4()
    return Matrix.Translation(dst_point) @ rot @ Matrix.Translation(-src_point)


class MAYAKIT_OT_snap_together(bpy.types.Operator):
    """Click a point on the object to move, then a point on the target: the object moves
    there and turns so the surfaces face each other (Maya Modify > Snap Together Tool)"""
    bl_idname = "maya_kit.snap_together"
    bl_label = "Snap Together Tool"
    bl_options = {'REGISTER', 'UNDO'}

    set_orientation: BoolProperty(name="Set Orientation", default=True)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def _view(self, context, event):
        for area in context.window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for region in area.regions:
                if (region.type == 'WINDOW' and region.x <= event.mouse_x < region.x + region.width
                        and region.y <= event.mouse_y < region.y + region.height):
                    return area, region, region.data
        return None, None, None

    def invoke(self, context, event):
        self._first = None
        context.window_manager.modal_handler_add(self)
        context.workspace.status_text_set("Snap Together Tool: click a point on the object to move "
                                          "(Esc / right-click: cancel)")
        return {'RUNNING_MODAL'}

    def _end(self, context):
        context.workspace.status_text_set(None)

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'} and event.value == 'PRESS':
            self._end(context)
            return {'CANCELLED'}
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            area, region, rv3d = self._view(context, event)
            if region is None or rv3d is None:
                return {'PASS_THROUGH'}
            coord = (event.mouse_x - region.x, event.mouse_y - region.y)
            hit = surface_hit(context, region, rv3d, coord)
            if hit is None:
                return {'RUNNING_MODAL'}
            if self._first is None:
                self._first = hit
                context.workspace.status_text_set(f"Snap Together Tool: now click the target point "
                                                  f"(moving {hit[0].name})")
                return {'RUNNING_MODAL'}
            ob, p0, n0 = self._first
            _ob1, p1, n1 = hit
            m = snap_together_matrix(p0, n0, p1, n1, self.set_orientation)
            ob.matrix_world = m @ ob.matrix_world
            self._end(context)
            return {'FINISHED'}
        return {'PASS_THROUGH'} if event.type.startswith(('WHEEL', 'MIDDLEMOUSE', 'MOUSEMOVE', 'TRACKPAD')) \
            or event.alt else {'RUNNING_MODAL'}


classes = (MAYAKIT_OT_snap_points, MAYAKIT_OT_align_objects, MAYAKIT_OT_match_transform,
           MAYAKIT_OT_make_live, MAYAKIT_OT_snap_together)


def register_props():
    bpy.types.Scene.maya_kit_live = PointerProperty(
        type=bpy.types.Object, name="Live Surface",
        description="Maya live surface: moves snap onto it (Modify > Make Live)")


def unregister_props():
    del bpy.types.Scene.maya_kit_live


# --- Step Snap (Move/Rotate/Scale tool option, S3) -----------------------------------------------

STEP_FLAGS = {'TRANSLATE': "use_snap_translate", 'ROTATE': "use_snap_rotate", 'RESIZE': "use_snap_scale"}
MAYA_ROTATE_STEP = 0.2617993877991494      # 15 degrees (manipRotateContext -snapValue, S3)


def step_snap_mode(ts, kind):
    """'OFF' / 'RELATIVE' / 'ABSOLUTE' for the tool ``kind`` (Maya Step Snap)."""
    if not (ts.use_snap and 'INCREMENT' in ts.snap_elements and getattr(ts, STEP_FLAGS[kind])):
        return 'OFF'
    return 'ABSOLUTE' if ts.use_snap_grid_absolute else 'RELATIVE'


def set_step_snap(ts, kind, mode):
    if mode == 'TOGGLE':
        mode = 'OFF' if step_snap_mode(ts, kind) != 'OFF' else 'RELATIVE'
    if mode == 'OFF':
        setattr(ts, STEP_FLAGS[kind], False)
        if not any(getattr(ts, f) for f in STEP_FLAGS.values()) or set(ts.snap_elements) == {'INCREMENT'}:
            elements = set(ts.snap_elements) - {'INCREMENT'}
            if elements:
                ts.snap_elements = elements
            else:
                ts.use_snap = False
        return 'OFF'
    ts.snap_elements = set(ts.snap_elements if ts.use_snap else ()) | {'INCREMENT'}
    ts.use_snap = True
    setattr(ts, STEP_FLAGS[kind], True)
    ts.use_snap_grid_absolute = mode == 'ABSOLUTE'
    if kind == 'ROTATE' and abs(ts.snap_angle_increment_3d - 0.0872664600610733) < 1e-6:
        ts.snap_angle_increment_3d = MAYA_ROTATE_STEP     # Blender's 5 degrees -> Maya's 15
    return mode


class MAYAKIT_OT_step_snap(bpy.types.Operator):
    """Maya Step Snap of the Move / Rotate / Scale tool: off, relative to the start, or to
    absolute steps (Discrete Move / Rotate / Snap Scale)"""
    bl_idname = "maya_kit.step_snap"
    bl_label = "Step Snap"
    bl_options = {'REGISTER', 'UNDO'}

    kind: EnumProperty(items=(('TRANSLATE', "Move", ""), ('ROTATE', "Rotate", ""), ('RESIZE', "Scale", "")))
    mode: EnumProperty(items=(('OFF', "Off", ""), ('RELATIVE', "Relative", ""), ('ABSOLUTE', "Absolute", ""),
                              ('TOGGLE', "Toggle", "")))

    def execute(self, context):
        got = set_step_snap(context.scene.tool_settings, self.kind, self.mode)
        self.report({'INFO'}, f"Step snap {got.lower()}")
        for area in context.screen.areas if context.screen else ():
            area.tag_redraw()
        return {'FINISHED'}


classes += (MAYAKIT_OT_step_snap,)
