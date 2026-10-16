# HANDOFF

## 현재 작업

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

- 재점검 3차 backlog 남은 3개: Step 37 뷰 패널 메뉴 바 (View/Shading/Lighting/Show/Renderer/Panels), 38 Channel Box 다중 선택·상대값
  + AE 재질 라벨, 39 컴포넌트 픽워크 + Alt+Shift 축 고정. 대칭 남은 것 (클릭 시 반대쪽 하이라이트, HUD) 은 step_36.md 「남은 것」.
- 각 수정 후 `python tools/dogfood.py` (필요하면 `--session`) 로 회귀 확인.
