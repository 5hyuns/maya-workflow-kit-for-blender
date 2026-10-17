# Step 48 — Maya 고유 워크플로우 분석·계획 (모델링·UV·애니메이션·리깅·FX·렌더·씬 관리)

사용자 요청 (2026-10-17, 원문): 「모델링, 애니메이션, 리깅, FX 등등 Maya의 고유한 워크플로우를 분석하고 그 워크플로우가 들어가게 해줘.」
이번 단계는 분석·계획 (작은 버그 수정 하나: bevel 너비). 결과 = `docs/PLAN.md` 「Maya 워크플로우 계획」, 결정 10
(`docs/user_decisions.md`), backlog 14 개 (`C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` → 단계 54–67).

## 방법

1. **Maya 2022 를 실제로 띄워 47 단계를 따라 함**: `research/scripts/maya_workflows/wf.py` (+ `launch.ps1`, `userSetup.py`;
   `MAYA_APP_DIR=tmp/maya_app` 팩토리 prefs). 분야마다 Maya 메뉴가 부르는 runtime command (또는 그것이 부르는 cmds) 를 순서대로 실행,
   단계마다 메인 창 + 떠 있는 Maya 창을 찍고 순서·명령·결과를 `research/maya/workflows/_maya_run.json` 에 남김. 결과: modeling 14,
   uv 3, animation 8, rigging 9, fx 4, render 5, scene 4 단계, 스크린샷 79 장 (`research/maya/workflows/shots/`, research/ 는 추적 안 함).
   - **사고와 수정**: 첫 실행은 메인 창을 화면 영역으로 찍어서 그 위에 있던 다른 앱 창 (사용자의 다른 프로그램) 이 찍혔다 → 그 47 장을
     바로 지우고, 메인 창은 Maya 위젯 자체 (`QWidget.grab`) + 3D 뷰는 `M3dView.readColorBuffer` 로 다시 찍었다 (Maya 밖은 절대 안 찍힘).
     이 방식에서는 뷰 배경이 검게 나온다 (색 비교용이 아니라 순서·창 기록용).
   - Arnold (mtoa) 는 이 실행에서 안 올라와 standardSurface 로 대신; Increment and Save 는 파일을 만들지 않았다 (규칙은
     `incrementAndSaveScene.mel` 머리 주석 근거, scene.md).
2. **mayapy 측정**: nucleus `spaceScale` 1.0, gravity 9.8 (방향 0 −1 0), substeps 3, 장면 단위 cm; 재생 범위 1–120 / 애니메이션 범위
   1–200; `parentConstraint` (−mo 없이) = 자식이 부모 위치로 (0, 3, 0).
3. **분야별 분석** (서브에이전트 7 개, 읽기 전용, 파일 하나씩): `research/maya/workflows/{modeling,uv,animation,rigging,fx,render,scene}.md` —
   Maya 손 순서 ([O] 이 실행 / [I] / [K] / [U]), 같은 일의 kit 지금 (file:line), 간격 표 (빈도 1–5 × 끊김 1–5), 개념 결정, 후보 단계와 GUI
   따라 하기 시나리오. 인용한 kit 주장 중 bevel 0.1 BU, Hypershade = Shader Editor (`ui/menu_map.py:92`), Create Reference = `wm.link`
   (`:111`), Separate = 편집 모드 `mesh.separate` (`:223`), 포즈 본 코드 없음 (grep), 셸프 Emitter = `particle_system_add`
   (`ui/shelf_map.py:102`) 는 직접 다시 확인.
4. **know-your-unknowns blindspot** (unknowns-scout 서브에이전트) 와 **/sc:brainstorm** (비대화형: 질문 없이 결정은 delegated, 아래 표).
5. 독립 검토 (self-review 서브에이전트) → 「검토」 절.

## Blindspot (unknowns-scout, 12 건) — 반영

| # | 종류 | 발견 | 반영 |
|---|---|---|---|
| 1 | Missing concept | 드라이버 큐에 49–53 (레이아웃·크롬·메뉴·핫박스·5.x) 이 이미 있음, backlog.json 은 큐가 빌 때 읽힘 (`autodrive_bmk/driver.py:174-190`) → 새 단계는 **54 부터** | 번호 54–67, 49/50 의존 표시 |
| 2 | History | Maya 기록이 진행 중이었음 | 끝난 뒤 분석 |
| 3 | Landmine | 많은 흐름이 이미 일부 매핑됨 (Skeleton/Skin/Constrain/Key/Visualize, CB 키 메뉴) | "kit 지금" 은 코드에서 |
| 4 | Landmine | 결정 8 이 비모델링 생성 경로에서 깨짐 (armature_add, effector_add, quick_smoke, text, light) | step 54, W5 |
| 5 | Missing concept | CB/Outliner/AE 가 오브젝트 전용, 포즈 본 없음 | step 55 (최고 점수 25) |
| 6 | Missing concept | Blender 낱말이 없는 Maya 개념 | PLAN W3 + 공용 안내 (step 54) |
| 7 | Landmine | 애니메이션 에디터 키 충돌 (K = knife, G repeat, Frames 키맵) | 56/57 에 "계획 먼저 + _add shadows" |
| 8 | Missing concept | 워크스페이스: 템플릿은 General 만, 핫박스는 Blender 워크스페이스로 | W6, step 57 (49 뒤) |
| 9 | Landmine | 얕은 매핑 (CHILD_OF 부모 제약, armature_add, ARMATURE_AUTO, playblast) | 각 단계의 "shallow → 고침" |
| 10 | Convention | 단계마다 지킬 규칙 (CLAUDE.md) | PLAN 절 머리 |
| 11 | Convention | 플러그인 메뉴 (MASH/Bifrost) 데이터 없음 | step 67 (CHILDREN/EXTRA) |
| 12 | History | 래퍼 연산 언두 함정 (step 26) | 63 에 "계획 먼저 (언두)" |

## Brainstorm — Resolved Decisions

비대화형 실행이라 모든 결정은 **delegated** (사용자 위임, "mandatory: 8 delegated decisions need independent audit" → 「검토」).

| # | 질문 | 결정 | 모드 |
|---|---|---|---|
| D1 | Maya 조인트는 무엇? | 아마추어 하나 안의 본 (W1), 포즈 모드 = 조인트 선택 | delegated |
| D2 | 컨스트럭션 히스토리 | 모디파이어 + kit 마지막 연산 INPUTS 한 행 (W2), 히스토리 노드는 계속 「불가」 | delegated |
| D3 | Blender 에 없는 기능 | 근접 대체 + 공용 안내 체계 (W3, step 54 가 먼저) | delegated |
| D4 | 시뮬레이션 스케일 | Maya 가 보이는 대로 (nucleus spaceScale 1 측정) — 결정 10 | delegated |
| D5 | 비모델링 생성 경로 단위 | 모두 `maya_unit()`, 조명 × `maya_unit()²` (W5) | delegated |
| D6 | Maya 워크스페이스 | `make_startup.py` 가 생성, 49 뒤 (W6) | delegated |
| D7 | 순서 | 점수 (빈도 × 끊김) 순, 의존만 조정: 기반 → 리깅/애니 핵심 (25·20) → 모델링 (20) → UV (20) → 렌더 (20) → FX 스케일 (20) → 씬 (16) → Graph Editor (15) (검토 v2) | delegated |
| D8 | 단계 크기 | 한 세션 = 한 분야의 한 흐름 묶음 (2–6 기능), 모달/키맵은 「계획」 먼저 | delegated |

탐색한 다른 안 (고르지 않음): 분야별 한 단계 (7 단계, 세션에 너무 큼); 기능별 한 단계 (40+ 단계, 흐름이 끊긴 채 쌓임);
FX 를 앞으로 (빈도 낮음); 포즈 본을 애니메이션 단계 안에 (리깅·애니 둘 다 막혀서 따로 먼저).

## 검토 (self-review 서브에이전트, 독립) — Self-Review Iteration Log

- v1 → v2 (검토 1 회차, 인용 22 개 확인 = 모두 맞음, 2 개 줄 번호 조금 어긋남):
  - (High, 크기) 57·59·64·66·67·55 가 한 세션보다 큼 → 점수 낮은 기능을 PLAN 「Left out」 으로: 버퍼 커브, Maya Animation 워크스페이스,
    Spline IK, Component Editor 표, Shape Editor, Outliner Sets, Hypergraph, 3D 유체, MASH (메뉴 데이터 먼저), 3D Cut and Sew 모달.
  - (Medium, 순서) Graph Editor (15) 가 모델링·UV (20) 앞 → 맨 뒤로; Target Weld·Extrude 의 MTK 의존 제거; UV·Graph Editor 는 52 (마킹 메뉴
    엔진), 씬은 50 (Outliner 모양) 의존 추가. 새 순서 = PLAN 표.
  - (Medium, 기대 결과) Combine 결과는 Maya 측정 `pCube2` (polySurface1 아님), 타임라인 RMB Delete = 현재 프레임 키만, S = 키 가능 채널 전부
    (Key Selected 가 CB 선택), 조명 검증은 energy == 10 W × maya_unit()² — backlog 고침.
  - (Medium, 불가 목록) □ 옵션 = `invoke_props_dialog` 팝업, 매니퓰레이터 = Python GizmoGroup 로 명시, Graph Editor F/A 는 이미 됨 → 제외.
  - (Medium, 결정 10) `/ Space Scale` 빠짐, 장면 중력 전역 문제, 다른 차원 양 (속도·Bullet·도메인·중력 방향), "1 단위 = 1 m" 는 [K] 표시,
    결정 8 의 해당 문장에 개정 표시 → 고침.
  - (Medium, 포괄) 빠진 간격 행 → PLAN 「Left out (점수, 이유)」 목록.
  - (Medium, 규칙) 키맵 단계마다 `_add` + mapping 재생성, 모달/키맵 단계에 「계획 먼저」, 새 마킹 메뉴는 research JSON 위치 + test_step8 식 검사.
  - (Low) 필드 크기는 54 가 맡음 (FX 에서 뺌), Light Editor 의 자리 (새 에디터 타입 불가 → 새 창 3D View 사이드바 탭).

## 한 것

- `research/scripts/maya_workflows/` (Maya 기록 도구), `research/maya/workflows/*.md` 7 개 + `_maya_run.json` + shots (추적 안 함).
- `docs/PLAN.md` 「Maya 워크플로우 계획」 (간격 표, 이미 된 것, 개념 결정 W1–W6, 단계 54–67 표와 의존).
- `docs/user_decisions.md` 결정 10 (시뮬레이션 스케일).
- backlog.json 14 항목 (새 파일; 이전 backlog 는 backlog_15/24/33/41.json 으로 옮겨져 있었음), 검토 v2 반영 (v1 사본 tmp/backlog48_v1.json).
- **버그 수정** (분석 중 발견): `maya_kit.bevel` exec 경로 너비 `offset=0.1` BU → `0.1 × maya_unit()` (cm 템플릿에서 10 Maya 단위였음,
  `src/maya_kit/operators/component.py`). 헤드리스 테스트 `test_step18_mesh_keys::test_bevel_exec_width_is_in_maya_units` (고치기 전
  실패, 고친 뒤 통과 확인).

## 검증

- Maya 실행 2 회차: 48 단계 모두 실행 (`_log.txt` "done"), Maya 스스로 종료 (프로세스 없음 확인). 스크린샷은 Maya 위젯만.
- 헤드리스 `python tests/run.py`: **375/375** (step 18 새 테스트 포함; 고치기 전 7/8 로 실패 확인). `python tools/dogfood.py`: **47/47**,
  콘솔 오류 0. GUI `gui_step18_mesh_keys` (Ctrl+B 포함): 14/14 (ui_scale 1.0), 14/14 (0.8).
- backlog.json: 14 항목, 각 항목에 근거 path:line, 할 일, 의존, Maya 순서 GUI 시나리오, 검증.

## 남은 것

- Maya 기록에서 못 본 것: Arnold 메뉴·aiStandardSurface (mtoa 미로드), Increment and Save 결과 파일, MASH Distribute 기본값,
  3D Container 크기, Ghost 메뉴 위치, UV Editor RMB 마킹 메뉴 — 해당 단계에서 Maya 를 다시 띄워 확인 (각 workflows/*.md 「반증·모름」).
- 뷰 배경이 검은 스크린샷 (readColorBuffer) — 순서 기록용이라 그대로.
- step 40 의 `research/scripts/maya_shots/shots.py` 도 메인 창을 화면 영역으로 찍는다 (지금 있는 샷은 깨끗함). 다시 돌리기 전에
  `wf.py` 의 `grab()` (위젯 렌더 + readColorBuffer) 로 바꿀 것 — 단, 색 비교용 뷰 픽셀은 readColorBuffer 가 화면 색과 같은지 먼저 확인.
