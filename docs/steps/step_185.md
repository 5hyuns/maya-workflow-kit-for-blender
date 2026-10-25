# Step 185 — Selected edges and manipulator look (backlog_183.json #3, audit 13 #3 + #7)

## 계획

문제 (`docs/steps/step_182_quant.md` §5c-2 / §5c-3, 확대 `tmp/audit182b/crop09_kit.png` vs `crop09_maya.png`): 편집 모드 선택 엣지가
두꺼운 하늘색 와이어 안에 가는 주황 줄로만 보임 (Maya: 얇은 와이어 위에 또렷한 주황); Move / Scale manipulator 평면 핸들이 작고 흐리고
가운데 상자가 흰색 (Maya: 더 큰 진한 평면, 노란 가운데).

먼저 잰다 (추측으로 굵기만 바꾸지 않음):
1. GUI 프로브 (`tmp/probe185/gui_probe185.py`, `tests/gui/run.py --dir tmp/probe185`): 실루엣 엣지 단면 픽셀을 kit 끔 / 지금 / 변형별로.
2. Maya 02 / 06 픽셀 (`tmp/probe185/manip_px.py`, `plane_fit.py`): 평면 핸들 픽셀을 축 좌표로 풀어 위치 · 크기, 테두리 · 채움 색,
   가운데 색 (`research/maya/workflows/pivot_snap/shots/manip_move_active_*.png` 도).
3. look_compare 에 「선택 엣지가 하늘색 띠 안에 있나」와 평면 크기 · 색, 가운데 색 샘플 추가 — 옛 kit 샷으로 이 샘플이 실제로 실패하는지 확인.

레인: 엣지 (component_colors) / manipulator / look_data 는 파일이 나뉘지만, GUI Blender 2 개 한도와 프로브 → 구현 → 같은 look_compare
검증 순서 때문에 순차 (측정이 결정을 바꿈: 아래 1).

## 측정

- **엣지** (UI 1.25, Maya 큐브 = 모든 엣지 `sharp_edge`, step 134): Blender 자신의 sharp 엣지 (팩토리 테마 #00ffff) 가 약 3 px
  (`519a9a 00dfdf 008a8a`) 로 그려지고 kit 의 #64dcff 는 가운데 1 px 만 덮음 → 「두꺼운 하늘색」의 정체는 Blender sharp 색. 선택 엣지는
  kit 주황 2 px 양옆으로 Blender 청록이 남음 (`52c7c7 e2aa78 e2aa78 31bebe`). `overlay.show_edge_sharp` 를 끄면 Blender 는 2 px 짙은 회색
  (`474747 333333`); kit 선은 실루엣 한쪽에서 깊이 검사에 져서 (bias 0.0005) 1 px 만 남음. bias ≥ 0.002 + 1.5 px (× 1.25 = 1.9) 면 2 px
  모두 #64dbff, 1.0 px 은 짙은 1 px 이 옆에 남음.
- **평면 핸들** (Maya 02, 1.0 배율, 화살표 105 px): 빨강 YZ · 파랑 XY 둘 다 축 좌표 **0.52–0.68** (가운데 0.60, 반폭 0.08; kit 0.55 ±
  0.055). 1 px 진한 축색 테두리 + 반투명 채움 (#767676 윗면 위 빨강 #b6655f, 파랑 #5f63db). 넓이 (빨강, ΔE00 < 10): Maya 167 px, 옛 kit
  84 px (1.0 환산).
- **가운데**: 활성 핸들 = **#fdff88** (Maya 02 / 06 가운데, `manip_move_active_center.png` 81 px), 축이 활성이면 가운데 **#64dcff**
  (`manip_move_active_x.png` 81 px), 활성 축도 #fdff88. step 59 의 「밝은 회색」은 이 연노랑을 잘못 읽은 것.

## 한 일

- `src/allset/ui/component_colors.py`: `OVERLAY_OFF = ("show_faces", "show_edge_sharp")` — step 176 의 면 오버레이 스위치를 sharp 엣지에도
  (Maya 레이아웃 뷰, kit 이 그릴 때만, kit 이 끈 것만 되돌림, 해제 시 복원). `LINE_PX` 2.0 → **1.5**, 선택 엣지 `EDGE_SEL_PX` 2.0 을 따로,
  `DEPTH_BIAS` 0.0005 → **0.002**, 선택 엣지 `EDGE_SEL_BIAS` 0.003 (kind `LINES_SEL`, 마지막에 그림), 면 점묘는 `FACE_BIAS` 0.0005 그대로.
- `src/allset/ui/manipulator.py`: `PLANE_AT, PLANE_HALF = 0.60, 0.08`; 평면 = 채움 (축색을 흰색 쪽으로 `PLANE_LIGHTEN` 0.35, 알파
  `PLANE_FILL` 0.65) + 1 px 테두리 (`_draw_plane`, in_view 의 방식); 활성 핸들 `ACTIVE` #fdff88, 가운데 (Move 사각 / Scale 큐브) = 활성이면
  #fdff88, 아니면 `CENTER_IDLE` #64dcff; hover 는 Maya manipCurrent #ffff00 그대로.
- `tools/look_data.py` VIEW_SAMPLES 8 행: 선택 엣지 색, 엣지 모드 와이어 색, **flank** (선택 엣지 픽셀 중 2 px 안에 하늘색 계열이 있는 비율),
  Move 가운데 / Scale 가운데 #fdff88, 평면 채움 빨강 / 파랑, **area** (빨강 평면 넓이, 1.0 환산 비 0.6–1.6). `tools/look_compare.py`:
  `colour_mask` / `flank_share` / `colour_count`, 모드 flank / area. `tools/look_shots.py`: 06 / 09 점 기록 (`pCube1.sel_edges`).
- look_compare 마킹 메뉴 샘플 (step 184 이후 1.0 배율에서 `marking_menu_box` ✗): 기준점을 누른 점 → 그려진 링 중심 `mm_centre`
  (`look_shots.s_mm` 이 `marking.draw.ACTIVE` 세션 중심 기록), 목록 샘플은 Maya 와 같은 자리 (링 아래 141 px) — delegated.
- 테스트 `tests/test_step185_look.py` (상수, 평면 모양 0.52–0.68, 채움 색, 기본 활성 = 가운데). `docs/manual_checks.md` Step 185.

결정 (delegated): 와이어 1.5 px (backlog 는 1 px) — 1 px 은 Blender 의 2 px 편집 엣지 절반이 짙게 남아 (프로브) Maya 의 얇은 하늘색보다
멀어짐. 평면 채움은 Maya 측정 픽셀에 맞춘 근사 (Maya 는 보는 각도로 평면 투명도가 달라 보임 — 바닥 XZ 는 거의 불투명 #00e549); 축색 배치
(kit 위 = 파랑, Z-up) 는 구조적이라 그대로.

## 검증

- look_compare UI 1.25: checks 9/9, pixels kit-drawn **6/6**, viewport **20/20** (12 → 20 행). UI 1.0 (`ALLSET_GUI_UI_SCALE=0.8
  ALLSET_LOOK_TAG=s185_s100`): checks 9/9, kit-drawn **6/6** (re-anchor 전 5/6: `marking_menu_box` 8.3), viewport **20/20**.
- 새 샘플이 옛 모양을 잡는지: flank = Maya 0.05, 옛 kit (`tmp/look_env_audit182_s125` / `_s100`) **1.00**, 새 kit 0.05 / 0.04; 빨강 평면
  넓이 Maya 167 px, 옛 kit 84 / 82 px (×0.5, ✗), 새 kit 177 / 158 px (×1.06 / ×0.95). 색: 선택 엣지 ΔE 0.7, 가운데 0.3 / 0.1, 채움 빨강 3.6 /
  파랑 2.9.
- 화면: `tmp/probe185/final_cmp.png` (Maya | kit 1.0 | kit 1.25; 09 / 02 / 06) — 얇은 하늘색, 또렷한 주황 선택 엣지, 평면 테두리 + 채움,
  연노랑 가운데.
- 헤드리스 전체 **1693 / 1693** (1690 + 새 3). GUI `-k step134,step59` 59 / 59, `-k step142_ui,step85,step176,step151_extrude` 49 / 49.

## 남은 것

- Maya 는 평면 핸들 투명도가 보는 각도에 따라 다름 (02 바닥 초록은 거의 불투명) — kit 는 고정 알파. 각도 규칙은 REA / 측정 필요 [U].
- Rotate 는 Blender C gizmo 그대로 (step 59).
