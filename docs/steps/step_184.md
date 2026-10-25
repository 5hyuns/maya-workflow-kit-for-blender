# Step 184 — RMB list under the ring (backlog.json #2, audit 13 #2)

## 계획

문제 (재점검 13차 점수 15): RMB 마킹 메뉴 목록이 창 아래쪽에서 링 왼쪽 옆으로 가서 Time Slider 를 덮는다 (step 161 의 delegated 결정).
backlog 지시는 「링 아래, 창 끝에서 잘리고 남은 줄은 끌거나 스크롤해서 닿게」였지만, 먼저 Maya 에서 쟀다.

측정 (레인: 포그라운드 에이전트 1, GUI Maya 2022 + 실제 입력; `research/maya/re/rmb_list_184.md`, 스크립트
`research/scripts/maya_rmb184/`, 화면 `research/maya/screens/rmb184/`):
- 목록은 **언제나 링 아래** (S 상자 아래 21 px, 링 중심 x 에 가운데), 잘리지도 옆으로 가지도 않는다.
- 목록이 **화면** 아래를 넘으면 **메뉴 전체 (링 + 목록) 를 그만큼 위로** 그려 목록 끝이 화면 아래 10 px 에 닿게 한다. 포인터는 그대로
  (링 중심이 포인터 위에 없음). 경계는 화면뿐 (마킹 메뉴는 화면 전체 크기 Qt 창) — 뷰 · Time Slider · Maya 창은 무시.
- 위로 그린 메뉴: 하이라이트는 그려진 줄 기준; 링 아래 (S 상자를 안 지나고) 목록 밑에서 놓으면 아무것도 안 함; 휠 스크롤 없음.

결정 (delegated):
- kit 의 경계 = Blender 창 (`draw.window_bounds`; Blender 는 창 밖에 못 그림) → Maya 의 「화면」 규칙을 창에 적용: 목록이 창 아래
  `list_gap` 을 넘으면 메뉴 전체를 위로 (`engine.lift_up`, `fit_ring` 이 올린 만큼 돌려줌, `Session` 은 그린 중심으로 그리고 맞춤,
  포인터 · 거리 판정은 누른 점 `press`). 영역 경계 띠 (step 136) 때문에 줄이 밀려 다시 넘치면 그만큼 더 올림.
- 올린 메뉴에서는 링 아래에서 방향으로 radial 을 고르지 않음 (`Layout.lifted`) — Maya B6 / B7.
- 빠른 클릭 (움직임 없이 놓기) 은 올린 메뉴에서 누른 점 아래 줄이 있어도 클릭 모드 (Maya 는 hold 후 놓기에서 줄을 실행 — 빠른 클릭은
  안 잼 [U]; 우연히 줄이 실행되지 않게).
- 링을 올려도 위가 모자라면 (목록이 창보다 김) step 52 / 161 의 옛 배치 (여러 줄 · 옆 · 위) 그대로.

순서: 측정 결과가 설계를 바꿔서 (잘라내기 → 들어올리기) 측정 → 구현 순차.

## 한 일

- `src/allset/marking/engine.py`: `lift_up`, `fit_ring` = 들어올림 + `_place` (옛 배치 규칙), `Layout.lifted` (hit), `Session.press`,
  빠른 클릭 규칙, 제자리 radial 서브메뉴도 들어올림 반영.
- 테스트: `test_step52_hotbox_rmb.test_rmb_list_under_the_ring` (새 규칙), `test_lifted_menu_picks_like_maya` (새), step33 / 136 /
  151 테스트의 「중심 = 누른 점」 가정을 「같은 x, 같거나 위」로, GUI `gui_step161_messages` G2, `gui_step151_ring` (올린 메뉴는 N 상자
  거리 검사 제외).

## 검증

- 헤드리스 마킹 관련 (`-k step33,step52,step151,step8_,step129_marking,step136,step161,step153`): **76 / 76**.
- GUI `-k step52,step136,step161,step151,step33`: 처음 65 / 69 (옛 가정 4) → 고친 뒤 실패 파일 `-k step151_ring,step161_messages,step33`
  **27 / 27**. 스크린샷 `1.25_object_rmb_bottom.png` 직접 봄: 아래쪽 RMB = 링이 위로, 목록이 링 아래 한 열로 창 아래까지.
- look_compare: checks 9 / 9, viewport 12 / 12, rects 5 / 12 (그대로); shot 14 나란히 봄 — Maya 는 1600 x 900 창 밖 (화면 안) 으로
  목록이 이어지고, kit 은 창이 경계라 메뉴 전체가 위로 (같은 규칙, 경계만 다름).
- 헤드리스 전체: **1690 / 1690** (206 파일).

## 남은 것

- Maya 의 경계는 화면 — Blender 창이 화면보다 작으면 kit 은 더 일찍 올린다 (Blender 는 창 밖에 그릴 수 없음).
- 올린 메뉴에서 빠른 마크 (보지 않고 긋기) 의 방향 기준: 그린 중심 [U] (Maya 측정 없음). 왼쪽 · 오른쪽 화면 끝은 Maya 측정 없음
  (kit 은 옆으로 밀기 그대로).
- 실제 마우스 느낌 → manual_checks 「Step 184」.
