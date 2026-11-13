"""The top bar, the Status Line and the dock tint redraw on every frame change, pose step and click in Maya mode.
What they ask on each redraw is found once per redraw, with the same answers: the Status Line glyphs' icon ids, the
menu bar's menu widths, the workspace dropdown's list, which dock panels show, and the dock's pixel reads."""

import itertools
import random
import types
from importlib import import_module

import bpy

import kit

status_icons = import_module(kit.MODULE + ".ui.status_icons")
status_line = import_module(kit.MODULE + ".ui.status_line")
menu_sets = import_module(kit.MODULE + ".ui.menu_sets")
ws_mod = import_module(kit.MODULE + ".ui.workspaces")
md = import_module(kit.MODULE + ".ui.maya_dock")
prefs_mod = import_module(kit.MODULE + ".preferences")


class _Count:
    def __init__(self, owner, name):
        self.owner, self.name, self.calls = owner, name, 0
        self.real = getattr(owner, name)

    def __enter__(self):
        def counted(*a, **k):
            self.calls += 1
            return self.real(*a, **k)
        setattr(self.owner, self.name, counted)
        return self

    def __exit__(self, *exc):
        setattr(self.owner, self.name, self.real)


class _Layout:
    """A stand-in UILayout: records menus with the width their row was given, props and operators. ``on_prop``
    stands in for what Blender does while it builds a property's field (an enum asks for its items and value)."""

    def __init__(self, log=None, on_prop=None):
        object.__setattr__(self, "log", [] if log is None else log)
        object.__setattr__(self, "on_prop", on_prop)
        object.__setattr__(self, "attrs", {})

    def _sub(self, *_a, **_k):
        return _Layout(self.log, self.on_prop)

    row = column = box = split = _sub

    def menu(self, idname, text=None, **kw):
        self.log.append(("menu", idname, self.attrs.get("ui_units_x")))

    def prop(self, owner, path, **kw):
        self.log.append(("prop", path))
        if self.on_prop is not None:
            self.on_prop(owner, path)

    def operator(self, idname, **kw):
        props = types.SimpleNamespace()
        self.log.append(("op", idname, kw.get("depress"), props))
        return props

    def __getattr__(self, name):
        return lambda *a, **k: self.log.append((name,) + a)

    def __setattr__(self, name, value):
        self.attrs[name] = value


def _ctx(**extra):
    c = bpy.context
    win = c.window_manager.windows[0]
    d = dict(area=types.SimpleNamespace(show_menus=True), screen=win.screen, window=win, scene=c.scene, mode=c.mode,
             preferences=c.preferences, window_manager=c.window_manager, workspace=win.workspace, region=None)
    d.update(extra)
    return types.SimpleNamespace(**d)


def _label(idname):
    return getattr(bpy.types, idname).bl_label


# --- Status Line glyphs ----------------------------------------------------------------------------------------

def test_glyph_icons_are_looked_up_once():
    names = sorted(status_icons.GLYPHS)[:12]
    first = [status_icons.icon(n) for n in names]
    pc = status_icons._collection()

    class _Gets:
        n = 0

        def get(self, key, default=None):
            _Gets.n += 1
            return pc.get(key, default)

        def __getattr__(self, name):
            return getattr(pc, name)

    real = status_icons._collection
    status_icons._collection = lambda: _Gets()
    try:
        again = [status_icons.icon(n) for n in names]
    finally:
        status_icons._collection = real
    # the same preview's icon, found without asking the preview collection again
    assert again == first, (again, first)
    assert again == [pc[f"{n}@{status_icons.icon_px()}"].icon_id for n in names]
    assert _Gets.n == 0, f"{_Gets.n} preview lookups for {len(names)} glyphs already shown"


# --- menu bar --------------------------------------------------------------------------------------------------

def _menus(log, names):
    ids = {menu_sets.menu_idname(n) for n in names}
    return [(e[1], e[2]) for e in log if e[0] == "menu" and e[1] in ids]


def test_menu_bar_sizes_each_menu_once():
    prefs = prefs_mod.get()
    names = menu_sets.menus_for_set(prefs.menu_set)
    want = [(menu_sets.menu_idname(n), menu_sets.menu_width_units(_label(menu_sets.menu_idname(n)), bpy.context))
            for n in names]
    # the whole bar (no region width: every menu inline)
    lay = _Layout()
    with _Count(menu_sets, "menu_width_units") as sized:
        status_line.draw_menu_bar_fit(lay, _ctx(), menu_set=True)
    assert _menus(lay.log, names) == want, (_menus(lay.log, names), want)
    assert sized.calls == len(names), f"{sized.calls} text sizes for {len(names)} menus"
    # a narrow bar: the menus that fit, then the » overflow
    widths, fixed, more = status_line.menu_bar_widths(bpy.context, names, True)
    width = fixed + more + sum(widths[:5]) + 2
    lay = _Layout()
    with _Count(menu_sets, "menu_width_units") as sized:
        status_line.draw_menu_bar_fit(lay, _ctx(region=types.SimpleNamespace(width=width)), menu_set=True)
    shown = _menus(lay.log, names)
    assert shown == want[:5], (shown, want[:5])
    assert ("menu", status_line.ALLSET_MT_menu_more.bl_idname, status_line.MENU_MORE_UNITS) in lay.log, lay.log
    assert sized.calls == len(names), f"{sized.calls} text sizes for {len(names)} menus"
    # the widths the fit used are the same as one measure per menu
    assert status_line.menu_bar_widths(bpy.context, names, True) == (widths, fixed, more)


# --- workspace dropdown ----------------------------------------------------------------------------------------

def test_workspace_field_reads_the_workspace_list_once():
    prefs = prefs_mod.get()
    was = prefs.maya_top_bar
    prefs.maya_top_bar = True
    wm = bpy.context.window_manager
    asked = {}

    def build_field(owner, path):
        # what Blender asks while it builds the Workspace dropdown: its items (twice) and its value
        if path == "allset_workspace":
            ctx = bpy.context
            asked["items"] = [status_line._workspaces(owner, ctx), status_line._workspaces(owner, ctx)]
            asked["value"] = status_line._get_workspace(owner)

    try:
        with bpy.context.temp_override(window=wm.windows[0]):
            lay = _Layout(on_prop=build_field)
            with _Count(ws_mod, "entries") as lists:
                status_line.draw_right(types.SimpleNamespace(layout=lay), _ctx())
            items, value = ws_mod.dropdown_items(None, None), ws_mod.dropdown_get(None)
    finally:
        prefs.maya_top_bar = was
    assert ("prop", "allset_workspace") in lay.log, lay.log
    assert asked["items"] == [items, items] and asked["value"] == value, (asked, items, value)
    assert lists.calls == 1, f"the workspace list was built {lists.calls} times for one draw of the field"
    # outside the top bar's draw the dropdown reads the list itself, as before
    assert status_line._workspaces(wm, bpy.context) == items and status_line._get_workspace(wm) == value


# --- dock panels shown -----------------------------------------------------------------------------------------

def test_visible_kinds_is_kind_visible_for_every_dock_state():
    areas = [types.SimpleNamespace(name=f"a{i}", as_pointer=lambda i=i: 1000 + i) for i in range(4)]
    roles = {}
    real_role = md.role
    md.role = lambda area: roles.get(getattr(area, "name", None))
    try:
        for stack, floating, want in itertools.product((False, True), itertools.chain.from_iterable(
                itertools.combinations(md.KINDS, n) for n in range(len(md.KINDS) + 1)), md.KINDS + ('BOGUS',)):
            roles.clear()
            if stack:
                roles["a0"] = 'STACK'
            for i, kind in enumerate(floating):
                roles[f"a{i + 1}"] = kind
            wm = types.SimpleNamespace(allset_dock=want, windows=[
                types.SimpleNamespace(screen=types.SimpleNamespace(areas=areas[:1])),
                types.SimpleNamespace(screen=types.SimpleNamespace(areas=areas[1:]))])
            got = md.visible_kinds(wm)
            ref = {k for k in md.KINDS if md.kind_visible(wm, k)}
            assert got == ref, (stack, floating, want, got, ref)
    finally:
        md.role = real_role


def test_status_line_looks_at_the_docks_once():
    lay = _Layout()
    with _Count(md, "floating_kinds") as looks:
        status_line.draw_status_line(lay, bpy.context)
    toggles = {e[3].editor: e[2] for e in lay.log
               if e[0] == "op" and e[1] == status_line.ALLSET_OT_editor_toggle.bl_idname}
    screen = bpy.context.screen
    assert toggles == {e: status_line.editor_shown(screen, e) for e, _d, _i in status_line.EDITORS}, toggles
    assert looks.calls == 1, f"the Status Line looked at every window's docks {looks.calls} times in one draw"


# --- dock tint pixel reads -------------------------------------------------------------------------------------

def test_dock_pixel_reads_give_the_same_values():
    """``_reds`` of a one-row / one-column RGBA byte read = the red values the per-pixel lists gave (a framebuffer
    read is [rows][columns][RGBA] bytes; the real reads are compared in the GUI test)."""
    rnd = random.Random(7)
    for h, w in ((1, 346), (412, 1), (1, 1)):
        data = bytes(rnd.randrange(256) for _ in range(h * w * 4))
        listed = [[list(data[(y * w + x) * 4:(y * w + x) * 4 + 4]) for x in range(w)] for y in range(h)]
        old = [px[0] for px in listed[0]] if h == 1 else [c[0][0] for c in listed]
        assert md._reds(data, h * w) == old, (h, w)
        assert md._reds(data + bytes(8), h * w) == old, "only the read's own pixels"
