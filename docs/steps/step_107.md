# Step 107 — Keymap: wrong daily keys, missing keys, unreviewed rows (step_98.md #35–#36, quant section 4)

## 계획 (delegated)

근거: `research/maya/hotkeys_default.json` (키·컨텍스트·runTimeCommand), 명령 뜻 = `research/maya/runtime_commands.json`
annotation, 동작 = Maya 2022 `scripts/others/*.mel` 을 읽어 적은 규칙 (복사 안 함). 시작: 미검토 219 (`python
tools/gen_keymap_mapping.py`).

**틀린 키 (지우고 Maya 뜻으로)**
| 키 | 지금 (IC) | Maya | kit |
|---|---|---|---|
| Alt+R | Object / Pose `scale_clear` | ToggleReflection (Artisan 대칭) | "3D View" `maya_kit.symmetry(TOGGLE)` (kit 대칭 = 메시 mirror 플래그 = 조각·페인트 대칭도) |
| Ctrl+I | 3D 모드 select_all INVERT | SelectNextIntermediatObject | 3D 모드의 invert 제거 (Maya Ctrl+Shift+I 반전은 IC 에 이미 있음); intermediate object 없음 → NO |
| F1 | 3D View 앞 뷰, Image 1:1 | Help | 둘 제거, "Window" F1 = `wm.doc_view_manual_ui_context` (마우스 아래 버튼의 Blender 설명서) |
| Alt+C | Mesh loop cut 도구 | ToggleColorFeedback | 제거, "Weight Paint" Alt+C = 가중치 색 표시 켬/끔 (`overlay.weight_paint_mode_opacity` 1 ↔ 0) |
| m | 모든 3D 모드 Measure 도구 | ModifyDisplacement (홀드 드래그) | 제거, "Sculpt" M = 세기 드래그 (radial control) |
| Ctrl+PgUp/PgDn | Screen workspace_cycle | PickWalkIn / Out (pickWalkIn.mel: `pickWalk -d in/out`) | 제거, Object Mode / Pose `select_hierarchy` CHILD / PARENT |
| Ctrl+, | Screen 환경설정 | PrevSkinPaintMode | 제거 (Maya Windows 의 환경설정은 메뉴만); 스킨 페인트 모드 없음 → NO |

**없던 키**
- Ctrl+M = 메인 메뉴 막대 접기/펴기 (top bar `area.show_menus`, kit 메뉴는 그 플래그를 이미 따름), Shift+M = 패널 메뉴 막대
  (마우스 아래 영역 `area.show_menus`), Ctrl+Shift+M = 패널 막대 (3D View 머리 `show_region_header`).
- Alt+B = 배경 순환 (cycleBackgroundColor.mel: 기본 0.36 → 0.631 → 그라데이션 → 검정 → 기본). Blender 의 그라데이션은 전역 테마라
  건너뛴다: 테마 (#5c5c5c) → 0.631 → 0 → 테마, 뷰별 `shading.background_type/background_color`.
- 스킨 페인트 ("Weight Paint"): u = 페인트 연산 메뉴 (Replace / Add / Scale / Smooth, IC 의 U 세기 대체), n = Value 드래그 (IC Ctrl+F
  가중치 radial 복사), Alt+F = Flood (`paint.weight_set`), Ctrl+Alt+C / V = Copy / Paste Vertex Weights (step 58, "Mesh" 에도),
  Shift+B (lower radius) = Blender 브러시엔 반지름 하나 → NO.
- 조각 ("Sculpt"): Ctrl+0–9 = Freeze (Mask) / Sculpt (Draw) / Smooth / Relax (Relax Slide) / Grab / Pinch (Pinch/Magnify) / Flatten
  (Flatten/Contrast) / Foamy (Blob) / Spray (Draw Sharp) / Repeat (Layer) — `brush.asset_activate` 필수 브러시 (IC 의 Ctrl+0–5
  multires 단계 대체; Spray / Repeat 는 가장 가까운 것, delegated). b = 크기 드래그 (IC B 브러시 선반 대체), m = 세기, Shift+U = Unfreeze
  All (마스크 지움), Ctrl+Shift+I = Invert Freeze (마스크 반전), f = Frame (kit 3D View F).
- Graph Editor h / j = 채널 잠금 / 풀기 (`anim.channels_setting_enable/disable PROTECT`), l (값 기준선) = Blender 에 없음 → NO.
- Time Slider 북마크 = Blender 마커 (`operators/bookmarks.py`): Alt+T 만들기 (이름 대화상자), Alt+Shift+T 바로 만들기, ' / ; 다음 / 이전
  (`screen.marker_jump`), Shift+| 현재 북마크 범위로 재생 범위, Shift+" / Shift+: 다음 / 이전 북마크로 가서 그 범위. 북마크 끝 =
  선택한 시간 범위의 끝 (scene ID 속성), 없으면 다음 마커 앞 프레임, 없으면 장면 끝.
- 그 밖: Ctrl+F = 검색 (`wm.search_menu`), Ctrl+Shift+% = Use Default Material (`maya_kit.panel_set DEFAULT_MATERIAL`), UV Editor
  7 = 왜곡 표시, 5 = UV 면 표시.

**나머지 미검토 분류**: Time Editor (NLA 에 대응, 프레임/삭제/그룹만 IC), Node Editor / Hypershade (클립보드·그룹·스냅만 IC), UV 도구
키 Q/W/E/R/F/A/Ctrl+C/V (IC), XGen / Profiler / Hypergraph / Shape / Pose 편집기 / UV 조각 브러시 (Blender 에 없음), Render View
노출·감마 (Color Management), 기타 전역 → NO + 이유. 목표: 미검토 < 100 (실제로 0 에 가깝게).

검증: `python tools/gen_keymap_mapping.py` (BAD 0, 미검토 < 100), 고친 키마다 헤드리스 테스트 (`tests/test_step107_keys.py`: 키컨피그
데이터 + 연산자 동작).

## 한 것

- `keymap/maya_patches.py` `patch_key_batch_3`: 위 표의 틀린 키 7 묶음 제거 + Maya 뜻으로 다시 묶음, 없던 키 (메뉴 막대 3, Alt+B,
  스킨 페인트 u / n / b / Alt+F / Alt+C / Ctrl+Alt+C·V, 조각 Ctrl+0–9 / b / m / Shift+U / Ctrl+Shift+I, Graph Editor h / j, 북마크 7,
  Ctrl+F, Ctrl+Shift+%, UV 7 / 5). 편집기 자신의 같은 키 (Ctrl+F 찾기·필터, Clip / Curve Alt+T, Sequencer Shift+M …) 는 그 편집기에서
  이기도록 shadows 로 선언.
- 새 연산자 `operators/key_batch3.py` (`maya_kit.cycle_background`, `main_menubar_toggle`, `color_feedback`, `paint_operation` +
  메뉴 `MAYAKIT_MT_paint_operation`), `operators/bookmarks.py` (`maya_kit.bookmark_create` / `bookmark_frame`).
- `keymap/mapping.py`: 새 KIT 43 · IC 16 · NO 160 행 (Time Editor / Node Editor / Hypershade / XGen / Profiler / Hypergraph /
  Shape · Pose 편집기 / UV 조각 브러시 / Render View 노출·감마 등은 이유와 함께 NO), 빈 Maya 바인딩 (`nameCommand ""`) 은
  `line:<n>` 으로. `CONTEXT_KEYMAPS` 에 sculptMeshCache.
- `docs/keymap_mapping.md` 재생성: **구현 198 (155), IC 일치 31 (15), 해당 없음 171 (11), 미검토 0 (219)**, macOS 68.
- 테스트: 새 `tests/test_step107_keys.py` (13: 고친 키마다 키컨피그 + 동작 — 대칭 토글, 계층 이동, 배경 순환 값, 북마크 범위,
  조각 브러시 이름이 Blender 필수 라이브러리에 있는지, 미검토 0), `test_keymap_maya._STACKS` 에 Weight Paint / Sculpt,
  `test_step35` 의 F1 기대값.

## 검증

- `python tools/gen_keymap_mapping.py`: 오류 없음 (BAD 0), 미검토 0 (< 100 목표).
- 헤드리스 `python tests/run.py`: **805/805** (96 파일; test_step35 F1 기대값 고친 뒤 재실행 6/6).
- GUI `python tests/gui/run.py`: **1060/1060** (84 파일, 키 변경으로 깨진 GUI 테스트 없음).

## 남은 것

- Maya 의 홀드-드래그 키 (b / m / n) 는 Blender radial control (누르고 놓은 뒤 마우스 이동, 클릭 확정) — 누르는 동안만 바뀌는 Maya
  감각과 다름 (manual_checks).
- u 페인트 연산은 마킹 메뉴가 아니라 보통 메뉴. Shift+B (아래 반지름), Ctrl+. / Ctrl+, (스킨 페인트 모드), Graph Editor l (값 기준선)
  은 Blender 에 없음 (NO).
- Alt+B 의 그라데이션 단계 (Blender 는 전역 테마).
- NO 로 분류한 편집기 키 (Time Editor 36, Node Editor / Hypershade 57 등) 는 그 편집기를 Maya 처럼 만들 때 다시 볼 것.
