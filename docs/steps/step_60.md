# Step 60 — Maya ⇄ Blender 스위치 · 완전 되돌리기

Request (user, verbatim, 2026-10-18): 「사용자가 편하게 이 스킨(Maya 모드)으로 스위치하게, 언제든지 되돌릴 수 있게.」

출발점: `maya_kit.make_maya` / `revert_maya` (`src/maya_kit/first_start.py`, step 42), 그룹별 백업·복원 (`prefs_preset.py`, step 4/42/44),
테마 백업 (`theme/__init__.py`), 키컨피그 활성화·이전 키컨피그 복원 (`keymap/__init__.py`), `test_enable_disable` 의 누수 0 스냅숏 (`tests/kit.py`).

## 계획

### 실측 (Blender 4.5, `tmp/probe60/`)

- 헤드리스에도 `keyconfigs.user` (104 keymap) 가 있다 → 사용자 키 수정 (user keyconfig 의 kmi 변경) 을 헤드리스로 만들고 확인할 수 있다.
- `bpy.data.workspaces.remove` 없음 → 워크스페이스 삭제는 `workspace.delete` (창 문맥). `workspace.append_activate(idname, filepath)` 있음.
- 템플릿 startup.blend 의 Maya 레이아웃 워크스페이스 = "General" (+ Blender 기본 워크스페이스들, 마스크 `.MayaKitStrip` / `.MayaKitShelf`).
- 단축키 Ctrl+Alt+Shift+M: Blender 기본·IC (research/blender/keymap_*.json) 와 Maya 기본 단축키 (research/maya/hotkeys_default.json) 어디에도 없음.

### 1. 모드 = 확장 안의 스위치 (delegated)

- 경로 후보: (a) 스위치 = 애드온 켜기/끄기 (`addon_utils.disable`) / (b) 애드온은 켜진 채 「Maya 모드」 를 이루는 하위 패키지만 등록/해제.
  (a) 는 끈 상태에서 스위치 자체가 사라져 다시 켤 버튼이 없다 → **(b)**.
- `__init__.py`: CORE = (`preferences`, `switch`) 는 늘 등록, MODE = (prefs_preset, operators, ui, command_line, marking, theme,
  app_template, first_start, keymap) 는 `prefs.maya_mode` 가 켜져 있을 때만. 끄기 = MODE 를 역순 unregister — 이미 `test_enable_disable`
  가 「unregister 가 모든 것을 되돌림」 을 강제하므로 같은 보장이 스위치에도 그대로 선다. 켜기 = MODE register + `keymap.activate()`
  (사용자가 다른 키맵을 고른 뒤에도 켜면 Maya 키맵: `keymap_auto_activated` 규칙은 첫 설치용).
- 전환은 타이머에서 (오퍼레이터·그리기 중에 클래스를 해제하지 않도록, step 42 의 교훈). 재시작 없음.
- `maya_mode` 는 애드온 환경설정에 저장 → 다음 시작도 같은 모드. 새로 설치 = 켜짐 (지금 동작 그대로).

### 2. 어디서든 한 번에

- 상단 바 오른쪽 작은 스위치 (`TOPBAR_HT_upper_bar.append`, 오른쪽 영역에서만): 「Maya」/「Blender」 두 칸 토글, 두 모드 모두에서 보임
  (Maya 모드의 `draw_right` 교체와 무관하게 append 함수는 그려진다).
- 환경설정 패널 맨 위: 큰 스위치 버튼 + 단축키 안내 + 「Restore Blender Settings」 (스냅숏으로 완전 복원). Blender 모드에서는 Maya 옵션을 숨김.
- F3 (메뉴 검색): Blender 모드 Edit 메뉴에 「Switch to Maya」, Maya 모드 Windows > Settings/Preferences 에 「Switch to Blender」 → 메뉴 검색에 걸림.
- 단축키 Ctrl+Alt+Shift+M (add-on 키컨피그 "Window" 키맵 → 어느 활성 키맵에서도 동작).

### 3. 레이아웃 · 뷰 설정 (열린 파일의 씬 데이터는 건드리지 않음)

- 켤 때: 지금 창의 워크스페이스가 Maya 레이아웃이 아니면 템플릿 startup.blend 의 "General" 워크스페이스를 append_activate →
  이름 "Maya", ID 속성 `maya_kit_switch_prev` = 이전 워크스페이스 이름. 3D 뷰의 그리드 스케일·클립은 이 씬 단위에 맞춤 (`units.grid_scale`, 클립).
- 끌 때: 이전 워크스페이스로 돌아가고 붙였던 "Maya" 워크스페이스를 지운다 → 파일의 UI 데이터도 켜기 전과 같다. 씬·오브젝트는 손대지 않음.
- MayaKit 템플릿으로 만든 파일 (Maya 레이아웃만 있는 파일) 은 레이아웃을 그대로 둔다 (Blender UI 로 그려짐).
- 앱 템플릿: Maya 모드의 시작 옵션 (`start_in_maya_layout`) 만 따르고, 스위치는 템플릿을 지우지 않는다 (다시 켜기가 즉시). 템플릿 제거 =
  「Restore Blender Settings」 와 확장 Remove.

### 4. 완전 되돌리기 (스냅숏)

- 켤 때 (스냅숏 파일이 없을 때만) 확장 사용자 폴더에 `switch_snapshot.json`: 켜기 전 키컨피그 이름, kit 이 쓰는 환경설정 값 전부
  (`FOOTPRINT`: prefs_preset 그룹들 + gizmo_size + ui_scale / font / splash / wire / undo), 테마·ui_styles 전체 XML (rna_xml), 사용자 키 수정 수,
  켜진 애드온 목록. 비정상 종료 뒤에도 파일이 남아 있어 복원 가능.
- 끌 때: MODE unregister (각 모듈의 백업 복원) → 스냅숏과 비교해 FOOTPRINT·테마·키컨피그가 다르면 스냅숏 값으로 → 스냅숏 삭제.
  FOOTPRINT 밖 (사용자가 Maya 모드 중에 바꾼 다른 설정, 다른 애드온) 은 손대지 않는다: 다른 사람이 만든 키·테마를 덮어쓰지 않음.
  사용자 키 수정은 Blender / 사용자 키컨피그에 있고 kit 은 "Maya" 키컨피그만 만들고 지우므로 그대로.
- 시작할 때 `maya_mode` 꺼짐 + 스냅숏 남음 (끄는 도중 비정상 종료) → 스냅숏으로 복원하고 지움.
- 확장 끄기 / Remove: 루트 unregister 가 Maya 모드면 같은 끄기 경로 + 스냅숏 복원 (모드 값은 남김: 다시 켜면 Maya).
- 「Restore Blender Settings」 = 끄기 + 템플릿 제거 + 옵션 초기화 (Make Blender Maya 이전).

### 5. 검증

- 헤드리스 `test_step60_switch.py`: (i) 한 프로세스 안 왕복 — 팩토리 → 사용자 키 수정·테마 색·회전 방식·다른 애드온 → kit 켬 →
  Make Blender Maya (레이아웃 열기 없이) → 끔 → 전체 환경설정 RNA 덤프 (`kit._walk`)·user 키컨피그 덤프·테마 XML 이 켜기 전과 같음
  (kit 자신의 애드온 항목 제외) → 다시 켬 → 끔 → 같음. (ii) 여러 프로세스 왕복 (샌드박스 config): 저장된 userpref.blend 를 새 프로세스로
  읽어 덤프 비교, 같은 모드 두 번 저장한 userpref.blend 바이트 비교 결과 기록, 끄지 않고 종료 (비정상 종료 흉내) → 다음 시작에서 복원,
  Maya 모드에서 확장 끄기 → 켜기 전과 같음.
- GUI: 상단 바 스위치 클릭 → Maya 레이아웃·메뉴·테마, 다시 클릭 → Blender UI·이전 워크스페이스, 씬 오브젝트·파일 경로 그대로; 단축키;
  스크린샷 두 장.
- manual_checks 갱신.

## 한 것

- **모드 = 확장 안의 스위치** (`src/maya_kit/switch.py`, `__init__.py`): CORE (preferences, switch) 는 늘 등록, MODE (prefs_preset … keymap) 는
  `maya_mode` 가 켜져 있을 때만. 전환은 타이머에서 MODE register / unregister — 재시작 없음, 키맵·메뉴·Status Line·Shelf·테마·레이아웃이 즉시 바뀜.
- **어디서든 한 번에**: 상단 바 오른쪽 「Maya | Blender」 토글 (두 모드 모두, `TOPBAR_HT_upper_bar.append`), 애드온 환경설정 맨 위 스위치 +
  「Restore Blender Settings」 (Blender 모드에서는 Maya 옵션 숨김), Blender Edit 메뉴 「Switch to Maya Mode」 / Maya Windows 「Switch to Blender」
  (F3 메뉴 검색에 걸림), Ctrl+Alt+Shift+M (애드온 키컨피그 "Window", Blender·IC·Maya 기본 단축키 어디에도 없음).
- **레이아웃**: 켤 때 Maya 레이아웃이 없는 파일이면 템플릿 "General" 워크스페이스를 "Maya" 로 붙여 활성 (마스크 같이, 툴 헤더 숨김, 씬 단위에
  그리드·클립 맞춤), 끌 때 이전 워크스페이스로 돌아가 붙인 것을 지움. 씬·오브젝트는 손대지 않음.
- **완전 되돌리기**: 첫 켜기 전에 `switch_snapshot.json` (확장 사용자 폴더: FOOTPRINT 환경설정 값, 테마·UI 스타일 XML, 활성 키컨피그, 애드온 목록).
  끌 때 MODE 의 각 백업 복원 → 아직 Maya 값인 것만 스냅숏 값으로 → 스냅숏·테마 백업 삭제. Maya 모드 중에 사용자가 바꾼 값·다른 애드온·
  사용자 키 수정은 그대로. 종료도 unregister 이므로 스냅숏·테마 백업은 남기고 (다음 시작이 Maya 모드), 꺼진 상태 + 스냅숏 = 중단된 전환 →
  시작 때 복원. 확장 끄기 / Remove (Maya 모드인 채) 도 같은 복원.
- **Maya 테마 표시를 `filepath` 에서 테마 이름으로** (`theme.THEME_NAME` = "Maya", `theme.is_applied`, `switch.restore_snapshot`): Blender 의 확장
  제거는 제거 전 `themes[0].filepath` 를 기억했다가 그 파일이 없어지면 kit 의 unregister 가 사용자 테마를 되돌린 **뒤에**
  `preferences.reset_default_theme` 를 부른다 (`$S\addons_core\bl_pkg\bl_extension_ops.py:1233-1270`). 이제 적용 때 `filepath` = "" (테마 UI 라벨
  「Presets」, 테마 저장·삭제 버튼은 「Built-in」 으로 막힘), 이름은 userpref 에 저장되고 XML 에는 없음 (실측 `tmp/probe60b/`). 백업의 `.filepath`
  파일은 filepath·이름 두 줄 (예전 한 줄 파일도 읽음).
- 테스트: `tests/test_step60_switch.py` (+ 세션 스크립트 `rt60_session.py`, 덤프 `rt60_dump.py`), `tests/gui/gui_step60_switch.py`,
  release_check 에 「Make Blender Maya 상태에서 Remove → 전부 복원」 (`tools/release_probe.py` make / remove). `tools/look_second_start.py` 는 테마 이름으로 확인.

## 검증

- 헤드리스 `python tests/run.py`: **482/482** (56 파일; `test_step60_switch.py` 4 개: 한 프로세스 왕복 두 번 — 전체 환경설정 RNA·user 키컨피그·
  테마 XML 이 켜기 전과 같음, Maya 테마 = 이름 "Maya" + 빈 filepath; 사용자 키 수정·다른 키컨피그 유지; 샌드박스 config 여러 프로세스 왕복
  (저장·재시작); 끄는 도중 비정상 종료 → 다음 시작에서 복원, Maya 모드에서 확장 끄기 → 전부 복원).
- GUI `python tests/gui/run.py --ui-scale 0.8`: **410/410** (45 파일; `gui_step60_switch.py` 11 개: 상단 바 클릭 → Maya 레이아웃·메뉴·테마, 다시 클릭 →
  Blender UI·이전 워크스페이스, 오브젝트 그대로, Ctrl+Alt+Shift+M). 샷 `tmp/shots60/gui_step60_{maya_mode,blender_mode,blender_again,
  maya_mode_factory_layout}.png` — 두 모드 모두 상단 바 오른쪽에 「Maya | Blender」.
- `python tools/release_check.py`: 전부 PASS — 새 항목 「Remove after Make Blender Maya restores everything (all)」 포함 (테마 표시 변경 전에는
  `['theme']` 로 실패: 위 「한 것」 마지막 항목).
- `python tools/dogfood.py`: **47/47**, 콘솔 오류 0.

## 남은 것

- `blender --command extension remove` (명령줄 제거) 는 애드온 코드를 불러오지 않아 unregister 가 안 돈다 → 그 경로로는 복원 불가. Maya 모드라면
  먼저 상단 바 「Blender」 또는 「Restore Blender Settings」 를 누르거나 Preferences 안에서 Remove 할 것 (사용 안내에 적을 것, step 61 배포).
- 테마 이름 "Maya" 표시: 사용자가 Maya 테마 위에서 색만 직접 바꾸면 여전히 「Maya 테마 적용됨」 으로 보고 끌 때 스냅숏 테마로 되돌린다
  (예전 filepath 표시와 같은 동작).
- 전환 속도 체감, 실제 사용자 설정에서의 왕복은 `docs/manual_checks.md` step 60 항목.
