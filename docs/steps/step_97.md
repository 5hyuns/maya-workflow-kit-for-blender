# Step 97 — manual_checks 정리 2 (시뮬레이션 가능 항목 이어서)

backlog 8 (재점검 6차, `hermes/autodrive_bmk/backlog.json` 마지막): step 88 「분류」 의 「시뮬레이션 가능, 아직 안 옮김」 항목
(step 59–79) 을 `tests/gui/gui_manual_sweep.py` 에 `[M<step>-<n>]` 검사로 옮기고, 통과한 항목을 `docs/manual_checks.md` 에서 체크.

## 계획

- step 88 과 같은 규칙: 항목 **문구 전부**를 확인한 검사가 모두 통과해야 `[x] … (gui_manual_sweep)`. 일부를 사람 눈 (색·느낌) 이나
  Python 이 못 읽는 것 (operator report) 으로 남기면 그 항목 끝에 주석.
- 키·클릭·드래그·마킹 메뉴 제스처 = simulated event (한 틱에 이동 하나: step 28 / 95). **delegated**: 메뉴 / 셸프 / 사이드바 버튼은 그 연산자를
  실행 (`maya_kit.menu_item` = 메뉴 경로, `maya_kit.shelf_button` = 셸프, 버튼은 그 operator) — 클릭 → 연산자 연결은 각 step 의 GUI 테스트가
  증명; 대화상자는 OK 값 (operator 속성) 으로 실행. 팝업 / 패널 내용은 draw 함수를 기록용 layout (`OpRecorder`) 으로 그려 확인.
- 블록 단위로 작성 (`tmp/sweep97/b<step>.py`, `splice.py` 로 이어 붙임), 개발 중엔 `MAYA_KIT_SWEEP_ONLY="m67_,…"` (설정 단계 + 접두사
  단계만) 로 절마다 실행. 전환 (step 60) 은 설정을 바꾸므로 맨 끝.
- 찾은 kit 버그는 그 자리에서 고치고 헤드리스 회귀 테스트 (`tests/test_step97_sweep_fixes.py`).

## 한 것

- `tests/gui/gui_manual_sweep.py`: step 88 의 13 항목 뒤에 57 항목 (아래), 검사 수는 「검증」. 공용 도우미 (`drag` 단계 생성, `gesture` /
  `mm2` 마킹 메뉴, `OpRecorder`, `wait`), 파일 맨 위 쪽 `GUI_TIMEOUT = 2400`.
  - 59-2/4/5/6/8/9, 60-2/3/4, 62-1..6, 63-2/3/4/6, 64-1/2/3/5, 65-2..5, 66-1/3, 67-2..5, 68-2/4/5/6, 69-2/4/5, 70-2, 72-1/3/4, 73-2,
    76-1..4, 77-1/3, 78-1/2/4/5, 79-1/2.
  - step 88 「분류」 의 목록은 58 이라 적었지만 실제로 세면 57 (59-2 … 79-2).
- `tests/gui/run.py`: 테스트 파일이 `GUI_TIMEOUT = <초>` 를 두면 그 시간 (기본 180 초 그대로) — sweep 전체는 180 초를 훨씬 넘음.
- **찾아 고친 kit 버그 10 건** (각각 그 절 GUI 로 확인):
  1. 매니퓰레이터를 누르고 잠시 멈춘 뒤 끌면 활성 핸들 기억·Shift 복제가 실패 — `operators/manip.py` watch 가 LMB 누른 동안 기다림
     (기즈모는 드래그 문턱을 넘어야 변환 시작).
  2. Tweak 툴에서 커브 / 본을 눌러 끌면 선택만 됨 — `select_priority.py` 가 PRESS 를 먹으면 직접 translate 시작.
  3. 오브젝트 모드 Shift+Q 탭 = 편집 모드는 되나 툴이 안 바뀜 — `marking/__init__.py` `_tool_later` (툴은 그 모드에서 설정).
  4. Shift+G 두 번째부터 큐브가 안 생김 — `key_batch.repeat_at_mouse` REGISTER 제거 (자신이 「마지막 연산」 이 되면 안 됨).
  5. cm 템플릿에서 1 cm 간격 SDK 키가 하나로 합쳐짐 — Blender F-curve 는 x 0.01 안의 키를 합침 (측정): 길이 드라이버 곡선의 x = 표시 단위
     (`driven_key.curve_scale`, 드라이버 식 `sdk*100`).
  6. Channel Box 사용자 속성 입력이 Min / Max 로 안 잘림 — `channel_box.set_value` clamp (Maya 처럼).
  7. 면 프리셀렉트 기즈모가 압출 화살표·In-View 상자 클릭을 가로챔 — `preselect._extrude_block`.
  8. Keep Image 안내 「J / Alt+J to compare」 뒤에 키가 없음 (IC 의 Image 키맵엔 J 가 없음) — `maya_patches.patch_render_slots`
     (`image.cycle_render_slot` J / Alt+J reverse, Blender 기본과 같음).
  9. 프로젝트가 있어도 Ctrl+O / Status Line 열기 / File > Open Scene 이 Documents 에서 열림 — Blender 의 Open 창은 넘겨준 `filepath` 대신
     최근 파일 자리에서 시작 (측정; Save As 는 따름, step 69 는 Save As 만 확인했었음): `project.browse_from_later` 가 열린 파일 창의
     `params.directory` 를 scenes 로.
  10. 피벗을 돌린 오브젝트 다음에 다른 오브젝트를 고르면 Move 축이 앞 오브젝트의 피벗 축 그대로 (X 홀드 그리드 스냅이 비스듬한 축을 따라
      7.14 cm 에) — Maya 는 피벗 축이 오브젝트마다: `pivot.follow_lead` (depsgraph 핸들러) 가 lead 가 바뀌면 「Maya Pivot」 축을 새 lead 의
      피벗 방향으로, 돌린 피벗이 없으면 Object (LOCAL) 로.
- 테스트용 리팩터: `view_message.placement` (메시지 위치 계산을 함수로).
- `tests/test_step97_sweep_fixes.py` (새): 5, 6, 8, 10 의 헤드리스 회귀 (SDK 1 cm 세 키 + 구동, rx 는 x 그대로, CB clamp 절대 / 상대 / 범위 없음,
  Image J / Alt+J, Maya Pivot 축이 lead 를 따름).
- `docs/manual_checks.md`: 통과 항목 체크 + 맨 위 자동 / 수동 수.

## 측정 / 함정

- 편집 모드 undo 는 그 단계의 선택 모드까지 되돌림; undo 뒤엔 오브젝트를 이름으로 다시 찾을 것. `bpy.data` 로 만든 상태는 undo 기준이 없어
  `ed.undo_push` 를 먼저. Python 직접 호출은 `('EXEC_DEFAULT', True, ...)` 로 undo 단계.
- `Operator.report` 는 RNA 함수라 Python 클래스에서 가로챌 수 없음 → report 문구는 코드 상수로 확인 (step 88 선례).
- `wm.window_new` = 탑바 없는 임시 창, `window_new_main` = 탑바 있는 창. hold 키는 틱마다 하나씩, 누르기 직전 다시 hover.
- 재질 미리보기는 장면 엔진의 preview 지원을 씀: Workbench 장면에서는 Hypershade 미리보기가 비어 있음 (Blender 동작).
- 렌더 슬롯이 비었는지는 `Image.save_render` 실패로만 알 수 있음 (Render Result 의 `size` 는 늘 (0, 0)).
- 파일 창의 연산자는 `SpaceFileBrowser.active_operator` (임시 창의 `modal_operators` 가 아님); `bpy.data.libraries.load` 는 열려 있는
  파일 자체를 못 읽음 (복사본으로).
- 강체가 바닥에 닿아 멈추는 데 Maya 단위 1 = 1 m 중력으로 2 초 넘게 걸림 (8 단위 낙하) — 검사는 3 초.

## 분류 (step 81–96, 49 항목 — 이번에 옮기지 않음, 다음 정리 후보)

- **사람 판단 (10)**: 81-1, 81-3, 82-5 (큰 장면), 90-2 (Walk 느낌), 90-5 (키보드 배열), 91-2 (UI 배율), 95-1, 96-1 (UI 배율), 96-2, 96-4.
- **event_simulate 로 못 함 (1)**: 90-3 (Range Slider 더블클릭).
- **시뮬레이션 가능 (38)**: 81-2, 82-1..4, 83-1..4, 84-1..4, 85-1..4, 86-1..3, 87-1..5, 90-1, 90-4, 91-1, 92-1..3, 93-1..3, 94-1..3, 96-3.

## 검증

- GUI `tests/gui/gui_manual_sweep.py` 331/331 (전 46: step 88 의 13 항목 + 이번 57 항목). 절마다 `MAYA_KIT_SWEEP_ONLY` 로 통과시킨 뒤
  전체 실행에서 순서 탓 실패 3 → 고침: M59-5 (kit 버그 10), M65-2 (노드 번호는 장면마다 — 테스트가 카운터를 지움), M68-4 (천 캐시가 재생
  범위를 따르는데 테스트가 1 프레임부터 돌림).
- `docs/manual_checks.md`: 369 항목 중 [x] 70 (전 13), 수동 299; 일부를 간접 확인한 8 항목은 끝에 주석.
- 헤드리스 718/718 (전 713 + step 97 5), GUI 전체 1003/1003, dogfood 47/47 (콘솔 0). `tools/gen_keymap_mapping.py` 대응표 변화 없음 (구현 155).

## 남은 것

- step 81–96 의 시뮬레이션 가능 38 항목 (위 분류), step 2–58 절.
- 사람 판단 / 환경 불가 항목은 손 확인.
- backlog (90–97) 끝. 다음은 사용자 결정 (배포 decision 11) 또는 재점검 7차.
