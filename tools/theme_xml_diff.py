"""Compare the kit's theme presets: each studio_grey_<5.m>.xml against studio_grey.xml (4.5), value by value.

    python tools/theme_xml_diff.py            # summary per file
    python tools/theme_xml_diff.py -v         # every differing key

A key that exists in both files (same path, or the 5.x path of a 4.5 key per the 5.0 migration table MOVED)
should hold the same value: then a 5.x Blender shows the same colours as 4.5 (step 119). Pure Python.
"""

import sys
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "src" / "allset" / "theme"


def flatten(path):
    """{dotted path: value} of every attribute in a theme preset XML (Theme + ThemeStyle)."""
    out = {}

    def walk(node, prefix):
        for name, value in node.attributes.items():
            out[f"{prefix}.{name}" if prefix else name] = value
        for child in node.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            # property elements hold one struct element: <view_3d><ThemeView3D ...>
            inner = [c for c in child.childNodes if c.nodeType == c.ELEMENT_NODE]
            if len(inner) == 1 and inner[0].tagName[0].isupper():
                walk(inner[0], f"{prefix}.{child.tagName}" if prefix else child.tagName)
            else:
                walk(child, f"{prefix}.{child.tagName}" if prefix else child.tagName)

    doc = xml.dom.minidom.parse(str(path))
    for top in doc.documentElement.childNodes:
        if top.nodeType == top.ELEMENT_NODE:
            walk(top, top.tagName)
    return out


def norm(v):
    v = v.lower()
    if v.startswith("#") and len(v) == 9 and v.endswith("ff"):
        return v[:7]
    return v


def compare(base, other, moved):
    """(common keys, [(4.5 key, 5.x key, 4.5 value, 5.x value)] that differ)."""
    old_to_new = {old: new for new, old in moved}
    common, diffs = 0, []
    for k, v in base.items():
        k2 = k
        if k not in other:
            tail = k.split(".", 1)[1] if "." in k else k
            k2 = "Theme." + old_to_new[tail] if tail in old_to_new else None
            if k2 not in other:
                continue
        common += 1
        if norm(v) != norm(other[k2]):
            diffs.append((k, k2, v, other[k2]))
    return common, diffs


def main(argv):
    sys.path.insert(0, str(ROOT / "tools"))
    import make_theme
    moved = make_theme.moved_table()
    base = flatten(FOLDER / "studio_grey.xml")
    total = 0
    for f in sorted(FOLDER.glob("studio_grey_*.xml")):
        common, diffs = compare(base, flatten(f), moved)
        total += len(diffs)
        print(f"theme_xml_diff: {f.name}: {common} keys shared with 4.5, {len(diffs)} differ")
        if "-v" in argv:
            for k, k2, a, b in diffs:
                print(f"  {k}{'' if k == k2 else ' -> ' + k2}: 4.5 {a} | {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
