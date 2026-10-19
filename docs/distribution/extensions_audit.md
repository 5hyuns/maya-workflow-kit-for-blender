# extensions.blender.org 등록 감사 + Maya 상표 조사 (Hermes 서브에이전트, 2026-10-19)

## 근거 URL
- [M] https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html (manifest)
- [T] https://docs.blender.org/manual/en/latest/advanced/extensions/tags.html
- [L] https://docs.blender.org/manual/en/latest/advanced/extensions/licenses.html
- [A] https://docs.blender.org/manual/en/latest/advanced/extensions/addons.html
- [ToS] https://extensions.blender.org/terms-of-service/
- [G] https://developer.blender.org/docs/handbook/extensions/addon_guidelines/
- [MG] https://developer.blender.org/docs/features/extensions/moderation/guidelines/
- Autodesk: https://www.autodesk.com/company/legal-notices-trademarks/trademarks/guidelines-for-use

## 요건 요약
- tagline은 64자 이하, 끝에 문장부호 없음. 빈 값 금지. type은 add-on. tags는 공식 목록에서만 [M][T].
- 애드온은 GPL-3.0-or-later. **바이너리·자산(png, blend, svg, 폰트)은 CC0** [ToS 1.2][L]. copyright 필드 [ToS 1.3].
- 이름에 "Blender" 금지. 보증받은 것처럼 보이면 안 됨. 타사 로고는 그 회사가 허락할 때만 [ToS 2.x].
- No surprises: 하는 일을 설명에 전부 적는다 [ToS 3.1]. 순수 Python, 난독화 금지 [3.5-3.6]. OS·타 소프트웨어·다른 확장·**Blender 내부 모듈**·민감한 사용자 데이터를 건드리지 않는다 [3.9].
- 네트워크를 쓰면 `network` 권한과 `bpy.app.online_access`가 필요하다 [ToS 4]. 자기완결, 원격 코드 금지 [5]. 다른 애드온 간섭 금지 [G].
- **sys.path 변경과 전역 모듈 딕셔너리(sys.modules) 삽입 금지** [G][MG]. 자기 폴더에 쓰지 말고 `bpy.utils.extension_path_user`를 쓴다 [G][A].
- 자동 업데이터 금지 [MG]. `__package__` 사용 [A]. `keyconfigs.addon`이 None일 때 처리 [MG]. 리뷰 이미지 품질 [MG]. 확장 빌드에 legacy `bl_info`를 남기지 않는 것을 권고 [A].
- 제출 전 실행: `blender --command extension validate <zip>`, 그리고 [MG]의 ruff 명령.

## 현재 코드 감사 (src/maya_kit, 0.1.0 시점 줄 번호 — 지금은 다를 수 있음)
- **위반** `command_line/__init__.py` ~207-211: `sys.modules["maya"]`, `sys.modules["maya.cmds"]` 삽입. → 커맨드 라인·셸프·스크립트 에디터의 exec 네임스페이스 안에서만 `cmds`를 제공한다. `import maya.cmds`는 그 네임스페이스 전용 `__import__` 훅으로 처리한다.
- **위반** splash*.png, welcome.png, startup.blend 등 자산에 CC0 표기 없음. → 자산 라이선스 표기를 넣는다(manifest license에 `SPDX:CC0-1.0` 추가 가능 여부 확인, 안 되면 README와 ASSETS_LICENSE). Maya 아이콘이나 Maya 화면 캡처는 넣지 않는다.
- **위험** app_template/MayaKit/__init__.py: 확장 밖에 설치된 템플릿 코드가 `addon_utils.enable`을 호출하고 활성 키맵을 바꾼다. 확장을 지워도 남는다. → 템플릿은 레이아웃만 담고 코드는 최소로 한다. 비활성화·제거 때 마커가 있는 템플릿을 삭제한다(또는 템플릿 없이 workspace append 방식만 쓴다).
- **위험** 활성화하자마자 키맵 활성화(keymap/__init__ ~96-104), 환경설정 프리셋 적용(prefs_preset ~188-197), 자동 `save_userpref`(switch.py ~409-424). → 첫 실행 환영 창에서 "Make Blender feel like Maya" 확인을 받은 뒤에만 적용한다(opt-in). 자동 저장은 사용자가 동작했을 때만 한다.
- **위험** Blender UI 클래스의 `draw` 교체: STATUSBAR_HT_header(command_line), outliner, shelf, toolbox, TOPBAR, TIME. → 가능한 곳은 append/prepend로 바꾼다. 남는 것은 설명에 이유와 복원 보장을 적는다.
- 경미: `operators/keystate.py` ctypes user32 GetAsyncKeyState(읽기 전용) → 설명에 적거나 fallback을 둔다. "Help/Autodesk App Store" 메뉴 라벨 → 오해 소지가 있어 바꾼다. 확장 빌드에서 `bl_info` 제거. `rig_tools`의 Rigify enable은 확인 창이 있어 괜찮음.
- 통과: manifest 필드, GPL, tags, 네트워크 없음, 업데이터 없음, `__package__`, keyconfigs.addon None 처리, exec는 사용자 입력만 실행.

## Maya 상표 결론
- 플랫폼 ToS는 다른 회사 제품 이름 자체를 금지하지 않는다. Autodesk 지침은 **제품 이름(id 포함)에 Autodesk 상표를 넣지 말 것, 비슷한 변형도 금지**, 대신 "for / for use with / compatible with Maya"는 허용, 내 제품명을 더 눈에 띄게, 상표 각주, 제휴를 암시하지 않을 것, 로고·아이콘 금지.
- 따라서: 이름·id·URL에는 Maya를 쓰지 않는다. tagline과 설명에서는 "Maya-style …", "for Maya users"처럼 참조로 쓰는 것은 괜찮다. UI 라벨 중 Maya의 동작을 설명하는 것("Maya-style", "as in Maya")은 괜찮지만, 브랜드처럼 쓰는 라벨(테마 이름 "Maya Grey" 등)은 "Studio Grey (Maya-inspired)"처럼 중립적으로 바꾼다. 연산자 id 접두사(`maya.` / `MAYA_OT_`)는 중립 접두사로 바꾼다.
- 선례: Maya Pivot, Origin_move_like_maya, Maya 테마 2종, Houdini 테마, Unreal Viewport Navigation 등이 승인돼 있다(심사에서 용인된 것일 뿐 Autodesk가 허락한 것은 아님).
- 필수 고지문 (설명, README, 환경설정 About에 넣는다):
  > Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc., and/or its subsidiaries and/or affiliates in the USA and/or other countries. This project is an independent, free and open-source (GPL) extension for Blender. It is not affiliated with, endorsed by, sponsored by, or otherwise approved by Autodesk, Inc. or the Blender Foundation. It contains no Autodesk code, icons, MEL scripts or other Autodesk assets; references to Maya are solely to describe compatibility and the intended audience.

## 이름 결정 (Hermes delegated, 사용자 지시: 인기 제품 패턴)
- 인기 패턴(다운로드 상위·유명 애드온): 짧은 기능명 1~2단어(LoopTools, Bool Tool, F2, BoxCutter, HardOps, Zen UV, Right Mouse Navigation)이고, tagline이 무엇을 하는지 설명한다. 다른 회사 제품명은 tagline에서 "…-style"로만 쓴다(Unreal-style navigation 등).
- **이름: Switchover** (id `switchover`). extensions.blender.org에서 검색해 보니 같은 이름이 없다.
- **tagline: "Maya-style keymap, hotbox and workflow for Maya users"** (53자, 마침표 없음). 이름에는 "Blender"도 "Maya"도 없다.

## 이름 수정 (사용자 10-19: 워크플로우 강조, 이름에 Maya를 넣고 싶다)
- **이름: Switchover for Maya Users**, id `switchover`. Autodesk가 허용하는 'for' 참조 형태다. 우리 이름이 먼저 나오고 Maya는 대상만 가리킨다. URL·id에는 maya를 넣지 않는다.
- **tagline: "The complete Maya workflow, not just a keymap"**

## 최종 이름 (copy-masters 실행 결과, 사용자 요청 '전부 합친 것' 반영)
- **Allset for Maya Users** (id `allset`). tagline: **The whole Maya workflow in Blender, in one install** (50자). 위 Switchover 안은 폐기.
- extensions.blender.org에 같은 이름 없음. 다른 업종에 Allset(음식 픽업 앱)이 있지만 3D 도구와는 분야가 다르다.

## 최종 상태 (step 117, 0.2.0 제출 직전)

OK = 코드/파일로 충족하고 검증함, 설명함 = 남겨 두고 등록 설명(`docs/distribution/listing.md` B·D)에 이유를 적음.

| 요건 (근거) | 상태 | 어떻게 / 검증 |
|---|---|---|
| tagline ≤ 64 자, 끝 문장부호 없음, 빈 값 금지 [M] | OK | "The whole Maya workflow in Blender, in one install" (50) — `tests/test_step61_distribution.py` |
| type = add-on, tags 는 공식 목록에서만 [M][T] | OK | User Interface, 3D View, Modeling, Animation, Rigging (`_bpy_internal/extensions/tags.py` 와 대조하는 test_step61) |
| 권한 사유 ≤ 64 자, 마침표 없음, 맞는 권한 [M][MG] | OK | `files` = "Layout template, settings backup, shelves, Maya project folders" (63); network 없음 |
| 지원 버전 표기 [M] | OK | 4.5.0 ≤ Blender < 5.3.0 (4.5.x – 5.2.x): 4.5.4 / 5.0.1 / 5.1.2 / 5.2.2 헤드리스·GUI·설치 왕복 통과 (`docs/compat_5x.md`, step 118); 4.2.23 은 실패가 있어 제외 (step 117) |
| GPL-3.0-or-later [ToS 1.1][L] | OK | `LICENSE` (루트와 `src/allset/` 동일, test_step13) |
| 바이너리·자산 CC0 [ToS 1.2] | OK | manifest `SPDX:CC0-1.0`, `src/allset/ASSETS_LICENSE.txt` 목록 (test_step114); 등록 미디어도 킷 스크립트가 만든 것 (`tools/make_splash.py --media`, `tools/listing_shots.py`) |
| copyright 필드 [ToS 1.3] | OK | `2026 ohnsk` |
| 이름에 "Blender" 금지, Blender 로고 금지 [ToS 2.1–2.2] | OK | 이름 "Allset for Maya Users"; 아이콘·대표 이미지는 킷 그림 (로고 없음), 스크린샷은 Blender 창이지만 로고 노출은 상단 메뉴의 작은 Blender 메뉴 아이콘뿐 (Blender UI 그 자체) |
| 보증·제휴 암시 금지 [ToS 2.3], Autodesk 상표 지침 | OK | 고지문을 설명 B 「Trademarks」, README, 환경설정 About, 대표 이미지 하단에; id·URL·패키지에 maya 없음 (decision 12) |
| No surprises: 하는 일 전부 설명 [ToS 3.1] | 설명함 | 설명 B: 워크플로우 6묶음, 켤 때 바뀌는 것 (opt-in 전에는 없음), 되돌리는 법, 확장 밖에 쓰는 경로, exec / execfile / ctypes 이유; D: UI 클래스 교체 표 |
| 순수 Python, 난독화 없음 [ToS 3.5–3.6] | OK | `.py` 와 킷 자산만 (zip 목록: `tools/build.py`) |
| OS·다른 소프트웨어·다른 확장·Blender 내부 모듈 [ToS 3.9][G] | 설명함 | Blender UI 클래스: own draw 교체 / helper / poll 감싼 재등록 — Maya 모드에서만, 끄면 원상 (test_enable_disable, test_step115 의 다른 애드온 append 보존); ctypes `GetAsyncKeyState` 읽기 전용 (Windows); `bpy.utils.execfile` = Blender 동봉 IC 키맵 데이터 |
| 민감한 사용자 데이터 [ToS 3.9] | OK | 읽지 않음; 환경설정 스냅숏은 확장 사용자 폴더에만 |
| 네트워크 → `network` 권한 + `online_access` [ToS 4][MG] | OK | 네트워크 코드 없음 (test_step61); Help 항목은 사용자가 누를 때 `wm.url_open` (브라우저) |
| 자기완결, 원격 코드 금지 [ToS 5] | OK | 외부 다운로드·의존성 없음; exec 는 사용자가 입력한 코드만 (Command Line, 셸프, Script Editor) |
| 다른 애드온 간섭 금지 [G] | OK | append 된 다른 UI 유지 (test_step115_opt_in), 사용자 애드온·환경설정 유지 (release_check 사용자 셋업) |
| sys.path / sys.modules 변경 금지 [G][MG] | OK | step 114 (`test_step114_guidelines` 소스 스캔 + enable/disable 검사) |
| 자기 폴더에 쓰지 말고 `extension_path_user` [G][A][MG] | OK | test_step61 이 소스의 쓰기 경로를 지킴; 앱 템플릿 폴더 / 프로젝트 폴더는 설명함 (B 「Files it writes outside the extension」) |
| 자동 업데이터 금지 [MG] | OK | 없음 |
| `__package__` 사용, `bl_ext` 하드코딩 금지 [A][MG] | OK | `preferences.py` 의 `__package__`; 소스에 저장소 이름 없음 (test_step61) |
| `keyconfigs.addon` None 처리 [MG] | OK | `keymap/__init__.py`, `switch.py` 둘 다 None 이면 건너뜀 |
| 확장 빌드에 `bl_info` 없음 [A] | OK | `tools/build.py legacy_bl_info()` 는 레거시 zip 만 (test_step114) |
| 리뷰 이미지 품질, 무거운 GIF 금지 [MG] | OK | PNG 6장 1600×900 + 대표 1920×1080 + 아이콘 256×256, GIF 없음 (`docs/distribution/media/`) |
| `blender --command extension validate <zip>` [MG] | OK | step 117: `dist/allset-0.2.0.zip` validate 통과 (release_check) |
| ruff 명령 [MG] `find . -iname "*.py" \| xargs ruff check --output-format=concise --ignore=E402,E741,E731` | OK | 확장 소스 (`src/allset`) 에서 지적 10 건 수정 → "All checks passed!" (ruff 0.8.6 = 기본 규칙 E4/E7/E9/F). 최신 ruff 0.17 은 기본 규칙이 넓어져 스타일 지적 (RUF012 등) 이 수백 건 — 오류가 아니라 남김 (step_117.md) |
| 바이너리 / 위반 감사 항목 (위 「현재 코드 감사」) | OK | sys.modules → step 114, CC0 → 114, 템플릿 코드 → 115 (코드 없는 템플릿, 제거 시 삭제), opt-in·자동 저장 → 115, draw 교체 → 115 (own-draw), ctypes → 설명함, "Autodesk App Store" 라벨 → 111 (Blender Extensions), bl_info → 114 |
| 깨끗한 설정에서 설치→활성화→opt-in→비활성화→제거 후 남는 파일 0 | OK | `tools/release_check.py leftover_check` (step 117): 남는 것은 Blender 자신의 `userpref.blend`, `extensions/.cache` 뿐 |
