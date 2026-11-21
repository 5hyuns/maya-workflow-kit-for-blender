"""#422 Isolate Select keys: Ctrl+1 isolates in the 3D View and the UV Editor on every platform, and on macOS Cmd+1
does the same (Maya's macOS hotkeys have both); no select-mode key is left on Ctrl+1 / Cmd+1 in front of them (a
vertex-mode switch there would stop a face click from picking the face). The macOS keymap data is built here by
running the kit's keymap generation as on macOS."""

import sys
from importlib import import_module

import kit

keymap = import_module(kit.MODULE + ".keymap")


def _data(platform):
    saved = sys.platform
    sys.platform = platform
    try:
        return keymap.generate_data()
    finally:
        sys.platform = saved


def _items(data, km, type_, **mods):
    want = {m: bool(mods.get(m)) for m in ("shift", "ctrl", "alt", "oskey")}
    out = []
    for name, _params, body in data:
        if name != km:
            continue
        for idname, ev, _props in body["items"]:
            if ev.get("type") != type_ or ev.get("value", "PRESS") != "PRESS" or ev.get("any"):
                continue
            if {m: bool(ev.get(m)) for m in want} == want:
                out.append(idname)
    return out


def _check(data, mod, label):
    for km, op in (("3D View", "allset.isolate"), ("UV Editor", "allset.uv_isolate")):
        got = _items(data, km, "ONE", **{mod: True})
        if op not in got:
            raise AssertionError(f"{label}: {km} {mod}+1 has no {op} ({got})")
    for km in ("Mesh", "UV Editor", "Object Mode", "Object Non-modal"):
        bad = [i for i in _items(data, km, "ONE", **{mod: True}) if i.endswith("select_mode")]
        if bad:
            raise AssertionError(f"{label}: {km} {mod}+1 still switches the select mode ({bad})")


def test_ctrl_one_isolates_on_windows_and_linux():
    for platform in ("win32", "linux"):
        data = _data(platform)
        _check(data, "ctrl", platform)
        if _items(data, "3D View", "ONE", oskey=True):
            raise AssertionError(f"{platform}: an OS-key+1 item was added")


def test_cmd_one_isolates_on_macos():
    data = _data("darwin")
    _check(data, "ctrl", "darwin")
    _check(data, "oskey", "darwin")
