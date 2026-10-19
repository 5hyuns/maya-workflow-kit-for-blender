"""Download the marketing-screenshot assets listed in assets.json.

    python tools/marketing/fetch_assets.py            # download / verify everything
    python tools/marketing/fetch_assets.py -k robot   # only ids containing "robot"
    python tools/marketing/fetch_assets.py --record   # fill in missing sha256 / size

Files go to <id>/ (untracked, outside the extension).
Each download is checked against its sha256; a file already present with the
right hash is skipped. Zip archives listed with "extract": true are unpacked
next to the zip. Standard library only.
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets.json")
DEST = os.path.join(ROOT, "research", "marketing_assets")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    tmp = path + ".part"
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
        while True:
            block = r.read(1 << 20)
            if not block:
                break
            f.write(block)
    os.replace(tmp, path)


def safe_extract(zpath, folder):
    """Unzip without letting member names escape the folder."""
    base = os.path.realpath(folder)
    with zipfile.ZipFile(zpath) as z:
        for m in z.infolist():
            target = os.path.realpath(os.path.join(base, m.filename))
            if target != base and not target.startswith(base + os.sep):
                raise ValueError(f"unsafe path in {zpath}: {m.filename}")
        z.extractall(base)


def fetch(asset, record):
    folder = os.path.join(DEST, asset["id"])
    ok = True
    for d in asset["downloads"]:
        path = os.path.join(folder, *d["path"].split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        want = d.get("sha256")
        if os.path.exists(path) and want and sha256(path) == want:
            state = "present"
        else:
            download(d["url"], path)
            state = "downloaded"
        got = sha256(path)
        if want and got != want:
            print(f"  FAIL {asset['id']}/{d['path']}: sha256 {got} != {want}")
            ok = False
            continue
        if not want:
            if not record:
                print(f"  FAIL {asset['id']}/{d['path']}: no sha256 in assets.json (run --record)")
                ok = False
                continue
            d["sha256"] = got
        d["size"] = os.path.getsize(path)
        if d.get("extract"):
            safe_extract(path, folder)
        print(f"  ok   {asset['id']}/{d['path']} ({state}, {d['size']} bytes)")
    for rel in asset.get("files", []):
        if not os.path.exists(os.path.join(folder, *rel.split("/"))):
            print(f"  FAIL {asset['id']}: import file missing: {rel}")
            ok = False
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", default="", help="only asset ids containing this text")
    ap.add_argument("--record", action="store_true", help="write missing sha256/size into assets.json")
    a = ap.parse_args()
    with open(LIST, encoding="utf-8") as f:
        data = json.load(f)
    failed = []
    for asset in data["assets"]:
        if a.k and a.k not in asset["id"]:
            continue
        print(asset["id"])
        if not fetch(asset, a.record):
            failed.append(asset["id"])
        main_dl = asset["downloads"][0]
        asset["download_url"] = main_dl["url"]
        asset["sha256"] = main_dl.get("sha256")
    if a.record:
        with open(LIST, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    print("FAILED: " + ", ".join(failed) if failed else "all assets verified")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
