# SPDX-License-Identifier: GPL-3.0-or-later
"""The order the selected objects were picked in, like Maya's selection list.

Maya keeps the selection as a list in pick order; its last node is the lead. Blender keeps a selected flag per object
and one active object, and only a click makes the clicked object active: a box, lasso or circle drag, an Outliner box
or range, Select All and the select menus add objects and leave the active one alone. So the kit follows the
selection as it changes and keeps the order itself, per view layer:

- objects that get selected go to the end; several at once (one box) go in name order, the active one last when it
  is among them;
- an object that becomes the active one while selected (a click on an object already selected) moves to the end;
- objects that get deselected drop out.

The order is kept in memory only, objects by ``session_uid`` (it stays the same across undo and renames). After a
file load, or for a selection made while nothing was looking, it starts from the selection: the active object last,
the others by name.
"""

import bpy
from bpy.app.handlers import persistent

# (scene session_uid, view layer name) -> object session_uids, first pick first
_orders = {}
# same key -> session_uid of the active object when the order was last brought up to date (0: none)
_actives = {}


def _sync(scene, view_layer):
    """Bring the order of ``view_layer`` up to date with its selection; the selected objects in pick order."""
    key = (scene.session_uid, view_layer.name)
    selected = {ob.session_uid: ob for ob in view_layer.objects.selected}
    order = [uid for uid in _orders.get(key, ()) if uid in selected]
    active = view_layer.objects.active
    active_uid = active.session_uid if active is not None else 0
    known = set(order)
    added = [ob for uid, ob in selected.items() if uid not in known]
    added.sort(key=lambda ob: (ob.session_uid == active_uid, ob.name_full))
    order += [ob.session_uid for ob in added]
    if active_uid in selected and active_uid != _actives.get(key) and order[-1] != active_uid:
        order.remove(active_uid)
        order.append(active_uid)
    _orders[key] = order
    _actives[key] = active_uid
    return [selected[uid] for uid in order]


def ordered(context):
    """The selected objects of the context's view layer in pick order: the last one is Maya's lead."""
    return _sync(context.scene, context.view_layer)


def last(context):
    """The last picked of the selected objects (Maya's lead), or None when nothing is selected."""
    obs = ordered(context)
    return obs[-1] if obs else None


@persistent
def _on_depsgraph(scene, depsgraph):
    # selection and active-object changes update the Scene alone; edits that touch no Scene can't change them
    if depsgraph is None or not depsgraph.id_type_updated('SCENE'):
        return
    try:
        _sync(depsgraph.scene, depsgraph.view_layer)
    except (ReferenceError, AttributeError, RuntimeError):
        pass


@persistent
def _on_load(*_args):
    _orders.clear()
    _actives.clear()


_HANDLERS = (("depsgraph_update_post", _on_depsgraph), ("load_post", _on_load))


def register_handlers():
    for name, fn in _HANDLERS:
        handlers = getattr(bpy.app.handlers, name)
        if fn not in handlers:
            handlers.append(fn)


def unregister_handlers():
    for name, fn in _HANDLERS:
        handlers = getattr(bpy.app.handlers, name)
        while fn in handlers:
            handlers.remove(fn)
    _orders.clear()
    _actives.clear()
