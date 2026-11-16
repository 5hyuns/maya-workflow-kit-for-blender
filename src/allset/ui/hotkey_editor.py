# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya's Hotkey Editor window (Issue #121; Windows > Settings/Preferences > Hotkey Editor).

Maya's Hotkey Editor lists the commands of the current hotkey set with their keys, searches them by name or by
hotkey, filters by category, and lets a key be assigned. A key belongs to one command of a hotkey context: when the
key is already used, Maya warns, and once the user confirms, the other command loses it, so the new key works at once
(#381). The kit's list = Maya's standard hotkeys (``keymap/hotkey_rows``: Maya's standard hotkey list joined with
``keymap/mapping.py``) with what the kit binds for each one; a command with two Maya hotkeys (Undo: z and Ctrl+Z) has
a row per hotkey ("Undo", "Undo (2nd hotkey)"), each changing its own key.

A binding is changed the Blender way: on the items of ``wm.keyconfigs.user`` — the merged keymap Blender's own
Preferences > Keymap edits. The user keyconfig holds the kit's add-on items at the head of each keymap; changing
``type`` / modifiers there marks the keymap user-modified and leaves the add-on item as it was, so a row finds its
item through the add-on item of its operator, properties and Maya key (``KeyMapItems.find_match``) whatever keys the
user gave; the same add-on item in the other object-mode keymaps belongs to the row too (Y = Last Tool is one Maya
hotkey, bound in Object Mode and in Mesh). A key taken from another kit item leaves that item without a key (event
type ``NONE``): switching it off instead (``active``) would let Blender's keymap diff drop the item for the
identical Blender item the Maya keys switch off, and Blender mode would then lose that key.
``KeyMap.restore_item_to_default`` brings the Maya key back; the edits survive Maya mode off / on and restarts
(``keymap/user_keys``, #363); the kit writes no file — the edit is kept only by Blender's own Save Preferences /
auto-save (``preferences.is_dirty`` turns on), exactly like an edit in Blender's keymap editor. Only rows whose
binding is a kit add-on item (status KIT / IC with a check) can be changed; the active keyconfig is never touched.

Window = a ``marked_window`` kind "HOTKEY_EDITOR" (Properties Tool tab in its own window). Rows live in a
WindowManager collection rebuilt by the search / category updates and the edit operators, never in ``draw``.
"""

import json

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, IntProperty, StringProperty

from . import marked_window
from ..keymap import hotkey_import, hotkey_rows, mapping

KIND = "HOTKEY_EDITOR"
TITLE = "Hotkey Editor"
SET_NAME = "Maya Workflow Kit"          # names.PRODUCT; Maya shows the current hotkey set's name ("Maya_Default")
COLUMNS = (("Command", 0.36), ("Maya Hotkey", 0.17), ("Kit Hotkey", 0.24), ("Status", 1.0))
PERSIST_NOTE = "Changes are Blender keymap edits: Save Preferences (or auto-save) keeps them"
CONFIRM_NOTE = "Return: assign it here (they lose it)    Esc: cancel"

# Blender keymaps of one object mode each (keymap/maya_patches_mesh.MODE_KEYMAPS + Sculpt)
MODE_KEYMAPS = frozenset(("Object Mode", "Mesh", "Pose", "Curve", "Curves", "Armature", "Metaball", "Lattice",
                          "Particle", "Font", "Sculpt", "Weight Paint", "Vertex Paint", "Image Paint"))
# Keymaps an editor's key leaves alone: they run in every editor (or several), and in that editor its own item runs
# first, like a Maya editor hotkey over a global one
_SHARED = frozenset(mapping.CONTEXT_KEYMAPS["global"]) | {"Animation"}
_MAP_TYPES = {'KEYBOARD', 'MOUSE', 'NDOF', 'TEXTINPUT'}
_ROWS = []            # hotkey_rows.build_rows(), built once
_BY_INDEX = {}
_SIBLINGS = {}        # check signature -> [row]
_SAME_COMMAND = {}    # (command, context) -> [row] (a command with more than one Maya hotkey)
_BY_OP = {}           # check idname -> [row]
_PRIMARY = set()      # (check signature, Maya key) of the editable rows: an item another row has as its own
_OP_NAMES = {}        # idname -> the operator's name
_CATEGORIES = []      # EnumProperty items (kept referenced: Blender reads the strings later)

_IGNORE = {"MOUSEMOVE", "INBETWEEN_MOUSEMOVE", "TIMER", "TIMER_REPORT", "TIMERREGION", "NONE", "WINDOW_DEACTIVATE",
           "LEFT_CTRL", "RIGHT_CTRL", "LEFT_SHIFT", "RIGHT_SHIFT", "LEFT_ALT", "RIGHT_ALT", "OSKEY", "TEXTINPUT",
           "WHEELUPMOUSE", "WHEELDOWNMOUSE", "WHEELINMOUSE", "WHEELOUTMOUSE", "TRACKPADPAN", "TRACKPADZOOM",
           "MOUSEROTATE", "MOUSESMARTZOOM", "KM_TEXTINPUT"}
_CANCEL = {"ESC", "LEFTMOUSE", "RIGHTMOUSE", "MIDDLEMOUSE", "BUTTON4MOUSE", "BUTTON5MOUSE"}


def rows():
    if not _ROWS:
        _ROWS.extend(hotkey_rows.build_rows())
        _BY_INDEX.update((r["index"], r) for r in _ROWS)
        for r in _ROWS:
            if r["check"]:
                _SIBLINGS.setdefault(_sig(r["check"]), []).append(r)
                if r["editable"]:
                    _BY_OP.setdefault(r["check"][1], []).append(r)
                    _PRIMARY.add((_sig(r["check"]), hotkey_rows.event_key(r["event"])))
            if r["command"]:
                _SAME_COMMAND.setdefault((r["command"], r["context"]), []).append(r)
    return _ROWS


def row_of(index):
    rows()
    return _BY_INDEX.get(index)


def _sig(check):
    km, idname, props = check
    return km, idname, tuple(sorted((k, repr(v)) for k, v in props.items()))


def category_items(self, context):
    if not _CATEGORIES:
        _CATEGORIES.append(("ALL", "All Categories", "Every Maya hotkey"))
        _CATEGORIES.extend((c, c, f"Maya hotkeys of {c}") for c in hotkey_rows.categories(rows()))
    return _CATEGORIES


# --- live keymap items (wm.keyconfigs.user) ---------------------------------------------------------------------

def item_event(kmi):
    return {"type": kmi.type, "value": kmi.value, "any": kmi.any, "ctrl": bool(kmi.ctrl), "alt": bool(kmi.alt),
            "shift": bool(kmi.shift), "oskey": bool(kmi.oskey)}


def _norm(value):
    if isinstance(value, float):
        return round(value, 5)          # float32 storage: 0.8 reads back as 0.800000011920929
    if isinstance(value, (set, frozenset)):
        return frozenset(value)
    if not isinstance(value, str) and hasattr(value, "__len__"):
        return tuple(value)
    return value


def _prop(p, name):
    """An item property's value; an unset one = its RNA default, None for an unset enum (reading an unset enum whose
    default isn't an item prints a bpy.rna warning, e.g. allset.set_key ``channels``)."""
    rna = p.bl_rna.properties.get(name)
    if rna is None:
        raise AttributeError(name)
    if p.is_property_set(name):
        return getattr(p, name)
    if getattr(rna, "is_array", False):
        return tuple(rna.default_array)
    if rna.type == 'ENUM':
        # even ``rna.default`` warns when the default is no item; the kit's add-on items set what they compare
        return None
    return rna.default


def _props_match(kmi, want):
    p = kmi.properties
    for k, v in want.items():
        try:
            cur = _prop(p, k) if p is not None else None
        except AttributeError:
            return False
        if p is None or _norm(cur) != _norm(v):
            return False
    return True


def has_key(kmi):
    """The item runs on a key: switched on and not left without one (a key taken by another command)."""
    return kmi.active and kmi.type != 'NONE'


def _user_keymaps(context):
    kcs = context.window_manager.keyconfigs
    return kcs.user.keymaps if kcs.user is not None else None


def _addon_keymaps(context):
    kcs = context.window_manager.keyconfigs
    return kcs.addon.keymaps if kcs.addon is not None else None


def addon_index(context):
    """{(keymap name, idname): [(add-on KeyMap, item)]} of the add-on keyconfig, to look up many rows in one pass."""
    out = {}
    for akm in _addon_keymaps(context) or ():
        if akm.is_modal:
            continue
        for a in akm.keymap_items:
            out.setdefault((akm.name, a.idname), []).append((akm, a))
    return out


def _addon_candidates(context, km_name, idname, index):
    if index is not None:
        return index.get((km_name, idname), ())
    akms = _addon_keymaps(context)
    akm = akms.get(km_name) if akms is not None else None
    return [(akm, a) for a in akm.keymap_items if a.idname == idname] if akm is not None else ()


def _row_keymaps(km_name):
    """The row's keymap, then (an object-mode keymap) the other object modes' keymaps."""
    if km_name in MODE_KEYMAPS:
        return [km_name] + sorted(MODE_KEYMAPS - {km_name})
    return [km_name]


def row_items(context, row, index=None):
    """[(user KeyMap, user KeyMapItem)] that carry ``row``'s key, its own keymap's item first; [] when the kit doesn't
    bind it (Maya mode or the Maya keys off, a row the kit has no key for).

    The add-on item of the row's operator, properties and Maya key (add-on items keep the kit's key: the user's change
    is on the user keymap item ``find_match`` gives), in the row's keymap and, for an object-mode keymap, in the other
    object modes' keymaps (one Maya hotkey works in every mode: Y = Last Tool in Object Mode and in Mesh)."""
    out = []
    for name, _akm, _a, ukm, u in _row_pairs(context, row, index):
        if u is not None:
            out.append((ukm, u))
        elif name == row["check"][0]:
            return []
    return out


def row_gone(context, row, index=None):
    """[(add-on KeyMap, item)] of ``row``'s Maya keys that Blender's user keymap no longer shows: switched off or
    removed in Preferences > Keymap (a switched-off Maya key that is the same item as a Blender key the Maya keys
    switch off is shown as that Blender item, see keymap/user_keys)."""
    return [(akm, a) for _name, akm, a, _ukm, u in _row_pairs(context, row, index) if u is None]


def _row_pairs(context, row, index=None):
    """[(keymap name, add-on KeyMap, add-on item, user KeyMap, user item or None)] of ``row``, own keymap first."""
    if not row or not row["check"]:
        return []
    kms = _user_keymaps(context)
    if kms is None:
        return []
    rows()
    km_name, idname, want = row["check"]
    key = hotkey_rows.event_key(row["event"])
    out = []
    for name in _row_keymaps(km_name):
        if name != km_name and (_sig((name, idname, want)), key) in _PRIMARY:
            continue                # that mode's item is another Maya hotkey row's own
        ukm = kms.get(name)
        if ukm is None:
            continue
        for akm, a in _addon_candidates(context, name, idname, index):
            if hotkey_rows.event_key(item_event(a)) == key and _props_match(a, want):
                out.append((name, akm, a, ukm, ukm.keymap_items.find_match(akm, a)))
                break
    return out


def find_item(context, row, index=None):
    """(user KeyMap, KeyMapItem) of ``row``'s own keymap (a kit add-on item), else (KeyMap or None, None)."""
    items = row_items(context, row, index)
    if items:
        return items[0]
    kms = _user_keymaps(context)
    return (kms.get(row["check"][0]) if kms is not None and row and row["check"] else None), None


def editable_item(context, row, index=None):
    return find_item(context, row, index)


def kit_name(row):
    """The kit command's own name ("Last Tool" for NonSacredTool), "" for a Blender operator or an unknown one."""
    if not row or not row["check"] or not row["check"][1].startswith("allset."):
        return ""
    idname = row["check"][1]
    name = _OP_NAMES.get(idname)
    if name is None:
        name = ""
        module, _dot, op = idname.partition(".")
        try:
            name = getattr(getattr(bpy.ops, module), op).get_rna_type().name
        except (AttributeError, KeyError, RuntimeError):
            pass
        if name:
            _OP_NAMES[idname] = name
    return name


def key_text(kmi):
    """The kit key of an item: "Ctrl+Z", "Ctrl+Z (off)" when switched off, "—" when its key was taken."""
    if kmi.type == 'NONE':
        return "—"
    text = hotkey_rows.event_text(item_event(kmi))
    return text if kmi.active else text + " (off)"


def kit_text(context, row, index=None):
    """The list's Kit Hotkey cell ("—" when the kit has no key for it or its key was taken, "(off)" when it is
    switched off; " *" = changed)."""
    if not row["editable"]:
        return "—"
    items = row_items(context, row, index)
    if not items:
        gone = row_gone(context, row, index)
        return hotkey_rows.event_text(item_event(gone[0][1])) + " (off) *" if gone else "—"
    text = key_text(items[0][1])
    return text + " *" if any(k.is_user_modified for _km, k in items) else text


def scope(row, own=()):
    """Blender keymaps one key of ``row``'s Maya context reaches (``own`` = the keymaps of the row's items): for a
    global key every keymap Blender runs in the 3D View (each object mode's, 3D View, Screen, Window...), for an
    editor's key that editor's own keymaps. Keys of different object modes never meet."""
    own = list(own) or ([row["check"][0]] if row["check"] else [])
    if row["context"] == "global":
        names = list(mapping.CONTEXT_KEYMAPS["global"]) + sorted(MODE_KEYMAPS)
    else:
        names = [n for n in mapping.CONTEXT_KEYMAPS.get(row["context"], ()) if n not in _SHARED]
    names = list(dict.fromkeys(own + names))
    if MODE_KEYMAPS.intersection(own):
        names = [n for n in names if n in own or n not in MODE_KEYMAPS]
    return names


def clashes(context, row, event, items=None, exclude=None):
    """[(keymap name, user KeyMapItem)] of the active items in ``scope`` that a press of ``event`` also runs, the
    row's own items (``items``, found when None) and ``exclude`` left out."""
    kms = _user_keymaps(context)
    if kms is None:
        return []
    if items is None:
        items = row_items(context, row)
    own = {k.as_pointer() for _km, k in items}
    if exclude is not None:
        own.add(exclude.as_pointer())
    ev = dict(event, value=event.get("value", "PRESS"))
    out = []
    for name in scope(row, [km.name for km, _k in items]):
        km = kms.get(name)
        if km is None:
            continue
        out.extend((name, k) for k in km.keymap_items
                   if has_key(k) and k.map_type in _MAP_TYPES and k.as_pointer() not in own
                   and hotkey_rows.same_event(item_event(k), ev))
    return out


def _owner(context, km_name, kmi):
    """The Maya hotkey row whose item ``kmi`` (of keymap ``km_name``) is, else None."""
    rows()
    p = kmi.as_pointer()
    for r in _BY_OP.get(kmi.idname, ()):
        if km_name in _row_keymaps(r["check"][0]) and any(k.as_pointer() == p for _km, k in row_items(context, r)):
            return r
    return None


def named(context, found):
    """[(keymap name, command)] of ``clashes``: a Maya hotkey row's label, else the item's own name."""
    out = []
    for name, k in found:
        r = _owner(context, name, k)
        out.append((name, r["label"] if r is not None else (k.name or k.idname)))
    return out


def describe(pairs):
    """'NonSacredTool (Object Mode, Mesh), Split (Mesh)' of [(keymap name, command)]."""
    groups = {}
    for km, label in pairs:
        groups.setdefault(label, []).append(km)
    return ", ".join(f"{label} ({', '.join(dict.fromkeys(kms))})" for label, kms in groups.items())


def _is_kit(context, km_name, kmi, ptrs):
    """``kmi`` (a user keymap item) is one of the Maya keys (an add-on item of the kit)."""
    akms, ukms = _addon_keymaps(context), _user_keymaps(context)
    akm = akms.get(km_name) if akms is not None else None
    ukm = ukms.get(km_name) if ukms is not None else None
    if akm is None or ukm is None:
        return False
    p = kmi.as_pointer()
    for a in akm.keymap_items:
        if a.idname == kmi.idname and a.as_pointer() in ptrs:
            u = ukm.keymap_items.find_match(akm, a)
            if u is not None and u.as_pointer() == p:
                return True
    return False


def conflicts(context, row, event, exclude=None):
    """[(keymap name, command)] of the items that already use ``event`` in the row's Maya context."""
    return named(context, clashes(context, row, event, exclude=exclude))


def take(context, row, event, items=None, changed_only=False):
    """Maya: a key belongs to one command of a context, so giving it to ``row`` takes it from the kit items that
    use it there: they are left without a key (event type ``NONE``; Restore gives it back).
    ``changed_only``: only items whose key the user changed. Returns [(keymap name, command)] that lost it; the
    caller updates the keyconfigs. Keys that aren't the kit's (another add-on's, the user's own) are left alone."""
    from .. import keymap as kit_keymap
    ptrs = kit_keymap.kit_item_pointers()
    found = [(n, k) for n, k in clashes(context, row, event, items)
             if (not changed_only or k.is_user_modified) and _is_kit(context, n, k, ptrs)]
    taken = named(context, found)
    for _n, k in found:
        k.type = 'NONE'
    return taken


def assign(context, row, event):
    """Bind ``row``'s kit items to ``event`` (type + modifiers) in the user keyconfig; the kit items of the row's
    Maya context that used it lose it (``take``). Returns (ok, [(keymap name, command)] that lost it)."""
    _bring_back(context, row)
    items = row_items(context, row)
    if not items:
        return False, []
    taken = take(context, row, dict(event, value=items[0][1].value), items)
    for _km, kmi in items:
        if not kmi.active:          # switched off in Preferences > Keymap: a new key turns it on
            kmi.active = True
        kmi.type = event["type"]
        for m in hotkey_rows.MODIFIERS:
            setattr(kmi, m, bool(event.get(m)))
    context.window_manager.keyconfigs.update()
    return True, taken


def unbind(context, row):
    """Remove ``row``'s key (its kit items left without one). True if the row has kit items."""
    items = row_items(context, row)
    for _km, kmi in items:
        if kmi.type != 'NONE':
            kmi.type = 'NONE'
    if items:
        context.window_manager.keyconfigs.update()
    return bool(items)


def _bring_back(context, row):
    """Give ``row``'s Maya keys that Blender's keymap no longer shows (``row_gone``) the kit's key again. True if
    there were any."""
    gone = row_gone(context, row)
    if not gone:
        return False
    from .. import keymap as kit_keymap
    from ..keymap import user_keys
    kcs = context.window_manager.keyconfigs
    ptrs = kit_keymap.kit_item_pointers()
    where = {}
    for akm, a in gone:
        where.setdefault((akm.name, akm.space_type, akm.region_type), set()).add(a.as_pointer())
    for (name, space, region), back in where.items():
        user_keys.restore_items(kcs, ptrs, name, space, region, back)
    return True


def restore(context, row):
    """Give ``row``'s kit items their Maya key back (Blender's Restore Item; a key switched off or removed in
    Preferences > Keymap too); a key the user gave another command moves back here. True if something was
    restored."""
    back = _bring_back(context, row)
    changed = [(km, k) for km, k in row_items(context, row) if k.is_user_modified]
    if not changed and not back:
        return False
    for km, kmi in changed:
        km.restore_item_to_default(kmi)
    kcs = context.window_manager.keyconfigs
    kcs.update()
    items = row_items(context, row)
    if items and take(context, row, item_event(items[0][1]), items, changed_only=True):
        kcs.update()
    return True


def changed_rows(context):
    index = addon_index(context)
    return [row for row in rows() if row["editable"]
            and (any(k.is_user_modified for _km, k in row_items(context, row, index))
                 or row_gone(context, row, index))]


def restore_all(context):
    """Give every Maya key the kit's key again (changed, removed or taken by another key; the user's edits of
    other items stay). Returns how many items were restored."""
    from .. import keymap as kit_keymap
    ptrs = kit_keymap.kit_item_pointers()
    akms, ukms = _addon_keymaps(context), _user_keymaps(context)
    if not ptrs or akms is None or ukms is None:
        return 0
    items, gone = {}, []
    for akm in akms:
        if akm.is_modal:
            continue
        ukm = ukms.find(akm.name, space_type=akm.space_type, region_type=akm.region_type)
        if ukm is None or not ukm.is_user_modified:
            continue
        for a in akm.keymap_items:
            if a.as_pointer() in ptrs:
                u = ukm.keymap_items.find_match(akm, a)
                if u is None:               # switched off or removed in Preferences > Keymap (user_keys)
                    gone.append((akm.name, akm.space_type, akm.region_type))
                elif u.is_user_modified:
                    items[u.as_pointer()] = (ukm, u)      # rows of several Maya contexts can share one item
    for ukm, u in items.values():
        ukm.restore_item_to_default(u)
    kcs = context.window_manager.keyconfigs
    if items:
        kcs.update()
    if gone:
        from ..keymap import user_keys
        for where in dict.fromkeys(gone):
            user_keys.reset_keymap(kcs, ptrs, *where)
        kcs.update()
    return len(items) + len(gone)


# --- the list ---------------------------------------------------------------------------------------------------

class ALLSET_PG_hotkey_row(bpy.types.PropertyGroup):
    index: IntProperty()            # hotkey_data index
    command: StringProperty()
    maya_key: StringProperty()
    kit_key: StringProperty()
    status: StringProperty()
    editable: BoolProperty()


def _wm(context):
    return context.window_manager


def live_events(context, row, index=None):
    _km, kmi = find_item(context, row, index) if row["editable"] else (None, None)
    return [item_event(kmi)] if kmi is not None and has_key(kmi) else []


def refresh(context):
    """Rebuild the shown rows from the search text, search mode and category (keeps the selected command)."""
    wm = _wm(context)
    coll = wm.allset_hk_rows
    keep = coll[wm.allset_hk_active].index if 0 <= wm.allset_hk_active < len(coll) else -1
    text, by = wm.allset_hk_search, wm.allset_hk_by
    index = addon_index(context)
    live, names = {}, {}
    if by == "HOTKEY" and text.strip():
        live = {r["index"]: live_events(context, r, index) for r in rows() if r["editable"]}
    elif text.strip():
        names = {r["index"]: [kit_name(r)] for r in rows() if r["editable"]}
    shown = hotkey_rows.search(rows(), text, by, wm.allset_hk_category, live, names)
    coll.clear()
    active = 0
    for i, r in enumerate(shown):
        item = coll.add()
        item.index, item.command, item.maya_key = r["index"], r["label"], r["maya_key"]
        item.kit_key, item.status, item.editable = kit_text(context, r, index), r["status_text"], r["editable"]
        if r["index"] == keep:
            active = i
    wm.allset_hk_active = active if shown else -1
    marked_window.redraw(context, KIND)


def _refresh_update(self, context):
    refresh(context)


def selected_row(context):
    wm = _wm(context)
    coll = wm.allset_hk_rows
    if 0 <= wm.allset_hk_active < len(coll):
        return row_of(coll[wm.allset_hk_active].index)
    return None


class ALLSET_UL_hotkeys(bpy.types.UIList):
    """Maya's Hotkey Editor list: command, Maya key, the kit's key, status"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0):
        cells = _columns(layout)
        cells[0].label(text=item.command)
        cells[1].label(text=item.maya_key)
        cells[2].label(text=item.kit_key)
        cells[3].label(text=item.status)

    def filter_items(self, context, data, propname):
        return [], []      # the collection is already filtered (refresh)


def _columns(layout):
    out, rest = [], layout
    for _name, factor in COLUMNS[:-1]:
        split = rest.split(factor=factor / max(1e-6, 1.0 - sum(f for _n, f in COLUMNS[:len(out)])))
        out.append(split.row())
        rest = split
    out.append(rest.row())
    return out


# --- operators --------------------------------------------------------------------------------------------------

class ALLSET_OT_hotkey_editor(bpy.types.Operator):
    """Open the Hotkey Editor: Maya's hotkeys, the kit's keys for them, search and assign new keys"""
    bl_idname = "allset.hotkey_editor"
    bl_label = "Hotkey Editor"

    def execute(self, context):
        if context.window is None:
            return {'CANCELLED'}
        refresh(context)
        if marked_window.open_window(context, KIND) is None:
            from . import window_places
            if not window_places.deferred():     # opens on a later tick (#203)
                self.report({'ERROR'}, "Could not open the Hotkey Editor window")
            return {'CANCELLED'}
        return {'FINISHED'}


class ALLSET_OT_hotkey_assign(bpy.types.Operator):
    """Assign a new key to this command: press it (with Ctrl / Alt / Shift); a key in use asks first, Esc cancels"""
    bl_idname = "allset.hotkey_assign"
    bl_label = "Assign New Hotkey"
    bl_options = {'INTERNAL'}

    row: IntProperty(default=-1, options={'SKIP_SAVE'})
    key: StringProperty(options={'SKIP_SAVE'})        # event type; empty = capture the next key press
    ctrl: BoolProperty(options={'SKIP_SAVE'})
    alt: BoolProperty(options={'SKIP_SAVE'})
    shift: BoolProperty(options={'SKIP_SAVE'})
    oskey: BoolProperty(options={'SKIP_SAVE'})

    def _row(self, context):
        return row_of(self.row) if self.row >= 0 else selected_row(context)

    def _event(self):
        return {"type": self.key, "ctrl": self.ctrl, "alt": self.alt, "shift": self.shift, "oskey": self.oskey}

    def execute(self, context):
        row = self._row(context)
        if row is None or not self.key:
            return {'CANCELLED'}
        event = self._event()
        ok, taken = assign(context, row, event)
        if not ok:
            self.report({'WARNING'}, f"{row['label'] or row['maya_key']}: not a kit key binding, can't be changed")
            return {'CANCELLED'}
        refresh(context)
        text = hotkey_rows.event_text(event)
        _km, kmi = find_item(context, row)
        left = conflicts(context, row, item_event(kmi)) if kmi is not None else []
        if left:        # keys that aren't the kit's (another add-on's, the user's own) stay
            self.report({'WARNING'}, f"{text} is also used by " + describe(left))
        else:
            from .. import results
            results.result(self, f"{row['label']}: {text}" + (f" (taken from {describe(taken)})" if taken else ""))
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.key:
            return self.execute(context)
        row = self._row(context)
        if row is None or (editable_item(context, row)[1] is None and not row_gone(context, row)):
            self.report({'WARNING'}, "Pick a command the kit binds (status Kit / Blender (IC))")
            return {'CANCELLED'}
        self.row = row["index"]
        _wm(context).allset_hk_capture = True
        _wm(context).allset_hk_pending = ""
        marked_window.redraw(context, KIND)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _end(self, context):
        _wm(context).allset_hk_capture = False
        _wm(context).allset_hk_pending = ""
        marked_window.redraw(context, KIND)

    def modal(self, context, event):
        etype = event.type
        if etype in _IGNORE or event.value != 'PRESS':
            return {'RUNNING_MODAL'}
        if self.key and etype in {'RET', 'NUMPAD_ENTER'}:      # confirmed: the used key moves here
            self._end(context)
            return self.execute(context)
        if etype in _CANCEL:
            self._end(context)
            return {'CANCELLED'}
        if etype not in hotkey_rows.KEYBOARD:
            return {'RUNNING_MODAL'}
        self.key = etype
        self.ctrl, self.alt, self.shift, self.oskey = event.ctrl, event.alt, event.shift, event.oskey
        row = self._row(context)
        items = row_items(context, row)
        used = clashes(context, row, dict(self._event(), value=items[0][1].value), items) if items else []
        if used:        # like Maya: warn first; another key press tries that key instead
            text = hotkey_rows.event_text(self._event())
            _wm(context).allset_hk_pending = f"{text} is used by: {describe(named(context, used))}"
            marked_window.redraw(context, KIND)
            return {'RUNNING_MODAL'}
        self._end(context)
        return self.execute(context)


class ALLSET_OT_hotkey_take(bpy.types.Operator):
    """Take this command's key from the other commands that use it, like Maya (their Restore gives it back)"""
    bl_idname = "allset.hotkey_take"
    bl_label = "Remove From Others"
    bl_options = {'INTERNAL'}

    row: IntProperty(default=-1, options={'SKIP_SAVE'})

    def execute(self, context):
        row = row_of(self.row) if self.row >= 0 else selected_row(context)
        items = row_items(context, row) if row is not None else []
        if not items or not has_key(items[0][1]):
            return {'CANCELLED'}
        ev = item_event(items[0][1])
        taken = take(context, row, ev, items)
        if not taken:
            return {'CANCELLED'}
        context.window_manager.keyconfigs.update()
        refresh(context)
        from .. import results
        results.result(self, f"{hotkey_rows.event_text(ev)}: taken from {describe(taken)}")
        return {'FINISHED'}


class ALLSET_OT_hotkey_restore(bpy.types.Operator):
    """Give this command its Maya hotkey back"""
    bl_idname = "allset.hotkey_restore"
    bl_label = "Restore"
    bl_options = {'INTERNAL'}

    row: IntProperty(default=-1, options={'SKIP_SAVE'})
    all: BoolProperty(name="All", options={'SKIP_SAVE'})

    def execute(self, context):
        from .. import results
        if self.all:
            n = restore_all(context)
            refresh(context)
            results.result(self, f"Restored {n} Maya hotkey(s)")
            return {'FINISHED'}
        row = row_of(self.row) if self.row >= 0 else selected_row(context)
        if row is None or not restore(context, row):
            return {'CANCELLED'}
        refresh(context)
        results.result(self, f"{row['label']}: {row['maya_key']}")
        return {'FINISHED'}


def import_hotkeys(context, text):
    """Apply a Maya hotkey set file's bindings to the kit rows. Returns (changed, skipped bindings)."""
    bindings, names = hotkey_import.parse(text)
    changes, skipped = hotkey_import.plan(rows(), bindings, names, key_of=hotkey_rows.event_key)
    done = 0
    for row, event in changes:
        ok, _clash = assign(context, row, event)
        if ok:
            done += 1
        else:
            skipped.append(({"key": row["maya_key"], "name": row["command"]}, "the kit key can't be changed here"))
    return done, skipped


class ALLSET_OT_hotkey_import(bpy.types.Operator):
    """Import a hotkey set exported from Maya's Hotkey Editor (.mhk) or the kit's Export (.json): its keys replace
    the kit keys of the same commands (only key bindings are read; nothing in the file is run)"""
    bl_idname = "allset.hotkey_import"
    bl_label = "Import..."
    bl_options = {'INTERNAL'}

    filepath: StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})
    filter_glob: StringProperty(default="*.mhk;*.mel;*.txt;*.json", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        try:
            with open(self.filepath, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            self.report({'ERROR'}, f"Could not read {self.filepath}: {exc}")
            return {'CANCELLED'}
        from .. import results, settings_io
        if text.lstrip().startswith("{"):           # a kit settings file: only its hotkeys
            try:
                lines = settings_io.apply(context, json.loads(text), ("hotkeys",))
            except ValueError as exc:
                self.report({'ERROR'}, f"Could not import {self.filepath}: {exc}")
                return {'CANCELLED'}
            refresh(context)
            results.result(self, "Imported " + ("; ".join(lines) if lines else "no hotkeys"))
            return {'FINISHED'}
        done, skipped = import_hotkeys(context, text)
        refresh(context)
        for b, reason in skipped[:20]:
            print(f"Hotkey import: {b.get('key')} {b.get('name')}: {reason}")
        msg = f"Imported {done} hotkey{'s' if done != 1 else ''}"
        if skipped:
            msg += f"; {len(skipped)} left out (see the system console)"
        results.result(self, msg)
        return {'FINISHED'}


class ALLSET_OT_hotkey_blender_prefs(bpy.types.Operator):
    """Open Blender's Preferences > Keymap (every Blender and add-on key)"""
    bl_idname = "allset.hotkey_blender_prefs"
    bl_label = "Blender Keymap Preferences"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return bpy.ops.screen.userpref_show('INVOKE_DEFAULT', section='KEYMAP')


# --- the window -------------------------------------------------------------------------------------------------

def _details(layout, context, row):
    box = layout.box()
    col = box.column(align=True)
    col.label(text=f"{row['label']}" + (f"  /  {row['release']} (release)" if row["release"] else ""))
    col.label(text=f"Maya hotkey: {row['maya_key']}    Context: {row['context']}"
                   + (f"    Category: {row['category']}" if row["category"] else ""))
    items = row_items(context, row) if row["editable"] else []
    if row["check"]:
        km_name, idname, props = row["check"]
        args = ", ".join(f"{k}={v!r}" for k, v in props.items())
        where = ", ".join(km.name for km, _k in items) or km_name
        name = kit_name(row)
        col.label(text="Kit: " + (f"{name} = " if name else "") + idname + (f"({args})" if args else "")
                       + f"  in  {where}")
    else:
        col.label(text=f"Kit: {row['status_text']}" + (f" (step {row['step']})" if row["step"] else ""))
    same = _SAME_COMMAND.get((row["command"], row["context"]), ()) if row["command"] else ()
    if len(same) > 1:
        col.label(text=f"{row['command']} has {len(same)} Maya hotkeys ({', '.join(r['maya_key'] for r in same)}): "
                       f"this row changes {row['maya_key']} only")
    if row["check"]:
        key = hotkey_rows.event_key(row["event"])
        shared = [r for r in _SIBLINGS.get(_sig(row["check"]), ())
                  if r["index"] != row["index"] and hotkey_rows.event_key(r["event"]) == key]
        if shared:
            col.label(text="Same kit key as " + ", ".join(f"{r['label']} ({r['context']})" for r in shared))
    if row["note"] and row["note"].isascii():     # mapping.py notes are partly Korean dev notes: not shown
        col.label(text=row["note"])
    if not row["editable"]:
        return
    gone = row_gone(context, row) if not items else []
    if not items and not gone:
        box.label(text="Kit hotkey: — (Maya mode off or the item was removed)", icon='INFO')
        return
    kmi = items[0][1] if items else gone[0][1]
    ev = item_event(kmi)
    changed = bool(gone) or any(k.is_user_modified for _km, k in items)
    wm = _wm(context)
    line = box.row(align=True)
    shown = key_text(kmi) if items else hotkey_rows.event_text(ev) + " (off)"
    line.label(text="Kit hotkey: " + ("none" if shown == "—" else shown) + ("  (changed)" if changed else ""))
    act = line.row(align=True)
    if wm.allset_hk_capture:
        act.alert = True
        act.label(text="Press a key... (Esc cancels)")
    else:
        act.operator(ALLSET_OT_hotkey_assign.bl_idname, text="Assign New Hotkey...").row = row["index"]
    sub = act.row(align=True)
    sub.enabled = changed
    sub.operator(ALLSET_OT_hotkey_restore.bl_idname, text="Restore").row = row["index"]
    if wm.allset_hk_capture and wm.allset_hk_pending:
        warn = box.column(align=True)
        warn.alert = True
        warn.label(text=wm.allset_hk_pending, icon='ERROR')
        warn.label(text=CONFIRM_NOTE, icon='BLANK1')
        return
    found = clashes(context, row, ev, items) if items and has_key(kmi) else []
    if found:
        from .. import keymap as kit_keymap
        ptrs = kit_keymap.kit_item_pointers()
        warn = box.row(align=True)
        warn.label(text="Also used by: " + describe(named(context, found)), icon='ERROR')
        if any(_is_kit(context, n, k, ptrs) for n, k in found):
            warn.operator(ALLSET_OT_hotkey_take.bl_idname, text="Remove From Others").row = row["index"]


class ALLSET_PT_hotkey_editor(bpy.types.Panel):
    """Maya's Hotkey Editor (a marked Properties Tool tab in its own window)"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_label = "Hotkey Editor"
    bl_options = {'HIDE_HEADER'}
    bl_order = -300

    @classmethod
    def poll(cls, context):
        return marked_window.context_kind(context) == KIND

    def draw(self, context):
        wm = _wm(context)
        layout = self.layout
        top = layout.row(align=True)
        top.label(text=f"Hotkey Set: {SET_NAME}")
        top.operator(ALLSET_OT_hotkey_import.bl_idname, icon='IMPORT')
        op = top.operator("allset.settings_export", text="Export...", icon='EXPORT')
        op.preferences = op.shelves = op.marking_menus = False
        from .. import preferences
        try:
            top.prop(preferences.get(context), "keymap_set")     # Maya keys or the Blender keymap (#309)
        except KeyError:
            pass
        top.operator(ALLSET_OT_hotkey_blender_prefs.bl_idname, icon='PREFERENCES')
        search = layout.row(align=True)
        search.prop(wm, "allset_hk_by", text="")
        search.prop(wm, "allset_hk_search", text="", icon='VIEWZOOM')
        search.prop(wm, "allset_hk_category", text="")
        head = _columns(layout.row())
        for cell, (name, _f) in zip(head, COLUMNS):
            cell.label(text=name)
        layout.template_list("ALLSET_UL_hotkeys", "", wm, "allset_hk_rows", wm, "allset_hk_active", rows=9)
        layout.label(text=f"{len(wm.allset_hk_rows)} of {len(rows())} Maya hotkeys")
        row = selected_row(context)
        if row is not None:
            _details(layout, context, row)
        layout.label(text=PERSIST_NOTE, icon='INFO')
        bottom = layout.row(align=True)
        bottom.operator(ALLSET_OT_hotkey_restore.bl_idname, text="Restore All Maya Hotkeys").all = True
        bottom.operator("allset.marked_window_close", text="Close")


classes = (ALLSET_PG_hotkey_row, ALLSET_UL_hotkeys, ALLSET_OT_hotkey_editor, ALLSET_OT_hotkey_assign,
           ALLSET_OT_hotkey_take, ALLSET_OT_hotkey_restore, ALLSET_OT_hotkey_import, ALLSET_OT_hotkey_blender_prefs,
           ALLSET_PT_hotkey_editor)

_WM_PROPS = ("allset_hk_rows", "allset_hk_active", "allset_hk_search", "allset_hk_by", "allset_hk_category",
             "allset_hk_capture", "allset_hk_pending")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.types.WindowManager
    wm.allset_hk_rows = CollectionProperty(type=ALLSET_PG_hotkey_row)
    wm.allset_hk_active = IntProperty(name="Hotkey", default=-1)
    wm.allset_hk_search = StringProperty(name="Search", update=_refresh_update, options={'TEXTEDIT_UPDATE'},
                                         description="Search the Maya hotkeys by command name or by hotkey")
    wm.allset_hk_by = EnumProperty(name="Search by", update=_refresh_update, default="NAME",
                                   items=(("NAME", "Search by Name", "Find commands whose name contains the text"),
                                          ("HOTKEY", "Search by Hotkey", "Find commands bound to a key "
                                                                         "(e.g. Ctrl+Z, Shift+Q, F8)")))
    wm.allset_hk_category = EnumProperty(name="Category", items=category_items, update=_refresh_update)
    wm.allset_hk_capture = BoolProperty(name="Capturing a Key")
    wm.allset_hk_pending = StringProperty(name="Key in Use")     # the captured key's warning, waiting for Return


def unregister():
    for name in _WM_PROPS:
        if hasattr(bpy.types.WindowManager, name):
            delattr(bpy.types.WindowManager, name)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
