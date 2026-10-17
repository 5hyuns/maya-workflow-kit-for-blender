"""Build a static extension repository (Blender 4.2+ "remote repository") into dist/repo/.

    python tools/build_repo.py [--blender PATH] [--out DIR] [--zip ZIP ...] [--no-build]

dist/repo/ gets the extension zip(s) and the listing Blender reads, made by Blender itself:
``blender --command extension server-generate --repo-dir dist/repo --html`` -> index.json +
index.html. Any static file host can serve the folder (docs/DISTRIBUTION.md §(b)); a Blender
user adds ``<url>/index.json`` once under Preferences > Get Extensions > Repositories and then
gets updates like from extensions.blender.org. ``file:///.../index.json`` works too, which is how
tools/repo_check.py tests the whole path offline.

Nothing is uploaded: publishing is the user's decision (docs/user_decisions.md 11).
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402

REPO = build.DIST / "repo"


def generate(blender, repo_dir):
    """index.json (+ index.html) for every zip in repo_dir."""
    cmd = [blender, "--factory-startup", "--command", "extension", "server-generate",
           "--repo-dir", str(repo_dir), "--html"]
    import subprocess
    r = subprocess.run(cmd, env=build.sandbox_env(), stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    if r.returncode != 0 or not (repo_dir / "index.json").exists():
        raise SystemExit(f"server-generate failed (exit {r.returncode})")
    return repo_dir / "index.json"


def file_url(path):
    """file:// URL Blender accepts for a local repository listing (file:///C:/...)."""
    return Path(path).resolve().as_uri()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--blender", default=os.environ.get("BLENDER", build.DEFAULT_BLENDER))
    ap.add_argument("--out", default=str(REPO), help="repository folder (default dist/repo)")
    ap.add_argument("--zip", action="append", default=[], help="extension zip(s) to list (default: build one)")
    ap.add_argument("--no-build", action="store_true", help="use dist/<id>-<version>.zip as it is")
    args = ap.parse_args(argv)

    out = Path(args.out)
    zips = [Path(z) for z in args.zip]
    if not zips:
        version = build.manifest_value("version")
        zip_path = build.DIST / f"{build.manifest_value('id')}-{version}.zip"
        if not args.no_build or not zip_path.exists():
            zip_path = build.main(["--blender", args.blender, "--no-legacy"])
        zips = [zip_path]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for z in zips:
        shutil.copy2(z, out / z.name)
    index = generate(args.blender, out)
    print(f"repository: {out}")
    print(f"listing:    {index}  ({file_url(index)})")
    return index


if __name__ == "__main__":
    main()
