# Step 135 lane WIDTH — the Maya dock width follows the UI scale (#60)

## 계획

증상 (#60, `step_133_ui.md` #5): Maya tab stack (Channel Box / Layer Editor · Attribute Editor · Modeling Toolkit, `ui/maya_dock.py`
의 STACK 영역) 이 UI 배율 1.0 · 1.25 모두 278 px 에 머문다. 아웃라이너는 `toolbox.fit_columns` 가 260 × 배율로 맞추는데 (step 99) 독은
맞추는 규칙이 없다 — 1.25 에서 탭 · 「Subdivisions Height」 · AE 메뉴 줄이 잘리거나 두 줄.

### 측정 (`tmp/probe135/gui_probe_width.py`: Maya 레이아웃 + 큐브, 독을 280 → 740 px 로 20 px 씩, 화면 캡처)

Maya 2022 (100 %): CB 탭이 위인 스택 = x 1320 – 1600 = **280 px** (260 패널 + 세로 탭 띠, `research/maya/screens/01_layout_empty.png`,
`make_startup.DOCK_PX` = 277), AE 탭을 올리면 스택이 **480 px** (x 1120 – 1600, `10_attribute_editor.png`; 기본 AE 폭 460,
`research/maya/ui_layout.md` createGlobalOptVars:218-221). Maya 탭은 세로 띠라 폭과 상관없이 보인다.

킷 독 (1.25, `tmp/width135/probe/sheet_125_*.png`):

| 무엇 | 안 잘리는 최소 독 폭 |
|---|---|
| CB 라벨 「Subdivisions Height」 (라벨 열 = 레이아웃의 0.5) | 300 (280 은 「Subdivisions Hei…」) |
| AE 메뉴 줄 한 줄 (`attribute_editor.fits`: (Σ 글자 × 7 + 14) × s + 20 s) | 540 (= 412 × 1.25 = 515 이상) |
| 탭 줄 (지금: 펼친 align 줄 = 탭 셋이 **같은 폭**, 그립 약 80 px) | 680 |

blf 폭 (UI 글꼴 11 pt × s): 「Channel Box / Layer Editor」 140 / 174 / 205, 「Attribute Editor」 82 / 97 / 115,
「Modeling Toolkit」 90 / 108 / 131, 「Subdivisions Height」 107 / 126 / 156 (1.0 / 1.25 / 1.5).

탭이 같은 폭이라 탭 줄은 어떤 합리적인 폭에서도 맞지 않는다 — 탭 그리기는 레인 CB (`maya_dock.draw_handle`) 가 고친다 (cb135 와 합의:
탭마다 글자 폭에 맞춘 `ui_units_x`, 왼쪽 정렬). 이 레인은 그 자연 폭을 기준으로 독 폭을 정한다.

### 규칙 (delegated)

`toolbox.dock_width(scale)` = min(**480 × s** (Maya 의 가장 넓은 스택 = AE 를 올린 폭), max(**277 × s** (Maya CB 스택), need(s))),
need(s) = 다음 중 큰 것 (U = Blender 위젯 단위 floor(18 s + 0.5) + 2 × pixel_size, 글자 폭 = blf):

- 탭 줄: 그립 (`":" × 8` 글자 + 1.5 U) + Σ 탭 (글자 + U) + 2 U (패널 여백);
- CB 라벨: 2 × (가장 긴 Maya 기본 채널 라벨 + 0.8 U) + 0.8 U (라벨 열이 절반);
- AE 메뉴 줄: `attribute_editor.fits` 와 같은 식 (412 × s) — 그 함수가 한 줄을 고르는 폭.

추정: 1.0 ≈ 466, 1.25 ≈ 574, 1.5 ≈ 672 px (Maya CB 스택 277 / 346 / 416, AE 스택 480 / 600 / 720). Maya 의 CB 스택보다 넓지만 Maya 가
AE 를 올렸을 때보다 좁다: Blender 의 탭이 가로라서 (Maya 는 세로 띠) 탭과 AE 메뉴 줄이 한 줄에 들어갈 폭이 필요하다. 탭마다 폭을 바꾸는
것은 (Maya 처럼) 못 한다 — `area_move` 는 마우스가 영역 위에 있으면 poll 이 실패해 탭 클릭 순간에 옮길 수 없다.

맞추는 방법 = step 99 / 132 #53 규칙 그대로: `fit_columns` 가 armed 인 화면 (로드 직후 · 처음 봄 · 배율 변경, 영역 집합이 그대로) 에서만
STACK 영역 (`maya_dock.find_stack`) 의 왼쪽 모서리를 옮긴다. poll 이 실패하면 틈 점 (모서리 왼쪽 1 px) 을 pending 에 넣어
`ALLSET_OT_fit_columns` 가 커서를 옮겨 맞춘다 (이벤트 시뮬레이션에서는 `ALLSET_FIT_WARP=1`). 메인 뷰는 최소 320 × s 를 남긴다 (작은 창).
떼어낸 독 · 사용자가 연 독 (영역 집합이 바뀜) 은 맞추지 않는다.

startup.blend: 1.0 에서도 277 은 새 규칙과 다르다 → `tools/make_startup.py` `DOCK_PX` = `dock_width(1.0)` 로 다시 만든다 (로드 맞춤이
실패해도 1.0 은 맞게).

버린 대안: (1) 독 폭 = 277 × s 만 — 1.25 에서 탭 · AE 메뉴 줄이 그대로 잘림 (#60 의 확인 항목). (2) 탭에 따라 폭 바꾸기 — 위 poll 이유.
(3) AE 메뉴 줄을 blf 로 다시 재기 — `attribute_editor.fits` 는 이 레인 파일이 아니고, 같은 식을 쓰면 두 쪽이 어긋나지 않는다.

검증: 헤드리스 `tests/test_step135_width.py` (규칙: 배율별 폭, Maya 하한 · 상한, blf 로 잰 탭 · 라벨 · AE 메뉴 줄이 폭 안,
`attribute_editor.fits` 가 그 폭에서 한 줄); GUI `tests/gui/gui_step135_width.py` (`ALLSET_FIT_WARP=1`: 로드 후 독 폭 = 규칙, 뷰포트 =
남은 폭, AE 메뉴 줄 한 줄, 스크린숏). 1.0 / 1.25 / 1.5 첫 화면을 Maya 와 나란히 `tmp/width135/`.

## 한 것

- `src/allset/ui/toolbox.py`: `dock_need` / `dock_width` (blf `text_px`, U = `toolbar_fit.unit`), `_fit_dock` — `fit_columns` 가
  armed 인 화면에서 STACK 영역 왼쪽 모서리를 옮긴다 (poll 실패 → 틈 점 pending → `ALLSET_OT_fit_columns` 커서 맞춤). 뷰포트 하한은
  툴 박스 열 · 아웃라이너가 맞춰진 뒤의 폭으로 계산 (`MIN_VIEW_PX` 280 × s; 처음 320 이었는데 1.5 에서 독보다 나중에 아웃라이너가 커져
  뷰포트가 439 px 로 하한 아래가 됐다 → 계산을 고치고 하한을 Maya 150 % AE 화면 (약 430 px) 에 맞춤, delegated).
- 측정하며 하나 더 고침: 영역 사이 틈은 1.0 에서 3 px, 1.5 에서 5 px (모서리 굵기가 배율을 따름) — 아웃라이너 · 독을 "옆 영역" 으로
  찾는 허용치 4 px 때문에 1.5 에서는 아웃라이너 (step 99) 도 독도 맞추지 않았다 → `GAP_PX` = 8.
- `tools/make_startup.py` `DOCK_PX` = 466 (= `dock_width(1.0)`), startup.blend 다시 만듦 (독 468, 1.0 뷰포트 773 px).
- 레인 CB (cb135) 와 합의: 탭 줄 = 왼쪽 정렬, 그립 `ui_units_x` = blf / U + 1.5, 탭마다 blf / U + 1. 그립을 고정하지 않으면 그립
  sub-row 가 늘어나 탭이 다시 잘린다 (미리보기 패치로 측정, `tmp/probe135/gui_probe_merged.py`).

## 검증

- 폭 (blf, 1600 × 900 창): 1.0 **466** (Maya CB 스택 277, AE 480) · 1.25 **574** (346 / 600) · 1.5 **672** (416 / 720);
  need = 탭 466 / 574 / 672, 라벨 262 / 312 / 382, AE 메뉴 412 / 515 / 618. 맞춘 뒤 뷰포트 807 / 622 / 439 px.
- `ALLSET_SANDBOX=width135 python tests/run.py -k step135,step99,step132,enable_disable`: **15 / 0** (4 파일); 추가로
  `-k step49,step31,step116,step112,step130` **36 / 0** (8 파일).
- `ALLSET_SANDBOX=width135 python tests/gui/run.py -k step135_width,step99,step106_tool,step5_layout,step116,step132`: 1.25 **60 / 0**,
  `--ui-scale 0.8` **60 / 0**, `--ui-scale 1.2` **60 / 0** (6 파일).
- 나란히 (Maya 100 % | 킷 1.0 / 1.25 / 1.5, 레인 CB 탭 미리보기 패치 포함): `tmp/width135/side_first_screen.png`,
  `side_channel_box.png`, `side_attribute_editor.png` — 세 배율 모두 탭 · 라벨 · AE 메뉴 줄 안 잘림, AE 화면 폭이 Maya 의 AE 스택과 비슷.
  이 레인만으로는 (탭이 같은 폭) 1.25 에서 「Channel Box / Layer …」 가 여전히 잘린다 (`tmp/width135/shots/s135_channel_box_125.png`).

## 남은 것

- 탭이 잘리지 않는 것은 레인 CB 의 탭 줄 변경과 병합된 뒤에야 성립 — 메인이 병합 후 1.0 / 1.25 / 1.5 그림으로 확인.
- CB 탭이 위일 때 독은 Maya (277 × s) 보다 넓다: 가로 탭 줄 때문. Maya 처럼 세로 탭 띠로 그리면 277 × s 로 돌아갈 수 있다 (후속 후보).
