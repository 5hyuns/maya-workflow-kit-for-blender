# SPDX-License-Identifier: GPL-3.0-or-later
"""The kit's handlers keep running after File > Open and File > New. Blender drops every ``bpy.app.handlers`` entry
that is not marked persistent when it loads a file, and the kit adds its handlers once (when Maya mode turns on), so
each one is persistent: after a file is opened or a new file is made every handler the kit had added is still there,
exactly once. A Tension deformer's rest positions and partner table still follow a topology change made after a file
was opened. Switching to Blender after a file load still takes every Maya mode handler away, and switching back
adds each one once."""

import os
from collections import Counter
from importlib import import_module

import bmesh
import bpy

import kit

dfa = import_module(kit.MODULE + ".operators.deformers_205a")
switch = import_module(kit.MODULE + ".switch")

OUT = os.path.join(kit.ROOT, "tmp", os.environ.get("ALLSET_SANDBOX", "test_env"), "persistent_handlers")


def _kit_functions():
    """(list name, 'module:function', function) of every handler the kit has added."""
    out = []
    for name in dir(bpy.app.handlers):
        lst = getattr(bpy.app.handlers, name)
        if not isinstance(lst, list):
            continue
        for fn in lst:
            func = getattr(fn, "__func__", None) or getattr(fn, "func", None) or fn
            mod = getattr(func, "__module__", None) or ""
            if mod == kit.MODULE or mod.startswith(kit.MODULE + "."):
                out.append((name, f"{mod[len(kit.MODULE) + 1:]}:{getattr(func, '__qualname__', repr(func))}", fn))
    return out


def _kit_handlers():
    return Counter(f"{name} {label}" for name, label, _fn in _kit_functions())


def _save(name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    return path


def _same_after(before, label):
    after = _kit_handlers()
    lost = sorted(set(before) - set(after))
    twice = sorted(k for k, n in after.items() if n > 1)
    added = sorted(set(after) - set(before))
    assert not lost and not twice and not added, (
        f"kit handlers after {label}:\n lost {len(lost)}: {lost}\n twice: {twice}\n new: {added}")


def _fresh():
    """Maya mode off and on again: every kit handler registered anew, whatever an earlier load dropped."""
    switch.set_mode(False, layout=False)
    switch.set_mode(True, layout=False)
    return _kit_handlers()


def _clear():
    if bpy.context.active_object is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def test_the_kit_adds_handlers():
    """Guard against a vacuous pass: Maya mode on adds the kit's handlers, the deformer one among them."""
    found = _kit_handlers()
    assert len(found) > 50, found
    assert found["depsgraph_update_post operators.deformers_205a:_on_depsgraph"] == 1, found


def test_every_kit_handler_is_persistent():
    plain = sorted(f"{name} {label}" for name, label, fn in _kit_functions()
                   if not hasattr(getattr(fn, "__func__", fn), "_bpy_persistent"))
    assert not plain, f"{len(plain)} kit handlers Blender drops on a file load:\n" + "\n".join(plain)


def test_handlers_kept_after_open():
    before = _fresh()
    path = _save("kept_after_open.blend")
    bpy.ops.wm.open_mainfile(filepath=path)
    _same_after(before, "File > Open")
    bpy.ops.wm.open_mainfile(filepath=path)
    _same_after(before, "a second File > Open")


def test_handlers_kept_after_new_file():
    before = _fresh()
    bpy.ops.wm.read_homefile()
    _same_after(before, "File > New")
    bpy.ops.wm.read_homefile(use_empty=True)
    _same_after(before, "File > New (empty)")


def _subdivide(ob):
    """A topology change made outside the kit, then the depsgraph update that follows it."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
    bm.to_mesh(me)
    bm.free()
    me.update()
    bpy.context.view_layer.update()


def _synced(ob):
    me = ob.data
    rest = me.attributes.get(dfa.REST + "tension1")
    co = [v.co.copy() for v in me.vertices]
    return (list(me.get(dfa.TOPO_PROP, [])) == dfa._signature(me) and rest is not None
            and all((r.vector - c).length < 1e-6 for r, c in zip(rest.data, co))
            and dfa.SLOT_COUNT in me.attributes)


def test_tension_rest_follows_topology_after_open():
    _fresh()
    _clear()
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = bpy.context.active_object
    ob.name = "pCube1"
    dfa.create(bpy.context, 'TENSION')
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    _subdivide(ob)
    assert _synced(ob), "the rest positions did not follow a topology change before any file load"
    path = _save("tension_rest.blend")
    for label, load in (("File > Open", lambda: bpy.ops.wm.open_mainfile(filepath=path)),
                        ("a second File > Open", lambda: bpy.ops.wm.open_mainfile(filepath=path))):
        load()
        ob = bpy.data.objects["pCube1"]
        n = len(ob.data.vertices)
        _subdivide(ob)
        assert len(ob.data.vertices) > n
        assert _synced(ob), f"after {label} the rest positions no longer follow a topology change"


CORE = ("i18n", "preferences", "translations", "settings_io", "switch", "welcome")


def _maya_mode_only(handlers):
    """The handlers of the Maya mode modules (everything but the always registered part of the kit)."""
    return sorted(k for k in handlers if k.split(" ", 1)[1].split(":")[0].split(".")[0] not in CORE)


def test_switch_to_blender_after_a_load_takes_every_handler():
    before = _fresh()
    assert _maya_mode_only(before)
    path = _save("switch_after_load.blend")
    bpy.ops.wm.open_mainfile(filepath=path)
    switch.set_mode(False, layout=False)
    try:
        left = _kit_handlers()
        assert not _maya_mode_only(left), f"Maya mode handlers left in Blender mode: {_maya_mode_only(left)}"
        bpy.ops.wm.open_mainfile(filepath=path)
        assert _kit_handlers() == left, "a file load in Blender mode changed the kit handlers"
    finally:
        switch.set_mode(True, layout=False)
    _same_after(before, "Blender mode, File > Open, Maya mode")
    bpy.ops.wm.open_mainfile(filepath=path)
    _same_after(before, "Blender mode, File > Open, Maya mode, File > Open")
