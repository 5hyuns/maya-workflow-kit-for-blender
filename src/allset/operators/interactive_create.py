# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Create > Polygon Primitives > Interactive Creation (#225).

While the check item is on, a polygon primitive from the Create menu, the shelf or its option window is drawn in a
view instead of appearing at the origin, like Maya:

- the first click-drag sets the location and the base (cube / plane: corner to corner, the others: the radius from
  the press point); the following click-drags set the remaining sizes (height; torus section radius; pipe thickness;
  helix coils);
- a single click without dragging creates the default-size primitive at that point; a click on a later step skips it;
- Enter completes the primitive at once (the remaining sizes keep the default proportions);
- Shift: equal proportions from the first drag (the remaining steps are skipped), growing from the base;
  Ctrl: cube / plane grow from their centre; Ctrl+Shift: equal proportions, centred on the press point;
- Esc drops an unfinished primitive and ends the tool;
- Exit On Completion (on by default) ends the tool after one primitive; off, it stays until Esc / Enter with nothing
  started / Q / W / E / R.

Perspective views draw on the ground grid (z = 0), orthographic views on the view plane through the origin. The
primitive is a regular kit primitive (Maya name, creation node in Channel Box INPUTS, lambert1), rebuilt while
dragging; each finished primitive is one undo step.
"""

import math

import bpy
from bpy.props import EnumProperty, StringProperty
from mathutils import Matrix, Vector

from .. import results

# kind -> its steps. The first step places the primitive; the others size it along the plane normal or in the plane.
STEPS = {
    'CUBE': ("rect", "height"),
    'PLANE': ("rect",),
    'SPHERE': ("radius",),
    'SOCCER_BALL': ("radius",),
    'PLATONIC': ("radius",),
    'DISC': ("radius",),
    'TORUS': ("radius", "section"),
    'CYLINDER': ("radius", "height"),
    'CONE': ("radius", "height"),
    'PRISM': ("side", "height"),
    'PYRAMID': ("side",),
    'PIPE': ("radius", "height", "thickness"),
    'HELIX': ("width", "height", "coils"),
}
# Primitives with one size only (no height step): centred on the plane unless Shift grows them from their base.
SOLIDS = {'SPHERE', 'SOCCER_BALL', 'PLATONIC', 'TORUS'}
# The attribute each later step drives (prism height = its "length")
HEIGHT_ATTR = {'PRISM': "length"}
# Default proportions of the later sizes to the first one (as the default primitives: cube 1 x 1 x 1, cylinder / cone r 1
# h 2, torus r 1 section 0.5, prism side 1 length 2, pipe r 1 h 2 thickness 0.5, helix width 2 height 2 coils 3).
RATIO = {
    'CUBE': {"height": 1.0}, 'CYLINDER': {"height": 2.0}, 'CONE': {"height": 2.0},
    'TORUS': {"sectionRadius": 0.5}, 'PRISM': {"length": 2.0}, 'PIPE': {"height": 2.0, "thickness": 0.5},
    'HELIX': {"height": 1.0},
}
COIL_PX = 20.0          # px of drag per coil
FLAT = 1e-4             # smallest size while drawing (a zero size has no faces to build)
# size attributes a single click sets to the option-window / factory value
SIZES = ("width", "height", "depth", "radius", "sideLength", "length", "sectionRadius", "thickness")
STATUS = ("Interactive Creation: drag to place and size, click to skip a step, Enter to complete, "
          "Shift equal proportions, Ctrl from the centre, Esc to cancel")


def wanted(context, kind):
    """True when Interactive Creation is on and ``kind`` can be drawn in a window."""
    from .. import preferences
    if kind not in STEPS or bpy.app.background or getattr(context, "window", None) is None:
        return False
    try:
        return bool(preferences.get(context).interactive_creation)
    except (KeyError, AttributeError):
        return False


def start(context, kind, overrides=None):
    """Start the tool for ``kind`` with option-window values ``overrides`` (Maya node attributes)."""
    import json
    return bpy.ops.allset.interactive_create('INVOKE_DEFAULT', kind=kind, values=json.dumps(overrides or {}))


# --- geometry (no bpy) ----------------------------------------------------------------------------------------

class Plane:
    """The drawing plane: ``origin``, unit ``normal`` and in-plane axes ``u`` / ``v`` (u x v = normal)."""

    def __init__(self, origin, normal, u):
        self.origin = Vector(origin)
        self.normal = Vector(normal).normalized()
        self.u = Vector(u).normalized()
        self.v = self.normal.cross(self.u).normalized()

    def hit(self, ray_origin, ray_dir, forward_only=True):
        """Where the ray meets the plane, or None (parallel / behind the eye)."""
        d = Vector(ray_dir)
        den = d.dot(self.normal)
        if abs(den) < 1e-8:
            return None
        t = (self.origin - Vector(ray_origin)).dot(self.normal) / den
        if forward_only and t < 0:
            return None
        return Vector(ray_origin) + d * t

    def coords(self, p):
        q = Vector(p) - self.origin
        return q.dot(self.u), q.dot(self.v)

    def point(self, a, b):
        return self.origin + self.u * a + self.v * b

    def rotation(self):
        """Object rotation: local X = u, Y = v, Z = normal (Maya's up axis)."""
        return Matrix((self.u, self.v, self.normal)).transposed().to_4x4()


def axis_param(center, normal, ray_origin, ray_dir):
    """Parameter t of the point on the line ``center + normal t`` closest to the ray, or None when they're parallel."""
    n, d = Vector(normal), Vector(ray_dir).normalized()
    w = Vector(center) - Vector(ray_origin)
    b = n.dot(d)
    den = 1.0 - b * b
    if den < 1e-4:
        return None
    return (b * d.dot(w) - n.dot(w)) / den


def rect(a0, b0, a1, b1, centred=False, square=False):
    """(centre a, centre b, width, depth) of a base dragged from (a0, b0) to (a1, b1) in plane coordinates."""
    da, db = a1 - a0, b1 - b0
    if square:
        s = max(abs(da), abs(db))
        da, db = math.copysign(s, da or 1.0), math.copysign(s, db or 1.0)
    if centred:
        return a0, b0, 2 * abs(da), 2 * abs(db)
    return a0 + da / 2, b0 + db / 2, abs(da), abs(db)


def side_for_radius(radius, sides):
    """Side length of a regular ``sides``-gon with circumradius ``radius``."""
    return 2.0 * radius * math.sin(math.pi / sides)


def first_values(kind, size, sides=4):
    """Node attributes the first step sets from its size (Maya units): width x depth for "rect", else a radius."""
    step = STEPS[kind][0]
    if step == "rect":
        w, dp = size
        return {"width": w, ("height" if kind == 'PLANE' else "depth"): dp}
    if step == "side":
        return {"sideLength": side_for_radius(size, sides)}
    if step == "width":
        return {"width": 2.0 * size}
    return {"radius": size}


def base_size(kind, values):
    """The first step's size the default proportions refer to."""
    if kind == 'CUBE':
        return max(values["width"], values["depth"])
    if kind in {'PRISM', 'PYRAMID'}:
        return values["sideLength"]
    if kind == 'HELIX':
        return values["width"]
    return values.get("radius", 1.0)


def skipped(kind, values, step):
    """Attribute values of a skipped later ``step``: the factory proportion to the first size."""
    attr = step_attr(kind, step)
    if attr is None:
        return {}
    if attr == "coils":
        return {}                  # keeps its value (factory 3)
    ratio = RATIO.get(kind, {}).get(attr)
    if ratio is None:
        return {}
    return {attr: ratio * base_size(kind, values)}


def step_attr(kind, step):
    return {"height": HEIGHT_ATTR.get(kind, "height"), "section": "sectionRadius", "thickness": "thickness",
            "coils": "coils"}.get(step)


def placement(base_point, normal, zmin, zmax, mode):
    """Object location so the shape (local extent [zmin, zmax] along ``normal``) sits on the plane: "base" = bottom
    on the plane, "top" = top on it (a height dragged below), "centre" = centred on it."""
    n = Vector(normal)
    off = {"base": -zmin, "top": -zmax}.get(mode, -(zmin + zmax) / 2)
    return Vector(base_point) + n * off


# --- the tool --------------------------------------------------------------------------------------------------

def drawing_plane(rv3d):
    """Ground (z = 0, X / Y) in a perspective view, else the view plane through the origin."""
    if rv3d.is_perspective:
        return Plane((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
    rot = rv3d.view_rotation
    return Plane((0.0, 0.0, 0.0), rot @ Vector((0.0, 0.0, 1.0)), rot @ Vector((1.0, 0.0, 0.0)))


def _ray(region, rv3d, coord):
    from bpy_extras import view3d_utils
    return (view3d_utils.region_2d_to_origin_3d(region, rv3d, coord),
            view3d_utils.region_2d_to_vector_3d(region, rv3d, coord))


def _px_size(region, rv3d, point):
    """World length of one pixel at ``point`` (screen-vertical)."""
    from bpy_extras import view3d_utils
    c = view3d_utils.location_3d_to_region_2d(region, rv3d, point)
    if c is None:
        return 0.0
    a = view3d_utils.region_2d_to_location_3d(region, rv3d, c, point)
    b = view3d_utils.region_2d_to_location_3d(region, rv3d, (c[0], c[1] + 1.0), point)
    return (b - a).length


class ALLSET_OT_interactive_create(bpy.types.Operator):
    """Maya Interactive Creation: drag in a view to place and size a polygon primitive"""
    bl_idname = "allset.interactive_create"
    bl_label = "Interactive Creation"
    bl_options = set()          # each finished primitive pushes its own undo step

    kind: EnumProperty(name="Kind", items=[(k, k.replace("_", " ").title(), "") for k in STEPS])
    values: StringProperty(options={'SKIP_SAVE', 'HIDDEN'}, description="JSON: option-window node attributes")

    def invoke(self, context, event):
        import json
        if context.window is None:
            return {'CANCELLED'}
        try:
            self._over = dict(json.loads(self.values)) if self.values else {}
        except (ValueError, TypeError):
            self._over = {}
        self._reset()
        self._made = 0
        context.workspace.status_text_set(STATUS)
        context.window.cursor_modal_set('CROSSHAIR')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    # state of one primitive
    def _reset(self):
        self._ob = None          # the primitive being drawn
        self._step = 0           # index into STEPS[kind]
        self._down = None        # (x, y) of the press of the current drag
        self._moved = False
        self._area = self._region = None
        self._plane = None
        self._history = True
        self._px0 = 0
        self._start = None       # plane coords of the first press
        self._base = None        # base point on the plane
        self._mode = "centre" if self.kind in SOLIDS else "base"
        self._vals = {}
        self._t0 = None
        self._v0 = 0.0

    def _end(self, context):
        context.workspace.status_text_set(None)
        if context.window is not None:
            context.window.cursor_modal_restore()

    # --- events
    def modal(self, context, event):
        if event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':
            if self._ob is None:
                self._end(context)
                return {'FINISHED'} if self._made else {'CANCELLED'}
            return self._complete(context, rest=True)
        if event.type == 'ESC' and event.value == 'PRESS':
            self._drop()
            self._end(context)
            return {'FINISHED'} if self._made else {'CANCELLED'}
        if self._ob is None and event.type in {'Q', 'W', 'E', 'R'} and event.value == 'PRESS' \
                and not (event.alt or event.ctrl or event.shift or event.oskey):
            self._end(context)                       # the key goes on to pick its tool
            return {'FINISHED', 'PASS_THROUGH'} if self._made else {'CANCELLED', 'PASS_THROUGH'}
        if event.type == 'LEFTMOUSE' and not event.alt:
            if event.value == 'PRESS':
                return self._press(context, event)
            if event.value == 'RELEASE' and self._down is not None:
                return self._release(context, event)
        if event.type == 'MOUSEMOVE' and self._down is not None:
            self._drag(context, event)
            return {'RUNNING_MODAL'}
        return {'PASS_THROUGH'}

    def _press(self, context, event):
        from .joints import view_under
        if self._ob is None:
            hit = view_under(context.window, event.mouse_x, event.mouse_y)
            if hit is None:
                return {'PASS_THROUGH'}
            area, region = hit
            coord = (event.mouse_x - region.x, event.mouse_y - region.y)
            plane = drawing_plane(region.data)
            p = plane.hit(*_ray(region, region.data, coord), forward_only=region.data.is_perspective)
            if p is None:
                return {'RUNNING_MODAL'}
            self._area, self._region, self._plane = area, region, plane
            self._start = plane.coords(p)
            self._base = p
            self._new(context)
        elif self._region is None or view_under(context.window, event.mouse_x, event.mouse_y) is None:
            return {'PASS_THROUGH'}            # a later step is dragged in a view; clicks elsewhere go on
        else:
            self._t0 = self._axis_t(event)
            self._v0 = self._vals.get(step_attr(self.kind, STEPS[self.kind][self._step]), 0.0) or 0.0
            self._px0 = event.mouse_y
        self._down = (event.mouse_x, event.mouse_y)
        self._moved = False
        return {'RUNNING_MODAL'}

    def _drag(self, context, event):
        dx, dy = event.mouse_x - self._down[0], event.mouse_y - self._down[1]
        thr = context.preferences.inputs.drag_threshold_mouse * (context.preferences.system.ui_scale or 1.0)
        if not self._moved and math.hypot(dx, dy) < max(thr, 3):
            return
        self._moved = True
        self._apply(context, event)

    def _release(self, context, event):
        self._down = None
        steps = STEPS[self.kind]
        if self._step == 0 and not self._moved:
            return self._complete(context, rest=False, default=True)     # single click: default size here
        if self._step == 0 and event.shift:
            return self._complete(context, rest=True)                    # equal proportions: one drag
        if self._step > 0 and not self._moved:
            self._set(context, skipped(self.kind, self._vals, steps[self._step]))
        self._step += 1
        if self._step >= len(steps):
            return self._complete(context, rest=False)
        if self._step == 1 and steps[1] == "height":
            self._set(context, {step_attr(self.kind, "height"): FLAT})   # the height starts flat
        return {'RUNNING_MODAL'}

    # --- the primitive
    def _new(self, context):
        from . import create, material, prim_history
        with context.temp_override(window=context.window, area=self._area, region=self._region):
            if context.mode != 'OBJECT' and context.active_object is not None:
                bpy.ops.object.mode_set(mode='OBJECT')
            vals = dict(self._over)
            uvs = bool(vals.pop("createUVs", True))
            tiny = FLAT         # grows from nothing
            vals.update(first_values(self.kind, (tiny, tiny) if STEPS[self.kind][0] == "rect" else tiny,
                                     int(vals.get("numberOfSides", 4 if self.kind == 'PYRAMID' else 3))))
            for later in STEPS[self.kind][1:]:
                vals.update(skipped(self.kind, vals, later))
            history = prim_history.history_on(context)
            wm = context.window_manager
            live = hasattr(wm, "allset_construction_history")
            if live:
                wm.allset_construction_history = True     # rebuilt live from its node; dropped at the end if off
            try:
                ob = prim_history.create_object(context, self.kind, vals, create._maya_naming(context), create_uvs=uvs)
            finally:
                if live:
                    wm.allset_construction_history = history
            material.give_default(ob)
        self._ob, self._history = ob, history
        self._vals = prim_history.attrs(prim_history.owner_of(ob))
        self._place()

    def _set(self, context, changes):
        from . import prim_history
        if self._ob is None or not changes:
            return
        vals = prim_history.rebuild(context, self._ob, changes)
        if vals is not None:
            self._vals = vals
        self._place()

    def _place(self):
        ob = self._ob
        zs = [v.co.z for v in ob.data.vertices] or [0.0]
        ob.matrix_world = Matrix.Translation(
            placement(self._base, self._plane.normal, min(zs), max(zs), self._mode)) @ self._plane.rotation()
        if self._area is not None:
            self._area.tag_redraw()

    def _axis_t(self, event):
        region = self._region
        coord = (event.mouse_x - region.x, event.mouse_y - region.y)
        return axis_param(self._base, self._plane.normal, *_ray(region, region.data, coord))

    def _apply(self, context, event):
        from . import units
        k = units.maya_unit(context.scene) or 1.0
        region, plane, kind = self._region, self._plane, self.kind
        step = STEPS[kind][self._step]
        coord = (event.mouse_x - region.x, event.mouse_y - region.y)
        if self._step == 0:
            p = plane.hit(*_ray(region, region.data, coord), forward_only=region.data.is_perspective)
            if p is None:
                return
            a, b = plane.coords(p)
            a0, b0 = self._start
            equal = event.shift
            if step == "rect":
                ca, cb, w, dp = rect(a0, b0, a, b, centred=event.ctrl, square=equal)
                self._base = plane.point(ca, cb)
                changes = first_values(kind, (w / k, dp / k))
            else:
                changes = first_values(kind, math.hypot(a - a0, b - b0) / k,
                                       int(self._vals.get("numberOfSides", 3)))
            for later in STEPS[kind][1:]:
                # Shift: every remaining size follows the first one; else only the in-plane ones (torus section,
                # pipe thickness) do while the base is dragged, the height starts flat in its own step
                if equal or later != "height":
                    changes.update(skipped(kind, {**self._vals, **changes}, later))
            if equal:
                self._mode = "centre" if event.ctrl else "base"
            else:
                self._mode = "centre" if kind in SOLIDS else "base"
            self._set(context, changes)
            return
        attr = step_attr(kind, step)
        if step == "height":
            t = self._axis_t(event)
            if t is None or self._t0 is None:
                t = (event.mouse_y - self._px0) * _px_size(region, region.data, self._base)
                h = self._v0 * self._sign() + t / k
            else:
                h = self._v0 * self._sign() + (t - self._t0) / k
            self._mode = "top" if h < 0 else "base"     # dragged below the plane: the shape hangs under it
            self._set(context, {attr: max(abs(h), FLAT)})
        elif step in {"section", "thickness"}:
            p = plane.hit(*_ray(region, region.data, coord), forward_only=region.data.is_perspective)
            if p is None:
                return
            ca, cb = plane.coords(self._base)
            a, b = plane.coords(p)
            r = math.hypot(a - ca, b - cb) / k
            radius = self._vals.get("radius", 1.0)
            self._set(context, {attr: abs(r - radius) if step == "section" else max(radius - r, 0.0)})
        elif step == "coils":
            self._set(context, {attr: max(self._v0 + (event.mouse_y - self._px0) / COIL_PX, 0.5)})

    def _sign(self):
        return -1.0 if self._mode == "top" else 1.0

    def _complete(self, context, rest, default=False):
        """Finish the primitive: ``rest`` = remaining steps take the default proportions, ``default`` = factory size."""
        from . import prim_history, prim_shapes
        ob = self._ob
        if default:   # the option-window size, else the factory size
            factory = prim_shapes.defaults(prim_history.node_of(ob)[1]["type"])
            self._set(context, {a: self._over.get(a, factory[a]) for a in SIZES if a in factory})
        elif rest:    # Enter: the steps not done yet keep the default proportions
            first = max(self._step + (1 if self._down is not None else 0), 1)   # a step being dragged keeps its value
            for later in STEPS[self.kind][first:]:
                self._set(context, skipped(self.kind, self._vals, later))
        if not self._history:
            prim_history.drop(ob)                   # Construction History off: no creation node (Maya -ch 0)
        name = ob.name
        self._made += 1
        self._reset()
        with context.temp_override(window=context.window):
            bpy.ops.ed.undo_push(message=f"Create {name}")
        results.result(self, f"Created {name}")
        from .. import preferences
        try:
            exit_now = preferences.get(context).exit_on_completion
        except (KeyError, AttributeError):
            exit_now = True
        if exit_now:
            self._end(context)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

    def _drop(self):
        ob = self._ob
        if ob is None:
            return
        data = ob.data
        bpy.data.objects.remove(ob)
        if data is not None and data.users == 0:
            bpy.data.meshes.remove(data)
        self._reset()


classes = (ALLSET_OT_interactive_create,)
