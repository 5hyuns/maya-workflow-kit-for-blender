# Step 141 — 키맵 · 선택 작은 묶음 (#65 #72 #73, B4 B6, quant gap 3)

## 계획

0. QA (사용자 결정 10-24, 커밋 776dd37 "QA: ..."): GUI 실행기 파일당 시간제한 (`ALLSET_GUI_TIMEOUT`, TIMEOUT 보고 뒤 다음 파일),
   `GUI_SKIP` 격리 (gui_step75_input_line 클립보드 멈춤, gui_step63_mtk 묶음 안에서만 실패 → `docs/manual_checks.md`),
   PYTHONUNBUFFERED 로그, 실행당 고정 비용 측정 (샌드박스 3 s + 설치 16 s ≈ 19 s → 실패 파일은 한 번의 `-k a,b` 로).
1. 레인 KEYS (worktree, 포그라운드): Ctrl+A 모든 모드 = AE / Channel Box (#65, IC select-all 제거), UV / Image Editor Alt+RMB
   좌우 = Maya dolly (Blender Zoom Axis 설정 없이 킷 연산자, #51 처럼; B4), Undo 깊이 (B6: 스토어 규칙상 설정 못 씀 → README
   Recommended setup + 앱 안 안내), joint 이름 joint1 부터 다시 (#73), Gravity / Newton 기본값 (#72).
2. 레인 SELECT (worktree, 포그라운드): Select 메뉴 / Ctrl+RMB 변환 — Grow / Shrink Along Loop, To UVs / UV Shell / Vertex Face,
   Vertex / UV Perimeter, To Face Path, To Shell Border (quant gap 3) + GUI 테스트.
두 레인은 파일이 겹치지 않음 (KEYS = keymap / view / joints / fx / README / 안내, SELECT = 선택 연산자 / menu_map Select 줄 /
marking 변환 / notices Select 줄). 테스트 규칙 (사용자 10-23): 기능 테스트 깊게 + 헤드리스 전체 + 바뀐 모듈 GUI 만, GUI 전체 묶음 없음.

## 한 일 (상세: `step_141_keys.md`, `step_141_select.md`)

- QA (776dd37): 위 계획 0 그대로.
- #65 Ctrl+A = `allset.ae_toggle` 가 Mesh / Pose / Curve / Armature / Metaball / Lattice / Particle / Curves / Sculpt Curves /
  Point Cloud / Paint Face Mask / Paint Vertex Selection / UV Editor 에서 (IC select-all 제거, Ctrl+Shift+A = select all,
  Alt+D = 선택 해제). Graph Editor 등 2D 편집기 · 텍스트 편집기는 Ctrl+A select-all 유지 (delegated).
- B4: UV / Image Editor Alt+RMB = `allset.dolly_2d` (좌우 드래그, Blender Zoom Axis 설정과 무관; Esc 원래 배율).
- B6: README Recommended setup 의 Undo Steps 256 안내 확장, 킷 환경설정 패널에 Undo Steps < 256 일 때 안내 줄, 환영 창 Tip
  (설정은 쓰지 않음 — 스토어 규칙).
- #73: joint 이름은 오브젝트가 쓰는 armature 의 뼈만 센다 (지운 skeleton 의 armature 데이터가 purge 전까지 남아 joint1 을 막았음).
- #72: Gravity = 아래로 부는 Wind (세기 9.8, Flow 0), Newton = Force −5 (끌어당김), 둘 다 step 68 `fx.sim_scale` 적용
  (`research/maya/re/fields_141.md`: Maya 설치본 기본값 + mayapy 측정; 중력장 낙하 = nucleus 중력 낙하).
- quant gap 3: `operators/select_convert.py` (`allset.select_convert`) — Grow / Shrink Along Loop, To Vertex / Edge / Face
  Perimeter, To Face Path, To Shell Border, To UV Shell Border, To UVs, To UV Perimeter, To UV Edge Loop, Components > UV / UV
  Shell; To Vertices / Edges / Faces 는 `allset.convert_selection` (Maya 의 닿는 요소). 규칙 = mayapy 3 회 측정
  (`research/maya/re/select_convert_141.md`). Ctrl+RMB polyConvertMM 변환 항목은 모두 `("item", "Select/...")`, UV Editor
  Select 메뉴도 같은 9 개. Vertex Face 계열은 Blender 에 face-corner 선택이 없어 회색 + 알림 (delegated).

## 검증

- 헤드리스 전체 `python tests/run.py`: **1212 / 1212** (148 파일; step141_keys 15, step141_select 6 = 99 변환 사례가 mayapy 결과와 같음).
- GUI (바뀐 모듈 + 스모크, 한 번의 `-k`): step141_keys / step141_select / step136 / step8_marking / step18 — **54 / 54**
  (UV Alt+RMB 오른쪽 120 px → 배율 1.000 → 1.558, 왼쪽 → 0.642; Ctrl+RMB Grow Along Loop / To Vertex Perimeter / To Face Path).
- `python tools/menu_count.py`: Select 작동 39 → 50, 전체 664 → 675 (45.4 %), 알림 없는 회색 0, polyConvertMM 회색 4 → 0.
- `tools/gen_keymap_mapping.py`: 468 행, 구현 199.
- GUI 전체 묶음은 돌리지 않음 (사용자 결정 10-23: 출시 준비 단계에서만).

## 남은 것

- 2D 편집기 (Graph Editor / Dope Sheet / Outliner / Node) 의 Ctrl+A = AE 는 아직 select-all (Markers 키맵 순서 확인 필요).
- Node Editor Alt+RMB 는 IC 링크 끊기 그대로 (Hypershade dolly 없음). Graph Editor `view2d.zoom` 이 Zoom Axis 를 안 읽는지 미측정.
- 다른 필드 (Air / Radial / Uniform / Turbulence / Vortex) 는 Blender 세기 — Maya 값은 `fields_141.md`.
- Newton 감쇠: Blender (1+d)^-p 로 Maya 1/d 재현 불가.
- `marking/rmb_items.py` mm_poly 의 VERTEX_PERIMETER / SHELL_BORDER 옛 규칙 정리 (메뉴는 이제 안 씀).
- UV 선택의 Grow / Shrink Along Loop 은 정점 기준 근사. 5.x UV 선택 setter 미검증.
