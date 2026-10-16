"""Release check: build, validate, install into a clean config, screenshot set.

    python tools/release_check.py [--blender PATH] [--no-shots]

1. ``tools/build.py`` (extension zip + legacy zip).
2. ``blender --command extension validate`` on the zip.
3. A fresh sandbox (tmp/release_env: empty user config, scripts and extensions;
   the user's real Blender settings are never read or written, ):
   ``blender --command extension install-file -r user_default --enable``.
4. A GUI Blender on that sandbox (no --factory-startup, so the saved sandbox
   preferences with the enabled extension load like a real first start) runs
   tools/release_shots.py: checks the extension and the Maya keymap are active,
   installs the MayaKit layout, builds a small scene and writes docs/screenshots/.
   Only the Blender process started here is terminated on timeout.
 「계획」.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402

SANDBOX = ROOT / "tmp" / "release_env"
SHOTS = ROOT / "docs" / "screenshots"
REPO_ID = "user_default"
TIMEOUT = 300


def sandbox_env():
    assert SANDBOX.resolve().is_relative_to(ROOT / "tmp"), SANDBOX
    if SANDBOX.exists():
        shutil.rmtree(SANDBOX)
    env = os.environ.copy()
    for var, sub in (("BLENDER_USER_CONFIG", "config"), ("BLENDER_USER_SCRIPTS", "scripts"),
                     ("BLENDER_USER_EXTENSIONS", "extensions")):
        d = SANDBOX / sub
        d.mkdir(parents=True)
        env[var] = str(d)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run(cmd, env, timeout=TIMEOUT):
    r = subprocess.run(cmd, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--blender", default=os.environ.get("BLENDER", build.DEFAULT_BLENDER))
    ap.add_argument("--no-shots", action="store_true")
    args = ap.parse_args(argv)
    ok = True

    zip_path = build.main(["--blender", args.blender])
    env = sandbox_env()
    rc, out = run([args.blender, "--factory-startup", "--command", "extension", "validate",
                   str(zip_path)], env)
    valid = rc == 0 and "Success" in out
    print("validate:", "PASS" if valid else "FAIL", out.strip().splitlines()[-1] if out.strip() else "")
    ok &= valid

    rc, out = run([args.blender, "--command", "extension", "install-file", "-r", REPO_ID,
                   "--enable", str(zip_path)], env)
    installed = (SANDBOX / "extensions" / REPO_ID / build.manifest_value("id") / "__init__.py").exists()
    print("install + enable:", "PASS" if rc == 0 and installed else "FAIL")
    if not (rc == 0 and installed):
        print(out[-3000:])
        return 1

    if args.no_shots:
        return 0 if ok else 1
    SHOTS.mkdir(parents=True, exist_ok=True)
    result = SANDBOX / "shots.json"
    log = SANDBOX / "shots.log"
    env["MAYA_KIT_SHOTS"] = str(SHOTS)
    cmd = [args.blender, "--enable-event-simulate", "--window-geometry", "0", "0", "1600", "900",
           "--python", str(ROOT / "tools" / "release_shots.py"), "--", str(result)]
    with open(log, "w", encoding="utf-8", errors="replace") as fh:
        proc = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=fh,
                                stderr=subprocess.STDOUT)
        try:
            proc.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()  # only the Blender started here
    checks = json.loads(result.read_text(encoding="utf-8")) if result.exists() else \
        [{"name": "release_shots.py wrote no results (see tmp/release_env/shots.log)", "ok": False}]
    for c in checks:
        print("PASS" if c["ok"] else "FAIL", c["name"])
        ok &= c["ok"]
    print("screenshots:", ", ".join(sorted(p.name for p in SHOTS.glob("*.png"))))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
