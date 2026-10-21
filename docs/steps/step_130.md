# Step 130 — Store review compliance (#40)

## 계획

심사자 요구 (gh issue 40): exec/eval 금지, sys.path·sys.modules·import 훅 금지, 테마 관련 전부 삭제, user_disabling 삭제 +
unregister 가 모든 것을 되돌림 + 추가 조치가 필요한 변경 금지, tags = User Interface 만.

위반 목록 (grep, 2bfd5d8):
- exec/eval: `command_line/runner.py:125-126`, `ui/shelf.py:165`; import 훅 `command_line/runner.py:40-74`; `ui/render_settings.py:334` sys.modules;
  `keymap/ic_data.py` `bpy.utils.execfile` (Blender API — 레인 K 가 정적 데이터로 바꿀지 판단).
- 테마: `theme/`, compat / first_start / preferences / prefs_preset / switch / welcome / `__init__` / ui 11개 파일 / key_batch3 (Alt+B 가 테마 그라디언트를 바꿈).
- 영구 변경: 활성 keyconfig 를 "Maya-style" 로 바꿈 (`keymap.activate`, 이름이 userpref 에 저장됨), `prefs_preset.py` (입력·내비·undo·패널·오토키),
  `panel_menus.py:405` (`use_rotate_around_active`), 앱 템플릿을 사용자 scripts 폴더에 복사 (`app_template/`), `switch.user_disabling`, `remove_on_disable`.
- tags 5개.

결정 (delegated):
1. 스크립트 실행 = Blender 자신의 경로: 코드를 Text 데이터블록에 쓰고 `bpy.ops.text.run_script` (Command Line, Script Editor, 셸프).
   `import maya.cmds` 는 훅 대신 실행 전 소스의 import 줄을 킷 cmds 모듈 import 로 바꿔 쓴다 (사용자에게 보이는 Text 에 그대로 남음).
2. 테마: 킷 테마·테마 파일·적용/복원 코드 전부 삭제. 킷이 그리는 색은 사용자 테마 값 또는 킷 고정 색. 사이트·리스팅에 추천 테마 문구
   (나중에 별도 테마 확장으로 낼 수 있음). Alt+B = 뷰마다 `View3DShading.background_type='VIEWPORT'` (그라디언트 없음).
3. 키맵: 활성 keyconfig 를 바꾸지 않는다. Maya 키 전부를 **애드온 keyconfig** (`wm.keyconfigs.addon`) 에 넣는다 — 애드온 항목은 같은 키맵의
   기본 항목보다 앞에 붙으므로 (Blender `wm_keymap_addon_add` = addhead, 측정으로 확인) 이긴다; 기본 keyconfig 의 같은 이벤트 항목 중 Maya 에
   없는 것은 막는 항목 (아무것도 안 하고 끝내는 킷 연산자) 으로 가린다. unregister 때 전부 제거 → 사용자 키맵 원상태.
4. 사용자 환경설정 영구 변경 금지: `prefs_preset` 삭제 (내비·undo·패널·오토키 프리셋 제거; 오토키 "Available" 은 킷 핸들러가 직접 키),
   `save_userpref` 메뉴 항목은 사용자가 고르는 명령이라 유지 여부 레인 판단, `use_rotate_around_active` 는 뷰 단위 대체 또는 제거.
5. 앱 템플릿 삭제 (확장 폴더 밖 쓰기 금지): Maya 레이아웃 = 확장 안의 startup.blend 에서 워크스페이스를 현재 파일로 append (`switch.enter_layout`),
   새 파일에 Maya 레이아웃을 원하면 명령으로. user_disabling / remove_on_disable 삭제. 스냅샷 파일은 확장 사용자 폴더 안 (허용) 이지만
   되돌릴 영구 변경이 없어지면 스냅샷 자체를 없앤다.
6. manifest tags = ["User Interface"].
7. 검증 테스트: 패키지 grep (exec/eval/compile-exec/sys.path/sys.modules/__import__/builtins/theme xml 0건), 설치→등록→Maya 모드→해제→제거 후
   userpref.blend 바이트·keyconfig 목록·활성 keyconfig·config 폴더 목록·handlers·timers·msgbus 가 이전과 같음, `extension validate`.

레인 (worktree, 파일 소유):
| 레인 | 범위 | 소유 파일 |
|---|---|---|
| E exec | 결정 1 + render_settings sys.modules | `command_line/`, `ui/shelf.py`(스크립트 실행부), `ui/script_editor.py`, `ui/render_settings.py` |
| H theme | 결정 2 | `theme/`, `compat.py` 테마 부분, `ui/*` 색 코드, `operators/key_batch3.py`, `tools/make_theme.py`, `tools/theme_diff.py` |
| K keymap | 결정 3 | `keymap/`, 키맵 테스트 |
| C core | 결정 4·5 + 핵심 파일의 테마·스냅샷 호출 제거 | `switch.py`, `preferences.py`, `prefs_preset.py`, `first_start.py`, `welcome.py`, `__init__.py`, `app_template/`, `ui/panel_menus.py:405`, `tools/build.py` |
| D docs+tests | 결정 6·7, 문서 | `blender_manifest.toml`, 새 테스트, README, listing, site, DISTRIBUTION, review_reply, user_decisions |
순차인 것: 레인 병합 후 통합 테스트 (병합 결과에서만 가능).

## 한 것

5개 레인 (worktree) 병합 + 통합 수정. 레인 문서: `step_130_exec.md`, `step_130_theme.md`, `step_130_keymap.md`, `step_130_docs.md`
(레인 C 는 `docs/user_decisions.md` 14 와 커밋 메시지).

| 심사 항목 | 결과 |
|---|---|
| exec / eval | Command Line · Script Editor · 셸프 = Text 데이터블록 + `bpy.ops.text.run_script` (`temp_override(edit_text=...)`, 측정), `import maya.cmds` 줄은 킷 모듈 import 로 바꿔 씀; IC 키맵 데이터 = 정적 파일 (`keymap/ic_4_5.py` … `ic_5_2.py`, `tools/gen_ic_data.py`), `execfile` 없음 |
| sys.path / sys.modules / import 훅 | runner 의 `__import__` 훅 · `builtins` · `importlib.util` 삭제, render_settings 의 `sys.modules` → 함수 `__globals__` |
| 테마 | `theme/` · xml 4개 · 적용/백업/복원 · 테마 도구 삭제; Alt+B = 뷰 단위 단색 배경; Maya 레이아웃 뷰 = 뷰 데이터 #5c5c5c (#45) |
| user_disabling · 영구 변경 | `user_disabling` / `remove_on_disable` / 스냅숏 / `prefs_preset` / 앱 템플릿 설치 삭제; 레이아웃 = 확장 안 startup.blend 를 append 또는 새 파일로 읽기; Maya 키 = 애드온 keyconfig + 활성 keyconfig 항목 메모리에서만 끔 (저장 안 됨 측정); Auto Key = 킷 자체 토글 + 핸들러; Alt+RMB 돌리 = 킷 연산자 (#51) |
| tags | `["User Interface"]` |

- 통합 중 발견 → 이슈 먼저 올리고 수정: #47 (새 Maya 장면 직후 시작 훅이 한 번 더 읽어 창이 닫힘), #48, #49, #50 (dogfood 기대값),
  #51 (Alt+RMB 돌리). 수정 안 한 것: #41 (홍보 이미지 재촬영), #44 (Ctrl+N), #52 (1.25 배율에서 패널 툴바 잘림), #53 (1.25 배율에서 첫
  분할 때 레이아웃 재조정).
- 결정: `docs/user_decisions.md` 13 (레인 D, 개요), 14 (레인 C, 세부·사라진 기능). 심사자 답글 초안: `docs/distribution/review_reply.md`.
- 키맵 설계는 계획 (막는 항목) 과 다름: 측정 결과 막는 항목은 뒤 키맵 (Screen / Window) 의 Maya 전역 키까지 죽여서 쓸 수 없음
  → 활성 keyconfig 의 같은 키맵 항목을 메모리에서만 끔 (delegated, `step_130_keymap.md`).

## 검증

- 헤드리스 전체: 992/993 → dolly 그림자 선언 후 키맵·step130 27/27 (전체 = 993 중 실패 0).
- 패키지 스캔 `test_step130_package_scan` / `test_step130_no_exec` PASS (exec/eval/훅/sys.*/테마/환경설정 쓰기/user_resource 0건);
  수명주기 `test_step130_lifecycle` / `test_step130_keymap_lifecycle` PASS (설치→등록→Maya 모드→해제→제거 후 환경설정·keyconfig·config 폴더·
  핸들러 동일).
- `blender --command extension validate dist/maya-workflow-kit-0.2.0.zip`: Success.
- `tools/dogfood.py`: 48/48.
- GUI 전체 1회: 948/957 → 실패 파일만 재실행: manual_sweep · step27 · step129_time · step129_panel_toolbar PASS (테스트를 새 동작에
  맞춤: 킷 Auto Key, 킷 매니퓰레이터 크기, Maya 밀도에서 툴바), `gui_step112_opaque` 삭제 (Region Overlap 프리셋 기능 삭제),
  `gui_step106_tool_settings` 은 1.25 배율에서 1건 실패 (#53, 0.8 배율에서는 12/12).

## 남은 것

- #53 (1.25 배율 레이아웃 재조정), #52 (툴바 넘침), #44 (Ctrl+N), #41 (홍보·스토어 이미지 재촬영 — 테마가 없어진 화면으로).
- 스토어에 0.2.1 업로드 후 `review_reply.md` 를 심사 스레드에 올리기 (사용자).
- 심사자가 「활성 keyconfig 항목을 메모리에서 끄는 것」 을 문제 삼으면 대안이 마땅치 않음 (`step_130_keymap.md` 위험 절).
