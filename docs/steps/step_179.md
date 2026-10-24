# Step 179 — Light Linking

Backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_174.json` 6 번째 (재점검 12차 step_173_quant.md §7 #7).

## 계획 / 레인

측정 (mayapy 한 번) → Blender 의미 측정 (Cycles 프로브) → 구현은 둘의 결과에 따라 정해져서 순차 (레인으로 나눌 독립 작업이
작고 같은 모듈에 모임; 서브에이전트 없이 메인이 함 — 기다리는 포그라운드 레인보다 빠름).

## Maya 측정 (`research/maya/re/light_links_179.md` / `.json`, `research/scripts/light_links_179_mayapy.py`)

- 메뉴 = `lightlink -make / -break [-shadow] -useActiveLights -useActiveObjects`; 선택 4 개 = `Ren(Lighting|Shadowing)Select*` →
  첫 선택 노드로 `selectObjectsIlluminatedBy` 등 (`lightlink -q -transforms true -shapes false -hierarchy false -sets false`).
- 기본은 모두 연결; Break 는 그 라이트에서만, 그룹이면 계층 전체; 새 오브젝트는 기본 라이트에 연결; Illuminates by Default 끄면
  아무것도 안 비추고 Make 한 것만; 그림자 링크는 따로. 선택: transform 만 (그룹 없음), 첫 노드가 맞는 종류가 아니면 빈 선택.
- standalone 에서 `Ren*Select*` 는 `selectionConnection` 에서 실패 → 안쪽 proc 를 첫 노드로 불러 측정 (그림자 proc 는 바깥 파일 source 뒤).

## Blender 의미 (Cycles 프로브 `tmp/s179/probe_ll.py`)

receiver / blocker 컬렉션: EXCLUDE 만 = 나머지 비춤, INCLUDE 있음 = INCLUDE 만, 빈 컬렉션 = 전부, 빛을 받지 않는 오브젝트만
INCLUDE = 아무것도 안 비춤; blocker EXCLUDE = 그림자 없음.

## 한 것

- `operators/light_links.py`: 기본 라이트의 끊긴 연결 = EXCLUDE, Illuminates by Default 끔 (`Object.allset_illuminates_by_default`,
  Maya 라이트 속성) = 연결 INCLUDE + 라이트 자신 INCLUDE (자리표시: 연결 없음 = 아무것도 안 비춤). 컬렉션
  `<light>_lightLinks` / `<light>_shadowLinks` (씬에 안 붙음, fake user; delegated 이름). `allset.light_link(kind, make)`,
  `allset.light_link_select(kind, lights)` (첫 노드 = 선택된 활성 오브젝트, 아니면 첫 선택 — Blender 는 선택 순서가 없음, delegated),
  `allset.light_link_toggle`.
- `ui/light_link_editor.py`: Light Linking Editor = kit 팝오버 (keep_open): Light Centric / Object Centric, Light / Shadow Links,
  왼쪽 목록 = 고르기, 오른쪽 = 연결 토글 (계층 포함).
- `ui/menu_map.py` 9 행 (8 새 + 편집기를 Object 속성 대신 kit 창), `notices` Lighting/Shading 문구 = Transfer Maps 만.

## 검증

- menu_count: Lighting/Shading 5 → **13 / 14** (+8), 전체 806 → 814, 회색 notice 없음 0.
- 헤드리스 전체 `ALLSET_SANDBOX=s179full python tests/run.py`: **1653 / 1653** (+ `test_step179_light_links` 4): 같은 씬 · 같은 명령에서
  lightlink 질의 = mayapy (7 경우 + Illuminates by Default 끔 + 새 오브젝트), 선택 명령 9 경우 = mayapy, Cycles 프로브 (라이트 하나,
  큐브 둘, 연결 끊은 큐브 0.004 / 연결된 큐브 0.66).
- GUI `gui_step179_light_linking` 3 / 3: 메뉴의 Break Light Links, 편집기 (light-centric, 선택한 라이트). 샷 직접 봄: 왼쪽
  pointLight1, 오른쪽 pCube1 체크 / pCube2 해제.
- GUI 전체 묶음은 돌리지 않음 (CLAUDE.md step 141 규칙).

## 남은 것

- EEVEE 는 렌더 프로브 안 함 (Blender 4.5 EEVEE Next 도 light linking 을 쓴다고 문서에 있음; 측정은 Cycles 만).
- Maya 의 Illuminates by Default 는 AE 체크 상자 — kit 속성은 있지만 AE 라이트 탭 행은 아직 없음.
- Illuminates by Default 끈 라이트의 그림자 목록 (Maya 는 `[]`) 은 따라 하지 않음 (Blender 그림자는 그대로).
