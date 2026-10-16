"""Generate docs/keymap_mapping.md: Maya hotkey -> runTimeCommand -> Blender.

    python tools/gen_keymap_mapping.py            # re-runs itself inside Blender
    blender -b --factory-startup --python tools/gen_keymap_mapping.py

Input: research/maya/hotkeys_default.json (all 468 bindings). Only keys,
contexts and runTimeCommand names are written (no MEL, no Maya UI strings;
docs/user_decisions.md #6). Blender side: the "Maya" keyconfig data generated
by src/maya_kit/keymap (IC + maya_patches), status from keymap/mapping.py.
Exit code 1 if an IC/KIT row is not actually bound.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOTKEYS = ROOT / "research" / "maya" / "hotkeys_default.json"
OUT = ROOT / "docs" / "keymap_mapping.md"

STATUS_LABEL = {"KIT": "구현", "IC": "IC 일치", "STEP": "계획", "NO": "해당 없음",
                None: "미검토", "MAC": "macOS 전용", "BAD": "❌ 불일치"}


def run_outside_blender():
    import subprocess
    sys.path.insert(0, str(ROOT / "tools"))
    import build
    r = subprocess.run([os.environ.get("BLENDER", build.DEFAULT_BLENDER), "-b", "--factory-startup",
                        "--python-exit-code", "1", "--python", __file__],
                       env=build.sandbox_env(), stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in r.stdout.splitlines():
        if line.startswith("maya_mapping"):
            print(line)
    if r.returncode:
        sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:])
    return r.returncode


def fmt_event(ev):
    mods = [m.capitalize() for m in ("ctrl", "alt", "shift", "oskey") if ev.get(m)]
    return "+".join(mods + [ev["type"]])


def fmt_item(km, item):
    from maya_kit.keymap.patch import props_dict
    p = ", ".join(f"{k}={v!r}" for k, v in props_dict(item[2]).items())
    return f"{km}: `{item[0]}`" + (f" ({p})" if p else "")


def build_rows():
    sys.path.insert(0, str(ROOT / "src"))
    from maya_kit.keymap import ic_data, maya_patches, mapping
    from maya_kit.keymap.patch import KeyconfigData

    kd = KeyconfigData(maya_patches.apply(ic_data.generate()))
    hotkeys = json.loads(HOTKEYS.read_text(encoding="utf-8"))["hotkeys"]
    rows = []
    for hk in hotkeys:
        press = hk.get("press") or {}
        release = hk.get("release") or {}
        rtc = press.get("runTimeCommand") or press.get("nameCommand") or "—"
        if release.get("runTimeCommand"):
            rtc += f" / {release['runTimeCommand']} (release)"
        entry = mapping.entry_for(hk)
        if hk["platform"] == "mac-only":
            status, note, step = "MAC", "Cmd 키 바인딩 (Windows 해당 없음)", None
        elif entry is None:
            status, note, step = None, "", None
        else:
            status, note, step = entry["status"], entry["note"], entry["step"]
            if entry["check"] and not mapping.check_entry(kd, hk, entry):
                status = "BAD"
                note = f"기대: {entry['check'][0]} `{entry['check'][1]}`. {note}"
        current = "; ".join(fmt_item(km, it) for km, it in mapping.current_bindings(kd, hk)) or "—"
        label = STATUS_LABEL[status] + (f" Step {step}" if status == "STEP" else "")
        rows.append((hk["display"], fmt_event(mapping.maya_event(hk)), hk["context"], rtc,
                     current, label, note, f"hotkeySetup.mel:{hk['line']}", status))
    return rows


def write_doc(rows):
    from collections import Counter
    counts = Counter(r[-1] for r in rows)
    lines = [
        "# Maya 기본 단축키 → Blender 대응표",
        "",
        "자동 생성: `python tools/gen_keymap_mapping.py` (손으로 고치지 말 것).",
        f"입력: `research/maya/hotkeys_default.json` (Maya 2022 팩토리 핫키 {len(rows)}개; "
        "근거 열 = Maya `scripts/startup/hotkeySetup.mel` 줄). "
        "Blender 쪽: 이 킷의 \"Maya\" 키컨피그 (`src/maya_kit/keymap/`), 상태 = `keymap/mapping.py`.",
        "",
        "현재 바인딩 = Maya 컨텍스트에 대응하는 Blender 키맵들(`mapping.CONTEXT_KEYMAPS`)에서 "
        "같은 키에 걸린 항목. 근사 조회라 모드에 따라 실제로 먼저 잡히는 항목은 다를 수 있다.",
        "",
        "| 상태 | 개수 |",
        "|---|---|",
    ]
    for key in STATUS_LABEL:
        if counts.get(key):
            lines.append(f"| {STATUS_LABEL[key]} | {counts[key]} |")
    lines += ["",
              "| Maya 키 | Blender 이벤트 | 컨텍스트 | runTimeCommand | Maya 키컨피그 현재 바인딩 | 상태 | 비고 | 근거 |",
              "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| " + " | ".join(str(c).replace("|", "\\|") for c in r[:-1]) + " |")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"maya_mapping: wrote {OUT.relative_to(ROOT)} ({len(rows)} rows; "
          + ", ".join(f"{STATUS_LABEL[k]}={counts[k]}" for k in STATUS_LABEL if counts.get(k)) + ")")
    return counts


def main():
    counts = write_doc(build_rows())
    if counts.get("BAD"):
        print(f"maya_mapping: {counts['BAD']} IC/KIT row(s) not bound as expected")
        sys.exit(1)


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        sys.exit(run_outside_blender())
    main()
