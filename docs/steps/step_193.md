# Step 193 — RMB flick works when the menu is lifted (backlog.json #1, audit 14 G1)

## 계획

문제 (재점검 14차 점수 9, dogfood 47 / 48): 1600 × 900 창의 뷰 가운데에서 pCube1 위 RMB → 목록 (22 줄, 476 px) 이 링 아래에 안
들어가 step 184 규칙대로 **메뉴 전체 (링 + 목록) 가 ~340 px 위로** 그려진다 (`tmp/dogfood/shots/05_rmb_marking_menu.png`: 링이 Status
Line · 셸프 위). `Layout.lifted` 때문에 그린 링 아래에서는 방향 선택이 없어 RMB → 서쪽 110 px 끌기가 Vertex 를 안 고른다 — Maya
사용자가 가장 많이 쓰는 동작 (RMB → Vertex / Edge / Face / Object Mode) 이 화면 가운데에서 죽는다.

Maya 근거 (`research/maya/re/rmb_list_184.md` Rule 2–3): Maya 는 목록이 **화면** (모니터 전체, 1440 px) 아래를 넘을 때만 메뉴 전체를
올린다 — 마킹 메뉴는 화면 크기 Qt 창이라 Maya 창 · Time Slider 를 무시하고 그 밖으로 그린다. 그래서 보통 위치 (B1 같은 화면 아래
끝 말고는) 에서 링은 누른 점에 있고 flick 이 항상 된다. Blender 는 창 밖에 그릴 수 없고 (`draw.window_bounds`), 창은 보통 화면보다
작다 (1600 × 900 창에서 목록이 들어가는 누른 점은 창 위쪽 1/3 뿐) — step 184 는 Maya 의 「화면」 규칙을 창에 적용해서 Maya 보다
훨씬 자주 (뷰 가운데에서도) 올렸다.

결정 (delegated):
- **링은 언제나 누른 점** (radial 방향 = 누른 점 기준, 보지 않고 긋는 마크도 같음): Maya 사용자가 몸으로 외운 것은 방향이고, Maya 에서
  링이 누른 점을 떠나는 경우는 화면 끝뿐이다. 메뉴 전체 들어올리기 (`lift_up`, `Layout.lifted`, step 191 의 「그려지기 전 마크는 누른
  점 기준」 예외, 빠른 클릭 예외) 를 지운다.
- 목록은 링 아래에 들어가면 링 아래 (Maya, 한 열, 링 x 가운데). 안 들어가면 **목록만** 옮긴다: 링 옆 한 열 (가는 길에 radial 하위
  메뉴가 없는 쪽 — RMB 메시는 E = UV 가 열리므로 왼쪽, step 161 규칙), 그다음 링 위, 그다음 창 안으로 민 것 (`_place` 의 옛 규칙, step
  33 / 136 / 161) — 순서는 Maya 순서 그대로, 줄은 자르지 않음.
- 링 상자 자체가 창 밖이면 상자만 안으로 미는 step 33 규칙 그대로 (중심 = 누른 점 유지).
- 남는 차이 (문서화): Maya 는 화면 끝에서만 메뉴 전체를 올리고 목록은 언제나 링 아래 — kit 은 창이 작으면 목록이 링 옆으로 간다.

검증: 헤드리스 `test_step52_hotbox_rmb` (lift 테스트 → 「링 = 누른 점, 목록 아래 또는 옆 한 열, 서쪽 flick = Vertex」),
`-k step8_,step33,step52,step129_marking,step136,step151,step153,step161,step184`, 헤드리스 전체; GUI `-k step52,step151,step184`
+ lift 를 가정한 GUI 파일 (`gui_step129_marking_bounds`, `gui_step8_marking_menus`, `gui_step151_ring`, `gui_step91_view_chrome`);
`python tools/dogfood.py` → RMB > Vertex PASS (48 / 48); 스크린샷 UI 1.0 · 1.25 직접 봄.

레인: 엔진 한 파일 + 그 테스트라 나눌 독립 레인이 없음 (순차, delegated) — GUI 검증만 Blender 2 개까지.

## 한 일

- `src/allset/marking/engine.py`: `lift_up` / `Layout.lifted` 지움, `fit_ring` = `_place` 만 (중심 = 누른 점, 0 반환), `Session` 의
  step 191 「그려지기 전 마크는 누른 점 기준」 예외와 빠른 클릭의 lift 예외 지움 (링이 늘 누른 점이라 필요 없음). 목록 배치는
  `_place` (step 33 / 136 / 161): 링 아래 → 링 옆 한 열 (RMB 메시 = W 쪽) → 링 위 → 창 안으로.
- 테스트: `test_step52_hotbox_rmb` — lift 테스트 3 개를 `test_rmb_list_under_or_beside_the_ring` (링 = 누른 점, 한 열, Maya 순서,
  링 안 덮음, 창 안, 450 px 에서 W 쪽 옆) + `test_rmb_marks_work_where_the_list_does_not_fit` (세 위치 × N / S / W / NW 빠른 마크 ·
  느린 끌기 = 그 항목) 으로; step33 / 136 / 151 의 「중심 = 누른 점 또는 위」 → 「중심 = 누른 점」. GUI `gui_step8` (`_drawn` = 누른 점
  기준), `gui_step9` (주석), `gui_step129_marking_bounds` (타임라인 위로 끌기 = Face, lift 분기 지움), `gui_step151_ring` (N 상자 검사
  늘), `gui_step161_messages` G2 (링 = 누른 점), `gui_step91_view_chrome` (HUD 오른쪽 300 px 누르기 = step 161 배치로 되돌림).
- `docs/manual_checks.md`: step 52 / 161 / 184 문구 고침, 「Step 193」 2 개. `CLAUDE.md` step 184 줄을 193 규칙으로.

## 검증

- 헤드리스 마킹 묶음 (`-k step8_,step33,step52,step129_marking,step136,step151,step153,step161,step184`): 75 / 76 → 새 테스트의 회색 SW 상자 기대 고친 뒤 step52 9 / 9.
- GUI `-k step8_marking,step9_hotbox,step33_menu,step52_hotbox,step91_view,step129_marking,step136_edges,step136_items,step151_ring,
  step161_messages`: **103 / 103** (10 파일). step 184 이름의 GUI 파일은 없음 (lift 는 step161 / 129 / 8 / 9 / 151 / 91 이 검사).
- `python tools/dogfood.py`: **48 / 48** (UI 1.25) · `ALLSET_GUI_UI_SCALE=0.8` (실효 1.0) **48 / 48**, 콘솔 0. `05_rmb_marking_menu.png`
  두 배율 직접 봄: 링이 누른 점, 목록은 링 W 쪽 한 열, 창 안.
- 헤드리스 전체 4.5: **1730 / 1730** (215 파일; 1731 → 1730 = lift 테스트 3 개를 2 개로 바꿈).

## 남은 것

- Maya 와 남는 차이: Maya 는 화면 끝에서만 메뉴 전체를 올리고 목록은 늘 링 아래 — kit 은 창 (보통 화면보다 작음) 안에 목록이 링 아래
  안 들어가면 링 옆에 둔다 (step 161 배치). Blender 는 창 밖에 못 그림.
- UI 1.25 에서 옆 목록이 타임라인 경계 띠를 건너뛰며 마지막 줄 앞에 틈 (step 136 경계 띠 규칙, Blender 가 경계를 마지막에 칠함;
  `tmp/dogfood/shots` 1.25 샷) — 감사 14 레인 B #6 의 나머지.
- 실제 마우스 느낌 → manual_checks 「Step 193」.
