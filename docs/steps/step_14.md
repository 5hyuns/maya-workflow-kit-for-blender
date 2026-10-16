# Step 14 — 재점검 1차 (AUDIT 1)

계획된 단계 1–13 이 끝난 뒤의 첫 재점검: 전체 테스트, 깨끗한 설정 설치 + Maya 사용자 관점 dogfood,
남은 것 통합 정리, blindspot 보완, 다음 할 일(backlog).

## 계획

- 테스트: `python tests/run.py` (헤드리스) + `python tests/gui/run.py` (GUI) 전체.
- Dogfood (delegated): 손으로 GUI 를 만질 수 없으므로 `tools/release_check.py` 와 같은 깨끗한 샌드박스
  (`tmp/release_env`, 사용자 실제 설정 안 건드림)에 zip 을 명령줄 설치·활성화하고, `--enable-event-simulate`
  GUI Blender 에서 **Maya 사용자의 첫 세션**을 이벤트로 재생하는 `tools/dogfood.py` + `tools/dogfood_session.py`
  를 만든다. 각 동작은 "Maya 사용자가 기대하는 결과" 체크 + 스크린샷(`tmp/dogfood/shots/`)을 남기고,
  세션 로그의 콘솔 오류/경고 줄을 모은다. 스크린샷은 직접 보고 어색한 점을 적는다.
  다음 재점검에서도 다시 돌릴 수 있게 저장소 도구로 둔다 (테스트 묶음 `tests/` 에는 넣지 않음: 아직 실패하는
  "기대" 체크가 들어 있어 녹색 기준선이 아니다).
- 정리: research/README.md 대응표 33행을 완료/부분/미착수/불가로 판정, `keymap/mapping.py` 상태 집계,
  step 「남은 것」·manual_checks 를 모아 PLAN 「재점검 1차」 절에 우선순위로.
- Blindspot: `unknowns:blindspot` 절차 (unknowns-scout 서브에이전트, 읽기 전용) 로 문서에 없는 누락을 찾는다.
- 버그 수정은 이번 단계에서 하지 않는다 (delegated): 재점검 결과를 backlog 로 넘겨 단계별로 고치고 검증한다.

## 한 것

- 전체 테스트 재실행 (HEAD `c0f37b0` 코드 그대로): 헤드리스 188/188, GUI 115/115.
- `tools/dogfood.py` + `tools/dogfood_session.py` (새 도구): 깨끗한 샌드박스에 zip 설치·활성화 → MayaKit 레이아웃 →
  Maya 사용자 첫 세션을 이벤트로 재생, 체크 43개 + 스크린샷 12장 + 콘솔 오류 수집.
- 대응표 33행 판정, 키맵 대응표 집계, 「남은 것」·manual_checks 통합 → `docs/PLAN.md` 「재점검 1차」.
- Blindspot (unknowns-scout, 읽기 전용): 문서에 없던 누락 14건. 상위 4건은 코드에서 직접 재확인
  (`operators/history.py:24-60`, `command_line/cmds_shim.py:424-429`, `docs/keymap_mapping.md:19,219`,
  `ui/menu_map.py:59,64`).
- manual_checks 에 Step 14 손 확인 2개 추가.
- 다음 할 일 8개 → `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json`.

## Dogfood 결과 (`python tools/dogfood.py`, 마지막 실행)

통과: 첫 시작 Maya 키맵, 빈 Maya 씬, Create Cube = pCube1, F, Alt+LMB/MMB/RMB, W/E/R/Q, 4/5, 3/1, Ctrl+D 제자리,
Ctrl+G group1 + Ctrl+Z, P (월드 위치 유지) / Shift+P, RMB 마킹메뉴 → Vertex, F8, Space 탭 4분할, Channel Box 탭 +
MMB 가상 슬라이더, Ctrl+A AE, Insert, Delete, Ctrl+Z, F11 면 모드, Ctrl+E (익스트루드 툴로 전환). 콘솔 오류 0줄.

실패 (Maya 기대와 다름 — 모두 backlog):

| 동작 | 결과 | 근거 |
|---|---|---|
| Ctrl+D | 사본 이름 `pCube1.001` (Maya `pCube2`) | research/maya/concepts.md:150-154 |
| `z` | Blender zoom border 모달 시작 (Maya Undo) | hotkeySetup.mel:67 (keymap_mapping.md) |
| Shift+Z | 아무 일 없음 (Maya Redo) | hotkeySetup.mel:69 |
| `h` | 숨기지 않음 (Maya 가시성 토글) | mapping.py `ToggleVisibilityAndKeepSelection` STEP 8 |
| Ctrl+1 | 로컬 뷰로 들어가지 않음 (Maya Isolate Select) | `ToggleIsolateSelect` STEP 8 |
| `.` | 프레임 그대로, Blender 피벗 파이가 열려 이후 키를 먹음 | `NextKey` STEP 7 |
| `=` | 매니퓰레이터 크기 그대로 | `IncreaseManipulatorSize` STEP 8 |
| Shift+> | 면 선택 확장 안 됨 | `GrowPolygonSelectionRegion` 미검토 |

스크린샷에서 본 어색한 점 (`tmp/dogfood/shots/`):

- F 프레이밍이 너무 빡빡함: 1 BU 큐브, persp 35 mm 에서 view_distance 1.07 — 큐브가 뷰를 넘침 (03, 05).
  팩토리 50 mm 는 1.66. Maya F 는 여백이 있음 (step_4 「남은 것」 fit factor 0.95 가 미구현으로 남아 있었음).
- 3 스무스 프리뷰가 각진 면(flat shading)으로 보임 (04): Maya 는 매끈한 셰이딩.
- 핫박스 메뉴 행이 오른쪽 사이드바(Channel Box) 밑으로 잘림 — "Windov", "Defor" (07).
- 왼쪽 Outliner 가 좁아 이름이 "pCube", "Scene Collect" 로 잘리고, Maya DAG 대신 Blender 컬렉션 트리 (01, 09).
- 타임라인 눈금 0–250, 재생 범위 1–120 (01, 기존 step_5 「남은 것」).
- 4분할 → 단일로 돌아온 정면 뷰 헤더가 "User Orthographic" (09).
- Channel Box 축 = Blender 축 (Translate Y 가 깊이). Y-up 불가 결정(decision 5)대로이나 Maya 사용자에게는 혼란 — 문서화 유지.

## Blindspot 카드 (scout 보고 요약, 중요도 순)

| # | 종류 | 발견 | 근거 | 조치 |
|---|---|---|---|---|
| B1 | Landmine | Delete History 가 "Maya Smooth Preview" Subsurf 까지 메시에 구움; 1 은 첫 Subsurf(사용자 것일 수 있음)를 끔 | `operators/history.py:24-60`, `operators/display.py:66-92` | 프리뷰 모디파이어 제외, 1/2/3 은 프리뷰 모디파이어만 |
| B2 | Missing concept | Create/셸프 큐브 1 BU(100 cm 표시) vs `cmds.polyCube()` 1 cm | `operators/create.py:29`, `command_line/cmds_shim.py:424-429` | 생성 경로 단위 규칙 하나로 (delegated 결정) |
| B3 | Landmine | 편집 모드 D = Annotate, Ctrl+Shift+A = 해제, Alt+D 없음 | `docs/keymap_mapping.md:19,219` | Mesh 키맵 패치 |
| B4 | Missing concept | Shift+매니퓰레이터 드래그 = 복제/압출이 PLAN 에 없음 | research/README.md:75 | 계획부터 (GizmoGroup / 킷 툴) |
| B5 | Missing concept | Ctrl+E / Ctrl+B 가 툴 전환만 | keymap_mapping.md (Mesh) | 즉시 실행 연산자로 |
| B6 | Missing concept | 컴포넌트 마키가 뒤쪽을 못 고름 (Maya 기본 관통) | research/maya/interaction.md:68 | X-ray / Camera-based 토글 결정 |
| B7 | Missing concept | 프리셀렉트 하이라이트 없음 | interaction.md:73 | 조사 (`mesh_preselect` 기즈모) |
| B8 | Missing concept | 언두 32 단계 (Maya 무한) | interaction.md:222 | `prefs_preset` 으로 |
| B9 | Landmine | `tests/test_keymap_maya.py` 가 IC idname 을 고정, `_STACKS` 밖 키맵 KeyError | tests/test_keymap_maya.py:148-203 | 키 작업 시 함께 갱신 |
| B10 | Landmine | `tests/kit.py` 가 `prefs.edit` 미스냅샷; gizmo_size 런타임 변경은 복원 안 됨 | tests/kit.py:79-80, prefs_preset.py:16-28 | 스냅샷 확장 |
| B11 | Missing concept | Increment and Save = Save As, Export Selection = 전체 내보내기 메뉴 | `ui/menu_map.py:59,64` | 재매핑 |
| B12 | Missing concept | 3D 뷰 Return = 이름 바꾸기 팝오버 | keymap_mapping.md:217 | 검토 |
| B13 | Missing concept | Ctrl+Shift+I, Ctrl+Y, Shift+G 미바인딩 | keymap_mapping.md | 키 묶음에 포함 |
| B14 | Convention | 테스트·생성기가 미추적 `research/*.json` 을 읽음 — 깨끗한 체크아웃에서 테스트 불가 | tests/test_keymap_maya.py:191 | 기록만 (decision 6) |

## 검증

- `python tests/run.py` → `188 passed, 0 failed, 14 file(s)`.
- `python tests/gui/run.py` → `115 passed, 0 failed, 10 file(s)`.
- `python tools/dogfood.py` → 체크 43개 중 통과 35, 실패 8 (위 표 — 의도된 "기대" 체크), 콘솔 오류/경고 0줄;
  스크린샷 12장 직접 확인.
- 코드 변경 없음 (`src/` 그대로) → 기존 테스트 결과가 그대로 유효.

## 남은 것

- PLAN 「재점검 1차」 우선순위 목록 1–14 전부. 다음 단계는 backlog.json 순서.
- dogfood 는 시뮬레이션 이벤트라 실제 손 감각은 manual_checks (84개 미확인).
- dogfood 도구는 아직 기대 체크 8개가 실패하므로 `tests/` 에 넣지 않음 — 고칠 때마다 해당 체크가 PASS 로 바뀌는지로 확인.
