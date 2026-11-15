"""Release check: build, validate, install into a clean config, screenshot set, on every supported Blender.

    python tools/release_check.py [--no-shots] [--shots DIR]      # Blender 5.2 LTS, then 5.3
    python tools/release_check.py --blender 5.3                    # one Blender (a version or a path)

Items 2-4 run on each Blender of ``--blenders`` (default the supported 5.2 and 5.3), one after the other, each in its
own sandboxes (the first in tmp/release_env*, the others with ``_<version>`` after the name). The first Blender
builds the zips and writes docs/screenshots/; the others' screenshots stay in their sandbox. Then the site checks.

1. ``tools/build.py`` (extension zip + legacy zip).
2. ``blender --command extension validate`` on the zip.
3. A fresh sandbox (tmp/release_env: empty user config, scripts and extensions;
   the user's real Blender settings are never read or written):
   ``blender --command extension install-file -r user_default --enable``. Also the same install over a
   "user" setup in its own sandbox tmp/release_env_user (tools/release_probe.py seed: an enabled add-on of their own, changed input
   preferences, undo steps and theme). After the install the user's add-ons, theme and interface
   preferences are unchanged and only the kit's declared, backed-up changes appear (Maya keymap active,
   prefs_preset navigation / undo values); after disabling the kit everything is as seeded.
4. A GUI Blender on that sandbox (no --factory-startup, so the saved sandbox
   preferences with the enabled extension load like a real first start) runs
   tools/release_shots.py: checks the extension and the Maya keymap are active,
   installs the Maya Workflow Kit layout, builds a small scene and writes docs/screenshots/.
   Only the Blender process started here is terminated on timeout.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import blender_slots  # noqa: E402
import build  # noqa: E402

SANDBOX = ROOT / "tmp" / "release_env"
SHOTS = ROOT / "docs" / "screenshots"
REPO_ID = "user_default"
TIMEOUT = 300


def sandbox_env(sandbox=SANDBOX):
    assert sandbox.resolve().is_relative_to(ROOT / "tmp"), sandbox
    if sandbox.exists():
        shutil.rmtree(sandbox)
    env = os.environ.copy()
    for var, sub in (("BLENDER_USER_CONFIG", "config"), ("BLENDER_USER_SCRIPTS", "scripts"),
                     ("BLENDER_USER_EXTENSIONS", "extensions")):
        d = sandbox / sub
        d.mkdir(parents=True)
        env[var] = str(d)
    # the default Maya Workflow Kit project (operators/project.default_root) lives in the sandbox, not in Documents
    env["ALLSET_PROJECTS_DIR"] = str(sandbox / "projects")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _nothing():
    import contextlib
    return contextlib.nullcontext()


def run(cmd, env, timeout=TIMEOUT):
    # a Blender holds one machine-wide slot while it runs (tools/blender_slots.py)
    is_blender = "blender" in Path(cmd[0]).name.lower()
    with blender_slots.slot(f"release_check {' '.join(map(str, cmd[1:4]))}") if is_blender else _nothing():
        r = subprocess.run(cmd, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.returncode, r.stdout + r.stderr


# What enabling the kit may change on purpose: the Maya keymap becomes active
# (keymap/__init__.py register) and the navigation / undo presets (prefs_preset.PRESET, UNDO_PRESET), all
# backed up and put back on disable.
DECLARED_INPUTS = {"view_rotate_method", "use_rotate_around_active", "use_mouse_depth_navigate", "use_zoom_to_mouse",
                   "use_auto_perspective", "view_zoom_method", "view_zoom_axis", "invert_mouse_zoom",
                   "invert_zoom_wheel"}


USER_SANDBOX = ROOT / "tmp" / "release_env_user"


def user_setup_check(blender, zip_path, suffix=""):
    """Seed a "user" setup in its own sandbox, install + enable the kit, snapshot, disable, snapshot."""
    user_sandbox = Path(f"{USER_SANDBOX}{suffix}")
    env = sandbox_env(user_sandbox)
    probe = [blender, "-b", "--python", str(ROOT / "tools" / "release_probe.py"), "--"]
    snaps = {name: user_sandbox / f"{name}.json" for name in ("before", "after", "disabled")}
    rc, out = run(probe + ["seed", str(snaps["before"])], env)
    if rc != 0 or not snaps["before"].exists():
        print(out[-3000:])
        return [("seed a user setup (tools/release_probe.py seed)", False)]
    rc, out = run([blender, "--command", "extension", "install-file", "-r", REPO_ID, "--enable", str(zip_path)], env)
    if rc != 0:
        print(out[-3000:])
        return [("install + enable over a user setup", False)]
    run(probe + ["check", str(snaps["after"])], env)
    run(probe + ["disable", str(snaps["disabled"])], env)
    checks = user_setup_checks(snaps["before"], snaps["after"], snaps["disabled"])
    # enable again, Make Blender Maya, then Remove the extension in Maya mode
    removed = user_sandbox / "removed.json"
    run([blender, "--command", "extension", "install-file", "-r", REPO_ID, "--enable", str(zip_path)], env)
    run(probe + ["make", str(user_sandbox / "made.json")], env)
    rc, out = run(probe + ["remove", str(user_sandbox / "removing.json")], env)
    run(probe + ["check", str(removed)], env)
    if rc != 0 or not removed.exists():
        print(out[-3000:])
        return checks + [("Remove in Maya mode (Preferences > Extensions > Remove)", False)]
    before, gone = (json.loads(p.read_text(encoding="utf-8")) for p in (snaps["before"], removed))
    same = {k: gone[k] == before[k] for k in ("active_keyconfig", "inputs", "undo_steps", "view", "theme")}
    return checks + [(f"Remove after Make Blender Maya restores everything "
                      f"({[k for k, v in same.items() if not v] or 'all'})",
                      all(same.values()) and set(before["addons"]) == set(gone["addons"]))]


CLEAN_SANDBOX = ROOT / "tmp" / "release_env_clean"
# Files Blender itself writes in a config it runs on (not the kit): the preferences the probe saves,
# the extension repositories' index / cache, the recent-files and bookmark lists.
BLENDER_OWN = ("config/userpref.blend", "config/userpref.blend1", "config/recent-files.txt",
               "config/recent-searches.txt", "config/bookmarks.txt", "config/platform_support.txt")


def _files(root):
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def leftover_check(blender, zip_path, suffix=""):
    """Clean config -> install -> enable -> opt in -> disable -> Remove leaves no kit file behind."""
    clean = Path(f"{CLEAN_SANDBOX}{suffix}")
    env = sandbox_env(clean)
    probe = [blender, "-b", "--python", str(ROOT / "tools" / "release_probe.py"), "--"]
    run(probe + ["check", str(clean / "start.json")], env)
    before = _files(clean)
    run([blender, "--command", "extension", "install-file", "-r", REPO_ID, "--enable", str(zip_path)], env)
    run(probe + ["make", str(clean / "made.json")], env)
    template = clean / "scripts" / "startup" / "bl_app_templates_user" / "Maya_Workflow_Kit"
    made = template.is_dir()
    run(probe + ["disable", str(clean / "disabled.json")], env)
    rc, out = run(probe + ["remove", str(clean / "removed.json")], env)
    # the probe's snapshots sit at the sandbox root; Blender keeps a managed repository's index / cache
    left = sorted(f for f in _files(clean) - before
                  if "/" in f and f not in BLENDER_OWN
                  and not f.startswith(("extensions/.cache/", f"extensions/{REPO_ID}/.blender_ext/")))
    for f in left:
        print("  left behind:", f)
    return [(f"opt-in writes no layout template outside the extension (template there: {made})", not made),
             ("Remove from inside Blender", rc == 0),
             (f"clean config: install -> enable -> opt in -> disable -> Remove leaves {len(left)} kit files", not left)]


def user_setup_checks(before_path, after_path, disabled_path):
    """(name, ok) pairs: installing the kit kept the user's add-ons and settings."""
    if not after_path.exists() or not disabled_path.exists():
        return [("snapshots after the install / disable (tools/release_probe.py)", False)]
    before, after, off = (json.loads(p.read_text(encoding="utf-8")) for p in (before_path, after_path, disabled_path))
    kit = f"bl_ext.{REPO_ID}.{build.manifest_value('id')}"
    lost = sorted(set(before["addons"]) - set(after["addons"]))
    changed = {k for k in before["inputs"] if before["inputs"][k] != after["inputs"][k]}
    restored = {k: off[k] == before[k] for k in ("active_keyconfig", "inputs", "undo_steps", "view", "theme")}
    return [
        (f"install keeps the user's add-ons enabled (lost: {lost or 'none'})", not lost),
        ("install keeps the user's add-on files", after["probe_file"]),
        ("the kit is the only add-on added", sorted(set(after["addons"]) - set(before["addons"])) == [kit]),
        ("install keeps the user's theme", after["theme"] == before["theme"]),
        ("install keeps the user's interface preferences", after["view"] == before["view"]),
        (f"install changes only the declared navigation preferences ({sorted(changed)})",
         changed <= DECLARED_INPUTS),
        (f"active keymap: {before['active_keyconfig']} -> {after['active_keyconfig']} (declared)",
         after["active_keyconfig"] == before["active_keyconfig"]),   # never changed
        (f"disabling the kit restores everything ({[k for k, v in restored.items() if not v] or 'all'})",
         all(restored.values()) and kit not in off["addons"] and set(before["addons"]) <= set(off["addons"])),
    ]


def check_blender(blender, zip_path, suffix, shots):
    """Items 2-4 (module docstring) on one Blender, in the sandboxes named with ``suffix``; ``shots`` None = no
    screenshot run. Returns ok."""
    sandbox = Path(f"{SANDBOX}{suffix}")
    env = sandbox_env(sandbox)
    ok = True
    rc, out = run([blender, "--factory-startup", "--command", "extension", "validate",
                   str(zip_path)], env)
    valid = rc == 0 and "Success" in out
    print("validate:", "PASS" if valid else "FAIL", out.strip().splitlines()[-1] if out.strip() else "")
    ok &= valid

    rc, out = run([blender, "--command", "extension", "install-file", "-r", REPO_ID,
                   "--enable", str(zip_path)], env)
    installed = (sandbox / "extensions" / REPO_ID / build.manifest_value("id") / "__init__.py").exists()
    print("install + enable:", "PASS" if rc == 0 and installed else "FAIL")
    if not (rc == 0 and installed):
        print(out[-3000:])
        return False

    for name, good in user_setup_check(blender, zip_path, suffix) + leftover_check(blender, zip_path, suffix):
        print("PASS" if good else "FAIL", name)
        ok &= good

    if shots is None:
        return ok
    shots.mkdir(parents=True, exist_ok=True)
    result = sandbox / "shots.json"
    log = sandbox / "shots.log"
    env["ALLSET_SHOTS"] = str(shots)
    env["ALLSET_NO_WELCOME"] = "1"   # release_shots.py drives the first start itself
    cmd = [blender, "--enable-event-simulate", "--window-geometry", "0", "0", "1600", "900",
           "--python", str(ROOT / "tools" / "release_shots.py"), "--", str(result)]
    with blender_slots.slot("release_check shots"), open(log, "w", encoding="utf-8", errors="replace") as fh:
        proc = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=fh,
                                stderr=subprocess.STDOUT)
        try:
            proc.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()  # only the Blender started here
    checks = json.loads(result.read_text(encoding="utf-8")) if result.exists() else \
        [{"name": f"release_shots.py wrote no results (see {log.relative_to(ROOT).as_posix()})", "ok": False}]
    for c in checks:
        print("PASS" if c["ok"] else "FAIL", c["name"])
        ok &= c["ok"]
    print("screenshots:", ", ".join(sorted(p.name for p in shots.glob("*.png"))))
    return ok


def site_checks():
    """The product site names the current release and quotes today's menu coverage. Returns ok."""
    ok = True
    # the product site names the current release in its hero line; a release must not leave the old one there
    version = build.manifest_value("version")
    html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    found = re.findall(r'(?:\bv|maya-workflow-kit-|"softwareVersion": ")(\d+\.\d+\.\d+)', html)
    stale = sorted(set(v for v in found if v != version))
    stamped = bool(found) and not stale
    print("PASS" if stamped else "FAIL", f"site/index.html names only the current version v{version}"
          + (f" (found {', '.join(stale)})" if stale else "" if found else " (no version string at all)"))
    ok &= stamped
    # ... and the menu coverage it quotes is the one tools/menu_count.py counts today
    count = subprocess.run([sys.executable, str(ROOT / "tools" / "menu_count.py")], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL).stdout
    m = re.search(r"^total\s+leaves\s+(\d+)\s+working\s+(\d+)", count, re.M)
    quoted = bool(m) and f"{int(m.group(2)):,} of the {int(m.group(1)):,} main-menu items" in html
    print("PASS" if quoted else "FAIL", "site/index.html quotes the current menu coverage"
          + (f" ({m.group(2)} of {m.group(1)})" if m else " (menu_count.py gave no total)"))
    ok &= quoted
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--blenders", default=",".join(build.SUPPORTED),
                    help=f"comma-separated Blenders, versions or paths (default the supported "
                         f"{', '.join(build.SUPPORTED)}); the first one builds and takes docs/screenshots")
    ap.add_argument("--blender", default=os.environ.get("BLENDER", ""),
                    help="only this Blender (a path or a version) instead of --blenders")
    ap.add_argument("--no-shots", action="store_true")
    ap.add_argument("--shots", default=str(SHOTS), help="screenshot folder (default docs/screenshots)")
    args = ap.parse_args(argv)
    names = [args.blender] if args.blender else [v.strip() for v in args.blenders.split(",") if v.strip()]
    exes = [build.blender_exe(n) for n in names]

    zip_path = build.main(["--blender", exes[0]])
    results = []
    for i, (name, exe) in enumerate(zip(names, exes)):
        # the first Blender keeps the plain sandbox names and writes the screenshot folder; the others write their
        # screenshots into their own sandbox. Absolute: Blender writes nothing to a relative screenshot path.
        suffix = "" if i == 0 else f"_{name if exe != name else i}"
        print(f"\n=== Blender {name}: {exe} (sandboxes tmp/release_env*{suffix}) ===", flush=True)
        shots = None if args.no_shots else \
            Path(args.shots).resolve() if i == 0 else Path(f"{SANDBOX}{suffix}") / "screenshots"
        results.append((name, check_blender(exe, zip_path, suffix, shots)))
    print()
    site = site_checks()
    print("\nRelease check per Blender:")
    for name, good in results:
        print(f"  {name}: {'PASS' if good else 'FAIL'}")
    return 0 if site and all(good for _n, good in results) else 1


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import hidden_desktop  # noqa: E402  (test Blenders never show on screen)
    hidden_desktop.ensure_hidden()
    sys.exit(main())
