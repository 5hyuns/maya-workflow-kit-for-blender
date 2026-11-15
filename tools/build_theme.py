"""Build the Maya Workflow Kit Theme, a separate theme extension, into dist/.

    python tools/build_theme.py [--blender PATH]

Output: dist/maya-workflow-kit-theme-<version>.zip (manifest type "theme": the manifest and one theme XML from
src/allset_theme). Built with ``blender --command extension build`` (it also validates the manifest) in a
throwaway user config inside tmp/; without Blender, a plain zip of the same two files.

The Maya Workflow Kit add-on never changes the theme. This theme is installed and picked by the user like any
other theme (Preferences > Themes), and Blender's own preset menu switches back.
"""

import argparse
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "allset_theme"
DIST = ROOT / "dist"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402  (paths and the sandbox environment only)


def version():
    text = (SRC / "blender_manifest.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    if not m:
        raise SystemExit("src/allset_theme/blender_manifest.toml: 'version' not found")
    return m.group(1)


def theme_zip(ver=None, folder=None):
    return (folder or DIST) / f"maya-workflow-kit-theme-{ver or version()}.zip"


def files():
    names = sorted(p.name for p in SRC.iterdir() if p.is_file())
    xml = [n for n in names if n.endswith(".xml")]
    if names != sorted(["blender_manifest.toml", *xml]) or len(xml) != 1:
        raise SystemExit(f"src/allset_theme must hold the manifest and one .xml, found {names}")
    return [SRC / n for n in names]


def build_with_blender(blender, out):
    cmd = [blender, "--factory-startup", "--command", "extension", "build",
           "--source-dir", str(SRC), "--output-filepath", str(out)]
    from blender_slots import slot
    with slot("tools/build_theme.py extension build"):
        r = subprocess.run(cmd, env=build.sandbox_env(), stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=300)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    if r.returncode != 0 or not out.exists():
        raise SystemExit(f"theme extension build failed (exit {r.returncode})")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--blender", default=os.environ.get("BLENDER", build.DEFAULT_BLENDER))
    args = ap.parse_args(argv)
    paths = files()
    DIST.mkdir(exist_ok=True)
    out = theme_zip()
    out.unlink(missing_ok=True)
    if Path(args.blender).is_file():
        build_with_blender(args.blender, out)
    else:
        print(f"Blender not found at {args.blender}; using plain zip fallback")
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in paths:
                zf.write(p, p.name)
    print(f"built {out.relative_to(ROOT)}")
    return out


if __name__ == "__main__":
    main()
