"""#432 macOS Cmd keys: the kit's keymap data is made for macOS like Blender's own, after the Maya patches. Every
Ctrl key in it (Blender's kept ones and the kit's own) also has its Cmd copy, except the keys Blender leaves to macOS
(Cmd+H / M / W / Space / ...); no Cmd key is left of a Ctrl key the kit removed or replaced. Built here by running the
kit's keymap generation as on macOS."""

import sys
from importlib import import_module

import kit

keymap = import_module(kit.MODULE + ".keymap")

SYSTEM = {"H", "M", "SPACE", "W", "ACCENT_GRAVE", "PERIOD", "TAB"}       # plain Cmd+key left to macOS


def _data(platform):
    saved = sys.platform
    sys.platform = platform
    try:
        return keymap.generate_data()
    finally:
        sys.platform = saved


def _key(idname, ev, props, mod):
    e = {k: v for k, v in ev.items() if k not in ("ctrl", "oskey") and v not in (False, None)}
    return idname, tuple(sorted(e.items())), repr(props), bool(ev.get(mod))


def _left_to_system(ev):
    t = ev.get("type")
    return ((t in SYSTEM and not ev.get("alt") and not ev.get("shift"))
            or (t == "Q" and ev.get("alt") and not ev.get("shift")))


def test_every_ctrl_key_has_its_cmd_copy_and_no_cmd_key_is_orphaned():
    data = _data("darwin")
    missing, orphans = [], []
    for km, _params, body in data:
        items = body["items"]
        ctrl = {_key(i, e, p, "ctrl")[:3] for i, e, p in items if e.get("ctrl")}
        cmd = {_key(i, e, p, "oskey")[:3] for i, e, p in items if e.get("oskey")}
        for i, e, p in items:
            if e.get("ctrl") and not _left_to_system(e) and _key(i, e, p, "ctrl")[:3] not in cmd:
                missing.append((km, i, e))
            if e.get("oskey") and _key(i, e, p, "oskey")[:3] not in ctrl:
                orphans.append((km, i, e))
    assert not missing, missing[:10]
    assert not orphans, orphans[:10]


def test_kit_keys_get_cmd_and_removed_ctrl_keys_leave_none():
    data = _data("darwin")
    by_km = {km: body["items"] for km, _p, body in data}
    # a kit key on Ctrl answers Cmd too
    iso = [(i, e) for i, e, _p in by_km["3D View"] if i == "allset.isolate" and e.get("type") == "ONE"]
    assert {bool(e.get("oskey")) for _i, e in iso} == {True, False}, iso
    # the IC Ctrl+1 vertex mode the kit took out leaves no Cmd+1 copy
    # (Ctrl+Shift+1 = add vertex mode stays, with its Cmd copy)
    assert not [i for i, e, _p in by_km["Mesh"] if i == "mesh.select_mode" and e.get("type") == "ONE"
                and (e.get("oskey") or e.get("ctrl")) and not e.get("shift")]


def _oskey_items(data):
    return {(km, i, repr(sorted(e.items()))) for km, _p, body in data for i, e, _q in body["items"] if e.get("oskey")}


def test_other_platforms_have_no_cmd_copies():
    # the only Cmd keys there are the ones in Blender's own data on every platform (Generic Gizmo's)
    base = _oskey_items(import_module(kit.MODULE + ".keymap.ic_data").generate())
    for platform in ("win32", "linux"):
        extra = _oskey_items(_data(platform)) - base
        assert not extra, (platform, sorted(extra)[:5])
