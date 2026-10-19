# SPDX-License-Identifier: GPL-3.0-or-later
"""A small ``maya.cmds`` look-alike for the command line (docs/steps/step_7.md 「계획」 5).

Re-implemented from Maya's documented command behaviour (flag long/short
names, return values) — no Maya code. Numbers are in the scene's display
units like Maya's current linear unit (cm by default, decision 1) and angles
in degrees (radians if the scene's rotation unit is radians). Attribute names
match the Channel Box (``ui/channel_box.py`` MAIN).

Supported: ls, select, move, rotate, scale, setAttr, getAttr, xform,
polyCube, polySphere, polyCylinder, polyPlane, delete, rename, objExists,
listRelatives, currentTime. Anything else raises AttributeError.
"""

import math

import bmesh
import bpy
from mathutils import Vector

from ..operators import units as _units

__all__ = ["ls", "select", "move", "rotate", "scale", "setAttr", "getAttr", "xform",
           "polyCube", "polySphere", "polyCylinder", "polyPlane", "delete", "rename",
           "objExists", "listRelatives", "currentTime"]


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    raise AttributeError(f"maya.cmds.{name} is not available in Allset (cmds_shim)")


# --- units, flags, objects ----------------------------------------------------------

def linear_factor(scene=None):
    """Blender units per Maya linear unit (= one scene display unit, decision 8)."""
    return _units.maya_unit(scene)


def _to_bu(v):
    return v * linear_factor()


def _from_bu(v):
    return v / linear_factor()


def _degrees():
    return bpy.context.scene.unit_settings.system_rotation != 'RADIANS'


def _to_rad(v):
    return math.radians(v) if _degrees() else v


def _from_rad(v):
    return math.degrees(v) if _degrees() else v


class _Flags:
    """Maya flags have a long and a short name; unknown flags are an error."""

    def __init__(self, cmd, kwargs):
        self.cmd = cmd
        self.kw = dict(kwargs)

    def get(self, long, short=None, default=None):
        for key in (long, short):
            if key and key in self.kw:
                return self.kw.pop(key)
        return default

    def done(self):
        if self.kw:
            raise TypeError(f"{self.cmd}: Invalid flag '{next(iter(self.kw))}'")


def _flatten(args):
    for a in args:
        if isinstance(a, (list, tuple)):
            yield from _flatten(a)
        else:
            yield a


def _object(name):
    if isinstance(name, bpy.types.Object):
        return name
    short = str(name).rsplit("|", 1)[-1]
    if "." in short or "[" in short:
        raise RuntimeError(f"Components are not supported: {name}")
    ob = bpy.data.objects.get(short)
    if ob is None:  # a shape name ("pCubeShape1") -> its transform
        ob = next((o for o in bpy.data.objects if o.data is not None and o.data.name == short), None)
    if ob is None:
        raise ValueError(f"No object matches name: {name}")
    return ob


def _objects(args, default_selection=True):
    names = list(_flatten(args))
    if names:
        return [_object(n) for n in names]
    if default_selection:
        sel = _selection()
        if not sel:
            raise RuntimeError("Nothing selected")
        return sel
    return []


def _view_layer():
    vl = bpy.context.view_layer
    vl.update()  # objects added/removed by earlier commands
    return vl


def _selection():
    """Selected objects in Maya order: the active (lead) object last."""
    vl = _view_layer()
    sel = [o for o in vl.objects if o.select_get()]
    active = vl.objects.active
    if active in sel:
        sel.remove(active)
        sel.append(active)
    return sel


# --- ls / select ------------------------------------------------------------------

_SHAPE_TYPES = {"mesh": 'MESH', "camera": 'CAMERA', "light": 'LIGHT', "pointLight": 'LIGHT',
                "nurbsCurve": 'CURVE', "nurbsSurface": 'SURFACE', "lattice": 'LATTICE'}


def ls(*args, **kwargs):
    f = _Flags("ls", kwargs)
    sl = f.get("selection", "sl", False)
    typ = f.get("type", "typ")
    long = f.get("long", "l", False)
    transforms = f.get("transforms", "tr", False)
    f.done()
    if args:
        obs = [_object(n) for n in _flatten(args)]
    elif sl:
        obs = _selection()
    else:
        obs = list(bpy.context.scene.objects)
    if transforms:
        typ = "transform"
    if typ in (None, "transform"):
        return [_long_name(o) if long else o.name for o in obs]
    types = typ if isinstance(typ, (list, tuple)) else [typ]
    want = {_SHAPE_TYPES[t] for t in types if t in _SHAPE_TYPES}
    return [o.data.name for o in obs if o.type in want and o.data is not None]


def _long_name(ob):
    parts = []
    while ob is not None:
        parts.append(ob.name)
        ob = ob.parent
    return "|" + "|".join(reversed(parts))


def select(*args, **kwargs):
    f = _Flags("select", kwargs)
    clear = f.get("clear", "cl", False)
    add = f.get("add", None, False) or f.get("addFirst", "af", False)
    deselect = f.get("deselect", "d", False)
    toggle = f.get("toggle", "tgl", False)
    f.get("replace", "r", False)
    f.done()
    vl = _view_layer()
    obs = [_object(n) for n in _flatten(args)]
    if clear or not obs:  # select with nothing given clears the selection
        for o in vl.objects:
            o.select_set(False)
        return None
    if not (add or deselect or toggle):
        for o in vl.objects:
            o.select_set(False)
    for o in obs:
        state = not o.select_get() if toggle else not deselect
        o.select_set(state)
        if state:
            vl.objects.active = o
    return None


# --- transforms --------------------------------------------------------------------

def _split_values(args, count=3):
    values, rest = [], []
    for a in _flatten(args):
        if isinstance(a, (int, float)) and not isinstance(a, bool) and len(values) < count and not rest:
            values.append(float(a))
        else:
            rest.append(a)
    if len(values) != count:
        raise ValueError(f"Expected {count} values, got {len(values)}")
    return values, rest


def move(*args, **kwargs):
    f = _Flags("move", kwargs)
    relative = f.get("relative", "r", False)
    f.get("absolute", "a", True)
    f.get("worldSpace", "ws", True)
    f.done()
    values, names = _split_values(args)
    v = Vector([_to_bu(x) for x in values])
    for ob in _objects(names):
        mw = ob.matrix_world.copy()
        mw.translation = mw.translation + v if relative else v
        ob.matrix_world = mw
    return None


def rotate(*args, **kwargs):
    f = _Flags("rotate", kwargs)
    relative = f.get("relative", "r", False)
    f.get("absolute", "a", True)
    f.get("objectSpace", "os", True)
    f.done()
    values, names = _split_values(args)
    rad = [_to_rad(x) for x in values]
    for ob in _objects(names):
        for i in range(3):
            ob.rotation_euler[i] = ob.rotation_euler[i] + rad[i] if relative else rad[i]
    return None


def scale(*args, **kwargs):
    f = _Flags("scale", kwargs)
    relative = f.get("relative", "r", False)
    f.get("absolute", "a", True)
    f.done()
    values, names = _split_values(args)
    for ob in _objects(names):
        for i in range(3):
            ob.scale[i] = ob.scale[i] * values[i] if relative else values[i]
    return None


# Maya attribute -> (Channel Box key or compound keys).
_COMPOUND = {"translate": ("tx", "ty", "tz"), "t": ("tx", "ty", "tz"),
             "rotate": ("rx", "ry", "rz"), "r": ("rx", "ry", "rz"),
             "scale": ("sx", "sy", "sz"), "s": ("sx", "sy", "sz")}
_SCALAR = {"translateX": "tx", "translateY": "ty", "translateZ": "tz",
           "rotateX": "rx", "rotateY": "ry", "rotateZ": "rz",
           "scaleX": "sx", "scaleY": "sy", "scaleZ": "sz", "visibility": "v",
           **{k: k for k in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v")}}


def _split_attr(attr):
    if "." not in str(attr):
        raise ValueError(f"Expected node.attribute, got {attr!r}")
    node, name = str(attr).split(".", 1)
    return _object(node), name


def _cb():
    from ..ui import channel_box
    return channel_box


def _get_key(ob, key):
    value = _cb().get_value(ob, key)
    kind = _cb().MAIN_BY_KEY[key][4]
    if kind == "LOC":
        return _from_bu(value)
    if kind == "ROT":
        return _from_rad(value)
    return bool(value) if kind == "VIS" else value


def _set_key(ob, key, value):
    kind = _cb().MAIN_BY_KEY[key][4]
    if kind == "LOC":
        value = _to_bu(value)
    elif kind == "ROT":
        value = _to_rad(value)
    _cb().set_value(ob, key, value)


def getAttr(attr, **kwargs):
    f = _Flags("getAttr", kwargs)
    lock = f.get("lock", "l", False)
    f.done()
    ob, name = _split_attr(attr)
    if lock:
        key = _SCALAR.get(name) or (_COMPOUND.get(name) or (None,))[0]
        return bool(key and _cb().is_locked(ob, key))
    if name in _COMPOUND:
        return [tuple(_get_key(ob, k) for k in _COMPOUND[name])]
    if name in _SCALAR:
        return _get_key(ob, _SCALAR[name])
    if name in ob.keys():
        return ob[name]
    raise ValueError(f"No attribute '{name}' on {ob.name}")


def setAttr(attr, *values, **kwargs):
    f = _Flags("setAttr", kwargs)
    lock = f.get("lock", "l")
    f.get("type", "typ")
    f.done()
    ob, name = _split_attr(attr)
    keys = _COMPOUND.get(name) or ((_SCALAR[name],) if name in _SCALAR else None)
    if lock is not None and keys:
        for k in keys:
            if k != "v":
                _cb().set_locked(ob, k, bool(lock))
    if not values:
        return None
    values = list(_flatten(values))
    if keys is None:
        if name not in ob.keys():
            raise ValueError(f"No attribute '{name}' on {ob.name}")
        ob[name] = type(ob[name])(values[0])
        return None
    if len(values) != len(keys):
        raise ValueError(f"setAttr {attr}: expected {len(keys)} value(s), got {len(values)}")
    for k, v in zip(keys, values):
        if _cb().is_locked(ob, k):
            raise RuntimeError(f"The attribute '{ob.name}.{name}' is locked or connected and cannot be modified.")
        _set_key(ob, k, v)
    return None


def xform(*args, **kwargs):
    f = _Flags("xform", kwargs)
    query = f.get("query", "q", False)
    t = f.get("translation", "t")
    ro = f.get("rotation", "ro")
    s = f.get("scale", "s")
    ws = f.get("worldSpace", "ws", False)
    relative = f.get("relative", "r", False)
    f.done()
    obs = _objects(args)
    if query:
        ob = obs[0]
        if t:
            loc = ob.matrix_world.translation if ws else ob.location
            return [_from_bu(x) for x in loc]
        if ro:
            return [_from_rad(x) for x in ob.rotation_euler]
        if s:
            return list(ob.scale)
        raise TypeError("xform -query needs -translation, -rotation or -scale")
    for ob in obs:
        if t is not None:
            v = Vector([_to_bu(x) for x in t])
            if ws:
                mw = ob.matrix_world.copy()
                mw.translation = mw.translation + v if relative else v
                ob.matrix_world = mw
            else:
                ob.location = ob.location + v if relative else v
        if ro is not None:
            for i in range(3):
                r = _to_rad(ro[i])
                ob.rotation_euler[i] = ob.rotation_euler[i] + r if relative else r
        if s is not None:
            for i in range(3):
                ob.scale[i] = ob.scale[i] * s[i] if relative else s[i]
    return None


# --- creation (Maya naming: pCube1 / pCubeShape1 / polyCube1) ----------------------

def _unique(base):
    n = 1
    while f"{base}{n}" in bpy.data.objects or f"{base}{n}" in bpy.data.meshes:
        n += 1
    return n


def _create(kind, base, name, build):
    """Build a mesh with ``build(bm)``, link it like Maya (origin, selected, lead)."""
    if name:
        ob_name, shape_name = name, f"{name}Shape"
        n = _unique(f"poly{kind}")
    else:
        n = _unique(base)
        ob_name, shape_name = f"{base}{n}", f"{base}Shape{n}"
    mesh = bpy.data.meshes.new(shape_name)
    bm = bmesh.new()
    build(bm)
    bm.to_mesh(mesh)
    bm.free()
    ob = bpy.data.objects.new(ob_name, mesh)
    bpy.context.collection.objects.link(ob)
    vl = _view_layer()
    for o in vl.objects:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    return [ob.name, f"poly{kind}{n}"]


def _no_history(f):
    f.get("constructionHistory", "ch")
    f.get("axis", "ax")


def polyCube(**kwargs):
    f = _Flags("polyCube", kwargs)
    w = f.get("width", "w", 1.0)
    h = f.get("height", "h", 1.0)
    d = f.get("depth", "d", 1.0)
    for long, short in (("subdivisionsX", "sx"), ("subdivisionsY", "sy"), ("subdivisionsZ", "sz")):
        if f.get(long, short, 1) != 1:
            raise ValueError("polyCube: subdivisions are not supported by cmds_shim")
    name = f.get("name", "n")
    _no_history(f)
    f.done()
    k = linear_factor()

    def build(bm):
        bmesh.ops.create_cube(bm, size=1.0)
        # Maya is Y-up: width = X, height = up (Blender Z), depth = Blender Y.
        bmesh.ops.scale(bm, vec=(w * k, d * k, h * k), verts=bm.verts)
    return _create("Cube", "pCube", name, build)


def polySphere(**kwargs):
    f = _Flags("polySphere", kwargs)
    r = f.get("radius", "r", 1.0)
    sa = f.get("subdivisionsAxis", "sa", 20)
    sh = f.get("subdivisionsHeight", "sh", 20)
    name = f.get("name", "n")
    _no_history(f)
    f.done()

    def build(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=sa, v_segments=sh, radius=r * linear_factor())
    return _create("Sphere", "pSphere", name, build)


def polyCylinder(**kwargs):
    f = _Flags("polyCylinder", kwargs)
    r = f.get("radius", "r", 1.0)
    h = f.get("height", "h", 2.0)
    sa = f.get("subdivisionsAxis", "sa", 20)
    if f.get("subdivisionsHeight", "sh", 1) != 1:
        raise ValueError("polyCylinder: height subdivisions are not supported by cmds_shim")
    name = f.get("name", "n")
    _no_history(f)
    f.done()
    k = linear_factor()

    def build(bm):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=sa, radius1=r * k, radius2=r * k, depth=h * k)
    return _create("Cylinder", "pCylinder", name, build)


def polyPlane(**kwargs):
    f = _Flags("polyPlane", kwargs)
    w = f.get("width", "w", 1.0)
    h = f.get("height", "h", 1.0)
    sx = f.get("subdivisionsX", "sx", 10)
    sy = f.get("subdivisionsY", "sy", 10)
    name = f.get("name", "n")
    _no_history(f)
    f.done()
    k = linear_factor()

    def build(bm):
        # Maya's plane lies on the ground (XZ), Blender's ground is XY.
        bmesh.ops.create_grid(bm, x_segments=sx, y_segments=sy, size=0.5)
        bmesh.ops.scale(bm, vec=(w * k, h * k, 1.0), verts=bm.verts)
    return _create("Plane", "pPlane", name, build)


# --- scene ------------------------------------------------------------------------------

def delete(*args, **kwargs):
    _Flags("delete", kwargs).done()
    for ob in _objects(args):
        bpy.data.objects.remove(ob)
    return None


def rename(*args, **kwargs):
    _Flags("rename", kwargs).done()
    names = list(_flatten(args))
    if len(names) == 1:
        sel = _selection()
        if not sel:
            raise RuntimeError("rename: Nothing selected")
        ob, new = sel[-1], names[0]
    elif len(names) == 2:
        ob, new = _object(names[0]), names[1]
    else:
        raise ValueError("rename: expected [object] newName")
    ob.name = str(new)
    return ob.name


def objExists(name, **kwargs):
    _Flags("objExists", kwargs).done()
    try:
        _object(name)
    except (ValueError, RuntimeError):
        return False
    return True


def listRelatives(*args, **kwargs):
    f = _Flags("listRelatives", kwargs)
    parent = f.get("parent", "p", False)
    all_desc = f.get("allDescendents", "ad", False)
    f.get("children", "c", False)
    shapes = f.get("shapes", "s", False)
    long = f.get("fullPath", "f", False)
    f.done()
    out = []
    for ob in _objects(args):
        if parent:
            rel = [ob.parent] if ob.parent else []
        elif shapes:
            out.extend([ob.data.name] if ob.data is not None else [])
            continue
        else:
            rel = list(ob.children_recursive if all_desc else ob.children)
        out.extend(_long_name(o) if long else o.name for o in rel)
    return out or None  # Maya returns None when there is nothing


def currentTime(*args, **kwargs):
    f = _Flags("currentTime", kwargs)
    query = f.get("query", "q", False)
    f.get("edit", "e", False)
    f.get("update", "u", True)
    f.done()
    scene = bpy.context.scene
    if query or not args:
        return float(scene.frame_current) + scene.frame_subframe
    t = float(args[0])
    scene.frame_set(int(math.floor(t)), subframe=t - math.floor(t))
    return t

