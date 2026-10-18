# HANDOFF

## 현재 작업

- Step 98 (재점검 7차, 정밀 비판 「이건 Maya여야 한다」) 완료 — `docs/steps/step_98.md`, 수치 부록 `docs/steps/step_98_quant.md`,
  PLAN 「재점검 7차(정밀 비판)」.
  - Maya 2022 와 kit 를 1600x900 로 같은 장면 (첫 화면, 5 메뉴 세트 전 최상위 메뉴, 셸프 탭, File 대화상자·옵션, 모델링·UV·애니·리깅·FX·렌더
    창) 을 띄워 나란히 113 쌍 `research/maya/screens/audit7/pairs/` (Maya 스크립트 `research/scripts/maya_audit7/`, kit 세션
    `tmp/audit7_session.py`). 차이 36 항목 점수화.
  - 수치: 메뉴 1251 중 작동 370 (29.6 %), 회색 881 중 866 이유 없음, 진짜 옵션 창 6/500, 셸프 98/203, 키 미검토 219 (잘못된 동작 7),
    실제 Maya 메뉴 최상위 746 중 kit 에 없는 것 약 60 (Audio·Stereo 빈 메뉴).
  - 가장 큰 차이: 빈 Outliner, **125 % 에서 Tool Box 열이 빔** (이 PC 실제 배율), 회색 메뉴, 옵션 박스, Blender 파일 브라우저, lambert1 없음,
    Import/Export 하위 메뉴, UV / Graph / Hypershade 창이 Blender 모양.
  - 고친 버그 2: Channel Box 핸들러 AttributeError (File Browser / Preferences 창 컨텍스트, `tests/test_step98_audit_fixes.py`),
    Create Reference 의 「.ma 를 Import」 안내 문구.
  - 검증: 헤드리스 719/719, kit 세션 PASS (콘솔 traceback 0), Maya 촬영 146 장.
  - **바로 다음 할 일**: step 99 = backlog 1 「First screen: Maya Outliner rows, Tool Box at 125 %, dock tabs」. backlog 12 개 =
    `hermes/autodrive_bmk/backlog.json` (사본 `backlog_98.json`), PLAN 「재점검 7차」 우선순위 1–12 와 같음. 배포 결정 (decision 11) 은 사용자 대기.

- Step 97 (manual_checks 정리 2) 완료 — `docs/steps/step_97.md`. **재점검 6차 backlog (90–97) 모두 끝.**
  - `tests/gui/gui_manual_sweep.py` 에 step 59–79 의 시뮬레이션 가능 57 항목 (`[M<step>-<n>]`) → `docs/manual_checks.md` 369 항목 중 [x] 70
    (전 13), 수동 299. step 81–96 절 분류 (사람 판단 10 · 불가 1 · 시뮬레이션 가능 38) 는 step_97.md 「분류」.
  - 찾아 고친 kit 버그 10 (step_97.md 「한 것」): 매니퓰레이터 누른 채 멈춤, Tweak 커브 / 본 드래그, Shift+Q 탭 툴, Shift+G 반복, SDK 1 cm 키 병합,
    CB 사용자 속성 clamp, 프리셀렉트가 압출 화살표 가로챔, J / Alt+J 렌더 슬롯 키 없음, Ctrl+O 가 프로젝트 scenes 에서 안 열림,
    「Maya Pivot」 Move 축이 다음 오브젝트에 남음. 헤드리스 회귀 `tests/test_step97_sweep_fixes.py`. `tests/gui/run.py` 에 파일별 `GUI_TIMEOUT`.
  - 검증: 헤드리스 718/718, GUI 1003/1003 (sweep 331), dogfood 47/47 (콘솔 0).
  - **바로 다음 할 일**: 계획된 단계 없음 (backlog 90–97 끝). 사용자 결정 대기 — (1) 배포 결정 (decision 11, `docs/DISTRIBUTION.md`),
    (2) 재점검 7차 (대응표·키맵 미검토 219 행·manual_checks), (3) manual_checks step 81–96 의 시뮬레이션 가능 38 항목 이어서 옮기기.

- Step 96 (Outliner Sets) 완료 — `docs/steps/step_96.md`. **대응표 UI 마지막 Partial 종결 (UI 9/0/0/0, 합계 30/1/0/2 = 91 %).**
  - 세트 = 씬에 연결 안 한 컬렉션 (`operators/sets.py`, mayapy 측정 `research/maya/re/sets.md`: set1/set2…, 선택 유지, select = 멤버). Create > Sets > Set (❑) /
    Quick Select Set..., Select > Quick Select Sets 매핑. 레이아웃 Outliner (Blender C 목록) 밑에 세트 행을 그림 (`ui/outliner_sets.py`: framebuffer 한 줄 + 이진 탐색으로
    마지막 행, 클릭 = 멤버 선택 / Ctrl 토글 / 삼각형 = 멤버 행, RMB = 세트 메뉴). 사이드바 kit Outliner 에도 SET 행.
  - 검증: 헤드리스 713/713, GUI 718/718, dogfood 47/47.
  - **바로 다음 할 일**: step 97 = manual checks 정리 2 (step_88.md 「분류」 의 step 59–79 시뮬레이션 가능 58 항목을 tests/gui 로, 체크 표시).
    backlog 의 마지막 항목. backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 95 (V 스냅 확대) 완료 — `docs/steps/step_95.md`.
  - step 81 의 「확대하면 V 스냅이 안 걸림」 은 kit · 확대 · 가림 검사 탓이 아니라 Blender 가 스냅 대상을 10 ms 에 한 번만 찾는 것
    (`transform_snap.cc` transform_snap_mixed_apply) + 시뮬레이션이 이동을 한 틱에 몰아 보낸 것. 확대하면 드래그가 길어 첫 이동이 정점에서 멀었음.
    `tests/gui/gui_step95_v_snap.py` (기본 / 확대 × X 화살표 → 앞·안쪽 정점, 가운데 핸들) 이동을 틱마다 → 모두 붙음. kit 코드 변경 없음 (delegated),
    manual check (빠르게 끌어 바로 놓기) 추가, CLAUDE.md 주의 한 줄.
  - 검증: 헤드리스 704/704, GUI 708/708.
  - **바로 다음 할 일**: step 96 = Outliner Sets (research/README.md 대응표의 Outliner 행이 Sets 없어서 Partial, step_82.md 「남은 것」).
    그다음 97 manual checks 정리 2. backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 94 (피벗 편집 RMB 마킹 메뉴) 완료 — `docs/steps/step_94.md`.
  - D / Insert 피벗 편집 중 RMB = Maya buildObjectMenuItemsNow 편집 모드 메뉴 (N Pin ☐ · NW/NE Snap Orientation/Position ☐ · S/SE/SW Reset ·
    E Exit, research 위치). Reset = 오브젝트 delta_location 0 / 컴포넌트 커서 → bbox 중심, Pin 꺼짐 (Maya 기본) = 선택이 바뀌면 사용자 컴포넌트
    피벗 해제 (`operators/pivot_menu.py`, `hold.ComponentPivotEdit`).
  - 검증: 헤드리스 704/704, GUI 702/702, dogfood 47/47.
  - **바로 다음 할 일**: step 95 = backlog 6 「V snap when zoomed in」 (step_81.md 「남은 것」: 확대 상태에서 V 점 스냅이 안 걸림 — GUI 재현, 원인,
    고치거나 한계로 문서화). backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 93 (선택 마스크 다듬기) 완료 — `docs/steps/step_93.md`.
  - Shift+Q 메뉴 체크 상자 (Poly Vertices / Poly Edges / Faces = 메시 선택 모드), **선택 마스크를 New / Open 너머로 유지** (Maya 2022 GUI 측정:
    마스크는 세션 상태라 초기화되지 않음 — backlog 문구와 반대, `research/maya/re/selection_masks.md`), Tool Settings 맨 위 Reset Tool
    (`ui/tool_settings.py`: 툴 옵션 기본값 + Maya Move/Rotate/Scale 기본값).
  - 검증: 헤드리스 698/698, GUI 698/698, dogfood 47/47.
  - **바로 다음 할 일**: step 94 = backlog 5 「Pivot-edit RMB marking menu」 (D / Insert 피벗 편집 중 RMB: N Pin, S Reset, NE Snap pivot position, NW Snap
    pivot orientation, E Exit). backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 92 (Graph Editor 키 묶음) 완료 — `docs/steps/step_92.md`.
  - t = 현재 시간 가운데 (가로만), Alt+/ = Snap Time To Selection **토글** (Maya 관찰: 켜면 키 선택마다 가장 이른 선택 키로 시간; View 메뉴 체크),
    i 홀드 = Insert Key 툴 (MMB → 정수 프레임에 모양 유지 키, 새 키만 선택). Maya 동작 명세 `research/maya/re/graph_editor_keys.md` (QTest 관찰).
    대응표 구현 155 · 미검토 219.
  - 검증: 헤드리스 692/692, GUI 693/693, dogfood 47/47.
  - **바로 다음 할 일**: step 93 = backlog 4 「Selection mask polish」 (Shift+Q 마킹 메뉴 체크 표시, 새 장면 / 열기에서 마스크 초기화, Tool Settings
    Reset Tool). backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 91 (뷰 표시 수정) 완료 — `docs/steps/step_91.md`.
  - 템플릿 3D 뷰 부모 관계 점선 끔 (Maya 2022 실행으로 선 없음 확인, `research/maya/screens/parent/`), 마킹 메뉴가 HUD (Adjust Last Operation) 위에
    그려짐 (`draw.REGION_TYPES` + 'HUD', 4.5 / 5.2 측정, 대조 실험), 독 = Channel Box 패널 하나가 CB / AE / MTK 를 그림 → Channel Box 탭이 Item 밑으로
    안 감 (AE 제목 줄도 없어짐).
  - 검증: 헤드리스 685/685, GUI 685/685, dogfood 47/47.
  - **바로 다음 할 일**: step 92 = backlog 3 「Graph Editor key batch」 (t = 현재 시간 가운데, Alt+/ = 선택 키로 시간, i 홀드 = Insert Key 툴).
    backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 90 (전역 키 묶음 4) 완료 — `docs/steps/step_90.md`.
  - Ctrl+X cut (계층째, 빈 data 도) + Ctrl+V paste (첫 노드 lead), Alt+X Walk (IC X-ray 제거), Alt+\ 재생 범위 = 애니메이션 범위, Alt+1/2/4 보이기
    토글, Ctrl+` / Shift+~ / Ctrl+Shift+~ 스무드 프록시 (`operators/global_keys4.py`), Edit > Cut / Paste. 대응표 구현 152 · IC 15 · 미검토 222.
  - 검증: 헤드리스 685/685, GUI 677/677, dogfood 47/47.
  - **바로 다음 할 일**: step 91 = backlog 2 「Viewport chrome fixes」 (부모 관계 점선 끄기, RMB 목록이 HUD 위로, AE 전환 때 사이드바 탭 순서).
    backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 89 (재점검 6차) 완료 — `docs/steps/step_89.md`, `docs/PLAN.md` 「재점검 6차」.
  - 대응표 29/2/0/2 (88 %; 타임라인 Done), 키맵 구현 142 · 미검토 237, manual_checks [x] 13 / 348. 탐색 세션 19/19: 부모 관계 점선이
    그려짐, RMB 목록이 Adjust Last Operation 패널 밑, AE 전환 때 사이드바 탭 순서. blindspot 7 (Ctrl+X, Alt+X Walk, Alt+\, Graph t / Alt+/,
    Alt+1/2/4, 스무드 프록시 키, Ctrl+PgUp/Dn).
  - 검증: 헤드리스 677/677, dogfood 47/47, 세션 19/19 (콘솔 0).
  - **바로 다음 할 일**: step 90 = backlog 1 「Global key batch 4」 (Ctrl+X, Alt+X, Alt+\, Alt+1/2/4, 스무드 프록시 키 + IC 행 정리).
    backlog = `hermes/autodrive_bmk/backlog.json` (8개, 사본 backlog_90.json). 배포 결정 (decision 11) 은 사용자 대기.

- Step 88 (manual_checks → GUI 테스트 정리) 완료 — `docs/steps/step_88.md`. **재점검 5차 backlog (81–88) 모두 끝.**
  - `tests/gui/gui_manual_sweep.py` 46 검사로 step 59–79 의 13 항목 확인 → `docs/manual_checks.md` 348 항목 중 [x] 13 (맨 위 자동 / 수동 수).
    step 59–79 분류: 자동 13, 사람 판단 23, 시뮬레이션 불가 7, 시뮬레이션 가능하지만 아직 안 옮김 58.
  - 검증: 헤드리스 677/677, GUI 667/667, dogfood 47/47.
  - **바로 다음 할 일**: 계획된 단계 없음. 사용자 결정 대기 — (1) 배포 결정 (decision 11, `docs/DISTRIBUTION.md`), (2) 재점검 6차 (대응표·키맵 미검토
    237 행·manual_checks 다시 매기기), (3) manual_checks 의 시뮬레이션 가능 58 항목 이어서 옮기기 (step_88.md 「분류」).

- Step 87 (뷰 키 묶음 3) 완료 — `docs/steps/step_87.md`.
  - Alt+A 표시 순환 (X-ray 조인트 / 전부 / 메시만), Alt+P persp ↔ ortho, Alt+화살표 1 px 이동, ` 홀드 = Tweak 툴, \ 홀드 = 카메라 뷰 2D 팬/줌
    (`operators/view_keys3.py`). 대응표 생성기: 셀 `|` = `&#124;` + 열 수 검사. 키맵 구현 142, 미검토 237.
  - 검증: 헤드리스 677/677, GUI 621/621, dogfood 47/47.
  - **바로 다음 할 일**: step 88 manual_checks → GUI 테스트 정리 (재점검 5차 backlog 마지막; step 59–79 항목 중 시뮬레이션 가능한 것을
    tests/gui 로, 체크 표시). backlog = `hermes/autodrive_bmk/backlog_81.json`. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 86 (Dope Sheet · NLA · Node Editor 선택 수식) 완료 — `docs/steps/step_86.md`.
  - SELECT_RULES 에 action / nla / node 클릭·박스 6 규칙 + Ctrl+Shift+LMB 기존 항목 3 개 제거 (select_leftright ×2, node viewer). Node 는 Maya 그대로
    (deselect / toggle), Dope Sheet / NLA Ctrl 은 토글 (Graph 와 같은 한계), Node Ctrl+드래그 = Blender 링크 떼기 유지.
  - 검증: 헤드리스 671/671, GUI 611/611, dogfood 47/47.
  - **바로 다음 할 일**: step 87 뷰 키 묶음 3 (Alt+A CycleDisplayMode, Alt+P CameraModeToggle, Alt+화살표 뷰 nudge, backtick, 백슬래시 + `Shift+\`
    표 행 이스케이프). 그 뒤 88 manual_checks → GUI. backlog = `hermes/autodrive_bmk/backlog_81.json`. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 85 (매니퓰레이터 Ctrl+축 / Shift+MMB) 완료 — `docs/steps/step_85.md`.
  - W / R 매니퓰레이터 축 Ctrl+LMB 드래그 = 나머지 두 축 평면 이동 / 스케일 + 그 평면이 활성 핸들, Move 가운데 Ctrl+클릭 = 활성 핸들 해제,
    Shift+MMB 드래그 = 첫 움직임에 가까운 축 (`operators/manip.py` manip_ctrl / manip_mmb_auto). Rotate 는 C 기즈모 그대로.
  - 측정: Ctrl 을 누른 채 시작한 이동은 스냅 반전 안 됨; 시뮬레이션에서 MMB CLICK_DRAG 항목은 불리지 않음 → PRESS + 모달.
  - 검증: 헤드리스 667/667, GUI 601/601, dogfood 47/47.
  - **바로 다음 할 일**: step 86 Dope Sheet · NLA · Node Editor 선택 수식 (Shift 토글 / Ctrl 해제 / Ctrl+Shift 추가; keymap/maya_patches.py
    SELECT_RULES 확장, step 84 의 Dopesheet LMB PRESS 맨 앞 항목 (TIMELINE 만) 고려). 그 뒤 87 뷰 키 묶음 3, 88 manual_checks → GUI.
    backlog = `hermes/autodrive_bmk/backlog_81.json`. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 84 (타임 슬라이더 Shift 범위 키 이동·늘이기) 완료 — `docs/steps/step_84.md`.
  - Shift 범위 가운데 드래그 = 범위 안 키 이동, 끝 화살표 = 반대 끝 기준 늘이기, 덮어쓰기, 언두 한 단계, 흰 화살표 (`operators/time_range.py`,
    `ui/time_slider.py` `time_range_drag`). 측정: `FCurve.update()` 는 같은 프레임 키를 합침 → 드래그 중엔 sort + handles_recalc 만.
  - 측정: 템플릿 Time Slider 줄은 전부 Blender 스크럽 띠 ("Time Scrub" 키맵이 Dopesheet 보다 먼저, IC 엔 없어 Blender 기본 것이 쓰였음) →
    Maya 키컨피그에 "Time Scrub" 을 만들고 kit 항목을 앞에 (step 56 의 범위 밖 클릭 = 해제도 이제 템플릿에서 동작).
  - 검증: 헤드리스 662/662, GUI 594/594, dogfood 47/47. 대응표 타임라인 행 → Done (Once / Oscillate 는 Blender 한계).
  - **바로 다음 할 일**: step 85 매니퓰레이터 Ctrl+축 = 평면 이동, Shift+MMB 자동 축 (`ui/manipulator.py`; 기즈모 키맵이라 「계획」 먼저).
    그 뒤 86 Dope Sheet·NLA·Node 수식, 87 뷰 키 묶음 3, 88 manual_checks → GUI. backlog = `hermes/autodrive_bmk/backlog_81.json`.
    배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 83 (키 삽입·이동 묶음) 완료 — `docs/steps/step_83.md`.
  - Alt+I / Ctrl+Shift+W/E/R = 곡선 모양 그대로 키 삽입 (Blender insert 는 auto 구간만 지킴 → 그 밖은 de Casteljau 분할), Shift+( / ) = 키 1 프레임
    이동 (키 에디터 = 선택 키, 그 밖 = 현재 시간 키 + 시간), Ctrl+Alt+, / . = 이전 / 다음 키 선택 + 이동 (`operators/key_insert.py`). 키맵 구현 133.
  - 검증: 헤드리스 656/656, GUI 585/587 (gui_step26 RMB 취소 간헐 2, 단독 통과), dogfood 47/47.
  - **바로 다음 할 일**: step 84 타임 슬라이더 Shift 범위 키 이동·늘이기 (모달이라 「계획」 먼저; `key_insert.move_keys`, `time_keys.time_range` 재사용).
    그 뒤 85 매니퓰레이터 Ctrl 평면, 86 Dope Sheet·NLA·Node 수식, 87 뷰 키 묶음 3, 88 manual_checks → GUI.
    backlog = `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_81.json`. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 82 (Outliner 드래그 = Maya 부모 지정) 완료 — `docs/steps/step_82.md`.
  - Outliner MMB 드래그 = Maya: 항목 위 = 자식으로, 행 사이 = 그 자리 (정렬 끔일 때 순서까지), 빈 곳 = 월드. 월드 위치 유지, parent inverse
    identity, 선택 그대로 (`operators/outliner_drag.py`). Blender LMB 드롭도 언두 후 Maya 방식으로 다시 적용 (언두 한 단계).
  - 측정: Blender 의 정렬 끈 Outliner 는 목록의 첫 항목을 맨 뒤에 그림 → 템플릿 정렬은 켜 둠 (delegated).
  - 검증: 헤드리스 646/646, GUI 579/579, dogfood 47/47.
  - **바로 다음 할 일**: step 83 키 삽입·이동 묶음 (Alt+I, Ctrl+Shift+W/E/R, Shift+( ), Ctrl+Alt+, .; backlog_81.json 3번).
    그 뒤 84 Shift 범위 키 이동, 85 매니퓰레이터 Ctrl 평면, 86 Dope Sheet·NLA·Node 수식, 87 뷰 키 묶음 3, 88 manual_checks → GUI.
    backlog = `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_81.json` (backlog.json 은 없음). 배포 결정 (decision 11) 은 여전히 사용자 대기.

- **체크포인트 (2026-10-18, /sc:save) — 지금 단계 = 없음 (step 81 까지 완료, 다음 = step 82)**
  - HEAD `06bfd06` = step 81. 작업 트리는 깨끗하다 (research/ 는 원래 추적 안 함; 이 체크포인트 줄만 미커밋).
  - 이번 세션: step 76–79 (재점검 4차 backlog 끝) → step 80 재점검 5차 (c74dead, f45557c) → step 81 persp 화각 (06bfd06).
  - 검증 (HEAD): 헤드리스 637/637, GUI (기본 배율) 559/559, dogfood 47/47.
  - **바로 다음 할 일**: step 82 Outliner 드래그 = Maya 부모 지정 (드롭/키맵 충돌이라 `docs/steps/step_82.md` 「계획」 부터).
    그 뒤 83 키 삽입·이동, 84 Shift 범위 키 이동, 85 매니퓰레이터 Ctrl 평면, 86 Dope Sheet·NLA·Node 수식, 87 뷰 키 묶음 3, 88 manual_checks → GUI.
    backlog = `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 여전히 사용자 대기.
  - 열린 발견: 끌고 가는 오브젝트가 화면에서 크면 V 스냅이 안 걸림 (시뮬레이션, step_81.md 「남은 것」, 손 확인 필요).

- Step 81 (Maya persp 화각) 완료 — `docs/steps/step_81.md`.
  - 템플릿 뷰 렌즈 35 → 70 (Blender 72 mm 센서 기준 = Maya 35 mm / 36 mm, 수평 54.4°), 모든 3D 뷰. Create > Camera = Maya 35 mm / 36 mm,
    Ctrl+Shift+C 카메라도 35. 새 장면 그리드 크기가 Maya 와 같아짐 (뷰 폭의 0.75, Maya 0.73).
  - 검증: 헤드리스 637/637, GUI 559/559 (gui_step59 화면 크기 맞춘 뒤), dogfood 47/47.
  - 발견: 끌고 가는 큐브가 화면에서 크면 V 스냅이 안 걸림 (시뮬레이션) → manual_checks, step_81 「남은 것」.
  - **바로 다음 할 일**: backlog 2 = step 82 Outliner 드래그 = Maya 부모 지정 (키맵/드롭 충돌이라 「계획」 먼저). 그 뒤 83 키 삽입·이동,
    84 Shift 범위 키 이동, 85 매니퓰레이터 Ctrl 평면, 86 Dope Sheet·NLA·Node 수식, 87 뷰 키 묶음 3, 88 manual_checks → GUI.

- Step 80 (재점검 5차) 완료 — `docs/steps/step_80.md`, `docs/PLAN.md` 「재점검 5차」.
  - 대응표 28/3/0/2 (85 %), 키맵 구현 125 · 미검토 254, manual_checks 320 열림 (체크 0). 4차 backlog (72–79) 모두 종결.
  - 새 발견: MayaKit persp 가 Maya 의 두 배 광각 (템플릿 뷰 렌즈 35 = Blender 72 mm 센서 기준 91.6°, Maya 54.4° = Blender 70).
  - 검증: 헤드리스 634/634, dogfood 47/47, 탐색 세션 15/16 (실패 1 은 세션 탓), 콘솔 0.
  - **바로 다음 할 일**: `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 8개 순서대로 (step 81부터) —
    1 Maya persp 화각 (렌즈 70), 2 Outliner 드래그 = Maya 부모 지정, 3 키 삽입·이동 묶음, 4 타임 슬라이더 Shift 범위 키 이동,
    5 매니퓰레이터 Ctrl+축 평면 / Shift+MMB, 6 Dope Sheet·NLA·Node 선택 수식, 7 뷰 키 묶음 3, 8 manual_checks → GUI 테스트.
    배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 79 (3D Cut and Sew UV Tool) 완료 — `docs/steps/step_79.md`. **재점검 4차 backlog (72–79) 모두 끝.**
  - UV > 3D Cut and Sew UV Tool: 3D 뷰에서 엣지를 따라 드래그 = UV 자르기, Ctrl = 꿰매기, Shift = 선택, x / s / d = Cut / Sew / Unfold + Layout,
    셸 경계 흰 굵은 선, 누를 엣지는 빨간 프리셀렉트. 메뉴·셸프·UV Toolkit·UV 마킹 메뉴에서 진입.
  - 검증: 헤드리스 634/634, GUI 555/555, dogfood 47/47.
  - **바로 다음 할 일**: 계획된 단계 없음. 사용자 결정 대기 — (1) 배포 결정 (decision 11: 이름·id, 무료/유료, 계정, CC0, 서명;
    `docs/DISTRIBUTION.md`), (2) 재점검 5차 (대응표·키맵 미검토 254 행·manual_checks 다시 매기기), (3) PLAN 「Left out」 나머지와
    각 step 문서 「남은 것」 (예: Cut and Sew 툴 마킹 메뉴, Shift+Q 체크 표시, Graph Editor 보기 버튼, 피벗 편집 RMB 메뉴).

- Step 78 (키 묶음 2) 완료 — `docs/steps/step_78.md`.
  - Graph Editor 1/2/3 (Stacked = Normalized + 안내), Shift+Q / Alt+Q 선택 툴 마킹 메뉴 (픽 마스크 / 정점·엣지·면·UV), Ctrl+Alt+←/→ Spin Edge,
    Shift+G 마우스 위치 반복, Ctrl+Shift+C 뷰에서 카메라. 키맵 구현 113 → 122.
  - 검증: 헤드리스 627/627, GUI 549/549, dogfood 47/47.
  - **바로 다음 할 일**: step 79 3D Cut and Sew UV 툴 (PLAN 「Left out of steps 54–67」 점수 20; 3D 뷰 엣지 클릭/드래그 = 자르기,
    Ctrl = 꿰매기, x/s/d = Cut/Sew/Unfold; step 66 `operators/uv_tools.py` 의 uv_cut / sew 재사용). 툴 모달이라 「계획」 먼저.
    79 가 재점검 4차 backlog 의 마지막. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 77 (편집 모드 Insert / D 피벗) 완료 — `docs/steps/step_77.md`.
  - 메시 편집 모드 Insert = D 와 같은 피벗 편집 (커서 툴 + 3D 커서 피벗) 토글. 면을 클릭하면 피벗 방향도 맞고, 끝나면 Move 축 "Maya Pivot".
    탭 = 사용자 피벗 지움 (bbox 중심). 대응표 D/Insert → Done (85 %).
  - 검증: 헤드리스 619/619, GUI 539/539, dogfood 47/47.
  - **바로 다음 할 일**: step 78 키 묶음 (Graph Editor 1/2/3, Shift+Q / Alt+Q, Ctrl+Alt+←/→ Spin Edge, Shift+G, Ctrl+Shift+C;
    `docs/keymap_mapping.md` 미검토 행). 그 뒤 79 3D Cut and Sew. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 76 (선택 우선순위) 완료 — `docs/steps/step_76.md`.
  - 오브젝트 모드 클릭이 Maya 처럼 IK 핸들 (10) > 조인트 = 아마추어 (9) > 커브 (4) > 메시 (2) 순으로 겹친 것 중 고른다 (가려져도).
    `operators/select_priority.py`, "3D View" CLICK / Tweak PRESS 앞 PASS_THROUGH_FIRST, 환경설정 「Selection Priority」.
  - 검증: 헤드리스 612/612, GUI 528/528, dogfood 47/47.
  - **바로 다음 할 일**: step 77 편집 모드 Insert / D 피벗 (컴포넌트 매니퓰레이터 피벗, research/maya/interaction.md D/Insert 행).
    그 뒤 78 키 묶음 (Graph 1/2/3, Shift+Q / Alt+Q, Spin Edge, Shift+G, Ctrl+Shift+C), 79 3D Cut and Sew.
    backlog = `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_72.json`. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- **체크포인트 (2026-10-18, /sc:save) — 지금 단계 = 없음 (step 75 까지 완료, 다음 = step 76)**
  - HEAD `10e6fd5` = step 75. 작업 트리는 깨끗하다 (research/ 는 원래 추적 안 함).
  - 이번 세션: step 71 재점검 4차 (8f4b596) → backlog 8개 (step 72–79) 중 72 (90ec5db) · 73 (9936fef) · 74 (46e43c9) · 75 (10e6fd5) 완료, 각 STEP_DONE.
  - 검증 (HEAD): 헤드리스 604/604, GUI (기본 배율) 516/516, dogfood 47/47.
  - **바로 다음 할 일**: step 76 선택 우선순위 (클릭 시 핸들 10 > 조인트 9 > 커브 4 > 메시 2, research/maya/interaction.md:74, defaults.json:105).
    키맵 충돌 설계라 `docs/steps/step_76.md` 「계획」 부터.
  - 그 뒤 77 편집 모드 Insert, 78 키 묶음 (Graph 1/2/3, Shift+Q / Alt+Q, Spin Edge, Shift+G, Ctrl+Shift+C), 79 3D Cut and Sew.
    backlog.json = `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json`.
  - 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 75 (Status Line 입력 줄) 완료 — `docs/steps/step_75.md`.
  - Status Line 에 Maya 입력 줄 (Absolute / Relative X Y Z, Rename, Select by Name) 과 회색 Construction History 를 넣었다 (`ui/input_line.py`).
  - 검증: 헤드리스 604/604, GUI 516/516, dogfood 47/47.
  - **바로 다음 할 일**: step 76 선택 우선순위 (조인트·커브·핸들이 메시보다 먼저, research/maya/interaction.md:74). 키맵 충돌 설계라 「계획」 먼저.
    그 뒤 77 편집 모드 Insert, 78 키 묶음, 79 3D Cut and Sew.

- Step 74 (프리셀렉트 확대) 완료 — `docs/steps/step_74.md`.
  - 엣지 / 면 모드와 Move / Rotate / Scale 툴에서도 Maya 처럼 커서 아래 컴포넌트를 빨갛게 미리 보인다 (Python 기즈모 `operators/preselect.py`).
  - Maya 2022 실측: 오브젝트 모드에는 하이라이트가 없다.
  - 검증: 헤드리스 596/596, GUI 510/510, dogfood 47/47.
  - **바로 다음 할 일**: step 75 Status Line 입력 줄 (abs / rel / rename / select by name, research/maya/ui_layout.md:208-211).
    그 뒤 76 선택 우선순위, 77 편집 모드 Insert, 78 키 묶음, 79 3D Cut and Sew.

- Step 73 (타임 슬라이더 키 틱 + Range Slider 드래그) 완료 — `docs/steps/step_73.md`.
  - 선택 노드의 키가 Maya 처럼 1 px 빨간 선 (브레이크다운 초록).
  - MayaKit 타임라인 헤더의 Range Slider 바를 끌어 재생 범위를 옮기거나 끝을 바꾼다. 더블클릭 = 전체 범위.
    바는 `ui/range_bar.py` 가 헤더 한 줄을 읽어 자리를 찾고 직접 그린다.
  - 검증: 헤드리스 589/589, GUI 504/504, dogfood 47/47.
  - **바로 다음 할 일**: step 74 프리셀렉트 확대 (엣지·면·오브젝트, Move/Rotate/Scale 툴 중; step 30 기즈모). 그 뒤 75 Status Line 입력 줄,
    76 선택 우선순위, 77 편집 모드 Insert, 78 키 묶음, 79 3D Cut and Sew.

- Step 72 (상단 바 다시 그리기 + Maya 인뷰 메시지) 완료 — `docs/steps/step_72.md`.
  - F2–F6 이 상단 메뉴 바를 바로 다시 그린다 (`status_line.redraw_top_bars`).
  - Maya 실측대로 인뷰 메시지 (`ui/view_message.py`): F8 (`maya_kit.toggle_sel_mode`), Ctrl+G, Ctrl+H / Alt+H / h, b 소프트 선택 켬, Make Live.
  - 검증: 헤드리스 581/581, GUI 496/496, dogfood 47/47.
  - **바로 다음 할 일**: backlog 2 = step 73 타임 슬라이더 키 틱 + Range Slider 드래그 (모달이니 step_73 「계획」 먼저).
    그 뒤 74 프리셀렉트 확대, 75 Status Line 입력 줄, 76 선택 우선순위, 77 편집 모드 Insert, 78 키 묶음, 79 3D Cut and Sew.

- Step 71 (재점검 4차) 완료 — `docs/steps/step_71.md`, `docs/PLAN.md` 「재점검 4차」. 대응표 27/4/0/2 (82 %, 3차 25/6/0/2),
  키맵 구현 113 · IC 10 · 미검토 267, manual_checks 287 열림. 새 발견: F2–F6 이 상단 메뉴 바를 다시 그리지 않음 (전역 영역),
  타임 슬라이더 키 틱 없음. 헤드리스 574/574, GUI (기본 배율) 483/483, dogfood 47/47, 탐색 세션 14/15 (실패 1 = 세션 확인 오류).
  **바로 다음 할 일**: `hermes/autodrive_bmk/backlog.json` 8개 순서대로 (step 72부터) — 1 메뉴 바 다시 그리기 + 인뷰 메시지,
  2 키 틱 + Range Slider 드래그, 3 프리셀렉트 확대, 4 Status Line 입력 줄, 5 선택 우선순위, 6 편집 모드 Insert, 7 키 묶음,
  8 3D Cut and Sew. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 70 (Graph Editor 탄젠트 툴바 · Shift+S · G · Auto Key · Playblast) 완료 — `docs/steps/step_70.md`. Graph Editor 헤더 탄젠트 아이콘 줄 + 고스트 커브,
  `maya_kit.set_tangent` / `key_edit` (Graph Editor 선택 키, 그 밖은 현재 시간 키), Shift+S 홀드 = Keys / Tangents 마킹 메뉴, Graph Editor G = 재생 범위 · D = Auto,
  Maya Auto Key (Only Insert Available, 백업·복원), `maya_kit.playblast` (임시 동영상 + 플레이어, □ 옵션 대화상자).
  헤드리스 574/574, GUI 0.8 484/484, gui_step70 7/7, dogfood 47/47.
  **바로 다음 할 일**: PLAN 의 워크플로우 단계 (54–70) 가 모두 끝남. 다음은 사용자 결정: (1) 배포 결정 (이름·id, 무료/유료 — decision 11, `docs/DISTRIBUTION.md`),
  (2) 남긴 후보 (`docs/PLAN.md` 「Left out of steps 54–67」 + 각 step 문서 「남은 것」: 3D Cut and Sew, Quad Draw Make Live, Maya Animation 워크스페이스, MASH, 3D 유체,
  Outliner Sets, Hypergraph, Graph 1/2/3, 버퍼 커브 스왑 등) 중 고르기, 또는 재점검 4차 (전체 갭 표 다시 매기기).

- Step 69 (씬 관리: 프로젝트 · 증분 저장 · 레퍼런스) 완료 — `docs/steps/step_69.md`. `operators/project.py`: Project Window / Set Project / Recent Projects
  (루트 + Maya 폴더 + 표시 파일, add-on 환경설정), 파일 창이 `<root>/scenes` 에서 (Ctrl+O/S/Shift+S, 메뉴, Status Line), 프로젝트 안 저장 → 렌더 `//../images/`,
  Ctrl+Alt+S = Maya 증분 (`shot_v001.0001`), Ctrl+R Create Reference = 링크 + library override + `ns:` 이름, Reference Editor = Outliner Blender File 창.
  헤드리스 566/566, GUI 0.8 477/477, gui_step69 7/7, dogfood 47/47.
  **바로 다음 할 일**: step 70 — Graph Editor 탄젠트 툴바 · Shift+S · G · Auto Key · Playblast 플레이어 (근거 `research/maya/workflows/animation.md`;
  `operators/time_keys.TANGENTS` 표). `docs/steps/step_70.md` 「계획」 먼저 (키맵 충돌). 70 이 PLAN 의 마지막 워크플로우 단계.

- Step 68 (FX: 시뮬레이션 스케일 · nucleus · 이미터 · nCloth · nCache) 완료 — `docs/steps/step_68.md`. `operators/fx.py`: g = maya_unit / Space Scale
  (중력 9.8·g, 길이 × maya_unit, 천 강성·감쇠 × g — 측정), `Scene.maya_kit_nucleus` + AE 「nucleus1」 탭, Create Emitter (`emitter1` + `nParticle1`),
  Emit from Object, nCloth / Passive / Remove / 강체를 선택 전부에, `maya_kit.ncache` (포인트 캐시 · 강체 · GN · Mantaflow). 측정: 파티클·강체는 1 m 장면과
  정확히 같음, Blender 하한 0.001 m (충돌 거리·두께·파티클 크기 = 0.1 유닛). 헤드리스 560/560, GUI 0.8 470/470, gui_step68 8/8, dogfood 47/47.
  **바로 다음 할 일**: step 69 — 씬 관리: Set Project · Ctrl+Alt+S 증분 · Create Reference + 네임스페이스 · Reference Editor (근거
  `research/maya/workflows/scene.md`). `docs/steps/step_69.md` 「계획」 먼저. 그다음 70 Graph Editor.

- Step 67 (Hypershade · Light Editor · Render 메뉴 · Keep Image · AE 맵 버튼) 완료 — `docs/steps/step_67.md`. `maya_kit.hypershade` = Shader Editor 새 창 +
  사이드바 「Hypershade」 탭 (Browser 미리보기 · Create · Assign Material To Selection · Property Editor; 메뉴·Status Line·핫박스 Windows 메뉴 공통),
  `maya_kit.light_editor` = 3D View 새 창 + 「Light Editor」 탭 (이름·색·Intensity·켜기·Solo, AE 라이트 섹션), Render 메뉴 17 항목 복원 (gen_menu_data
  `PLACEHOLDERS`), Render Result 헤더 Keep / Remove Image (render slots), AE 소켓 행 맵 버튼 (File/Ramp/Noise/Checker, Bump, Break Connection),
  standardSurface 이름 표 + aiStandardSurface. 측정: `Region.active_panel_category` 는 탭이 그려진 뒤 설정 가능 (전엔 read-only 오류).
  이어서: Render Settings = 언제나 새 Properties 창 (Render 탭, 타이머로 탭 설정), AE 라이트 Decay Rate 회색 행.
  헤드리스 550/550, GUI 0.8 460/462 (gui_step26 RMB 취소 2 항목 — 혼자 3/3 통과, 전체 실행 때만 나는 간헐 실패), gui_step67 10/10, dogfood 47/47.
  **바로 다음 할 일**: step 68 — FX: Maya 시뮬레이션 스케일 · nucleus · nParticles 이미터 · nCloth · nCache (근거 `research/maya/workflows/fx.md`,
  결정 10). `docs/steps/step_68.md` 「계획」 먼저. 그다음 69 씬 관리, 70 Graph Editor.

- Step 66 (UV 워크플로우) 완료 — `docs/steps/step_66.md`. UV Editor 열기 = 편집 모드 + UV Sync (창 하나만), `maya_kit.uv_component`
  (F12 UV / Alt+F12 UV Shell / 3D RMB E UV), UV Editor RMB 마킹 메뉴 (Maya texturePanelMenus.mel 방향) + Shift+RMB UV / UV Shell 도구,
  Cut (솔기 + 2e-4 분리 — Blender 섬 계산은 솔기를 무시, 측정) / Sew (작은 셸 닮음 변환) / Unfold (Unwrap Minimum Stretch, 셸 자리 유지) /
  Layout (pack, 패딩 px) / Texel Density, 키 Shift+X · Shift+S · Ctrl+U · Ctrl+L, UV Toolkit 사이드바 탭. 헤드리스 539/539, GUI 0.8 452/452,
  gui_step66 6/6, dogfood 47/47.
  **바로 다음 할 일**: step 67 — Hypershade 창·Light Editor·Render 메뉴·Render View Keep Image·AE 맵 버튼 (근거 `research/maya/workflows/render.md`).
  계획 먼저.

- Step 65 (Extrude 매니퓰레이터·In-View Editor·마지막 연산 INPUTS) 완료 — `docs/steps/step_65.md`. `maya_kit.extrude` = Maya polyExtrudeFace
  (mayapy 8 경우와 좌표 일치: Thickness shell · Local Translate Z · Offset · Divisions · Keep Faces Together), Ctrl+E/메뉴/마킹 메뉴/셸프/MTK.
  마지막 압출 = `Record` (압출 전 BMesh, 상태 서명; 언두/리두 따라감) → `maya_kit.extrude_edit` 로 다시 만들기 (언두 한 단계, F9 = Maya 이름).
  파란 화살표 기즈모 (Local Translate Z), In-View Editor 상자 (행 드래그/클릭 입력/토글), Channel Box INPUTS 맨 위 polyExtrudeFace1 + 안내.
  발견: 파이썬 `bpy.ops` 호출은 `undo=True` 없이는 언두를 쌓지 않음. 헤드리스 529/529, GUI 0.8 445/446 (step 18 Ctrl+E 기대 갱신 후 14/14),
  gui_step65 7/7, dogfood 47/47.
  **바로 다음 할 일**: step 66 — UV 워크플로우 (UV Editor 진입·UV Toolkit·UV 마킹 메뉴·Cut/Sew/Unfold/Layout·Texel Density; 근거
  `research/maya/workflows/uv.md`). 계획 먼저.

- Step 64 (Target Weld · Crease Tool · Multi-Cut 감각) 완료 — `docs/steps/step_64.md`. Target Weld = 킷 툴 (`register_tool`, LMB 드래그 모달,
  선택된 정점도 함께, Target/Center, 엣지 짝 병합), Crease Tool = 킷 툴 (MMB 좌우 드래그, Maya 값 ↔ Blender √(c/10), 실측 sharpness 10·b²),
  Multi-Cut (knife) Ctrl+클릭 = 클릭 자리 엣지 루프 / Ctrl+MMB 가운데 / Shift+클릭 = Snap Step % 시작점 + Tool Settings Maya 항목. 메뉴·마킹 메뉴·
  셸프·MTK 연결. 키맵 매핑 nameCommand 조회 고침 (Ctrl+Shift+X/Q 구현). 헤드리스 516/516 (+1), GUI 0.8 439/439, gui_step64 12/12, dogfood 47/47.
  **바로 다음 할 일**: step 65 — Extrude 매니퓰레이터 (Python GizmoGroup) + In-View Editor + 마지막 연산 INPUTS 행 (근거
  `research/maya/workflows/modeling.md` A3·A4, 히스토리 사후 수정 20 / Ctrl+E 15). 계획 먼저 (GPU·모달).

- Step 63 (Modeling Toolkit 도크·소프트 선택 Maya 단위·Combine/Separate/Mirror/Boolean) 완료 — `docs/steps/step_63.md`. MTK = dock 세 번째 항목
  (modeling_03 순서, 버튼 = 메뉴 동작, Status Line 토글 맨 앞), Maya 실측 (mayapy): 소프트 선택 반경 5, Combine = pCube2 + bbox 중심 피벗, Separate =
  그룹 아래 polySurfaceN. Mirror = bmesh 적용 + □ Mirror Options (`run_action` 이 `option_box` 속성 연산자에 넘김). 헤드리스 505/505, GUI 0.8 426/427
  (step 3 B 드래그 기대값 갱신 후 17/17), gui_step63 8/8, dogfood 47/47.
  **바로 다음 할 일**: step 64 Target Weld·Crease 툴·Multi-Cut 감각 (근거 `research/maya/workflows/modeling.md` 갭 표; MTK Tools 의 Target Weld 회색을 연결).

- Step 62 (Set Driven Key·포즈 모드 제약·Add Attribute·Blend Shape·Quick Rig) 완료 — `docs/steps/step_62.md`. SDK 창 = dock 의 CB 아래
  (Driver/Driven 스크롤 목록, Key · Load Driver · Load Driven · Close; 결과 = 드라이버 F-커브 키 = Maya animCurveUU), 창이 열린 동안 CB 로 바꾼 피동 값은
  드라이버 mute 로 유지 → Key/Close 가 풂; Constrain 이 포즈 모드면 본에; Modify/CB Edit > Add·Edit·Delete Attribute (CB 라벨 = Maya nice name);
  Blend Shape = join_shapes; Quick Rig = Rigify 켜기 + 메타 리그. CB 커스텀 속성 쓰기가 이제 depsgraph 를 태그 (드라이버 갱신). 헤드리스 495/495,
  GUI 0.8 417/419 (step 26 간헐, 재실행 통과), gui_step62 9/9 (tx 0.5 → ry 45), dogfood 47/47.
  **바로 다음 할 일**: step 63 Modeling Toolkit 도크·소프트 선택 Maya 단위·Separate/Combine/Mirror Maya 의미 (근거 `research/maya/workflows/modeling.md`).

- Step 61 (배포 방식 조사·결정, 공개 안 함, 사용자 요청 2026-10-18) 완료 — `docs/steps/step_61.md`, 비교·추천 `docs/DISTRIBUTION.md`,
  결정 `docs/user_decisions.md` 11. 추천 (delegated): 무료 GPL 핵심판 = 자체 정적 저장소 먼저 (`tools/build_repo.py` → `dist/repo/index.json`)
  → extensions.blender.org 제출; exe 선택 (초안 `tools/installer/`, 컴파일·서명 안 함); 유료는 별도 상품; 포터블 묶음 안 함. 사용자 결정 대기:
  이름·id (Autodesk 지침상 제품 이름에 "Maya" 금지), 무료/유료, 계정·공개 이메일, 바이너리 CC0, exe 서명. 왕복 검증: release_check 11 PASS,
  `tools/repo_check.py` 10/10 (설치·업데이트 0.1.0→0.1.1·Remove), `tools/installer_check.py` 9/9, 헤드리스 486/486.
  **바로 다음 할 일**: step 62 Set Driven Key·포즈 모드 제약·Add Attribute·Blend Shape (근거 `research/maya/workflows/rigging.md` 후보 D).

- Step 60 (Maya ⇄ Blender 스위치·완전 되돌리기, 사용자 요청 2026-10-18) 완료 — `docs/steps/step_60.md`. 확장은 켜진 채 「Maya 모드」 =
  MODE 하위 패키지 register/unregister (`switch.py`, 재시작 없음). 전환: 상단 바 오른쪽 「Maya | Blender」 (두 모드), 환경설정 맨 위 스위치·
  「Restore Blender Settings」, Edit 「Switch to Maya Mode」 / Windows 「Switch to Blender」 (F3), Ctrl+Alt+Shift+M. 켜기 = 스냅숏
  (`switch_snapshot.json`) + 템플릿 레이아웃을 "Maya" 워크스페이스로, 끄기 = 이전 워크스페이스·스냅숏 복원 (아직 Maya 값인 것만).
  Maya 테마 표시 = 테마 이름 "Maya" (filepath 아님: 확장 Remove 가 filepath 파일이 사라지면 테마를 리셋, `bl_extension_ops.py:1233-1270`).
  헤드리스 482/482, GUI 0.8 410/410, release_check 전부 PASS, dogfood 47/47. 남은 것: 명령줄 `extension remove` 는 복원 불가 (안내 필요).
  **바로 다음 할 일**: step 61 배포 방식 조사 (공개는 안 함; 명령줄 Remove 안내 포함), 그다음 62 Set Driven Key …

- Step 59 (피벗 개념·스냅 전부·Maya 모양 매니퓰레이터, 사용자 요청 2026-10-18) 완료 — `docs/steps/step_59.md`, Maya 실측
  `research/maya/workflows/pivot_snap.md`. D / Insert = 피벗만 (Translate·형상·자식 불변, 피벗 회전 = 「Maya Pivot」 방향), Reset / Bake /
  Match Pivots, 오브젝트 = lead 피벗·컴포넌트 = bbox 중심, X/C/V/J = 매니퓰레이터 중심 스냅 (X 절대 그리드), Step Snap, Snap Align Objects,
  Snap Together Tool, Make Live (+ Status Line 칸), Move/Scale = Maya 모양 Python 기즈모 (Rotate 는 C 링 유지), Tool Settings 「Move Settings」,
  W/E/R 메뉴 = 툴별 축 슬롯. 헤드리스 478/478, GUI 399/399 (0.8; 1.25 는 step 37/51/9 기존 실패 — step 59 와 무관, 문서 참고), dogfood 47/47.
  **바로 다음 할 일**: step 60 「켜고 끄는 스위치·완전 되돌리기」 (사용자 요청 2026-10-18: 언제든지 Maya 모드로 / 원래로; 기존
  `maya_kit.make_maya` / `revert_maya` (`src/maya_kit/first_start.py`) 확인부터. step 59 가 바꾼 것 — 툴 위젯 교체, 템플릿 툴 기본값,
  pivot 감시자 — 도 되돌리기 대상). 그다음 61 배포 방식 조사 (공개는 안 함), 62 Set Driven Key·포즈 모드 제약·Add Attribute·Blend Shape
  (근거 `research/maya/workflows/rigging.md` 후보 D), 63 MTK 도크 … 70 Graph Editor (PLAN 표 번호를 3 씩 뒤로 미룸).

- Step 58 (IK Handle·Bind Skin·Paint Skin Weights·가중치 복사/미러) 완료 — `docs/steps/step_58.md`. `maya_kit.ik_handle` (시작·끝 조인트
  클릭 또는 두 조인트 선택 → 끝 조인트로 들어오는 본에 IK + chain_count, 목표 `ikHandleN`), Pole Vector (자세 유지 각), Bind Skin (순서 무관,
  메시 부모 안 됨, Max Influences, Selected Joints), Unbind, Paint Skin Weights (웨이트 페인트 + 아마추어 자동 포즈, 도크 맨 위 Influences 목록·
  Replace/Add/Scale/Smooth·Value·Flood), Copy / Mirror Skin Weights (반사 위치로 조인트 짝), Copy / Paste Vertex Weights.
  헤드리스 462/462, GUI 384/384 (0.8) · 383/383 (1.25), dogfood 47/47.
  **바로 다음 할 일**: step 59 「Set Driven Key·포즈 모드 제약·Add Attribute·Blend Shape」 (근거 `research/maya/workflows/rigging.md`
  후보 D). 그다음 60 … 67.

- Step 57 (Joint Tool·Orient/Mirror Joint·포즈 픽워크) 완료 — `docs/steps/step_57.md`. Skeleton > Create Joints / 셸프 = `maya_kit.joint_tool`
  (클릭마다 조인트, 정사영 = 원점 뷰 평면 / persp = 바닥, Enter → 포즈 모드, `skeleton1` / `jointN`, XYZ, CB lead = 마지막), Orient Joint /
  Mirror Joints = Maya 옵션 창 (`invoke_props_dialog`; Y 축 안내, 평면·Behavior·검색/치환), 포즈 모드 ↑↓←→ = 조인트 pick-walk, 포즈·아마추어
  편집 모드 P / Shift+P = 조인트 부모 지정 (제자리). 헤드리스 451/451, GUI 376/376 (0.8) · 375/375 (1.25), dogfood 47/47.

- Step 56 (Time Slider·키 감각) 완료 — `docs/steps/step_56.md`. 타임라인 LMB = 시간 (Shift = 빨간 범위, MMB = 시간 + 안내), RMB = Maya Time
  Slider 메뉴 (Cut/Copy/Paste/Delete/Snap/Keys/Tangents/Playback Speed/Looping/Set Range to/Playblast), K + 드래그 = 어디서나 시간 (Mesh
  knife K 제거), S = 키 가능한 채널 전부 (`maya_kit.set_key`), Set Breakdown Key, Key > Delete Keys = 모든 키 (`keyframe_clear_v3d`),
  Cut/Copy/Paste Keys, CB 버튼 RMB 메뉴 맨 위 Key Selected 류. 헤드리스 442/442, GUI 365/365 (0.8) · 364/364 (1.25), dogfood 47/47.
  67 의 Graph Editor 탄젠트는 `operators/time_keys.TANGENTS` 재사용.

- Step 55 (포즈 본 = Maya 조인트: CB·Outliner·AE·제약 가중치) 완료 — `docs/steps/step_55.md`. 포즈 모드에서 CB lead/targets = 활성/선택
  본 (경로 `pose.bones["n"].…`, 키·브레이크다운·뮤트·잠금·숨김·Key Selected·`+=` 입력·MMB 슬라이더가 본에), 쿼터니언 본 「Rotate Order
  XYZ」, 편집 모드 「Placing joints」, Ctrl+Tab 포즈 모드; INPUTS 제약 노드 `joint2_pointConstraint1` + `locator1W0` = influence, 제약
  채널 파랑 (눌린 버튼); kit Outliner JOINT 행 (클릭 = 포즈 모드 + 본); AE joint 탭 + 제약 탭. 헤드리스 430/430, GUI 356/356 (0.8) ·
  355/355 (1.25), dogfood 47/47.

- Step 54 (워크플로우 기반: 단위 생성 경로·조명·안내) 완료 — `docs/steps/step_54.md`. Create Joints / Type / Free Image Plane /
  필드 8 개 / 3D Container·Fire·Smoke 가 Maya 단위 (`create.KINDS`, `maya_kit.quick_smoke`), 조명 × maya_unit², 「Blender 에 없음」 안내 체계
  `ui/notices.py` (26 경로, 툴팁 + Help Line). 헤드리스 420/420, GUI 342/342 · 341/341, dogfood 47/47.
- Step 53 (Blender 5.x 호환·안전한 설치) 완료 — `docs/steps/step_53.md`. 대상 4.5 그대로, 매니페스트 `blender_version_max = "5.3.0"`.
  5.2.2 에서 처음엔 켜기 실패 (Timeline = Dope Sheet 모드) → 얇은 버전 분기 (time_slider, theme `_rna_xml` + MOVED, keymap STRICT/DRIFT,
  select_loops, 5.x 타임라인 버튼 위치). 헤드리스 4.5 / 5.0.1 / 5.1.2 / 5.2.2 모두 414/414, GUI 4.5 337/337 · 336/336, 5.2 337/337,
  다른 에디터 GUI 9/9 (두 버전), release_check: 설치가 사용자 애드온·테마·설정을 지키고 kit 을 끄면 전부 원래대로 (8 단언, 4.5·5.2),
  dogfood 47/47.
- Step 52 (핫박스·RMB 충실도) 완료 — `docs/steps/step_52.md`. 핫박스 = Maya 8 줄 (공통 + Cache/Help, 패널 메뉴, Recent | Maya | Controls,
  메뉴 세트 5 줄, Show All 기본), 대각 영역선, 영역 이름·어둡게 하기 없음; 마킹 메뉴·핫박스가 창 전체에 그려짐 (사이드바·타임라인 위);
  RMB 목록 = Maya 2022 순서 (「pCube1...」 → AE, Select All/Deselect All/Invert, Select Similar □, 회색 ▸ 9 개), 링 아래 (넘치면 열 나눔);
  버그: Segoe UI 에 ▸ 가 없어 목록 폭이 수백만 px (step 41 부터) → 화살표 삼각형. 헤드리스 407/407, GUI 328/328 · 327/327,
  픽셀 ΔE>5 5/31 (메뉴 3 지점 0.3), dogfood 47/47, release_check PASS.
- Step 51 (메뉴 옵션 박스·셸프 줄) 완료 — `docs/steps/step_51.md`. Maya 옵션 박스 494 항목 = 창 아이콘 + 길게 누르기 「Option Box」
  (같은 줄 두 번째 버튼은 메뉴가 계단처럼 깨짐), 셸프 줄 64 px = 탭 줄 (머리, #373737 로 어둡게) + kit 제작 32 px 컬러 아이콘 줄
  (`ui/shelf_icons.py`, 이미지 편집기 POST_PIXEL + 기즈모 풀 고르기). 헤드리스 398/398, GUI 314/314 (0.8) · 313/313 (1.25),
  look_compare density 6/6 (셸프 64, 아이콘 32), rects 5/12, 셸프 픽셀 4 지점 ΔE ≤ 2.4, dogfood 47/47, release_check PASS.
  후속: Status Line 그룹 접기 손잡이 (Maya openBar, `maya_kit.status_group`) — 헤드리스 399/399, GUI 316/316 · 315/315.
- Step 50 (에디터 크롬) 완료 — `docs/steps/step_50.md`. Channel Box: 패널 머리·톱니 대신 메뉴 줄 Channels/Edit/Object/Show, 상자 없는
  이름·SHAPES·INPUTS, Maya 빈 선택 문구; Layer Editor: Display/Anim 탭 + Layers/Options/Help; Outliner (Maya 식) 머리 = Display/Show/Help
  + 검색 (`ui/maya_outliner.py`), 눈 열 없음; Time Slider 오른쪽 (타임라인 사이드바) 현재 프레임 + 재생 버튼 8, 헤더 = Maya 순서 Range
  Slider (Blender 메뉴는 오른쪽 끝 설정 메뉴로). 헤드리스 392/392, GUI 309/309 (0.8; 1.25 고친 파일 다시 통과), 픽셀 ΔE>5 7 → 5/28,
  CB 행 16.0 px, dogfood 47/47.
- Step 49 (레이아웃 동등화) 완료 — `docs/steps/step_49.md`. MayaKit = Status Line 줄 / Shelf 줄 (헤더만 있는 두 영역) /
  [툴박스 열 (좁은 3D 뷰, Maya 툴만 그리기 필터, `ui/toolbox.py`) | Outliner 260 | 뷰 + 사이드바 도크 277] / Time Slider + 아래 Range
  Slider (헤더 뒤집음) / Help Line | Command Line 한 줄. 오른쪽 Outliner·Properties 열 없음 (AE = 도크, Render Settings = 새 창).
  사이드바 「Channel Box Dock Only」 (`ui/dock_tabs.py`, Item 의 C 패널은 남음). 생성기 `tools/make_startup.py` 는 이제 GUI Blender
  (헤드리스 area_close/join 불가). 헤드리스 385/385, GUI 307/307 (1.25·0.8), rects 1/12 → 4/12 (x/w 대부분 ✓, y 는 셸프 높이 = step 51).
  미해결 확인: step 42 사고로 사용자 실제 설정에서 node_wrangler 가 켜진 채 (사용자 확인 필요); step 40 의
  `research/scripts/maya_shots/shots.py` 는 화면 영역 캡처라 다시 돌리기 전에 위젯 캡처로 바꿀 것.
- Step 48 (Maya 고유 워크플로우 분석·계획) 완료 — `docs/steps/step_48.md`, `docs/PLAN.md` 「Maya 워크플로우 계획」, 결정 10
  (`docs/user_decisions.md`: 시뮬레이션 스케일 = Maya nucleus spaceScale 1 처럼). Maya 2022 를 실제로 띄워 7 분야 47 단계 기록
  (`research/scripts/maya_workflows/wf.py`, `research/maya/workflows/*.md` + shots, Maya 위젯만 찍음), 분야별 분석 7 개, blindspot 12 건,
  brainstorm (결정 8 개 delegated), 독립 검토 반영 (v2). backlog 14 개 → 단계 54–67 (큐의 49–53 뒤). 버그 수정: bevel exec 너비 Maya 단위.
  헤드리스 375/375, GUI step 18 14/14 (1.0·0.8), dogfood 47/47.
- Step 47 (선택 와이어) 완료 — `docs/steps/step_47.md`. `ui/selection_wire.py`: 선택 오브젝트의 평가된 엣지를 kit 이 직접 그림 (POST_VIEW,
  사용자 셰이더 + 깊이 바이어스, 오브젝트별 numpy 배치 캐시, 테마 리드/선택 색을 선형으로). Blender `show_wire` 는 선택 색을 테마 wire 쪽으로
  최대 19 % 섞어 (실측) 버림 — 그래서 ID 데이터에 아무것도 안 씀 (저장·언두 잔존 0). 템플릿 선택 외곽선 끔. viewport 10/12 (리드 0.2, 흰색 0.0),
  10 만 폴리 프레임 +3–14 %. 헤드리스 374/374, GUI 293/293 (1.0·0.8), dogfood 47/47.
- Step 46 (뷰 가구) 완료 — `docs/steps/step_46.md`. `ui/view_furniture.py`: ViewCube (Python 기즈모, 면 클릭 → view_axis, 평소 0.5,
  4 분할은 마우스가 있던 패널에만), 카메라 라벨 (persp / top −Z / front +Y / side −X, 카메라 이름), 축 삼각 (Blender 축) — Blender 내비 기즈모가
  꺼진 뷰에서; 템플릿은 내비 기즈모·텍스트 정보 끔. HUD 메뉴 Camera Names / View Axis / View Cube = 애드온 환경설정. look_compare
  `furniture.md` 3/3 ±10 px, 텍스트 오버레이 픽셀 0. 헤드리스 369/369, GUI 289/289 (1.0·0.8), dogfood 47/47.
- Step 45 (Maya 그리드) 완료 — `docs/steps/step_45.md`. 자체 GPU 그리드 `ui/maya_grid.py`: ±12 단위, 1 단위마다 1 px, 5 마다 2 px,
  축 2 px, 모두 테마 그리드 회색, 계단선, 깊이 검사. 바닥에만 (4 분할 front/side 는 그리드 없음 = Maya). 뷰별 상태 = Blender 바닥·정사영
  그리드 끔 + `overlay.grid_lines == 0` (delegated). Show > Grid / Display > Grid = `maya_kit.toggle_grid`. 템플릿 뷰 모두 켬.
  look_compare `grid.md`: 그리드선 200 점 ΔE00 0.7, 모서리 4/4 ±1 px. 그리기 0.22–0.27 ms. 헤드리스 362/362, GUI 283/283 (1.0·0.8),
  dogfood 47/47.
- Step 44 (Maya 위젯 감각) 완료 — `docs/steps/step_44.md`. 테마: 모든 위젯 각지고 평평 (roundness 0, shade·엠보스·메뉴 그림자 없음,
  panel_roundness 0). 환경설정 그룹 「Maya Density」 (`view.ui_scale` = 1 / OS 배율, 125 % 화면 → 0.8 = Maya 와 같은 픽셀), 「Maya Font」
  (Windows Segoe UI, 동봉 안 함), 「Aliased Wireframes」 — 백업/복원, Make Blender Maya 가 켬. CB 행 scale_y 0.8 (16 px). GUI 테스트
  `--ui-scale 0.8` + `sim.px()`. look_compare `density.md` 3/3 (메뉴바 26, 메뉴 항목 19.4, CB 행 16.0 px). 면 채움 α 재보정 0.28
  (step 43 기준 샷에 매니퓰레이터가 걸려 있었음). 헤드리스 356/356, GUI 1.0 281/281 · 0.8 281/281, dogfood 47/47.
  미해결 확인 (step 42): 사용자 실제 설정에서 node_wrangler 가 켜진 채 남음 (사용자 확인 필요).
- Step 43 (Maya 테마 v2 색) 완료 — `docs/steps/step_43.md`. 컴포넌트 (하늘색 와이어, 보라/연노랑 정점, 살구색 엣지·면 — 면은 Maya 점묘
  평균에 맞춘 알파), 매니퓰레이터 (Z = 실제로 그려지는 순파랑), Outliner (#373737, 리드 행 파랑, 이름 흰색), 탭, 현재 프레임 회색,
  3D 뷰 헤더·툴바·사이드바 불투명, 템플릿 빨강/초록 그리드 축선 끔, 프리셀렉트 빨강. 새 `viewport.md` (렌더 픽셀 10 요소).
  theme ΔE00 38/38 < 2, viewport 9/10 < 5, 헤드리스 349/349, GUI 281/281, dogfood 47/47.
- Step 42 (켜자마자 Maya) 완료 — `docs/steps/step_42.md`. 템플릿 `userpref.blend` 는 실측 후 기각 (템플릿 안에서 사용자 add-on 목록·테마·
  ui_scale 을 통째로 바꿈). 대신 첫 GUI 시작의 환영 대화상자 → 「Make Blender Maya」 1 번 = 레이아웃 설치·Maya 테마·스플래시 끔·
  다음부터 Maya 레이아웃으로 시작, 「Revert Maya Look」 으로 모두 되돌림 (`first_start.py`, 결정 3 개정 = user_decisions 9). 테마는 옵션 +
  끄면 복원. 버그 수정: 오퍼레이터 안 템플릿 전환이 Blender 를 죽이던 것 (layout_open 포함). kit 시작 화면 그림 `tools/make_splash.py`.
  뷰 배경 단색 #5c5c5c. 헤드리스 348/348, GUI 281/281, dogfood 47/47, look_compare 체크 9/9 (메뉴바·패널·뷰 배경 ΔE 0.0).
  **주의: 실험 중 사용자 실제 userpref.blend 를 덮어쓴 사고 — 3 값은 되돌렸고 node_wrangler 는 켜진 채 (step_42.md 「실측」).**
- Step 41 (비교 기준 정확화) 완료 — `docs/steps/step_41.md`. `tools/look_shots.py` 가 Maya 와 같은 카메라 (Maya f_px 973 px, pCube1 화면
  높이를 Maya 샷에 맞춘 거리)·같은 선택 상태·메뉴바에서 연 Create 메뉴로 찍고, `tools/look_compare.py` 가 `pixels.md` (렌더 픽셀 ΔE,
  kit 지점 = `tools/look_data.py` 앵커 표), `rects.md` (영역 ±10 px), `scene.md` (큐브 크기 ±10 %), `crop_*.png` 6장을 만든다.
  결과: 큐브 3/3 (−1.3 %), 픽셀 29 중 ΔE>5 9 + kit 에 없음 9, 사각형 12 중 1. 헤드리스 344/344.
- Step 40 (Maya 동일화 조사·계획) 완료 — `docs/steps/step_40.md`, `docs/PLAN.md` 「Maya 동일화 계획」. Maya 2022.4 를 팩토리 prefs 로 띄워
  스크린샷 22장 + 실측 색·크기 (`research/maya/colors.json`), kit 비교 도구 `tools/look_compare.py` (+ `look_shots.py`: 나란히 이미지,
  테마 ΔE00), 경쟁 제품 22개 (`research/competitors.md`), blindspot 18건, self-review 반영. 버그 수정: 리드(연두)/다른 선택(흰색)
  색이 반대였음 → ΔE 28.5 → 0. 테마 ΔE00>5 13/31 → 11/31. 헤드리스 339/339. backlog 12개 (`autodrive_bmk/backlog.json`).
- Step 39 (컴포넌트 픽워크 + Alt+Shift 축 고정) 완료 — `docs/steps/step_39.md`. 편집 모드 화살표 = `maya_kit.pick_walk_component`
  (엣지 루프/링, 정점·면은 화면 방향), Alt+Shift+LMB/MMB = `maya_kit.view_axis_lock` (처음 우세한 축으로 텀블/트랙).
  헤드리스 339/339, GUI 281/281, dogfood 47/47. **재점검 3차 backlog 7개 모두 처리 (step 33–39).**
- Step 38 (Channel Box 다중 선택·상대값, AE 재질 라벨) 완료 — `docs/steps/step_38.md`. CB 값 필드 = 텍스트 (Maya 숫자 표시,
  `+=5`/`*=2`, 모든 선택·고른 채널 모두), 사용자 속성/SHAPES/INPUTS 도 같은 이름 채널에 적용 (`Scene.maya_kit_cb.rows`),
  재질 `maya_kit_type` → AE `lambert: lambert1` + lambert/blinn/phong/surfaceShader 섹션. 헤드리스 333/333, GUI 277/277, dogfood 47/47.
  재점검 3차 backlog 7개 중 1–6 처리.
- Step 37 (뷰 패널 메뉴 바) 완료 — `docs/steps/step_37.md`. 3D 뷰 헤더 메뉴 = Maya View/Shading/Lighting/Show/Renderer/Panels
  (`ui/panel_menus.py`, `VIEW3D_MT_editor_menus.draw_collapsible` 덮어쓰기, Blender 메뉴는 「Blender ▸」, 환경설정 Panel Menus).
  매핑 67 / 회색 51. 헤드리스 322/322, GUI 272/272, dogfood 47/47. 재점검 3차 backlog 7개 중 1–5 처리.
- Step 36 (대칭 Symmetry) 완료 — `docs/steps/step_36.md`. 전역 Maya 대칭 상태 `Scene.maya_kit_symmetry` → 메시 `use_mirror_*`
  (`operators/symmetry.py`, 편집 모드 진입 시 적용 + 헤더 미러 버튼 역반영), Status Line 대칭 그룹 (토글 + ▾ Off/Object/World/Topology),
  Tool Settings 「Symmetry Settings」, W/E/R 홀드 N Symmetry ▸. 헤드리스 312/312, GUI 267/267, dogfood 47/47.
  재점검 3차 backlog (`C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_33.json`) 7개 중 1–4 처리.
- Step 35 (Maya 키 묶음) 완료 — `docs/steps/step_35.md`. Ctrl+Alt+LMB 박스 줌, Ctrl+T, Y (마지막 비 QWERT 툴), Ctrl+Shift+X/Q,
  F2–F6 메뉴 세트 (IC 3D 뷰 F2–F5 제거), 3D 뷰 Return 팝오버 제거. 키맵 대응표 구현 95 / 계획 0. 헤드리스 300/300, GUI 261/261, dogfood 47/47.
- Step 34 (메뉴 막다른 길) 완료 — `docs/steps/step_34.md`. `menu_map.CHILDREN` (Maya 가 실행 중에 만드는 하위 메뉴: Windows > ... Editors,
  HUD), 편집기는 새 창 (`maya_kit.open_editor`), Edit > Ungroup, UV Editor/Planar/Normal-Based, HUD Poly Count, Increment and Save
  (Maya 번호 규칙), Export Selection (선택만). 헤드리스 294/294, GUI 251/251, dogfood 47/47.
- Step 33 (메뉴가 화면 안에) 완료 — `docs/steps/step_33.md`. `engine.fit_ring`: 마킹 메뉴 중심(누른 점)은 그대로, 방사 상자는 안으로,
  목록은 링 아래/위/옆으로; 핫박스 행이 위로 넘치면 가운데 상자 아래로. 헤드리스 287/287, GUI 246/246, dogfood 47/47.
- Step 32 (재점검 3차) 완료 — `docs/steps/step_32.md`, `docs/PLAN.md` 「재점검 3차」. 코드(`src/`) 변경 없음. 헤드리스 281/281, dogfood 47/47,
  탐색 세션 15 중 13 (실패: 세션 bmesh 선택 탓 1, 박스 줌 미구현 1). 대응표 33행: 완료 25, 부분 6, 불가 2. 새 발견: RMB 루트 목록이 뷰 아래로 잘림,
  AE 재질 라벨이 모두 standardSurface, 메뉴 막다른 길 (Windows 편집기, UV, Ungroup, HUD, Increment and Save), 대칭 없음.
- Step 31 (레이아웃 다듬기) 완료 — `docs/steps/step_31.md`. MayaKit 템플릿 왼쪽 Outliner 폭 0.2 + 컬렉션 행·렌더 열 숨김 (Maya DAG),
  쿼드 → 단일 때 축 뷰 이름 유지 (`is_orthographic_side_view`), 홀드 메뉴 체크 켜짐 색 강조 + 파이 폴백 체크 아이콘, release 스크린샷 재생성.
  타임라인 프레임 상자 겹침은 C 그리기라 미해결. 헤드리스 281/281, GUI 239/239, dogfood 47/47. backlog.json 8 항목 모두 처리.
- Step 30 (선택 감각) 완료 — `docs/steps/step_30.md`. 편집 모드 박스/라쏘 = 가려진 요소까지 (드래그 동안만 X-Ray 플래그, `operators/marquee.py`),
  정점 모드 + 셀렉트 툴 프리셀렉트 하이라이트 (`operators/preselect.py`, C 기즈모 `GIZMO_GT_mesh_preselect_elem_3d`), 언두 256 단계
  (`prefs_preset.GROUPS["undo"]`, disable 시 복원, `tests/kit.py` 가 prefs.edit 스냅샷). 헤드리스 279/279, GUI 232/232, dogfood 47/47.
- Step 29 (Maya 식 재질 지정) 완료 — `docs/steps/step_29.md`. `operators/material.py`: Lighting/Shading Material Attributes /
  Assign New (검색 팝업, Shift+T) / Favorite ▸ / Existing ▸, RMB 목록 끝 같은 항목 (선택 없으면 커서 아래 오브젝트), 면 선택 모드 = 면에만,
  아니면 오브젝트 전체 (슬롯 1개). 엔진: 목록 하위 메뉴 영역 안으로, 클릭 모드 항목은 버튼을 뗄 때 실행. 헤드리스 274/274, GUI 218/218,
  dogfood 47/47.
- Step 28 (MMB = 마지막 핸들) 완료 — `docs/steps/step_28.md`. 기즈모 LMB 누름 감시 → 등록된 transform 의 제약을 툴별로 기억,
  Tool 키맵 MMB = `maya_kit.manip_mmb` (CB 슬라이더 우선), 같은 툴 키 재탭 = 리셋. 헤드리스 264/264, GUI 206/206, dogfood 47/47.
- Step 27 (매니퓰레이터 크기·뷰 키) 완료 — `docs/steps/step_27.md`. = / Shift+= / - gizmo_size (`prefs_preset.set_runtime`, disable 시 복원),
  PgUp/PgDn 스무스 단계, 0, Home (Maya persp), Alt+5 와이어프레임. 키맵 대응표 구현 87 / 계획 5 (F2–F6). 헤드리스 260/260, GUI 202/202,
  dogfood **47/47**.
- Step 26 (Smart Extrude) 완료 — `docs/steps/step_26.md`. 면/엣지 Shift+기즈모 드래그 = 압출 후 변환, 안 움직이면 (Shift+클릭·취소)
  사본/압출을 되돌림, xform 기즈모만 (`context.gizmo_group`), 홀드 메뉴 체크 상자. 헤드리스 256/256, GUI 195/195, dogfood 46/47.
- Step 25 (cm 그리드와 그리드 스냅) 완료 — `docs/steps/step_25.md`. 원인: Blender 원근 뷰는 1 m 아래 그리드 단계를 건너뜀 →
  `overlay.grid_scale` = 표시 단위의 미터 값 (`units.grid_scale`, 템플릿 0.01, Maya Units 적용/복원). X 스냅 템플릿 9 cm / Maya Units 9 cm /
  팩토리 3 m. 헤드리스 249/249, GUI 187/187, dogfood 46/47.
- Step 24 (컴포넌트 Delete) 완료 — `docs/steps/step_24.md`. 편집 모드 Delete / Backspace = `maya_kit.delete_components` (면 삭제,
  경계 아닌 엣지 dissolve + 정점 정리, 정점 dissolve, 메뉴 없음). Ctrl+Delete = IC dissolve. 헤드리스 246/246, GUI 179/179, dogfood 46/47.
- Step 23 (재점검 2차) 완료 — `docs/steps/step_23.md`, `docs/PLAN.md` 「재점검 2차」. 코드(`src/`) 변경 없음; `tools/dogfood.py --session`.
  헤드리스 239/239, GUI 172/172, dogfood 46/47, 탐색 세션 13 중 12 (면 Delete 가 메뉴), 콘솔 오류 0.
  대응표 33행: 완료 23, 부분 8, 미착수 0, 불가 2 (1차 21/8/2/2). 키맵 468행: 구현 79 + IC 6, 계획 13, 미검토 292.
  새 발견: 컴포넌트 Delete, cm 템플릿 그리드 안 보임 + X 스냅 0 cm, Outliner 이름 잘림; blindspot 8건 (MMB 마지막 핸들, 재질 지정 등).
- Step 22 (매니퓰레이터 Shift+드래그 = Smart Duplicate) 완료 — `docs/steps/step_22.md`. Maya 키컨피그의 기즈모 키맵
  (`Generic Gizmo Maybe Drag` / `Drag`) 맨 앞 Shift+LMB PRESS → `maya_kit.manip_duplicate` (복제 후 PASS_THROUGH → 기즈모가 사본 변환).
  Shift 정밀은 그대로 (실측: 누른 채 시작한 드래그는 정밀 아님). W/E/R 홀드 메뉴 Smart Duplicate = 환경설정 토글.
  헤드리스 239/239, GUI 172/172, dogfood 47 중 46 (남은 실패: `=`).
- Step 21 (생성 경로 단위 통일) 완료 — `docs/steps/step_21.md`, 결정 8 (`docs/user_decisions.md`). Maya 길이 1 = 씬 표시 단위 1
  (`operators/units.maya_unit()`): Create/셸프/메뉴/마킹 메뉴/핫박스/Ctrl+G/`cmds` 가 같은 크기, Maya FBX 임포트 크기와도 같음.
  MayaKit 템플릿 pCube1 = 0.01 BU = "1 cm", 템플릿 3D 뷰 = Maya persp (28, 21, 28 cm) + 클립 0.1 / 10000 cm; Maya Units 켬 = 1 BU = "1 cm".
  헤드리스 235/235, GUI 162/162, dogfood 47 중 46 (남은 실패: `=`).
- Step 20 (타임라인) 완료 — `docs/steps/step_20.md`. `.` `,` = 다음/이전 키, Alt+`.` Alt+`,` = 프레임 (Frames 키맵, 3D View 피벗/방향 파이 제거),
  타임라인 헤더 = Maya Time Slider 버튼 + Range Slider 4 필드, 타임라인 뷰가 재생 범위를 따라감, MayaKit 템플릿 애니메이션 1–200 / 재생 1–120.
  헤드리스 227/227, GUI 156/156, dogfood 47 중 46 (남은 실패: `=`).
- Step 19 (복제 이름) 완료 — `docs/steps/step_19.md`. Ctrl+D = `maya_kit.duplicate` (제자리, 하위 계층, pCube2 / pCubeShape2, group1 → group2,
  Shift+D 스마트 반복과 연결); 메뉴 Edit > Duplicate 도 같음. 헤드리스 223/223, GUI 147/147, dogfood 45 중 43 (남은 실패: `.`, `=`).
- Step 18 (편집 모드 키) 완료 — `docs/steps/step_18.md`. Mesh: D = 컴포넌트 피벗 홀드(3D 커서, 놓으면 유지 / 탭 = 리셋),
  Ctrl+Shift+A 전체 선택, Alt+D 해제 + 오브젝트 모드, Ctrl+E 즉시 압출, Ctrl+B 즉시 베벨(정점 모드 = 정점), Shift+> / < 확장·축소,
  Ctrl+F9–F11 닿는 요소로 변환 (`maya_kit.convert_selection`). 헤드리스 218/218, GUI 147/147, dogfood 45 중 42 (남은 실패: Ctrl+D 이름, `.`, `=`).
- Step 17 (Maya 프레이밍 여백 + 핫박스 잘림) 완료 — `docs/steps/step_17.md`. F/A/Shift+F/Shift+A/Ctrl+Shift+F 가 보이는 영역(사이드바·툴바·
  투명 헤더 제외)의 0.95 에 경계 상자를 맞춤 (`operators/framing.py`, `maya_kit.frame`); 핫박스 행은 보이는 영역 안으로 밀고 긴 행은 줄바꿈.
  헤드리스 211/211, GUI 133/133, dogfood 45 중 41 (남은 실패: Ctrl+D 이름, `.`, `=`, Shift+>).
- Step 16 (언두·가시성·아이솔레이트 키) 완료 — `docs/steps/step_16.md`. z/Shift+Z/Ctrl+Y (Screen, border 4개 제거), h·Ctrl+H·Alt+H·
  Shift+H·Ctrl+Shift+H (`maya_kit.visibility`, 오브젝트 모드; Mesh 는 hide/reveal), Ctrl+1 아이솔레이트(카메라 고정), Ctrl+Shift+I 반전.
  헤드리스 203/203, GUI 127/127, dogfood 45 중 41 (남은 실패: Ctrl+D 이름, `.`, `=`, Shift+>). 키맵 대응표 구현 51→63.
- Step 15 (스무스 프리뷰 = 표시 전용) 완료 — `docs/steps/step_15.md`. 3 이 Set Shade Smooth 노드 모디파이어 + 프리뷰 Subsurf(마지막)로
  매끈하게 보이고 메시 데이터는 그대로; Delete History 는 프리뷰를 굽지 않음; 1/2/3 은 사용자 Subsurf 를 건드리지 않음; INPUTS/AE 탭에서 숨김.
  헤드리스 196/196, GUI 115/115, dogfood 45 중 37 통과 (실패 8 = backlog 2·5 의 키·이름).
- Step 14 (재점검 1차) 완료 — `docs/steps/step_14.md`, `docs/PLAN.md` 「재점검 1차」. 코드(`src/`) 변경 없음.
  헤드리스 188/188, GUI 115/115. 새 도구 `tools/dogfood.py` (깨끗한 설치 + Maya 사용자 첫 세션 이벤트 재생):
  체크 43개 중 35 통과, 실패 8 = 아직 없는 Maya 키(z, Shift+Z, h, Ctrl+1, `.`, `=`, Shift+>) + Ctrl+D 이름 `pCube1.001`; 콘솔 오류 0.
- 구현률 (research 대응표 33행): 완료 21, 부분 8, 미착수 2, 불가 2. 키맵 468행: 구현 51 + IC 8, 계획 26, 미검토 306.
- 발견: PLAN 8행(M1-d 나머지 키 25개)이 번호 변경 때 빠져 미구현; blindspot 14건 (Delete History 가 스무스 프리뷰를 구움,
  생성 경로 단위 100배 차이, 편집 모드 D/Ctrl+Shift+A 충돌, Shift+매니퓰레이터 복제 미계획 등).
- Step 13 (통합·배포) 완료 — release 0.1.0 (`c0f37b0`).

## 바로 다음 할 일

- 드라이버 큐 순서: backlog.json 의 Maya 워크플로우 55–67 (PLAN 「Maya 워크플로우 계획」 표: 54 기반 (단위·안내),
  55 포즈 본 CB, 56 Time Slider·키, 57 Joint Tool, 58 IK·스킨, 59 SDK·제약, 60 MTK, 61 Target Weld, 62 Extrude/In-View, 63 UV, 64 Hypershade,
  65 FX, 66 씬 관리, 67 Graph Editor). 각 단계 근거 = `research/maya/workflows/<분야>.md` (research/ 는 추적 안 함 — 지우지 말 것).
- Maya 를 다시 띄울 때: `research/scripts/maya_workflows/launch.ps1` (스크린샷은 Maya 위젯만; 화면 영역 캡처 금지 — step 48 사고).
- 검증은 `python tools/look_compare.py` (`delta_e.md`, `pixels.md`, `viewport.md`, `rects.md`, `density.md`, `grid.md`, `furniture.md`); 샷은 Maya 밀도 (실효 배율 1.0)
  로 찍힌다. GUI 테스트는 두 배율로: `python tests/gui/run.py` 와 `--ui-scale 0.8` (새 고정 픽셀 좌표는 `sim.px()`).
- Blender 를 손으로 띄울 때는 `BLENDER_USER_*` 폴더를 먼저 만들 것 (CLAUDE.md, step 42 사고).
- 외형 검증: `python tools/look_compare.py` (Maya 자료 다시 찍기: `research/scripts/maya_shots/launch.ps1` → `mayapy research/scripts/maya_colors.py`).
- 이전 남은 항목: step_36–39 「남은 것」, PLAN 「재점검 3차」 8–9, step_49 「남은 것」 (Item 탭, AE 460), step_51 「남은 것」 (다른 배율의 셸프 줄 높이, Status Line 아이콘은 Blender 것), step_50 「남은 것」 (Outliner 카메라 행, 목록 바탕색).
