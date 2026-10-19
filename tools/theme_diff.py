"""Factory theme of each Blender version, key by key (step 119).

    python tools/theme_diff.py                    # 4.5 + every portable 5.x in allset_blenders -> tmp/theme_diff/
    python tools/theme_diff.py --md               # also print the markdown section for 

In each Blender (`-b --factory-startup`, user dirs in tmp/build_env): reset the theme to the factory default and
dump every theme value as `path = value` (the struct tree under Preferences.themes[0], the same tree Blender's
theme preset XML writes). Then diff the key sets against 4.5: keys added, keys removed, and removed keys whose
leaf name moved somewhere else (renamed / moved, with the 5.0 migration table of src/allset/theme MOVED).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tmp" / "theme_diff"
PORTABLE = Path(os.environ.get("ALLSET_BLENDERS", r"C:\Users\ohnsk\AppData\Local\allset_blenders"))


def blenders():
    sys.path.insert(0, str(ROOT / "tools"))
    import build
    out = [("4.5", build.DEFAULT_BLENDER)]
    for d in sorted(PORTABLE.glob("blender-*-windows-x64")):
        out.append((d.name.split("-")[1], str(d / "blender.exe")))
    return out


# ---------------------------------------------------------------- in Blender
def walk(struct, prefix, out, depth=0):
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
                walk(sub, path, out, depth + 1)
        elif prop.type == 'COLLECTION':
            continue
        else:
            v = getattr(struct, ident)
            try:
                v = [round(x, 4) for x in v]
            except TypeError:
                v = round(v, 4) if isinstance(v, float) else v
            out[path] = v


def dump(path):
    import bpy
    bpy.ops.preferences.reset_default_theme()
    out = {}
    walk(bpy.context.preferences.themes[0], "", out)
    for i, style in enumerate(bpy.context.preferences.ui_styles):
        walk(style, f"ui_styles[{i}]", out)
    Path(path).write_text(json.dumps(out, indent=0, sort_keys=True), encoding="utf-8")
    print(f"theme_diff: {len(out)} keys -> {path}")


# ---------------------------------------------------------------- outside
def leaf(key):
    return key.rsplit(".", 1)[-1]


def diff(base, other, moved):
    added = sorted(set(other) - set(base))
    removed = sorted(set(base) - set(other))
    old_to_new = {old: new for new, old in moved}
    # one 5.x value replaces the same setting of several editors: the table names one source per value, so a
    # removed key whose path after the editor matches a table source counts as merged too
    tails = {old.split(".", 1)[1]: new for new, old in moved}
    renamed = []
    for k in removed:
        new = old_to_new.get(k) or tails.get(k.split(".", 1)[1] if "." in k else k)
        if new is not None and new in other:
            renamed.append((k, new))
    gone = [k for k in removed if k not in dict(renamed)]
    return added, removed, renamed, gone


def moved_table():
    """MOVED of src/allset/theme (the 5.0 migration table), read from its source: the module needs bpy."""
    src = (ROOT / "src" / "allset" / "theme" / "__init__.py").read_text(encoding="utf-8")
    start = src.index("_ANIM = (")
    end = src.index("\n)\n", src.index("MOVED = (")) + 3
    ns = {}
    exec(src[start:end], ns)
    return ns["MOVED"]


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / "tools"))
    import build
    data = {}
    for ver, exe in blenders():
        path = OUT / f"factory_{ver}.json"
        r = subprocess.run([exe, "-b", "--factory-startup", "--python-exit-code", "1", "--python", __file__,
                            "--", "dump", str(path)], env=build.sandbox_env(), stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode:
            sys.stderr.write(r.stdout[-2000:] + r.stderr[-2000:])
            return 1
        data[ver] = json.loads(path.read_text(encoding="utf-8"))
        print(f"theme_diff: {ver}: {len(data[ver])} keys")
    moved = moved_table()
    report = {}
    base = data["4.5"]
    for ver, keys in data.items():
        if ver == "4.5":
            continue
        added, removed, renamed, gone = diff(base, keys, moved)
        report[ver] = dict(added=added, removed=removed, renamed=renamed, gone=gone)
        print(f"theme_diff: {ver}: +{len(added)} added, -{len(removed)} removed "
              f"({len(renamed)} moved / merged per the 5.0 table, {len(gone)} without a successor)")
    (OUT / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    if "--md" in argv:
        print(markdown(report))
    return 0


def _groups(keys):
    """Collapse per-editor repeats: 'x.space.tab_back' over 18 editors -> '*.space.tab_back (18)'."""
    from collections import Counter
    tails = Counter(".".join(k.split(".")[1:]) if "." in k else k for k in keys)
    heads = {}
    for k in keys:
        t = ".".join(k.split(".")[1:]) if "." in k else k
        heads.setdefault(t, []).append(k.split(".")[0])
    out = []
    for t, n in sorted(tails.items()):
        out.append(f"`{heads[t][0]}.{t}`" if n == 1 else f"`*.{t}` ({n}: {', '.join(sorted(heads[t])[:4])}…)")
    return out


def markdown(report):
    lines = []
    for ver, r in report.items():
        lines += [f"#### {ver}: +{len(r['added'])} / −{len(r['removed'])} "
                  f"(옮김 {len(r['renamed'])}, 후속 없음 {len(r['gone'])})", "",
                  "- 새 키: " + ", ".join(_groups(r["added"])), "",
                  "- 후속 없이 없어진 키: " + ", ".join(_groups(r["gone"])), ""]
    return "\n".join(lines)


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        sys.exit(main(sys.argv[1:]))
    args = sys.argv[sys.argv.index("--") + 1:]
    if args and args[0] == "dump":
        dump(args[1])
