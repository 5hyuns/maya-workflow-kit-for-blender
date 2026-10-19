"""Step 119: Maya colours on every Blender version. Blender 5.x has its own theme keys, so tools/make_theme.py writes
one preset per minor version (studio_grey.xml = 4.5, studio_grey_<5.m>.xml); docs/compat_5x.md "테마 차이"."""

import os
import sys
from importlib import import_module
from pathlib import Path

import bpy

import kit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import make_theme  # noqa: E402
import theme_xml_diff  # noqa: E402

compat = import_module(kit.MODULE + ".compat")
theme_mod = import_module(kit.MODULE + ".theme")
FOLDER = ROOT / "src" / "allset" / "theme"


def test_theme_file_for_this_blender():
    got = os.path.basename(compat.theme_file(str(FOLDER)))
    major, minor = bpy.app.version[:2]
    want = "studio_grey.xml" if (major, minor) == (4, 5) else f"studio_grey_{major}.{minor}.xml"
    assert got == want, (got, want)
    assert os.path.basename(theme_mod.THEME_FILE) == want


def test_every_version_file_matches_45_on_shared_keys():
    """A key 5.x shares with 4.5 (same path or moved per the 5.0 table) holds the 4.5 value."""
    base = theme_xml_diff.flatten(FOLDER / "studio_grey.xml")
    files = sorted(FOLDER.glob("studio_grey_*.xml"))
    assert [f.name for f in files] == ["studio_grey_5.0.xml", "studio_grey_5.1.xml", "studio_grey_5.2.xml"]
    for f in files:
        common, diffs = theme_xml_diff.compare(base, theme_xml_diff.flatten(f), make_theme.moved_table())
        assert common > 600, (f.name, common)
        # freestyle: 4.5 has an RGB edge mark, 5.x one RGBA mark for edges and faces (alpha from the face mark)
        rest = [d for d in diffs if not (d[1].endswith("view_3d.freestyle") and d[3].lower().startswith(d[2].lower()))]
        assert not rest, (f.name, rest)


def _walk(struct, prefix, out, depth=0):
    if depth > 6:
        return
    for prop in struct.bl_rna.properties:
        ident = prop.identifier
        if ident in ("rna_type", "name", "filepath"):
            continue
        path = f"{prefix}.{ident}" if prefix else ident
        if prop.type == 'POINTER':
            sub = getattr(struct, ident)
            if sub is not None:
                _walk(sub, path, out, depth + 1)
        elif prop.type == 'FLOAT' and prop.subtype in ('COLOR', 'COLOR_GAMMA'):
            out[path] = tuple(round(x, 3) for x in getattr(struct, ident))


def test_no_blender_default_left_on_new_keys():
    """Colour keys only this Blender has: the kit theme sets each, except the declared KEEP_FACTORY_5X."""
    if compat.IS_TARGET:
        return   # 4.5 is the reference
    bpy.ops.preferences.reset_default_theme()
    factory = {}
    _walk(bpy.context.preferences.themes[0], "", factory)
    theme_mod.apply()
    try:
        kit_vals = {}
        _walk(bpy.context.preferences.themes[0], "", kit_vals)
    finally:
        theme_mod.restore()
    base = theme_xml_diff.flatten(FOLDER / "studio_grey.xml")
    shared = {k.split(".", 1)[1] for k in base if k.startswith("Theme.")}
    moved_to = {new for new, _old in make_theme.moved_table()}
    new_keys = [k for k in factory if k not in shared and k not in moved_to]

    def by_rule(k):   # make_theme.apply_5x: a selected widget keeps its normal outline, as 4.5 drew it
        return k.endswith(".outline_sel") and kit_vals.get(k) == kit_vals.get(k[:-len("_sel")])
    left = sorted(k for k in new_keys
                  if kit_vals.get(k) == factory[k] and k not in make_theme.KEEP_FACTORY_5X and not by_rule(k))
    assert not left, left
    # the 5.0-moved colours are the 4.5 file's values (Maya's), not Blender's
    for new, old in make_theme.moved_table():
        if new in kit_vals and ("Theme." + old) in base:
            h = base["Theme." + old].lstrip("#")
            want = tuple(round(int(h[i:i + 2], 16) / 255, 3) for i in (0, 2, 4))
            assert all(abs(a - b) < 0.006 for a, b in zip(kit_vals[new][:3], want)), (new, kit_vals[new], want)
