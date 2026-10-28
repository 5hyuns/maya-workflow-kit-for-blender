# Manual checks

Things headless tests can't prove (modal input, feel, visuals). Run in a GUI Blender
started with sandbox user dirs (never the real `%APPDATA%` config):

```
set BLENDER_USER_CONFIG=C:\Repos\blender-maya-kit\tmp\test_env\config
set BLENDER_USER_SCRIPTS=C:\Repos\blender-maya-kit\tmp\test_env\scripts
set BLENDER_USER_EXTENSIONS=C:\Repos\blender-maya-kit\tmp\test_env\extensions
"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" --factory-startup
```

Format: `- [ ] (step N) what to do → what you should see`.

**자동 / 수동 (step 97, 2026-10-18)**: 항목 369 개 (step 96 까지) 중 **70 개 자동 확인** (`[x]`, 끝에 확인한 GUI 테스트 이름 —
`tests/gui/gui_manual_sweep.py`, 항목 id `[M<step>-<번호>]`; step 88 에 13, step 97 에 57), **299 개 수동** (`[ ]`). step 59–79 에서 수동으로 남은
것은 사람 판단 (느낌·색·Maya 화면 비교·다른 UI 배율) 과 event_simulate 로 못 만드는 입력 (DOUBLE_CLICK, OS 에 가는 키·창 / 재시작·강제 종료·설치)
뿐 (`docs/steps/step_88.md` 「분류」); step 81–96 의 분류와 다음 정리 후보 (시뮬레이션 가능 38) 는 `docs/steps/step_97.md` 「분류」.


## Checklist

### Step 2 — Maya 키컨피그

- [ ] (step 2) 3D 뷰에서 오브젝트 클릭 / Shift 클릭 / Ctrl 클릭 / Ctrl+Shift 클릭 → 교체 / 토글 / 해제 / 추가.
- [ ] (step 2) 빈 곳에서 드래그 / Shift / Ctrl / Ctrl+Shift 드래그 → 교체 / 토글 / 해제 / 추가 (Select Box 툴, Move 툴 fallback 둘 다).
- [ ] (step 2) 편집 모드 Ctrl+Shift 클릭 → 현재는 최단 경로 선택(IC Mesh). Maya 2022 에서 같은 조작 결과와 비교.
- [ ] (step 2) Outliner Ctrl 클릭·Shift 클릭 → 지금은 둘 다 토글. Maya 2022 Outliner (Ctrl=토글, Shift=범위?) 와 비교해 규칙 확정.
- [ ] (step 2) 마우스를 둔 3D 뷰에서 4/5/6/7 → 와이어 / 솔리드 / 텍스처 솔리드 / Material Preview+씬 라이트. 다른 3D 뷰는 안 바뀜.
- [ ] (step 2) F8 → 오브젝트 ↔ 에디트 모드 (마지막 컴포넌트 모드 유지).
- [ ] (step 2) 오브젝트 2개 선택 후 Ctrl+G → `group1` 생성·선택, 오브젝트 제자리, Ctrl+Z 한 번에 되돌림. Outliner 에서 Ctrl+G 도 동일.
- [ ] (step 2) Space → 아무 일 없음, Alt+V 재생/정지, Alt+Shift+V 시작 프레임.

### Step 3 — 홀드/탭, 피벗, pick-walk

GUI 자동 테스트(`python tests/gui/run.py`)가 이벤트 순서는 확인한다. 아래는 실제 손 감각과 OS 입력 경로 확인.

- [ ] (step 3) 실제 키보드로 X 를 누른 채 Move 기즈모 드래그 → 그리드에 딱딱 붙음; 드래그 중 X 를 먼저 놓고 마우스를 놓아도 스냅이 꺼짐 (keystate 폴백, 실제 OS 키).
- [ ] (step 3) V 홀드 + 드래그 → 정점에 스냅; C 홀드 → 엣지 위 스냅. Maya 의 C(커브) 와 감각 비교.
- [ ] (step 3) 스냅을 헤더에서 켜 둔 상태에서 X 를 눌렀다 놓기 → 원래 스냅 설정(요소 포함)으로 돌아옴.
- [ ] (step 3) J 홀드 + 회전/이동 → 증분 스냅.
- [ ] (step 3) B 탭 → 소프트 셀렉트(Proportional) 켜짐/꺼짐 (오브젝트/편집 모드 각각). B 홀드 + LMB 좌우 드래그 → 헤더에 반경, 놓으면 유지; 드래그 중 ESC → 원래 반경.
- [ ] (step 3) A 탭 → 전체 프레이밍. A 홀드 + 클릭 → Select 메뉴가 뜨고 항목 클릭으로 실행.
- [ ] (step 3) D 홀드 + 이동 → 오브젝트는 그대로, 원점(피벗)만 이동; 놓으면 일반 이동. Insert → 토글, 상태바 메시지.
- [ ] (step 3) 계층에서 ↑/↓/←/→ → 부모/첫 자식/이전·다음 형제 (끝에서 순환). Outliner 순서(이름순)와 일치.
- [ ] (step 3) 키를 누른 채 다른 창(Alt+Tab)으로 갔다 와도 스냅·피벗 상태가 남지 않음.

### Step 4 — 카메라·뷰

- [ ] (step 4) Alt+LMB 텀블: 씬이 세워진 채(턴테이블) 뷰 중심(COI) 기준으로 돈다; 선택 오브젝트 중심으로 돌지 않음. F 후 텀블 → 선택 중심.
- [ ] (step 4) Alt+RMB 오른쪽 드래그 = 다가감, 왼쪽 = 멀어짐; 휠 위 = 다가감; 커서 위치로 줌되지 않음. Maya 와 속도 비교.
- [ ] (step 4) 정면/측면/윗면 직교 뷰에서 Alt+LMB → 안 돎 (환경설정 Lock Tumble in Ortho Views 끄면 돎).
- [ ] (step 4) 여러 번 내비게이션 후 `[` 반복 → 단계별 이전 뷰, `]` → 다시 앞으로. Ctrl+Z 는 뷰를 되돌리지 않음.
- [ ] (step 4) Space 탭 → 4분할, 아무 쿼드 위에서 Space 탭 → 그 뷰로 단일. Space 를 누르고 있으면 아무 일 없음(핫박스 자리).
- [ ] (step 4) Shift+F / Shift+A → 쿼드·다른 3D 뷰 영역 모두 프레이밍.
- [ ] (step 4) 1/2/3 (오브젝트·편집 모드) → 스무스 끔 / 와이어+스무스 / 스무스; 렌더 결과는 그대로.
- [ ] (step 4) F9/F10/F11/F7 → 정점/엣지/면/멀티 편집, F8 → 오브젝트 모드.
- [ ] (step 4) Ctrl+Space → UI 숨긴 전체 화면, 다시 → 원래대로.

### Step 5 — 레이아웃·테마

- [ ] (step 5) 오브젝트 와이어프레임(4) 색: 비선택 짙은 파랑, 선택 초록, 리드 흰색이 Maya 와 비슷한지.

### Step 6 — Channel Box / Layer Editor

- [ ] (step 6) 오브젝트 3개 선택 -> Translate X 에 값 입력 -> 셋 다 같은 값; Ctrl+Z 한 번에 되돌림.
- [ ] (step 6) Translate X 이름 클릭 -> 뷰포트 MMB 좌우 드래그로 값 변화 (Ctrl 느리게, Shift 빠르게), 커서가 화면 끝에서 감겨도 계속; ESC 로 취소. 채널 선택 해제 후 MMB -> Move 툴 드래그.
- [ ] (step 6) Channels 메뉴: Key Selected -> 타임라인에 키, 필드 붉게; Lock Selected -> 회색·편집 불가; Hide Selected -> 행 사라짐, Show All -> 복귀.
- [ ] (step 6) Settings 메뉴 속도 Slowest~Fast, Hyperbolic -> 슬라이더 감도 (Maya 와 체감 비교).
- [ ] (step 6) Layer Editor: 선택으로 새 레이어 -> V 끄면 숨김, T -> 와이어·선택 불가, R -> 선택 불가, P 끄고 재생(Alt+V) -> 재생 중만 숨김. 레이어 삭제 -> 원상.

### Step 7 — 메뉴바·메뉴셋, Status Line, 커맨드 라인, Help Line

- [ ] (step 7) 메뉴셋 드롭다운 Modeling → Rigging → Animation → FX → Rendering: 메뉴가 바뀌고 다시 시작해도 마지막 메뉴셋 유지.
- [ ] (step 7) 각 메뉴의 진한 항목 몇 개 실행 (Create > Polygon Primitives > Cube, Edit Mesh > Bevel 은 마우스로 조절, Mesh Tools > Multi-Cut, Constrain > Parent 를 대상→피구속 순서로 선택 후) — Maya 와 비슷한 결과인지. 회색 항목 툴팁에 Maya 경로.
- [ ] (step 7) 좁은 창(1280 px)에서 메뉴바가 잘리는 정도; 헤더 우클릭 > Show Menus 끄면 메뉴가 하나로 접힘.
- [ ] (step 7) Status Line: 스냅 버튼 클릭/홀드 X·C·V 중 표시, 마스크로 메시 선택 막기, Component 버튼 → 편집 모드에서 정점/엣지/면 토글, Render 버튼, Channel Box 버튼 → 사이드바, Tool Settings 팝업.
- [ ] (step 7) 커맨드 라인: `cmds.polyCube(w=200, h=200, d=200)` Enter → 2 m 큐브, Ctrl+Z 한 번에 사라짐; `polyCube -w 2;` → 붉은 힌트; 최근 명령 메뉴에서 다시 실행; Script Editor 버튼 → 콘솔 창.
- [ ] (step 7) Help Line: Move/Rotate/Scale 툴 전환 시 문구, 결과가 길 때 상태바에서 잘리는 정도.

### Step 8 — 마킹메뉴 (파이)

- [ ] (step 8) 오브젝트 모드, 큐브 위 RMB 누른 채 위/왼쪽/아래로 끌어 놓기 → 엣지/정점/면 모드; 짧게 클릭하면 파이가 남고 클릭으로 고름. Maya 와 손맛 비교 (`pie_tap_timeout` 200 ms, 문턱 12 px).
- [ ] (step 8) 두 객체 중 선택 안 된 쪽 위에서 RMB → Vertex: 그 객체만 컴포넌트 모드. RMB 후 ESC: 선택 그대로.
- [ ] (step 8) 편집 모드에서 Shift+RMB (정점/엣지/면 선택 모드마다 다른 메뉴), Ctrl+RMB 변환, NE Object Mode 로 나가기.
- [ ] (step 8) W/E/R/Q 누른 채 LMB → 옵션 파이, 끌어 놓기로 World/Object/Component; 그냥 W 탭 = 툴 전환만.
- [ ] (step 8) Ctrl+Shift+RMB = 현재 툴 옵션 파이; 페인트/스컬프트 모드 RMB 는 Blender 그대로.

### Step 9 — 핫박스 + 마킹메뉴 엔진

- [ ] (step 9) RMB 누른 채 가만히: 약 0.15 s 뒤 메뉴가 뜬다; 빠르게 그어 놓으면 메뉴 없이 그 방향 항목 (Maya "mark" 와 비교).
- [ ] (step 9) Shift+RMB 엣지 모드: 위로 끌어 Merge/Collapse ▸ 가 그 자리에서 열리고 이어서 오른쪽 = Collapse Edge. 위→오른쪽 지그재그 한 번에도 같은 결과.
- [ ] (step 9) 옵션 박스 `[]` 위에서 놓기 → 그 항목의 옵션 상자 (step 103 / 147 뒤: Maya 창 종류는 Maya 옵션 창, "redo" 종류만 Adjust Last Operation — `menu_sets.option_kind`; 예: Face 모드 Poke Face `[]`); 툴(Multi-Cut `[]`) → 툴 + Tool Settings 팝업. 베벨처럼 모달인 것은 팝업 없이 모달.
- [ ] (step 9) 짧은 RMB 클릭 → 메뉴가 남음, 항목 클릭/ESC/가운데 클릭 = 취소.
- [ ] (step 9) Space 홀드 → 핫박스 행(Recent Commands, Hotbox Controls, File…, 메뉴셋 메뉴), 이름 클릭 → 메뉴. 가운데/위/아래/좌/우 클릭 → 뷰/레이아웃/패널 종류/마스크/UI 마킹메뉴. Space 짧게 = 4분할↔단일 (다른 에디터는 최대화), 오래 누르고 그냥 놓기 = 아무것도 안 함.
- [ ] (step 9) S 존으로 3D 뷰를 Outliner/Graph 로 바꾼 뒤 거기서 Space → 가운데 Perspective 로 3D 뷰 복귀.
- [ ] (step 9) 환경설정 Marking Menus = Blender Pies 로 바꾸면 Step 8 파이로 돌아감.
- [ ] (step 9) 4K/HiDPI(UI 배율 2)에서 크기·글자, 빠르게 움직일 때 끊김 없음, 창 밖으로 끌고 나가 놓아도 메뉴가 남지 않음.

### Step 10 — 개념 연산자

- [ ] (step 10) 회전·비균일 스케일한 큐브에 Modify > Freeze Transformations: 모양·위치 그대로, Channel Box 0/0/1, Move 툴 기즈모(피벗)가 제자리. 이어서 이동·회전 후 Modify > Reset Transformations → 동결 직후 상태.
- [ ] (step 10) 그룹(Ctrl+G) 위에서 Freeze: 자식까지 0/0/1, 모양 그대로. Freeze 옵션은 Adjust Last Operation(마킹메뉴 `[]`)에서 Translate/Rotate/Scale 끄고 켜기.
- [ ] (step 10) 정점을 한쪽으로 옮긴 객체에 Modify > Center Pivot: 메시 그대로, 피벗이 가운데로, Translate 값 그대로. N 패널 Delta Transform 에 피벗 오프셋이 보이는 것이 거슬리지 않는지.
- [ ] (step 10) P: 자식들 → 부모 순서로 선택 후 P, Outliner 에서도 P. Channel Box 값이 부모 기준(Maya 와 같은 숫자). Shift+P 로 월드로. 환경설정 Parent Mode = Blender 로 바꾸면 Blender 방식.
- [ ] (step 10) Shift+D: 복제 → 옮기기/회전 → Shift+D 반복 = 같은 간격 배열 (Maya smart duplicate). Ctrl+Shift+D: Adjust Last Operation 에서 사본 수·오프셋·Instance·Group Under 조절.
- [ ] (step 10) Alt+Shift+D / A 홀드+LMB 마킹메뉴(NW Delete History, NE Non-Deformer, SE Freeze): Subsurf·Bevel 굽기, Armature 는 Non-Deformer 에서 남음. Edit > Delete by Type / Delete All by Type 항목들.
- [ ] (step 10) Create 메뉴: pCube1/pSphere1… 원점·Maya 크기(큐브 = 그리드 한 칸), 데이터 이름 pCubeShape1. 라이트·카메라는 수평 방향.
- [ ] (step 10) 환경설정 Maya Units 켜기: 1 cm 큐브가 그리드 한 칸, 확대·축소 시 클리핑 없음(0.1–10000), 물리/라이트 감쇠 차이 확인. 끄면 원래 값. 저장한 파일을 다시 열면 바뀌지 않음, File > New 는 Maya 단위.

### Step 11 — Outliner, Attribute Editor

- [ ] (step 11) 뷰포트에서 Ctrl+A: 사이드바가 열리고 Channel Box 탭에서 Attribute Editor 가 보임, 다시 Ctrl+A 로 Channel Box. 다른 사이드바 탭(Item 등)이 열려 있으면 탭은 그대로라 Channel Box 탭으로 직접 가야 함 — 거슬리는지.
- [ ] (step 11) AE 탭 클릭(transform / shape / 모디파이어 / 재질), 섹션 열고 닫기가 노드 종류마다 기억됨, 이름 필드에서 바로 이름 변경, 모디파이어 탭 ◀ ▶ 로 스택 이동, Delete History 버튼.
- [ ] (step 11) 선택을 바꿔도 같은 종류의 탭(예: 재질)이 유지되는지 — Maya 와 비교.
- [ ] (step 11) Outliner 탭: 행 더블클릭 = 이름 변경 (객체, Shapes 켜면 데이터 이름도), 화살표 / Shift+화살표 펼치기, 행 클릭 선택, 아이콘 Ctrl+클릭 토글 / Shift+클릭 범위, 숨긴 객체 흐림.
- [ ] (step 11) 객체 추가·삭제·부모 변경(P) 직후 Outliner 행이 바로 갱신되는지, 객체 수백 개에서 느려지지 않는지.
- [ ] (step 11) Ctrl+Shift+A 전체 선택, Alt+D 선택 해제 (Maya), 편집 모드 Ctrl+A 는 Blender 그대로.

### Step 12 — 셸프

- [ ] (step 12) Maya Workflow Kit 레이아웃: 메뉴바 아래 Status Line, 그 아래 셸프 (Maya 와 같은 순서), 창 크기를 바꿔도 띠가 두 줄 높이로 남는지.
- [ ] (step 12) Poly Modeling 큐브 버튼 클릭 → pCube1, **더블클릭** → 큐브 하나 + 그 큐브의 옵션 (두 개 생기지 않음), Ctrl+클릭 → 옵션. step 167 부터 더블클릭 = 그 버튼의 Maya 메뉴 항목 옵션 상자 (`allset.menu_option_box`, Polygon Cube 는 `gui_step167_shelf` 가 확인) — 실제 마우스의 더블클릭 간격에서도 큐브가 하나인지 볼 것.
- [ ] (step 12) 탭 드롭다운 / ◀ ▶ 로 Rigging·Animation·Rendering 전환, 다시 시작해도 마지막 탭 유지 (환경설정 저장 시).
- [ ] (step 12) 톱니 > New Shelf → Add Button(스크립트 한 줄, 아이콘 이름) → 클릭 실행, Edit/Delete Button, Add Last Command (커맨드 라인 실행 후), 다시 시작해도 사용자 셸프가 남음.
- [ ] (step 12) 팩토리 레이아웃에서 Windows > UI Elements > Shelf 로 띠 추가/제거, 다른 Image Editor 는 평소처럼 보임.

### Step 13 — 배포

- [ ] (step 13) 비활성화 → 키맵·Image Editor 헤더가 원래대로, 다시 활성화.

### Step 14 — 재점검 1차

`python tools/dogfood.py` 가 같은 순서를 시뮬레이션 이벤트로 재생한다 (체크 + `tmp/dogfood/shots/`). 아래는 실제 손으로.

- [ ] (step 14) 깨끗한 프로필에서 첫 세션: Create Cube → F → Alt 마우스 → W/E/R → 4/5/3/1 → Ctrl+D → Ctrl+G → P → RMB Vertex → F8 → Space 탭/홀드 → Channel Box MMB → Ctrl+A. 각 단계가 Maya 와 같은 결과·속도인지, 콘솔(Window > Toggle System Console) 오류가 없는지.
- [ ] (step 14) F 프레이밍 여백을 Maya 2022 의 같은 장면(1 단위 큐브, persp 35 mm)과 나란히 비교.

### Step 15 — 스무스 프리뷰

- [ ] (step 15) 큐브에 3 → 매끈한 셰이딩, 빠르게 회전해도 끊김 없음 (Preferences > Viewport > GPU Subdivision 켠 상태에서 Subsurf 가 GPU 로 도는지: 고해상도 메시로 1 ↔ 3 체감 비교). 3 → Alt+Shift+D → 메시 그대로·프리뷰 유지, 1 → 원래 각진 큐브.

### Step 16 — 언두·가시성·아이솔레이트

- [ ] (step 16) 실제 키보드로 z / Shift+Z / Ctrl+Y: 3D 뷰, Outliner, Graph Editor 위에서 각각 언두·리두. 텍스트 에디터·Python 콘솔·커맨드 라인 필드에서는 z 가 글자로 입력됨.
- [ ] (step 16) h 두 번 (숨김 → 보임+선택), Ctrl+H → Ctrl+Shift+H, Alt+H → Shift+H, Outliner 에서 숨긴 객체 클릭 후 Shift+H. Maya 2022 와 선택 상태 비교.
- [ ] (step 16) Ctrl+1 아이솔레이트 중 카메라가 움직이지 않음, 다시 Ctrl+1 로 원래 뷰.

### Step 17 — 프레이밍·핫박스

- [ ] (step 17) 큐브·구·여러 객체에서 F / A / Shift+F / Ctrl+Shift+F 여백을 Maya 2022 의 같은 장면과 비교 (사이드바 열고/닫고). 편집 모드 면 몇 개 선택 후 F.
- [ ] (step 17) 사이드바 가까이에서 Space 홀드: 메뉴 행이 모두 보이고 이름 클릭이 동작. 좁은 창(1280 px)에서 긴 행 줄바꿈.

### Step 18 — 편집 모드 키

- [ ] (step 18) 편집 모드에서 D 를 누른 채 클릭/드래그로 피벗(3D 커서) 배치 → D 놓고 W 로 이동·회전 시 그 점 기준; D 탭으로 원래 피벗. V 홀드와 함께 정점에 피벗 스냅.
- [ ] (step 18) Ctrl+E (면/엣지/정점), Ctrl+B (정점 모드 = 정점 베벨) 드래그 감각을 Maya 와 비교. Shift+> / Shift+< 반복, Ctrl+F9–F11 변환 결과를 Maya 와 비교.

### Step 19 — 복제

- [ ] (step 19) 애니메이션이 있는 객체를 Ctrl+D: 사본도 같은 액션을 공유하는지(Blender) / Maya 2022 는 사본에 애니메이션이 없는지 비교해 규칙 확정. 그룹 Ctrl+D 후 Outliner 이름 (group2, pCube2 …).

### Step 20 — 타임라인

- [ ] (step 20) 키가 있는 객체에서 `.` / `,` / Alt+`.` / Alt+`,` 를 3D 뷰·타임라인·그래프 에디터 위에서. Range Slider 네 필드를 바꾸면 재생 범위·타임라인 뷰가 Maya 처럼 따라가는지, 재생 범위 토글을 끄면 애니메이션 범위 전체가 재생되는지.

### Step 21 — 단위

- [ ] (step 21) Maya Workflow Kit 레이아웃 새 씬에서 Create > Polygon Primitives > Cube 의 화면 크기를 Maya 2022 새 씬 기본 persp 와 비교 (뷰 거리·클립은 Maya 값이지만 Blender 뷰포트 렌즈 화각이 다를 수 있음). 1 cm 큐브를 가까이 텀블·돌리·W 이동 했을 때 클립 잘림·그리드(cm 간격)·매니퓰레이터 감각.
- [ ] (step 21) Maya 에서 내보낸 FBX(cm)를 File > Import 로 가져와 Create 큐브와 같은 크기인지, Maya Units 켬/끔 둘 다.

### Step 22 — 매니퓰레이터 Shift+드래그 복제

- [ ] (step 22) W/E/R 툴에서 기즈모 화살표·평면·중앙·회전 링·스케일 핸들을 Shift+드래그 → 사본이 변환되고 원본 제자리. Shift 를 끝까지 누른 채 끌어도 느려지지 않는지, 드래그 도중 Shift 를 떼었다 다시 누르면 Blender 정밀 모드가 되는지. Maya 2022 의 같은 동작과 손 감각 비교.
- [ ] (step 22) Shift+클릭(드래그 없음), 드래그 중 RMB/Esc 취소 때 사본이 남는지 Maya 와 비교. Ctrl+Z 한 번에 사본까지 사라지는지.
- [ ] (step 22) 라이트(스포트 크기 등) 기즈모를 Shift+드래그 했을 때 복제가 일어나지 않아야 함.

### Step 24 — 컴포넌트 Delete

- [ ] (step 24) Maya 2022 와 같은 메시에서 면·엣지·정점(모서리 정점, 3개 이상 엣지 정점, 경계 정점) Delete 결과 비교. 경계 엣지만 선택하고 Delete 했을 때 Maya 경고와 비교.

### Step 25 — cm 그리드·스냅

- [ ] (step 25) Maya Workflow Kit 레이아웃에서 확대/축소하며 그리드 단계(1 cm → 10 cm → 1 m)가 바뀔 때 X 홀드 스냅 간격이 따라 바뀌는지, Maya 2022 그리드 스냅 감각과 비교.

### Step 26 — Smart Extrude

- [ ] (step 26) 면·엣지 선택에서 이동/회전/스케일 기즈모 Shift+드래그 → 압출 후 변환; Shift+클릭, RMB/Esc 취소 → 아무것도 남지 않음; 그 뒤 Ctrl+Z / Ctrl+Shift+Z 가 앞 작업을 망가뜨리지 않는지. Maya 2022 와 손 감각 비교.
- [ ] (step 26) 스포트 라이트 선택 + 라이트 기즈모(크기·블렌드) Shift+드래그 → 복제 안 됨.

### Step 27 — 매니퓰레이터 크기·뷰 키

- [ ] (step 27) = / - 몇 번 눌러 매니퓰레이터 크기 변화 폭을 Maya 2022 와 비교; 애드온을 껐다 켜면 원래 크기. Home 이 Maya 기본 뷰처럼 느껴지는지 (Maya Workflow Kit 레이아웃 cm 장면에서). PgUp/PgDn 단계 변화를 3 모드에서 비교.

### Step 28 — MMB 활성 핸들

- [ ] (step 28) W/E/R 에서 축·평면·중앙 핸들을 한 번 끈 뒤 뷰 아무 곳 MMB 드래그 → 그 핸들로 변환; 툴을 바꿨다 돌아와도 유지; 같은 툴 키 다시 탭 → 자유. Maya 2022 와 손 감각 비교 (회전 MMB 드래그 방향 포함). Channel Box 채널 선택 시 MMB = 슬라이더가 우선.

### Step 29 — 재질 지정

- [ ] (step 29) 아무것도 선택하지 않고 오브젝트 위 RMB → Assign Favorite Material ▸ / Assign Existing Material ▸ / Assign New Material... → 커서 아래 오브젝트에 지정; 선택이 있으면 선택에 지정. 뷰 아래쪽 오브젝트에서 RMB 했을 때 목록·하위 메뉴가 잘리지 않는지. Maya 2022 와 비교.
- [ ] (step 29) 클릭 모드(RMB 짧게 클릭)에서 항목을 클릭했을 때 손을 뗄 때 실행되는 감각이 어색하지 않은지 (모든 클릭 모드 항목이 버튼을 뗄 때 실행).
- [ ] (step 29) 편집 모드 면 선택 → Shift+T → 종류 검색 → Enter: 그 면만 바뀜; 정점/엣지 모드는 오브젝트 전체. Maya 의 컴포넌트 재질 지정과 비교. 렌더/Material Preview 에서 색 차이 확인.

### Step 30 — 선택 감각

- [ ] (step 30) 편집 모드에서 Maya 처럼 뒤쪽 정점까지 마키로 잡히는지 (Select 툴, Move 툴 빈 곳 드래그, 라쏘). 드래그 중 숨은 엣지가 비쳐 보이는 것이 거슬리지 않는지, 놓은 뒤 X-Ray 버튼이 원래대로인지. Maya 2022 와 비교.
- [ ] (step 30) 정점 모드에서 마우스 아래 정점 하이라이트(작은 점)가 Maya 프리셀렉트처럼 도움이 되는지, 큰 메시에서 호버가 느려지지 않는지. 엣지/면 모드는 하이라이트 없음.
- [ ] (step 30, step 141 에서 바뀜) 킷은 Undo Steps 를 쓰지 않는다 (step 130): Blender 기본 32 단계 그대로인지, 킷 환경설정에 "Recommended setup" 언두 안내가 보이는지 (Undo Steps < 256 일 때만), 사용자가 직접 256 으로 올리면 안내가 사라지고 긴 세션에서 256 단계까지 되는지, 메모리 사용이 괜찮은지.

### Step 31 — 레이아웃 다듬기

- [ ] (step 31) Maya Workflow Kit 레이아웃 왼쪽 Outliner 에서 긴 이름(pCylinder12, group3 아래 3 단계)이 잘리지 않는지, 컬렉션 행 없이 오브젝트만 보이는 것이 Maya Outliner 처럼 느껴지는지. 새 컬렉션을 만든 경우 Layer Editor 쪽에서만 보이는 것이 혼란스럽지 않은지.
- [ ] (step 31) Space 탭 4분할 → top/front/side 위에서 다시 Space 탭 → 헤더가 "Top/Front/Right Orthographic" 으로 남는지.
- [ ] (step 31) W/E/R 홀드 메뉴 체크 상자 켜짐/꺼짐이 한눈에 구분되는지 (엔진, 환경설정 Blender Pies 둘 다).
- [ ] (step 31) 타임라인 현재 프레임 상자가 옆 눈금 숫자를 가리는 것 (Blender C 그리기, 고치지 못함) 이 Maya 사용자에게 거슬리는지.

### Step 33 — 메뉴가 화면 안에

- [ ] (step 33) 뷰 아래쪽·위쪽·좌우 가장자리·모서리의 오브젝트에서 RMB / Shift+RMB / Ctrl+RMB / W 홀드 → 모든 항목이 보이고, 목록이 링 위·옆으로 옮겨져도 드래그·플릭·클릭이 어색하지 않은지. Maya 2022 의 가장자리 동작과 비교.
- [ ] (step 33) 화면 위쪽에서 Space 홀드 → 메뉴 행이 가운데 상자 아래로 내려온 핫박스가 쓸 만한지 (Maya 비교).

### Step 34 — 메뉴 막다른 길

- [ ] (step 34) Windows > Animation Editors > Graph Editor 등이 떠 있는 창으로 열리는 것이 Maya 사용자에게 자연스러운지 (Maya 도 별도 창). 창 크기·위치, 닫은 뒤 다시 열기.
- [ ] (step 34) Edit > Ungroup: 중첩 그룹·여러 그룹 선택·애니메이션 있는 자식에서 Maya 2022 결과와 비교 (월드 위치 유지, 선택 결과).
- [ ] (step 34) File > Increment and Save 를 여러 번 → shot.0001, 0002 …; 저장 안 한 씬에서는 Save As 창.
- [ ] (step 34) UV > Planar / Normal-Based 결과를 Maya 의 Planar (Best Plane 아님) 와 비교 (회전·비율).

### Step 35 — Maya 키 묶음

- [ ] (step 35) Ctrl+Alt+LMB 박스 줌: 왼→오 확대 / 오→왼 축소 비율이 Maya 2022 와 비슷한지, 직교 뷰·카메라 뷰에서도.
- [ ] (step 35) F2–F6 메뉴 세트 전환이 3D 뷰 밖(Outliner, Graph Editor)에서도 되는지; 직교 뷰가 F 키에서 빠진 것이 불편하지 않은지 (핫박스·Space·Ctrl+F1–F3).
- [ ] (step 35) Y 가 Maya 처럼 마지막 툴(Multi-Cut, Quad Draw, Extrude 등)로 돌아가는지, 모드를 바꿨을 때 기억이 자연스러운지.
- [ ] (step 35) 3D 뷰에서 Enter 를 눌러도 아무 창이 뜨지 않는지, Knife / Poly Build 안에서는 Enter 가 확정인지.

### Step 36 — 대칭 (Symmetry)

- [ ] (step 36) Status Line ▾ → Object X 를 켠 뒤 정점·엣지·면을 Move/Rotate/Scale 기즈모로, 그리고 MMB 드래그로 옮기면 반대쪽이 Maya 2022 처럼 따라오는지 (가운데 seam 정점 포함). 소프트 선택(B)과 함께도.
- [ ] (step 36) 대칭을 켤 때 반대쪽 선택이 더해지는 것 (Maya SymmetrizeSelection) 이 자연스러운지; 켠 뒤 한쪽만 클릭해 고를 때 Maya 는 반대쪽도 하이라이트하지만 여기서는 안 함 (옮기면 같이 움직임) — 거슬리는지.
- [ ] (step 36) World X 를 회전한 오브젝트 / 원점이 월드 면 위에 없는 오브젝트에서 켰을 때 경고 문구가 이해되는지, 결과가 Maya 와 어떻게 다른지.
- [ ] (step 36) 대칭을 켠 채 다른 메시를 편집 모드로 열면 그대로 켜져 있는지 (Maya 처럼 전역), Blender 헤더의 X/Y/Z 미러 버튼을 눌렀을 때 Status Line 글자가 따라 바뀌는지.
- [ ] (step 36) W/E/R 홀드 → N Symmetry ▸ 하위 메뉴의 체크 상자 (Symmetry / World / Object / Topology / X·Y·Z Axis) 가 Maya 와 같은 자리·같은 동작인지. Topology 는 Blender 가 축 + 토폴로지로 짝을 찾는 것 (Maya 의 seam 엣지 고르기 없음).

### Step 37 — 뷰 패널 메뉴 바

- [ ] (step 37) 3D 뷰 헤더 View / Shading / Lighting / Show / Renderer / Panels 를 Maya 2022 패널 메뉴와 나란히 열어 보고 순서·이름·회색 항목이 낯설지 않은지. 헤더 메뉴 사이를 마우스로 옮겨 다닐 때 (메뉴 열린 채 옆 메뉴로) 자연스러운지.
- [ ] (step 37) Shading > Wireframe / Smooth Shade All, Lighting > Use All Lights (Material Preview + 씬 라이트) / Flat, Renderer > 엔진 이름 (Rendered) 이 Maya 사용자의 기대와 맞는지. 4분할 뷰에서 각 뷰 헤더 메뉴가 그 뷰에만 적용되는지 (Blender 4분할은 헤더가 하나 → 사용자 뷰에 적용).
- [ ] (step 37) Show > 종류 체크 (Polygons, Lights, Cameras, Joints, Locators …) 와 All / None, Isolate Select > View Selected (Ctrl+1 과 같음) 가 Maya 처럼 동작하는지.
- [ ] (step 37) Panels > Perspective / Orthographic 의 카메라 목록, Look Through Selected, Panel ▸ (편집기 바꾸기), Layouts ▸ 4분할, Tear Off… (새 창) 이 Maya 와 비슷한지. 헤더 메뉴를 접었을 때 (헤더 우클릭 > Show Menus 끔) 아이콘 하나로 모이는지.
- [ ] (step 37) Blender ▸ 아래 View / Select / Add / Object (편집 모드면 Mesh / Vertex / Edge / Face …) 가 Blender 사용자가 찾기에 충분한지. 환경설정 Panel Menus 를 끄면 Blender 메뉴로 돌아오는지.

### Step 38 — Channel Box 다중 선택·상대값, AE 재질 라벨

- [ ] (step 38) Channel Box 값 필드를 클릭해 숫자 입력 → Enter: Maya 처럼 바로 적용되는지. `+=5`, `-=2`, `*=2`, `/=2` 가 여러 오브젝트에서 오브젝트마다 자기 값 기준으로 적용되는지. 단위 없는 숫자 = cm (Maya Workflow Kit 레이아웃), `5 m` 도 되는지.
- [ ] (step 38) 채널 이름 여러 개 (Rotate X/Y/Z) 를 고르고 하나에 입력 → 고른 채널 모두에 적용; 고르지 않은 채널에 입력하면 그 채널만.
- [ ] (step 38) 필드 숫자가 단위 없이 보이는 것 (Maya 처럼 "1.5"), 필드 Ctrl+휠·드래그가 없어진 것 (값 끌기는 뷰포트 MMB 가상 슬라이더) 이 Maya 사용자에게 자연스러운지; Blender 사용자는 불편할 수 있음.
- [ ] (step 38) 여러 오브젝트에 같은 Bevel/Subdivision 모디파이어가 있을 때 INPUTS 값 입력이 모두에 적용되는지, 카메라 여러 개 선택 후 SHAPES Focal Length, 사용자 속성. 그 뒤 Ctrl+Z 한 번에 모두 되돌아가는지.
- [ ] (step 38) Lighting/Shading > Assign New Material > Lambert / Blinn / Phong → AE 탭 라벨 "lambert: lambert1" 과 Common Material Attributes / Specular Shading 섹션이 Maya 와 비슷한지.

### Step 39 — 컴포넌트 픽워크, Alt+Shift 축 고정

- [ ] (step 39) 편집 모드 정점/면에서 화살표 → 화면의 그 방향 이웃으로 옮겨 가는지 (원근 뷰에서 비스듬히 볼 때도), 갈 곳이 없으면 그대로인지. 키를 누르고 있으면 반복되는지.
- [ ] (step 39) 엣지에서 ←/→ = 엣지 루프를 따라, ↑/↓ = 엣지 링으로 (Maya 2022 와 같은지), 극점 (정점에 엣지 3·5개) 에서 멈추는지.
- [ ] (step 39) 여러 요소 선택 후 화살표 → 각자 걸음; Ctrl+Z 로 되돌아가는지. Maya 처럼 정점 인덱스 순서가 아니라 화면 방향인 것 (delegated) 이 Maya 사용자에게 괜찮은지.
- [ ] (step 39) Alt+Shift+LMB 드래그: 처음 움직인 방향 (가로/세로) 으로만 텀블되는지, 도중에 방향을 바꿔도 고정되는지. Alt+Shift+MMB 트랙도. ESC/RMB 취소로 원래 뷰. Maya 2022 와 감도 비교.
- [ ] (step 39) Alt+Shift+클릭 (드래그 없이) 이 이제 아무것도 선택하지 않는 것 (IC 의 토글 선택 제거) 이 불편하지 않은지.

### Step 42 — 켜자마자 Maya (환영 대화상자, Make Blender Maya)

- [ ] (step 42) 실제 설치 (환경설정 > Get Extensions > Install from Disk 로 zip) 직후 환영 대화상자가 커서 근처에 뜨는지, Blender 스플래시와 겹쳐도 "Make Blender Maya" 를 누를 수 있는지. 누르면 Maya 레이아웃, 스플래시 없음 (테마는 바꾸지 않음, step 130).
- [ ] (step 42) zip 을 Blender 창으로 끌어 놓아 설치해도 같은지. Cancel 을 누르면 다시 묻지 않고, 환경설정 > Add-ons > Maya Workflow Kit 맨 위 버튼으로 할 수 있는지.
- [ ] (step 42) Blender 를 껐다 켜면 (파일 없이) Maya 레이아웃으로 열리는지; .blend 를 더블클릭해 열면 그 파일이 그대로 열리는지; 세션 중 File > New > General 은 General 인지.
- [ ] (step 42) 다른 애드온 (예: Node Wrangler) 이 Make Blender Maya 전후로 그대로 켜져 있는지.

### Step 45 — Maya 그리드

- [ ] (step 45) Maya Workflow Kit 레이아웃 persp: 그리드가 ±12 cm 에서 끝나고 5 cm 마다 굵은 선, 축선도 굵은 회색 (빨강/초록 아님). 확대·축소·텀블해도 깜빡이거나 끊기지 않는지, 큐브가 그리드 뒤를 가리는지.
- [ ] (step 45) 사용자 정사영 (Numpad 5 로 바꾼 비스듬한 뷰) 에서는 바닥 그리드. (4 분할의 top / front / side 는 step 161 부터 각자 평면에 칸 끝까지 격자 — Maya 와 같음, `gui_step161_views`.)
- [ ] (step 45) X 홀드 + 이동: 그리드 안에서 사본이 그리드선에 붙는지; 멀리 축소하면 Blender 가 10 cm 단계로 붙는데 (Blender 그리드 단계) 그것도 그리드선 (10 의 배수) 인지. 정사영에서 아주 크게 확대하면 1 cm 보다 잘게 붙을 수 있음 — Maya 사용자에게 괜찮은지.
- [ ] (step 45) Show > Grid / Display > Grid: 끄면 그리드 없음, 다시 켜면 Maya 그리드. 오버레이 팝오버에서 Blender Floor 를 켜면 Blender 그리드로 바뀌는 것 (delegated) 이 헷갈리지 않는지.

### Step 46 — 뷰 가구 (ViewCube·축 삼각·카메라 라벨)

- [ ] (step 46) ViewCube: 마우스를 올리면 진해지고 가리킨 면이 하늘색, 면 클릭 → 그 방향 정사영 뷰 (부드러운 전환). 모서리·꼭짓점 클릭은 아직 없음 (Maya 는 있음) — 아쉬운지.
- [ ] (step 46) ViewCube 를 드래그해도 뷰가 돌지 않음 (Maya 는 큐브 드래그 = 텀블) — Alt+LMB 로 충분한지.
- [ ] (step 46) 4 분할: ViewCube 가 마우스가 있는 패널로 옮겨 가는지; 라벨 top -Y / persp / front -Z / side -X 가 각 패널 아래 가운데 (step 176: Maya 카메라 이름 그대로, 축 삼각대는 Blender Z-up 축).
- [ ] (step 46) 축 삼각이 텀블에 따라 돌고 x/y/z 글자가 Channel Box 축과 맞는지. 카메라 뷰 (Numpad 0) 에서 라벨이 카메라 이름인지.
- [ ] (step 46) Display > Heads Up Display > Camera Names / View Axis / View Cube 가 모든 뷰에서 켜고 끄는지.

### Step 47 — 선택 와이어

- [ ] (step 47) 오브젝트를 고르면 셰이딩 위에 모든 엣지가 연두 (리드) / 흰색 (나머지), 외곽선 없음. 해제하면 사라짐. Maya 와 선 굵기·밝기 비교.
- [ ] (step 47) 와이어가 면에 가려지는 뒤쪽 엣지는 안 보이고 앞쪽 엣지는 끊김 없이 보이는지 (아주 멀리 / 아주 가까이 확대해서도, cm 장면·m 장면).
- [ ] (step 47) 큰 메시 (수십만 폴리) 를 고를 때 잠깐 멈춤 (배치 만들기, 10 만 폴리 약 30 ms) 이 거슬리지 않는지; 편집 모드에서 나올 때도.
- [ ] (step 47) 스무스 프리뷰 3 에서 와이어가 케이지 엣지 (매끈한 면 밖에 뜸) 인 것이 Maya 와 비교해 괜찮은지.

### Step 49 — 레이아웃 동등화

- [ ] (step 49) Maya Workflow Kit 레이아웃: 위에서 아래로 메뉴바 / Status Line / Shelf / [툴박스 | Outliner | 뷰 | Channel Box 도크] / Time Slider / Range Slider / Help Line + Command Line 한 줄. Maya 를 옆에 띄워 놓고 배치가 같게 읽히는지.
- [ ] (step 49) 툴박스: Select·Lasso·Paint Select·Move·Rotate·Scale 가 오브젝트·편집·포즈 모드에서 같은 자리에 있고, 다른 툴 (Multi-Cut 등) 을 쓴 뒤 그 툴이 구분선 아래 마지막 칸에 나오는지. 툴 버튼 더블클릭·길게 누르기가 이상하지 않은지.
- [ ] (step 49) 툴박스 아래 빈 곳 클릭·드래그 → 선택이 그대로인지. 빠른 레이아웃 Single / Four 버튼, Outliner 버튼 (새 창), Front/Persp 는 회색.
- [ ] (step 49) Resolution Scale 을 1.0 보다 크게 하면: 툴박스 열이 한 열 폭으로 맞춰지거나 (마우스가 영역 경계를 지날 때) 그동안 메인 뷰에 툴바가 보이는지; Status Line·Shelf 두 줄이 잘리지 않는지.
- [ ] (step 49) Status Line 의 Attribute Editor 버튼 = 도크 AE 전환, Render Settings = Properties 새 창 (Render 탭).
- [ ] (step 49) 하단 줄: 왼쪽 Help Line (툴 도움말, 없으면 Blender 마우스 힌트·보고·진행), 오른쪽 Command Line. 오류 보고가 Help Line 칸에 보이는지.

### Step 50 — 에디터 크롬

- [ ] (step 50) Channel Box 메뉴 줄 Channels / Edit / Object / Show 가 열리고 항목이 동작하는지 (Edit > Settings ▸ 속도, Object 에서 리드 바꾸기, Show > All). 선택 없음 = Maya 문구.
- [ ] (step 50) Layer Editor: Display / Anim 탭, Layers 메뉴로 레이어 만들기·추가·삭제, 아이콘 버튼이 오른쪽. (step 182: Anim 탭은 글이 아니라 Maya 애니메이션 레이어 목록 — 손 확인은 「Step 180」 절.)
- [ ] (step 50) Outliner 머리 Display / Show / Help: Show 의 종류 필터, Display > Shapes 를 켜면 Blender Outliner 머리로 돌아오는 것 (delegated) 이 괜찮은지. 눈 열이 없는 것 (H 로 숨김) 이 불편하지 않은지.
- [ ] (step 50) Time Slider 오른쪽 현재 프레임 칸 + 재생 버튼 8 개, Range Slider 줄 순서가 Maya 와 같게 읽히는지; 범위 막대를 누르면 타임라인이 재생 범위에 맞춰지는지; 오른쪽 끝 톱니 = Playback / Keying / View / Marker.

### Step 51 — 메뉴 옵션 박스·셸프 줄

- [ ] (step 51) Maya 메뉴 (Create, Edit Mesh 등) 에서 라벨 끝에 ❒ 가 있는 항목: 클릭 = 명령, 길게 누르기 → 「Option Box ❒」 줄 → 그 항목의 옵션 창 (step 103 / 146; "redo" 종류만 Adjust Last Operation). Maya 의 □ 클릭 습관과 비교해 길게 누르기가 불편하지 않은지 (같은 줄 버튼 두 개는 메뉴가 계단처럼 깨져 못 씀).
- [ ] (step 51) 셸프 줄 = 탭 줄 (어두운 #373737, 고른 탭 밝게) + 32 px 컬러 아이콘 줄. 아이콘에 마우스 = 칸 강조 + 툴팁, 클릭 = 명령, 0.35 s 안 두 번째 클릭·Ctrl+클릭 = 옵션. 탭 바꾸기, 톱니 = 셸프 설정 (새 셸프·버튼 추가·마지막 명령 추가).
- [ ] (step 51) kit 아이콘이 무엇인지 읽히는지 (기본 도형·도구 기호, 기호 없는 버튼은 셸프 색 + 글자 두 개). Maya 아이콘과 헷갈릴 만큼 비슷하지 않은지 (결정 6).
- [ ] (step 51) Resolution Scale 을 바꾼 뒤 마우스가 셸프 줄 아래 경계를 지나면 셸프 줄이 64 px × 배율로 돌아오는지.
- [ ] (step 51) Status Line 그룹 앞 세로 그립 (Maya openBar) 을 누르면 그 그룹이 접혀 ▸ 만 남고, 다시 누르면 펼쳐지는지. 그립이 너무 작거나 눈에 안 띄지 않는지.

### Step 52 — 핫박스·RMB 마킹 메뉴

- [ ] (step 52) Space 길게: 위 2 줄 (공통 + Cache/Help, View … Panels), 커서 줄 Recent Commands | Maya | Hotbox Controls, 아래 5 줄 (메뉴 세트 모두), 대각선 4 개. 커서가 사이드바 근처여도 줄이 접히지 않고 Channel Box 위에 그려지는지, 그 위의 메뉴 이름을 눌러 열리는지.
- [ ] (step 52) Hotbox Controls 에서 「Show All Menu Sets」 를 끄면 현재 세트 줄만 나오는지.
- [ ] (step 52) 오브젝트 위 RMB: 링 아래 (자리가 없으면 옆) 목록 첫 줄 「pCube1...」 (누르면 AE 도크에 그 오브젝트), Select … Invert Selection, Select Similar □ (옵션 = `menu_sets.option_kind` 에 따름, step 103 / 147), DG Traversal / Inputs / Outputs ▸ = 노드 목록 (step 165, 회색 아님), 재질 항목. 목록은 한 열로 링 아래 (링 아래에 안 들어가면 링 옆 한 열, 링은 언제나 누른 점 — step 193 규칙) 이고 모든 항목에 닿는지.

### Step 53 — Blender 5.x 와 안전한 설치

- [ ] (step 53) 쓰던 Blender (애드온 몇 개, 바꾼 키·탐색 설정) 에 kit 을 설치: 기존 애드온이 그대로 켜져 있고, kit 을 끄면 키맵·탐색·undo 설정이 설치 전과 같은지.
- [ ] (step 53) Blender 5.0–5.2 에서 kit 을 켜고 Maya 레이아웃: Status Line·셸프·툴박스·Channel Box·핫박스가 4.5 와 같게 보이는지, Range Slider 줄의 재생 버튼, 킷이 그리는 뷰포트 색 (선택 와이어 · 그리드 · 컴포넌트, step 134; 위젯은 사용자 테마).
- [ ] (step 53) kit 을 켠 채 Graph Editor (Alt+MMB/Alt+RMB, A/F, 키 클릭), Node Editor, Text Editor (z/h/Space 입력) 가 평소대로인지.
- [ ] (step 53) Blender 5.3 이상에 설치하면 확장 관리자가 「호환 안 됨」 을 분명히 보여 주는지.

### Step 54 — 단위 생성 경로·조명 세기·「Blender 에 없음」 안내

- [ ] (step 54) Maya Workflow Kit 레이아웃에서 Skeleton > Create Joints, Create > Type, Create > Free Image Plane, Fields/Solvers 필드들이 pCube1 (1 단위) 과 같은 크기 감으로 원점에 생기는지. Gravity 필드 화살표가 아래를 향하는지.
- [ ] (step 54) Create > Lights > Point/Spot/Area 를 pCube1 에서 Maya 습관 거리 (5–10 단위) 에 두고 렌더 미리보기 밝기가 Maya 의 No Decay 기본 (step 137: Cycles 정확, EEVEE · 뷰포트는 10 단위에서 맞춤) 과 비슷한지. 감쇠 안내는 Command Line 결과 칸에 "Created pointLight1. …" (step 161).
- [ ] (step 54) Windows > Animation Editors > Trax / Time Editor, Relationship Editors > Character Sets (Animation Layers 는 step 188 부터 Layer Editor Anim 탭 — step 192 에서 문구 고침), Windows > Node Editor, Rendering Editors > Light Editor, Skeleton > HumanIK / Quick Rig, File > Create Reference / Set Project 위에 마우스: 툴팁과 Help Line 의 안내 문구가 이해되는지, 대체 항목은 눌렀을 때 대체 편집기가 열리는지.
- [ ] (step 54) Fluids > 3D Container / Effects > Smoke 를 메시 선택 후: 도메인이 메시 둘레에 Maya 단위로 알맞게 (cm 템플릿에서 2 m 상자가 아님).

### Step 55 — 포즈 본 = Maya 조인트 (CB·Outliner·AE·제약 가중치)

- [ ] (step 55) Skeleton > Create Joints 후 오브젝트 모드에서 아마추어를 고르면 CB 머리 아래 「Joint channels: Ctrl+Tab (pose mode)」; Ctrl+Tab → 포즈 모드, 뷰에서 조인트 클릭 = CB 머리가 조인트 이름, Translate/Rotate/Scale/Visibility 행. 아무 조인트도 안 고르면 빈 CB 문구.
- [ ] (step 55) 조인트 두 개를 고르고 Rotate Z 칸에 `+=10` = 둘 다 각자 값에서 10° 더. 채널 이름 Shift+클릭으로 Rotate X–Z 를 고르고 Channels > Lock Selected → 뷰에서 E 로 돌려도 안 돌고, Key Selected 키가 Graph Editor 에 `joint2` 그룹으로 보이는지. MMB 드래그 (가상 슬라이더) 가 고른 조인트 채널을 바꾸는지.
- [ ] (step 55) Blender 로 만든 본 (쿼터니언) 을 고르면 「Rotation mode QUATERNION」 + 「Rotate Order XYZ」 버튼; 누르면 자세 그대로 Rotate X/Y/Z 행이 나오는지.
- [ ] (step 55) 조인트에 Copy Location (대상 locator1) 제약: CB INPUTS 에 `joint2_pointConstraint1` 과 `locator1W0`, Translate 칸이 파랑 (눌린 버튼 색) 으로 Maya 의 제약 채널처럼 읽히는지; W0 에 0.5 → 조인트가 반만 따라감. 제약 체크를 끄면 파랑이 사라지는지.
- [ ] (step 55) 사이드바 Outliner (Dock Only 끔): skeleton1 ▸ 를 펼치면 joint1 ▸ joint2 ▸ joint3 계층, 조인트 행 클릭 = 포즈 모드 + 그 조인트, 오브젝트 행 클릭 = 오브젝트 모드로 돌아가 선택. 레이아웃의 Outliner (Blender 트리) 는 Display > Shapes 를 켜야 본이 보임.
- [ ] (step 55) AE (Ctrl+A) 에서 조인트: joint 탭 + 제약 노드 탭, Transform Attributes / Joint (Joint Orient 읽기 전용, 축 안내) / Limit Information (Add Limit Rotation 이 조인트에 붙음) / Display (Display as Control Shape). 아마추어 편집 모드에서는 CB·AE 에 「Placing joints」 한 줄.

### Step 56 — Time Slider·키 감각

- [ ] (step 56) Maya Workflow Kit 레이아웃 Time Slider 아무 곳 LMB 클릭·드래그 = 시간 이동 (키를 집어 옮기지 않음), Dope Sheet 창 본문 LMB 는 여전히 키 선택.
- [ ] (step 56) Time Slider Shift+LMB 드래그 = 빨간 범위 띠; 그 상태로 RMB > Copy / Delete 가 범위의 키에, 보통 클릭으로 띠가 사라지는지. 범위 띠가 Maya 처럼 읽히는지 (색·투명도).
- [ ] (step 56) Time Slider RMB 메뉴: Cut/Copy/Paste ▸/Delete/Snap/Keys ▸/Tangents ▸/Playback Speed ▸/Playback Looping ▸/Set Range to ▸/Playblast... 순서, 회색 항목 (Paste Connect, Free, Once/Oscillate) 툴팁 안내. 현재 프레임 Copy → 다른 프레임 Paste.
- [ ] (step 56) K 누른 채 뷰 (또는 Graph Editor) 에서 LMB 드래그 = 시간 이동, 속도가 너무 빠르거나 느리지 않은지 (영역 폭 = 재생 범위), 놓은 뒤 선택 그대로. 편집 모드 K 가 더 이상 Knife 가 아님 (Multi-Cut = Ctrl+Shift+X).
- [ ] (step 56) S = 가시성·커스텀 속성까지 키 (Graph Editor 채널 목록), Channel Box 에서 숨긴/Nonkeyable 채널은 안 찍힘. Key > Set Breakdown Key = 초록 (breakdown) 키. Key > Delete Keys = 선택의 모든 키.
- [ ] (step 56) Channel Box 채널 이름·값 칸 RMB = 메뉴 맨 위에 Key Selected … Make Selected Nonkeyable (아래는 Blender 버튼 메뉴).
- [ ] (step 56) 타임라인 MMB = 시간 이동 + Help Line 안내 문구 (Maya MMB 시간 드래그는 Blender 에 없음).

### Step 57 — Joint Tool·Orient/Mirror Joint·포즈 픽워크

- [ ] (step 57) F3 → Skeleton > Create Joints → front 뷰 (정사영) 에서 세 번 클릭 → Enter: 클릭한 자리에 joint1 > joint2 > joint3, 포즈 모드, CB joint3. persp 뷰 클릭은 바닥에 놓임. 놓는 동안 Alt+드래그 텀블·휠 줌이 되는지, 상태 표시줄 안내.
- [ ] (step 57) 놓는 중 기존 조인트에서 가지 치기: 편집 모드에서 조인트 하나 고른 뒤 Create Joints → 그 조인트 아래로 이어짐.
- [ ] (step 57) Skeleton > Orient Joint (옵션 창): Secondary World Orientation Y+ / Z+ 로 바꿔 보고 로컬 축 (Display > Local Rotation Axes 또는 아마추어 Axes) 이 기대대로 도는지; 창의 Y 축 안내 문구가 이해되는지.
- [ ] (step 57) Skeleton > Mirror Joints (옵션 창) YZ + Search `l_` Replace `r_`: 반대편에 `r_…` 조인트, Behavior 로 미러한 팔을 반대로 돌렸을 때 Maya 처럼 대칭으로 움직이는지.
- [ ] (step 57) 포즈 모드 ↑↓←→ = 부모 / 자식 / 형제 조인트 (프레임은 Alt+, / Alt+.), P = 고른 조인트들을 마지막에 고른 조인트 아래로 (제자리), Shift+P = 부모 끊기.

### Step 58 — IK Handle·Bind Skin·Paint Skin Weights

- [ ] (step 58) Skeleton > Create IK Handle → 시작 조인트 클릭 → 끝 조인트 클릭: ikHandle1 이 끝 조인트에 생기고 선택됨, W 로 끌면 체인이 굽음. 조인트를 잘못 (끝 → 시작) 고르면 경고. 이미 두 조인트를 고른 상태면 바로 만들어짐.
- [ ] (step 58) 로케이터 → ikHandle1 순서로 고르고 Constrain > Pole Vector: 무릎이 튀지 않고, 로케이터를 옮기면 무릎 방향이 따라감.
- [ ] (step 58) 조인트 (skeleton1) 클릭 → Shift+메시 클릭 → Skin > Bind Skin: 메시가 Outliner 에서 skeleton1 아래로 들어가지 않음, 조인트를 돌리면 메시가 따라 굽음. 길게 누르기 (Option Box) 로 Max Influences / Selected Joints 를 바꿔 다시 실행.
- [ ] (step 58) Skin > Paint Skin Weights: 도크 맨 위 Paint Skin Weights Tool (Influences 목록·Replace/Add/Scale/Smooth·Value·Opacity·Flood), 목록 클릭 = 칠할 조인트, Ctrl+LMB 로 뷰의 조인트 고르기, 다시 메뉴 = 도구 끄기. 색은 Blender 웨이트 색 (파랑→빨강, Maya 흑백 아님).
- [ ] (step 58) Mirror Skin Weights (Mirror Joints 로 만든 반대편 조인트가 있을 때) → 반대편 가중치가 대칭으로; Copy Skin Weights (원본 → 대상), Copy / Paste Vertex Weights (편집 모드).

### Step 59 — 피벗 · 스냅 · 매니퓰레이터 모양

- [ ] (step 59) Move 툴 매니퓰레이터가 Maya 처럼 읽히는지: 얇은 축 + 원뿔, 가운데 빈 사각, 평면 핸들 (XY 파랑·YZ 빨강·XZ 초록), 크기 (Maya 와 같은 화면 크기, 줌인/아웃 해도 그대로), 축·평면 핸들을 잡기 쉬운지 (선이 얇아도 잡힘).
- [x] (step 59) 축을 한 번 끈 뒤 그 축이 노랗게 남는지 (활성 핸들), MMB 아무 데나 드래그 = 그 축; 가운데 사각 드래그 = 화면 평면 자유 이동. (gui_manual_sweep)
- [ ] (step 59) Scale 툴: 끝 큐브 + 노란 가운데 큐브 (균일 스케일) + 평면 핸들. Rotate 툴은 Blender 링 (Maya 배치·색) — 차이가 거슬리는지.
- [x] (step 59) D 누른 채 매니퓰레이터 끌기 = 피벗만 이동 (Channel Box Translate 그대로, 형상·자식 그대로), 작은 링 = 피벗 방향 (Move 축이 「Maya Pivot」 방향으로), 놓은 뒤 E 회전이 새 피벗 둘레로. Insert 토글도 같은지. Ctrl+Z 한 번 = 피벗 이동 전. (gui_manual_sweep)
- [x] (step 59) D + X / V: 피벗이 그리드 선 / 정점에. Modify > Bake Pivot (방향 → Rotate 채널, 형상 그대로), Tool Settings 의 Reset (피벗 = 오브젝트 원점), Match Transformations > Match Pivots. (gui_manual_sweep)
- [x] (step 59) X 누른 채 드래그 (시작 0.3 cm) → 정수 cm 만, V 누른 채 가운데 핸들 → 다른 오브젝트 정점에 피벗이 붙음, Status Line 의 스냅 버튼이 키를 누른 동안 눌림. (gui_manual_sweep)
- [x] (step 59) 여러 오브젝트 선택: 매니퓰레이터가 마지막 선택 (lead) 피벗에, 컴포넌트 선택: 선택의 바운딩 박스 중심에 (편집 모드로 들어가면 Pivot 이 Bounding Box Center 로 바뀜). (gui_manual_sweep)
- [x] (step 59) Status Line / W 메뉴 「Move Options」 Tool Settings: Move Settings (Axis Orientation, Pivot, Step Snap Off/Relative/Absolute, Retain Component Spacing, Edit Pivot/Reset/Bake). W 메뉴 World/Object/Component 가 Move 축만, E 메뉴가 Rotate 축만 바꾸는지; E 메뉴 Discrete Rotate = 15° 스텝. (gui_manual_sweep)
- [x] (step 59) Modify > Snap Align Objects: Point to Point (편집 모드에서 두 오브젝트의 정점 — 움직일 쪽 먼저, 목표 오브젝트가 활성), 2/3 Points (방향까지), Align Objects (X 가운데 정렬). Snap Together Tool: 움직일 면 클릭 → 목표 면 클릭 → 면끼리 맞닿음. Make Live: 선택한 참조 메시를 뷰포트에서 선택할 수 없고 Status Line 칸에 이름이 표시됨. 빈 선택으로 다시 = 해제. 일반 스냅 설정은 유지됨. (gui_manual_sweep)

### Step 60 — Maya ⇄ Blender 스위치 · 완전 되돌리기

- [ ] (step 60) 상단 바 오른쪽 「Maya | Blender」 스위치가 두 모드 모두에서 보이고, 클릭 한 번에 재시작 없이 바뀌는지 (키맵·메뉴·Status Line·Shelf·Channel Box). 바뀌는 데 걸리는 시간이 거슬리지 않는지.
- [x] (step 60) Ctrl+Alt+Shift+M 로 같은 전환 (어느 에디터 위에서든). Blender 모드에서 F3 (메뉴 검색) 「Switch to Maya」, Maya 모드에서 Windows > Switch to Blender. (gui_manual_sweep — F3 = Blender 메뉴 검색이 찾는 Edit 메뉴 항목으로 확인)
- [x] (step 60) 작업 중인 파일 (오브젝트·애니메이션·저장 경로) 이 전환 전후 그대로, Blender 로 돌아오면 원래 워크스페이스 (Layout 등) 가 다시 열리고 「Maya」 워크스페이스는 사라짐. 그 파일을 저장해도 Maya 레이아웃이 남지 않는지. (gui_manual_sweep)
- [x] (step 60) 내 키 수정 (Preferences > Keymap 에서 바꾼 키), 내 테마, 다른 애드온, 회전 방식 등을 바꿔 둔 설정에서 Maya → Blender: 전부 그대로. Maya 모드 중에 바꾼 다른 설정 (Maya 가 건드리지 않는 것) 도 그대로. (gui_manual_sweep)
- [ ] (step 60) Maya 모드인 채 Blender 를 닫고 다시 열기 → Maya 모드 그대로, 그다음 Blender 로 → 원래 설정. Maya 모드에서 작업 관리자로 강제 종료 → 다시 열어서 Blender 로 전환 → 원래 설정.

### Step 61 — 배포 경로 (공개 전, 실제 Blender 창에서)

- [ ] (step 61) `python tools/build_repo.py` 로 만든 `dist/repo/index.html` 을 브라우저로 열고, 링크를 Blender 창에 끌어 놓기 → 설치 + 저장소 등록, 이후 Get Extensions 에 업데이트가 보이는지 (테스트용 Blender 설정에서).
- [ ] (step 61) Preferences > Get Extensions > Repositories > + > Add Remote Repository 에 `file:///…/dist/repo/index.json` → 검색 → Install → 「Check for Updates on Startup」 켜고 다음 시작에 상태 표시줄 알림.
- [ ] (step 61) (exe 를 만들기로 하면) Inno Setup 으로 `tools/installer/allset.iss` 컴파일 → 서명 없는 exe 의 SmartScreen 화면, Blender 버전 선택 페이지, 제어판 제거 뒤 원래 설정.

### Step 62 — Set Driven Key · 포즈 모드 제약 · Add Attribute · Blend Shape · Quick Rig

- [x] (step 62) Key > Set Driven Key > Set... → 사이드바 Channel Box 아래에 Driver / Driven 목록 + Key · Load Driver · Load Driven · Close. Maya 처럼 드라이버 선택 → CB 채널 클릭 → Load Driver, 피동 선택 → CB 채널 → Load Driven → Key → 드라이버 값·피동 값 CB 입력 → Key → 드라이버를 움직이면 피동이 따라옴 (CB 피동 행 = 드라이버 표시). (gui_manual_sweep)
- [x] (step 62) SDK 창이 열려 있을 때 피동 채널을 CB 로 바꾸면 값이 남고 (Key 전까지), 창을 닫으면 Key 하지 않은 포즈는 커브 값으로 돌아감. 매니퓰레이터로 피동 채널을 돌리면 Blender 가 드라이버로 되돌림 (CB 로 입력 — 안내대로인지). (gui_manual_sweep)
- [x] (step 62) Key > Set Driven Key > Go to Previous / Go to Next 가 드라이버 값을 이웃 키로 옮기는지. Graph Editor (Drivers) 에서 커브 모양 (Maya 의 SDK 커브와 같은 매끈한 S 자, 끝은 평평). (gui_manual_sweep)
- [x] (step 62) 컨트롤 선택 → 아마추어 Shift 선택 → Ctrl+Tab (포즈 모드) → 조인트 선택 → Constrain > Orient: 제약이 본에 붙고 (Bone Constraints 탭) 아마추어 오브젝트에는 없음. 대상이 없으면 Help Line 에 「Select the control first, then the joint last」. (gui_manual_sweep)
- [x] (step 62) Modify > Add Attribute... (Attributes 절) / CB Edit > Add Attribute: 이름·Float/Integer/Boolean·Min/Max/Default → CB 에 Maya nice name 행 (fingerCurl → Finger Curl), 범위 밖 입력이 잘림. Edit Attribute (이름 바꾸기 → 키가 따라감), Delete Attributes (선택 채널). (gui_manual_sweep)
- [x] (step 62) 머리 복제 → 수정 → 타깃·베이스 순서 선택 → Deform > Blend Shape: 베이스에 Basis + 타깃 이름 셰이프 키 (값 0), CB SHAPES. 정점 수가 다르면 오류 문구. (gui_manual_sweep)
- [ ] (step 62) Skeleton > Quick Rig: Rigify 가 꺼져 있으면 확인 대화상자 → 켜고 사람 메타 리그 추가; 툴팁·Help Line 의 Rigify 안내. HumanIK 는 회색 + 같은 안내.

### Step 63 — Modeling Toolkit · 소프트 선택 Maya 단위 · Combine / Separate / Mirror / Boolean

- [ ] (step 63) Status Line 오른쪽 편집기 토글 맨 앞 (MTK) 아이콘 / Windows > Modeling Editors > Modeling Toolkit / Mesh Tools > Show/Hide Modeling Toolkit → 사이드바 도크가 Modeling Toolkit; 다시 누르면 Channel Box. modeling_03.png 와 순서·묶음이 같은지 (선택 모드 아이콘, "N faces selected", Pick/Marquee · Drag · Tweak/Marquee, Symmetry, ▸Soft Selection, ▾Mesh, ▾Components, ▾Tools).
- [x] (step 63) MTK 버튼: Extrude (면 선택 → 바로 압출 + Move 매니퓰레이터, 드래그해서 뺌), Bevel, Bridge, Add Divisions, Multi-Cut, Connect, Quad Draw, Combine, Separate, Smooth, Boolean. 회색 (Highlight Backfaces, Selection/Transform Constraint, UV, Target Weld) 은 툴팁·Help Line 에 안내. (gui_manual_sweep)
- [x] (step 63) Camera Based Selection 을 켜면 편집 모드 마키가 보이는 것만 선택, 끄면 뒤쪽까지 (Maya 기본 꺼짐). Highlight Nearest Component 끄면 호버 강조 없음. (gui_manual_sweep)
- [x] (step 63) B 탭으로 소프트 선택 켤 때 반경이 Maya 기본 5 (cm 템플릿 = 5 cm), B+드래그 머리글이 Maya 단위, MTK Soft Selection 의 Falloff radius 가 같은 숫자; Volume / Surface; Reset. (gui_manual_sweep)
- [x] (step 63) pCube1 + pSphere1 선택 → Mesh > Combine → pCube2 하나, Channel Box Translate 0, 피벗이 둘을 합친 상자 중심. Mesh > Separate (오브젝트 모드) → pCube2 그룹 아래 polySurface1 / polySurface2 (Translate 0). 편집 모드 Separate = Blender 그대로. (gui_manual_sweep)
- [x] (step 63) Mesh > Mirror (클릭 = 지난 설정), 메뉴를 누른 채 □ = Mirror Options 창 (Cut / World·Object·Bounding Box / Offset / X·Y·Z / + − / Combine / Merge / Threshold). 원점이 아닌 곳의 큐브에 World X − → 오른쪽 반을 잘라 왼쪽으로, 경계 병합. Mesh > Booleans 세 가지 (먼저 선택한 것 − 나중 것). (gui_manual_sweep)

### Step 64 — Target Weld · Crease Tool · Multi-Cut 감각

- [x] (step 64) Mesh Tools > Target Weld (또는 Shift+RMB N / 정점 Merge▸S / 엣지 Merge▸S / 셸프 Polygons / MTK Tools) → 편집 모드 + Target Weld 툴, Help Line 안내. 정점 위에서 LMB 누르고 끄는 동안 노란 고무줄 선 + 목표 정점 빨간 점, 놓으면 그 정점으로 병합. 정점 근처가 아닌 곳의 드래그 = 마키 선택 (fallback). ESC/RMB = 취소. (gui_manual_sweep)
- [x] (step 64) 정점 모드에서 이 툴이면 마우스 아래 정점이 빨갛게 강조 (pre-selection). 정점 둘을 선택하고 그중 하나를 끌면 둘 다 목표로 병합 (Maya 설명문), 선택 안 된 정점을 끌면 그것만. (gui_manual_sweep)
- [x] (step 64) Tool Settings (툴 헤더 / Status Line Tool Settings): Merge To Target / Center, Preserve UVs. Center = 중간에서 병합. 엣지 모드: 엣지를 다른 엣지에 끌면 두 끝이 짝지어 병합 (이웃 엣지면 공유 정점은 그대로). Adjust Last Operation 에서 Merge To 바꾸기. (gui_manual_sweep)
- [ ] (step 64) Mesh Tools > Crease Tool: 엣지 선택 → MMB 를 오른쪽으로 끌면 머리글 "Crease Mode: Absolute   Crease Value: n.nn (Blender b)" 가 오르고 왼쪽은 내려감, 3 (스무스 프리뷰) 에서 각이 살아남. 놓기 = 확정 (Ctrl+Z 한 번), ESC = 원래 값. Relative 모드는 엣지마다 더함. 정점 모드면 정점 crease. 메뉴 툴팁 / Help Line 의 0–1 안내. 감도 (50 px = Maya 1) 가 Maya 와 비슷한지.
- [x] (step 64) Multi-Cut (Ctrl+Shift+X): Ctrl+클릭 = 클릭한 자리 비율로 엣지 루프 (삼각형/경계에서 멈춤), Ctrl+MMB = 가운데, Ctrl+Shift+클릭 = Snap Step 자리. Adjust Last Operation 의 Position 으로 옮기기. Shift+클릭 = 커서가 가장 가까운 Snap Step % 점으로 옮겨지며 거기서 자르기 시작; 자르는 중 Shift = 엣지 중점 스냅 (Maya 의 10 % 단계 대신 50 % 만). Tool Settings 에 Snap Step % + 회색 Maya 항목 (Smoothing Angle · Edge Flow · Subdivisions · Slice Tool, 툴팁 안내). (gui_manual_sweep)

### Step 65 — Extrude 매니퓰레이터 · In-View Editor · 마지막 연산 INPUTS

- [ ] (step 65) 면 선택 → Ctrl+E (또는 Edit Mesh > Extrude / Shift+RMB Extrude Face / 셸프 / MTK Extrude): 모양은 그대로 (길이 0 압출), 면 가운데에 파란 화살표 + 오른쪽에 In-View Editor 상자 (제목 polyExtrudeFace1, Thickness · Local Translate Z · Offset · Divisions · Keep Faces Together) — modeling_03.png 와 비교. Move 툴의 매니퓰레이터는 그동안 숨음.
- [x] (step 65) 화살표를 끌면 면이 법선 방향으로 따라오고 In-View / Channel Box 의 Local Translate Z 가 같이 바뀜; 놓으면 Ctrl+Z 한 번으로 되돌아감, ESC/RMB = 취소. (gui_manual_sweep)
- [x] (step 65) In-View 행을 옆으로 끌기 = 값 (Ctrl 미세, Shift 크게), 끌지 않고 클릭 = 값 입력 창, Keep Faces Together 클릭 = 토글 (두 면 압출에서 차이). 호버 / 마지막 행 이름이 노랑. (gui_manual_sweep)
- [x] (step 65) Channel Box INPUTS 맨 위 polyExtrudeFace1 + 다섯 행 (`0.5`, `+=0.25` 입력), 아래 회색 안내 「Blender keeps no edit-mode history」. Divisions 2 → 옆면 고리 2 개 (modeling_04.png). Ctrl+Z / Ctrl+Shift+Z 에 행 값이 따라감. 정점을 손으로 옮기거나 다른 연산을 하면 행이 사라짐 (마지막 하나만). (gui_manual_sweep)
- [x] (step 65) 다른 면을 선택하면 화살표·In-View 가 사라지고 Move 매니퓰레이터가 돌아옴 (INPUTS 행은 남음). F9 (Adjust Last Operation) 에 같은 Maya 이름 속성. 엣지/정점 선택에서 Ctrl+E = 예전처럼 압출 + 법선 드래그. (gui_manual_sweep)

### Step 66 — UV 워크플로우

- [x] (step 66) 큐브 선택 → UV > UV Editor (또는 Windows > Modeling Editors > UV Editor / F12 / 3D RMB E 「UV」): UV Editor 창이 하나 열리고 (다시 해도 새 창 안 생김) 큐브가 편집 모드, UV 가 바로 보임. F12 = UV (Sync 끔, 정점), Alt+F12 = UV Shell (섬) — 이때 3D 뷰에는 면이 모두 선택돼 보임 (안내대로인지). (gui_manual_sweep)
- [ ] (step 66) UV Editor RMB 길게 = 마킹 메뉴 (N Edge, S Face, W Vertex, E UV, NW UV Shell + 아래 Cut/Sew/Unfold/Layout 목록), Shift+RMB = UV 도구 (UV 모드) / UV Shell 도구 (섬 모드) — Maya 와 위치 비교.
- [x] (step 66) 3D 뷰에서 에지 고리 선택 → UV Editor 에서 Shift+X: 빨간 솔기 + 셸이 그 자리에서 나뉨 (섬 선택으로 한쪽만 잡히는지), Shift+S: 작은 셸이 엣지에 붙어 하나로. Ctrl+U: 셸 자리 그대로 펴짐 (Unfold3D 와 모양 차이 안내), Ctrl+L: 0–1 안에 겹침 없이, 셸끼리 같은 텍셀 밀도. (gui_manual_sweep)
- [ ] (step 66) UV Editor 사이드바 「UV Toolkit」 탭 (Ctrl+휠): uv_01_win1 순서, 컴포넌트 아이콘·Pick/Drag/Tweak·All/Clear/Inverse·접는 절. Transform > Texel Density: 큐브 Get → 값 (px/cm, 맵 1024), 다른 크기 큐브에서 Set → 같은 밀도. 회색 항목 툴팁 안내.

### Step 67 — Hypershade · Light Editor · Render 메뉴 · Keep Image · AE 맵 버튼

- [ ] (step 67) Windows > Rendering Editors > Hypershade, Status Line 재질 아이콘, 핫박스 Windows 메뉴 셋 다 같은 새 창 (Shader Editor + 사이드바 「Hypershade」 탭 활성) — render_01_win1 과 구성 비교 (Browser 위, Create, Property Editor). 핫박스 N 존 Hypershade 레이아웃은 여전히 Shading 워크스페이스.
- [x] (step 67) Browser 격자 미리보기가 렌더된 뒤 보이는지, 클릭 = 그래프 + Property Editor 가 그 재질 (오브젝트에 없는 재질이면 핀 아이콘 켜짐). Create 버튼 = 할당 없이 새 재질 (저장 후 다시 열어도 남음). Assign Material To Selection = 선택에, 면 선택 모드면 그 면에. (gui_manual_sweep)
- [x] (step 67) AE (독 / Hypershade Property Editor) 재질 행 오른쪽 체커 버튼 → 팝업 Create Render Node: File / Ramp / Noise / Checker → 노드가 그래프 왼쪽에 생기고 연결, 행이 「connected (…)」 + File 이면 이미지 New/Open. 연결된 행 버튼 = Break Connection (노드는 남음). 툴팁에 Maya 속성 이름 (baseColor 등). Normal 은 Bump 노드 경유. (gui_manual_sweep)
- [x] (step 67) Rendering 메뉴셋 (F6) Render 메뉴: Render Settings… / Render Using (엔진 목록) / … / Render Current Frame / Redo Previous Render / IPR … / Render Sequence / Batch Render (회색, 툴팁 「blender -b」). Render Current Frame → Render Result 창, 헤더 왼쪽 Render · Keep Image · Remove Image · 「Slot N · k kept」. (gui_manual_sweep — 헤더 왼쪽 위치는 draw 순서로 확인)
- [x] (step 67) Keep Image → 다시 렌더 → 새 슬롯에 그려짐, J / Alt+J 로 이전 이미지와 비교 (Maya Render View 아래 스크롤바 대신). Remove Image = 지금 슬롯 비움. (gui_manual_sweep)
- [ ] (step 67) Windows > Rendering Editors > Light Editor: 3D View 창, 사이드바 「Light Editor」 탭 활성, 표 (이름 · 색 · Intensity · 켜기 · Solo), 위 라이트 만들기 아이콘 — render_03_win1 비교. 이름 클릭 = 선택 (Shift 추가), Solo = 나머지 꺼짐 (뷰포트 Rendered 에서 확인), 다시 = 복구. 아래 Property Editor = 선두 라이트 AE 섹션 + Translate/Rotate/Scale.
- [ ] (step 67) Render > Render Settings… / Status Line 톱니 / Windows > Rendering Editors > Render Settings: 새 Properties 창이 Render 탭으로 열리고 (render_04_win1 비교), 원래 화면의 AE (독 또는 Properties) 는 그대로. AE 라이트 (Point/Spot/Area) 에 회색 Decay Rate: Quadratic 행.

### Step 68 — FX (시뮬레이션 스케일 · nucleus · 이미터 · nCloth · nCache)

- [ ] (step 68) Maya Workflow Kit 레이아웃에서 F5 → nParticles > Create Emitter: 아웃라이너에 emitter1, 재생 (Alt+V) → 원점에서 점들이 나와 떨어지는 빠르기가 Maya (fx_01.png) 와 비슷한지 (1 초에 약 5 유닛). 점이 큰 공이 아니라 작은 점으로 보이는지.
- [x] (step 68) 메시 둘 선택 → Emit from Object: 둘 다 정점에서 방출. Shelf FX 「Emitter」 = Create Emitter, 「Add Emitter」 = Emit from Object. (gui_manual_sweep)
- [ ] (step 68) Create > Plane (위로 올림) → nCloth > Create nCloth → 처음 프레임부터 재생: Maya fx_02→03 처럼 1 m 천 같은 빠르기로 떨어지고 주름. 바닥 평면 Create Passive Collider 위에서 0.2 유닛 정도 위에 멈춤 (1.5 유닛 위에 뜨지 않음). 두 평면을 같이 선택하면 둘 다 천.
- [x] (step 68) AE 「nucleus1」 탭 (천·파티클·콜라이더·강체 오브젝트): Gravity 19.6 → 더 빨리 떨어짐, Space Scale 0.01 → 실제 1 cm 물리 (아주 빠르고 뻣뻣), Substeps 6 → 천 품질 10. 안내 글. (gui_manual_sweep)
- [x] (step 68) nCache > Create New Cache > nObject → 타임라인에 구운 캐시 (주황 → 확정), 선택 없으면 장면 전체; Delete Cache → 다시 시뮬레이션. Enable/Disable All Caches 는 회색 + 안내. (gui_manual_sweep — 타임라인 캐시 색은 Blender 그리기 — 구운 상태로 확인)
- [x] (step 68) Fields/Solvers > Create Active Rigid Body (여러 개 선택) → 모두 강체, 바닥 Passive 위에 Maya 처럼 떨어져 멈춤. (gui_manual_sweep)

### Step 69 — 씬 관리 (프로젝트 · 증분 저장 · 레퍼런스)

- [ ] (step 69) File > Project Window: 대화상자 (안내 글, 이름, 위치, 폴더 12 개) — scene_01_win1 과 비교. Accept → 폴더 생김, 환경설정 Scene Concepts 의 Current Project 에 표시. File > Set Project… = 폴더 고르기 (Create Default Folders 옵션), File > Recent Projects 목록.
- [x] (step 69) 프로젝트가 있을 때 Ctrl+O / Ctrl+Shift+S / 처음 Ctrl+S / Status Line 열기·저장 아이콘 / File 메뉴: 파일 창이 `<프로젝트>/scenes` 에서 열림. 프로젝트 안에 저장하면 Render 출력 = `//../images/` (사용자가 바꾼 경로는 그대로). 다른 컴퓨터로 옮긴 프로젝트의 scenes 안 파일을 열면 그 프로젝트가 현재 프로젝트가 됨. (gui_manual_sweep — 다른 컴퓨터 = 프로젝트 폴더를 다른 곳에 복사)
- [x] (step 69) Ctrl+Alt+S (= File > Increment and Save): `shot_v001.blend` → `shot_v001.0001.blend` 로 저장하고 그 파일에서 계속 (원본 유지, 상태 표시줄 "Saved …"). (gui_manual_sweep — 상태 표시줄 「Saved」 문구는 Blender 저장 report (Python 에서 읽을 수 없음))
- [x] (step 69) Ctrl+R (= File > Create Reference…): 파일 창 (scenes 에서 시작, 오른쪽 옵션 Namespace / Editable) → `prop:pCube1` 등이 `prop` 컬렉션 아래에, 옮기기·키 가능 (원본 파일 그대로), 같은 파일 다시 = `prop1:`. 파일 브라우저·이미지 에디터·시퀀서에서는 Ctrl+R 이 원래 새로고침. (gui_manual_sweep)

### Step 70 — Graph Editor 툴바 · Shift+S · G · Auto Key · Playblast

- [ ] (step 70) Graph Editor 헤더 오른쪽 아이콘 줄: Auto / Spline / Clamped / Linear / Flat / Stepped / Plateau | Break / Unify | Buffer Curve Snapshot / Swap (step 198 부터 Maya 버퍼 커브, 전에는 Blender 고스트 커브). 툴팁 = Maya 이름 + Blender 대응. 키 선택 후 클릭 → 커브 모양이 animation_02_win1 의 툴바와 같은 뜻으로 바뀌는지.
- [x] (step 70) Shift+S 누른 채 LMB: Keys (W) / Tangents (E) 마킹 메뉴 — Graph Editor 에서는 선택 키, 3D View · 타임라인에서는 선택 오브젝트의 현재 프레임 키 (Time Slider 범위가 있으면 그 범위). Shift+S 탭은 아무 일 없음. Stepped Next 는 Stepped + 안내. (gui_manual_sweep — Stepped Next 안내는 연산자 INFO report (상태 표시줄))
- [x] (step 70) Graph Editor 위 G = 재생 범위로 가로 맞춤 (3D View 의 G = kit Repeat Last, step 175), D = 선택 키 Auto 탄젠트, F / A = 선택 / 전체. (gui_manual_sweep)
- [x] (step 70) Auto Key 켬: 키가 있는 채널만 값 바꿀 때 키 (이동 키만 있는 큐브를 회전 → 회전 키 안 생김; Channel Box 입력도 같음). 환경설정 「Maya Auto Key」 끄면 Blender 처럼 모든 채널. (gui_manual_sweep)
- [ ] (step 70) Windows > Playblast (Playback > Playblast, 셸프) → 재생 범위 동영상 → Blender 플레이어 창이 열림. □ (길게) = Playblast Options (Time Range / View / Format / Quality / Scale) — animation_08_win1 비교. 끝나면 장면의 렌더 설정 (출력 경로·형식·해상도 %) 은 그대로.

### Step 72 — 상단 바 다시 그리기 · Maya 인뷰 메시지

- [x] (step 72) F2–F6: 마우스를 뷰에 둔 채 누르면 상단 메뉴 바가 바로 그 메뉴 세트로 바뀜 (호버 없이). 창을 하나 더 연 (Hypershade 등) 뒤에도 두 창의 상단 바가 모두 바뀜. (gui_manual_sweep)
- [ ] (step 72) F8 → 뷰 가운데 위 "Component selection on. / F8 goes back to objects." 상자가 0.3 초에 나타나 2 초 머문 뒤 1.5 초에 걸쳐 사라짐 — Maya 의 in-view 메시지와 모양·위치·노란 강조 비교.
- [x] (step 72) Maya Workflow Kit 레이아웃에서 Ctrl+G / Ctrl+H / Alt+H 메시지는 뷰 왼쪽 위 (ivm_02, ivm_09 위치), Blender 텍스트 정보가 켜진 뷰에서는 가운데 위. b 로 소프트 선택 켤 때만 메시지, Make Live 켬 / 끔 메시지. (gui_manual_sweep)
- [x] (step 72) 환경설정 UI Elements 「In-View Messages」 끄면 메시지 없음. 4분할에서는 키를 누른 그 뷰에만. (gui_manual_sweep)

### Step 73 — 타임 슬라이더 키 틱 · Range Slider 드래그

- [ ] (step 73) 키가 있는 오브젝트를 선택하면 타임 슬라이더에 그 프레임마다 1 px 빨간 세로선 (Breakdown 키는 초록), 선택을 풀면 사라짐 — Maya 타임 슬라이더와 비교. 뼈 (포즈 모드) 는 그 뼈의 키만.
- [x] (step 73) Range Slider 바: 회색 구간 가운데를 끌면 재생 범위가 같은 길이로 움직이고 타임 슬라이더가 따라감; 양끝 손잡이를 끌면 그 끝만; 애니메이션 범위 밖으로는 안 나감; ESC / RMB = 취소; Ctrl+Z 로 되돌림. (gui_manual_sweep)
- [ ] (step 73) 바 더블클릭 = 전체 애니메이션 범위 ↔ 재생 범위 (GUI 테스트는 더블클릭 이벤트를 만들 수 없어 동작만 확인함).
- [ ] (step 73) UI 배율 1.0 / 1.5 / 2.0 에서 바가 playback start 필드와 playback end 필드 사이에 정확히 그려지고 숫자가 손잡이 옆에 읽힘.

### Step 74 — 프리셀렉트 (엣지 · 면 · 변형 툴)

- [ ] (step 74) 엣지 모드: 엣지 위 = 2 px 빨간 선, 꼭짓점 가까이에서도 엣지 (Maya 의 미리 선택 표시와 비교). 면 위 엣지에서 먼 곳 = 그 면의 가장 가까운 엣지.
- [ ] (step 74) 면 모드: 커서 아래 면 = 빨간 테두리 + 붉은 채움 (Maya 점무늬 pre_05 와 느낌 비교). 뒤쪽 면 / 엣지 / 정점은 X-ray 일 때만.
- [ ] (step 74) Move / Rotate / Scale 툴: 컴포넌트 위 프리셀렉트가 그대로 되고, 매니퓰레이터 화살표·가운데·회전 원 위에서는 꺼져서 손잡이를 잡을 수 있음. 클릭은 선택, 드래그는 박스 선택 그대로.
- [ ] (step 74) 큰 메쉬 (10만 정점) 에서 호버가 끊기지 않는지 (numpy 투영 + 캐시; 편집 후 첫 호버만 캐시를 다시 만듦).

### Step 75 — Status Line 입력 줄

- [x] (step 75) 입력 줄 모드 버튼: Absolute / Relative / Rename / Select by Name. Abs 에서 X 만 `10` Enter → 선택 오브젝트 x = 10 cm, Y / Z 그대로. Rotate 툴 (E) 이면 회전 값, Scale 툴 (R) 이면 배율. Ctrl+Z 한 번에 되돌림. (gui_manual_sweep)
- [x] (step 75) 편집 모드 (F9 / F11) 에서 Abs Z = 0 → 선택 컴포넌트 중심이 z 0 으로, Rel 은 그만큼 이동. (gui_manual_sweep)
- [x] (step 75) Rename: 칸에 리드 이름이 보이고, 여러 개 선택 후 `crate` → crate, crate1, crate2 (셰이프 crateShape…). `1x`, `a-b` 는 Help Line 오류. (gui_manual_sweep)
- [x] (step 75) Select by Name: `pCube*` / `p?phere1` → 선택, 없는 이름은 Help Line 오류 + 글자 남음. 회색 History 버튼 툴팁 = Blender 에 히스토리 없음 안내. (gui_manual_sweep)

### Step 76 — 선택 우선순위

- [x] (step 76) 오브젝트 모드: 메시 앞의 컨트롤 커브 (원) 를 클릭 → 커브. 메시 뒤에 가려진 커브의 선 위를 클릭해도 커브 (Maya 우선순위는 깊이를 보지 않음). 커브에서 5 px 넘게 떨어진 메시 위 = 메시. (gui_manual_sweep)
- [x] (step 76) 리그: 메시 몸통 앞/안의 본 (팔면체 두꺼운 쪽 포함) 클릭 → 아마추어, IK 핸들 (`ikHandleN` 엠프티 축) 클릭 → 핸들 (본·커브보다 먼저). (gui_manual_sweep)
- [x] (step 76) Shift = 토글, Ctrl = 해제, Ctrl+Shift = 추가가 커브·본에서도 그대로. Tweak 툴에서 커브를 눌러 바로 드래그 = 커브가 잡혀 움직임. (gui_manual_sweep)
- [x] (step 76) 환경설정 「Selection Priority」 끄기 → Blender 깊이 픽 (가려진 커브는 메시에 짐). 메시끼리 겹친 곳의 반복 클릭 순환은 켜져 있어도 그대로. (gui_manual_sweep)

### Step 77 — 편집 모드 Insert / D 피벗

- [x] (step 77) F9 + Insert: 툴바가 커서 툴, Help Line 「Pivot edit on」. 면 위 클릭 = 그 자리에 커서, 축이 면에 맞음; 드래그 = 커서가 따라 움직임. Insert 다시 = 이전 툴 (Move) + 매니퓰레이터가 그 피벗에서 면 방향 축으로. (gui_manual_sweep)
- [x] (step 77) Insert 를 켠 채 D 를 누르면 피벗 편집이 꺼짐. 커서를 옮기지 않고 Insert 두 번 = 사용자 피벗 지움 (매니퓰레이터가 선택 bbox 중심). (gui_manual_sweep)
- [x] (step 77) Insert 켠 채 F8 / Tab 으로 오브젝트 모드 → 피벗 편집 꺼짐; 다시 편집 모드 → 원래 툴. Maya 처럼 W 메뉴로 축을 World 로 돌릴 수 있음. (gui_manual_sweep)

### Step 78 — 키 묶음 2

- [x] (step 78) Shift+Q 탭 = 선택 툴 + 메시 편집 모드; 홀드 + LMB = 컴포넌트 픽 마스크 마킹 메뉴 (Maya 위치), Poly Vertices / Poly Edges / Faces 가 켜고 끄기, 없는 항목 회색. Maya 의 체크 표시는 안 보임. (gui_manual_sweep)
- [x] (step 78) Alt+Q 홀드 + LMB = Vertices N / Edges E / Faces S / UVs W (F9-F12 와 같음). Alt 를 누른 채라도 뷰가 돌지 않음. (gui_manual_sweep)
- [x] (step 78) Ctrl+Alt+← / → 로 선택 엣지가 돌아감 (Spin Edge Backward / Forward, 메뉴와 같은 방향). (gui_manual_sweep)
- [x] (step 78) 큐브를 만든 뒤 Shift+G 를 그리드 여러 곳에서 = 그 자리마다 큐브. 옆 직교 뷰에서도 원점 깊이의 마우스 자리. (gui_manual_sweep)
- [x] (step 78) Ctrl+Shift+C = 지금 뷰 그대로의 camera1 (Look Through 하면 같은 화면; 직교 뷰는 크기 [I]). (gui_manual_sweep)
- [x] (step 78) Graph Editor 1 / 2 / 3: 2 는 Help Line 에 Stacked 없음 안내 + Normalized. (gui_manual_sweep — 안내는 step 161 부터 Command Line 결과 칸 `results.result`, 상태 표시줄 보고 아님)

### Step 79 — 3D Cut and Sew UV Tool

- [x] (step 79) UV > 3D Cut and Sew UV Tool (메뉴 / 셸프 / UV Toolkit / UV 마킹 메뉴 NW) = 편집 모드 + 엣지 모드 + 툴바의 툴. 셸 경계가 흰 굵은 선으로 보임 (Maya Texture Borders). (gui_manual_sweep — 경계 선은 그릴 선 수·색·굵기로 확인 (픽셀 아님))
- [x] (step 79) 엣지 위 호버 = 빨간 하이라이트, 누르고 엣지를 따라 드래그 = 노란 선이 따라오고 놓으면 그 엣지만 잘림 (모서리를 돌아도 옆 세로 엣지는 안 잘림). Ctrl+드래그 = 꿰매기 (작은 셸이 붙음), Shift+드래그 = 선택만. (gui_manual_sweep — 빨강 / 노랑은 상수 + 호버·획 상태로 확인)
- [x] (step 79) 툴 안에서 x / s = 선택 엣지 Cut / Sew, d = Unfold + Layout (0-1). 툴 밖에서는 X / S / D 가 원래 키 (스냅 홀드 · 스케일 · 피벗). (gui_manual_sweep)
- [ ] (step 79) 큰 메시 (10만 정점) 에서 드래그가 끊기지 않는지 (표본마다 프리셀렉트 픽), 경계 선 캐시가 편집 뒤 다시 계산되는지.

### Step 81 — Maya persp 화각

- [ ] (step 81) 새 장면 (Maya Workflow Kit 레이아웃) 의 persp 가 Maya 새 장면과 같은 화각: 그리드 마름모 크기·원근, pCube1 크기를 Maya 와 나란히 비교. Four View 의 persp 사분면도.
- [ ] (step 81) Create > Cameras > Camera = Focal Length 35 (AE / CB), Ctrl+Shift+C 카메라로 Look Through 하면 뷰와 같은 화면.
- [ ] (step 81) 큐브를 화면 가득 확대한 상태에서 W + V + 가운데 핸들로 다른 큐브 정점에 붙이기 → 붙음 (step 95: 시뮬레이션 실패는 확대 탓이 아니라 Blender 의 10 ms 스냅 스로틀 + 한 틱에 몰아 보낸 이동 탓, `gui_step95_v_snap` 은 확대 / 기본 모두 통과).

### Step 82 — Outliner 드래그 = Maya 부모 지정

- [ ] (step 82) Outliner 에서 항목을 MMB 로 끌어 다른 항목 위에 놓기 = 그 자식 (흰 테두리가 놓을 행), Channel Box 값이 Maya 처럼 부모 기준. 선택은 그대로.
- [ ] (step 82) MMB 로 빈 곳에 놓기 = 월드로 (제자리). 선택된 항목을 끌면 선택 전부, 선택 안 된 항목을 끌면 그것만. ESC / RMB = 취소.
- [ ] (step 82) LMB 드래그 (Blender 드래그) 로 놓아도 결과가 Maya 부모 지정 (parent inverse 없음), Ctrl+Z 한 번 = 드롭 전. 아마추어 본 행에 놓기는 Blender 그대로.
- [ ] (step 82) Display > Sort Alphabetically 끈 뒤 MMB 를 행 위/아래 1/4 에 놓기 = 그 자리로 순서 바꿈 (흰 선). 정렬이 켜져 있으면 그 행의 부모 아래로만 옮김.
- [ ] (step 82) Alt+MMB = Outliner 패닝, 휠 스크롤 그대로. 큰 장면 (오브젝트 수천) 에서 MMB 누름이 끊기지 않는지 (누를 때·놓을 때 선택을 바꿨다 되돌림).

### Step 83 — 키 삽입·이동 묶음

- [ ] (step 83) 애니메이션된 큐브, 키 사이 프레임에서 Ctrl+Shift+W / E / R = 그 채널에만 키, Graph Editor 곡선 모양 그대로 (오버슈트 있는 곡선도). 키 없는 채널은 그대로 (새 곡선 안 생김).
- [ ] (step 83) Alt+I: Graph Editor 에서 곡선 하나의 키를 선택하고 = 그 곡선에만, 선택 없으면 보이는 곡선 전부; 3D View 에서는 선택 오브젝트 곡선 전부.
- [ ] (step 83) Shift+) / Shift+( 를 3D View 에서 누르고 있으면 현재 시간 키와 시간이 같이 한 프레임씩; Graph Editor / Dope Sheet 에서는 선택 키만 (시간 그대로). 다른 키 위로 가면 그 키를 덮어씀.
- [ ] (step 83) Ctrl+Alt+. / , = 다음 / 이전 키로 시간 이동 + 그 키만 선택 (Graph Editor 에서 하이라이트). 웨이트 페인트·그리스 펜슬 모드의 Alt+I 는 원래 기능.

### Step 84 — 타임 슬라이더 범위 키 이동·늘이기

- [ ] (step 84) 키 있는 큐브, Time Slider 에서 Shift+드래그 = 빨간 범위 + 흰 화살표 (끝 ◀ ▶, 가운데 ◀▶). 가운데를 끌면 범위 안 키와 범위가 정수 프레임으로 같이 움직이고 Graph Editor 곡선도 실시간으로 따라감.
- [ ] (step 84) 오른쪽 / 왼쪽 끝 화살표를 끌면 반대쪽 끝을 기준으로 키 간격이 늘고 줄어듦 (반대 끝을 넘지 않음). 놓은 자리의 다른 키는 덮어써짐. ESC / RMB = 원래대로.
- [ ] (step 84) 범위 위를 움직이지 않고 클릭 = 범위 사라지고 시간 이동. 범위 밖 클릭 / 드래그 = 시간 스크럽 (범위 사라짐). Ctrl+Z 한 번 = 드래그 전.
- [ ] (step 84) Graph Editor / Dope Sheet 의 위쪽 프레임 숫자 줄 클릭은 Blender 그대로 시간 이동.

### Step 85 — 매니퓰레이터 Ctrl+축 / Shift+MMB

- [ ] (step 85) W 툴에서 X 화살표를 Ctrl+LMB 로 끌기 = YZ 평면 이동 (X 그대로), 그 평면 핸들이 노랗게 (활성) 되고 이어서 MMB 드래그도 그 평면. Ctrl 을 누른 채 끌어도 스냅이 켜지지 않음.
- [ ] (step 85) 가운데 사각형 Ctrl+클릭 = 활성 핸들 해제 (노란 평면 / 축 없어짐, MMB = 화면 평면 자유 이동), 큐브는 안 움직임.
- [ ] (step 85) 아무 곳에서 Shift+MMB 드래그 = 처음 움직인 방향에 가까운 축으로만 이동 (persp 에서 비스듬한 축도), MMB 를 놓으면 확정. R 툴 Ctrl+X 화살표 = Y·Z 스케일.
- [ ] (step 85) 편집 모드 (컴포넌트) 에서도 같음. E (Rotate) 툴은 Blender 기즈모 그대로 (Ctrl+링 = Blender 스냅).

### Step 86 — Dope Sheet · NLA · Node Editor 선택 수식

- [ ] (step 86) Dope Sheet / NLA: 클릭 = 그것만, Shift+클릭 = 토글, Ctrl+클릭 = 해제 (선택 안 된 키는 Blender 토글이라 선택됨), Ctrl+Shift+클릭 = 추가 (선택된 키는 빠짐 — 같은 한계). 박스: Shift = 추가, Ctrl = 빼기.
- [ ] (step 86) Node Editor: 클릭 / Shift 토글 / Ctrl 해제 / Ctrl+Shift 추가 (Maya 그대로), Shift+드래그 / Ctrl+Shift+드래그 = 박스 추가, Ctrl+드래그 = Blender 링크 떼기 (소켓에서). Ctrl+Shift+클릭 Viewer 연결은 없어짐.
- [ ] (step 86) Time Slider 의 클릭 / Shift 드래그 (step 56 / 84) 는 그대로.

### Step 87 — 뷰 키 묶음 3

- [ ] (step 87) 리그가 있는 장면에서 Alt+A 세 번: 조인트가 메시 앞에 (In Front) → 보통 → 메시만 (조인트·커브 숨김), 인뷰 메시지로 상태 이름. 네 번째 = 처음으로.
- [ ] (step 87) Alt+P: persp ↔ ortho, 화면 위치 유지. 카메라를 통해 볼 때 = 그 카메라가 ortho 로 바뀌고 크기가 대략 그대로.
- [ ] (step 87) Alt+화살표를 누르고 있으면 선택이 화면에서 1 px 씩 (오브젝트·컴포넌트), 언두 단계마다 한 번.
- [ ] (step 87) ` 를 누른 채 다른 오브젝트 / 컴포넌트를 드래그 = 선택하지 않고 바로 이동, 놓으면 원래 툴 (Move/Rotate/Scale/선택).
- [ ] (step 87) 카메라 뷰에서 \ 누른 채 LMB 드래그 = 카메라 화면 팬, MMB 드래그 = 줌 (렌더는 그대로); 사용자 뷰에서는 Help Line 안내.


### Step 90 — 전역 키 묶음 4

- [ ] (step 90) 그룹을 선택하고 Ctrl+X → 그룹과 자식이 사라짐, Ctrl+V → 같은 이름 (shape 도 .001 없음) 으로 돌아오고 그룹이 lead (Channel Box 에 보임). Outliner 에서 Ctrl+X 도 같음. Edit > Cut 메뉴도 같음.
- [ ] (step 90) Alt+X → Walk (WASD / 마우스), 클릭 또는 Enter = 그 자리에서 끝, ESC = 원래 뷰. X-ray 는 켜지지 않음. Maya Walk 툴은 툴을 바꿀 때까지 남지만 kit 는 모달 (느낌 비교).
- [ ] (step 90) 재생 범위를 줄인 뒤 Alt+\ → Range Slider 가 애니메이션 범위 전체, Range Slider 더블클릭 → 줄였던 범위로 돌아옴.
- [ ] (step 90) 네 분할 뷰에서 마우스를 둔 뷰만 Alt+1 = 커브 숨김 / 보임, Alt+2 = 메시 숨김 / 보임. Alt+4 = Free Image Plane 숨김 / 보임 (Blender 한계로 모든 뷰).
- [ ] (step 90) Ctrl+Shift+~ = Subdivision 추가 (Smooth Preview 3 이 켜져 있어도 미리보기는 스택 끝), Ctrl+` = 케이지 ↔ 스무드, Shift+~ = 스무드 + 케이지 와이어, 다시 Ctrl+` = 케이지만. 프록시 없이 Ctrl+` = Help Line 경고. 미국 배열이 아닌 키보드에서 ` / ~ 위치 확인.

### Step 91 — 뷰 표시

- [ ] (step 91) Maya Workflow Kit 레이아웃에서 자식을 부모에서 떨어뜨려도 (Ctrl+G, P) 부모–자식 점선이 없음. Blender 로 전환하면 원래 워크스페이스의 뷰는 예전 그대로 (점선 있음).
- [ ] (step 91) 아무 작업 뒤 Adjust Last Operation 패널이 떠 있을 때 RMB / Space 메뉴가 그 패널 위에 그려짐 (UI 배율 0.8 / 1.25 에서도).

### Step 92 — Graph Editor 키

- [ ] (step 92) Graph Editor 를 확대한 상태에서 t → 현재 시간이 가운데로, 확대와 세로 범위는 그대로.
- [ ] (step 92) Alt+/ (또는 View > Snap Time To Selection) 켜고 키를 클릭 / 마키 / Shift 추가 → 현재 시간이 선택한 키 중 가장 이른 키로. 빈 곳 클릭 = 시간 그대로. 다시 Alt+/ = 끔.
- [ ] (step 92) 곡선을 선택하고 i 를 누른 채 MMB 클릭 → 그 프레임에 키, 곡선 모양 그대로, 새 키만 선택. MMB 를 누른 채 끌면 점선이 따라오고 놓은 곳에 키. 선택된 곡선이 없으면 아무 일 없음. i 를 놓으면 원래대로.

### Step 93 — 선택 마스크

- [ ] (step 93) 편집 모드 Shift+Q 홀드 + LMB → Faces 옆 체크 상자가 지금 선택 모드대로, Points ▸ / Lines ▸ 안의 Poly Vertices / Poly Edges 도. 하나 누르면 다음에 열 때 상태가 바뀌어 있음.
- [ ] (step 93) Status Line 의 선택 마스크 (예: 메시) 를 끄고 File > New, 그다음 File > Open → 마스크가 그대로 꺼져 있음 (Maya 와 같음). 엣지 선택 모드도 그대로.
- [ ] (step 93) Move 툴 옵션 (축 Local, Step Snap Relative) 을 바꾸고 Tool Settings 의 Reset Tool → 축 World, Step Snap 끔. Rotate 툴 = 축 Object, 스텝 15°.

### Step 94 — 피벗 편집 RMB 메뉴

- [ ] (step 94) 오브젝트 모드에서 D 를 누른 채 (또는 Insert 뒤) RMB 홀드 → Pin / Snap / Reset / Exit 메뉴. 피벗을 옮긴 뒤 S 방향 = Reset Pivot (피벗이 오브젝트 원점으로, 지오메트리 그대로), SE = 위치만, SW = 방향만, E = 피벗 편집 끝.
- [ ] (step 94) 편집 모드에서 면 선택 → D 로 피벗을 다른 곳에 놓기 → 다른 면 선택 = 피벗이 새 선택 가운데로 (Pin 꺼짐). D + RMB 로 Pin Component Pivot 체크 → 선택을 바꿔도 놓은 피벗이 남음.
- [ ] (step 94) Snap Pivot Orientation 끄기 → D + 면 클릭 = 피벗 위치만 바뀌고 방향은 그대로. Snap Pivot Position 끄기 → 클릭 위치가 면에 붙지 않음 (뷰 깊이).

### Step 95 — V 스냅 (확대)

- [ ] (step 95) W + V 로 X 축 화살표를 빠르게 휙 끌어 다른 큐브 정점 위에서 바로 놓기 (멈추지 않고) → 대부분 붙음. 가끔 놓은 자리가 정점 바로 앞이면 Blender 의 스냅이 10 ms 에 한 번만 다시 계산되는 한계 (`transform_snap.cc` transform_snap_mixed_apply; Blender 기본 스냅도 같음, step_95.md) — 정점 위에서 잠깐 멈추면 붙는지, Maya 사용자에게 거슬리는지.

### Step 96 — Outliner Sets

- [ ] (step 96) 오브젝트 몇 개 선택 → Create > Sets > Set → Outliner 의 DAG 행 바로 밑에 `set1` 행 (겹친 두 원 아이콘). 행 높이·글자 위치가 Blender 행과 맞는지, UI 배율 0.8 / 1.5 에서도 (행 높이 = round(18 × 배율) + 2 × pixel size 가정).
- [ ] (step 96) 오브젝트를 화면에 다 안 들어갈 만큼 많이 만든 뒤 → 세트 행이 Outliner 아래쪽 불투명 띠로 고정되어 보이고, 그 띠를 클릭하면 밑에 깔린 Blender 행이 아니라 세트 행이 잡히는지 (고정 모드). Maya 처럼 목록 끝에 오지 않는 것이 거슬리는지.
- [ ] (step 96) Select > Quick Select Sets ▸ (Create > Sets > Quick Select Set... 로 만든 것) → 멤버 선택. 만들기 전에는 회색 "No Quick Select Sets".
- [ ] (step 96) 세트 행 더블클릭 이름 바꾸기는 없음 (RMB > Rename...), MMB 로 오브젝트를 세트 행에 끌어 넣기도 없음 (RMB > Add Selected Objects) — Maya 사용자에게 필요한지.

### Step 99 — 첫 화면 (Outliner 기본 행, Tool Box 125 %, 도크 탭)

- [ ] (step 99) Windows 125 % 에서 Preferences > Interface > Resolution Scale 1.0 으로 Maya Workflow Kit 새 장면 → 시작 직후 마우스 커서가 Tool Box 열 오른쪽 경계로 잠깐 갔다가 제자리로 돌아오고, Tool Box 열에 Q W E R 툴이 보이며 뷰포트 안에 Blender 툴바가 남지 않는지. 커서가 순간 이동하는 것이 거슬리는지 (로드당 한 번).
- [ ] (step 99) 새 장면 Outliner = persp / top / front / side (회색, 카메라 그림) → defaultLightSet / defaultObjectSet. persp 클릭 = 선택 해제 + 행 강조, defaultLightSet = 라이트 선택. 큐브를 만들면 카메라 행이 pCube1 **뒤**로 감 (Maya 는 앞) — 거슬리는지.
- [ ] (step 99) Layer Editor (Display / Anim 탭) 가 도크 높이의 약 절반에서 시작하고 목록이 아래 끝까지 차는지 (Maya 처럼). 큐브 INPUTS 가 있을 때는 CB 바로 밑에 붙음.

### Step 101 — 메뉴 정직성 (회색마다 안내, 싼 매핑, 객체 모드에서도 활성)

- [ ] (step 101) 아무 회색 메뉴 항목 (예: Surfaces > Trim Tool, Generate > XGen Editor, Skeleton > Joint Labelling > Label Left) 에 마우스를 올리면 툴팁에 「(greyed) → 가장 가까운 Blender 기능」 과 한 줄 안내, Help Line 에도 같은 줄. 문장이 Maya 사용자에게 이해되는지.
- [ ] (step 101) 큐브를 객체 모드로 선택하고 Edit Mesh > Poke / Merge / Bevel → 큐브 전체에 적용되고 객체 모드 그대로 (Maya 처럼), Ctrl+Z 한 번에 원래대로. Bridge / Detach / Wedge → 상태 표시줄에 Maya 경고 문장, 모양 그대로.
- [ ] (step 101) Edit Mesh > Wedge: 면 몇 개 + 그 테두리 모서리를 활성으로 (Shift+클릭 마지막) → 그 모서리 축으로 90° 4 단 회전 압출. Maya 결과와 방향이 같은지 (반대면 축 부호 확인).
- [ ] (step 101) Edit Mesh > Edit Edge Flow: 굽은 면 위 가운데 루프를 평평하게 눌러 둔 뒤 실행 → 주변 곡률을 따라 다시 볼록해지는지 (Maya polyEditEdgeFlow 1.0 과 비교).
- [ ] (step 101) Mesh Tools > Sculpting Tools > Grab Tool 등 → Sculpt 모드 + 해당 브러시. Audio > Import Audio... → 파일 선택 후 재생 시 소리 (VSE 스트립), Mute 토글. Cache > Alembic Cache > Export Selection to Alembic... → .abc 파일, Import Alembic... → 불러옴.
- [ ] (step 101) Help > Maya Help / Python Command Reference → 웹 브라우저로 Blender 문서가 열림. Help > About Maya → Blender About.

### Step 102 — Maya 파일 대화상자, 기본 프로젝트

- [ ] (step 102) 새로 설치한 상태 (프로젝트 설정 없음) 에서 Ctrl+O / File > Import... → 대화상자가 `Documents/Maya Workflow Kit/projects/default/scenes` (step 111 / 125 이름) 에서 열리고 그 폴더들이 생김 (Documents 맨 바닥이 아님). 왼쪽 「Current Project」 의 폴더를 누르면 그 폴더로, Set Project... 는 보고 있는 폴더를 프로젝트로.
- [ ] (step 102) File > Export Selection... → 오른쪽 Files of type 을 OBJ → FBX 로 바꾸면 파일 이름 확장자가 따라 바뀌는지, 시작 폴더 (OBJ = data, FBX = scenes) 가 Maya 와 같다고 느껴지는지.
- [ ] (step 102) 실제 Maya 2022 에서 kit 가 내보낸 FBX / OBJ 를 Import → 크기·방향이 Maya 에서 만든 것과 같은지. Maya 가 내보낸 FBX 를 kit 로 Import → Channel Box 크기 그대로.
- [ ] (step 102) Import 대화상자에 .ma 파일을 고르면 「.ma / .mb can't be read: export FBX from Maya」 오류.

### Step 103 — Maya 옵션 창

- [ ] (step 103) Create > Polygon Primitives > Cube ❒ 를 누르고 있기 → 「Option Box」 → Polygon Cube Options 창. Width 3 → Apply: 창이 열린 채 큐브가 생기는지 (Maya Apply). Create: 만들고 닫힘. 다시 메뉴에서 그냥 Cube 클릭 → 3 폭 큐브 (Maya 처럼 저장된 값). Reset Settings → 1 로 돌아가는지.
- [ ] (step 103) Edit Mesh > Bevel ❒ / Constrain > Parent ❒ 창의 필드 이름·기본값이 Maya 창과 같다고 느껴지는지. 회색 「Not in Blender」 목록이 거슬리는지.
- [ ] (step 103) 메뉴 라벨 끝의 ❒ 표시가 Maya 사용자에게 옵션 상자로 읽히는지, 누르고 있기로 여는 것이 불편한지 (Maya 는 ❒ 를 클릭).

### Step 104 — Graph Editor / Dope Sheet / UV Editor 메뉴·아이콘 줄

- [ ] (step 104) 실제 마우스로 Graph Editor 헤더의 Edit / View / Curves / Tangents … 를 차례로 열고 (시뮬레이션은 헤더 메뉴 클릭이 안 열림, 테스트는 wm.call_menu), 메뉴 사이를 가로로 훑을 때 다음 메뉴로 넘어가는지. 「Blender」 메뉴에 Blender 원래 메뉴가 다 있는지.
- [ ] (step 104) Graph Editor 왼쪽 Maya 목록: 오브젝트 여러 개 (20 개 이상) 일 때 행이 넘치는지 — kit 목록은 스크롤을 따라가지 않음 (남은 것). 행을 드래그로 여러 개 고르기 (Maya 마키) 가 안 되는 것이 불편한지.
- [ ] (step 104) 아이콘 줄의 Stats 칸에 키 시간 `+=5` / 값 `10` 을 입력해 선택 키가 움직이고 Ctrl+Z 로 돌아오는지.
- [ ] (step 104) UV Editor 둘째 줄 아이콘 (Wireframe / Shaded / Distortion / Grid / 체커 / 이미지 칸) 이 Maya 아이콘 줄처럼 읽히는지, 오른쪽 UV Toolkit 의 Options / Help 드롭다운이 Maya 메뉴 막대처럼 보이는지.

### Step 105 — Hypershade / Render Settings / Script Editor

- [ ] (step 105) Hypershade: Browser 탭 (Materials … Shading Groups) 을 차례로 눌러 견본이 바뀌는지, View > As Large Swatches / By Type / Reverse Order 가 격자에 바로 반영되는지. 사이드바가 좁으면 탭 이름이 잘리는데 거슬리는지.
- [ ] (step 105) Hypershade Create > 2D Textures > Checker / General Utilities > 2d Placement 를 누르면 현재 재질 그래프 왼쪽에 노드가 생기는지 (연결은 안 함 — Maya 처럼).
- [ ] (step 105) Render Settings Common 탭: File name prefix 를 입력하고 Frame/Animation ext 를 name.#.ext 로 → F12 / 애니메이션 렌더가 그 이름으로 저장되는지; Ctrl+Z 로 필드 편집이 되돌아가는지. EEVEE 탭과 Common 탭을 오갈 때 Blender 렌더 패널이 그 창에서만 숨는지 (다른 Properties 창 Render 탭은 그대로).
- [ ] (step 105) Script Editor: 실제 키보드로 Ctrl+Enter (입력 유지) / 숫자패드 Enter (입력 지움), MEL 탭에서 실행하면 경고만. 위 기록 창에 명령과 결과가 Maya 처럼 읽히는지 (Blender 연산자 기록도 함께 나옴).

### Step 106 — Tool Settings 도크 / Attribute Editor

- [ ] (step 106) 실제 마우스로 Status Line 의 Tool Settings 버튼을 여러 번 눌러 도크가 열리고 닫히는지 (닫히면 뷰포트 너비가 원래대로). 도크 너비 280 px 가 Maya 처럼 느껴지는지, Outliner 와 뷰포트 사이 자리가 거슬리는지 (Maya 는 창 맨 왼쪽).
- [ ] (step 106) 도크를 연 채 저장 → 다시 열기: 도크가 남고 토글로 닫히는지. Q/W/E/R 를 바꾸면 절이 바로 바뀌는지, 조각 브러시 등 다른 도구는 Blender 도구 패널이 아래에 보이는지.
- [ ] (step 106) 회색 줄 (Transform Constraint, Tweak Mode, Bake Pivot Orientation …) 에 마우스를 올리면 툴팁에 Blender 대안이 나오는지; 머리 줄의 도구 아이콘과 "Move Tool" 글자가 겹쳐 보이지 않는지.
- [ ] (step 106) AE: Focus 를 누르고 다른 물체를 선택해도 AE 가 그 노드에 머무는지, List > Auto Load Selected Attributes 를 켜면 다시 선택을 따르는지; Copy Tab 으로 뜬 창이 그 물체에 고정되는지; Notes 에 입력 → Ctrl+Z.
- [ ] (step 106) Channel Box INPUTS 의 polyExtrudeFace1 이름에 마우스를 올리면 「Blender keeps no edit-mode history」 툴팁이 나오는지; Project Window 의 Current Project 칸 툴팁.

### Step 107 — 키맵 batch 3

- [ ] (step 107) 실제 키보드: Alt+R 로 대칭이 켜지고 꺼지는지 (Status Line Symmetry 글자), Ctrl+I 가 아무것도 반전하지 않는지, F1 을 버튼 위에서 누르면 Blender 설명서가 브라우저에 열리는지 (인터넷 필요).
- [ ] (step 107) Ctrl+M 으로 메인 메뉴가 ≡ 버튼으로 접히고 다시 펴지는지, Shift+M (마우스 아래 편집기 메뉴), Ctrl+Shift+M (3D 뷰 머리 숨김) 이 Maya 처럼 느껴지는지.
- [ ] (step 107) Alt+B 를 세 번: 밝은 회색 → 검정 → 원래 회색 (뷰마다 따로).
- [ ] (step 107) 스킨 페인트에서 u 메뉴로 Replace / Add / Scale / Smooth 가 바뀌는지, n 드래그 = 값, b 드래그 = 크기, Alt+F = Flood, Alt+C 로 가중치 색이 사라졌다 돌아오는지.
- [ ] (step 107) 조각에서 Ctrl+1–9 브러시가 바뀌는지 (Spray = Draw Sharp, Repeat = Layer 가 납득되는지), b / m 드래그, Shift+U / Ctrl+Shift+I 마스크.
- [ ] (step 107) Time Slider 에서 Shift 드래그로 범위를 고르고 Alt+T → 이름 → 마커; ' / ; 로 이동, Shift+| 로 재생 범위가 그 북마크로 바뀌는지.

### Step 108 — 메뉴 단축키 글자

- [ ] (step 108) 실제 마우스로 위 막대 File / Edit / Edit Mesh / Select / Key 메뉴를 열어 Maya 키가 오른쪽 한 열에 맞는지 (글꼴·배율 바꿔서도: Preferences > Interface > Resolution Scale), Recent Files 옆에 Blender 키가 없는지, 125 % 에서 File 메뉴 끝 (Exit) 이 화면 안에 있는지.

### Step 109 — 셸프 (Maya 순서, 회색 자리, 조각 브러시, 아이콘)

- [ ] (step 109) 실제 마우스로 셸프 탭 8 개를 돌며 버튼 수가 Maya 공장 셸프와 같은지 (38 / 43 / 26 / 18 / 14 / 25 / 29 / 10), 회색 아이콘 위에 머물면 「(Maya shelf, greyed) → 대체」 툴팁과 Help Line 글이 뜨는지, 누르면 아무것도 안 되고 안내만 나오는지.
- [ ] (step 109) Sculpting 셸프: 메시를 고르고 Smooth / Grab / Bulge / Freeze 를 차례로 눌러 조각 모드 + Smooth / Grab / Inflate/Deflate / Mask 브러시가 되는지 (세션 첫 클릭도 — 에셋 라이브러리 로딩 뒤 재시도), 드래그 느낌이 Maya 툴과 납득되는지.
- [ ] (step 109) Curves / Surfaces: 원 두 개 → Loft (step 181 부터 NURBS 표면), 닫힌 커브 → Planar / Bevel Plus, 프로필 + 경로 → Extrude, 커브 → Offset Curve / Sweep Mesh, Pencil Curve Tool 로 그리기, Add Points Tool 로 끝점 연장이 Maya 손에 맞는지.
- [ ] (step 109) 아이콘 모양 (셸프마다 Maya 색, 도구 부분 회색) 이 125 % 와 100 % 에서 Maya 셸프와 같은 인상인지.

### Step 110 — 모델링·리깅 기능

- [ ] (step 110) 실제 손으로: 구멍 테두리 / 면 묶음에 Circularize, 구 링을 줄였다가 Edit Edge Flow, 모서리 둘 → Connect, 면 두 개 → Make Hole 의 결과가 Maya 손에 맞는지 (뷰포트에서).
- [ ] (step 110) 조인트 체인에서 Reroot / Set·Assume Preferred Angle / Create IK Spline Handle (curve1 을 움직이면 체인이 따라오는지), Hammer Skin Weights 를 웨이트 페인트로 확인.
- [ ] (step 110) Cluster / Soft Modification 핸들을 W 로 움직이는 느낌 (Soft Mod 는 반경 5 안에서 부드럽게), Nonlinear Bend / Twist 값을 Channel Box 나 모디파이어에서 바꿀 때 핸들 기준으로 휘는지.

### Step 113 — 상단 (메뉴 막대, Status Line, 셸프, 패널 바)

- [ ] (step 113) 실제 125 % 화면, 자기 설정: Maya 로 전환 → 메뉴 막대에 File … Help 가 다 보이고 메뉴셋 드롭다운은 Status Line 맨 왼쪽, 오른쪽 Workspace: 드롭다운으로 작업 공간이 바뀌는지, Maya | Blender 글자가 눈에 덜 띄면서 눌리는지.
- [ ] (step 113) Status Line 의 ▷ 로 그룹 접기 / ▶ 로 펴기, 스냅 자석·선택 모드·렌더 아이콘 툴팁, 오른쪽 끝 사이드바 토글 (Modeling Toolkit / Attribute Editor / Tool Settings / Channel Box).
- [ ] (step 113) 셸프: 탭 클릭, ≡ (셸프 고르기), 톱니 (셸프 편집), 아이콘이 버튼마다 알아볼 만한지, 구분선 위치가 Maya 와 같은지.
- [ ] (step 113) 뷰 패널 툴바: 와이어 / 스무스 / 텍스처 / 모든 조명 / 그림자 / X-ray / 아이솔레이트 / 그리드가 그 뷰에서 켜고 꺼지는지, 노출·감마 칸, Blender 로 돌아가면 Blender 헤더와 테마가 돌아오는지.

### Step 115 — opt-in, 템플릿 정리

- [ ] (step 115) 실제 Blender 에서 Get Extensions 로 설치·활성화 → 그 자리에서 환영 창이 뜨고, 그 전에는 키맵·테마·레이아웃이 그대로인지. 「Make Blender feel like Maya」 → 저장 안 한 작업 중 파일이면 그 파일에 Maya-style 작업 공간만 붙고 데이터는 그대로, 새 빈 파일이면 Maya Workflow Kit 레이아웃 파일로 바뀌는지. 취소하면 아무것도 안 바뀌고 다시 안 뜨는지 (환경설정의 같은 버튼은 남음).
- [ ] (step 115) Auto-Save Preferences 를 끈 설정: Maya 로 바꾸고 저장하지 않고 종료 → 다음 시작이 Blender 그대로인지 (킷이 혼자 저장하지 않음).

### Step 116 — Maya 도킹 모델 (패널마다 창, ::::: 핸들)

- [ ] (step 116) 실제 화면에서 오른쪽 탭 스택 (Channel Box / Layer Editor | Attribute Editor | Modeling Toolkit) 이 뷰포트 옆 자기 영역에 있고, 뷰포트 사이드바(N)에는 Maya 패널이 없는지. 스택과 뷰포트 경계를 끌어 폭이 바뀌는지.
- [ ] (step 116) 스택 맨 위 ::::: 핸들 클릭 → 그 탭만 든 떠 있는 창, OS 창으로 옮기기 / 크기 바꾸기, 그 창의 ::::: → Dock / Close. 창의 X 로 닫아도 탭이 스택으로 돌아오는지. 두 모니터에서도.
- [ ] (step 116) Outliner 헤더 왼쪽 ::::: , Tool Settings 맨 위 ::::: 로 떼기 / 붙이기. 메뉴 맨 위 점선 줄 → 떠 있는 메뉴 창에서 항목 실행.
- [ ] (step 116) 떠 있는 창이 있는 채로 파일 저장 → 다시 열기: CB / AE 창은 그대로 보이고, 떼어낸 메뉴 창은 저절로 닫히는지. Blender 로 전환하면 떠 있는 Maya 패널 창이 닫히는지.

### Step 117 — 등록 자료 (업로드는 사용자)

- [ ] (step 117) https://extensions.blender.org/submit/ 에 `dist/allset-0.2.0.zip` 업로드 → 폼이 manifest 의 이름·tagline·태그·권한 사유·지원 버전을 그대로 읽는지; 설명 칸에 `docs/distribution/listing.md` B 를 붙여 넣고 미리보기에서 Markdown (굵게, 목록, 코드) 이 깨지지 않는지.
- [ ] (step 117) 아이콘 (256 × 256), 대표 이미지 (1920 × 1080), 미리보기 6장이 플랫폼의 크기·비율 요구에 맞는지 (맞지 않으면 `tools/make_splash.py` / `tools/marketing/` 스크립트의 크기를 바꿔 다시 만들기), 캡션은 listing.md C 표 순서대로.
- [ ] (step 117) 업로드 뒤 지원 URL (이슈 트래커) 을 정했으면 플랫폼에 넣기 — 아직 공개 저장소 없음 (결정 11).

### Step 118 — Blender 5.x 호환

- [ ] (step 118) Blender 5.0 / 5.1 / 5.2 실제 화면 (사용자 Blender 5.x 설치본): 확장 설치 → 환영 창 → Make Blender Maya → Maya Workflow Kit 레이아웃. 타임라인은 5.x 에서 사이드바가 열리지 않으므로 Range Slider 막대가 머리줄에 있고 재생 버튼 8 개는 그 줄 오른쪽 끝 — 막대 끌기 / 양 끝 핸들 / 더블클릭이 4.5 처럼 되는지.
- [ ] (step 118) 5.x: 관절 Channel Box Visibility off → 포즈·오브젝트 모드에서 그 본이 정말 숨는지 (5.0 의 `PoseBone.hide`), on → 다시 보이는지.
- [ ] (step 118) 5.2: 저장 안 된 이미지 (Texture Paint 한 획) 가 있는 채로 Ctrl+S → Blender 5.2 의 「수정된 이미지 저장」 창이 뜨는지.

### Step 120 — Maya 배경 · Alt+B

- [ ] (step 120) Windows > Settings/Preferences 가 Maya 처럼 하위 메뉴 (Preferences, Hotkey Editor, Color Settings, Marking Menu Editor, Shelf Editor, Panel Editor, Plug-in Manager) 인지; Color Settings 에서 Background 색을 바꾸고 Apply → 모든 뷰가 그 색, Gradient Background 켜고 Apply → 그라데이션.
- [ ] (step 120) 자기 테마 (Maya 테마 끔) 로 Maya 모드: Alt+B 가 회색 → 밝은 회색 → 검정 (그라데이션 없음) 이고 Preferences > Themes 가 바뀌지 않는지. Blender 로 전환 → 테마가 사용자 것으로 돌아오는지.
- [ ] (step 120) Edit Mode 에서 Ctrl+B = Bevel (Maya BevelPolygon) 그대로인지.

### Step 123 — 클립 · 트레일러 · 마케팅 키트

- [ ] (step 123) `docs/distribution/marketing/clips/00_trailer.mp4` 와 클립 7 개를 실제 속도로 보기: 커서 움직임이 자연스러운지 (가상 시간 — 드래그는 1/15 초 간격 그림), 클릭 원·키 칩이 화면 동작과 같은 순간인지, 캡션 줄이 하는 일과 맞는지, 크로스페이드에서 두 띠 글자가 겹쳐 보이는 0.27 초가 거슬리는지.
- [ ] (step 123) GIF 7 개를 GitHub 처럼 50 % 폭 (약 480 px) 으로 보았을 때 캡션 띠 글자를 읽을 수 있는지 (UI 글자는 못 읽어도 됨).
- [ ] (step 123) 올리기 전: 트레일러 끝 카드·`posts.md` 의 다운로드 자리표시 (`extensions.blender.org/add-ons/allset`, `<listing URL>` 등) 를 실제 주소로 바꾸고 `python tools/marketing/clip_compose.py` 다시; r/blender · r/Maya 사이드바 규칙을 직접 다시 읽기 (조사 때 Reddit 페이지가 막혀 검색 결과 문구만 봄).

### Step 124 — 홍보 디자인 재작업 (틸 · 잠금업 · 영상 움직임)

- [ ] (step 124) 클립 7 개 + 트레일러를 실제 속도로: 1.35 × 에서 조작이 읽히는지, 카메라 줌·팬이 어지럽지 않고 조작 지점을 잘라 먹지 않는지, 노랑 클릭 펄스·키 칩 플래시가 동작과 같은 순간인지, 트레일러 전환 (푸시 / 줌) 과 엔드 카드 움직임이 의도적으로 보이는지.
- [ ] (step 124) 키 비주얼 · 키트 카드를 갤러리 크기 (약 400 px 폭) 로 보았을 때 「for Maya Users」 가 바로 읽히고, 틸이 Maya 색으로 읽히는지 (Blender 주황과 헷갈리지 않는지).
- [ ] (step 124) 포즈 / 웨이트 페인트 모드 (Maya 모드) 에서 뷰포트 아래 카메라 라벨이 한 번만 보이는지, 에셋 셸프를 열고 닫아도 띠가 바르게 나오고 사라지는지; 환영 창 (125 % 와 100 % UI 배율) 본문이 잘리지 않는지.
- [ ] (step 124) 스토어 심사에서 틸이 Autodesk 제휴 암시로 지적되면 `ALLSET_MARKETING_PALETTE=maya-ui python tools/make_listing_media.py --no-shots` + `python tools/marketing/clip_compose.py` + `python tools/marketing/kit.py` 로 대체 팔레트 재생성 (style.md 「Trademark note」).

### Step 125 — 이름 Maya Workflow Kit · README

- [ ] (step 125) 깨끗한 설정에 `maya-workflow-kit-<ver>.zip` 설치: Preferences > Add-ons 에 「Maya Workflow Kit」, 환영 창 제목 「Welcome to Maya Workflow Kit」, 핫박스 가운데 상자 「Maya Workflow Kit」; 화면 어디에도 「Allset」 글자가 남지 않는지 (내부 id `allset` 은 Get Extensions 의 정보에만).
- [ ] (step 125) 저장소를 GitHub (`5hyuns/maya-workflow-kit-for-blender`) 에 올린 뒤 README 를 GitHub 화면에서: 히어로 이미지 · GIF 7 개 · 트레일러 MP4 링크가 열리고, 목차 앵커가 맞는 곳으로 가는지 (`tools` 없이 로컬 검사는 경로 존재만 확인).
- [ ] (step 125) 업로드 전 extensions.blender.org 에서 「Maya Workflow Kit」 와 같은 / 비슷한 이름이 없는지 검색 (다시 확인 안 함). 심사에서 이름이 지적되면 대체 이름 「Workflow Kit for Maya Users」 (결정 12 개정).

### Step 127 — 제품 사이트

- [ ] (step 127) 실제 브라우저 (Chrome, Safari 모바일) 에서 `site/index.html` (로컬 서버): 셸프 탭 클릭 · 화살표 · 1–6 으로 클립과 사실 열이 바뀌는지, 클립이 화면에 보일 때만 재생되는지, Maya | Blender 전환, 모바일 가로 스크롤 메뉴, FAQ 열고 닫기.
- [ ] (step 127) 저장소 공개 + push 뒤 GitHub Pages (Settings › Pages › GitHub Actions) 가 https://5hyuns.github.io/maya-workflow-kit-for-blender/ 에 뜨는지, og 이미지 미리보기.

### Step 129 marking menu bounds

- [ ] (step 129, #5) 실제 마우스로 Maya Workflow Kit 레이아웃에서 pCube1 을 뷰포트 아래쪽에 두고 RMB 를 누른 채 목록을 따라 천천히 아래로 끌기: Paint ▸ / Assign Favorite Material ▸ 줄을 지날 때 하위 메뉴가 줄 오른쪽에 열리고 목록은 그대로 남는지, 다음 줄로 내려가면 하위 메뉴가 닫히는지, 하위 메뉴 안의 항목에서 놓으면 실행되는지 (Qt 메뉴처럼; delegated).
- [ ] (step 129, #5) 같은 RMB 메뉴를 Time Slider 바로 위에서 열어 커서를 Time Slider / Range Slider 위로 내리기: 메뉴가 닫히지 않고, Time Slider 위에 그려진 남쪽 항목 · 목록 줄이 강조되고 놓으면 실행되는지; Time Slider 의 현재 프레임이 바뀌지 않는지 (RMB 놓기가 타임라인으로 가지 않음).
- [ ] (step 129, #5) Space 를 누른 채 (핫박스) 뷰포트 아래쪽에서 커서를 Time Slider 위로: 핫박스가 남아 있고 그 위 메뉴 이름이 강조되며 클릭하면 그 메뉴가 열리는지.

### Step 129 — Tool Settings (#3, #28, #29)

- [ ] (step 129) 실제 마우스로 Tool Box 아이콘 (Select / Lasso / Paint Select / Move / Rotate / Scale) 을 더블클릭: Tool Settings 도크가 열리고 그 툴의 Maya 절이 보이는지; 이미 열려 있으면 두 번째 도크가 생기지 않는지; 한 번 클릭 / W W 키는 열지 않는지.
- [ ] (step 129) Paint Selection 의 Select / Unselect / Add to current selection 이 실제 칠하기 선택 결과와 맞는지, Insert Edge Loop 의 Equal distance / Multiple edge loops 가 loop cut 결과에 반영되는지.

### Step 129 soft select

- [ ] (step 129) Maya Workflow Kit layout, cube in object mode: B → in-view message; F11 (faces) → soft select still on (header proportional button lit); B in face mode → off; back to object mode → off too (#15). Open a file saved with soft select on → it follows the current setting (Maya global option).
- [ ] (step 129) Edit mode, select one vertex of a dense grid, B on: the wire around it is yellow at the selection → red → black at the radius (Maya look, `tmp/maya129/out/softsel_00_on.png` reference); G moves exactly the coloured region and the colours stay put during the move; switch Volume / Surface and the falloff curve in the Modeling Toolkit → colours follow at once.
- [ ] (step 129) Hold B, drag with the **middle** mouse (and with the left) left / right: a white circle of the radius around the selection + "Falloff Radius: x" next to the mouse, the view does not orbit, releasing B keeps soft select on. Judge whether ×2 per 100 px feels like Maya (Maya's exact rate is not known).
- [ ] (step 129) Feel on a ~100k-vertex mesh: orbiting / selecting with soft select on stays fluid; Surface mode first draw after a selection change ~0.5 s at radius ≈ 6 % of the mesh (headless: Volume 0.2 s first / 5 ms on a radius change, Surface 0.5 s).

### Step 129 Multi-Cut

- [ ] (step 129) Ctrl+Shift+X (또는 Mesh Tools > Multi-Cut, Shift+RMB W, Polygons 셸프) → 엣지 위에 마우스를 두면 노란/회색 점과 `NN%` 가 마우스를 따라오고, 클릭 → 다음 엣지까지 회색 미리보기 선이 실시간으로 따라오는지; Maya 2022 Multi-Cut 과 나란히 놓고 점 크기·색·% 위치 비교.
- [ ] (step 129) 엣지를 누른 채 드래그 → 점이 엣지를 따라 미끄러지고 Shift 를 누르면 Snap Step % (Tool Settings 의 값) 칸마다 딱딱 붙는지.
- [ ] (step 129) Ctrl 만 누르고 (마우스 이동 없이) 엣지 위에 있을 때 링 전체에 주황 루프 미리보기가 바로 뜨고, Ctrl 을 떼면 사라지는지 (OS 키 이벤트 경로); Ctrl+클릭 → 루프, Ctrl+Shift+클릭 → 스텝 위치, Ctrl+MMB → 가운데; F9 (Adjust Last Operation) 의 Position 으로 루프가 움직이는지.
- [ ] (step 129) 정점 근처 (10 px) 클릭 = 정점에서 시작, 면 가운데 클릭 = 면 위 점 → 다음 엣지 클릭 → Enter: 면 안에 새 정점이 생기는지; 다른 면의 엣지를 클릭하면 경고만 나오고 점이 안 생기는지 (빨간 미리보기 점).
- [ ] (step 129) Backspace 로 점 하나씩 지우기, RMB / Enter 로 완료 후에도 툴이 그대로인지, Ctrl+Z 한 번에 컷 전체가 되돌아가는지, 점 없이 Esc → Select 툴.
- [ ] (step 129) 면 위 / 빈 곳에서 드래그 → 노란 선이 그려지고 놓으면 메시 전체가 그 선 (시선 방향 평면) 으로 잘리는지; Tool Settings 의 Ignore Backfaces / Delete Faces / Extract Faces (오프셋, cm 템플릿에서 0.5 cm) 와 Slice Along Plane YZ / ZX / XY (클릭한 점을 지나는 월드 평면) 결과를 Maya 와 비교 (지우는 쪽이 Maya 와 같은지 [K]).
- [ ] (step 129) Tool Settings 도크 (Properties Tool 탭) 에 Maya 순서대로 Snap Step % · Cut / Insert Edge Loop Tool (Smoothing Angle, Edge Flow 회색, Subdivisions) · Slice Tool · Color Settings / Live Constraint Options 회색 (툴팁 안내) · Keyboard/Mouse Shortcuts 가 보이고, Reset Tool 이 값을 Maya 공장값 (10 / 180 / 1 / 모두 끔) 으로 돌리는지; 툴 헤더에는 Snap Step 만.
- [ ] (step 129) Alt+LMB / MMB / 휠 네비게이션이 점을 찍는 중에도 되는지 (모달이 통과시킴), 여러 메시를 편집 모드에 넣었을 때 첫 점의 메시에만 점이 찍히는지.

### Step 129 — 뷰포트 (카메라 뷰, 패널 툴바)

- [ ] (step 129) Panels > Perspective > camera1 로 본 뒤 Alt+LMB / Alt+MMB / Alt+RMB / 휠: camera1 이 텀블 · 트랙 · 돌리되고 카메라 뷰가 유지되는지 (Maya 느낌), 툴바 Lock Camera 를 켜면 안 움직이는지.
- [ ] (step 129) 패널 툴바 아이콘을 실제 마우스로 두 번씩: 눌린 표시가 상태를 따라가는지 (카메라 버튼은 persp 에서 비활성).

### Step 129 misc — 떼어낸 창 크기, 머티리얼 색, 더블클릭 루프, 오토 키, 키 틱

- [ ] (step 129, #4) 오른쪽 탭 스택의 ::::: 을 눌러 Channel Box / Attribute Editor / Modeling Toolkit 을 떼어 낼 때 창이 내용 높이 (최소 약 200 px, 최대 dock 열 높이) 로 dock 열 위쪽 자리에 뜨고, dock 열이 잠깐 나뉘었다 원래대로 돌아오는 깜빡임이 거슬리지 않는지; 짧은 메뉴 (Cache 등) 의 점선 tear-off 는 작은 창, 긴 메뉴는 열 높이 창. 템플릿 첫 화면에서 처음 나누기 (Tool Settings dock 을 열 때도 같음) 에 셸프 줄 / Tool Box 열이 한 번 다시 맞춰지는지 (기존 동작) 확인.
- [ ] (step 129, #14) Lambert / Blinn 을 Shift+T 등으로 붙이고 Attribute Editor 의 Color · Transparency 를 바꾸면 기본 5 (Solid / Material) 뷰포트에 바로 그 색 · 투명도가 보이는지; Blender 에서 만든 머티리얼 (키트 밖) 은 Viewport Display 색 그대로인지.
- [ ] (step 129, #22) 실제 마우스로 엣지 / 버텍스 / 페이스 모드에서 더블클릭 = 루프 (방향은 가까운 엣지), 하나 고르고 같은 줄의 다른 하나를 Shift+더블클릭 = 사이 구간, 다른 줄이면 그 루프 추가. 이벤트 시뮬레이션은 DOUBLE_CLICK 을 못 보내므로 GUI 테스트는 연산자를 직접 부른다.
- [ ] (step 129, #37) Time Slider 오른쪽 열쇠 버튼 = Auto Key (켜면 빨갛게), 키가 있는 큐브를 다른 프레임에서 움직이면 움직인 채널만 키가 생기는지 (Channel Box 입력도).
- [ ] (step 129, #38) 현재 프레임에 키가 있으면 플레이헤드 상자 둘레가 빨갛게 보이는지 (Blender 가 상자를 애드온 그림 위에 그려 키 틱이 가려졌음); 다른 프레임의 틱은 1 px 빨간 선.

### Step 129 — Channel Box 채널 드래그 · Layer Editor · 가시성 하나 (lane CB)

- [ ] (step 129) 실제 마우스로 Channel Box 이름 칸 Translate X → Scale Z 를 끌어 범위 선택 (파란 이름 칸), 값 칸에서 시작한 드래그도 범위 선택; Ctrl 클릭 토글, Shift 클릭 범위. 값 칸 한 번 클릭 → 그 자리에 편집 칸이 바로 뜨고 (글자 전체 선택) 입력 + Enter 로 선택한 채널 전부 · 선택한 오브젝트 전부에 들어가는지, Esc 로 닫으면 값이 그대로인지.
- [ ] (step 129) 빠르게 끌 때 (한 이벤트에 여러 행) 범위 끝이 마우스 행과 맞는지, 드래그 중 Channel Box 밖으로 나갔다 들어와도 선택이 남는지, 125 % 와 100 % UI 배율.
- [ ] (step 129) h → Channel Box Visibility off; Channel Box Visibility 0 → Display > Show 로 다시 보임; 레이어 V 끄고 켜도 자기 Visibility 0 인 오브젝트는 숨은 채; 레이어 Template → Normal 뒤 Bounding Box 표시가 그대로인지.
- [ ] (step 129) Layer Editor: 행의 V / P / T 상자 클릭, 이름 더블클릭 이름 바꾸기, 상자 위 RMB → Maya 레이어 메뉴, 화살표로 순서 이동 (새 레이어가 맨 위). Maya Layer Editor 와 나란히.

### Step 131 — Hypershade

- [ ] (step 131, #25) Windows > Rendering Editors > Hypershade (그리고 Status Line 아이콘, 핫박스 Windows 메뉴) → 새 창이 Maya 배치로 열리는지: 맨 위 Maya 메뉴 줄 (File … Help), 왼쪽 위 Browser, 오른쪽 위 Material Viewer, 왼쪽 아래 Create, 가운데 Graph (툴바 + "Untitled_1" 탭), 오른쪽 아래 Property Editor. Maya Hypershade 와 나란히. 창을 크게 늘렸을 때 비율이 맞는지 (Blender 영역 경계는 창 크기에 비례).
- [ ] (step 131) 창이 만들어지는 동안 (한 틱에 한 번 나누기, 약 0.2 s) 깜빡임이 거슬리지 않는지; 125 % / 100 % UI 배율에서 메뉴 줄이 헤더 한 줄 높이로 보이고 (본문이 비치지 않음) 메뉴가 열리는지.
- [ ] (step 131) Browser 스와치 클릭 → Graph · Material Viewer · Property Editor 가 같은 재질로 바뀌는지; 검색 칸에 글자 입력 시 바로 걸러지는지; Bake Sets / Projects / Asset Nodes 탭, Show, 일시정지 버튼은 회색 + 툴팁 안내.
- [ ] (step 131) Create: Favorites / Maya / 카테고리 클릭으로 목록이 바뀌는지, 검색 칸으로 전체에서 찾기, Blinn 클릭 = 할당 안 된 새 재질, Checker 클릭 = 현재 재질 그래프에 노드, Point Light = 씬에 라이트; 회색 항목 툴팁.
- [ ] (step 131) Material Viewer: 모양 (Sphere / Shader Ball …) · World 토글 · EEVEE 미리보기가 그려지는지 (Workbench 면 안내 문구); 미리보기 아래 ::: 로 크기 조절.
- [ ] (step 131) Graph 툴바: 입력 / 입출력 / 출력 연결 = 네트워크 선택 + 화면 맞춤, Hide / Show connected / Show primary attributes, swatch 토글; 회색 버튼 툴팁. View > Frame All / Frame Selected 가 메뉴 줄이 아니라 Graph 에서 동작하는지.
- [ ] (step 131) Hypershade 를 연 채 메인 창에서 다시 열기 → 이전 창이 닫히고 새 창이 앞에 하나만; Hypershade 창의 Window > Browser… 는 아무 창도 새로 열지 않음. 파일 저장 → 다시 열기 후에도 패널들이 Hypershade 로 그려지는지 (메뉴 줄 / Graph 인식은 패널 표식 기준).

### Step 131 — menu icons

- [ ] (step 131, #23) Create > Polygon Primitives / NURBS Primitives, Mesh, Edit Mesh, Mesh Tools, Deform, Constrain, Key, Windows > General Editors 를 실제 마우스로 열어 Maya 2022 메뉴 (`tmp/maya_icons131/grab`) 와 나란히: 아이콘이 있는 줄이 Maya 와 같은 명령인지, 16 px 에서 한눈에 구분되는지 (같은 메뉴 안에서 서로 다른 그림).
- [ ] (step 131) 아이콘이 있는 줄 / 없는 줄의 글자가 한 열에서 시작하는지, Maya 단축키 (Ctrl+B, Ctrl+Shift+X …) 와 ❒ 옵션 상자 열이 그대로 오른쪽에 맞는지 — 100 % 와 125 % UI 배율, 그리고 Preferences 에서 Resolution Scale 을 바꾼 직후 (잠깐 이전 크기 그림이 쓰이다가 새 크기로 바뀜).
- [ ] (step 131) Maya 모드를 켠 직후 처음 여는 메뉴에도 아이콘이 있는지 (미리 만들어 둠), 회색 항목 (Surfaces > Trim Tool 등; Super Ellipse 는 step 190 부터 작동 — step 192 에서 문구 고침) 의 아이콘이 흐리게 보이는지.

## Step 131 — icons

- [ ] Shelves (every tab) at 100 % and 125 %: each button readable as the Maya 2022 button (shape, hue, corner mark), no two alike; greyed buttons faded.
- [ ] Status Line, panel toolbar, Tool Box column, Layer Editor buttons, Outliner set / camera rows: crisp at 100 / 125 / 150 % (change Resolution Scale while Blender runs — icons rebuild at the new size).
- [ ] Tool Box tools show Maya's teal accents at the default theme Icon Saturation; switching Maya mode off and quitting Blender does not crash.

### Step 132 — panel toolbar overflow

- [ ] (step 132, #52) Maya 레이아웃 메인 뷰포트를 100 % / 125 % / 150 % 에서: 패널 툴바가 잘리지 않고, 들어가지 않는 묶음이 있으면 오른쪽 끝에 » 가 보이는지. » 클릭 → 숨은 버튼 (아이콘 + Maya 이름) 과 노출 / 감마 / view transform 칸이 열리고, 각 버튼이 툴바 버튼과 똑같이 동작 (토글 두 번 = 원래대로)하는지.
- [ ] (step 132) 뷰포트 경계를 끌어 넓히고 좁히면 묶음이 하나씩 » 로 들어가고 나오는지 (넓으면 » 없음), Panels > Layouts 로 네 화면을 만들었을 때 좁은 패널마다 » 가 따로 맞는지.

## Step 134 — grid / cursor

- [ ] (step 134, #59) 새 Maya 장면 (100 % / 125 %): 그리드가 Maya 2022 첫 화면처럼 또렷한지 (#404040 선, 원점 축선과 5 칸마다 선이 굵게), 원점에 Blender 3D 커서 (빨강·흰 점선 원) 가 없는지. Blender 테마를 바꿔도 (Preferences > Themes) 그리드 색이 그대로인지.
- [ ] (step 134) 컴포넌트 모드에서 D 를 누르고 있는 동안 / Insert 를 켠 동안 커서 (= 피벗) 가 보이고 클릭으로 옮겨지는지, D 를 떼거나 Insert 를 다시 누르면 커서가 사라지고 조작기가 놓은 피벗에 남는지.

## Step 134 — display keys

- [ ] (step 134, #58) Maya 레이아웃에서 큐브를 만들고 1 / 2 / 3, 4 / 5 / 6 / 7, F8, F9 / F10 / F11, Alt+A, Alt+P 를 실제 키보드로 눌러: 뷰포트 왼쪽 아래에 Adjust Last Operation 패널 (「Component Mode」, 「Smooth Mesh Preview」 등) 이 뜨지 않는지. 다른 연산 (예: Alt+W, step 147 뒤 Shift+H 는 패널을 안 엶) 의 패널이 떠 있을 때 3 / F9 를 누르면 그 패널이 닫히는지.
- [ ] (step 134) F9 → Ctrl+Z 가 오브젝트 모드로 돌아가는지, 3 → 이동 → Ctrl+Z 가 이동만 되돌리고 미리보기는 남는지.
- [ ] (step 134, #61) Create > Polygon Primitives 의 Cube / Cylinder / Pipe 에 3: 미리보기가 매끈한 음영 (면 경계가 보이지 않음), 1 로 돌아오면 Maya 처럼 각진 hard edge. 0.2.x 에서 3 을 켜고 저장한 파일을 열어 3 을 다시 누르면 매끈해지는지.
### Step 134 — selection colours

- [ ] (step 134 SEL) 오브젝트 모드에서 큐브 둘을 Shift 클릭: 마지막에 고른 것 (리드) 의 모든 엣지가 Maya 연두 #43ffa3, 다른 선택은 흰색, 선택 안 된 것은 와이어 없음 — Blender 기본 테마 (주황) 그대로인 사용자 설정에서도. 와이어프레임 (4) 에서도 같은 색. Maya 레이아웃 밖의 뷰 (사용자 화면) 는 Blender 주황 외곽선이 와이어 바깥에 남는다 (의도, `docs/steps/step_134_sel.md`).
- [ ] (step 134) 편집 모드 F9 / F10 / F11 을 오가며: 엣지 연파랑 #64dcff, 정점 모드 = 보라 점 + 선택 노랑 점 (조금 큼), 엣지 모드 = 선택 엣지 주황 #e3ac79, 면 모드 = 선택 면이 주황 점묘. 가려진 뒤쪽 정점 · 엣지는 셰이딩 모드에서 안 보이고 X-ray (Alt+Z) 에서는 보이는지. 100 % / 125 %.
- [ ] (step 134) 10 만 정점 메시 편집 모드에서 정점 선택 · G 드래그가 느려지지 않는지 (변경마다 캐시 약 30 ms), Smooth Preview 3 을 켠 메시는 케이지 위에 색이 그려지는지 (5 만 정점 초과 + 편집 모드 모디파이어면 Blender 색으로 돌아감). Preferences > Component Colors 끄면 Blender 색.
- [ ] (step 134) Soft Select (b) 켬: 거짓 색 (노랑-빨강-검정) 이 킷 컴포넌트 색 위에 보이는지; 마우스 아래 프리셀렉트 빨강도 그 위에.

## Step 135 — dock width

- [ ] (step 135) 맞춘 뒤 독 왼쪽 모서리를 직접 끌어 좁히거나 넓혀도 다시 되돌아가지 않는지 (#53 규칙), Tool Settings 를 열고 닫아도 뷰포트 폭이 그대로인지, UI 배율을 바꾸면 다시 맞춰지는지.

## Step 135 — Channel Box / Layer Editor

- [ ] (step 135 CB, #55) Maya 레이아웃 새 장면, 100 % / 125 % / 150 %: Create > Polygon Primitives > Cube → Channel Box INPUTS 에 `polyCube1` 한 줄만 (접힘), 오른쪽 독 아래 절반에 Layer Editor (Display / Anim 탭, Layers / Options / Help, 빈 목록) 가 보이는지 (Maya Channel Box 와 같은지).
- [ ] (step 135) `polyCube1` 을 클릭 → Width … 행이 그 아래 펼쳐지고, Layer Editor 는 같은 자리에 그대로; 다시 클릭 → 접힘. 펼침은 Ctrl+Z 단계를 남기지 않는지 (Ctrl+Z 가 큐브 생성을 되돌림).
- [ ] (step 135) 펼친 채 두 번째 큐브를 만들거나 다른 오브젝트를 고른 뒤 첫 큐브로 돌아오면 다시 접혀 있는지 (Maya `cb135/d04_first_again.png`). 압출 (polyExtrudeFace1), modifier, 제약 노드도 접힌 채 시작하는지.
- [ ] (step 135) INPUTS 를 여러 개 펼쳐 Channel Box 가 길어지면: 마지막 줄에 ▲ ▼ 단추, Channel Box 위에서 마우스 휠로 행이 스크롤되고 Layer Editor 위의 휠은 Layer Editor 목록에만 작동하는지. Properties 의 modifier 패널 접힘 (show_expanded) 이 Channel Box 클릭으로 바뀌지 않는지.

## Step 136 — marking menus inside the window

- [ ] Cube near the bottom of the view, hold RMB: no list row is cut by the 3D View / Time Slider border; Time Slider numbers don't show on top of the menu.
- [ ] Same near the left (Outliner) and right (dock) edges, and Shift+RMB / Ctrl+RMB in object, vertex, edge and face mode: everything readable, gestures still go to the right item.
- [ ] Component mode (F9 / F10 / F11), RMB: Select All / Deselect All / Select Hierarchy / Invert Selection are not greyed and work like the Select menu.
- [x] Hover a greyed item (e.g. RMB > Time Editor): its notice appears in the Help Line. (gui_step136_items, step 154)
- [ ] Ctrl+RMB on a mesh in object mode: the convert menu; To Vertices / To Faces select every component of the object in component mode.
- [ ] Select tool, q hold + LMB (Select options): Camera-Based Selection shows a check box that follows the setting.

## Step 137 — animation / render basics

- [ ] Maya layout, key Translate X 0 → 5 (cm), Graph Editor, frame all: with the mouse over the curves the value axis reads 0–5; moving the mouse to the channel list shows Blender's 0.00–0.05 again (Blender limit) — is the switch distracting?
- [x] Translate + Rotate curves shown together: Blender's numbers stay (no wrong cm labels on degrees). (gui_step137_graph_units, step 154)
- [ ] File > New Scene → Cube → Render > Render Current Frame: Render View opens with the cube framed like the viewport; the Outliner shows persp once.
- [ ] Look through a camera (Panels > Perspective > camera) and render: that camera is used.
- [ ] Assign New Material > Blinn: AE Color grey 0.5, Incandescence black, Eccentricity 0.3, Specular Roll Off 0.7.
- [ ] Create > Lights > Point Light: AE Intensity 1, Decay Rate No Decay; Cycles render lights a surface 10 units away like Maya.

## Step 138 — scenes and files

- [x] Cube, Ctrl+N: 「Warning: Scene Not Saved / Save changes to untitled scene?」 Save / Don't Save / Cancel. Save → Save As in the project's scenes folder, the new scene only after saving; cancelling the browser keeps the scene. (gui_step138_prompt, step 145)
- [x] Saved scene changed, Ctrl+N: 「Save Changes / Save changes to <path>?」; Save writes the file, then the new scene. (gui_step138_prompt, step 145)
- [x] Maya mode, File > Open a .blend made in plain Blender: the Maya layout (Status Line, shelf, Tool Box, Channel Box dock, Time Slider) shows; add-on option 「Keep Maya Layout When Opening Files」 off → the file's own layout. (gui_step138_open, step 145)
- [ ] Set Move axis World/Object, step snap, soft select radius, symmetry; New Scene and File > Open keep them.
- [ ] Export All → FBX / OBJ / Alembic / USD, import in Maya 2022: pCube1 keeps translate / rotate / scale, no extra root / env_light, no Rotate X -90 / Scale 100. Maya → kit import: same channels, names pCube1 / pCubeShape1.

## Step 139 — Edit Mesh / UV with Maya results

- [x] Cube, F10, two opposite edges, Edit Mesh > Connect: one edge through their midpoints (10/15/7). (gui_step139_edit, step 145)
- [x] Two neighbouring vertices, Edit Mesh > Merge: one vertex at their midpoint (always merge two vertices). (gui_step139_edit, step 145)
- [x] One face, Mesh > Smooth: only that face smoothed (13/20/9), no Subdivision modifier. (gui_step139_edit, step 145)
- [x] Edit Mesh > Symmetrize: waits for an edge click (mesh unchanged), the click mirrors, Esc cancels. (gui_step139_edit, step 145)
- [ ] Ctrl+E on edges / a vertex: made at once (no mouse drag), In-View Editor + arrow change Thickness / Length.
- [ ] Ctrl+B on an edge: bevel at once (Fraction 0.5), Esc keeps it, In-View Editor Fraction / Segments edit it; vertex mode = Chamfer Vertex.
- [x] Object mode, UV > Automatic: 6 shells on a cube; UV Editor > Create > Best Plane / Contour Stretch enabled. (gui_step139_uv, step 145)

## Step 140 — Daily Maya option windows

- [ ] Skeleton > Create Joints ❒: "Joint Tool" window; Create Joints with Secondary Axis World Orientation Z: clicked joints roll to world Z; with Create IK handle on, an IK handle from the first to the last joint.
- [ ] Skeleton > Create IK Handle ❒ → Single-Chain Solver: the end joint follows the handle's rotation.
- [ ] Constrain > Aim (plain click and ❒ Add): the constrained cube's red (X) axis points at the target, its top stays up while the target moves around it.
- [ ] Skin > Paint Skin Weights ❒ → Paint operation Smooth: Blender's Blur tool is active; Opacity / Value reach the brush.
- [ ] Mesh Tools > Insert Edge Loop ❒ → Multiple edge loops 3: the Loop Cut tool cuts 3 loops.
- [ ] Key > Paste Keys ❒ → Time offset 10, Copies 2: two copies after the current frame; Key > Scale Keys ❒ → Time scale 2: keys spread from the pivot.
- [ ] Option window values kept: Apply, close, reopen → same values; plain menu click runs with them; Reset Settings → Maya factory values.

## Step 141 — quarantined GUI tests (run by hand; `python tests/gui/run.py --include-skipped -k ...` still runs them)

- [ ] (gui_step75_input_line) Status Line input line: Absolute X = 10 moves pCube1 to x = 10 cm; Rename field "crate" renames the lead; Select by name "pSph*" selects the spheres.
- [ ] (gui_step63_mtk) Modeling Toolkit dock: Face icon → edit mode, face selection; Extrude button extrudes one face (polyExtrudeFace1 with its manipulator); Object icon → object mode; Combine → one mesh pCube2; Separate → pCube2 group with two pieces; Mesh > Mirror ❒ opens Mirror Options.

## Step 141 — Select conversions

- [ ] Cube, vertex mode, one vertex: Ctrl+RMB ▸ Grow Selection ▸ Grow Along Loop → the vertex and its 3 neighbours; again on a subdivided plane with two neighbouring vertices → the row grows one vertex at each end.
- [ ] Plane 4×4, a row of 4 faces: Select > Shrink Along Loop → the 2 middle faces; Select > Grow Along Loop twice → the row reaches both borders.
- [ ] Face mode, 2×2 faces: Select > Convert Selection > To Vertex Perimeter → 8 vertices around, To Edge Perimeter → 8 edges, To Face Perimeter on a 3×3 block → the 8 outer faces.
- [ ] One edge selected: Convert Selection > To Face Path → the column of faces across that edge's ring.
- [ ] Face mode, a face: Convert Selection > To UVs → a UV Editor window opens, UV Sync Selection off, exactly the face's 4 UVs selected; then Ctrl+RMB in the 3D View ▸ To Edges → the face's 4 edges (back in edge mode, sync on).
- [ ] Plane with a face selected: To UV Shell Border → the border faces; closed cube → nothing (Maya does the same); To Shell Border on an interior face → nothing, on a border face → every border face.
- [ ] Select > Components > Vertex Face / Convert Selection > To Vertex Faces stay greyed; the tooltip says Blender has no vertex-face component.

## Step 142 — UI

- [ ] New Maya scene at UI scale 1.0 / 1.25 / 1.5: the right dock shows Maya's vertical tab strip on its right edge (Channel Box / Layer Editor, Attribute Editor, Modeling Toolkit, reading top to bottom); the stack is about as narrow as Maya's (286 / 346 / 418 px), nothing in the Channel Box is cut ("Subdivisions Height" of a polyCube1 input).
- [ ] Click Attribute Editor on the strip: the cursor jumps to the dock's left edge for a moment, the stack widens to Maya's AE width (480 / 600 / 720 px, less in a small window), the AE menu bar is one row; Channel Box tab: it narrows again. Ctrl+A does the same. A dock you resized yourself keeps its width.
- [ ] Hover / click below the last tab or on the strip's empty part: nothing happens; the AE region still scrolls with the wheel.
- [ ] UI scale 1.5 in a 1600 px window: the menu bar ends with » after the menus that fit; » opens the rest (Deform, UV, Generate, Cache, Help) as submenus that work like the bar's.
- [ ] UI scale 1.5: Key > Set Driven Key > Set...: the window under the Channel Box shows its lists with fewer rows and Key / Load Driver / Load Driven / Close stay inside the dock.
- [ ] Move / Scale tool on a selected cube: axes Maya red #e60000, green #00e600, blue #0000ff; the handle under the mouse and the last-used axis yellow. Rotate keeps Blender's ring colours (theme).
- [ ] Wireframe shading (4): unselected objects draw Maya's dark blue wire, the lead light green, others white; the "Selection Wireframe" preference off brings Blender's own wire colours back.

## Step 144 — Quad Draw / Create Polygon

- [ ] Object mode, nothing selected: Mesh Tools > Create Polygon, click 5 points on the grid in the perspective view (a cyan outline follows, a grey line closes it to the mouse), Backspace removes the last one, Enter → polySurface1 (one face, lambert1), selected; the tool stays for the next polygon. Esc with no points → Select tool.
- [ ] Create Polygon in the front view: the points lie on the view plane through the origin; with X held they snap to the grid, with V held to a vertex.
- [ ] Create Polygon ❒: the Tool Settings dock opens on Create Polygon Tool (Description, Settings: Divisions 1, Keep new faces planar off, Limit the number of points off / 4 greyed, Texture space Normalize); limit on at 3 → the third click completes the triangle.
- [ ] Select polySurface1, Mesh Tools > Append to Polygon: its border edges show orange; click one, then two points beyond it, Enter → a new face joined to that edge, shading continuous (normals agree). Clicking a second border edge instead of points bridges the two edges.
- [ ] Make a sphere live (Modify > Make Live), Ctrl+Shift+Q: a new polySurfaceN in edit mode, Quad Draw tool. Clicks drop green dots on the sphere; hold Shift: the green outline of the quad under the mouse; Shift+click fills it; the faces show over the sphere (Retopology overlay) and stay on its surface.
- [ ] Quad Draw feel: drag a dot / vertex / edge / face → it slides over the sphere; let a vertex go near another one → they weld (Auto-weld 10 px). Shift+drag over a patch → the brush circle shows, inner vertices even out and stay on the surface. Ctrl hover an edge → orange loop preview, Ctrl+click → loop, Ctrl+middle-click → loop in the middle. Ctrl+Shift+middle-drag an edge → its loop moves over the surface. Ctrl+Shift+click a dot / face → it goes, on an edge → its edge loop goes; Ctrl+Shift+drag across faces deletes them. Shift+middle-drag → only the highlighted points relax. Hold Tab and drag a border edge outwards → a new quad (Extend: Loop, or Tab+middle-drag = the whole border); Tab+drag in empty space on the sphere → a strip of quads about Quad Strip Width px wide.
- [ ] Ctrl+Z after placing a dot removes it; Clear Dots removes every dot; Esc / another tool → the dots go, the Retopology overlay comes back as it was, a polySurfaceN that never got a face is removed.

## Step 144 — Edge loops

- [ ] Cube (Mesh > Smooth or a polyCube with subdivisions), Mesh Tools > Insert Edge Loop: one click on an edge → the loop appears right where you clicked (no second click); press and drag → the loop slides along the ring under the mouse, release keeps it; Esc / right-click while dragging → no loop. The new loop is selected; Ctrl+Z removes it.
- [ ] Insert Edge Loop Tool Settings: Equal distance from edge on a tapered ring → the new loop stays the same distance from the side of the clicked edge nearer to the click; Multiple edge loops with 3 → a click inserts 3 evenly spaced loops wherever you click. Insert with edge flow on a sphere → the loop bulges with the surface.
- [ ] Mesh Tools > Offset Edge Loop on a cube's middle loop: click → two loops either side at half the neighbouring edges (Maya's 0.5); click-drag → they start at the edge and spread out with the drag. On a border edge: a warning, nothing happens. Offset Edge Loop ❒ opens "Offset Edge Loop Options" with Enter Tool And Close / Enter Tool / Close.
- [ ] Mesh Tools > Slide Edge: click / box-select an edge loop with the left button, then middle-drag → it slides along the neighbouring edges towards the drag, catching at the middle (Use Snapping, 1 point, 0.1); Mode Absolute → every vertex slides the same distance.
- [ ] Shift+RMB edge marking menu ▸ Edge Loop Utilities ▸ To Edge Loop and Duplicate → two offset loops around the selected edges' loops (Maya polyDuplicateEdge).
## Step 144 — Deform

- [ ] Maya layout, a cube: Deform > Lattice → ffd1Lattice (2 × 5 × 2 points, tall axis = up) exactly around the cube, selected; the Channel Box shows SHAPES ffd1LatticeShape S / T / U Divisions 2 5 2 and INPUTS ffd1 (click it: Envelope 1). Tab into the lattice, move the top points → the cube bends; Tab out, move / scale ffd1Lattice → the cube follows (Maya base lattice).
- [ ] Edit mode, top faces selected, Deform > Lattice ❒: Lattice Options (Divisions 2 5 2, Center around selection, Auto parent to selection, greyed "Not in Blender" list); Create with 3 3 3 → a lattice around the selected part only; only those points deform.
- [ ] Deform > Nonlinear > Bend on a tall cylinder: bend1Handle (arrow) at the middle selected; Channel Box INPUTS bend1 Curvature 0, Low Bound -1, High Bound 1; type 1 into Curvature → the cylinder bends; High Bound 0 → only the lower half bends.
- [ ] Two cubes, the small one selected last: Deform > Wrap → wrap1 on the big cube; edit the small cube's vertices or move the small cube → the big one follows; the small cube is not rendered (F12).
- [ ] Deform > Cluster on selected vertices → cluster1Handle; Deform > Paint Weights > Cluster with the handle selected → Weight Paint on the mesh with group cluster1 active; painting 0 on some vertices makes them stay when the handle moves.
- [ ] Deform > Wrinkle / Muscle / Pose Space Deformation > Create Pose Interpolator are greyed; hovering shows the Blender substitute in the tooltip and the Help Line. (Tension / Solidify / Morph / Sculpt / Jiggle work since step 205, Wire since step 169.)

## Step 146 — Option boxes without a drag (#82)

- [ ] Maya layout, Display menu: press and hold Grid ~0.3 s → the pointer jumps onto a tall "Option Box ❒" row under Grid; let go without moving → the Display menu closes (the pointer flicks to the window edge and back) and Grid Options opens where the pointer was.
- [ ] Same with Key > Set Key (Set Key Options) and Constrain > Parent (Parent Constraint Options); an item whose next row is a submenu (Display > Grid, next row Heads Up Display) leaves no submenu or menu open.
- [ ] Shift+click and Ctrl+click on Grid / Set Key open the option box instead of running the command (OS key state; event simulation can't test it). If Blender runs nothing on a modifier click, note it here.
- [ ] Hover Grid with tooltips on: the last tooltip line reads "❒ Option box: press and hold the item, then let go (or Shift / Ctrl+click)".
- [ ] Hold, then drag away from the Option Box row before letting go → nothing runs, the menu stays (Blender's own cancel).

## Step 147 — Undo steps and no redo panel (#88 #92 #86)

- [ ] Object mode, cube selected: Mesh Tools > Insert Edge Loop, click an edge, Ctrl+Z → the loop goes, you stay in component mode with the tool; Ctrl+Z again → object mode.
- [ ] Create > Polygon Primitives > Cube from the menu, move it, Ctrl+Z → only the move goes back; Ctrl+Z again → the cube goes. Same from the shelf and from a marking menu (Shift+RMB Create).
- [ ] Ctrl+E on a face, Ctrl+B on an edge, Skeleton > Create IK Handle, Rigging shelf > Create Joints (4 clicks, Enter): no Adjust Last Operation panel anywhere; G repeats the last Ctrl+E / Ctrl+B.
- [ ] An option box of the "redo" kind (Create > Lights > Point Light ❒; NURBS Primitives > Circle ❒ is a Maya window since step 196): Adjust Last Operation shows the light's settings and changing them edits the light.

## Step 148 — Channel Box finish (#87 #85 #83 #95)

- [ ] Channel Box, a keyed object: RMB on a channel name (selected or not) → Maya's Channels menu only (Key Selected, Key All Keyable, Breakdown Selected, Mute ...), no Blender Insert Keyframe / Add Driver rows; Key Selected keys the channel you clicked.
- [ ] UI 1.5 (and 1.0): a long Channel Box (many custom attributes / expanded INPUTS) fills its pane down to the Layer Editor, no two empty rows; the Layer Editor doesn't jump when INPUTS nodes open.
- [ ] Attribute Editor, transform tab: Translate / Rotate / Scale read plain Maya numbers (62, -150, 1.5), never "62 c"; typing +=5 works like the Channel Box.
- [ ] Create a Polygon Sphere, Deform > Lattice: ffd1Lattice Scale X / Y / Z = 2 2 2; moving lattice points still bends the sphere.
- [ ] Create > Lights > Point Light: SHAPES shows Color R / G / B and Intensity; typing 2 into Intensity brightens the light.

## Step 150 — Graph Editor View / Show (lane A)

- [ ] Maya layout, two animated cubes, Graph Editor open: with View > Auto Frame on (Maya factory), clicking the other cube in the viewport or Outliner reframes the Graph Editor on its curves within ~0.25 s; with Auto Frame off and Auto Frame Time on only the time axis follows (the value axis stays, the Range Slider / preview range don't change).
- [ ] View > Curve Name > Always: "pCube1.translateX" etc. in the curve colours just above each curve's last key (at the right edge when the last key is off screen); Active Only = only the selected curves; Never = none; Normalized View hides the names.
- [ ] Show > Objects > Clear Below after unticking Polygon Objects / Cameras → every object type is listed again; Show > Attributes > Clear Below clears the channel name filter.
- [ ] Greyed View items (Undo View Change, Clip Time, Show Results, Play Range Shades, Keys > Never, Key View, Time Ruler Placement, Simple Toolbar) show their own line in the tooltip / Help Line.

## Step 151 — Extrude manipulator (lane B)

- [ ] Cube, top face, Ctrl+E from Maya's persp angle: blue arrow up (normal), red arrow along world X, green along the face's Y, a cube past each cone, three translucent plane squares between the axes, a light-blue centre square; compare with Maya's extrude manipulator (Maya also draws a cyan rotate ring and a world / local toggle icon: not in the kit).
- [ ] Hover each handle ~1 s: it turns yellow, no Blender tooltip appears. Pre-selection doesn't highlight the face under a handle.
- [ ] Drag the red arrow → the top slides along X; drag a plane square → it slides in that plane; Ctrl+Z once takes each drag back.
- [ ] Drag the red / green cube outward → the top grows along that axis; drag the blue cube → nothing visible on a flat top (Maya too); drag the centre square right / left → the top grows / shrinks evenly.
- [ ] Ctrl+E on two adjacent faces (top + side), drag the red arrow → the shared edge moves by the mean of both faces' moves; In-View Editor and Channel Box INPUTS still list only Thickness / Local Translate Z / Offset / Divisions / Keep Faces Together.
- [ ] Edge and vertex extrusions, bevels: still only their single arrow.

## Step 152 lane B — default light, Test Resolution, Batch Render (#101)

- [x] New Maya scene, a cube, no lights: Render > Render Current Frame renders the cube lit from the camera's upper left (not black); the Outliner never shows `defaultLight`, and it is gone after the render. (gui_step137_render)
- [ ] Render Settings > Common > Render Options > Enable Default Light off → Render Current Frame renders the lightless scene dark (world light only); on again → lit. Create > Lights > any light → only that light lights the render.
- [ ] Render > Test Resolution: the submenu shows Camera Panel / Render Settings (960x540) / 10% … 150% Settings with a check on Render Settings; pick 50% → the next Render Current Frame is 480 x 270, Render Settings still says 960 x 540; Camera Panel → the render has the viewport's size.
- [ ] Render > Batch Render on a saved and on an untitled scene: the Help Line reports the output folder, Blender stays usable while a background Blender renders; Render > Show Batch Render opens the image in a new Image Editor window; Batch Render again while one runs warns; Cancel Batch Render on a long sequence stops it.

## Step 152 — Render option windows (main)

- [ ] Render > Render Sequence ❒: "Render Sequence (Current Frame)" with Current Camera (persp + scene cameras) and Alternate Output File Location; pick a folder, Render Sequence → images land there and the Render Settings output path is unchanged afterwards.
- [ ] Render > Batch Render ❒: "Batch Render Frame"; untick Use all available processors, 2 processors → the background Blender runs with `-t 2` (Task Manager).
- [ ] Render > Render Current Frame ❒: no window, the Help Line warns 'Renderer "EEVEE" does not provide render options.'

## Step 153 — Blender 5.x pass (#90)

- [ ] Blender 5.0+ (portable 5.2.3): bind a mesh, Skin > Paint Skin Weights ❒ → the window opens without an error; Value 0.25 / Opacity 0.5 / Radius(U) 3 → Weight Paint with weight 0.25, strength 0.5 and a brush of radius 3 cm (Blender shows the size as a diameter, 6 cm).
- [ ] Blender 5.x: hold a Maya menu item with an option box (Display > Grid) → the pointer goes onto the Option Box row, letting go opens Grid Options with the Display menu still open under it (5.0 menus stay open until a click); Esc / a click closes it. With Preferences > Interface > "Close menus when the mouse is moved out" on, the menu closes first like in 4.5.
- [ ] 4.5 and 5.x: W hold + a quick drag to the upper left / upper right through the wide Symmetry box → Object / Component (the Symmetry submenu doesn't open); a slow drag straight up still opens Symmetry.

## Step 155 — UV Editor shell tools

- [ ] UV Editor on a mesh with several shells: select one UV on each of three shells, Modify > Stack Shells → they sit on one centre; Modify > Orient Shells → a turned rectangle stands upright (counter-clockwise turn); Modify > Distribute Shells → widest first, touching, to the right.
- [ ] Select two UVs on two shells, Modify > Snap Together → the first shell's UV lands on the second (pick order doesn't matter, like Maya).
- [ ] Select the seam edges between a small and a big shell, Cut/Sew > Move and Sew → the small shell turns / moves onto the big one without scaling and the seam merges.
- [ ] Select faces inside a shell, Ctrl+Shift+X → a new shell (Select > Shell picks only those faces); Delete → their UVs collapse to the 0,0 corner.
- [x] Keys in the UV Editor: 4 wireframe, 8 blue shell borders on, 9 texture borders off / on, Ctrl+1 shows only the selected UVs and Ctrl+1 again every face. (gui_step155_uv)
- [ ] Keys in the UV Editor: 5 shaded, 6 hides and shows the texture image; Ctrl+1 out of isolation gives back the old UV selection.
- [ ] Tools > Move UV Shell: a click on a UV picks its shell, dragging moves it; choosing another UV tool goes back to UV picking.

## Step 156 — Curves tools

- [ ] Create > Curve Tools > EP Curve Tool in persp: clicks on the grid add edit points (preview), the curve passes through every click after Enter; Backspace removes the last point, Esc cancels; holding X snaps to the grid.
- [x] CV Curve Tool: Enter with 3 clicks keeps waiting (degree 3 needs 4), after the 4th click Enter makes the curve; its CVs are the clicks. (gui_step156_curves)
- [ ] Three Point Circular Arc: start, through, end clicks give a smooth arc through all three; Two Point Circular Arc gives a half circle on the ground.
- [ ] Two curves meeting at a corner: Curves > Fillet makes a round corner curve (filletedCurve1) of radius 1 cm; Curves > Attach joins two curves into curveAattachedCurve1 (both originals kept); Curves > Cut on two crossing curves leaves four pieces.
- [ ] Curves > Rebuild on a hand-drawn curve: 4 spans, the ends stay where they were; Rebuild ❒ opens Rebuild Curve Options with Number of spans 4.
- [ ] Curve edit mode, select one CV, Curves > Detach: the curve splits near that CV into two objects.

## Step 157 — Graph Editor keys in Maya terms
- [ ] Graph Editor Select > Only Curve, click a key: the whole curve's keys light up; box-drag over two keys of another curve picks that whole curve too. Select > All, click a key: only that key.
- [ ] Select > Key off (In / Out Tangent on), click a key with handles shown: the key is not picked; clicking a handle still picks it. The highlight drops within a blink (≤ 50 ms), never stays.
- [ ] Select a key in the middle of a curve, Keys > Mute Key: the curve goes flat from that key to the next one, then continues; Keys > Unmute Key on it restores the curve. The F-Curve sidebar Modifiers tab lists "Maya mute".
- [ ] Current time 10, Keys > Add Inbetween: every key at or after 10 on the shown curves moves one frame later; Remove Inbetween moves them back.
- [ ] Tangents > Default Out Tangent > Stepped, then S on a new frame: the new key is stepped; Default In Tangent > Flat: its incoming handle is level. Back to Auto: new keys are Blender's Auto Clamped again.
- [ ] Keys selected in the Graph Editor, Edit > Delete ❒ > Delete Keys: only those keys go; with nothing selected the same window deletes the selected objects' keys (Maya).

## Step 158 — Channel Box menus complete
- [x] RMB on the empty space under the Channel Box rows (above the Layer Editor) opens Maya's Channels menu, not Blender's; Ctrl+RMB there or on a channel opens the Edit menu. (gui_step158_cb_menus)
- [ ] Copy Selected on a keyed Translate X, select Translate Y, go to frame 15, Paste Selected: the copied curve starts at 15 and joins Translate Y's curve there; later Translate Y keys move right.
- [ ] Channels > Sync Selection in Graph Editor on: clicking a channel selects its curve in the Graph Editor; S keys only the selected channels. Sync Timeline Display on: the Time Slider ticks show only the selected channels' keys.
- [ ] Point light: click Intensity in SHAPES (scroll the Channel Box), RMB > Key Selected: the row shows the key state; Graph Editor shows a Power curve.
- [ ] Spot light: Cone Angle 40 / Penumbra Angle 0 rows; typing Penumbra 5 widens the cone softly.
- [ ] Bind a mesh to a skeleton: INPUTS shows skinCluster1 (a second bound mesh shows skinCluster2).

## Step 159 — Skin weights / Joint Labelling
- [ ] Skinned mesh selected: Deform > Export Weights... saves `skinCluster1.xml` in the project's data folder; Unbind + Bind again, Deform > Import Weights... brings the painted weights back.
- [ ] Pose mode, a leg joint chain's top selected: Skeleton > Joint Labelling > Add Joint Labels > Label Left, then the first Label Hip: the chain reads Hip / Knee / Foot / Toe; Show All Labels draws "Hip (L)" etc. in Maya's blue beside each joint; Rename Joints From Labels renames them LeftHip, LeftKnee ...
- [ ] Label both legs Left / Right, paint the left leg, Skin > Mirror Skin Weights with Influence Association Label: the right leg gets the weights even when its joints are not placed exactly mirrored.
- [ ] Select an ikHandle, Skeleton > Disable Selected IK Handles: the chain stops following the handle; Enable brings it back.

## Step 160 — Maya workspaces / Reset (#81)
- [ ] Status Line "Workspace:" dropdown lists Maya Classic, Modeling - Standard, Modeling - Expert, Sculpting, UV Editing, Rigging, Animation, Rendering - Standard, then the file's other workspaces; picking Animation switches the menu set to Animation and shows the Graph Editor under the viewport.
- [ ] In a Blender file (Maya mode switched on), Windows > Workspaces > UV Editing appends the Maya UV Editing layout once; picking it again reuses it.
- [x] Mess up a Maya workspace (close the Outliner, resize areas), Windows > Workspaces > Reset "…" to Factory Default: the layout comes back, the workspace keeps its name. (gui_step160_workspaces)

## Step 161 — Viewport messages and views
- [x] Edit > Group on two objects: no Blender ⓘ banner in the Help Line; the Command Line result field (right of the Python field) shows Maya's result "group1", drawn inside the window. (gui_step161_messages G1)
- [ ] The same with the Ctrl+G key on real keys; Create > Polygon Primitives > Cube: "Created pCube1" in the result field.
- [x] RMB on an object near the bottom of the viewport: the list stays one column (beside the ring when it doesn't fit under it, the ring at the press point — step 193 rule), never wrapping into columns, every row inside the window. (gui_step161_messages G2, updated in steps 184 / 193)
- [ ] (superseded by Step 184: the list is under the ring now, the "beside" question is closed) RMB list under a lifted ring: dragging from the ring down onto a row and releasing runs it.
- [x] Space tap: the top / front / side panes show about 30 units across (a 1-unit cube is a small square), each gridded edge to edge in its own plane; zoom the side pane, Space-tap out and back in: the side pane keeps its zoom, the others stay at 30. (gui_step161_views)
- [ ] Tooltip of Panels > Layouts > Four View (or the Tool Box Four View button) says Blender's four view has one header for all panes.
- [x] Select a parent whose child sits in front of it (side view): the child is drawn in the parent's green / white wire too (Maya hierarchy highlight). (gui_step161_views)

## Step 162 — Option boxes and menu gestures
- [ ] Display > Toggle Show/Hide ❒ opens "Toggle Visibility Options" (First Selection Independent / Dependent). Pick Dependent, Apply and Close; select a hidden-but-selected object first and two visible ones: h shows all three.
- [x] Edit > Delete by Type > Non-Deformer History ❒ = a Maya window; Delete with the factory All bakes the non-deformer history and keeps only the deformer. (gui_step162_option_windows)
- [ ] Non-Deformer History ❒ with a Bevel after an Armature: "History before deformers only" keeps the bevel (the GUI test only runs All).
- [ ] Ctrl+Shift+click a Maya menu item (Create > Polygon Primitives > Cube) on real keys: the item doesn't run, no option box, a Cube button appears at the end of the current shelf tab, the Command Line shows "Cube added to the … shelf"; Shift+click / Ctrl+click still open the option box.
- [ ] Restart Blender: the added shelf button is still there; click runs the item, Ctrl+click opens its option box, the shelf menu's Edit / Delete reach it (factory tabs too).
- [x] Hypershade floating beside the main window: MMB-drag a Browser swatch's name onto an object in the main viewport: the material is assigned (one undo step); releasing over empty space does nothing; ESC cancels; a plain LMB click still picks the swatch. (gui_step162_hs_drag)
- [ ] The same drag on a real mouse: the swatch + name follow the cursor; releasing over the Outliner does nothing.

## Step 164 — Maya DAG rules for parents
- [x] Select a group, press h: its cube is not drawn, the cube's own Visibility stays on; h again shows it. (gui_step164_dag)
- [ ] Group two cubes (Ctrl+G), hide one cube on its own first, then h twice on the group: that cube stays hidden (Maya); the other comes back.
- [ ] Select the group, Delete (key, Edit > Delete, Outliner Delete): the group and both cubes are gone; Ctrl+Z brings all three back.
- [ ] File > Export Selection of the group as FBX, import the file into Maya: group + both cubes.
- [x] Select the group, Ctrl+1: the view shows the group's cube with it, other objects disappear; Ctrl+1 again leaves the isolation. (gui_step164_dag)
- [ ] Put the group in a display layer and turn its V off: the cubes disappear too (headless test only).
- [ ] A scene with a few thousand objects: dragging objects stays as fluid as before step 164 (the parent rule runs on every scene update).

## Step 165 — Component-mode Channel Box and RMB node submenus

- [ ] Edit mode on a cube, select 3 vertices: the Channel Box shows pCubeShape1, "CVs (click to show)", INPUTS polyCube1 — no Translate / Rotate / Scale rows.
- [ ] Click "CVs (click to show)": a row per selected vertex with X / Y / Z; type `+=1` in X: the vertex moves, Ctrl+Z undoes it.
- [ ] Select an edge / a face: no CVs line; deselect all: the empty Channel Box text.
- [ ] RMB on an object > Inputs: Select / Enable / Disable All Inputs, the nodes (Poly Cube ...), All Inputs...; pick a node: the Channel Box scrolls to it, open; its ❒: the Attribute Editor on that node.
- [ ] Disable All Inputs on a cube with a bend: the bend stops deforming; Enable All brings it back.
- [ ] RMB > Outputs on a locator used by a constraint lists the constraint; RMB > DG Traversal > pCubeShape1 > Select pCubeShape1 shows the shape in the Attribute Editor.

## Step 166 — Menu consistency

- [x] Dope Sheet: select keys of a rotation curve with a 350° jump, Curves > Euler Filter: the jump is gone, curves without selected keys are left alone, the area is a Dope Sheet again; Resample Curve keys every frame. (gui_step166_dope_curves)
- [ ] After Dope Sheet Curves > Euler Filter the Dope Sheet keeps its scroll / zoom (no flicker from the Graph Editor switch).
- [ ] Dope Sheet View > Auto Frame on: selecting another animated object frames the Dope Sheet.
- [ ] Select > All by Type > IK Handles / Clusters selects the kit's ikHandle / clusterHandle empties; Edit > Delete All by Type > IK Handles / Clusters removes them with their constraints / hooks.
- [ ] UV Editor Tools > Unfold / Cut / Sew / Pin act on the selection like Modify > Unfold, Cut/Sew > Cut / Sew, Edit > Pin Selection.

## Step 167 — Shelf double-click and overflow

- [x] Double-click Polygon Cube on the shelf: one cube, then Polygon Cube Options opens. (gui_step167_shelf)
- [ ] Double-click a "run + settings" button (e.g. Extrude) on a real mouse: one result (the first click's run is taken back) with Adjust Last Operation.
- [x] Window narrower than the Poly Modeling shelf (1600 px, UI 1.25): two rows, one shown, scroll bar drawn; the wheel over the icons shows the next row with the last button on screen; ▲ shows row 0 again. (gui_step167_shelf)
- [ ] The ▼ arrow moves one row down and the arrow at the end of the range is dimmed.
- [ ] Buttons added with Ctrl+Shift+click past the end of a long shelf are reachable by scrolling.

## Step 168 — Modify menu and Smooth Mesh Preview to Polygons

- [ ] Bind a cube to a joint chain, press 3, Modify > Convert > Smooth Mesh Preview to Polygons: the mesh is dense in edit mode, the skin still bends it when a joint rotates, the Channel Box INPUTS still lists skinCluster1.
- [ ] Modify > Evaluate Nodes: untick Constraints — a constrained cube stops following its target; tick it again — it follows. Ignore All / Evaluate All tick and untick every item.
- [ ] Modify > Align Tool with two cubes: the popup's X Min lines the first cube's left side up with the last selected one.
- [ ] Modify > Convert > Geometry to Bounding Box ❒ (hold): the Maya option window; Keep original keeps the mesh, Convert replaces it with a grey box.

## Step 169 — Deform completion

- [ ] Select a plane, then a curve, Deform > Wire: moving / bending the curve (edit its CVs) pulls the plane within the dropoff; twisting the curve object does nothing (Maya).
- [ ] Deform > Wire > Wire Dropoff Locator with a CV of the wire selected: a locator appears on the wire; a Percent 2 widens the pull there.
- [ ] Deform > Wire > Reset puts the curve back; Show Base Wire shows curve1BaseWire; Remove leaves the curve and restores the plane.
- [ ] Deform > Paint Weights > Wire ❒ (hold): Paint Attributes Tool window; Paint starts Weight Paint on wire1 with the values.

## Step 170 — Selection modifiers outside the 3D View

Real keys only: `Window.event_simulate` drops modifiers on CLICK_DRAG and Ctrl CLICK, so `gui_step170_select_mods` drives those cases through the operators — these items stay open until checked by hand.

- [ ] Graph Editor: select keys 1 and 10, Shift+drag a box over 10 and 20 → 1 and 20 selected; Ctrl+drag over 20 → only 1; Ctrl+Shift+click a selected key → nothing removed; click a selected key and drag → all selected keys move.
- [ ] Dope Sheet: Ctrl+click a selected key deselects it; Shift+box toggles.
- [ ] UV Editor: Shift+box over selected and unselected UVs toggles each.
- [ ] Outliner: click A, Shift+click C → A..C; Ctrl+click B → B off; Ctrl+Shift+click E → C..E added.

## Step 171 — Animation Snapshot / ghosting

- [ ] Animate a cube, Visualize > Create Animation Snapshot: snapshot1Group with transform1_1..10 in the Outliner; move a key in the Graph Editor → the copies follow a moment after the drag ends (Fast); type a Scale → nothing until Visualize > Update Snapshot.
- [ ] Visualize > Ghost Selected: cyan ghosts before, pink after, fading outwards; scrub the Time Slider → ghosts follow (new frames appear a tick after the scrub stops); during playback missing ghost frames are not sampled.
- [ ] Visualize > Open Ghosting Editor: preset 2s + Apply to All Ghosts spaces the ghosts every other frame; Unghost All removes them.

## Step 174 — One tool across object / component modes

- [x] W on a cube, F9: Move + kit manipulator in vertex mode; F8 back: Move on the object; E / F10, R / F11, Q / F9 the same. (gui_step174_tool_modes)
- [ ] ... and no Select Box flash between the key and the Move manipulator (feel; the test reads the tool after the switch).
- [x] E, then RMB > Vertex: Rotate in vertex mode; Shift+RMB > Target Weld from object mode still starts Target Weld. (gui_step174_tool_modes, gui_step64)

## Step 175 — G repeats Maya commands

- [x] Menu Create > Polygon Primitives > Cube, then the real G key: pCube2; Edit > Repeat label `Repeat "Cube"`; Ctrl+D then G duplicates again (key command newer). (gui_step175_repeat)
- [ ] Mesh > Combine on two cubes, select two other cubes, G: they combine too; Edit menu shows Repeat "Combine".
- [ ] A shelf button (Poly Cube), then G: another cube; Ctrl+E on faces, then G: extrudes again (the key command is newer).
- [ ] Hotbox (Space) > Recent Commands: the last commands, newest first; clicking one runs it.

## Step 176

- [x] 면 모드에서 면 선택: 선택 면이 Maya 처럼 점 무늬만 (주황 덮개 없음), Preferences > Maya Component Colors 끄면 Blender 주황 강조가 돌아옴. (gui_step134_selection: `show_faces` 꺼짐, 점 사이 회색, 설정 끄면 다시 켜짐)
- [x] Ctrl+G 뒤 Ctrl+Z → 결과 칸 `Undo: Group`. (gui_step176_inputs_undo G2, gui_step161_messages)
- [ ] Shift+Z → `Redo: Group`; 이동 후 Adjust Last Operation 값 바꾸기 → 결과 칸이 `Undo: ...` 로 바뀌지 않음.

## Step 177

- [x] View > Camera Tools > Tumble / Dolly Tool: plain LMB drag tumbles / dollies, the selection stays, Dolly ends on the LMB release, W leaves the tool. (gui_step177_panel_menus)
- [ ] Track Tool LMB drag tracks like Alt+MMB; Q / E / R leave the tool; a plain click (no drag) doesn't select.
- [x] View > Center View of Selection in persp: centre on the selection, rotation kept, distance = eye to selection (Maya viewFit -c). (gui_step177_panel_menus)
- [ ] ... the same through a camera (the camera moves), and it doesn't feel like a zoom.
- [ ] Hover greyed panel menu rows (Shading > Flat Shade All, Show > Controllers, toolbar Resolution Gate, Status Line Render Setup): tooltip + Help Line show the notice, not "No Blender equivalent".

## Step 178

- [x] UV Editor > Modify > Map Border on a shrunk / turned pPlane: every border UV on the 0-1 square, corners 4; Texture Borders / Back-Facing / Match Grid run from the menu. (gui_step178_uv_map_border)
- [ ] UV Editor > Modify > Map Border / Straighten Border / Layout Along / Stack Similar Shells on your own meshes: the result looks like Maya's (border on the 0-1 square, chains straight, shells in one row, similar shells stacked).
- [ ] UV Editor > View > Isolate Select > Add / Remove Selected with Ctrl+1 on: the shown faces follow; Remove All shows everything.

## Step 179

- [x] Lighting/Shading > Break Light Links from the menu on a light + pCube2: the light no longer lights pCube2, still lights pCube1; Light Linking Editor opens light-centric on the selected light. (gui_step179_light_linking)
- [ ] ... render (Cycles / EEVEE): the object goes dark for that light; Make Light Links brings it back.
- [ ] Light Linking Editor: click objects on the right to toggle; Object Centric / Shadow Links switch the lists.

## Step 180

- [x] Layer Editor > Anim: two layers from selected, top layer listed first and BaseAnimation last, row click selects, Mute = NLA track muted, Weight 0.4 = strip influence, Additive = COMBINE. (gui_step180_anim_layers)
- [ ] Layer Editor > Anim: Create Layer from Selected on an animated object, select the layer, move it in the viewport and press S: the motion plays as base + layer; Mute / Solo / Weight change the result like Maya.
- [ ] Keys on the selected layer keep what you see (the layer stores the difference); BaseAnimation selected keys the base.


## Step 181

- [x] Surfaces > Loft on three EP curves: loftedSurface1 is a NURBS surface (5 x 6 CVs) through the three curves, selected lead, lambert1; Revolve = 8 segments, cyclic. (gui_step181_surfaces)
- [ ] Surfaces > Loft on three curves picked in order (last picked = active): the surface passes through them in that order; CV edits in surface edit mode reshape it like Maya CVs.
- [ ] Surfaces > Birail > Birail 1 Tool with a profile touching two rails: the sweep follows both rails whatever order the three curves were picked in.
- [ ] Surfaces > Detach / Insert Isoparms: select a CV row or column in surface edit mode, run the item: the split / new isoparm is at that row; Duplicate NURBS Patch copies the patch around the selected CVs.

## Step 182

- [ ] (step 197 fixed it — same check as Step 197) Hotbox right after F8: the in-view message ("Object selection on…") doesn't cover the hotbox rows.
- [ ] (step 197 fixed it — same check as Step 197) Undo then P / Shift+P: the Command Line result field shows the new command's result, not the old "Undo: …".
- [ ] (step 197: tabs / menus now wrap — same check as Step 197) Attribute Editor tab in a real (non-simulated) session: the dock widens so AE tabs / menus are not cut ("Sele…", "pCub…").

## Step 183

- [ ] Real mouse, Maya menu bar: Edit Mesh > Bevel — click the ❒ = Bevel Options window, click the label = bevel; Create > Polygon Primitives > Cube ❒ = Polygon Cube Options. Try UI scale 1.0, 1.25, 1.5.
- [ ] The same items from the hotbox / Shift+RMB menus still need press-and-hold or Shift / Ctrl+click (no ❒ click there yet).

## Step 184

- [ ] (superseded by Step 193: the ring is no longer lifted) RMB on an object near the bottom of the viewport: the whole marking menu is drawn higher, the list hangs under the ring to the window bottom (Maya); drag onto rows and the ring boxes as drawn; a quick RMB click keeps the menu open (no row runs).

## Step 185

- [ ] Edit mode on a Maya cube (Edge mode), select two edges with a real mouse: thin light-blue wire, the selected edges crisp orange (no cyan band around them); Display > hard edges no longer teal in the Maya layout views; turn the kit's Maya component colours off in the preferences = Blender's sharp-edge colour comes back.
- [ ] Move tool (W) on an object: three plane squares (rim + translucent fill) a little larger and farther out than before, the centre square pale yellow; drag the X arrow = X yellow, centre light blue; Scale (R) the same with the centre cube. Hover = bright yellow.

## Step 186

- [ ] Maya layout Time Slider: small grey labels with a tick under each (1-120 = every 5 frames), the current frame's cell lit with its white number (Blender's blue current-frame box still sits on top); widen / narrow the window and change the range (1-24, 1-1000): the step changes like Maya's; Alt+T bookmark = red bar in a strip on top; keys = red lines on the ticks.

## Step 187

- [ ] Select a cube, Key > Create Character Set: the Time Slider field reads "character1"; select another object (or nothing) and press S = only character1's channels get keys; the field's dropdown > None, then S keys the selection again. Key > Select Character Set Members > character1 selects the cube; Channel Box select Translate X of another object + Key > Add to Character Set adds it.

## Step 188

- [ ] Object in AnimLayer1 with a key on the layer, Auto Key on: move it at another frame = a key on AnimLayer1 (Graph Editor), the pose stays after scrubbing; Channel Box select Translate Y + Channels > Remove From Selected Layers = its layer curve gone; Windows > Relationship Editors > Animation Layers raises the Layer Editor's Anim tab.

## Step 189

- [ ] Status Line: open the Construction History group (▶ after Symmetry), click the button off, Create > Polygon Primitives > Cube = no polyCube1 in Channel Box INPUTS; Ctrl+E on a face = no In-View Editor / polyExtrudeFace; click it on again and both come back. File > New keeps it off.
- [ ] Mesh Display: select two cube vertices, Set Vertex Normal ❒ Y = 1 → the shading turns at those corners; Unlock Normals on one of them = back to the hard face shading. Apply Color on faces in face mode colours only those faces (Solid view > Attribute colour); Modify Current Set with Value 2 brightens; Prelight with a sun bakes lit colours (Cycles). Panel Show > IK Handles hides / shows ikHandle empties; Image Planes too.

## Step 190

- [ ] Create > Polygon Primitives > Pipe / Helix / Gear / Soccer Ball / Super Ellipse / Spherical Harmonics / Ultra Shape: each appears at the origin with Maya's name (pPipe1 …), Channel Box INPUTS shows polyPipe1 … — change Subdivisions Axis / Coils / Sides / Ellipse 0 / Ultra 1 there and the shape rebuilds; Shift+RMB Create marking menu Pipe / Helix / Gear work.

## Step 192

Blindspots of audit 14 (`docs/steps/step_192_remaining.md` §4). Steps 194 / 196 / 197 / 200 addressed all four (audit 15,
`docs/steps/step_201_remaining.md` §2): they should now pass.

- [ ] Animate a cube (keys at 1 and 24), Layer Editor > Anim > Create Layer from Selected: the Time Slider still shows the red key ticks, the Channel Box Translate fields stay red on a key frame, the Graph Editor still lists the cube's curves (Maya shows the selected layer's / base keys). Before step 194 all three went blank.
- [ ] Create > Polygon Primitives > Pipe (also Helix, Gear, Platonic Solid, NURBS Primitives > Sphere) ❒ click: a Maya "Polygon Pipe Options" window opens like Cube ❒ does, not Blender's Adjust Last Operation panel.
- [ ] Key > Create Character Set, then hover Windows > Relationship Editors > Character Sets and Graph Editor Show > Objects > Characters: the tooltip / Help Line must not say "Blender has no character sets".
- [ ] Blender 5.2, Maya Workflow Kit layout: the Time Slider ruler (grey labels, ticks, lit cell) and the character set field show like on 4.5; Create > Polygon Primitives ❒ click from the menu bar opens the option window. (Step 200 ran 5.2 GUI step183 / 187 only — no Time Slider ruler GUI file.)

## Step 193

- [ ] Real mouse, Blender window not maximised (e.g. 1600 x 900): RMB on an object in the middle and near the bottom of the viewport, flick W / N / S without looking (Vertex / Edge / Face) — the ring is drawn at the pointer and every flick picks its item; the list sits beside the ring (W side on a mesh) in one column, all rows reachable by dragging.
- [ ] Same with Shift+RMB (component tools list) and RMB in a UV Editor near its bottom edge.

## Step 194

- [ ] Layered cube (Create Layer from Selected, keys on the layer): clicking AnimLayer1 / BaseAnimation in the Anim tab switches the Graph Editor, Dope Sheet and Time Slider ticks to that layer's keys at once, the cube does not move; layer members show the NLA icon in the Channel Box (Maya teal), channels outside the layer keep red / pink.
- [ ] Layers > Zero Key Layer and Merge Layers from the Anim tab menu: the cube's motion is unchanged after Merge, undo brings the layer back.

## Step 195

- [ ] Channel Box / Attribute Editor / Modeling Toolkit docks are Maya's lighter grey (#444444) with darker value fields; the Layer Editor list stays dark; hovering / clicking fields, dragging channels and scrolling look right (no grey veil over highlighted rows); Preferences > Dock Colors off brings Blender's grey back.
- [ ] A custom (lighter or coloured) Blender theme: the docks are not lifted when the theme's Properties grey is already as light as Maya's.

## Step 196

- [ ] Create > Polygon Primitives > Gear / Pipe / Super Ellipse ❒ and NURBS Primitives > Sphere ❒: Maya's window opens, Create / Apply build the shape with the typed values, Save Settings makes the plain menu click use them; Control > Create Character Set ❒ names the set and its attributes.
- [ ] Curves > Smooth and UV > Merge UVs from the menu feel like Maya (ends kept / UVs of one vertex merged, not every UV to one point).

## Step 197

- [ ] Show an in-view message (F8) or the In-View Editor (Ctrl+E on faces), then hold Space: the hotbox covers them (they come back when it closes).
- [ ] Ctrl+Z after Group, then P / Delete / Ctrl+E: the result field no longer reads `Undo: Group`.
- [ ] Narrow the dock on the Attribute Editor: tabs / menus / Select-Load Attributes-Copy Tab wrap instead of showing "…".
- [ ] Mesh > Cleanup… opens no submenu; its ❒ opens Cleanup Options; Select matching polygons with 4-sided faces selects every quad.
- [ ] Windows > Relationship Editors > Character Sets lists the sets; Graph Editor Show > Objects > Characters lists character rows.

## Step 198

- [ ] Graph Editor > Edit > Transformation Tools > Retime Tool: a real double-click adds a marker; dragging its middle handle retimes smoothly; the low part of the line moves only the marker; the ✕ deletes; Esc ends.
- [ ] Curves > Buffer Curve > Snapshot, edit a key, View > Show Buffer Curves: the grey snapshot shows; Swap Buffer Curve swaps.
- [ ] Curves > Non-weighted Tangents, then drag a tangent handle: after release the handle length goes back to a third of the interval.
- [ ] Switch the big view to the Graph Editor: no Blender sidebar; N still opens it.

## Step 201

Blindspots of audit 15 (`docs/steps/step_201_remaining.md` §4) — step 202 fixed the first three (audit 16,
`docs/steps/step_210_remaining.md` §2): they should now pass — and manual-only checks that steps 199 / 200 left without a group.

- [ ] A cube with an extrude and a kit Wire deformer (Deform > Wire), Edit > Delete by Type > Non-Deformer History: Maya keeps wire1 (moving the curve still deforms the cube). Before step 202 the kit baked the wire's Geometry Nodes modifier into the mesh. Same with a skin on Skin > Normalize Weights > Disable Weight Normalization: the mode must survive.
- [ ] Constrain > Normal (or Tangent) on a cube to a sphere, then Delete the cube (or Edit > Delete by Type > Constraints): no hidden `pCube1_normalConstraint1Aim` empty must stay in Blender's Outliner (View Layer, hidden objects shown). Fixed in step 202 for kit Delete / Edit > Delete / Delete by Type; Blender's own Outliner Delete and X still leave it (step_202.md 「남은 것」).
- [ ] With a kit wire deformer / nCloth / nParticles in the scene, hover Select > All by Type > Wires / nCloths / nParticles and Edit > Delete All by Type > Wires: Maya selects / deletes them (step 202; Wires select the curve, not a wire node). Fluids stay greyed.
- [ ] (step 199) Constrain > Normal: drag the constrained cube over a sphere with a real mouse — it turns to the surface at once, no lag; Skin > Normalize Weights > Disable Weight Normalization, then paint one joint's weight down: that part of the mesh pulls toward the world origin like Maya.
- [ ] (step 200) Blender 5.2, Maya Workflow Kit layout: dock grey (#444444, Layer Editor list dark), Graph Editor Retime Tool lines / handle, buffer curves and a layered cube's layer curves draw like on 4.5 (step 200 ran 5.x GUI step183 / 187 only).

### Step 202 — Audit 15 fix batch

- [ ] Windows 125 % (UI 1.25), Maya Workflow Kit layout 새로 열기: Time Slider ruler 가 1.0 때와 같은 비율로 높아지고 (header 아래 ~45 px), 현재 프레임 칸 회색 (#525252) 이 Blender 파란 상자 아래로 보임; 직접 Time Slider 높이를 바꾼 뒤엔 다시 맞추지 않음.
- [ ] Channel Box dock 을 손으로 좁히면 메뉴 바가 "Channels Edit Object" / "Show" 두 줄로 (글자 잘림 없음), 넓히면 한 줄.
- [ ] 큐브 RMB > Vertex: 왼쪽 Outliner 에 모드 아이콘 / 점 열이 없고, persp / top / defaultLightSet 행 아이콘이 pCube1 아이콘과 같은 x.

### Step 203 — Graph Editor depth 3

- [ ] Graph Editor: List > Auto Load Selected Objects 켜진 동안 Load / Add Selected Objects 줄이 회색; 끄고 Load → 다른 오브젝트를 선택해도 목록 그대로; Auto Load 다시 켜면 선택을 따라감.
- [ ] 채널 행을 하이라이트 → Curves > Pin Channel: 다른 오브젝트를 선택해도 그 채널 행과 커브가 남고 똑바른 핀 아이콘, Unpin 하면 사라짐.
- [ ] 회전 키가 X / Y / Z 다른 시각에 있는 큐브: Curves > Change Rotation Interp > Synchronized Euler → 세 채널에 같은 시각 키, Rotate X 키를 끌면 Y / Z 키도 같이 움직임; Quaternion Slerp → 뷰포트 회전이 최단 경로, Independent Euler 로 되돌리면 원래 커브.

### Step 204 — Animation layers 4

- [ ] Layer Editor Anim 탭: AnimLayer1 클릭, AnimLayer2 Ctrl+클릭 → 둘 다 선택, Graph Editor 에 두 레이어 커브 (하나는 흐리게); 흐린 커브를 클릭하면 그 레이어가 편집 가능해짐.
- [ ] 레이어 RMB → Duplicate Layer 두 번 → `AnimLayer1_copy` 위, `AnimLayer1_copy1` 그 아래; Ctrl+Z 한 번에 하나씩 사라짐.
- [ ] Zero Weight and Key Layer 버튼 → 레이어 weight 0 + Time Slider 에 키, 되돌리기 한 번.

### Step 205 — Deform 2

- [ ] 스킨 바인드한 실린더에 Deform > Tension: 관절을 굽히면 접힌 쪽 면이 덜 찌그러짐 (Maya 처럼), AE tension1 탭의 Smoothing Iterations 를 바꾸면 바로 반영.
- [ ] Deform > Jiggle 뒤 큐브를 키로 움직이고 재생: 멈출 때 출렁임, 처음 프레임으로 되감으면 다시 원래 모양.
- [ ] Constrain > UV Pin 으로 Locator 를 변형되는 메시에 붙이기: 메시가 휘면 Locator 가 표면을 따라감, Channel Box 의 Translate / Rotate 는 0.

### Step 206 — UV Editor depth 2

- [ ] UV Editor에서 면 하나 선택 → Modify > Cycle 을 여러 번: UV 가 한 꼭짓점씩 돌고, 4 번이면 (사각형) 원래 자리.
- [ ] pPlane 4x4 의 두 꼭짓점 (사각형의 마주보는 모서리) 선택 → Cut/Sew > Create Shell (Grid): 그 사이 면들이 0-1 격자 셸이 됨, 나머지와 분리.
- [ ] 구를 Planar 로 펼친 뒤 Cut/Sew > Auto Seams → Modify > Unfold: 극을 지나는 한 줄 이음새로 한 셸로 펼쳐짐.
- [ ] UV 하나 선택 → Cut/Sew > Split → Move 툴로 끌면 면마다 따로 움직임.
- [ ] 아래 왼쪽 U / V, 아래 오른쪽 셸 · 겹친 UV · 뒤집힌 UV 수가 선택을 바꿀 때 바로 갱신되는지 (0.25 초 안), View > Heads-Up Display 로 끄고 켜기.

### Step 207 — Curves 3

- [ ] CV 커브를 그린 뒤 Curves > Bend / Curl / Scale Curvature (❒ 옵션 창 값 바꿔서도): Maya 처럼 휘고 감기는지, 편집 모드에서 CV 범위만 골라도 그 뒤 CV 가 따라가는지.
- [ ] Curves > Lock Length 뒤 편집 모드에서 CV 하나를 Move 툴로 끌기: 다른 CV 가 따라와 길이가 유지되는지 (끄는 동안 튀지 않는지), Unlock 뒤에는 따라오지 않는지.
- [ ] CV 하나 선택 → CV Hardness: 그 CV 에서 커브가 꺾이며 지나감; 끝 CV 는 아무 일 없음.
- [ ] NURBS Plane 선택 → Duplicate Surface Curves: 보이는 isoparm 마다 커브 (2×2 스팬이면 6 개).

### Step 209 — Reference Editor

- [ ] File > Reference Editor with two references — click a row (selected highlight), the
      load check box unloads / loads the objects in the viewport, Reference > Replace Reference opens the file browser
      at the current file, the Namespace field renames the `ns:` objects in the Outliner, Read Only blocks moving them.

### Step 210 — Audit 16 blindspots

Blindspots of audit 16 (`docs/steps/step_210_remaining.md` §4) — expected to show a difference today.

- [ ] Skin a cylinder to two joints, select some vertices, Windows > General Editors > Component Editor: Maya shows an editable skinCluster weight table (type 0.5 in a cell). Today it opens Blender's Spreadsheet (read-only, no skin weights tab); Shape Editor opens the Properties Data tab, Connection Editor / Expression Editor the Drivers editor (NB12).
- [ ] Windows > Relationship Editors > Light Linking: Maya opens the Light Linking editor like Lighting/Shading > Light Linking Editor does. Today it opens the Properties Object tab instead of the kit's step 179 editor (NB13).
- [ ] After two Create References with namespaces `prop` / `prop1`, Windows > General Editors > Namespace Editor: Maya lists `:`, `prop`, `prop1` and can rename / merge them. Today the item is greyed (NB14).
- [ ] pCube1 selected, Ctrl+C then Ctrl+V: Maya pastes `pasted__pCube1`. Today the copy is `pCube1.001` with a `.001` shape (NB15). Also: Create > Sets > Set three times, delete set2, make another set → `set4` if Maya's one-past-the-highest rule (seen on transforms / joints / history nodes, not yet on sets) holds; the kit makes `set2` again. Same for display layers (`layer`N) and animation layers.
- [ ] Blender 5.2 (and 5.0), Maya Workflow Kit layout: Reference Editor window, Graph Editor pin / kit list, Layer Editor two selected anim layers (dimmed curves), Deform > Tension / Jiggle, UV Editor HUDs, Script Editor `cmds.file(new=True, f=True)` work like on 4.5 — steps 202–209 ran no 5.x headless or GUI files (NB16).

### Step 211 — Audit 16 fix batch (#117)

- [ ] Windows > Relationship Editors > Light Linking ▸ Light-Centric / Object-Centric: the kit Light Linking Editor opens in that mode (not the Properties Object tab).
- [ ] pCube1 selected, Ctrl+C, Ctrl+V: a new `group` holds `pasted__pCube1` (shape `pasted__pCubeShape1`) at the cube's place, only `group` is selected; a second Ctrl+V makes `group1` / `pasted__pCube2`. Create > Sets > Set ×3, delete set2, another set → `set4`.
- [ ] File > New Scene (Maya layout): the Outliner starts with greyed persp / top / front / side, new objects follow in creation order (also after making 10+ objects and after grouping three cubes: the group lists them in creation order), sets last. Click persp: the Channel Box shows persp (Visibility off). Edit > Delete with persp active and a cube selected deletes only the cube.
- [ ] Attribute Editor on a cube: the node tabs are one row (pCube1 / pCubeShape1 / polyCube1 / initialShadingGroup / lambert1); drag the dock narrower: ◀ ▶ appear around the current tab instead of the tabs stacking; Select / Load Attributes / Copy Tab stay one row at the fitted width.
- [ ] nHair > Modify Curves > Bend ❒ / Curl ❒ / Scale Curvature ❒ open the same Maya windows as Curves > Bend ❒ / Curl ❒ / Scale Curvature ❒.

### Step 213 — Component, Shape and Connection Editors (#119)

- [ ] Skin a cylinder, select a few vertices, Windows > General Editors > Component Editor: Smooth Skins shows the joints + Total; type 0.5 in a joint cell — the other joints share the rest proportionally (Total stays 1.000); set a Hold to on and edit again: the held column stays. Polygons tab: type a new vertex.y and see the vertex move; Ctrl+Z undoes it.
- [ ] Windows > Animation Editors > Shape Editor on pCube1: Create Blend Shape, Add Target (pCube2, red Edit), move vertices in Edit Mode, turn Edit off, drag the weight slider: the shape blends; Shapes > Key keys the weight; Reset sets 0.
- [ ] Windows > General Editors > Connection Editor with two objects selected: pick translate on the left, translate on the right: the right object follows the left; pick the right translate again: the connection breaks and the object stays where it was.

## Step 214 — Render parity 2

- [ ] Create > Lights > Ambient Light in a scene with a cube, Render > Render Current Frame (Cycles): the cube is lit from all sides, the background stays as before; Attribute Editor shows Ambient Light Attributes (Color, Intensity, Ambient Shade 0.45).
- [ ] Create > Lights > Volume Light, scale it to 5 around the cube, render (Cycles): faces nearer the centre are brighter, nothing lit outside the sphere.
- [ ] Attribute Editor of lambert1: Diffuse 0.8; set it to 1 and render — the cube gets brighter by 1.25 x.
- [ ] In Maya mode with the mouse over the Outliner, F12 opens Blender's Render window with the cube lit (no lights in the scene); over the 3D View F12 stays Maya's UV selection mask.

## Step 215 — Maya Preferences window and Hotkey Editor (#121)

- [ ] Windows > Settings/Preferences > Preferences: click through the Categories (the list scrolls); change Settings > Linear to millimeters and Time Slider > Framerate, then Cancel: both come back. Change them again and Save: they stay.
- [ ] In Preferences > Undo, the "Blender Preferences" button opens Blender's Preferences on System (Undo Steps); the kit didn't change it.
- [ ] Windows > Settings/Preferences > Hotkey Editor: search "duplicate", pick Duplicate, Assign New Hotkey..., press Ctrl+Shift+F9: Ctrl+Shift+F9 duplicates in the viewport; Restore brings Ctrl+D back. Quit without saving preferences: the change is gone next start (Blender's Save Preferences keeps it).

## PR #125 follow-up (0.5.0) — joints, Channel Box, Paint Skin Weights

- [ ] F8 on a selected skeleton: Edit mode (joint positions editable), F8 again: Pose mode with joints selectable. In
  Maya 2022, F8 with a joint selected goes to component mode, the selection empties and no
  joint component mask (joint pivot / local rotation axis / rotate pivot / scale pivot) is on — Maya's F8 does nothing
  useful on joints. The kit's Edit mode = "the joint's components" is a Blender stand-in (`delegated`); the in-view
  message still says object / component selection.
- [ ] Select a skeleton in the Outliner: Pose mode starts; the Channel Box shows the lead joint's channels once a joint
  is clicked (Maya would show the root joint at once — check it is not confusingly empty). **Step 217**: the root joint
  is now selected at once (Maya 2026) — check it.
- [ ] Mouse wheel over the Channel Box: three rows per notch, values unchanged, the Layer Editor below doesn't move.
- [ ] Drag the Move manipulator: Channel Box numbers follow during the drag; with nothing moving, no constant redraw
  (CPU idle in Task Manager).
- [ ] Skin > Paint Skin Weights (plain click): painting starts, the Channel Box still shows channels; Skin > Paint Skin
  Weights ❒ opens Tool Settings with Skin Clusters / Influences / Brush / Visualization / Stroke / Stylus Pressure /
  Display. W leaves painting with the mesh selected.
- [ ] Tool Box: the magnifier under the Outliner button opens command search; the column is as wide as before 0.5.0.
- [ ] Preferences > Add-ons > Maya Workflow Kit: Armature Mode Picker / Pulse Armature Mode off by default; turned on,
  the picker appears at the start of the main viewport header with a skeleton active and its button pulses softly.

## Step 217 — Bake Simulation, Joint Tool end, pick walk (Issue #128)

- [ ] Key > Bake Simulation ❒ on a constrained cube: the window shows "Disable implicit control" (on); Bake keeps the
  motion, the constraint stays in the Channel Box INPUTS but off (muted), the channels are no longer blue; turning
  "Keep unbaked keys" off removes keys outside the range and still keeps the constraint.
- [ ] Skeleton > Create Joints, three clicks, Enter: the root joint is selected and the Select tool is active (Maya
  2026); clicking near a big joint's sphere (zoomed in) branches from it, a click just outside the drawn sphere starts
  a new skeleton — check the hit area feels like the drawn ball.
- [ ] Generated Rigify human: arrow keys walk from control to control (no MCH / ORG bones selected); turn on the MCH
  collection and the arrows walk into it; Preferences > Add-ons > Maya Workflow Kit > "Pick walk skips hidden bone
  collections" off = plain hierarchy. Check `shin_tweak.L` Up lands somewhere a Maya user expects (decision 6, weakest
  point).
- [ ] Control > Tag As Controller / Parent Controller on three bones: Up from a child goes to the parent controller.

## Step 218 — paint keys, Spline IK on a curve, curve clusters, deformer order (Issue #129)

- [ ] Paint Skin Weights: select a few vertices in Edit mode, enter the tool — the vertex mask is on and Alt+F floods
  only them; Ctrl+. / Ctrl+, cycle Paint / Select / Paint Select and painting feels right in each.
- [ ] Influences list: the menu button next to the search field shows Lock Selected … Remove Affected Vertices first;
  Select Vertices shows the joint's vertices.
- [ ] Skeleton > Create IK Spline Handle ❒ with Auto create curve off: click root joint, end joint, then a curve —
  the chain lies on the curve (Root on curve); Snap curve to root moves the curve to the root.
- [ ] Select two CVs of that curve, Deform > Cluster: moving the cluster handle bends the spine chain.
- [ ] RMB > Inputs > All Inputs… on a skinned mesh with a cluster: ▲ / ▼ swap the cluster and the skin, the mesh
  updates, Ctrl+Z restores (check the popup stays usable after a click).

## Step 221 — quaternion bones in the Channel Box (Issue #131)

- [ ] Generated Rigify rig, pick a control (Pose): the Channel Box shows Rotate X / Y / Z; type 270 in Rotate Y — it
  stays 270; MMB-drag Rotate X turns the control; S keys it and the Graph Editor shows Rotate W / X / Y / Z.

### Step 224 — Paint Skin Weights numeric / skin clusters
- [ ] Visualization > Numeric > Show Numbers: labels stay put during a stroke and update when it ends; with many vertices in view the labels follow the brush as the mouse moves (no lag).
- [ ] Second Bind Skin on a skinned mesh: the question pops up at the mouse, Yes is greyed, No / moving away closes it.

### Step 226 L1 — control shapes (bone Custom Shapes, Issue #136)
- [ ] Command Line `cmds.parent('nurbsCircleShape1', 'joint1', s=True, r=True)` on a joint chain: the circle draws around joint1 (CV local values in the joint's frame), `nurbsCircle1` stays as an empty transform; a click on the circle's wire in Object Mode picks joint1 (Pose, Channel Box = joint1), a click inside the circle picks nothing; dragging right after the click on the wire moves the joint.
- [ ] Same with a Rigify-generated rig: clicking a widget's wire picks its control bone; File > Export All (FBX) has no WGT- or Shape objects when re-imported.

## Step 227 — corrective shapes (Pose Editor)
- [ ] Pose Editor > Add Shape on a skinned arm at the bent pose: Edit enters Edit Mode on the deformed cage; sculpted vertices land where you put them on the bent arm, and at rest the corrective shows nothing (weight 0).
- [ ] Shape Editor: dragging the target slider through an in-between feels like Maya (in-between shape reached at its weight, no jump).

## Step 237 — Four View = four real panels
- [ ] Space tap over a panel with a real mouse: that panel fills the viewport at once and takes keys right away (event simulation lost the first key sent in the same tick as the move).
- [ ] Dragging the edges between the four panels feels like Maya's pane dividers (Blender moves aligned edges together; Maya's horizontal divider spans the whole width).

## Step 241 — Joints move after placement (#156)
- [ ] Joint Tool 3 clicks → W → drag the Move manipulator's arrows / centre with a real mouse: the joint and its children move, the parent stays (tests/gui/gui_step241_joint_move.py drags the joint itself).
- [ ] Skinned skeleton → Skin > Move Skinned Joints → drag the Move manipulator with a real mouse: the joint moves, the mesh stays (simulated presses on the manipulator after the menu item didn't reach the gizmo; the GUI test runs the same transform from code).
- [ ] With the Move tool on an unskinned skeleton, press E / R / Q: the same joints stay picked in Pose mode and the Channel Box shows their channels.

## Step 243 — Moving a joint keeps the parent's Maya frame (#160)
- [ ] Joint Tool on a bent chain → W → drag joint2 with the manipulator arrows (real mouse): joint1's local axes (Display > Joint axes) keep their direction; the Channel Box Translate of joint2 gets Y / Z values like Maya.
- [ ] Hold D (or press Insert) and drag a joint: its children stay; release D: the next drag moves the subtree again. Tool Settings > Move Settings > Preserve Children shows the same state.
- [ ] Type `+=2` in the Edit-mode Channel Box Translate Y of a joint: it moves, its children follow (or stay with Preserve Children on); Ctrl+Z puts it back in one step.

## Step 244 — Joint orientation = Maya 2025+ factory (#161)
- [ ] Joint Tool in the side and top views (real mouse): the secondary axis follows the bend like Maya (Display Local Axis), a zig-zag flips at the bend joint, the end joint copies its parent's axes.
- [ ] Skeleton > Orient Joint ❒: Orient Joint to World, Primary / Secondary axis and Auto orient secondary axis change the axes as in Maya; a rotated joint prints "Skipping <joint>: It has non-zero rotations."
- [ ] AE joint tab: Joint Orient reads Maya's values; Segment Scale Compensate check box off -> scaling the parent shears the child like Maya SSC off.

## Step 245 — IK RP like Maya (#162)
- [ ] Skeleton > Create IK Handle on a bent arm with a real mouse, then drag the handle with the Move manipulator: the elbow stays on the pole side like Maya, no flip when the goal passes near the shoulder.
- [ ] Channel Box: type Twist 45 / -45 on the handle, and Pole Vector X/Y/Z values: the arm plane turns like Maya's; key Twist over frames and play: no visible lag.
- [ ] Constrain > Pole Vector with a locator, then move the locator: the knee follows it.

## Step 246 — Skeleton menu commands with Maya meaning (#163)
- [ ] Skeleton > Insert Joints with a real mouse: press on a joint, drag — the new joint follows the cursor, the joint's children stay where they are; a click without a drag leaves the new joint on the clicked one; Enter / Q ends the tool.
- [ ] Skeleton > Remove Joints on a skinned joint, then pose the skeleton: the vertices it drove follow the remaining joints (Blender divides by the weight sum while Maya leaves the weights unnormalised — compare the look with Maya).
- [ ] Skeleton > Connect Joint ❒: Connect joint / Parent joint; pick a joint of another skeleton first (Shift-click into the second skeleton): both become one skeleton, its skinned mesh still deforms.
- [ ] Skeleton > Mirror Joints on a posed arm (rotate values set): the copy shows the same Rotate X / Y / Z in the Channel Box and mirrors the pose.

## Step 247 — Skin basics corrections (#164)
- [ ] Skin > Prune Small Weights ❒: "Prune below" changes the threshold; with some vertices selected in Edit / Weight Paint (vertex mask) only those change; a locked joint keeps its small weights.
- [ ] Skin > Edit Influences > Set Max Influences...: the dialog shows Max influences 5; 2 on a skinned arm — the deformation looks like Maya's (weights recomputed by distance, painted weights replaced).
- [ ] Bind a skeleton while it is posed, pose it further, Go to Bind Pose: Maya returns to the pose at bind; compare the mesh (Blender's skin binds at the rest pose — see step_247.md 남은 것).
- [ ] Skin > Mirror Skin Weights on a character with uneven topology (left / right vertices not at mirrored places): the copied side looks smooth like Maya (closest point + interpolation), no stair steps.

## Step 248 — Pick walk order and joint display (#165)
- [ ] Build a spine with three branches by hand (Joint Tool: click spine, then L_arm, R_arm, neck branches): ↓ goes to the first branch made, ← / → walk the branches in the order they were made and wrap, like Maya.
- [ ] P a branch to another joint and back: it is now the last child (→ from the others reaches it last), like Maya.
- [ ] Channel Box: a joint shows Radius under Visibility; typing 2 makes the joint easier to click (larger pick sphere); Display > Animation > Joint Size... scales all of them.
- [ ] Display > Transform Display > Local Rotation Axes with joints selected: the skeleton's axes show (Blender shows all joints of that skeleton, Maya only the selected ones).

## Step 249 — Spline IK twist and roll (#166)
- [ ] Skeleton > Create IK Spline Handle on a spine, bend the curve by moving CVs, then drag the handle's Twist in the Channel Box (MMB virtual slider): the in-between joints turn smoothly like Maya; Twist Type Ease In / Ease Out / Ease In Out moves the turn toward the end / root / middle.
- [ ] Roll turns the whole chain from the root like Maya; key Twist over frames and play: no lag.
- [ ] Delete the ikHandle: the chain stops following the curve (Maya deletes the solver with the handle).

## Step 250 — Weight Blended and DQ parity (#167)
- [ ] Bind a character, AE skinCluster1 > Skinning Method Dual Quaternion: elbows / shoulders keep their volume like Maya DQ; Weight Blended: paint the `blendWeights` vertex group (Weight Paint) — 1 = DQ, 0 = linear, like Maya's Paint Skin Weights > DQ blend weights.
- [ ] With a scaled joint (squash / stretch rig) and Dual Quaternion, compare with Maya: Blender scales about the joint, Maya about the origin (known difference, step_250.md).

## Step 254 — #170 / #172 (real mouse, Blender 5.2.x and 4.5)
- [ ] Fresh Blender 5.2.x: Edit > Preferences > Get Extensions > Install from Disk (the zip), keep the mouse on the Preferences window: the top menus of the main window still open on the first click; the welcome dialog appears only after the mouse moves into the main viewport.
- [ ] Same on 4.5.
- [ ] Maya mode, UV Editing workspace, a 50 k-face mesh: click faces, W-drag a face selection and a UV shell, Cut UV Edges, Ctrl+Z — no freeze, no crash; the UV HUD and the thick texture borders come back right after each drag.

## Step 255 — #171 Rigify controls keep Pose mode (real mouse)
- [ ] Maya mode, Rigify human rig, Pose mode: click IK hand / foot, torso, hips widgets one after another with the Select tool and with W — the rig never leaves Pose; a click on empty space only clears the selection; a click on the character mesh selects the mesh.

## Step 256 — UV Shell selection (#172, real mouse)
- [ ] Maya mode, a mesh with several UV shells: RMB > UV > UV Shell (or Alt+F12), click a face in the viewport — its whole UV shell is selected; Shift toggles a shell, Ctrl removes, a click on empty space clears; a marquee over part of a shell selects the whole shell; the UV Editor shows the same selection, and a click there picks shells too.

## Step 260 (#174 #177)
- [ ] Windows, real keyboard: hold Space 5 s over the viewport → the hotbox stays up, no Four View toggle; release → nothing; tap → Four View.
- [ ] Linux X11 (if available): the same hold → no toggle.
- [ ] Hotbox: click a menu name → the menu stays open, nothing runs; press a name and drag down onto a row, release → that row runs.
- [ ] Emulate 3 Button Mouse on: Maya mode preferences / welcome dialog show the Alt+LMB hint.

## Step 265 — #178 D hold with a real keyboard (key repeat)

- [ ] Hold D for a second (the OS repeats the key), then drag a Move arrow / the centre: the pivot moves at once, on
      the first try (before: only when the drag crossed Blender's threshold between two key repeats). Same with X / C / V
      held + a manipulator drag (grid / curve / point snap).
- [ ] With another add-on that binds D in Object Mode (e.g. a draw / annotate add-on): Maya mode on → D = pivot edit;
      Maya mode off → that add-on's D again.

## Step 267 (#174 #177 follow-up)
- [ ] Windows 11, Blender 5.2.x, a plain keyboard (no remote desktop / remapper): hold Space 5 s over the 3D View → the
      hotbox stays up and the Four View never toggles; release → it closes; a quick tap → Four View once. Repeat with a
      keyboard that has its own software (G Hub / Synapse) running.
- [ ] Blender 5.1, a 2-button mouse with a wheel: Emulate 3 Button Mouse off → Alt+LMB tumbles; on → no tumble, and the
      welcome dialog / add-on preferences show the Emulate hint.
