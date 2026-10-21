"""Audit 128: inventory of every Maya tool / command menu item: how it is implemented and what its option box opens.
Run: blender -b --factory-startup --python tool_inventory.py -- out.tsv (sandbox BLENDER_USER_* with the kit)."""
import sys
from importlib import import_module

import addon_utils
import bpy

MODULE = "bl_ext.user_default.allset"
addon_utils.enable(MODULE, default_set=True)
import_module(MODULE + ".switch").set_mode(True, layout=False, theme=False)
ms = import_module(MODULE + ".ui.menu_sets")
md = import_module(MODULE + ".ui.menu_data")
mm = import_module(MODULE + ".ui.menu_map")
ow = import_module(MODULE + ".operators.option_windows")
sm = import_module(MODULE + ".ui.shelf_map")
sd = import_module(MODULE + ".ui.shelf_data")

TOPS = ("Mesh", "Edit Mesh", "Mesh Tools", "Mesh Display", "Select", "Modify", "Skeleton", "Skin", "Deform",
        "Constrain", "Control", "Key", "Edit", "Create", "UV", "Curves", "Surfaces", "Generate", "Effects", "Animate",
        "Visualize", "Cache")
out = open(sys.argv[-1], "w", encoding="utf-8")
out.write("path\tmaya_option_box\tmapped_kind\ttarget\timpl\toption_kind\twindow_fields\twindow_missing\n")
n = 0
for path, it in ms.iter_items():
    top = path.split("/")[0]
    if top not in TOPS or "/" in path and path.count("/") > 3:
        continue
    s = mm.spec(path)
    kind, target = (s[0], s[1]) if s else ("-", "-")
    if kind in ("menu", "pie"):
        continue
    tgt = target if isinstance(target, str) else repr(target)
    impl = "kit" if tgt.startswith("allset.") else ("-" if kind == "-" else "blender")
    try:
        ok = ms.option_kind(path)
    except Exception as ex:
        ok = f"error {ex!r}"
    w = ow.find_path(path)
    nf = len(w.fields) if w else 0
    miss = len(w.missing) if w else 0
    out.write(f"{path}\t{path in md.OPTION_BOXES}\t{kind}\t{tgt}\t{impl}\t{ok}\t{nf}\t{miss}\n")
    n += 1
out.close()
print("AUDIT rows", n)
bpy.ops.wm.quit_blender()
