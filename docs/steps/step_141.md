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
