# Blender 5.x 호환 (step 118, 153)

대상은 그대로 Blender 4.5 LTS (결정 4). 이 문서는 5.0 / 5.1 / 5.2 에서 바뀐 Python API 가 킷에 주는 영향, 대응, 버전별
측정 결과를 적는다. **버전 분기는 한 곳 — `src/allset/compat.py`** (`test_step118_compat.test_version_checks_only_in_compat`
가 다른 모듈의 `bpy.app.version` 을 막음). 각 도우미는 4.5 동작을 먼저 하므로 4.5 는 바뀌지 않는다.

측정에 쓴 Blender: 공식 `download.blender.org/release/` 의 각 5.x 마이너 최신 Windows x64 포터블 zip (sha256 확인), 저장소 밖
`C:/Users/ohnsk/AppData/Local/allset_blenders/blender-<ver>-windows-x64/` (2026-10-19 기준 5.0.1, 5.1.2, 5.2.2 — 5.3 은 아직 없음).
4.5 = 설치된 4.5.4 LTS.

근거: 릴리스 노트 `developer.blender.org/docs/release_notes/5.{0,1,2}/python_api/` (+ 5.0 animation_rigging, user_interface,
theme_migration_api), 그리고 실측 (헤드리스 RNA 덤프·동작 탐침, 번들 스크립트 diff — `tmp/r118/`, 저장소에 넣지 않음).

## 영향 목록과 대응

### 5.0

| 바뀐 것 | 킷에서 쓰는 곳 | 영향 | 대응 (`compat.py`) |
|---|---|---|---|
| bpy.props 값의 dict 접근 제거 (`prefs["x"] = v`) | `switch.py` (테마 / Make Blender Maya 옵션을 콜백 없이 끄기) | **깨짐**: `TypeError` (switch 왕복 3 테스트) | 버전 분기 없이 `preferences.set_quiet()` (QUIET 집합 → 콜백이 건너뜀) |
| 레거시 `Action.fcurves` / `groups` 제거 (layered action) | Graph Editor 키 선택, 정적 채널 삭제, 속성 이름 바꾸기, Channel Box | **깨짐** (Graph Editor 탄젠트 / 키 / Time Slider 틱 테스트) | `fcurve_owners` / `action_fcurves` / `id_fcurves` / `id_fcurve_collection` (슬롯 channelbag) |
| Python 으로 만든 드라이버: Generator 모디파이어 대신 키 (0,0)(1,1) + LINEAR 외삽 | Set Driven Key | **깨짐** (45° 대신 84°, 마지막 키 뒤 상수 아님) | `driven_key.ensure_driver` 가 키도 지우고 외삽 CONSTANT (분기 불필요) |
| `ToolSettings.uv_select_mode` 의 `ISLAND` 제거 → `use_uv_select_island` | UV Shell 모드, UV 마킹 메뉴 고르기, UV Toolkit | **깨짐** | `uv_island_mode` / `set_uv_island_mode` |
| UV 선택이 UV 층에서 루프로: `BMLoopUV.select/select_edge` → `BMLoop.uv_select_vert/edge` | UV 동기화 끈 Cut / Sew / 섬 고르기 | **깨짐** (GUI 스윕에서 발견) | `uv_vert_selected` / `uv_edge_selected` |
| `ImageFormatSettings.media_type` 먼저 (`FFMPEG` 는 `VIDEO` 일 때만) | Playblast, Render Settings 기본값 | **깨짐** | `set_file_format`, Playblast 저장·복원에 `media_type` 추가 |
| `SequenceEditor.sequences` 제거 | Audio > Delete Sounds | **깨짐** | `strips` |
| `Bone.hide` = 편집 본 표시만, 포즈·오브젝트 표시 = `PoseBone.hide` | 관절 Channel Box Visibility, 선택 우선순위, Outliner | 동작 (숨겨도 안 숨음) | `bone_hidden` / `set_bone_hidden` |
| Properties 탭 플래그 추가 (`show_properties_strip`, `_strip_modifier`) — 4.5 로 저장한 파일에서 켜진 채 열림 | Maya 도크 역할 (숨은 탭 플래그, step 116) | **깨짐**: Maya 레이아웃 템플릿 (그때 Allset) 의 도크 스택을 못 알아봄 | `LATER_PROPERTIES_TABS` 는 역할 판정에서 뺌 |
| Timeline = Dope Sheet 모드: `TIME_HT_editor_buttons`, `TIME_MT_editor_menus`, `TIME_MT_marker` 없음 | Time Slider / Range Slider 헤더, Marker 메뉴 | 켜기 실패 (step 53 에서 고침) / Marker 메뉴 빈칸 | `timeline_header_classes`, `timeline_marker_menu` (`DOPESHEET_MT_marker`) |
| 테마 구조 재편 (300 개 넘게 이동·삭제, 공식 표 theme_migration_api) | `theme/studio_grey.xml` (4.5 형식) | 동작: 5.x 에서 Maya 패널색·핸들색·이음매/날카로움 색 등이 Blender 값 | `theme.MOVED` = 공식 표 55 항목 전부 (이전: 26). 후속 없이 삭제된 설정 (face_dot 등) 은 Blender 값 |
| `rna_xml` → `_rna_xml` (비공개) | 테마 적용·복원, 스위치 스냅숏 | 깨짐 (step 53) | `rna_xml()` |
| `np.array(Matrix)` 가 float32 | 선택 우선순위 화면 거리 | 정밀도 | `dtype=np.float64` (분기 불필요) |
| `Material.use_nodes` 폐기 예정 (항상 노드, 쓰면 경고) | 재질 만들기, Hypershade, AE | 경고 | `ensure_material_nodes` / `material_uses_nodes` |
| IC 키맵: Ctrl+G 가 메뉴 호출 | 키맵 패치 | (step 53 에서 이벤트로 제거) | `keymap/patch.STRICT` = `compat.IS_TARGET` |
| 메뉴 · 팝업이 클릭할 때까지 열림 (`PreferencesView.menu_close_leave` 기본 꺼짐, 5953ff318c) | 옵션 상자를 누르고 있다 열기 (step 146: 포인터를 멀리 보내 Maya 메뉴를 닫음) | 동작: Maya 메뉴가 옵션 창 아래 열린 채 | `menus_close_on_leave` (읽기만, 킷은 환경설정을 안 씀): 꺼져 있으면 멀리 보내기를 건너뜀, 메뉴는 클릭 / Esc 로 닫힘 (step 153) |
| `ToolSettings.unified_paint_settings` → 페인트 모드마다 (`tool_settings.weight_paint.unified_paint_settings`), `unprojected_radius` (반지름) → `unprojected_size` (**지름**, 「Diameter of brush in Blender units」 실측 5.0.1 / 5.2.3) | Skin > Paint Skin Weights ❒ (Value / Opacity / Radius(U)) | **깨짐**: `AttributeError`, 메시가 Maya 설정 없이 Weight Paint 에 남음 (#90, step 153) | `unified_paint_settings(ts, paint)` / `unprojected_radius` / `set_unprojected_radius` (5.x 는 지름 = 2 × Maya 반지름) |
| `Bone.select` 제거 (선택 = `PoseBone.select`) — step 110 / 199 코드가 직접 읽음 | Skin > Move Weights to Influences (선택 관절), 영향 관절 목록 (`rig_maya`) | **깨짐**: `AttributeError` (step 200) | 이미 있던 shim `channel_box.bone_selected` / `set_bone_selected` 로 (테스트도) |
| 새 World 가 항상 노드 (Background 기본 회색이 장면을 밝힘) | 테스트의 Cycles 조명 링크 탐침 | 테스트만: 링크 안 된 큐브가 0.149 | 테스트가 Background Strength 0 |
| 상단 바 첫 메뉴 위치: 영역 왼쪽 → 첫 Maya 메뉴 1.48 u → **1.25 u** (UI 1.0: 25 px, 1.25: 31 px; 5.0.1 / 5.1.2 / 5.2.3 같음) | 옵션 상자 ❒ 클릭 모델 (`ui/option_click`, step 183) | 동작: 메뉴 바에서 연 메뉴의 ❒ 칸이 6 px 오른쪽 → ❒ 클릭이 라벨 클릭으로 | `MENU_BAR_LEAD_UNITS` (step 200) |
| BGL 제거, GLSL 소스 셰이더 제거, EEVEE id, Alembic/USD 인자, 브러시 이름 | — | 없음 (안 씀; 키맵 브러시 속성은 설치된 IC 에서 복사) | — |

### 5.1

| 바뀐 것 | 킷 | 영향 | 대응 |
|---|---|---|---|
| `mesh.loop_multi_select` 제거 | Select Edge Loop / Ring 메뉴 | 깨짐 (step 53) | `has_op` + `select_edge_loop_multi` / `_ring_multi` |
| `GPUFrameBuffer.read_color` 범위 밖이면 `ValueError` | Outliner 세트 행 찾기, Range Slider 막대 찾기 (그리기 처리기 안) | 그리기 오류 가능 | `read_region_row` (영역 안으로 제한, 오류면 None) |
| IC 새 키맵 "Grease Pencil Draw Mode" (Alt+I, Ctrl+Shift+E), Sequencer Ctrl+Shift+R, Preferences Ctrl+F | 킷 Screen 키 (Maya 키 넣기 / 검색) | 가림 테스트 실패 | `KEY_STEP_SHADOWS` / `SEARCH_SHADOWS` 에 선언 (그 편집기 안에서는 Blender 것이 먼저 — 4.5 의 다른 편집기와 같은 규칙) |
| Node Editor `node.viewer_border` (Z) 제거 | 키맵 패치 | 드리프트 한 줄 (무해) | 그대로 (`patch.DRIFT`) |
| 영역 경계 강조 그리기 (`screen_draw_move_highlight`) 가 창이 아직 그리는 screen 을 읽음 | Maya → Blender 전환이 Maya 작업 공간을 `workspace.delete` 로 지움 (`window.workspace` 변경은 다음 이벤트 루프에 적용) | **크래시** (5.1.2 GUI 스윕, EXCEPTION_ACCESS_VIOLATION) | 버전 무관: 창이 실제로 떠난 뒤 타이머에서 `bpy.data.batch_remove` (`workspace.delete` 는 override 와 상관없이 창의 활성 작업 공간을 지움 — 실측) |
| Python 3.13 | — | 없음 (src 컴파일 경고 0, step 53 테스트) | — |

### 5.2

| 바뀐 것 | 킷 | 영향 | 대응 |
|---|---|---|---|
| `bmesh.ops.pointmerge_facedata(vert_snap=)` → `vert_target=` | Target Weld (UV 유지) | **깨짐** | `pointmerge_facedata` |
| 「Only Insert Available」 공장값 켜짐 | Maya Auto Key 프리셋 | 없음 (이미 켜져 있으면 프리셋이 아무것도 안 바꿈, 끄면 공장값으로) | 테스트만 공장값 기준 |
| IC Ctrl+S 계열에 `show_save_modified_images_dialog=True` | 킷의 Save Scene / Save Scene As | 동작: 저장 안 된 이미지 확인 창이 안 뜸 | `save_dialog_args` |
| 가장자리 맞붙은 영역이 같이 안 움직임, 사이드바 탭 항상 보임 | Tool Box 열 맞춤, 뷰포트 사이드바 | GUI 확인 항목 | 아래 시각 확인 |
| GN 모디파이어 입력이 ID 속성 (`md["Socket_1"]`, `_use_attribute` / `_attribute_name`) 에서 `md.properties.inputs.Socket_1.value` / `.type` ('VALUE' / 'ATTRIBUTE') / `.attribute_name` 로 (옛 쓰기는 `TypeError`) | Deform > Wire (`wire_deformer`, step 169) | **깨짐**: Wire 만들기 실패 (step169 8 테스트, step 200) | `GN_INPUT_STRUCT`, `gn_input_get` / `gn_input_set` / `gn_input_attribute` |
| `FunctionNodeCompare` 가 지금 data type 의 소켓 둘만 가짐 (4.5 – 5.1: 모든 type 의 A / B, INT = 인덱스 2 / 3) | Deform > Morph / Jiggle (`deformers_205b`, step 205) | **깨짐**: 노드 그룹 만들기 IndexError (step205_deform_b 7 테스트, step 212) | `compare_inputs` (identifier `A_INT` / `B_INT` …, 없으면 처음 둘) |
| `-b` 에서 방금 읽은 home 파일 / 스크립트 편집이 `bpy.data.is_dirty` 로 안 보임 (4.5 – 5.1 은 home 파일이 modified) | maya.cmds `file -new` 의 Unsaved changes (step 208) | 헤드리스 테스트만 (GUI 는 4 버전 모두 오류 냄, `gui_step208`) | 테스트가 `-b` 상태를 재고 그 경우만 건너뜀 |
| 조각 자동 마스킹, `template_palette(color=)` | — | 없음 | — |

## 버전별 결과

### step 212 (2026-10-26, 최신 전체)

헤드리스 = `ALLSET_SANDBOX=<ver> python tests/run.py --no-build --blender <exe>` 전체 243 파일 (zip 은 4.5 로 빌드), Blender 둘씩.
GUI = 버전마다 `-k step203_outliner,step204,step205,step206,step207,step208,step209,step211,step5_layout,step60_switch` (10 파일).
steps 202–211 (Graph Editor list, anim layers 4, Deform 2, UV 2, Curves 3, maya.cmds 2, Reference Editor, audit 16 fixes) 의 첫
5.x 통과 (`docs/steps/step_212.md`).

| Blender | 헤드리스 첫 실행 | 헤드리스 (수정 뒤) | GUI (10 파일) |
|---|---|---|---|
| 4.5.4 LTS (대상) | (step 211: 2032 / 2032) | **2032 / 2032** | (step 211 관련 160 / 160) |
| 5.0.1 | 2031 / 2032 (테스트의 `Bone.select`) | 고친 파일 63 / 63 | **88 / 88** |
| 5.1.2 | **2032 / 2032** | 고친 파일 63 / 63 | **88 / 88** |
| 5.2.3 LTS | 2022 / 2032 (+ Compare 노드 7, `-b` modified 2) | **2032 / 2032** | **88 / 88** |

- 고친 것: `compat.compare_inputs` (5.2 Compare 노드, Morph / Jiggle), 테스트 둘 (`test_step203_list` 가 `Bone.select` 대신 kit shim,
  `test_step208_cmds` 의 Unsaved changes 는 `-b` 가 modified 를 보일 때만 — GUI 는 4 버전 모두 확인).
- step 211 의 Outliner 순서 보정 (불안정 qsort 회전) 은 5.0.1 / 5.1.2 / 5.2.3 GUI 에서도 그대로 맞음 (`gui_step211_fix_batch` 10 / 10).

### step 200 (2026-10-25)

헤드리스 = `ALLSET_SANDBOX=<ver> python tests/run.py --no-build --blender <exe>` 전체 226 파일 (zip 은 4.5 로 한 번 빌드),
한 번에 Blender 둘. GUI = 5.2.3 에서 `-k step183,step186,step187` (step186 은 GUI 파일 없음 → 2 파일) + step183 UI 1.0.
step 153 이후 (step 154–199) 의 버전 민감 코드 첫 5.x 통과 (`docs/steps/step_200.md`).

| Blender | 헤드리스 첫 실행 | 헤드리스 (수정 뒤) | GUI |
|---|---|---|---|
| 4.5.4 LTS (대상) | (step 199: 1841 / 1841) | **1844 / 1844** | step183 **24 / 24** |
| 5.0.1 | 1841 / 1844 (Bone.select 2, Cycles 탐침) | **1844 / 1844** | step183: 첫 메뉴 6 px (수정 전 확인) |
| 5.1.2 | 1840 / 1844 (+ USD 왕복 = 동시 실행이 `tmp/file_io` 공유) | **1844 / 1844** | 〃 |
| 5.2.3 LTS | 1834 / 1844 (+ Wire 8: GN 입력 API) | **1844 / 1844** | step183 / 187 **28 / 28**, step183 UI 1.0 **24 / 24** |

- 고친 것: `compat.gn_input_*` (5.2 GN 입력), `compat.MENU_BAR_LEAD_UNITS` (5.x 메뉴 바), `Bone.select` 직접 읽기 2 곳 → shim,
  테스트 3 개 (Bone.select, 5.0 World 노드, `tmp/<sandbox>/file_io` 로 분리), step183 GUI 의 메뉴 가장자리 측정 (5.x 는 옆 영역이
  메뉴 배경색과 같아 넓게만 잴 수 있음 — ❒ 칸 검사는 그대로 엄격).

### step 153 (2026-10-24, 최신 전체)

헤드리스 = `ALLSET_SANDBOX=<ver> python tests/run.py --blender <exe>` 전체 169 파일 (수정 뒤), GUI = `tests/gui/run.py` 전체 146 파일
(2 개 GUI_SKIP) 한 번 + 실패 파일 `-k` 재실행 (`docs/steps/step_153.md`). 5.2.x 는 최신 패치 5.2.3 으로 잼 (5.2.2 대체).

| Blender | 헤드리스 | GUI 전체 (첫 실행) | GUI 실패 파일 재실행 (수정 뒤) |
|---|---|---|---|
| 4.5.4 LTS (대상) | **1398 / 1398** (1394 + `test_step153_compat` 4) | 1641 / 1644 (수정 뒤; 3 = `gui_step129_panel_toolbar`, 부하 중) | panel_toolbar 혼자 **36 / 36**, sweep 19 / 19 |
| 5.0.1 | **1398 / 1398** | — (5.x GUI 는 5.2.x 로 대표) | — |
| 5.1.2 | **1398 / 1398** | — | — |
| 5.2.3 LTS | **1398 / 1398** | 1622 통과 / 15 실패 | **7 파일 전부 통과** (16 / 16 + 69 / 69) |

- 15 실패 = #90 이 아닌 것들: 4.5 에서도 나는 step 151 이후 회귀 (마킹 메뉴 하위 메뉴가 넓은 N 상자로 열림 — 킷 수정, 테스트의
  Maya 기하 가정 2 개), 테스트의 5.x API 직접 사용 (`Action.fcurves`, `Bone.select`), 5.2.3 의 클릭 위치 · asset shelf 머리 띠 차이,
  그리고 **Blender 5.0 의 「메뉴는 클릭할 때까지 열림」** (`menu_close_leave`, 위 5.0 표).
- 첫 실행 (#90 수정만, step 153 처음): 네 버전 모두 헤드리스 1394 / 1394 (step 145 의 5.2.2 1305 / 1308 → 실패 3 개 = #90).

### step 118 (2026-10-19)


아래 표 = **step 118 측정 (2026-10-19, 그때의 코드)** — 네 버전을 모두 같은 날 잰 마지막 전체 비교. 그 뒤 단계에서 테스트가 늘어 숫자는
지금 전체와 다르다: 최신 실행은 **4.5.4, step 124 (2026-10-20): 헤드리스 890 / 890, GUI 1142 / 1142**; 5.x 는 그 뒤 단계마다 바뀐 기능의
파일만 다시 돌렸다 (`docs/steps/step_119.md` 이후). 헤드리스 = `tests/run.py` 전체 (그때 104 파일), GUI = `tests/gui/run.py` 전체 (그때 89 파일, 기본 UI 배율 =
이 PC 125 %), 설치 왕복 = `tools/release_check.py` (extension validate, 깨끗한 설정에 설치 → 켜기, 사용자 셋업 유지, 끄기 = 전부 복원,
Remove, 남는 킷 파일 0, opt-in · 레이아웃 스크린샷).

| Blender | 헤드리스 | GUI | 설치 왕복 | 시각 | 이 단계 전 (step 117) |
|---|---|---|---|---|---|
| 4.5.4 LTS (대상) | **877 / 877** | **1121 / 1121** | **23 / 23** | 테마 ΔE00 > 5: 0 / 38, 장면 3 / 3, 밀도 5 / 6 | 869 / 869 |
| 5.0.1 | **877 / 877** | **1121 / 1121** | **23 / 23** | 0 / 38, 3 / 3, 4 / 6 | 850 / 869 |
| 5.1.2 | **877 / 877** | **1121 / 1121** (세 세션, 아래) | **23 / 23** | 0 / 38, 3 / 3, 4 / 6 | 848 / 869 |
| 5.2.2 LTS | **877 / 877** | **1121 / 1121** | **23 / 23** | 0 / 38, 3 / 3, 4 / 6 | 845 / 869 |

- 처음 측정 (이 단계의 수정 전, 같은 테스트 876 개): 4.5 876, 5.0.1 856 (20 실패), 5.1.2 855 (21), 5.2.2 852 (24). 5.2.2 GUI 첫 전체:
  871 / 883 (12 실패, 수동 스윕이 M73 에서 중단) — 위 표의 원인들 (테마 경로, Range Slider, UV, 브러시, 도크, Auto Key 공장값).
- 5.1.2 GUI: 수동 스윕 (`gui_manual_sweep`, 검사 331 개) 을 한 세션으로 돌리면 5.1.2 에서만 같은 지점 (검사 79, M59-9 「2 Points to 2
  Points」 직전, Blender 가 `Win32 Error# (1407)` 창 클래스 없음을 반복 출력) 에서 멈춤 — 세 번 재현, 4.5 / 5.0.1 / 5.2.2 는 한 세션으로
  통과. 같은 단계들을 `ALLSET_SWEEP_ONLY` 로 두 세션에 나누면 전부 통과 (173 + 158 = 331). 나머지 88 파일 790 / 790. 합계 1121 / 1121.
  두 번째 묶음에서 실제 크래시 하나를 찾아 고침 (위 5.1 표: Maya → Blender 전환). 멈춤 자체는 원인 미확정 (남은 것).
- 전환 수정 뒤 `gui_step60` + 스윕 M60 을 네 버전에서 다시 돌림: 11 / 11 + 11 / 11 × 4.
- 시각: 버전별 나란히 그림·표, `tmp/look_env_<ver>/shots/` 를 직접 봄 — 레이아웃 (메뉴 막대, Status
  Line, 셸프, Tool Box, Outliner, 탭 스택), Maya 테마 색, 핫박스, Move / Rotate 매니퓰레이터, RMB 마킹 메뉴 + 목록, Channel Box 가
  4.5 와 같다. 차이: 5.x 타임라인은 한 줄 (재생 버튼이 Range Slider 줄 오른쪽 끝, 위 「5.x Time Slider」), Time Slider 눈금 간격이
  Blender 5.x 의 것 (5, 10 … 대신 6, 12 …). 「밀도」 5 / 6 → 4 / 6 은 Create 메뉴 줄 간격 측정이 5.x 메뉴 그림자 가장자리를 다른 열로
  잡은 것 (스크린샷에서 메뉴 위치·모양 같음) — 측정 도구 쪽.

## 테마 차이 (step 119)

5.0 에서 테마 구조가 크게 바뀌어 4.5 형식의 `studio_grey.xml` 하나에 이동 표 (`theme.MOVED`) 를 덧대는 것으로는 5.x 에만 있는 키가
Blender 기본색으로 남았다. step 119 부터 **버전마다 테마 파일**: `tools/make_theme.py` 가 각 Blender 에서 돌아 4.5 =
`theme/studio_grey.xml` (그대로), 5.x = `theme/studio_grey_5.0.xml` / `_5.1.xml` / `_5.2.xml` (4.5 킷 값 → MOVED 경로로 옮김 →
5.x 새 키 `FIVE_X`) 를 만든다. 실행 중인 Blender 는 `compat.theme_file` 이 자기 버전 이하의 가장 새 파일을 고르고, `MOVED` 는 그 파일이
없을 때만 쓰는 대체 경로.

### 팩토리 테마 키 비교 (`python tools/theme_diff.py --md`)

| Blender | 키 수 | 4.5 대비 새 키 | 없어진 키 | 그중 옮김·합침 (5.0 공식 표) | 후속 없음 |
|---|---|---|---|---|---|
| 4.5.4 | 1014 | — | — | — | — |
| 5.0.1 | 696 | 92 | 410 | 226 | 184 |
| 5.1.2 | 701 | 98 | 411 | 226 | 185 |
| 5.2.2 | 703 | 100 | 411 | 226 | 185 |

- 새 키의 처리: 옮겨진 값은 4.5 킷 값 그대로 (`common.anim.*`, `common.curves.*`, `regions.*`, `user_interface.panel_*`,
  `view_3d.seam/sharp/crease/bevel/freestyle`), `wcol_*.outline_sel` = 같은 위젯의 `outline` (Maya 는 선택 외곽선 색이 따로 없음),
  `wcol_curve` = `wcol_regular`, `FIVE_X`: `view_3d.grid_major` 0.25 (Maya 격자는 한 색), `user_interface.panel_active` = Maya 선택색,
  `panel_outline` 투명 (평평한 Maya 패널, step 44), `regions.scrubbing.text` = 4.5 Dope Sheet 글자색.
- 일부러 Blender 값으로 둔 10 키 (`make_theme.KEEP_FACTORY_5X`, Maya 에 대응 없음 / Maya 워크플로우에서 안 그려짐): `user_interface.link`,
  `axis_w`, `view_3d.grid_axis_brightness` (5.2, Maya 레이아웃 뷰는 격자 축선을 숨김), `gp_wire_edit`, `node_editor.node_outline`,
  `preferences.match`, `common.anim.scene_strip_range`, 5.2 Dope Sheet `anim_interpolation_*` 3 개.
  `test_step119_theme_5x.test_no_blender_default_left_on_new_keys` 가 나머지 새 키에 Blender 기본값이 남지 않았는지 본다.
- 후속 없이 없어진 키 (`face_dot`, `*.space.button_*`, `tab_*`, `lastsel_point` 등) 는 5.x 에 그릴 곳이 없음 — 영향 없음.
- 공유 키 비교 (`python tools/theme_xml_diff.py`): 5.x 파일과 4.5 파일의 공유 키 661–662 개 중 값이 다른 것 1 개
  (`view_3d.freestyle` 계열 알파 — 4.5 RGB, 5.x RGBA; 색은 같음).

### 테마 밖의 색 차이

- **셸프 아이콘이 5.x 에서 어두웠음**: 5.0 의 `gpu.shader.from_builtin('IMAGE')` 는 더 이상 선형 → sRGB 변환을 하지 않음.
  `compat.LINEAR_IMAGE_SHADER` (5.0+ `IMAGE_SCENE_LINEAR_TO_REC709_SRGB`) 로 `ui/shelf.py` 아이콘이 4.5 와 같은 밝기 (잘라 낸 그림 비교).
- 5.x Outliner 활성 행 외곽선: 5.x 가 `outliner.active` 색으로 활성 행에 외곽선을 그림 — 그 외곽선만의 테마 키가 없어 4.5 와 다름
  (남은 것).

### 버전 × 색 지표

Maya 모양 비교 (유지보수 도구) — 네 버전 모두 같은 값:

| Blender | 테마 ΔE00 > 5 | 픽셀 점 일치 | 뷰포트 | 영역 | 장면 | 밀도 | 격자 | 뷰 가구 |
|---|---|---|---|---|---|---|---|---|
| 4.5.4 | 0 / 38 | 4 / 25 (13 없음) | 11 / 12 | 5 / 12 | 3 / 3 | 5 / 6 | 4 / 4 | 2 / 3 |
| 5.0.1 | 0 / 38 | 4 / 25 | 11 / 12 | 5 / 12 | 3 / 3 | 5 / 6 | 4 / 4 | 2 / 3 |
| 5.1.2 | 0 / 38 | 4 / 25 | 11 / 12 | 5 / 12 | 3 / 3 | 5 / 6 | 4 / 4 | 2 / 3 |
| 5.2.2 | 0 / 38 | 4 / 25 | 11 / 12 | 5 / 12 | 3 / 3 | 5 / 6 | 4 / 4 | 2 / 3 |

(step 118 에서 5.x 밀도 4 / 6 이던 것은 측정점 문제 — 메뉴 탐지 x 시작, 5.x 타임라인 time_field 대체점, Outliner 검색칸 측정점을
비교 도구 쪽에서 고침.)

버전 비교 (4.5 대비 같은 장면, ±3 px 안에서 가장 작은 ΔE00):

| Blender | 평균 ΔE00 (레이아웃 장면) | ΔE00 > 5 픽셀 | ΔE00 2–5 픽셀 | 첫 화면 (opt-in 전, Blender 자기 화면) |
|---|---|---|---|---|
| 5.0.1 | 0.21–0.24 | 0.83–0.97 % | 0.62–0.78 % | 17.7 % |
| 5.1.2 | 0.22–0.24 | 0.83–0.97 % | 0.62–0.78 % | 17.1 % |
| 5.2.2 | 0.22–0.24 | 0.83–0.97 % | 0.62–0.78 % | 17.1 % |

남은 1 % 미만은 색이 아니라 배치: 5.x 한 줄 타임라인 (재생 버튼 위치), Time Slider 눈금 간격, Outliner 활성 행 외곽선. 첫 화면은
opt-in 전의 Blender 5.x 기본 화면이라 킷과 무관.

<details><summary>키 목록 (버전별 새 키 / 후속 없이 없어진 키)</summary>

#### 5.0.1: +92 / −410 (옮김 226, 후속 없음 184)

- 새 키: `common.anim.channel`, `common.anim.channel_group`, `common.anim.channel_group_active`, `common.anim.channel_selected`, `common.anim.channels`, `common.anim.channels_sub`, `common.anim.keyframe`, `common.anim.keyframe_breakdown`, `common.anim.keyframe_breakdown_selected`, `common.anim.keyframe_extreme`, `common.anim.keyframe_extreme_selected`, `common.anim.keyframe_generated`, `common.anim.keyframe_generated_selected`, `common.anim.keyframe_jitter`, `common.anim.keyframe_jitter_selected`, `common.anim.keyframe_moving_hold`, `common.anim.keyframe_moving_hold_selected`, `common.anim.keyframe_selected`, `common.anim.long_key`, `common.anim.long_key_selected`, `common.anim.playhead`, `common.anim.preview_range`, `common.anim.scene_strip_range`, `regions.asset_shelf.back`, `regions.asset_shelf.header_back`, `user_interface.axis_w`, `view_3d.bevel`, `regions.channels.back`, `regions.channels.text`, `regions.channels.text_selected`, `view_3d.crease`, `common.curves.handle_align`, `common.curves.handle_auto`, `common.curves.handle_auto_clamped`, `common.curves.handle_free`, `common.curves.handle_sel_align`, `common.curves.handle_sel_auto`, `common.curves.handle_sel_auto_clamped`, `common.curves.handle_sel_free`, `common.curves.handle_sel_vect`, `common.curves.handle_vect`, `common.curves.handle_vertex`, `common.curves.handle_vertex_select`, `common.curves.handle_vertex_size`, `view_3d.freestyle`, `node_editor.node_outline`, `user_interface.panel_active`, `user_interface.panel_back`, `user_interface.panel_header`, `user_interface.panel_outline`, `user_interface.panel_sub_back`, `user_interface.panel_text`, `user_interface.panel_title`, `regions.scrubbing.back`, `regions.scrubbing.text`, `regions.scrubbing.time_marker`, `regions.scrubbing.time_marker_selected`, `view_3d.seam`, `view_3d.sharp`, `regions.sidebars.back`, `regions.sidebars.tab_back`, `user_interface.wcol_box.outline_sel`, `user_interface.wcol_curve.inner`, `user_interface.wcol_curve.inner_sel`, `user_interface.wcol_curve.item`, `user_interface.wcol_curve.outline`, `user_interface.wcol_curve.outline_sel`, `user_interface.wcol_curve.roundness`, `user_interface.wcol_curve.shadedown`, `user_interface.wcol_curve.shadetop`, `user_interface.wcol_curve.show_shaded`, `user_interface.wcol_curve.text`, `user_interface.wcol_curve.text_sel`, `user_interface.wcol_list_item.outline_sel`, `user_interface.wcol_menu.outline_sel`, `user_interface.wcol_menu_back.outline_sel`, `user_interface.wcol_menu_item.outline_sel`, `user_interface.wcol_num.outline_sel`, `user_interface.wcol_numslider.outline_sel`, `user_interface.wcol_option.outline_sel`, `user_interface.wcol_pie_menu.outline_sel`, `user_interface.wcol_progress.outline_sel`, `user_interface.wcol_pulldown.outline_sel`, `user_interface.wcol_radio.outline_sel`, `user_interface.wcol_regular.outline_sel`, `user_interface.wcol_scroll.outline_sel`, `user_interface.wcol_tab.outline_sel`, `user_interface.wcol_text.outline_sel`, `user_interface.wcol_toggle.outline_sel`, `user_interface.wcol_tool.outline_sel`, `user_interface.wcol_toolbar_item.outline_sel`, `user_interface.wcol_tooltip.outline_sel`

- 후속 없이 없어진 키: `view_3d.act_spline`, `properties.active_modifier`, `graph_editor.channels_region`, `sequence_editor.draw_action`, `view_3d.edge_bevel`, `view_3d.edge_facesel`, `image_editor.face_back`, `*.face_dot` (2: image_editor, view_3d…), `image_editor.face_front`, `image_editor.face_retopology`, `*.freestyle_face_mark` (2: image_editor, view_3d…), `*.lastsel_point` (2: graph_editor, view_3d…), `node_editor.layout_node`, `nla_editor.nla_track`, `*.paint_curve_handle` (2: image_editor, view_3d…), `*.paint_curve_pivot` (2: image_editor, view_3d…), `node_editor.pattern_node`, `node_editor.selected_text`, `*.space.button_text` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.button_text_hi` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.button_title` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.execution_buts` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.navigation_bar` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.tab_active` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.tab_inactive` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.tab_outline` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space_list.list_title` (7: clip_editor, dopesheet_editor, graph_editor, nla_editor…), `clip_editor.strips`, `clip_editor.strips_selected`, `view_3d.text_keyframe`, `dopesheet_editor.value_sliders`, `*.vertex_unreferenced` (2: graph_editor, image_editor…), `*.view_sliders` (2: dopesheet_editor, nla_editor…), `*.window_sliders` (2: graph_editor, sequence_editor…)

#### 5.1.2: +98 / −411 (옮김 226, 후속 없음 185)

- 새 키: `common.anim.channel`, `common.anim.channel_group`, `common.anim.channel_group_active`, `common.anim.channel_selected`, `common.anim.channels`, `common.anim.channels_sub`, `common.anim.keyframe`, `common.anim.keyframe_breakdown`, `common.anim.keyframe_breakdown_selected`, `common.anim.keyframe_extreme`, `common.anim.keyframe_extreme_selected`, `common.anim.keyframe_generated`, `common.anim.keyframe_generated_selected`, `common.anim.keyframe_jitter`, `common.anim.keyframe_jitter_selected`, `common.anim.keyframe_moving_hold`, `common.anim.keyframe_moving_hold_selected`, `common.anim.keyframe_selected`, `common.anim.long_key`, `common.anim.long_key_selected`, `common.anim.playhead`, `common.anim.preview_range`, `common.anim.scene_strip_range`, `dopesheet_editor.anim_interpolation_constant`, `dopesheet_editor.anim_interpolation_linear`, `dopesheet_editor.anim_interpolation_other`, `regions.asset_shelf.back`, `regions.asset_shelf.header_back`, `user_interface.axis_w`, `view_3d.bevel`, `regions.channels.back`, `regions.channels.text`, `regions.channels.text_selected`, `view_3d.crease`, `common.curves.handle_align`, `common.curves.handle_auto`, `common.curves.handle_auto_clamped`, `common.curves.handle_free`, `common.curves.handle_sel_align`, `common.curves.handle_sel_auto`, `common.curves.handle_sel_auto_clamped`, `common.curves.handle_sel_free`, `common.curves.handle_sel_vect`, `common.curves.handle_vect`, `common.curves.handle_vertex`, `common.curves.handle_vertex_select`, `common.curves.handle_vertex_size`, `view_3d.freestyle`, `view_3d.gp_wire_edit`, `view_3d.grid_major`, `preferences.match`, `node_editor.node_outline`, `user_interface.panel_active`, `user_interface.panel_back`, `user_interface.panel_header`, `user_interface.panel_outline`, `user_interface.panel_sub_back`, `user_interface.panel_text`, `user_interface.panel_title`, `regions.scrubbing.back`, `regions.scrubbing.text`, `regions.scrubbing.time_marker`, `regions.scrubbing.time_marker_selected`, `view_3d.seam`, `view_3d.sharp`, `regions.sidebars.back`, `regions.sidebars.tab_back`, `user_interface.wcol_box.outline_sel`, `user_interface.wcol_curve.inner`, `user_interface.wcol_curve.inner_sel`, `user_interface.wcol_curve.item`, `user_interface.wcol_curve.outline`, `user_interface.wcol_curve.outline_sel`, `user_interface.wcol_curve.roundness`, `user_interface.wcol_curve.shadedown`, `user_interface.wcol_curve.shadetop`, `user_interface.wcol_curve.show_shaded`, `user_interface.wcol_curve.text`, `user_interface.wcol_curve.text_sel`, `user_interface.wcol_list_item.outline_sel`, `user_interface.wcol_menu.outline_sel`, `user_interface.wcol_menu_back.outline_sel`, `user_interface.wcol_menu_item.outline_sel`, `user_interface.wcol_num.outline_sel`, `user_interface.wcol_numslider.outline_sel`, `user_interface.wcol_option.outline_sel`, `user_interface.wcol_pie_menu.outline_sel`, `user_interface.wcol_progress.outline_sel`, `user_interface.wcol_pulldown.outline_sel`, `user_interface.wcol_radio.outline_sel`, `user_interface.wcol_regular.outline_sel`, `user_interface.wcol_scroll.outline_sel`, `user_interface.wcol_tab.outline_sel`, `user_interface.wcol_text.outline_sel`, `user_interface.wcol_toggle.outline_sel`, `user_interface.wcol_tool.outline_sel`, `user_interface.wcol_toolbar_item.outline_sel`, `user_interface.wcol_tooltip.outline_sel`

- 후속 없이 없어진 키: `view_3d.act_spline`, `properties.active_modifier`, `graph_editor.channels_region`, `sequence_editor.draw_action`, `view_3d.edge_bevel`, `view_3d.edge_facesel`, `image_editor.face_back`, `*.face_dot` (2: image_editor, view_3d…), `image_editor.face_front`, `image_editor.face_retopology`, `*.freestyle_face_mark` (2: image_editor, view_3d…), `dopesheet_editor.interpolation_line`, `*.lastsel_point` (2: graph_editor, view_3d…), `node_editor.layout_node`, `nla_editor.nla_track`, `*.paint_curve_handle` (2: image_editor, view_3d…), `*.paint_curve_pivot` (2: image_editor, view_3d…), `node_editor.pattern_node`, `node_editor.selected_text`, `*.space.button_text` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.button_text_hi` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.button_title` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.execution_buts` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.navigation_bar` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.tab_active` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.tab_inactive` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.tab_outline` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space_list.list_title` (7: clip_editor, dopesheet_editor, graph_editor, nla_editor…), `clip_editor.strips`, `clip_editor.strips_selected`, `view_3d.text_keyframe`, `dopesheet_editor.value_sliders`, `*.vertex_unreferenced` (2: graph_editor, image_editor…), `*.view_sliders` (2: dopesheet_editor, nla_editor…), `*.window_sliders` (2: graph_editor, sequence_editor…)

#### 5.2.2: +100 / −411 (옮김 226, 후속 없음 185)

- 새 키: `common.anim.channel`, `common.anim.channel_group`, `common.anim.channel_group_active`, `common.anim.channel_selected`, `common.anim.channels`, `common.anim.channels_sub`, `common.anim.keyframe`, `common.anim.keyframe_breakdown`, `common.anim.keyframe_breakdown_selected`, `common.anim.keyframe_extreme`, `common.anim.keyframe_extreme_selected`, `common.anim.keyframe_generated`, `common.anim.keyframe_generated_selected`, `common.anim.keyframe_jitter`, `common.anim.keyframe_jitter_selected`, `common.anim.keyframe_moving_hold`, `common.anim.keyframe_moving_hold_selected`, `common.anim.keyframe_selected`, `common.anim.long_key`, `common.anim.long_key_selected`, `common.anim.playhead`, `common.anim.preview_range`, `common.anim.scene_strip_range`, `dopesheet_editor.anim_interpolation_constant`, `dopesheet_editor.anim_interpolation_linear`, `dopesheet_editor.anim_interpolation_other`, `regions.asset_shelf.back`, `regions.asset_shelf.header_back`, `user_interface.axis_w`, `view_3d.bevel`, `regions.channels.back`, `regions.channels.text`, `regions.channels.text_selected`, `view_3d.crease`, `common.curves.handle_align`, `common.curves.handle_auto`, `common.curves.handle_auto_clamped`, `common.curves.handle_free`, `common.curves.handle_sel_align`, `common.curves.handle_sel_auto`, `common.curves.handle_sel_auto_clamped`, `common.curves.handle_sel_free`, `common.curves.handle_sel_vect`, `common.curves.handle_vect`, `common.curves.handle_vertex`, `common.curves.handle_vertex_select`, `common.curves.handle_vertex_size`, `view_3d.freestyle`, `view_3d.gp_wire_edit`, `view_3d.grid_axis_brightness`, `view_3d.grid_major`, `user_interface.link`, `preferences.match`, `node_editor.node_outline`, `user_interface.panel_active`, `user_interface.panel_back`, `user_interface.panel_header`, `user_interface.panel_outline`, `user_interface.panel_sub_back`, `user_interface.panel_text`, `user_interface.panel_title`, `regions.scrubbing.back`, `regions.scrubbing.text`, `regions.scrubbing.time_marker`, `regions.scrubbing.time_marker_selected`, `view_3d.seam`, `view_3d.sharp`, `regions.sidebars.back`, `regions.sidebars.tab_back`, `user_interface.wcol_box.outline_sel`, `user_interface.wcol_curve.inner`, `user_interface.wcol_curve.inner_sel`, `user_interface.wcol_curve.item`, `user_interface.wcol_curve.outline`, `user_interface.wcol_curve.outline_sel`, `user_interface.wcol_curve.roundness`, `user_interface.wcol_curve.shadedown`, `user_interface.wcol_curve.shadetop`, `user_interface.wcol_curve.show_shaded`, `user_interface.wcol_curve.text`, `user_interface.wcol_curve.text_sel`, `user_interface.wcol_list_item.outline_sel`, `user_interface.wcol_menu.outline_sel`, `user_interface.wcol_menu_back.outline_sel`, `user_interface.wcol_menu_item.outline_sel`, `user_interface.wcol_num.outline_sel`, `user_interface.wcol_numslider.outline_sel`, `user_interface.wcol_option.outline_sel`, `user_interface.wcol_pie_menu.outline_sel`, `user_interface.wcol_progress.outline_sel`, `user_interface.wcol_pulldown.outline_sel`, `user_interface.wcol_radio.outline_sel`, `user_interface.wcol_regular.outline_sel`, `user_interface.wcol_scroll.outline_sel`, `user_interface.wcol_tab.outline_sel`, `user_interface.wcol_text.outline_sel`, `user_interface.wcol_toggle.outline_sel`, `user_interface.wcol_tool.outline_sel`, `user_interface.wcol_toolbar_item.outline_sel`, `user_interface.wcol_tooltip.outline_sel`

- 후속 없이 없어진 키: `view_3d.act_spline`, `properties.active_modifier`, `graph_editor.channels_region`, `sequence_editor.draw_action`, `view_3d.edge_bevel`, `view_3d.edge_facesel`, `image_editor.face_back`, `*.face_dot` (2: image_editor, view_3d…), `image_editor.face_front`, `image_editor.face_retopology`, `*.freestyle_face_mark` (2: image_editor, view_3d…), `dopesheet_editor.interpolation_line`, `*.lastsel_point` (2: graph_editor, view_3d…), `node_editor.layout_node`, `nla_editor.nla_track`, `*.paint_curve_handle` (2: image_editor, view_3d…), `*.paint_curve_pivot` (2: image_editor, view_3d…), `node_editor.pattern_node`, `node_editor.selected_text`, `*.space.button_text` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.button_text_hi` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.button_title` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.execution_buts` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.navigation_bar` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.tab_active` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.tab_inactive` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space.tab_outline` (18: clip_editor, console, dopesheet_editor, file_browser…), `*.space_list.list_title` (7: clip_editor, dopesheet_editor, graph_editor, nla_editor…), `clip_editor.strips`, `clip_editor.strips_selected`, `view_3d.text_keyframe`, `dopesheet_editor.value_sliders`, `*.vertex_unreferenced` (2: graph_editor, image_editor…), `*.view_sliders` (2: dopesheet_editor, nla_editor…), `*.window_sliders` (2: graph_editor, sequence_editor…)

</details>

## 남은 것

- 5.3 이후: `blender_version_max = "5.3.0"` 이라 설치 안 됨. 새 마이너가 나오면 같은 순서 (zip → `ALLSET_SANDBOX=<v> tests/run.py
  --blender`, GUI, release_check, 모양 비교) 로 재고 compat 에 분기를 더한 뒤 올림.
- 5.x 테마 (step 119 이후): 후속 없이 삭제된 키는 그릴 곳이 없고, `KEEP_FACTORY_5X` 10 키만 Blender 값. 5.x Outliner 활성 행
  외곽선은 테마 키가 없어 4.5 와 다름. 새 5.x 마이너가 나오면 `python tools/make_theme.py` 로 그 버전 파일을 만들고 `theme_diff.py` 로 새 키 확인.
- 5.x Time Slider 는 사이드바가 없어 재생 버튼 위치만 Maya 와 다름 (한 줄). Blender 가 Timeline 사이드바를 다시 열게 되면 4.5 배치로.
- `_rna_xml` 은 5.x 에서 비공개 모듈 — 이후 버전에서 사라지면 테마 적용·복원을 킷 자체 XML 쓰기로 바꿔야 함.
- 5.1.2: 수동 스윕 한 세션이 검사 79 에서 멈춤 (Win32 1407, 위) — 사용자 조작에서 같은 일이 나는지 / Blender 5.1 의 GHOST 문제인지 미확정.
- 사용자 기기에서의 실제 화면 확인: `docs/manual_checks.md` 「Step 118」.
