# Step 120 — Maya 배경색 · Alt+B 배경 순환 (사용자 요청 2026-10-19)

사용자 말: 「Maya 에서 Ctrl+B 누르면 뒷배경 색이 바뀐다」. step 107 의 `allset.cycle_background` (Alt+B) 는 뷰 하나만, 그라데이션 단계를
건너뛰고 (회색 → 밝은 회색 → 검정) 돌았다. 이번 단계: Maya 2022 의 실제 키·순서·색을 재고, 같게 만들고, Maya 위치의 메뉴를 채우고, 기본
뷰포트 배경이 Maya 팩토리와 같은지 다시 확인한다.

## 계획

1. 키: `research/maya/hotkeys_default.json` (hotkeySetup.mel) 에서 B + 수식키 찾기.
2. 순서·색: `cycleBackgroundColor.mel` 규칙을 읽고, GUI Maya 2022 (팩토리 prefs) 에서 다섯 번 눌러 각 상태의 화면 픽셀을 잼
   (`research/scripts/maya_bg120/`, 결과 `research/maya/re/background_120.md`).
3. Blender 쪽: 단색 = 뷰의 `shading.background_type` VIEWPORT + 색, 그라데이션 = 테마 (`view_3d.space.gradients` LINEAR;
   Blender 에 뷰별 그라데이션은 없음). 4.5 / 5.2 에서 API 같음 (헤드리스 탐침).
4. 메뉴: Maya 의 위치 (Windows > Settings/Preferences > Color Settings) 를 채움.
5. 검증: 헤드리스 (규칙·모든 뷰·테마·키·메뉴·테마 파일 기본값), GUI (Maya 모드에서 Alt+B 를 실제 이벤트로, 화면 픽셀을 Maya 실측과
   ΔE00 비교) 4.5 + 5.2.2.

## 조사 결과 (Maya 2022 실측, `research/maya/re/background_120.md`)

- **Alt+B = CycleBackgroundColor** (hotkeySetup.mel:669). **Ctrl+B = BevelPolygon** (hotkeySetup.mel:385) — 사용자가 말한 Ctrl+B 는
  Maya 에서 Bevel. 킷은 이미 Mesh 의 Ctrl+B = `allset.bevel` (그대로 둠).
- 규칙: 그라데이션 켜짐 → 검정 + 그라데이션 끔; 배경 0 → 0.36; < 0.5 → 0.631; 그 밖 → 그라데이션 켬. **모든 뷰에 한 상태** (전역).
- 실측 픽셀: 팩토리 #5c5c5c → #a1a1a1 → 그라데이션 #889db3 (위) … #0d0d0d (아래) → #000000 → #5c5c5c. 팩토리는 그라데이션 꺼짐.
- Maya UI 위치: Windows > Settings/Preferences > Color Settings (+ Preferences > Display 의 Gradient background). 패널 메뉴에는 없음.

## 한 것

- `operators/key_batch3.py`: Maya 규칙 그대로 (`next_state`, 값으로도 판정 — 사용자 색 < 0.5 이면 밝은 회색으로), 상태는 마우스 아래
  뷰에서 읽고 **파일의 모든 3D View** 에 적용 (`view_spaces`, Tool Box 열 제외). GREY = 테마 (#5c5c5c), LIGHT / BLACK = VIEWPORT
  색, GRADIENT = 테마 그라데이션 LINEAR (`high_gradient` = 위 #889db3, `gradient` = 아래 #0d0d0d) 로 바꾸고 다음 단계에서 Maya 테마의
  단색 0.36 으로 되돌림. `reset_background()` = Maya 팩토리 배경 (홍보·비교 장면용).
- **`delegated`: 그라데이션은 킷의 Maya 테마가 켜져 있을 때만** (`theme.is_applied()`): Blender 의 그라데이션은 테마 (사용자 환경설정)
  라 사용자 자신의 테마는 고치지 않는다 — 그때 Alt+B 는 회색 → 밝은 회색 → 검정 (Maya 규칙의 「그라데이션 불가」 갈래). Maya 테마의
  변경은 Blender 로 전환 / 끄기에서 사용자 테마 복원으로 함께 사라짐; 다음 세션에도 남는 것은 Maya optionVar 와 같음.
- 메뉴: **Windows > Settings/Preferences** 를 잎에서 Maya 하위 메뉴로 (WindowMenu.mel:741 buildSettingsMenu 순서: Preferences ― Hotkey
  Editor, Color Settings, Marking Menu Editor, Shelf Editor, Panel Editor ― Plug-in Manager; Performance Settings 는 레거시 뷰포트일 때만).
  Preferences / Hotkey Editor (Keymap 절) / Plug-in Manager (Add-ons 절) = Blender 환경설정, **Color Settings = `allset.color_settings`**
  (3D Views: Background 색, Gradient Background, Gradient Top / Bottom; 현재 상태로 채워 열림), 나머지 셋은 회색 + 안내 (`notices`).
- **`delegated`: Ctrl+B 보조 연결 안 함** — Maya 에서 Ctrl+B 는 Bevel 이라 그 뜻을 유지 (사용자의 기억은 Alt+B).
- 홍보 장면: `tools/listing_shots.py` 가 테마 적용 직후 `reset_background()` — 이후 모든 홍보·마케팅 장면 (steps 121–123) 은 Maya
  팩토리 배경 (단색 #5c5c5c) 으로 찍는다.
- 매핑 표 `CycleBackgroundColor` 설명 갱신, `docs/keymap_mapping.md` 재생성.

## 기본 배경 확인

- 테마 파일 넷 (4.5 + 5.0 / 5.1 / 5.2) 모두 3D View `SINGLE_COLOR`, `high_gradient` #5c5c5c = Maya `background_flat` 0.36 (ΔE ≤ 2,
  `test_factory_background_is_maya_flat`). 화면 픽셀: Maya 모드 + Maya 테마의 뷰 왼쪽 열 11 점 #5c5c5c, Maya 실측 #5c5c5c — ΔE00 0.00.

## 검증

- 헤드리스 4.5 전체 **888 / 888** (106 파일, `test_step120_background` 8 개 포함). 5.0.1 / 5.1.2 / 5.2.2: 관련 4 파일 (아래 「최종 측정」).
- GUI `gui_step120_background` (실제 Alt+B 이벤트, 화면 픽셀 vs Maya 실측): 4.5 **14 / 14**, 5.2.2 **14 / 14**.

| 상태 | 킷 픽셀 | Maya 픽셀 | ΔE00 |
|---|---|---|---|
| 팩토리 | #5c5c5c | #5c5c5c | 0.00 |
| 밝은 회색 | #9f9f9f | #a1a1a1 | 0.61 |
| 그라데이션 위 | #869ab0 | #889db3 | 0.97 |
| 그라데이션 아래 | #111212 | #111315 (#0d0d0d 값) | 1.19 |
| 그라데이션 가운데 (t = 0.5) | #4d5863 | #5c6f83 | 9.0 (최대 9.2) |
| 검정 | #000000 | #000000 | 0.00 |

- 그라데이션 가운데가 다른 이유: Blender 는 두 테마 색을 화면 값으로 곧게 섞고, Maya 의 곡선은 더 밝다 (≈ 지수 1.7 섞기). Blender 테마에는
  두 색밖에 없고, PRE_VIEW 그리기 처리기로 직접 그린 그라데이션은 배경 패스에 덮여 안 보임 (GUI 탐침, `tmp/r120/pre_view.png`) — 남은 것.
- 스크린샷 직접 확인: 그라데이션 (위 청회색 → 아래 거의 검정), Color Settings 대화 상자.

## 최종 측정

마지막 코드 기준 (2026-10-20):

| Blender | 헤드리스 | GUI |
|---|---|---|
| 4.5.4 | 전체 888 / 888 (106 파일) | 전체 1135 / 1135 (90 파일) |
| 5.0.1 / 5.1.2 / 5.2.2 | 관련 4 파일 (step 120 / 107 / 101 / 54) 41 / 41 씩 | 5.2.2 `gui_step120_background` 14 / 14 |

- 메뉴 작동 비율 (`tools/menu_count.py`): 유일 경로 1318 중 587 (44.5 %).

## 남은 것

- 그라데이션 가운데 ΔE00 ≈ 9 (위 설명). Blender 가 그라데이션 곡선이나 3 색 이상을 허용하면 맞출 수 있음.
- 사용자 자신의 테마일 때 그라데이션 단계 없음 (delegated, 위).
- Maya Color Settings 창의 다른 색 (UI·노드 등) 과 Preferences > Display 의 다른 항목은 없음 (Color Settings = 배경 부분만).
- 실제 화면 확인: `docs/manual_checks.md` 「Step 120」.
