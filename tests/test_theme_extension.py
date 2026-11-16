"""The Maya Workflow Kit Theme (src/allset_theme): a separate theme extension with Maya's interface greys.

The add-on itself never changes the theme (tests/test_step5_layout.py, tests/test_step130_package_scan.py,
tests/test_step130_lifecycle.py). The Maya look comes only from this theme, which the user installs and picks;
Blender's own theme menu switches back. Checked here:

- the package is a theme extension (manifest type "theme", one XML, only theme types in it);
- picking it sets every value it lists and nothing else; Blender's default theme comes back exactly;
- the add-on (enable, Maya mode on / off, disable) leaves the picked theme alone;
- across sessions in a sandbox: install (the theme applies), Save Preferences and restart (it stays), the user's
  own theme picked back from the theme menu (every value as before), Remove (Blender's default theme), and a
  start without the theme installed changes nothing.
"""

import json
import os
import shutil
import subprocess
import tomllib
import xml.dom.minidom

import bpy

import kit

AUTO_ENABLE = False
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
THEME_DIR = os.path.join(ROOT, "src", "allset_theme")
MENU = "USERPREF_MT_interface_theme_presets"
# not theme colours: where the theme came from, and its name
SKIP = ("filepath", "name")


def _xml_path():
    xmls = [f for f in os.listdir(THEME_DIR) if f.endswith(".xml")]
    assert len(xmls) == 1, xmls
    return os.path.join(THEME_DIR, xmls[0])


def _listed():
    """{rna path below the theme ("user_interface.wcol_regular.inner"): XML value} of every value the theme sets."""
    doc = xml.dom.minidom.parse(_xml_path())
    theme = doc.getElementsByTagName("Theme")[0]
    out, types = {}, set()

    def walk(node, prefix):
        types.add(node.nodeName)
        for k, v in node.attributes.items():
            out[prefix + k] = v
        for prop in (c for c in node.childNodes if c.nodeType == c.ELEMENT_NODE):
            kids = [c for c in prop.childNodes if c.nodeType == c.ELEMENT_NODE]
            assert len(kids) == 1, f"{prefix}{prop.nodeName}: one type element expected"
            walk(kids[0], prefix + prop.nodeName + ".")

    walk(theme, "")
    return out, types


def _values():
    return {k: v for k, v in kit._walk(bpy.context.preferences.themes[0]).items() if k not in SKIP}


def _expected(text):
    if text.startswith("#"):
        return [int(text[i:i + 2], 16) / 255 for i in range(1, len(text), 2)]
    if text in ("TRUE", "FALSE"):
        return text == "TRUE"
    return float(text)


def _matches(rna_repr, text):
    want = _expected(text)
    got = eval(rna_repr, {})        # noqa: S307  (repr of a number / tuple written by kit._walk)
    if isinstance(want, bool):
        return got is want
    if isinstance(want, float):
        return abs(float(got) - want) < 1e-4
    return len(got) == len(want) and all(abs(a - b) < 0.6 / 255 for a, b in zip(got, want))


def _pick_theme():
    bpy.ops.script.execute_preset(filepath=_xml_path(), menu_idname=MENU)


def test_package_is_a_theme_extension():
    with open(os.path.join(THEME_DIR, "blender_manifest.toml"), "rb") as fh:
        m = tomllib.load(fh)
    assert m["type"] == "theme", m["type"]
    assert m["id"].startswith("allset") and "maya" not in m["id"], m["id"]
    assert sorted(os.listdir(THEME_DIR)) == sorted(["blender_manifest.toml", os.path.basename(_xml_path())])
    from _bpy_internal.extensions import tags
    assert set(m["tags"]) <= tags.themes, m["tags"]


def test_xml_holds_only_theme_types():
    _listed_values, types = _listed()
    secure = getattr(bpy.types, MENU).preset_xml_secure_types
    assert types <= secure, sorted(types - secure)
    doc = xml.dom.minidom.parse(_xml_path())
    assert [n.nodeName for n in doc.documentElement.childNodes if n.nodeType == n.ELEMENT_NODE] == \
        ["Theme", "ThemeStyle"]


def test_picking_sets_the_listed_values_and_nothing_else():
    bpy.ops.preferences.reset_default_theme()
    factory = _values()
    listed, _types = _listed()
    try:
        _pick_theme()
        picked = _values()
        missing = [k for k in listed if k not in picked]
        assert not missing, f"not theme properties: {missing}"
        wrong = [f"{k}: {picked[k]} != {v}" for k, v in listed.items() if not _matches(picked[k], v)]
        assert not wrong, "\n".join(wrong[:20])
        others = [k for k in picked if picked[k] != factory[k] and k not in listed]
        assert not others, f"changed without being listed: {others[:20]}"
        assert sum(picked[k] != factory[k] for k in listed) >= 0.9 * len(listed), "most values differ from Blender's"
    finally:
        bpy.ops.preferences.reset_default_theme()
    assert _values() == factory, "Blender's default theme comes back exactly"


def test_add_on_leaves_the_picked_theme_alone():
    _pick_theme()
    try:
        before = _values()
        kit.enable(maya=True)
        assert _values() == before, "enable + Maya mode on changed the theme"
        import importlib
        importlib.import_module(kit.MODULE + ".switch").set_mode(False, layout=False)
        kit.disable()
        assert _values() == before, "Maya mode off + disable changed the theme"
    finally:
        bpy.ops.preferences.reset_default_theme()


# --- across sessions, in a sandbox of its own ------------------------------------------------------------------

def _sandbox(name):
    root = os.path.abspath(os.path.join(bpy.utils.user_resource('CONFIG'), "..", name))
    assert "tmp" in root.replace("\\", "/").split("/"), root
    if os.path.isdir(root):
        shutil.rmtree(root)
    env = dict(os.environ)
    for var, sub in (("BLENDER_USER_CONFIG", "config"), ("BLENDER_USER_SCRIPTS", "scripts"),
                     ("BLENDER_USER_EXTENSIONS", "extensions")):
        os.makedirs(os.path.join(root, sub))     # Blender ignores a BLENDER_USER_* folder that doesn't exist
        env[var] = os.path.join(root, sub)
    env["ALLSET_NO_WELCOME"] = "1"
    env["ALLSET_PROJECTS_DIR"] = os.path.join(root, "projects")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return root, env


def _run(cmd, env):
    p = subprocess.run(cmd, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=240)
    return p.returncode, p.stdout + p.stderr


def _session(root, env, name, *actions):
    out = os.path.join(root, f"{name}.json")
    rc, log = _run([bpy.app.binary_path, "-b", "--python", os.path.join(HERE, "te_session.py"), "--", out,
                    *actions], env)
    assert os.path.isfile(out), f"session {name} wrote nothing (exit {rc}):\n{log[-3000:]}"
    with open(out, encoding="utf-8") as fh:
        data = json.load(fh)
    data["values"] = {k: v for k, v in data["values"].items() if k not in SKIP}
    return data


def _diff(a, b):
    return [k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


def test_install_restart_pick_back_and_remove():
    root, env = _sandbox("theme_ext")
    zip_path = os.path.join(root, "theme.zip")
    rc, log = _run([bpy.app.binary_path, "--factory-startup", "--command", "extension", "build",
                    "--source-dir", THEME_DIR, "--output-filepath", zip_path], env)
    assert rc == 0 and os.path.isfile(zip_path), log[-3000:]
    kit_zip = kit_zip_path()
    rc, log = _run([bpy.app.binary_path, "--command", "extension", "install-file", "-r", "user_default", kit_zip],
                   env)
    assert rc == 0, log[-3000:]

    factory = _session(root, env, "factory")
    own = _session(root, env, "own", "own_theme", "save")
    assert _diff(factory["values"], own["values"]), "the user's own theme differs from Blender's"
    listed, _types = _listed()

    installed = _session(root, env, "install", f"install:{zip_path}", "save")
    assert installed["installed"], installed["log"]
    assert all(_matches(installed["values"][k], v) for k, v in listed.items()), "installing picks the theme"
    restarted = _session(root, env, "restart")
    assert restarted["values"] == installed["values"], "Save Preferences + restart keep the theme"
    with_kit = _session(root, env, "kit", "kit_on", "kit_off", "save")
    assert with_kit["values"] == installed["values"], "the add-on left the theme alone"

    back = _session(root, env, "pick_own", "pick_own", "save")
    assert not _diff(own["values"], back["values"]), _diff(own["values"], back["values"])[:20]
    again = _session(root, env, "again")
    assert not _diff(own["values"], again["values"]), "the user's theme stays after a restart"

    removed = _session(root, env, "remove", "uninstall", "save")
    assert not removed["installed"], removed["log"]
    assert not _diff(own["values"], removed["values"]), "Remove keeps the user's own theme when it is picked"
    shutil.rmtree(root)


def test_remove_while_picked_gives_blenders_default_theme():
    """Blender's own rule for theme extensions: removing the theme in use falls back to Blender's default theme
    (a theme of the user's own comes back from the theme menu when it was saved there)."""
    root, env = _sandbox("theme_ext_remove")
    zip_path = os.path.join(root, "theme.zip")
    rc, log = _run([bpy.app.binary_path, "--factory-startup", "--command", "extension", "build",
                    "--source-dir", THEME_DIR, "--output-filepath", zip_path], env)
    assert rc == 0, log[-3000:]
    factory = _session(root, env, "factory")
    own = _session(root, env, "own", "own_theme", "save")
    _session(root, env, "install", f"install:{zip_path}", "save")
    removed = _session(root, env, "remove", "uninstall", "save")
    assert not _diff(factory["values"], removed["values"]), "Blender's default theme after Remove"
    back = _session(root, env, "pick_own", "pick_own", "save")
    assert not _diff(own["values"], back["values"]), "the user's saved theme comes back from the theme menu"
    shutil.rmtree(root)


def kit_zip_path():
    with open(os.path.join(ROOT, "src", "allset", "blender_manifest.toml"), "rb") as fh:
        ver = tomllib.load(fh)["version"]
    path = os.path.join(ROOT, "dist", f"maya-workflow-kit-{ver}.zip")
    assert os.path.isfile(path), path
    return path
