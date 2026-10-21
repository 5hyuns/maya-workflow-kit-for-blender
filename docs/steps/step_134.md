# Step 134 — Maya viewport look without a theme (#58 #59 #61 #75)

## 계획

backlog 1 (PLAN 「재점검 8차」 우선순위 1; `step_133_ui.md` #1 #3 #9 #15). Step 130 (#40, 결정 13) 이후 킷은 테마를 내보내지 않으므로
Maya 모습은 킷이 직접 그리는 것 (킷 고정 색 — 결정 13 이 허용) 과 레이아웃 파일의 뷰 단위 설정 (scene / screen 데이터 — 환경설정이 아님)
으로만 낸다. 환경설정 · 테마 쓰기는 여전히 금지 (`tests/test_step130_package_scan.py`).

### 레인 (병렬, worktree)

| 레인 | 이슈 | 파일 |
|---|---|---|
| SEL | (step_133_ui #1, 점수 20) 선택 색 = Maya 리드 초록 #43ffa3 / 나머지 흰색, 컴포넌트 (점 · 선 · 면) Maya 색 | `ui/selection_wire.py` (+ 새 모듈) |
| GRID | #59 그리드 대비 · 진한 축선, Maya 레이아웃 뷰의 3D 커서 숨김 | `ui/maya_grid.py`, 레이아웃 진입 (`switch` / `first_start`) 의 뷰 설정 |
| HUD | #58 F8–F11 · 1/2/3 뒤 Adjust Last Operation 패널 없음, #61 Smooth Preview (3) 부드러운 음영 | `operators/display.py` |
| LOOK | #75 `tools/look_compare.py` 를 step 116 dock + step 130 무테마 레이아웃에 맞게 고침 | `tools/look_*.py` |

메인: 병합, Maya 쌍 (`research/maya/screens/audit7/pairs/`) 과 1.0 / 1.25 나란히 그림, look_compare 수치, GUI 전체 한 번, 커밋.
순서가 필요한 것: look_compare 숫자는 다른 레인이 병합된 뒤에 잰다 (도구 수정은 병렬).

## 한 것

레인 4 개를 worktree 로 병렬 진행 후 병합 (레인 문서: `step_134_sel.md`, `step_134_grid.md`, `step_134_hud.md`, `step_134_look.md`).

- **SEL** (점수 20 차이): `ui/selection_wire.py` 가 테마 대신 킷 고정 Maya 색 (리드 #43ffa3, 나머지 #ffffff). 새 `ui/component_colors.py` (POST_VIEW):
  컴포넌트 모드 모서리 #64dcff, 점 #c800c8 / 선택 #fdff88, 선택 모서리 · 면 점묘 #e3ac79 (`research/maya/colors.json`, Maya 07/08/09 그림),
  편집 메시를 평가된 오브젝트의 `to_mesh()` 로 읽고 의존 그래프 갱신마다 캐시; 10 만 점에서 그리기 +1 ms, 다시 만들기 30–40 ms (선택이 바뀔 때만).
  애드온 환경설정 "Component Colors" (켬). Outliner 선택 줄 색은 Python 으로 믿을 만하게 못 바꿔 건너뜀 (delegated, 이유는 레인 문서).
- **GRID** (#59): `ui/maya_grid.py` 선 색 = 킷 고정 #404040 (테마를 읽어 #555555 → 거의 안 보였음), Maya 레이아웃 뷰 `show_cursor` 끔
  (`tools/make_startup.py` → `startup.blend` 재생성), D / Insert 컴포넌트 피벗 편집 중에만 커서를 보임 (`hold.show_cursors`).
  그리드 대비 (회색 표준편차) Maya 9.15 / 이전 3.91 / 지금 9.63.
- **HUD** (#58 #61): 디스플레이 · 모드 연산자 (1/2/3, PgUp/PgDn, F7–F11, F8, Shift+Q, RMB 컴포넌트, Alt+A / Alt+P / Alt+R 등) 에서
  REGISTER 를 빼고 UNDO 만 남김 → Adjust Last Operation 패널이 안 뜸. Smooth Preview: Maya 프리미티브의 hard edge 가 `sharp_edge` 라
  면만 매끄럽게 하던 노드 그룹에 모서리 Set Shade Smooth 를 더함 (0.2.x 파일의 그룹은 3 을 누를 때 다시 만듦).
- **LOOK** (#75): `tools/look_compare.py` / `look_data.py` / `look_shots.py` 를 step 116 dock · step 130 무테마 레이아웃에 맞춤 (새 앵커,
  픽셀을 킷이 그린 것 / 테마로 나눔, 섹션마다 한 줄 요약). 면 점묘 색을 킷 색으로.

## 검증

- 헤드리스 전체 `python tests/run.py`: **1046 passed, 0 failed** (130 파일).
- GUI 전체 `python tests/gui/run.py --no-build` (1.25): **1345 passed, 0 failed** (114 파일).
- `tools/look_compare.py` (1.0 / 1.25, `research/maya/screens/compare_step134_s100|s125/`):

| 섹션 | step 133 (1.0) | 지금 1.0 | 지금 1.25 |
|---|---|---|---|
| checks | 4 FAIL (도구 낡음) | 9/9 | 9/9 |
| pixels (킷이 그린 것) | 16/25 다름, 13 없음 | 6/6 ΔE00 < 5, 앵커 없음 0 | 같음 |
| viewport | 1/12 | **7/12** | 7/12 |
| grid | FAIL (ΔE00 7.1, 모서리 0/4) | **lines ok (ΔE00 0.7), 4/4** | 같음 |
| rects | 5/12 | 5/12 | 3/12 |
| density | 4/6 | 5/6 | 5/6 |
| scene / furniture | 3/3 · 1/3 | 3/3 · 2/3 | 3/3 · 2/3 |

- 나란히 그림을 직접 봄: 그리드 (`tmp/grid134/side_maya_vs_kit100.png`), 선택 (`tmp/sel134/pair_object_100.png`, `pair_verts_125.png`),
  Smooth Preview 3 (hud 레인 after 그림).
- 레인별: SEL 헤드리스 32 + GUI 20/20 (1.25 · 1.0), GRID 34 + 41/41 (두 배율), HUD 142 + 51, LOOK 도구 테스트 9.

## 남은 것

- #76: Move 조작기 축 색 (Blender 테마 색), 선택 안 된 와이어 색 (Maya #000460), look_compare 면 점묘 측정 방법.
- Blender 가 아직 그리는 것: 편집 모드 자기 점 · 선 · 면 색의 가장자리, 오브젝트 원점 점, Maya 레이아웃 밖 뷰의 주황 외곽선, Outliner 선택 줄
  (Python 불가). 킷 모서리 선이 Maya (1 px) 보다 굵음 (2 px — Blender 선을 덮으려고, delegated).
- 키 4–7 은 다른 연산의 열린 패널을 닫지 못함 (Python 으로 그 패널만 닫을 수 없음).
