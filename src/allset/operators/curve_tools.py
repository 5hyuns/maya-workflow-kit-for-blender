# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Curves / Surfaces commands Blender can build (step 109,  「계획」 3).

Results checked in Maya 2022  ( 「계획」, defaults of the commands):
- Planar on a closed curve -> ``planarTrimmedSurface1``; here a copy of the curve filled in 2D (Blender fills
  closed 2D curves; the curve is flattened onto its local XY plane).
- Loft of two or more curves -> ``loftedSurface1`` (NURBS in Maya, uniform off, degree 3); here a quad mesh
  through the curves, each resampled by arc length to the same point count.
- Extrude profile + path -> ``extrudedSurface1`` (tube: the profile swept along the path); here a copy of the
  path curve with the profile as its bevel object (Blender keeps it live, like Maya's history).
- Bevel Plus on a closed curve -> ``bevelPolygon1`` (a **mesh**, the curve kept): width 0.1, depth 0.1, extrude
  depth 0.25 in Maya units.
- Offset Curve -> ``offsetNurbsCurve1`` (distance 1), Sweep Mesh -> ``sweep1`` (an 8-sided tube mesh): see the
  constants below.
- Pencil Curve Tool / Add Points Tool: Blender's curve Draw tool on a new curve / extruding the curve's end
  points (curve edit mode).

Selection order: Maya lofts / extrudes in selection order; Blender objects have none, so the active (last
selected) object is last, the others keep their name order (delegated).
"""

import math

import bpy

from . import naming, units

# Maya Bevel Plus defaults (bevelPlus node, Maya): bevel width / depth 0.1, extrude depth 0.25.
BEVEL_WIDTH, BEVEL_DEPTH, EXTRUDE_DEPTH = 0.1, 0.1, 0.25


def _curves(context):
    """Selected curve objects, active last (module docstring: selection order)."""
    obs = sorted((ob for ob in context.selected_objects if ob.type == 'CURVE'), key=lambda o: o.name)
    act = context.active_object
    if act in obs:
        obs.remove(act)
        obs.append(act)
    return obs


def _link_new(context, ob, base, select=True):
    context.collection.objects.link(ob)
    naming.apply_maya_name(ob, base)
    if select:
        for o in context.selected_objects:
            o.select_set(False)
        ob.select_set(True)
        context.view_layer.objects.active = ob
    return ob


def _closed(curve):
    return any(sp.use_cyclic_u for sp in curve.splines)


def _object_mode(context):
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


# --- Planar -------------------------------------------------------------------------------------

def planar(context, ob):
    data = ob.data.copy()
    data.dimensions = '2D'
    data.fill_mode = 'BOTH'
    data.extrude = data.bevel_depth = 0.0
    data.bevel_mode = 'ROUND'
    data.bevel_object = None
    new = bpy.data.objects.new("planarTrimmedSurface", data)
    new.matrix_world = ob.matrix_world
    return _link_new(context, new, "planarTrimmedSurface", select=False)


class ALLSET_OT_surface_planar(bpy.types.Operator):
    """Fill the selected closed curves with a flat surface (Maya Surfaces > Planar)"""
    bl_idname = "allset.surface_planar"
    bl_label = "Planar"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _object_mode(context)
        obs = [ob for ob in _curves(context) if _closed(ob.data)]
        if not obs:
            self.report({'WARNING'}, "No valid items selected.  Select planar curves.")   # Maya's message
            return {'CANCELLED'}
        made = [planar(context, ob) for ob in obs]
        _select(context, made)
        return {'FINISHED'}


def _select(context, obs):
    for o in context.selected_objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    context.view_layer.objects.active = obs[-1]


# --- Loft ---------------------------------------------------------------------------------------

def curve_points(context, ob):
    """World-space points along the first spline of a curve object as drawn, and whether it is closed."""
    ev = ob.evaluated_get(context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    try:
        cos = [ob.matrix_world @ v.co for v in me.vertices]
        adj = {i: [] for i in range(len(cos))}
        for e in me.edges:
            a, b = e.vertices
            adj[a].append(b)
            adj[b].append(a)
    finally:
        ev.to_mesh_clear()
    if not cos:
        return [], False
    start = next((i for i, n in adj.items() if len(n) == 1), 0)
    path, prev, cur = [start], None, start
    while True:
        nxt = next((n for n in adj[cur] if n != prev and n not in path[-2:]), None)
        if nxt is None or nxt == start:
            break
        path.append(nxt)
        prev, cur = cur, nxt
    closed = len(adj[start]) == 2 and start in adj[path[-1]]
    return [cos[i] for i in path], closed


def resample(points, count, closed):
    """``count`` points spread evenly by arc length along a polyline."""
    pts = list(points) + ([points[0]] if closed else [])
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(seg) or 1.0
    steps = count if closed else count - 1
    out, i, acc = [], 0, 0.0
    for k in range(count):
        d = total * k / max(steps, 1)
        while i < len(seg) - 1 and acc + seg[i] < d:
            acc += seg[i]
            i += 1
        t = 0.0 if seg[i] == 0 else min(1.0, max(0.0, (d - acc) / seg[i]))
        out.append(pts[i].lerp(pts[i + 1], t))
    return out


def loft(context, obs):
    rows = [curve_points(context, ob) for ob in obs]
    rows = [r for r in rows if len(r[0]) >= 2]
    if len(rows) < 2:
        return None
    closed = all(c for _p, c in rows)
    n = max(len(p) for p, _c in rows)
    grid = [resample(p, n, closed) for p, _c in rows]
    verts = [tuple(v) for row in grid for v in row]
    faces = []
    span = n if closed else n - 1
    for r in range(len(grid) - 1):
        for i in range(span):
            j = (i + 1) % n
            faces.append((r * n + i, r * n + j, (r + 1) * n + j, (r + 1) * n + i))
    me = bpy.data.meshes.new("loftedSurfaceShape")
    me.from_pydata(verts, [], faces)
    me.shade_smooth()
    me.update()
    ob = _link_new(context, bpy.data.objects.new("loftedSurface", me), "loftedSurface")
    from . import material
    material.give_default(ob)
    return ob


class ALLSET_OT_loft(bpy.types.Operator):
    """Make a surface through the selected curves, in order (Maya Surfaces > Loft)"""
    bl_idname = "allset.loft"
    bl_label = "Loft"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _object_mode(context)
        ob = loft(context, _curves(context))
        if ob is None:
            self.report({'WARNING'}, "Invalid selection.  Need at least two curves.")   # Maya's message
            return {'CANCELLED'}
        return {'FINISHED'}


# --- Extrude ------------------------------------------------------------------------------------

def extrude(context, profile, path):
    data = path.data.copy()
    data.dimensions = '3D'
    data.bevel_mode = 'OBJECT'
    data.bevel_object = profile
    data.use_fill_caps = False
    new = bpy.data.objects.new("extrudedSurface", data)
    new.matrix_world = path.matrix_world
    return _link_new(context, new, "extrudedSurface")


class ALLSET_OT_surface_extrude(bpy.types.Operator):
    """Sweep the profile curve along the path curve (select the profile, then the path; Maya Surfaces >
    Extrude, tube style)"""
    bl_idname = "allset.surface_extrude"
    bl_label = "Extrude"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _object_mode(context)
        obs = _curves(context)
        if len(obs) < 2:
            self.report({'WARNING'}, "Select a profile curve, then the path curve.")
            return {'CANCELLED'}
        extrude(context, obs[0], obs[-1])
        return {'FINISHED'}


# --- Bevel Plus ---------------------------------------------------------------------------------

def bevel_plus(context, ob):
    """A mesh like Maya's bevelPolygon1: the closed curve filled, extruded and bevelled front and back."""
    k = units.maya_unit(context.scene)
    data = ob.data.copy()
    data.dimensions = '2D'
    data.fill_mode = 'BOTH'
    data.extrude = EXTRUDE_DEPTH * k / 2          # Blender extrudes both ways
    data.bevel_mode = 'ROUND'
    data.bevel_object = None
    data.bevel_depth = BEVEL_DEPTH * k
    data.bevel_resolution = 0                     # straight bevel
    data.offset = -BEVEL_WIDTH * k                # Maya bevels inside the curve
    tmp = bpy.data.objects.new("bevelPlusTmp", data)
    context.collection.objects.link(tmp)
    try:
        context.view_layer.update()
        me = bpy.data.meshes.new_from_object(tmp.evaluated_get(context.evaluated_depsgraph_get()))
    finally:
        bpy.data.objects.remove(tmp)
        bpy.data.curves.remove(data)
    new = bpy.data.objects.new("bevelPolygon", me)
    new.matrix_world = ob.matrix_world
    _link_new(context, new, "bevelPolygon", select=False)
    from . import material
    me.materials.clear()
    material.give_default(new)
    return new


class ALLSET_OT_bevel_plus(bpy.types.Operator):
    """Make a bevelled solid from the selected closed curves, the curves kept (Maya Surfaces > Bevel Plus)"""
    bl_idname = "allset.bevel_plus"
    bl_label = "Bevel Plus"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _object_mode(context)
        obs = [ob for ob in _curves(context) if _closed(ob.data)]
        if not obs:
            self.report({'WARNING'}, "Select closed curves.")
            return {'CANCELLED'}
        _select(context, [bevel_plus(context, ob) for ob in obs])
        return {'FINISHED'}


# --- Offset Curve -------------------------------------------------------------------------------
# Maya offsetCurve (Maya): distance 1, in the plane of the curve normal, towards normal x tangent (a line along
# +X with normal +Y moves to -Z; a radius-2 circle came out radius 1); result offsetNurbsCurve1, curve kept.
OFFSET_DISTANCE = 1.0
OFFSET_MIN_POINTS = 32


def offset_curve(context, ob, distance):
    from mathutils import Vector
    pts, closed = curve_points(context, ob)
    if len(pts) < 2:
        return None
    pts = resample(pts, max(OFFSET_MIN_POINTS, len(pts)), closed)
    normal = (ob.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
    out = []
    n = len(pts)
    for i, p in enumerate(pts):
        a = pts[(i - 1) % n] if closed or i > 0 else p
        b = pts[(i + 1) % n] if closed or i < n - 1 else p
        t = (b - a).normalized()
        out.append(p + normal.cross(t).normalized() * distance)
    data = bpy.data.curves.new("offsetNurbsCurveShape", 'CURVE')
    data.dimensions = '3D'
    sp = data.splines.new('POLY')
    sp.points.add(len(out) - 1)
    for p, q in zip(sp.points, out):
        p.co = (q.x, q.y, q.z, 1.0)
    sp.use_cyclic_u = closed
    return _link_new(context, bpy.data.objects.new("offsetNurbsCurve", data), "offsetNurbsCurve", select=False)


class ALLSET_OT_offset_curve(bpy.types.Operator):
    """Make a copy of the selected curves moved sideways in their plane (Maya Curves > Offset > Offset Curve)"""
    bl_idname = "allset.offset_curve"
    bl_label = "Offset Curve"
    bl_options = {'REGISTER', 'UNDO'}

    distance: bpy.props.FloatProperty(name="Offset Distance", default=OFFSET_DISTANCE,
                                      description="Maya units (offsetCurve distance)")

    def execute(self, context):
        _object_mode(context)
        k = units.maya_unit(context.scene)
        made = [o for o in (offset_curve(context, ob, self.distance * k) for ob in _curves(context)) if o]
        if not made:
            self.report({'WARNING'}, "Select curves to offset.")
            return {'CANCELLED'}
        _select(context, made)
        return {'FINISHED'}


# --- Sweep Mesh ---------------------------------------------------------------------------------
# Maya 2022 Sweep Mesh (sweep plug-in, Maya): a mesh sweep1 / sweepShape1 around the curve, default profile an
# 8-sided polygon of scale 1, 6 rings on a 4-CV curve (48 vertices, 40 faces); the curve is kept.
SWEEP_RADIUS, SWEEP_SIDES = 1.0, 8


def sweep_mesh(context, ob):
    k = units.maya_unit(context.scene)
    data = ob.data.copy()
    data.dimensions = '3D'
    data.fill_mode = 'FULL'
    data.bevel_mode = 'ROUND'
    data.bevel_object = None
    data.extrude = 0.0
    data.offset = 0.0
    data.bevel_depth = SWEEP_RADIUS * k
    data.bevel_resolution = SWEEP_SIDES // 2 - 2     # Blender: 2 * (resolution + 2) sides around (checked)
    data.use_fill_caps = True
    tmp = bpy.data.objects.new("sweepTmp", data)
    tmp.matrix_world = ob.matrix_world
    context.collection.objects.link(tmp)
    try:
        context.view_layer.update()
        me = bpy.data.meshes.new_from_object(tmp.evaluated_get(context.evaluated_depsgraph_get()))
    finally:
        bpy.data.objects.remove(tmp)
        bpy.data.curves.remove(data)
    me.materials.clear()
    new = bpy.data.objects.new("sweep", me)
    new.matrix_world = ob.matrix_world
    _link_new(context, new, "sweep", select=False)
    from . import material
    material.give_default(new)
    return new


class ALLSET_OT_sweep_mesh(bpy.types.Operator):
    """Make a tube mesh along the selected curves, the curves kept (Maya Create > Sweep Mesh)"""
    bl_idname = "allset.sweep_mesh"
    bl_label = "Sweep Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _object_mode(context)
        obs = _curves(context)
        if not obs:
            self.report({'WARNING'}, "Select curves to sweep.")
            return {'CANCELLED'}
        _select(context, [sweep_mesh(context, ob) for ob in obs])
        return {'FINISHED'}


# --- Pencil Curve Tool / Add Points Tool --------------------------------------------------------

class ALLSET_OT_pencil_curve(bpy.types.Operator):
    """Draw a new curve freehand (Maya Create > Curve Tools > Pencil Curve Tool: Blender's curve Draw tool)"""
    bl_idname = "allset.pencil_curve"
    bl_label = "Pencil Curve Tool"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _object_mode(context)
        data = bpy.data.curves.new("curveShape", 'CURVE')
        data.dimensions = '3D'
        ob = _link_new(context, bpy.data.objects.new("curve", data), "curve")
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            bpy.ops.wm.tool_set_by_id(name="builtin.draw", space_type='VIEW_3D')
        except RuntimeError:     # no tool keymaps in background (-b): the curve is still ready to draw on
            pass
        return {'FINISHED'}


def _end_points(curve):
    """Select only the last point of every open spline (Maya adds points at the curve's end)."""
    for sp in curve.splines:
        if sp.type == 'BEZIER':
            for p in sp.bezier_points:
                p.select_control_point = p.select_left_handle = p.select_right_handle = False
            if not sp.use_cyclic_u and len(sp.bezier_points):
                sp.bezier_points[-1].select_control_point = True
        else:
            for p in sp.points:
                p.select = False
            if not sp.use_cyclic_u and len(sp.points):
                sp.points[-1].select = True


class ALLSET_OT_add_points(bpy.types.Operator):
    """Add points at the end of the selected curve (Maya Curves > Add Points Tool: extrude the end point)"""
    bl_idname = "allset.add_points"
    bl_label = "Add Points Tool"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and ob.type == 'CURVE'

    def invoke(self, context, event):
        ob = context.active_object
        if context.mode != 'EDIT_CURVE':
            bpy.ops.object.mode_set(mode='OBJECT')
            _end_points(ob.data)
            bpy.ops.object.mode_set(mode='EDIT')
        if context.area is None or context.area.type != 'VIEW_3D':
            return {'FINISHED'}
        return bpy.ops.curve.extrude_move('INVOKE_DEFAULT')

    def execute(self, context):
        ob = context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')
        _end_points(ob.data)
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


# --- NURBS primitives Blender lacks (operators/create.BUILDERS) ---------------------------------
# Maya axes -> Blender: X -> X, Y -> Z, Z -> -Y. Sizes  ().

def _group(context, base):
    grp = bpy.data.objects.new(base, None)
    grp.empty_display_type = 'PLAIN_AXES'
    grp.empty_display_size = 0.0
    context.collection.objects.link(grp)
    naming.apply_maya_name(grp, base, rename_data=False)
    return grp


def _child_name(side, grp):
    return f"{side}{grp.name}"     # Maya: topnurbsSquare1, ... (the group's number makes it unique)


def nurbs_square(context, k):
    """Group ``nurbsSquare1`` of four straight curves (Maya top / left / bottom / right, side 1)."""
    grp = _group(context, "nurbsSquare")
    h = 0.5 * k
    # Maya (x, z) corners -> Blender (x, -z)
    sides = {"top": ((-h, -h), (h, -h)), "left": ((-h, h), (-h, -h)), "bottom": ((-h, h), (h, h)),
             "right": ((h, h), (h, -h))}
    for side, (a, b) in sides.items():
        data = bpy.data.curves.new(f"{side}{grp.name}Shape", 'CURVE')
        data.dimensions = '3D'
        sp = data.splines.new('NURBS')
        sp.points.add(1)
        sp.points[0].co = (a[0], a[1], 0.0, 1.0)
        sp.points[1].co = (b[0], b[1], 0.0, 1.0)
        sp.order_u = 2
        sp.use_endpoint_u = True
        ob = bpy.data.objects.new(_child_name(side, grp), data)
        context.collection.objects.link(ob)
        ob.parent = grp
    return grp


def nurbs_cube(context, k):
    """Group ``nurbsCube1`` of six NURBS patches (Maya top / bottom / left / right / front / back, width 1)."""
    grp = _group(context, "nurbsCube")
    h = 0.5 * k
    # side -> (Blender location, rotation): Maya +Y top -> +Z, Maya +Z left -> -Y, Maya +X front -> +X.
    sides = {"top": ((0, 0, h), (0, 0, 0)), "bottom": ((0, 0, -h), (math.pi, 0, 0)),
             "left": ((0, -h, 0), (math.pi / 2, 0, 0)), "right": ((0, h, 0), (-math.pi / 2, 0, 0)),
             "front": ((h, 0, 0), (0, math.pi / 2, 0)), "back": ((-h, 0, 0), (0, -math.pi / 2, 0))}
    for side, (loc, rot) in sides.items():
        bpy.ops.surface.primitive_nurbs_surface_surface_add(radius=h, location=loc, rotation=rot, align='WORLD')
        ob = context.view_layer.objects.active
        ob.name = _child_name(side, grp)
        ob.data.name = f"{ob.name}Shape"
        ob.parent = grp
        from . import material
        material.give_default(ob)
    return grp


def nurbs_cone(context, k):
    """``nurbsCone1``: radius 1, height 2 around the origin, apex up (Maya +Y = Blender +Z)."""
    bpy.ops.surface.primitive_nurbs_surface_cylinder_add(radius=k, location=(0, 0, 0), align='WORLD')
    ob = context.view_layer.objects.active
    pts = [p for sp in ob.data.splines for p in sp.points]
    top = max(p.co.z for p in pts)
    for p in pts:
        if abs(p.co.z - top) < 1e-6:
            p.co = (0.0, 0.0, p.co.z, p.co.w)
    naming.apply_maya_name(ob, "nurbsCone")
    return ob


classes = (ALLSET_OT_surface_planar, ALLSET_OT_loft, ALLSET_OT_surface_extrude, ALLSET_OT_bevel_plus,
           ALLSET_OT_offset_curve, ALLSET_OT_sweep_mesh, ALLSET_OT_pencil_curve, ALLSET_OT_add_points)
