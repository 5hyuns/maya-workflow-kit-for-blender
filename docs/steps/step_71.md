# Step 71 — 재점검 4차

## 계획 (delegated)

1. 전체 헤드리스 테스트 + 깨끗한 설정 설치 dogfood (기본 47 항목) + 탐색 세션 `tmp/audit4_session.py` (일회성, 저장소 밖).
   세션은 step 33–70 에서 생긴 것을 실제 키·마우스로 누른다: Ctrl+D / Ctrl+G / z, S 키, 1/3 스무스 프리뷰, F3 메뉴 세트,
   Shift+RMB 마킹 메뉴, Space 핫박스, Ctrl+Alt+LMB 박스 줌, F11 + Ctrl+E 압출 (In-View Editor), 면 픽워크, Hypershade 창.
   스크린샷은 직접 확인한다.
2. research 대응표·PLAN·step 33–70 「남은 것」·manual_checks·keymap_mapping 수집 + blindspot. 읽기 전용 서브에이전트 1개,
   "없다" 주장은 직접 grep 으로 재확인.
3. PLAN 「재점검 4차」, HANDOFF, backlog (5–8개, Maya 사용자가 매일 체감하는 것 우선) → `hermes/autodrive_bmk/backlog.json`.

## 한 것

- 탐색 세션 `tmp/audit4_session.py` (저장소 밖), `python tools/dogfood.py --session tmp/audit4_session.py`.
- 수집 (읽기 전용 서브에이전트) + grep 재확인 → `docs/PLAN.md` 「재점검 4차」: 대응표 27/4/0/2 (82 %), 키맵 구현 113 · IC 10 ·
  미검토 267, manual_checks 287 열림 (체크 0), 3차 backlog 종결 여부, 새 발견, blindspot, 우선순위.
- 다음 할 일 8개 → `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` (PLAN 「재점검 4차」 우선순위 1–8 과 같음).

## 검증

- 헤드리스 `python tests/run.py`: **574/574** (66 파일).
- GUI `python tests/gui/run.py` (기본 UI 배율): **483/483** (54 파일). 알려진 간헐 실패 gui_step26 은 이번엔 통과.
- `python tools/dogfood.py`: **47/47**, 콘솔 오류/경고 0.
- 탐색 세션: **15 중 14**, 콘솔 0.
  - 통과: 클릭 선택, Ctrl+D → pCube2, Ctrl+G → group1, z 두 번 = 그룹·복제 취소, S = 10 채널 키 (CB 붉은 칸, Help Line "Key: 10 channel(s)"),
    3 = 스무스 프리뷰, F3 → riggingMenuSet, Shift+RMB 마킹 메뉴, Space 핫박스, Ctrl+Alt+LMB 박스 줌 (거리 0.448 → 0.082),
    F11 면 모드, Ctrl+E = 면 6 → 10 + polyExtrudeFace1 In-View Editor + CB INPUTS, → 화살표 면 픽워크, Hypershade 새 창.
  - 실패 1 (세션 탓): "1 = 모디파이어 없음" 확인이 틀렸다. 1 은 프리뷰 모디파이어를 숨기고 레벨을 지킨다 (`operators/display.py:131-137`, 설계대로).
- 화면에서 본 것 (스크린샷 직접 확인):
  - **F3 뒤에도 상단 메뉴 바가 "Modeling"** (`a4_05_menuset_f3.png`, 0.8 초 뒤). `maya_kit.menu_set` 이 `window.screen.areas` 만
    다시 그리는데 상단 바는 전역 영역. gui_step35 는 찍기 전에 상단 바를 호버해서 이 문제를 가렸다.
  - **타임 슬라이더에 키 틱 없음**: 1·12 프레임 키가 눈금자에 안 보임 (`a4_03_keys_timeline.png`).
  - F 프레이밍이 꽉 차 보이는 것은 Maya fit 0.95 (research/maya/interaction.md:196) 그대로라 버그 아님.
  - 레이아웃·Channel Box·Outliner (group1 계층)·핫박스·Shift+RMB 메뉴는 의도대로.

## 남은 것

- `docs/PLAN.md` 「재점검 4차」 우선순위 1–8 (backlog.json) 과 9 (나중 후보).
- step 33–70 「남은 것」 모음 (영역별, ★ = 매일 체감):
  - 모델링: ★ 편집 모드 Insert, ★ 프리셀렉트 정점만, Bevel/Bridge 히스토리 없음 (step_65.md:104), Multi-Cut Shift 50 % 만 (step_64.md:138),
    Target Weld 가림 검사 (:140), Mirror 옵션 (step_63.md:107), 소프트 선택 색 (:105), Quad Draw Make Live, Nonlinear Bend/Flare.
  - UV: ★ 3D Cut and Sew (x/s/d), UV 표시 키 4–9, checker, Straighten, Create UV Shell (step_66.md:104-106).
  - 애니메이션: ★ Graph Editor 1/2/3 · Insert Key 툴 · L/H/J (step_70.md:77), ★ Range Slider 드래그 (step_50.md:67), Shift 범위 키 이동
    (step_56.md:113), Maya Animation/Rigging/UV 워크스페이스, 버퍼 커브, 고스팅, Time Editor.
  - 리깅: Joint Tool 옵션·Backspace (step_57.md:89), Spline IK, Component Editor, Hammer weights (step_58.md:104), IK 솔버 (:106),
    Maintain Offset (step_62.md:117), Shape Editor (:120), 다중 타깃 블렌드 (step_55.md:128).
  - FX: 3D 유체, MASH, Bifrost, nConstraint, nHair (step_68.md:87), 필드 연결 (:86), 파티클 vs Passive 콜라이더 (:85).
  - 렌더: Hypershade Textures/Utilities/Lights 탭, 스와치 드래그 (step_67.md:80), Light Editor 창 재로드 (:81), 960×540, Light Linking, Tab 노드 (:83).
  - 씬: Import/텍스처 창 sourceimages (step_69.md:72), Reference Unload/Replace (:73), Recent Increments, Namespace Editor, Outliner Sets (:74).
  - UI: ★ Status Line 입력 줄, 「Not in Blender」 안내가 셸프·마킹 메뉴·핫박스에 없음 (step_54.md:77), 셸프 재정렬 (step_51.md:84),
    다른 UI 배율에서 셸프 줄 (:76), ViewCube 모서리·드래그 (step_46.md:78), Maya 모양 회전 매니퓰레이터 (step_59.md:159), 피벗 RMB 메뉴 (:157),
    비선택 와이어 ΔE 5.8 (step_44.md:73), 셰이딩 밝기 (step_43.md:81), Layer Editor 배경 (step_50.md:66), 좁은 뷰 헤더 잘림 (step_37.md:100).
  - 키맵: Shift+M / Ctrl+Shift+M (step_37.md:106), Ctrl+PgUp/PgDn (step_39.md:88), Y 는 3D View 툴만 (step_35.md:60), 미검토 267 행.
  - 인프라: 5.x GUI 실행 안 함 (step_53.md:84), 5.x PoseBone.select (step_55.md:133), `.iss` 설치기 컴파일 안 함 (step_61.md:50),
    배포 결정 11 대기, [U] 측정 (Increment 결과, 천 낙하 시간, 조명 세기).
- manual_checks 287 항목: 손 검증 한 번도 안 함 — 가장 큰 미검증 영역.
