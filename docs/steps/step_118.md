# Step 118 — Blender 5.x 호환 (사용자 요청 2026-10-19, 최우선)

step 53 은 5.x 점검과 최소 대응만 했고, step 117 은 5.0.1 / 5.1.2 / 5.2.2 에서 19–23 실패를 재어 지원을 4.5.x 로 줄였다. 이번
단계는 실제 호환: 5.x 모든 마이너 최신판에서 헤드리스·GUI·설치 왕복을 통과시키고 지원 범위를 실측대로 넓힌다. 4.5 동작은 그대로,
버전 분기는 한 곳 (`src/allset/compat.py`).

## 계획

1. 공식 `download.blender.org/release/` 에서 5.x 마이너마다 최신 Windows x64 zip (5.0.1, 5.1.2, 5.2.2 — 5.3 은 아직 없음) 을 저장소 밖
   `C:/Users/ohnsk/AppData/Local/allset_blenders/` 에 받아 풀기 (sha256 확인, 설치기·사용자 설정 없음).
2. 릴리스 노트 Python API (5.0 의 테마·애니메이션·UI 대변경 포함) 를 읽고 킷 영향 목록 (`docs/compat_5x.md`) — 일반 서브에이전트가
   노트를 읽고 4.5 / 5.0 / 5.1 / 5.2 의 RNA·연산자·키맵 이름·bmesh.ops 를 헤드리스로 덤프해 소스와 교차 (`tmp/r118/`, 저장소 밖).
3. 네 버전을 병렬로 재기 위해 테스트 샌드박스를 고를 수 있게 (`ALLSET_SANDBOX`, `-k a,b,c`), 실패를 원인별로 고치고, 고친 것마다
   네 버전에서 해당 파일 재실행. 헤드리스 전체는 필요할 때, GUI 전체는 버전마다 끝에 한 번.
4. 버전 분기 = `compat.py` 의 도우미. 각 도우미는 4.5 경로를 먼저 (기능 검사 위주: `hasattr`, RNA 속성 유무; 버전 번호 비교는
   `compat.py` 안에서만). `test_step118_compat` 가 다른 모듈의 `bpy.app.version` 을 막는다.
5. 시각 확인: `tools/look_compare.py` 를 버전마다 (`ALLSET_LOOK_TAG`), 스크린샷 직접 보기.
6. 매니페스트 `blender_version_max` = 통과한 범위 바로 다음, 배포 문서 지원 표기.

## 한 것

- **`src/allset/compat.py` (새)**: `rna_xml`, `has_op`, `strips`, F-curve (`fcurve_owners` / `action_fcurves` / `id_fcurves` /
  `id_fcurve_collection` — layered action 의 슬롯 channelbag), `LATER_PROPERTIES_TABS`, `timeline_header_classes` /
  `timeline_marker_menu`, UV 섬 모드 (`uv_island_mode` / `set_uv_island_mode`), UV 루프 선택 (`uv_vert_selected` /
  `uv_edge_selected`), `set_file_format` (`media_type`), `pointmerge_facedata` (5.2 `vert_target`), `bone_hidden` /
  `set_bone_hidden` (`PoseBone.hide`), `ensure_material_nodes` / `material_uses_nodes`, `read_region_row` (5.1 범위 밖 읽기 오류),
  `save_dialog_args` (5.2 Ctrl+S 옵션), `toolbar_back` (`regions.sidebars.back`). 예전 버전 분기 (theme / switch 의 `_rna_xml`,
  component 의 `_has_op`, time_slider 의 Timeline 클래스, keymap 의 `TARGET_VERSION`) 도 여기로 옮김.
- **Maya → Blender 전환 크래시 (5.1.2)**: 전환이 Maya 작업 공간을 지우는 순간 창은 아직 그 screen 을 그림 (작업 공간 변경은 다음 이벤트
  루프) → 5.1 의 영역 경계 강조 그리기에서 접근 위반. `switch.leave_layout` 이 창이 떠난 뒤 타이머에서 `bpy.data.batch_remove` 로 지움
  (모든 버전; `workspace.delete` 는 override 를 무시하고 창의 활성 작업 공간을 지워 쓸 수 없음 — 실측). GUI 테스트는 삭제를 기다림.
- 버전과 무관하게 고친 것: `preferences.set_quiet` (bpy.props dict 쓰기 대신 콜백 건너뛰기 — 5.0 은 `prefs["x"] = v` 불가),
  SDK 새 드라이버 곡선의 기본 키 삭제 + 외삽 CONSTANT (5.x 는 Generator 대신 키 (0,0)(1,1)), `np.array(Matrix, dtype=float64)`,
  Playblast 설정 저장·복원에 `media_type`, 조각 브러시를 3D View 문맥에서 활성화 + 모드 오류도 재시도 (5.2 셸프 Grab).
- **테마**: `theme.MOVED` = Blender 공식 5.0 이전 표 55 항목 전부 (패널색 → `user_interface.panel_*` — Maya 도크인 Properties
  것에서, 영역 배경 → `regions.*`, 애니 색 → `common.anim.*`, 곡선 핸들 → `common.curves.*` (크기 정수 포함), 3D View 표식 →
  `view_3d.seam/sharp/crease/bevel/freestyle`). 4.5 에는 이 경로가 하나도 없어 그대로 (실측).
- **키맵**: 5.1+ IC 의 새 「Grease Pencil Draw Mode」·Sequencer·Preferences 키를 가림 선언 (`KEY_STEP_SHADOWS`, `SEARCH_SHADOWS`),
  5.x IC 가 「Screen Editing」 (편집기보다 먼저) 에 넣은 Alt+F12 / Ctrl+Alt+F12 렌더 제거 — 킷 UV Editor 의 Maya Alt+F12 (UV Shell)
  를 가로챘음 (있을 때만 제거, 4.5 에는 없음).
- **템플릿 도크**: 4.5 로 저장한 Allset 템플릿을 5.x 가 열면 새 탭 플래그 (`show_properties_strip(_modifier)`) 가 켜져 도크 역할을
  못 알아봄 → 역할 판정에서 그 플래그 무시.
- **Time Slider (5.x)**: Timeline 모드의 사이드바는 5.x 에서 공장 파일에서도 열리지 않음 (UI 영역 1 px, GUI 실측) → Allset 레이아웃의
  타임라인 = 한 줄: Range Slider (끌 수 있는 막대 포함) 다음 오른쪽 끝에 재생 버튼 8 개. 4.5 (사이드바 열림) 는 그대로.
- 도구: `tests/run.py` / `tests/gui/run.py` `-k a,b,c`, `ALLSET_SANDBOX` (버전마다 따로 샌드박스, 병렬); `tools/look_compare.py`
  `ALLSET_LOOK_TAG` (버전별 `compare_<v>`, `tmp/look_env_<v>`) + 5.x 에서 옮긴 테마 경로 읽기.
- 테스트: 새 `test_step118_compat` (8: 버전 검사는 compat 에만, layered action F-curve, SDK 빈 곡선 / CONSTANT, UV 섬 모드 왕복,
  동영상 / 이미지 포맷, pointmerge + strips, 도크 역할과 새 탭 플래그, UV 동기화 끈 선택 읽기). `tests/kit.fcurves()`; 기존 테스트의
  `action.fcurves` / `uv_select_mode == 'ISLAND'` / `bone.hide` / Auto Key 공장값 가정 / GUI 스윕의 `copy_global_transform` (5.0 에서
  내장) → `node_wrangler`. `test_step53` 범위 = 4.5.0–5.3.0.
- 매니페스트 `blender_version_max = "5.3.0"` (4.5.x – 5.2.x), `docs/compat_5x.md`, listing.md (A 표·D Versions), DISTRIBUTION.md,
  extensions_audit.md, README, CLAUDE.md, manual_checks.

## 판단 (delegated)

- zip 은 step 53 에 같은 공식 파일을 받아 둔 것이 있어 (`tmp/blender5/dl`) 공식 서버의 sha256 을 새로 받아 대조한 뒤 지정 폴더로 복사·
  풀기. 2026-10-19 기준 5.x 마이너 = 5.0 / 5.1 / 5.2 (5.3 디렉터리 없음).
- 버전 분기 = 기능 검사 우선 (RNA 속성·연산자 유무). 버전 번호는 재질 `use_nodes` (5.0 부터 항상 노드, 속성은 남아 있어 기능 검사로 구분
  불가) 하나뿐이며 compat 안.
- 테마의 5.x 전용 값 (후속 없이 삭제된 `face_dot`, `execution_buts` 등) 은 Blender 값 — 별도 5.x 테마 파일은 만들지 않음 (결정 4,
  테마 생성기는 4.5 형식). 로드 때 5.x 가 찍는 「not found」 경고는 rna_xml 의 출력이라 그대로.
- 5.x Time Slider 의 재생 버튼 위치: Maya 는 Time Slider 줄 오른쪽 끝이지만 5.x 에는 그 줄 옆 칸 (사이드바) 이 없으므로 Range Slider
  줄 오른쪽 끝 (같은 화면 아래쪽 오른편, 한 줄).
- `blender_version_max` = "5.3.0": 측정한 마지막 마이너 다음 (exclusive). 5.3 이 나오면 같은 측정 뒤 올림.
- 버전 번호 (0.2.0) 는 그대로 — 지시에 없음, 배포 때 사용자가 올림 (남은 것).

## 검증

버전별 표 = `docs/compat_5x.md` 「버전별 결과」 (마지막 코드 기준).

- 처음 (수정 전, 876 테스트): 4.5 876, 5.0.1 856, 5.1.2 855, 5.2.2 852. 5.2.2 GUI 첫 전체 871 / 883.
- 헤드리스 전체 (`ALLSET_SANDBOX` 로 네 버전 병렬): **877 / 877** × 4 (4.5.4, 5.0.1, 5.1.2, 5.2.2). 마지막 키맵 수정 (Alt+F12) 뒤 관련
  7 파일 79 / 79 × 4, `gen_keymap_mapping` 0.
- GUI 전체 (`tests/gui/run.py`, 기본 배율): 4.5 **1121 / 1121**, 5.0.1 **1121 / 1121**, 5.2.2 **1121 / 1121**, 5.1.2 **1121 / 1121** (88 파일 790 + 수동 스윕을 두 세션 173 + 158 — 한 세션 스윕은 5.1.2 에서만 검사 79 에서 멈춤, `docs/compat_5x.md`). 전환 크래시 수정 뒤 `gui_step60` + 스윕 M60 11 / 11 + 11 / 11 × 4.
- release_check (`--shots tmp/r118/rel_shots_<v>`): **23 / 23** × 4 — validate Success, 사용자 애드온·파일·테마·인터페이스 유지, 선언된
  것만 바뀜, 끄기 / Remove 뒤 전부 복원, opt-in 전에는 키맵·모드 그대로, 깨끗한 설정에서 남는 킷 파일 0, 레이아웃 스크린샷.
- look_compare × 4: 테마 ΔE00 > 5 = 0 / 38, 장면 (pCube1 상자) 3 / 3, 뷰포트 요소 11 / 12, 격자 모서리 4 / 4 — 5.x 와 4.5 같음.
  스크린샷 직접 확인 (4.5 / 5.0.1 / 5.2.2: 첫 화면, Create 메뉴, 핫박스, Rotate 매니퓰레이터, RMB 마킹 메뉴, Channel Box): 같음, 5.x
  타임라인만 한 줄.
- ruff 0.8.6 (`src/allset`): 새 지적 0 (E741 15 건은 HEAD 에도 있음).

## 남은 것

- `docs/compat_5x.md` 「남은 것」: 5.3 이후 측정, 5.x 테마의 삭제된 값, 5.x 타임라인 한 줄 배치, `_rna_xml` 비공개 모듈 의존.
- 5.1.2 에서 수동 스윕 한 세션이 검사 79 에서 멈춤 (Blender 가 Win32 1407 반복; 나눠 돌리면 통과) — 원인 미확정.
- 확장 버전 번호 (0.2.0) 는 그대로 — 지원 범위가 바뀌었으니 업로드 전 0.2.1 / 0.3.0 으로 올리기 (사용자).
- 실제 사용자 5.x 설치에서 확인: `docs/manual_checks.md` 「Step 118」.
