# Step 65 — Extrude 매니퓰레이터 · In-View Editor · 마지막 연산 INPUTS (히스토리 대체)

근거: `research/maya/workflows/modeling.md` §1 A3·A4 (:19-26), 킷 현황 (:83-90), 갭 표 (A4 히스토리 사후 수정 20 :145, A3 Ctrl+E 15 :149),
§4 결정 (:175-176), §5 후보 4 (:227-236); Maya 샷 `shots/modeling_03.png` (polyExtrudeFace1 In-View Editor: Thickness · Local Translate Z ·
Offset · Divisions · Keep Faces Together, 압출 매니퓰레이터), `modeling_04.png` (INPUTS 에서 Local Translate Z 0.5 / Divisions 2 → In-View 도
같은 값); `docs/PLAN.md` W2 (:343-345), C 변환 기즈모는 확장 불가 (PLAN.md:10, step 59).

## 계획

### 실측 (Maya 2022.4 mayapy, `tmp/maya65/probe.py`, 큐브 1 × 1 × 1, 윗면 f[1], +X 면 f[4])

| 경우 | 정점 / 면 | 결과 |
|---|---|---|
| 기본 (`polyExtrudeFacet`) | 12 / 10 | 길이 0 압출 (윗면 정점이 제자리에 복제). 기본값 thickness 0, localTranslateZ 0, offset 0, divisions 1, keepFacesTogether on |
| localTranslateZ 0.5 | 12 / 10 | 윗면 y 0.5 → 1.0 |
| thickness 0.5 | 12 / 10 | 같음 (면 하나면 법선 이동) |
| offset 0.1 | 12 / 10 | 윗면 모서리 ±0.5 → ±0.4 (면이 안쪽으로 줄어듦, 새 면 없음) |
| divisions 2 + ltz 0.5 | 16 / 14 | 옆면 중간 고리 y 0.75 |
| 두 면 (윗면 + +X) together, thickness 0.5 | 14 / 12 | 공유 엣지 정점 (0.5, 0.5) → (1.0, 1.0): 각 면 평면이 0.5 씩 (shell 두께) |
| 두 면 apart, thickness 0.5 | 16 / 14 | 면마다 따로 압출 |
| 두 면 together, ltz 0.5 | 14 / 12 | 공유 정점 → (0.75, 0.75): 면마다의 법선 이동의 평균 |

### 1. `maya_kit.extrude` = polyExtrudeFace (delegated)

- 순수 bmesh 함수 `operators/extrude.py` `extrude(bm, faces, thickness, ltz, offset, divisions, together)`: 위상 = 길이 0 압출
  (`extrude_face_region` / together 끔이면 `extrude_discrete_faces`) 을 divisions 번 (두 번째부터는 뚜껑만 다시) → 층 k 정점 = 뚜껑 정점
  변위의 k / divisions. 변위는 원래 면에서 계산: Local Translate Z = 붙은 선택 면 법선의 평균 × ltz, Thickness = 각 면 평면이 thickness 만큼
  (면 1 개 = 법선, 2 개 = (n1+n2)/(1+n1·n2), 그 이상 = 평균 방향 / 평균 cos), Offset = 뚜껑 경계 정점을 면 안쪽으로 (두 경계 엣지의 안쪽
  수직 p_a, p_b → (p_a+p_b)/(1+p_a·p_b) × offset). 위치가 세 값에 대해 선형이라 정점마다 (P0, T, L, O) 를 남겨 값만 바뀔 때는 위치만 다시 씀
  (빠른 길). 길이 값 = Maya 값 × `units.maya_unit()` (결정 8). 뚜껑 면 선택.
- 연산자 (REGISTER, UNDO): Maya 이름 속성 Thickness · Local Translate Z · Offset · Divisions · Keep Faces Together. 면이 선택돼 있지 않으면
  지금처럼 `view3d.edit_mesh_extrude_move_normal` (엣지·정점 압출 드래그). Ctrl+E · Edit Mesh > Extrude · 마킹 메뉴 Extrude Face · 셸프
  PolyExtrude · MTK Extrude 가 이것 (Maya 처럼 바로 길이 0 압출 + 매니퓰레이터; 이제 드래그 모달 없음).

### 2. 기록 = 「마지막 kit 모델링 연산」 (W2, delegated)

- 오브젝트마다 `Record`: 노드 이름 `polyExtrudeFaceN` (장면 ID 속성 카운터, Maya 처럼 장면 전체 번호), 압출 전 상태 (`BMesh.copy()`), 지금
  값, 정점별 (P0, T, L, O), 상태 목록 (값, 서명 = 정점·면 수 + 뚜껑 정점 번호·좌표). 메시가 상태 목록의 하나와 같을 때만 유효 →
  Ctrl+Z / Ctrl+Shift+Z 로 그 상태의 값으로 돌아가고, 다른 편집 (정점 이동, 다른 연산) 이나 압출 전까지의 언두면 사라짐 (Maya 의 「마지막
  하나만」 대체). 파일 열기·확장 끄기 = 지움.
- 값 바꾸기 = `maya_kit.extrude_edit` (REGISTER, UNDO, 라벨 polyExtrudeFace): 압출 전 상태로 bmesh 를 되돌리고 (`bm.clear` + `from_mesh`)
  새 값으로 다시 실행 → 언두 한 단계, Adjust Last Operation (F9) 에 같은 Maya 이름 속성 (= In-View 폴백). redo 도 압출 전 상태에서 다시
  만들므로 몇 단계를 되돌리든 결과가 같음. F9 로 `maya_kit.extrude` 를 고치면 (압출 전 상태와 서명이 같으면) 노드 이름을 다시 씀.
- 끄는 경로 (In-View 드래그, 매니퓰레이터 드래그) 는 킷 모달 (UNDO 없음) 이 빠른 길로 위치만 바꾸고 놓을 때 `extrude_edit` 한 번 (중첩
  호출이지만 바깥 모달에 UNDO 가 없어 언두가 쌓임 — step 26 함정 회피). Channel Box 입력은 WindowManager 프록시 (UI 편집이 언두를 쌓지 않음,
  CLAUDE.md step 38) 의 setter 가 `extrude_edit` 호출 → 한 단계.

### 3. 매니퓰레이터 (Python GizmoGroup, delegated)

- `ui/in_view.py` `MAYAKIT_GGT_extrude` (3D): 뚜껑 중심에 법선 방향 파란 화살표 (`GIZMO_GT_arrow_3d`, 화면 크기 고정) → 누르면
  `maya_kit.extrude_drag` 모달 (뷰 광선과 법선 축의 최근접점 → Local Translate Z, 놓기 = extrude_edit, ESC/RMB = 원래 값). Maya 의 로컬
  X/Y 이동·스케일·회전 핸들은 남은 것. 보이는 동안 킷 Move/Scale 매니퓰레이터 (step 59) 는 숨김 (Maya 도 압출 매니퓰레이터로 바뀜).
- 보이는 조건: 기록이 유효 + 지금 면 선택 = 뚜껑 면 (다른 것을 고르면 사라지고 Move 매니퓰레이터가 돌아옴).

### 4. In-View Editor (GPU 상자, delegated)

- 같은 조건에서 3D 뷰 WINDOW POST_PIXEL 핸들러가 뚜껑 중심 화면점 오른쪽 아래에 상자 (제목 = 노드 이름, 다섯 행, Maya 어두운 반투명 바탕,
  행 16 px × UI 배율, 마지막에 드래그한 행 / 호버 행 이름 노랑 — modeling_03). 그리기는 핸들러, 고르기는 2D 기즈모 (step 51 선반 방식:
  `test_select` 만, `target_set_operator`): 행을 누르고 가로로 끌면 값 (실수 0.01 / px, Divisions 20 px 마다 1, Ctrl ×0.1, Shift ×10),
  안 끌고 놓으면 그 값만 입력하는 작은 창 (`invoke_props_dialog`), Keep Faces Together 는 클릭 = 토글. 실패 시 폴백 = F9 패널 (위).

### 5. Channel Box INPUTS

- 리드 오브젝트에 유효한 기록이 있으면 INPUTS 맨 위 (Maya 는 최근 노드가 위) 에 `polyExtrudeFace1` + 다섯 행 (텍스트 프록시, `+=` 입력 그대로),
  그 아래 회색 안내 "Edit-mode operations have no history in Blender: only the last one can be changed here." (PLAN W2). 모디파이어는 그
  아래 그대로.

### 5. 검증

- 헤드리스 `test_step65_extrude.py`: 순수 함수가 Maya 실측 8 경우와 같음 (정점·면 수, 좌표, Y-up → Blender Z-up), 빠른 길 = 다시 실행과 같음,
  연산자 (면 없음 = 폴백 poll, 노드 이름·카운터, Maya 단위 cm 템플릿 값), extrude_edit (Divisions 2 → 16 / 14, 값 기억), 상태 서명 (언두
  흉내: 메시를 이전 상태로 되돌리면 그 값, 다른 편집이면 무효), CB 프록시 (`0.5`, `+=0.5`), In-View 레이아웃 함수, 키·메뉴·마킹 메뉴·셸프·MTK.
- GUI `gui_step65_extrude.py` (modeling_03·04): 면 선택 → Ctrl+E → In-View 상자·화살표 (샷 vs modeling_03) → Thickness 행 가로 드래그 →
  0.5 → 윗면 높이 → Channel Box INPUTS polyExtrudeFace1 Divisions 에 2 입력 → 정점 16 → Ctrl+Z → Divisions 1 (값도 되돌아감) → 화살표
  드래그 → Local Translate Z 변함.
- `docs/manual_checks.md`, dogfood (Ctrl+E 기대 바뀜: 모달 대신 polyExtrudeFace 노드).

## 한 것

- **`maya_kit.extrude`** (`operators/extrude.py`): 순수 bmesh `extrude()` — 길이 0 압출을 Divisions 번 (together = `extrude_face_region`,
  끔 = `extrude_discrete_faces`; 따로 떨어진 영역에 남는 원래 면은 지움 = Maya 처럼 바닥 없음), 변위 (T, L, O) 를 원래 면에서 계산해 층마다 k/n.
  Maya 실측 8 경우와 좌표까지 같음. Ctrl+E · Edit Mesh > Extrude · Shift+RMB 면 Extrude Face · 셸프 PolyExtrude · MTK Extrude 가 이것
  (step 63 의 `maya_kit.mtk_extrude` 는 없앰). 면이 없으면 Blender 압출 + 법선 드래그 (엣지/정점).
- **기록** (`Record`, `RECORDS`): 노드 이름 `polyExtrudeFaceN` (장면 ID 속성 카운터), 압출 전 `BMesh.copy()`, 값, 정점별 (P0, T, L, O), 상태 목록
  (값 + 서명). 메시가 상태 하나와 같을 때만 유효 (언두/리두는 그 상태의 값으로), mesh `session_uid` 로 같은 메시인지 확인, load_pre / 끄기에 지움.
  **`maya_kit.extrude_edit`** (라벨 polyExtrudeFace) = 압출 전 상태 복원 (`bm.clear` + `from_mesh`) + 새 값으로 다시 → 언두 한 단계, F9 패널 =
  Maya 이름 속성. `set_params` 는 `extrude_edit('EXEC_DEFAULT', True, ...)` — **파이썬 연산자 호출은 `undo=True` 를 주지 않으면 언두를 쌓지
  않음** (step 26 의 「중첩 호출은 언두 없음」 의 실제 이유). F9 로 `maya_kit.extrude` 를 고치면 같은 노드 이름.
- **매니퓰레이터** (`ui/in_view.py` `MAYAKIT_GGT_extrude`): 뚜껑 중심의 파란 `GIZMO_GT_arrow_3d` → `maya_kit.extrude_drag` (뷰 광선과 법선 축의
  최근접점 = Local Translate Z, 끄는 동안 빠른 길, 놓을 때 extrude_edit 한 번, ESC/RMB 되돌림). 보이는 동안 킷 Move/Scale 매니퓰레이터 숨김.
- **In-View Editor**: POST_PIXEL 상자 (제목 + 다섯 행, 호버/마지막 행 노랑), 2D 기즈모 5 개가 행을 고름 → `maya_kit.inview_drag` (옆으로 끌기
  0.01 / px, Divisions 20 px, Ctrl/Shift; 클릭 = `maya_kit.inview_type` 입력 창; Keep Faces Together = 토글).
- **Channel Box INPUTS**: 리드가 편집 중이고 기록이 유효하면 INPUTS 맨 위에 polyExtrudeFace1 + 다섯 텍스트 행 (WindowManager 프록시 →
  `set_params`, `+=` 입력) + 회색 안내 세 줄. 키맵 매핑 PolyExtrude 행 갱신.
- dogfood 의 Ctrl+E 기대를 「모달」 에서 「polyExtrudeFace 노드」 로 바꿈 (Maya 와 같게).

### 계획과 다르게 된 것 (delegated)

- Ctrl+E 뒤 바로 끄는 모달은 없어짐 (Maya 처럼 매니퓰레이터를 끌어야 함). 엣지/정점은 예전 그대로.
- Maya 매니퓰레이터의 로컬 X/Y 이동·스케일·회전 핸들과 polyExtrudeFace 의 localTranslate X/Y · localScale · localRotate 속성은 없음 (Z 화살표만).

## 남은 것

- 압출 외의 킷 모델링 연산 (Bevel = polyBevel, Bridge, Add Divisions …) 은 아직 기록하지 않음 — 같은 Record 틀로 넓힐 수 있음 (A5 Bevel 즉시 적용 8).
- In-View Editor 의 Maya 다른 동작 (MMB 드래그 = 선택 행 값, 상자 끌어 옮기기, 접기 버튼) 없음. 툴팁이 상자 행을 가릴 때가 있음.
- 정점 좌표로 뚜껑 정점을 짝지음: 원래 메시에 같은 좌표의 정점이 겹쳐 있으면 짝이 틀릴 수 있음 (드묾).

## 검증

- mayapy (Maya 2022.4, 팩토리 `MAYA_APP_DIR` = `tmp/maya65/app`): 위 표 8 경우. Maya 는 끝나고 종료됨 (standalone).
- 헤드리스 `python tests/run.py`: **529/529** (61 파일; 새 `test_step65_extrude.py` 12 개: Maya 8 경우 좌표 일치, 빠른 길 = 다시 실행, 따로 떨어진
  평면 바닥 없음, 연산자·노드 이름·카운터·면 없음, cm 장면 Maya 단위, extrude_edit + 상태 (언두 흉내·다른 편집 = 무효), preview → edit, redo 이름 유지,
  키·메뉴·마킹 메뉴·셸프·매핑, CB 프록시 `0.5` / `+=0.25` / Divisions 2 / 못 읽는 글, In-View 레이아웃, 등록). step 18 / 63 테스트의 Ctrl+E·MTK 기대 갱신.
- GUI `gui_step65_extrude.py` 7/7 (기본 배율): Ctrl+E → polyExtrudeFace1 (12/10), 매니퓰레이터·In-View 표시, Thickness 행 드래그 → 0.496,
  Channel Box INPUTS Divisions 필드에 클릭 + `2` 입력 → 16/14 (Thickness 유지), Ctrl+Z 한 번 → Divisions 1 · Thickness 0.496, 파란 화살표 드래그 →
  Local Translate Z 1.128. 샷 `tmp/shots65/gui_step65_extrude.png` (화살표 + 상자 + INPUTS, modeling_03 과 같은 행), `gui_step65_inputs.png`,
  `gui_step65_arrow.png`.
- GUI 전체 `python tests/gui/run.py --ui-scale 0.8`: 445/446 → 실패 1 = step 18 의 「Ctrl+E 는 이동 모달」 기대 (이번 단계가 바꾼 동작) → 고쳐서
  gui_step18 14/14 (0.8, 기본), gui_step63 8/8.
- `python tools/dogfood.py`: **47/47** (Ctrl+E = polyExtrudeFace1), 콘솔 오류 0. 키맵 매핑 문서 재생성.
