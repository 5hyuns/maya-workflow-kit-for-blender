"""Step 125: the product is "Maya Workflow Kit" — manifest name, template folder, zip name, no user-visible "Allset"
left in the package, and old "Allset" template copies (marker-checked) go with an install / remove."""

import os
import re
import shutil
import sys
from importlib import import_module

import kit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "allset")
# Hidden identifiers users never see (leading-dot data names, a PropertyGroup class name) and the old template
# folder name app_template.LEGACY cleans up.
HIDDEN = (".AllsetStrip", ".AllsetShelf", ".Allset Smooth Preview Shading", '".Allset"', "AllsetNucleus", '"Allset"')


def _mod(name):
    return import_module(f"{kit.MODULE}.{name}")


def test_manifest_and_constants():
    text = open(os.path.join(SRC, "blender_manifest.toml"), encoding="utf-8").read()
    assert re.search(r'^name = "Maya Workflow Kit"$', text, re.M)
    assert re.search(r'^id = "allset"$', text, re.M), "the extension id stays allset"
    tagline = re.search(r'^tagline = "([^"]+)"$', text, re.M).group(1)
    assert tagline == "The whole Maya workflow in Blender, in one install"
    assert len(tagline) <= 64 and not tagline.endswith(".")
    assert _mod("names").PRODUCT == "Maya Workflow Kit"
    app_template = _mod("app_template")
    assert app_template.TEMPLATE_ID == "Maya_Workflow_Kit" and os.path.isdir(app_template.SOURCE_DIR)
    import bpy
    assert bpy.path.display_name(app_template.TEMPLATE_ID) == "Maya Workflow Kit"   # File > New label


def test_zip_name():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    try:
        build = import_module("build")
    finally:
        sys.path.pop(0)
    version = build.manifest_value("version")
    assert build.ext_zip().name == f"maya-workflow-kit-{version}.zip"
    assert build.legacy_zip().name == f"maya-workflow-kit-{version}-legacy.zip"


def test_no_allset_in_user_visible_text():
    hits = []
    for folder, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            if not name.endswith((".py", ".toml", ".txt")):
                continue
            path = os.path.join(folder, name)
            for n, line in enumerate(open(path, encoding="utf-8"), 1):
                for h in HIDDEN:
                    line = line.replace(h, "")
                if "Allset" in line:
                    hits.append(f"{os.path.relpath(path, SRC)}:{n}: {line.strip()}")
    assert not hits, "\n".join(hits)


def test_old_allset_template_is_removed_marker_checked():
    app_template = _mod("app_template")
    base = app_template.user_templates_dir(create=True)
    old = os.path.join(base, "Allset")
    os.makedirs(old, exist_ok=True)
    open(os.path.join(old, app_template.MARKER), "w").close()
    foreign = os.path.join(base, "MayaKit")            # same old name, but not carrying its marker: left alone
    os.makedirs(foreign, exist_ok=True)
    try:
        dst = app_template.install()
        assert not os.path.isdir(old), "install left the old Allset template copy"
        assert os.path.basename(dst) == "Maya_Workflow_Kit"
        os.makedirs(old, exist_ok=True)
        open(os.path.join(old, app_template.MARKER), "w").close()
        assert app_template.remove()
        assert not os.path.isdir(old) and not os.path.isdir(dst)
        assert os.path.isdir(foreign), "a folder without the kit's marker must never be removed"
    finally:
        shutil.rmtree(foreign, ignore_errors=True)
        shutil.rmtree(old, ignore_errors=True)
