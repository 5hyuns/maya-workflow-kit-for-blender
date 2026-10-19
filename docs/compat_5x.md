# Blender 5.x 호환 (step 118)

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
| Properties 탭 플래그 추가 (`show_properties_strip`, `_strip_modifier`) — 4.5 로 저장한 파일에서 켜진 채 열림 | Maya 도크 역할 (숨은 탭 플래그, step 116) | **깨짐**: Allset 템플릿의 도크 스택을 못 알아봄 | `LATER_PROPERTIES_TABS` 는 역할 판정에서 뺌 |
| Timeline = Dope Sheet 모드: `TIME_HT_editor_buttons`, `TIME_MT_editor_menus`, `TIME_MT_marker` 없음 | Time Slider / Range Slider 헤더, Marker 메뉴 | 켜기 실패 (step 53 에서 고침) / Marker 메뉴 빈칸 | `timeline_header_classes`, `timeline_marker_menu` (`DOPESHEET_MT_marker`) |
| 테마 구조 재편 (300 개 넘게 이동·삭제, 공식 표 theme_migration_api) | `theme/studio_grey.xml` (4.5 형식) | 동작: 5.x 에서 Maya 패널색·핸들색·이음매/날카로움 색 등이 Blender 값 | `theme.MOVED` = 공식 표 55 항목 전부 (이전: 26). 후속 없이 삭제된 설정 (face_dot 등) 은 Blender 값 |
| `rna_xml` → `_rna_xml` (비공개) | 테마 적용·복원, 스위치 스냅숏 | 깨짐 (step 53) | `rna_xml()` |
| `np.array(Matrix)` 가 float32 | 선택 우선순위 화면 거리 | 정밀도 | `dtype=np.float64` (분기 불필요) |
| `Material.use_nodes` 폐기 예정 (항상 노드, 쓰면 경고) | 재질 만들기, Hypershade, AE | 경고 | `ensure_material_nodes` / `material_uses_nodes` |
| IC 키맵: Ctrl+G 가 메뉴 호출 | 키맵 패치 | (step 53 에서 이벤트로 제거) | `keymap/patch.STRICT` = `compat.IS_TARGET` |
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
| GN 모디파이어 입력 API, 조각 자동 마스킹, `template_palette(color=)` | — | 없음 | — |

## 버전별 결과

마지막 코드 기준 (2026-10-20). 헤드리스 = `tests/run.py` 전체 (104 파일), GUI = `tests/gui/run.py` 전체 (89 파일, 기본 UI 배율 =
이 PC 125 %), 설치 왕복 = `tools/release_check.py` (extension validate, 깨끗한 설정에 설치 → 켜기, 사용자 셋업 유지, 끄기 = 전부 복원,
Remove, 남는 킷 파일 0, opt-in · 레이아웃 스크린샷).

| Blender | 헤드리스 | GUI | 설치 왕복 | 시각 (look_compare) | 이 단계 전 (step 117) |
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
- 시각: `research/maya/screens/compare_<ver>/` (나란히 그림·표), `tmp/look_env_<ver>/shots/` 를 직접 봄 — 레이아웃 (메뉴 막대, Status
  Line, 셸프, Tool Box, Outliner, 탭 스택), Maya 테마 색, 핫박스, Move / Rotate 매니퓰레이터, RMB 마킹 메뉴 + 목록, Channel Box 가
  4.5 와 같다. 차이: 5.x 타임라인은 한 줄 (재생 버튼이 Range Slider 줄 오른쪽 끝, 위 「5.x Time Slider」), Time Slider 눈금 간격이
  Blender 5.x 의 것 (5, 10 … 대신 6, 12 …). 「밀도」 5 / 6 → 4 / 6 은 Create 메뉴 줄 간격 측정이 5.x 메뉴 그림자 가장자리를 다른 열로
  잡은 것 (스크린샷에서 메뉴 위치·모양 같음) — 측정 도구 쪽.

## 남은 것

- 5.3 이후: `blender_version_max = "5.3.0"` 이라 설치 안 됨. 새 마이너가 나오면 같은 순서 (zip → `ALLSET_SANDBOX=<v> tests/run.py
  --blender`, GUI, release_check, `ALLSET_LOOK_TAG` look_compare) 로 재고 compat 에 분기를 더한 뒤 올림.
- 5.x 테마: 후속 없이 삭제된 값 (`face_dot`, `execution_buts`, `lastsel_point`, 노드 편집기 일부 등) 은 Blender 기본, 5.x 에만 있는 새 값도
  Blender 기본. 로드 때 5.x 가 「not found」 경고를 찍음 (rna_xml 출력, 기능 영향 없음).
- 5.x Time Slider 는 사이드바가 없어 재생 버튼 위치만 Maya 와 다름 (한 줄). Blender 가 Timeline 사이드바를 다시 열게 되면 4.5 배치로.
- `_rna_xml` 은 5.x 에서 비공개 모듈 — 이후 버전에서 사라지면 테마 적용·복원을 킷 자체 XML 쓰기로 바꿔야 함.
- 5.1.2: 수동 스윕 한 세션이 검사 79 에서 멈춤 (Win32 1407, 위) — 사용자 조작에서 같은 일이 나는지 / Blender 5.1 의 GHOST 문제인지 미확정.
- 사용자 기기에서의 실제 화면 확인: `docs/manual_checks.md` 「Step 118」.
