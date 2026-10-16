"""GUI event-simulation tests.

    python tests/gui/run.py [-k PATTERN] [--no-build] [--shots DIR]

Builds and installs the extension into the same sandbox as tests/run.py,
then runs each tests/gui/gui_*.py in a GUI Blender started with
``--factory-startup --enable-event-simulate`` (real mouse/keyboard input is
ignored, a window appears briefly). Only the Blender process started here is
terminated on timeout. Prints PASS/FAIL per check; exit 1 on any failure.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))
import run as headless  # noqa: E402

TIMEOUT = 180


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run Maya Kit GUI event tests")
    ap.add_argument("-k", default="")
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--shots", default="", help="directory for screenshots")
    ap.add_argument("--blender", default=os.environ.get("BLENDER", headless.build.DEFAULT_BLENDER))
    args = ap.parse_args(argv)

    if args.no_build:
        zip_path = headless.build.DIST / f"{headless.PKG_ID}-{headless.build.manifest_value('version')}.zip"
    else:
        zip_path = headless.build.main(["--blender", args.blender, "--no-legacy"])
    env = headless.make_sandbox()
    headless.install(args.blender, zip_path, env)
    if args.shots:
        Path(args.shots).mkdir(parents=True, exist_ok=True)
        env["MAYA_KIT_GUI_SHOTS"] = str(Path(args.shots).resolve())

    passed = failed = 0
    files = sorted(p for p in HERE.glob("gui_*.py") if args.k in p.name)
    for path in files:
        out = headless.SANDBOX / "results" / f"{path.stem}.json"
        log = headless.SANDBOX / "logs" / f"{path.stem}.log"
        cmd = [args.blender, "--factory-startup", "--enable-event-simulate", *os.environ.get("MAYA_KIT_GUI_ARGS", "").split(),
               "--window-geometry", "0", "0", "1600", "900",
               "--python", str(path), "--", str(out)]
        with open(log, "w", encoding="utf-8", errors="replace") as fh:
            proc = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL,
                                    stdout=fh, stderr=subprocess.STDOUT)
            try:
                proc.wait(timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                proc.kill()  # only the Blender we started
        results = json.loads(out.read_text(encoding="utf-8")) if out.exists() else \
            [{"name": "<no result file>", "ok": False}]
        for r in results:
            print(f"{'PASS' if r['ok'] else 'FAIL'}  {path.stem}::{r['name']}")
            passed += r["ok"]
            failed += not r["ok"]
        print(f"      (log: {log.relative_to(ROOT)})")

    print(f"\n{passed} passed, {failed} failed, {len(files)} file(s)")
    return 1 if failed or not files else 0


if __name__ == "__main__":
    sys.exit(main())
