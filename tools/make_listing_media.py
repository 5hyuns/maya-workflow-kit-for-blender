"""extensions.blender.org listing media (step 117): docs/distribution/media/.

    python tools/make_listing_media.py [--blender PATH] [--no-build] [--no-shots]

1. ``tools/make_splash.py`` renders the kit-made icon (256 x 256) and featured image (1920 x 1080) next to the
   splash images (CC0, src/allset/ASSETS_LICENSE.txt rules; no Maya or Blender logo, terms of service 2.2).
2. The extension zip is installed and enabled in a clean sandbox (tmp/listing_env, the user's Blender settings are
   never read or written, ) and a GUI Blender runs tools/listing_shots.py: six 1600 x 900 screenshots,
   one per workflow group of docs/distribution/listing.md. Only the Blender started here is killed on timeout.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import release_check  # noqa: E402

MEDIA = ROOT / "docs" / "distribution" / "media"
SANDBOX = ROOT / "tmp" / "listing_env"
TIMEOUT = 300


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--blender", default=os.environ.get("BLENDER", build.DEFAULT_BLENDER))
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--no-shots", action="store_true")
    args = ap.parse_args(argv)
    MEDIA.mkdir(parents=True, exist_ok=True)
    rc = subprocess.run([sys.executable, str(ROOT / "tools" / "make_splash.py"), "--media"],
                        stdin=subprocess.DEVNULL).returncode
    if rc or args.no_shots:
        return rc

    zip_path = ROOT / "dist" / f"allset-{build.manifest_value('version')}.zip"
    if not args.no_build or not zip_path.exists():
        zip_path = build.main(["--blender", args.blender])
    env = release_check.sandbox_env(SANDBOX)
    rc, out = release_check.run([args.blender, "--command", "extension", "install-file", "-r",
                                 release_check.REPO_ID, "--enable", str(zip_path)], env)
    if rc:
        print(out[-3000:])
        return 1
    result, log = SANDBOX / "shots.json", SANDBOX / "shots.log"
    env["ALLSET_SHOTS"] = str(MEDIA)
    env["ALLSET_NO_WELCOME"] = "1"
    cmd = [args.blender, "--enable-event-simulate", "--window-geometry", "0", "0", "1600", "900",
           "--python", str(ROOT / "tools" / "listing_shots.py"), "--", str(result)]
    with open(log, "w", encoding="utf-8", errors="replace") as fh:
        proc = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT)
        try:
            proc.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()  # only the Blender started here
    checks = json.loads(result.read_text(encoding="utf-8")) if result.exists() else \
        [{"name": f"listing_shots.py wrote no results (see {log})", "ok": False}]
    ok = True
    for c in checks:
        print("PASS" if c["ok"] else "FAIL", c["name"])
        ok &= c["ok"]
    print("media:", ", ".join(sorted(p.name for p in MEDIA.glob("*.png"))))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
