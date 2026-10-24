# Step 153 — Blender 5.x pass (#90) + the owed 5.x runs

## 계획

backlog 146 의 153: #90 (5.0+ 에서 Paint Skin Weights ❒ 오류) 을 `compat.py` 로 고치고, 밀린 실행 (헤드리스 전체 5.0.1 / 5.1.2 /
5.2.3, GUI 전체 5.2.x) 의 실패를 모두 고친 뒤 `docs/compat_5x.md` 에 버전별 표.

레인 (delegated): 코드 수정은 한 파일 (`skin.py`) 이라 메인이 바로 함. 테스트 실행이 시간 대부분이라 버전별 실행을 레인으로 나눔:
Blender 동시 2 개 (PC 부하 규칙) → 5.0.1 + 5.2.3 헤드리스 → 5.1.2 헤드리스 + 5.2.3 GUI 전체 → 4.5 헤드리스, 실패 파일 `-k` 재실행 →
수정 뒤 네 버전 헤드리스 재실행 (한 줄로 순서대로) + 4.5 GUI 전체 (단계 끝 한 번). 서브에이전트는 안 씀: 실행은 백그라운드 명령,
판단·수정은 실패 로그를 본 메인이 해야 해서.

## 한 일

**#90 Paint Skin Weights ❒ (5.0+)** — 5.0.1 / 5.2.3 에서 실측: `ToolSettings.unified_paint_settings` 가 없어지고 페인트 모드마다
`tool_settings.weight_paint.unified_paint_settings`, 그리고 `unprojected_radius` (반지름) 가 `unprojected_size` (**지름**, 설명
"Diameter of brush in Blender units") 로 바뀜. 위치만 옮기면 5.x 에서 Maya Radius(U) 가 반이 됨.
- `compat.unified_paint_settings(ts, paint)` / `unprojected_radius(ups)` / `set_unprojected_radius(ups, r)` (속성 유무로 판단,
  5.x 는 2r 저장). `operators/skin.py apply_paint_settings` 가 이것을 씀.
- 테스트도 같은 도우미 (`test_step140_rig`, `test_step129_audit_p1` — step 145 감사의 5.2.2 실패 3 개 전부).

**GUI 전체 5.2.3 에서 나온 실패 15 개** (4.5 에서도 같은지 `-k` 로 나눠 봄):

| 실패 | 원인 | 고침 |
|---|---|---|
| sweep M59-8 W 메뉴 NW Object / NE Component (4.5 도) | step 151 의 Maya 크기 상자: N (Symmetry, 하위 메뉴) 상자가 넓어져 NE / NW 구역까지 옴. 빠른 대각선 제스처가 링 반경 밖에서 그 상자를 지나면 N 하위 메뉴가 열려 놓을 때 아무것도 안 됨 | **킷 수정** `marking/engine.Session.move`: 방사 하위 메뉴는 포인터가 **그 항목의 구역**에 있을 때만 끌어서 엶 (Maya 제스처 = 방향). `test_step153_compat` 두 개 |
| sweep M70-2 Shift+S 두 번 꺾는 제스처 4 개 (4.5 도) | 테스트: 첫 획 끝에서 하위 메뉴가 열린다고 가정 — step 151 (반경 80 → 55) 뒤로는 링을 처음 넘은 샘플에서 열림, 둘째 획의 구역이 어긋남 | 첫 획 샘플 0.2 / 0.4 / 1.0 (마지막만 링 밖) |
| `gui_step94_pivot_menu` S 끌기 = Reset Pivot (4.5 도) | 테스트: 120 px 끌기는 step 151 뒤 Maya 목록 (누른 점 아래 87 px × 배율) 의 첫 줄 (Bake Pivot Orientation) 에 떨어짐 | 세션의 S 상자 중심에서 놓음 |
| `gui_step129_time`, `gui_step148_cb` | 테스트가 `Action.fcurves` 직접 읽음 (5.0 layered action) | `compat.id_fcurve_collection` / `id_fcurves` |
| `gui_step150_outliner` | 테스트가 `Bone.select` 씀 (5.x 없음) | `channel_box.set_bone_selected` |
| `gui_step144_loop` Slide Edge | 테스트가 고리 높이 −0.296 을 1e-4 로 찾음 — 5.2.3 은 클릭 위치가 −0.2962 | 기억한 높이에 가장 가까운 고리 |
| `gui_step124_persp_label` 되돌리기 | 5.2.3 은 접힌 asset shelf 머리 띠를 Blender 가 스스로 1 px 로 둠 — 킷이 숨긴 게 없어 돌려줄 것도 없음 (실측) | 킷이 숨겼을 때만 「돌려줌」 검사, 아니면 「숨긴 것 없음」 |
| `gui_step146_option_box` 「옵션 창 뒤 Maya 메뉴 닫힘」 4 개 (5.x 만) | **Blender 5.0 동작 변경**: 메뉴 · 팝업이 클릭할 때까지 열려 있음 (`PreferencesView.menu_close_leave`, 기본 꺼짐, 5.0 UI 릴리스 노트 5953ff318c). 포인터를 멀리 보내도 Maya 메뉴가 안 닫힘. Python 에는 팝업을 닫는 호출이 없고 킷은 환경설정을 쓰지 않음 (step 130) | `compat.menus_close_on_leave(prefs)` (읽기만): 꺼져 있으면 멀리 / 되돌아오는 포인터 이동을 하지 않고 옵션 창을 엶 (Maya 메뉴는 그 아래 열린 채, 클릭 / Esc 로 닫힘). 테스트는 그 상태를 검사 |

- delegated: 5.x 옵션 상자 — 환경설정 `menu_close_leave` 를 잠깐 켜는 방법은 스토어 규칙 (환경설정 쓰기 금지, step 130 검사)
  때문에 안 씀. 4.5 와 5.x 에서 `menu_close_leave` 를 켠 사용자는 그대로 닫힘.
- delegated: M59-8 은 킷 동작 수정 (Maya 는 방향으로 고름), M70-2 / pivot 은 테스트 수정 (Maya 기하에서 사용자 손 동작과 같은 점에서
  놓도록).

## 검증

- 헤드리스 전체 (수정 뒤): 4.5.4 **1394 / 1394** (+ `test_step153_compat` 4 개 → 관련 6 파일 62 / 62), 5.0.1 **1398 / 1398**,
  5.1.2 **1398 / 1398**, 5.2.3 **1398 / 1398** (169 파일). 수정 전 첫 실행: 네 버전 모두 1394 / 1394 (#90 수정 포함).
- GUI 전체 5.2.3: 1622 통과 / 15 실패 (146 파일, 2 GUI_SKIP) → 실패 7 파일을 `-k` 로 다시: 전부 통과 (sweep M59-8 + M70-2 16 / 16,
  나머지 6 파일 69 / 69 → persp_label 3 / 3, pivot_menu 통과).
- 4.5 의 같은 파일: sweep 19 / 19, persp_label 3 / 3, loop + option box 36 / 36, pivot / skin 관련 통과.
- GUI 전체 4.5 (단계 끝 한 번, 수정 뒤): **1641 / 1644** (146 파일, 2 GUI_SKIP). 실패 3 개는 모두 `gui_step129_panel_toolbar`
  (버튼 29 / 25 개 찾음, popover 클릭) — 헤드리스 네 버전이 같이 돌던 때였고 혼자 다시 돌리면 **36 / 36** (부하 중 타이밍).
- 결과 표: `docs/compat_5x.md` 「버전별 결과 — step 153」.

## 남은 것

- 5.x: 옵션 상자를 누르고 있다 연 뒤 Maya 메뉴가 그 아래 열린 채 (Blender 5.0 의 「클릭할 때까지 열림」; 사용자가 Preferences >
  Interface > Close menus on leave 를 켜면 4.5 처럼 닫힘) — `docs/manual_checks.md` 「Step 153」.
- step 145 「5.2.2 1305 / 1308」 은 이제 5.2.3 기준 1398 / 1398. 5.2.2 는 따로 다시 돌리지 않음 (같은 5.2 LTS, 최신 패치로 대체).
- `gui_step129_panel_toolbar` 는 다른 Blender 가 돌 때 버튼 찾기가 흔들림 (혼자 36 / 36) — 다음 전체 묶음에서 다시 보이면 찾기 대기를 늘림.
- 5.1.2 수동 스윕 한 세션 멈춤 (step 118) 은 이번에 5.1.2 GUI 를 안 돌려 그대로 미확정.
