# Step 142 — UI 모습 · 맞춤 (#78 #77 #76 #54 #41)

## 계획

| 순서 | 레인 | 이슈 | 파일 |
|---|---|---|---|
| 1 | UI (worktree, 포그라운드) | #78 dock 폭 (Maya 처럼 Channel Box 탭일 때 좁게), #77 UI 1.5 배율 1600 px 창의 메뉴 막대 넘침 · Set Driven Key 버튼, #76 매니퓰레이터 축 색 · 선택 안 된 와이어 색 | `ui/maya_dock.py`, `ui/toolbox.py`, `ui/status_line.py`, `ui/set_driven_key.py`, `ui/manipulator.py`, `ui/selection_wire.py`, 관련 테스트 |
| 1 | ICONS (worktree, 포그라운드) | #54 남은 메뉴 아이콘 (Deform, Mesh Display, Effects / Fields, Edit Mesh / Mesh Tools) | `ui/menu_icons.py`, `ui/menu_icon_data.py`, `tools/gen_menu_icons.py`, 아이콘 그림 모듈, `tests/test_step131_icons.py` 계열 |
| 2 | MEDIA (포그라운드, 1 뒤) | #41 테마 없이 스토어 미디어 · 홍보 샷 · docs/screenshots 다시 찍기 (생성기에서 테마 적용 제거) | `tools/marketing/*`, `tools/release_shots.py`, `docs/distribution/media/`, `docs/distribution/marketing/`, `docs/screenshots/`, `site/media/` |

순서가 필요한 것: MEDIA 는 UI 레인의 새 모습 (dock 폭, 매니퓰레이터 색) 을 찍어야 해서 1 뒤. 부하 제한: 동시에 레인 2 개, Blender 2 개.
테스트 규칙: 기능 테스트 먼저 (사용자 지시 "Tests first") + 헤드리스 전체 + 바뀐 모듈 GUI 만. 새로 찾은 문제는 즉시 GitHub 이슈.

## 한 일 (상세: `step_142_ui.md`, `step_142_icons.md`, `step_142_media.md`)

- #78 dock: Maya 의 세로 탭 띠 (dock 오른쪽, `maya_dock.draw_strip`, 클릭 `allset.dock_strip_click`), 폭 = 올린 탭에 따라
  (Channel Box 286 / 346 / 418 px at 1.0 / 1.25 / 1.5 — Maya 277 / 346 / 416; AE 480 × scale), 템플릿 `DOCK_PX` 286 →
  1600 px 창에서 뷰포트 773 → 954 px. 가로 탭 + 좁은 폭은 340 px 미만에 안 들어가 세로 띠를 골랐다 (delegated).
- #77: 메인 메뉴 막대가 안 들어가면 Maya 처럼 » (`status_line.draw_menu_bar_fit`, `ALLSET_MT_menu_more`; 1.5 배율 1600 px 에서
  13 + »), Set Driven Key 목록이 남은 높이에 맞춰 줄 수를 줄임 (1.5 배율에서 Key / Load 버튼 닿음).
- #76: Move / Scale 매니퓰레이터 = Maya X #e60000 / Y #00e600 / Z #0000ff (테마 안 읽고 안 씀; Rotate 는 Blender C gizmo 라
  테마 색 그대로 — 한계), 와이어프레임의 선택 안 된 물체 = Maya #000460 (`selection_wire.py`). look_compare viewport 7/12 → 11/12.
- #54: 메뉴 아이콘 190 → 675 개 (Maya 가 아이콘을 보이는 679 항목 중; 남은 4 개는 Maya 캡처에 그림 없음 — USD / XGen 플러그인),
  킷이 그린 450 그림 (`ui/menu_drawings*.py`, `@icon` → `gen_menu_icons` 규칙 4). Outliner 타입 아이콘은 행 → 물체 대응을
  Python 이 못 얻어 하지 않음 (delegated).
- #41: 생성기에서 테마 적용 제거 (`tools/marketing/scene.py`, `bg_check.py` = 평평한 Maya #5c5c5c, 테마 쓰기 검사
  `tests/test_step142_media.py`), Blender 기본 테마로 다시 찍음 — 스토어 미디어 11, 홍보 화면 10 + 키 비주얼 2,
  docs/screenshots 7, 클립 7 + GIF 7 + 트레일러, 키트 이미지 6, 사이트 미디어 (check_site PASS). 테마 결정 (delegated): 킷은
  테마를 싣지 않으므로 Blender 기본 테마, Maya 색은 킷이 그리는 것만 — listing / marketing 문서에 적음.

## 검증

- 헤드리스 전체 (UI + ICONS 병합 뒤): **1234 / 1234** (150 파일). MEDIA 는 src 를 안 바꿈 (`-k step142_media,step130_package_scan` 9/9).
- GUI (바뀐 모듈만): 병합 뒤 step142 / 113 / 62 / 99 **59 / 59**, find_button 바뀐 뒤 step129_channel_box / step142_ui /
  step129_prims **32 / 32**; 레인 안: 1.25 배율 142 / 1.5 배율 (--ui-scale 1.2) step142 / 113 / 62 **35 / 35**
  (전에는 step113 1, step62 9 실패) / 1.0 배율 step142 12 / 12; 아이콘 GUI 26 / 26.
- 스크린샷 직접 확인: 레인 문서의 목록 + 메인이 `docs/distribution/marketing/screens/03_channel_box_ae.png` 확인 (세로 탭 띠,
  Maya 폭, 빨간 키 채널).
- GUI 전체 묶음은 돌리지 않음 (사용자 결정: 출시 준비 143 에서).

## 남은 것 / 새 이슈

- #83 UI 1.5 배율 Channel Box 아래 빈 두 줄 (`channel_box.cb_share` 추정), #85 좁은 dock 에서 라벨 · 값 잘림 ("Chann...",
  AE Translate "62 c"), #86 Create Joints 뒤 redo 패널이 셸프 클릭을 먹음, #87 Channel Box 채널 이름 RMB 에 Maya Channels 항목
  없음 — 모두 0.3.0.
- Rotate 매니퓰레이터 색 (C gizmo), look_compare face tint 측정, 메뉴 아이콘 4 개 (그림 없음), 편집기 메뉴 막대 아이콘 캡처 없음.
- 탭 바꿀 때 dock 폭 맞춤은 커서를 잠깐 옮긴다 (step 99 방식) — manual_checks 「Step 142 — UI」.
