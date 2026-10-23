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
- [ ] (step 2) 환경설정 > Keymap 을 Blender 로 바꾸고 재시작 → Blender 유지. 애드온 환경설정의 「Activate Maya Keymap」 → Maya 로 돌아옴.
- [ ] (step 2) 첫 실행 스플래시 Quick Setup 이 Keymap 을 "Blender" 로 표시 — Continue 해도 Maya 가 유지되는지.

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
- [ ] (step 4) 애드온 환경설정 「Maya Navigation Preferences」 끄기 → Preferences > Navigation 값이 켜기 전으로; 다시 켜기 → Maya 값.

### Step 5 — 레이아웃·테마

- [ ] (step 5) 애드온 환경설정 「Install Maya Layout」 → File > New 에 Allset 이 보이고, 선택하면 General 레이아웃(좌 Outliner / 가운데 뷰포트 / 우 Layer Editor·Properties / 아래 타임라인)으로 새 파일.
- [ ] (step 5) 「New File with Maya Layout」 → 확인 창 후 같은 결과. 「Remove Maya Layout」 → File > New 목록에서 사라짐.
- [ ] (step 5) 「Apply Maya Theme」 → Maya 와 나란히 놓고 회색·선택 색·그라디언트 비교 ([K] 값 조정 필요 여부). 「Restore Previous Theme」 → 원래 테마.
- [ ] (step 5) Allset 을 끈 상태에서 Allset 템플릿으로 새 파일 → Allset 이 다시 켜짐.
- [ ] (step 5) 오브젝트 와이어프레임(4) 색: 비선택 짙은 파랑, 선택 초록, 리드 흰색이 Maya 와 비슷한지.

### Step 6 — Channel Box / Layer Editor

- [ ] (step 6) 사이드바(N)에서 "Channel Box" 탭 한 번 클릭 -> 이후 그 화면은 Channel Box 를 기억 (템플릿에서 자동 지정 불가).
- [ ] (step 6) 오브젝트 3개 선택 -> Translate X 에 값 입력 -> 셋 다 같은 값; Ctrl+Z 한 번에 되돌림.
- [ ] (step 6) Translate X 이름 클릭 -> 뷰포트 MMB 좌우 드래그로 값 변화 (Ctrl 느리게, Shift 빠르게), 커서가 화면 끝에서 감겨도 계속; ESC 로 취소. 채널 선택 해제 후 MMB -> Move 툴 드래그.
- [ ] (step 6) Channels 메뉴: Key Selected -> 타임라인에 키, 필드 붉게; Lock Selected -> 회색·편집 불가; Hide Selected -> 행 사라짐, Show All -> 복귀.
- [ ] (step 6) Settings 메뉴 속도 Slowest~Fast, Hyperbolic -> 슬라이더 감도 (Maya 와 체감 비교).
- [ ] (step 6) Layer Editor: 선택으로 새 레이어 -> V 끄면 숨김, T -> 와이어·선택 불가, R -> 선택 불가, P 끄고 재생(Alt+V) -> 재생 중만 숨김. 레이어 삭제 -> 원상.

### Step 7 — 메뉴바·메뉴셋, Status Line, 커맨드 라인, Help Line

- [ ] (step 7) 저장한 사용자 환경설정으로 Blender 시작 → File > New > Allset: 활성 키맵이 계속 "Maya" 인지 (GUI 테스트의 `--factory-startup` 에서는 Blender 로 돌아감).
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
- [ ] (step 9) 옵션 박스 `[]` 위에서 놓기 → 실행 후 Adjust Last Operation 팝업 (예: Face 모드 Poke Face `[]`); 툴(Multi-Cut `[]`) → 툴 + Tool Settings 팝업. 베벨처럼 모달인 것은 팝업 없이 모달.
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

- [ ] (step 12) Allset 레이아웃: 메뉴바 아래 Status Line, 그 아래 셸프 (Maya 와 같은 순서), 창 크기를 바꿔도 띠가 두 줄 높이로 남는지.
- [ ] (step 12) Poly Modeling 큐브 버튼 클릭 → pCube1, **더블클릭** → 큐브 하나 + Adjust Last Operation 팝업 (두 개 생기지 않음), Ctrl+클릭 → 옵션.
- [ ] (step 12) 탭 드롭다운 / ◀ ▶ 로 Rigging·Animation·Rendering 전환, 다시 시작해도 마지막 탭 유지 (환경설정 저장 시).
- [ ] (step 12) 톱니 > New Shelf → Add Button(스크립트 한 줄, 아이콘 이름) → 클릭 실행, Edit/Delete Button, Add Last Command (커맨드 라인 실행 후), 다시 시작해도 사용자 셸프가 남음.
- [ ] (step 12) 팩토리 레이아웃에서 Windows > UI Elements > Shelf 로 띠 추가/제거, 다른 Image Editor 는 평소처럼 보임.

### Step 13 — 배포

- [ ] (step 13) 실제 사용자 설정(새 프로필)에서 zip 을 끌어다 놓아 설치: Maya 키맵·내비게이션 적용, Quick Setup 창에서 Continue 를 눌렀을 때 키맵이 Blender 로 바뀌는지 (바뀌면 Activate Maya Keymap).
- [ ] (step 13) Install Maya Layout → File > New > Allset → Blender 재시작 뒤에도 레이아웃·키맵 유지, Remove Maya Layout 후 템플릿 목록에서 사라짐.
- [ ] (step 13) 비활성화 → 키맵·내비게이션·Image Editor 헤더가 원래대로, 다시 활성화.

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

- [ ] (step 21) Allset 레이아웃 새 씬에서 Create > Polygon Primitives > Cube 의 화면 크기를 Maya 2022 새 씬 기본 persp 와 비교 (뷰 거리·클립은 Maya 값이지만 Blender 뷰포트 렌즈 화각이 다를 수 있음). 1 cm 큐브를 가까이 텀블·돌리·W 이동 했을 때 클립 잘림·그리드(cm 간격)·매니퓰레이터 감각.
- [ ] (step 21) Maya 에서 내보낸 FBX(cm)를 File > Import 로 가져와 Create 큐브와 같은 크기인지, Maya Units 켬/끔 둘 다.

### Step 22 — 매니퓰레이터 Shift+드래그 복제

- [ ] (step 22) W/E/R 툴에서 기즈모 화살표·평면·중앙·회전 링·스케일 핸들을 Shift+드래그 → 사본이 변환되고 원본 제자리. Shift 를 끝까지 누른 채 끌어도 느려지지 않는지, 드래그 도중 Shift 를 떼었다 다시 누르면 Blender 정밀 모드가 되는지. Maya 2022 의 같은 동작과 손 감각 비교.
- [ ] (step 22) Shift+클릭(드래그 없음), 드래그 중 RMB/Esc 취소 때 사본이 남는지 Maya 와 비교. Ctrl+Z 한 번에 사본까지 사라지는지.
- [ ] (step 22) 라이트(스포트 크기 등) 기즈모를 Shift+드래그 했을 때 복제가 일어나지 않아야 함.

### Step 24 — 컴포넌트 Delete

- [ ] (step 24) Maya 2022 와 같은 메시에서 면·엣지·정점(모서리 정점, 3개 이상 엣지 정점, 경계 정점) Delete 결과 비교. 경계 엣지만 선택하고 Delete 했을 때 Maya 경고와 비교.

### Step 25 — cm 그리드·스냅

- [ ] (step 25) Allset 레이아웃에서 확대/축소하며 그리드 단계(1 cm → 10 cm → 1 m)가 바뀔 때 X 홀드 스냅 간격이 따라 바뀌는지, Maya 2022 그리드 스냅 감각과 비교.

### Step 26 — Smart Extrude

- [ ] (step 26) 면·엣지 선택에서 이동/회전/스케일 기즈모 Shift+드래그 → 압출 후 변환; Shift+클릭, RMB/Esc 취소 → 아무것도 남지 않음; 그 뒤 Ctrl+Z / Ctrl+Shift+Z 가 앞 작업을 망가뜨리지 않는지. Maya 2022 와 손 감각 비교.
- [ ] (step 26) 스포트 라이트 선택 + 라이트 기즈모(크기·블렌드) Shift+드래그 → 복제 안 됨.

### Step 27 — 매니퓰레이터 크기·뷰 키

- [ ] (step 27) = / - 몇 번 눌러 매니퓰레이터 크기 변화 폭을 Maya 2022 와 비교; 애드온을 껐다 켜면 원래 크기. Home 이 Maya 기본 뷰처럼 느껴지는지 (Allset 레이아웃 cm 장면에서). PgUp/PgDn 단계 변화를 3 모드에서 비교.

### Step 28 — MMB 활성 핸들

- [ ] (step 28) W/E/R 에서 축·평면·중앙 핸들을 한 번 끈 뒤 뷰 아무 곳 MMB 드래그 → 그 핸들로 변환; 툴을 바꿨다 돌아와도 유지; 같은 툴 키 다시 탭 → 자유. Maya 2022 와 손 감각 비교 (회전 MMB 드래그 방향 포함). Channel Box 채널 선택 시 MMB = 슬라이더가 우선.

### Step 29 — 재질 지정

- [ ] (step 29) 아무것도 선택하지 않고 오브젝트 위 RMB → Assign Favorite Material ▸ / Assign Existing Material ▸ / Assign New Material... → 커서 아래 오브젝트에 지정; 선택이 있으면 선택에 지정. 뷰 아래쪽 오브젝트에서 RMB 했을 때 목록·하위 메뉴가 잘리지 않는지. Maya 2022 와 비교.
- [ ] (step 29) 클릭 모드(RMB 짧게 클릭)에서 항목을 클릭했을 때 손을 뗄 때 실행되는 감각이 어색하지 않은지 (모든 클릭 모드 항목이 버튼을 뗄 때 실행).
- [ ] (step 29) 편집 모드 면 선택 → Shift+T → 종류 검색 → Enter: 그 면만 바뀜; 정점/엣지 모드는 오브젝트 전체. Maya 의 컴포넌트 재질 지정과 비교. 렌더/Material Preview 에서 색 차이 확인.

### Step 30 — 선택 감각

- [ ] (step 30) 편집 모드에서 Maya 처럼 뒤쪽 정점까지 마키로 잡히는지 (Select 툴, Move 툴 빈 곳 드래그, 라쏘). 드래그 중 숨은 엣지가 비쳐 보이는 것이 거슬리지 않는지, 놓은 뒤 X-Ray 버튼이 원래대로인지. Maya 2022 와 비교.
- [ ] (step 30) 정점 모드에서 마우스 아래 정점 하이라이트(작은 점)가 Maya 프리셀렉트처럼 도움이 되는지, 큰 메시에서 호버가 느려지지 않는지. 엣지/면 모드는 하이라이트 없음.
- [ ] (step 30) 긴 모델링 세션에서 언두가 256 단계까지 되는지, 메모리 사용이 괜찮은지. 애드온을 끄면 Undo Steps 가 원래 값.

### Step 31 — 레이아웃 다듬기

- [ ] (step 31) Allset 레이아웃 왼쪽 Outliner 에서 긴 이름(pCylinder12, group3 아래 3 단계)이 잘리지 않는지, 컬렉션 행 없이 오브젝트만 보이는 것이 Maya Outliner 처럼 느껴지는지. 새 컬렉션을 만든 경우 Layer Editor 쪽에서만 보이는 것이 혼란스럽지 않은지.
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

- [ ] (step 38) Channel Box 값 필드를 클릭해 숫자 입력 → Enter: Maya 처럼 바로 적용되는지. `+=5`, `-=2`, `*=2`, `/=2` 가 여러 오브젝트에서 오브젝트마다 자기 값 기준으로 적용되는지. 단위 없는 숫자 = cm (Allset 템플릿), `5 m` 도 되는지.
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

- [ ] (step 42) 실제 설치 (환경설정 > Get Extensions > Install from Disk 로 zip) 직후 환영 대화상자가 커서 근처에 뜨는지, Blender 스플래시와 겹쳐도 "Make Blender Maya" 를 누를 수 있는지. 누르면 Maya 레이아웃 + 테마, 스플래시 없음.
- [ ] (step 42) zip 을 Blender 창으로 끌어 놓아 설치해도 같은지. Cancel 을 누르면 다시 묻지 않고, 환경설정 > Allset 맨 위 버튼으로 할 수 있는지.
- [ ] (step 42) Blender 를 껐다 켜면 (파일 없이) Maya 레이아웃으로 열리는지; .blend 를 더블클릭해 열면 그 파일이 그대로 열리는지; 세션 중 File > New > General 은 General 인지.
- [ ] (step 42) Revert Maya Look → 원래 테마·스플래시 설정이 돌아오고 File > New 목록에서 Allset 이 사라지는지. Allset 을 끄면 원래 테마로, 다시 켜면 Maya 테마로 돌아오는지.
- [ ] (step 42) 다른 애드온 (예: Node Wrangler) 이 Make Blender Maya 전후로 그대로 켜져 있는지.

### Step 44 — Maya 위젯 감각 (평면 위젯·밀도·Segoe UI)

- [ ] (step 44) Make Blender Maya 뒤 글자·행 크기가 같은 모니터의 Maya 2022 와 같아 보이는지 (125 % 화면: Resolution Scale 0.8). 100 %·150 % 모니터에서도 (0.8 이 아니라 1.0 / 0.667 이 되는지).
- [ ] (step 44) 실제 모니터 배율을 Blender 실행 중에 바꾸면 (노트북 ↔ 외부 모니터) 밀도는 처음 계산한 값 그대로 (delegated: 다시 켜면 새로 계산). 작아서 불편한지.
- [ ] (step 44) Segoe UI: 한글·특수문자 (°, ×) 가 빠지지 않고 보이는지 (Blender 가 빠진 글자는 기본 글꼴로 채우는지), 마킹 메뉴·핫박스 글자도 Segoe UI 인지.
- [ ] (step 44) 각진 평면 위젯이 Maya 처럼 읽히는지; 버튼·필드 경계가 너무 안 보이지 않는지 (엠보스 없음). 메뉴 그림자 없음이 어색하지 않은지.
- [ ] (step 44) Revert Maya Look / Allset 끄기 → Resolution Scale·글꼴·와이어 부드럽게가 원래대로 돌아오는지.

### Step 45 — Maya 그리드

- [ ] (step 45) Allset 레이아웃 persp: 그리드가 ±12 cm 에서 끝나고 5 cm 마다 굵은 선, 축선도 굵은 회색 (빨강/초록 아님). 확대·축소·텀블해도 깜빡이거나 끊기지 않는지, 큐브가 그리드 뒤를 가리는지.
- [ ] (step 45) 4 분할: top 에만 그리드, front / side 에는 그리드 없음 (Maya 와 같음). 사용자 정사영 (Numpad 5 로 바꾼 비스듬한 뷰) 에서는 바닥 그리드.
- [ ] (step 45) X 홀드 + 이동: 그리드 안에서 사본이 그리드선에 붙는지; 멀리 축소하면 Blender 가 10 cm 단계로 붙는데 (Blender 그리드 단계) 그것도 그리드선 (10 의 배수) 인지. 정사영에서 아주 크게 확대하면 1 cm 보다 잘게 붙을 수 있음 — Maya 사용자에게 괜찮은지.
- [ ] (step 45) Show > Grid / Display > Grid: 끄면 그리드 없음, 다시 켜면 Maya 그리드. 오버레이 팝오버에서 Blender Floor 를 켜면 Blender 그리드로 바뀌는 것 (delegated) 이 헷갈리지 않는지.

### Step 46 — 뷰 가구 (ViewCube·축 삼각·카메라 라벨)

- [ ] (step 46) ViewCube: 마우스를 올리면 진해지고 가리킨 면이 하늘색, 면 클릭 → 그 방향 정사영 뷰 (부드러운 전환). 모서리·꼭짓점 클릭은 아직 없음 (Maya 는 있음) — 아쉬운지.
- [ ] (step 46) ViewCube 를 드래그해도 뷰가 돌지 않음 (Maya 는 큐브 드래그 = 텀블) — Alt+LMB 로 충분한지.
- [ ] (step 46) 4 분할: ViewCube 가 마우스가 있는 패널로 옮겨 가는지; 라벨 top -Z / persp / front +Y / side -X 가 각 패널 아래 가운데. Maya 의 "top -Y / front -Z" 와 축 글자가 다른 것 (kit 은 Blender Z-up 축, Channel Box 와 같음, delegated) 이 헷갈리지 않는지.
- [ ] (step 46) 축 삼각이 텀블에 따라 돌고 x/y/z 글자가 Channel Box 축과 맞는지. 카메라 뷰 (Numpad 0) 에서 라벨이 카메라 이름인지.
- [ ] (step 46) Display > Heads Up Display > Camera Names / View Axis / View Cube 가 모든 뷰에서 켜고 끄는지.

### Step 47 — 선택 와이어

- [ ] (step 47) 오브젝트를 고르면 셰이딩 위에 모든 엣지가 연두 (리드) / 흰색 (나머지), 외곽선 없음. 해제하면 사라짐. Maya 와 선 굵기·밝기 비교.
- [ ] (step 47) 와이어가 면에 가려지는 뒤쪽 엣지는 안 보이고 앞쪽 엣지는 끊김 없이 보이는지 (아주 멀리 / 아주 가까이 확대해서도, cm 장면·m 장면).
- [ ] (step 47) 큰 메시 (수십만 폴리) 를 고를 때 잠깐 멈춤 (배치 만들기, 10 만 폴리 약 30 ms) 이 거슬리지 않는지; 편집 모드에서 나올 때도.
- [ ] (step 47) 스무스 프리뷰 3 에서 와이어가 케이지 엣지 (매끈한 면 밖에 뜸) 인 것이 Maya 와 비교해 괜찮은지.

### Step 49 — 레이아웃 동등화

- [ ] (step 49) Allset 레이아웃: 위에서 아래로 메뉴바 / Status Line / Shelf / [툴박스 | Outliner | 뷰 | Channel Box 도크] / Time Slider / Range Slider / Help Line + Command Line 한 줄. Maya 를 옆에 띄워 놓고 배치가 같게 읽히는지.
- [ ] (step 49) 툴박스: Select·Lasso·Paint Select·Move·Rotate·Scale 가 오브젝트·편집·포즈 모드에서 같은 자리에 있고, 다른 툴 (Multi-Cut 등) 을 쓴 뒤 그 툴이 구분선 아래 마지막 칸에 나오는지. 툴 버튼 더블클릭·길게 누르기가 이상하지 않은지.
- [ ] (step 49) 툴박스 아래 빈 곳 클릭·드래그 → 선택이 그대로인지. 빠른 레이아웃 Single / Four 버튼, Outliner 버튼 (새 창), Front/Persp 는 회색.
- [ ] (step 49) Resolution Scale 을 1.0 보다 크게 (Maya Density 끔) 하면: 툴박스 열이 한 열 폭으로 맞춰지거나 (마우스가 영역 경계를 지날 때) 그동안 메인 뷰에 툴바가 보이는지; Status Line·Shelf 두 줄이 잘리지 않는지.
- [ ] (step 49) 사이드바: Channel Box 탭으로 열리고 Tool / View 탭이 없음. 오브젝트를 고르면 Blender 의 Item 탭 (C 패널, 숨길 수 없음) 이 생김 — 거슬리는지. 환경설정 「Channel Box Dock Only」 를 끄면 Item / Tool / View / Outliner 탭이 돌아오는지.
- [ ] (step 49) Status Line 의 Attribute Editor 버튼 = 도크 AE 전환, Render Settings = Properties 새 창 (Render 탭).
- [ ] (step 49) 하단 줄: 왼쪽 Help Line (툴 도움말, 없으면 Blender 마우스 힌트·보고·진행), 오른쪽 Command Line. 오류 보고가 Help Line 칸에 보이는지.

### Step 50 — 에디터 크롬

- [ ] (step 50) Channel Box 메뉴 줄 Channels / Edit / Object / Show 가 열리고 항목이 동작하는지 (Edit > Settings ▸ 속도, Object 에서 리드 바꾸기, Show > All). 선택 없음 = Maya 문구.
- [ ] (step 50) Layer Editor: Display / Anim 탭, Layers 메뉴로 레이어 만들기·추가·삭제, 아이콘 버튼이 오른쪽. Anim 탭 안내가 헷갈리지 않는지.
- [ ] (step 50) Outliner 머리 Display / Show / Help: Show 의 종류 필터, Display > Shapes 를 켜면 Blender Outliner 머리로 돌아오는 것 (delegated) 이 괜찮은지. 눈 열이 없는 것 (H 로 숨김) 이 불편하지 않은지.
- [ ] (step 50) Time Slider 오른쪽 현재 프레임 칸 + 재생 버튼 8 개, Range Slider 줄 순서가 Maya 와 같게 읽히는지; 범위 막대를 누르면 타임라인이 재생 범위에 맞춰지는지; 오른쪽 끝 톱니 = Playback / Keying / View / Marker.

### Step 51 — 메뉴 옵션 박스·셸프 줄

- [ ] (step 51) Maya 메뉴 (Create, Edit Mesh 등) 에서 옵션 박스가 있는 항목 오른쪽의 창 아이콘: 클릭 = 명령, 길게 누르기 = 「Option Box」 → 실행 뒤 Adjust Last Operation 이 열리는지. Maya 의 □ 클릭 습관과 비교해 길게 누르기가 불편하지 않은지 (같은 줄 버튼 두 개는 메뉴가 계단처럼 깨져 못 씀).
- [ ] (step 51) 셸프 줄 = 탭 줄 (어두운 #373737, 고른 탭 밝게) + 32 px 컬러 아이콘 줄. 아이콘에 마우스 = 칸 강조 + 툴팁, 클릭 = 명령, 0.35 s 안 두 번째 클릭·Ctrl+클릭 = 옵션. 탭 바꾸기, 톱니 = 셸프 설정 (새 셸프·버튼 추가·마지막 명령 추가).
- [ ] (step 51) kit 아이콘이 무엇인지 읽히는지 (기본 도형·도구 기호, 기호 없는 버튼은 셸프 색 + 글자 두 개). Maya 아이콘과 헷갈릴 만큼 비슷하지 않은지 (결정 6).
- [ ] (step 51) Resolution Scale 을 바꾼 뒤 마우스가 셸프 줄 아래 경계를 지나면 셸프 줄이 64 px × 배율로 돌아오는지.
- [ ] (step 51) Status Line 그룹 앞 세로 그립 (Maya openBar) 을 누르면 그 그룹이 접혀 ▸ 만 남고, 다시 누르면 펼쳐지는지. 그립이 너무 작거나 눈에 안 띄지 않는지.

### Step 52 — 핫박스·RMB 마킹 메뉴

- [ ] (step 52) Space 길게: 위 2 줄 (공통 + Cache/Help, View … Panels), 커서 줄 Recent Commands | Maya | Hotbox Controls, 아래 5 줄 (메뉴 세트 모두), 대각선 4 개. 커서가 사이드바 근처여도 줄이 접히지 않고 Channel Box 위에 그려지는지, 그 위의 메뉴 이름을 눌러 열리는지.
- [ ] (step 52) Hotbox Controls 에서 「Show All Menu Sets」 를 끄면 현재 세트 줄만 나오는지.
- [ ] (step 52) 오브젝트 위 RMB: 링 아래 목록 첫 줄 「pCube1...」 (누르면 AE 도크에 그 오브젝트), Select … Invert Selection, Select Similar □ (옵션 = Adjust Last Operation), 회색 ▸ 항목들, 재질 항목. 목록이 아래로 넘치면 오른쪽 열로 이어지고 모든 항목에 닿는지; 목록이 타임라인 위로 그려져도 어색하지 않은지.
- [ ] (step 52) Maya Font (Segoe UI) 를 켠 상태에서 마킹 메뉴 하위 메뉴 화살표 (삼각형) 가 글자 옆에 맞게 보이는지.

### Step 53 — Blender 5.x 와 안전한 설치

- [ ] (step 53) 쓰던 Blender (애드온 몇 개, 바꾼 키·탐색 설정) 에 kit 을 설치: 기존 애드온이 그대로 켜져 있고, kit 을 끄면 키맵·탐색·undo 설정이 설치 전과 같은지.
- [ ] (step 53) Blender 5.0–5.2 에서 kit 을 켜고 Maya 레이아웃: Status Line·셸프·툴박스·Channel Box·핫박스가 4.5 와 같게 보이는지, Range Slider 줄의 재생 버튼, Maya 테마 색 (일부 5.x 전용 색은 Blender 기본).
- [ ] (step 53) kit 을 켠 채 Graph Editor (Alt+MMB/Alt+RMB, A/F, 키 클릭), Node Editor, Text Editor (z/h/Space 입력) 가 평소대로인지.
- [ ] (step 53) Blender 5.3 이상에 설치하면 확장 관리자가 「호환 안 됨」 을 분명히 보여 주는지.

### Step 54 — 단위 생성 경로·조명 세기·「Blender 에 없음」 안내

- [ ] (step 54) Allset 템플릿에서 Skeleton > Create Joints, Create > Type, Create > Free Image Plane, Fields/Solvers 필드들이 pCube1 (1 단위) 과 같은 크기 감으로 원점에 생기는지. Gravity 필드 화살표가 아래를 향하는지.
- [ ] (step 54) Create > Lights > Point/Spot/Area 를 pCube1 에서 Maya 습관 거리 (5–10 단위) 에 두고 렌더 미리보기 밝기가 m 장면의 같은 배치와 비슷한지 (역제곱 미터 보정). 상태 표시줄 보고에 감쇠 안내.
- [ ] (step 54) Windows > Animation Editors > Trax / Time Editor, Relationship Editors > Animation Layers / Character Sets, Windows > Node Editor, Rendering Editors > Light Editor, Skeleton > HumanIK / Quick Rig, File > Create Reference / Set Project 위에 마우스: 툴팁과 Help Line 의 안내 문구가 이해되는지, 대체 항목은 눌렀을 때 대체 편집기가 열리는지.
- [ ] (step 54) Fluids > 3D Container / Effects > Smoke 를 메시 선택 후: 도메인이 메시 둘레에 Maya 단위로 알맞게 (cm 템플릿에서 2 m 상자가 아님).

### Step 55 — 포즈 본 = Maya 조인트 (CB·Outliner·AE·제약 가중치)

- [ ] (step 55) Skeleton > Create Joints 후 오브젝트 모드에서 아마추어를 고르면 CB 머리 아래 「Joint channels: Ctrl+Tab (pose mode)」; Ctrl+Tab → 포즈 모드, 뷰에서 조인트 클릭 = CB 머리가 조인트 이름, Translate/Rotate/Scale/Visibility 행. 아무 조인트도 안 고르면 빈 CB 문구.
- [ ] (step 55) 조인트 두 개를 고르고 Rotate Z 칸에 `+=10` = 둘 다 각자 값에서 10° 더. 채널 이름 Shift+클릭으로 Rotate X–Z 를 고르고 Channels > Lock Selected → 뷰에서 E 로 돌려도 안 돌고, Key Selected 키가 Graph Editor 에 `joint2` 그룹으로 보이는지. MMB 드래그 (가상 슬라이더) 가 고른 조인트 채널을 바꾸는지.
- [ ] (step 55) Blender 로 만든 본 (쿼터니언) 을 고르면 「Rotation mode QUATERNION」 + 「Rotate Order XYZ」 버튼; 누르면 자세 그대로 Rotate X/Y/Z 행이 나오는지.
- [ ] (step 55) 조인트에 Copy Location (대상 locator1) 제약: CB INPUTS 에 `joint2_pointConstraint1` 과 `locator1W0`, Translate 칸이 파랑 (눌린 버튼 색) 으로 Maya 의 제약 채널처럼 읽히는지; W0 에 0.5 → 조인트가 반만 따라감. 제약 체크를 끄면 파랑이 사라지는지.
- [ ] (step 55) 사이드바 Outliner (Dock Only 끔): skeleton1 ▸ 를 펼치면 joint1 ▸ joint2 ▸ joint3 계층, 조인트 행 클릭 = 포즈 모드 + 그 조인트, 오브젝트 행 클릭 = 오브젝트 모드로 돌아가 선택. 레이아웃의 Outliner (Blender 트리) 는 Display > Shapes 를 켜야 본이 보임.
- [ ] (step 55) AE (Ctrl+A) 에서 조인트: joint 탭 + 제약 노드 탭, Transform Attributes / Joint (Joint Orient 읽기 전용, 축 안내) / Limit Information (Add Limit Rotation 이 조인트에 붙음) / Display (Display as Control Shape). 아마추어 편집 모드에서는 CB·AE 에 「Placing joints」 한 줄.

### Step 56 — Time Slider·키 감각

- [ ] (step 56) Allset 레이아웃 Time Slider 아무 곳 LMB 클릭·드래그 = 시간 이동 (키를 집어 옮기지 않음), Dope Sheet 창 본문 LMB 는 여전히 키 선택.
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
- [x] (step 59) Modify > Snap Align Objects: Point to Point (편집 모드에서 두 오브젝트의 정점 — 움직일 쪽 먼저, 목표 오브젝트가 활성), 2/3 Points (방향까지), Align Objects (X 가운데 정렬). Snap Together Tool: 움직일 면 클릭 → 목표 면 클릭 → 면끼리 맞닿음. Make Live: 면 스냅이 켜지고 Status Line 칸에 이름, 빈 선택으로 다시 = 해제. (gui_manual_sweep)

### Step 60 — Maya ⇄ Blender 스위치 · 완전 되돌리기

- [ ] (step 60) 상단 바 오른쪽 「Maya | Blender」 스위치가 두 모드 모두에서 보이고, 클릭 한 번에 재시작 없이 바뀌는지 (키맵·메뉴·Status Line·Shelf·Channel Box·테마). 바뀌는 데 걸리는 시간이 거슬리지 않는지.
- [x] (step 60) Ctrl+Alt+Shift+M 로 같은 전환 (어느 에디터 위에서든). Blender 모드에서 F3 (메뉴 검색) 「Switch to Maya」, Maya 모드에서 Windows > Switch to Blender. (gui_manual_sweep — F3 = Blender 메뉴 검색이 찾는 Edit 메뉴 항목으로 확인)
- [x] (step 60) 작업 중인 파일 (오브젝트·애니메이션·저장 경로) 이 전환 전후 그대로, Blender 로 돌아오면 원래 워크스페이스 (Layout 등) 가 다시 열리고 「Maya」 워크스페이스는 사라짐. 그 파일을 저장해도 Maya 레이아웃이 남지 않는지. (gui_manual_sweep)
- [x] (step 60) 내 키 수정 (Preferences > Keymap 에서 바꾼 키), 내 테마, 다른 애드온, 회전 방식 등을 바꿔 둔 설정에서 Maya → Blender: 전부 그대로. Maya 모드 중에 바꾼 다른 설정 (Maya 가 건드리지 않는 것) 도 그대로. (gui_manual_sweep)
- [ ] (step 60) Maya 모드인 채 Blender 를 닫고 다시 열기 → Maya 모드 그대로, 그다음 Blender 로 → 원래 설정. Maya 모드에서 작업 관리자로 강제 종료 → 다시 열어서 Blender 로 전환 → 원래 설정.
- [ ] (step 60) Preferences > Extensions 에서 Allset 을 Maya 모드인 채 끄기 / Remove → 키맵·테마·스플래시·UI 크기가 Allset 이전으로. 「Restore Blender Settings」 버튼 = Maya 끔 + Maya 레이아웃 템플릿 제거 + 원래 설정.

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

- [ ] (step 68) Allset 레이아웃에서 F5 → nParticles > Create Emitter: 아웃라이너에 emitter1, 재생 (Alt+V) → 원점에서 점들이 나와 떨어지는 빠르기가 Maya (fx_01.png) 와 비슷한지 (1 초에 약 5 유닛). 점이 큰 공이 아니라 작은 점으로 보이는지.
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
- [x] (step 69) File > Reference Editor: Outliner 새 창 Blender File 보기, 레퍼런스 파일 행 우클릭 Reload / Relocate. (gui_manual_sweep — 행 RMB 메뉴는 Blender 그대로 — Reload 동작으로 확인)

### Step 70 — Graph Editor 툴바 · Shift+S · G · Auto Key · Playblast

- [ ] (step 70) Graph Editor 헤더 오른쪽 아이콘 줄: Auto / Spline / Clamped / Linear / Flat / Stepped / Plateau | Break / Unify | 고스트 커브 (Buffer Curve). 툴팁 = Maya 이름 + Blender 대응. 키 선택 후 클릭 → 커브 모양이 animation_02_win1 의 툴바와 같은 뜻으로 바뀌는지.
- [x] (step 70) Shift+S 누른 채 LMB: Keys (W) / Tangents (E) 마킹 메뉴 — Graph Editor 에서는 선택 키, 3D View · 타임라인에서는 선택 오브젝트의 현재 프레임 키 (Time Slider 범위가 있으면 그 범위). Shift+S 탭은 아무 일 없음. Stepped Next 는 Stepped + 안내. (gui_manual_sweep — Stepped Next 안내는 연산자 INFO report (상태 표시줄))
- [x] (step 70) Graph Editor 위 G = 재생 범위로 가로 맞춤 (3D View 의 G = Repeat Last 그대로), D = 선택 키 Auto 탄젠트, F / A = 선택 / 전체. (gui_manual_sweep)
- [x] (step 70) Auto Key 켬: 키가 있는 채널만 값 바꿀 때 키 (이동 키만 있는 큐브를 회전 → 회전 키 안 생김; Channel Box 입력도 같음). 환경설정 「Maya Auto Key」 끄면 Blender 처럼 모든 채널. (gui_manual_sweep)
- [ ] (step 70) Windows > Playblast (Playback > Playblast, 셸프) → 재생 범위 동영상 → Blender 플레이어 창이 열림. □ (길게) = Playblast Options (Time Range / View / Format / Quality / Scale) — animation_08_win1 비교. 끝나면 장면의 렌더 설정 (출력 경로·형식·해상도 %) 은 그대로.

### Step 72 — 상단 바 다시 그리기 · Maya 인뷰 메시지

- [x] (step 72) F2–F6: 마우스를 뷰에 둔 채 누르면 상단 메뉴 바가 바로 그 메뉴 세트로 바뀜 (호버 없이). 창을 하나 더 연 (Hypershade 등) 뒤에도 두 창의 상단 바가 모두 바뀜. (gui_manual_sweep)
- [ ] (step 72) F8 → 뷰 가운데 위 "Component selection on. / F8 goes back to objects." 상자가 0.3 초에 나타나 2 초 머문 뒤 1.5 초에 걸쳐 사라짐 — research/maya/screens/ivm/ivm_05 와 모양·위치·노란 강조 비교.
- [x] (step 72) Allset 레이아웃에서 Ctrl+G / Ctrl+H / Alt+H 메시지는 뷰 왼쪽 위 (ivm_02, ivm_09 위치), Blender 텍스트 정보가 켜진 뷰에서는 가운데 위. b 로 소프트 선택 켤 때만 메시지, Make Live 켬 / 끔 메시지. (gui_manual_sweep)
- [x] (step 72) 환경설정 UI Elements 「In-View Messages」 끄면 메시지 없음. 4분할에서는 키를 누른 그 뷰에만. (gui_manual_sweep)

### Step 73 — 타임 슬라이더 키 틱 · Range Slider 드래그

- [ ] (step 73) 키가 있는 오브젝트를 선택하면 타임 슬라이더에 그 프레임마다 1 px 빨간 세로선 (Breakdown 키는 초록), 선택을 풀면 사라짐 — research/maya/screens/ts/ts_01_window.png 와 비교. 뼈 (포즈 모드) 는 그 뼈의 키만.
- [x] (step 73) Range Slider 바: 회색 구간 가운데를 끌면 재생 범위가 같은 길이로 움직이고 타임 슬라이더가 따라감; 양끝 손잡이를 끌면 그 끝만; 애니메이션 범위 밖으로는 안 나감; ESC / RMB = 취소; Ctrl+Z 로 되돌림. (gui_manual_sweep)
- [ ] (step 73) 바 더블클릭 = 전체 애니메이션 범위 ↔ 재생 범위 (GUI 테스트는 더블클릭 이벤트를 만들 수 없어 동작만 확인함).
- [ ] (step 73) UI 배율 1.0 / 1.5 / 2.0 에서 바가 playback start 필드와 playback end 필드 사이에 정확히 그려지고 숫자가 손잡이 옆에 읽힘.

### Step 74 — 프리셀렉트 (엣지 · 면 · 변형 툴)

- [ ] (step 74) 엣지 모드: 엣지 위 = 2 px 빨간 선, 꼭짓점 가까이에서도 엣지 (research/maya/screens/pre/pre_03, pre_04 와 비교). 면 위 엣지에서 먼 곳 = 그 면의 가장 가까운 엣지.
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
- [x] (step 78) Graph Editor 1 / 2 / 3: 2 는 Help Line 에 Stacked 없음 안내 + Normalized. (gui_manual_sweep — 안내는 연산자 INFO report (상태 표시줄))

### Step 79 — 3D Cut and Sew UV Tool

- [x] (step 79) UV > 3D Cut and Sew UV Tool (메뉴 / 셸프 / UV Toolkit / UV 마킹 메뉴 NW) = 편집 모드 + 엣지 모드 + 툴바의 툴. 셸 경계가 흰 굵은 선으로 보임 (Maya Texture Borders). (gui_manual_sweep — 경계 선은 그릴 선 수·색·굵기로 확인 (픽셀 아님))
- [x] (step 79) 엣지 위 호버 = 빨간 하이라이트, 누르고 엣지를 따라 드래그 = 노란 선이 따라오고 놓으면 그 엣지만 잘림 (모서리를 돌아도 옆 세로 엣지는 안 잘림). Ctrl+드래그 = 꿰매기 (작은 셸이 붙음), Shift+드래그 = 선택만. (gui_manual_sweep — 빨강 / 노랑은 상수 + 호버·획 상태로 확인)
- [x] (step 79) 툴 안에서 x / s = 선택 엣지 Cut / Sew, d = Unfold + Layout (0-1). 툴 밖에서는 X / S / D 가 원래 키 (스냅 홀드 · 스케일 · 피벗). (gui_manual_sweep)
- [ ] (step 79) 큰 메시 (10만 정점) 에서 드래그가 끊기지 않는지 (표본마다 프리셀렉트 픽), 경계 선 캐시가 편집 뒤 다시 계산되는지.

### Step 81 — Maya persp 화각

- [ ] (step 81) 새 장면 (Allset 템플릿) 의 persp 가 Maya 새 장면과 같은 화각: 그리드 마름모 크기·원근, pCube1 크기를 Maya 와 나란히 비교. Four View 의 persp 사분면도.
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

- [ ] (step 91) Allset 레이아웃에서 자식을 부모에서 떨어뜨려도 (Ctrl+G, P) 부모–자식 점선이 없음. Blender 로 전환하면 원래 워크스페이스의 뷰는 예전 그대로 (점선 있음).
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

- [ ] (step 99) Windows 125 % 에서 Maya Density 를 끈 채 (또는 Preferences > Interface > Resolution Scale 1.0) Allset 새 장면 → 시작 직후 마우스 커서가 Tool Box 열 오른쪽 경계로 잠깐 갔다가 제자리로 돌아오고, Tool Box 열에 Q W E R 툴이 보이며 뷰포트 안에 Blender 툴바가 남지 않는지. 커서가 순간 이동하는 것이 거슬리는지 (로드당 한 번).
- [ ] (step 99) 새 장면 Outliner = persp / top / front / side (회색, 카메라 그림) → defaultLightSet / defaultObjectSet. persp 클릭 = 선택 해제 + 행 강조, defaultLightSet = 라이트 선택. 큐브를 만들면 카메라 행이 pCube1 **뒤**로 감 (Maya 는 앞) — 거슬리는지.
- [ ] (step 99) 도크 오른쪽 가장자리 세로 탭 「Channel Box / Layer Editor」「Attribute Editor」「Modeling Toolkit」 클릭 → 각 편집기, Ctrl+A 로도 탭이 바뀜. 오브젝트를 선택하면 Blender 「Item」 탭이 네 번째로 생김 (C 패널, 숨길 수 없음) — 눌러도 되고 다른 탭을 누르면 돌아옴.
- [ ] (step 99) Layer Editor (Display / Anim 탭) 가 도크 높이의 약 절반에서 시작하고 목록이 아래 끝까지 차는지 (Maya 처럼). 큐브 INPUTS 가 있을 때는 CB 바로 밑에 붙음.

### Step 101 — 메뉴 정직성 (회색마다 안내, 싼 매핑, 객체 모드에서도 활성)

- [ ] (step 101) 아무 회색 메뉴 항목 (예: Surfaces > Loft, Generate > XGen Editor, Skeleton > Joint Labelling > Label Left) 에 마우스를 올리면 툴팁에 「(greyed) → 가장 가까운 Blender 기능」 과 한 줄 안내, Help Line 에도 같은 줄. 문장이 Maya 사용자에게 이해되는지.
- [ ] (step 101) 큐브를 객체 모드로 선택하고 Edit Mesh > Poke / Merge / Bevel → 큐브 전체에 적용되고 객체 모드 그대로 (Maya 처럼), Ctrl+Z 한 번에 원래대로. Bridge / Detach / Wedge → 상태 표시줄에 Maya 경고 문장, 모양 그대로.
- [ ] (step 101) Edit Mesh > Wedge: 면 몇 개 + 그 테두리 모서리를 활성으로 (Shift+클릭 마지막) → 그 모서리 축으로 90° 4 단 회전 압출. Maya 결과와 방향이 같은지 (반대면 축 부호 확인).
- [ ] (step 101) Edit Mesh > Edit Edge Flow: 굽은 면 위 가운데 루프를 평평하게 눌러 둔 뒤 실행 → 주변 곡률을 따라 다시 볼록해지는지 (Maya polyEditEdgeFlow 1.0 과 비교).
- [ ] (step 101) Mesh Tools > Sculpting Tools > Grab Tool 등 → Sculpt 모드 + 해당 브러시. Audio > Import Audio... → 파일 선택 후 재생 시 소리 (VSE 스트립), Mute 토글. Cache > Alembic Cache > Export Selection to Alembic... → .abc 파일, Import Alembic... → 불러옴.
- [ ] (step 101) Help > Maya Help / Python Command Reference → 웹 브라우저로 Blender 문서가 열림. Help > About Maya → Blender About.

### Step 102 — Maya 파일 대화상자, 기본 프로젝트

- [ ] (step 102) 새로 설치한 상태 (프로젝트 설정 없음) 에서 Ctrl+O / File > Import... → 대화상자가 `Documents/allset/projects/default/scenes` 에서 열리고 그 폴더들이 생김 (Documents 맨 바닥이 아님). 왼쪽 「Current Project」 의 폴더를 누르면 그 폴더로, Set Project... 는 보고 있는 폴더를 프로젝트로.
- [ ] (step 102) File > Export Selection... → 오른쪽 Files of type 을 OBJ → FBX 로 바꾸면 파일 이름 확장자가 따라 바뀌는지, 시작 폴더 (OBJ = data, FBX = scenes) 가 Maya 와 같다고 느껴지는지.
- [ ] (step 102) 실제 Maya 2022 GUI 에서 kit 가 내보낸 FBX / OBJ 를 Import → 크기·방향이 Maya 에서 만든 것과 같은지 (mayapy 로는 확인됨). Maya 가 내보낸 FBX 를 kit 로 Import → Channel Box 크기 그대로.
- [ ] (step 102) Import 대화상자에 .ma 파일을 고르면 「.ma / .mb can't be read: export FBX from Maya」 오류.

### Step 103 — Maya 옵션 창

- [ ] (step 103) Create > Polygon Primitives > Cube ❒ 를 누르고 있기 → 「Option Box」 → Polygon Cube Options 창. Width 3 → Apply: 창이 열린 채 큐브가 생기는지 (Maya Apply). Create: 만들고 닫힘. 다시 메뉴에서 그냥 Cube 클릭 → 3 폭 큐브 (Maya 처럼 저장된 값). Reset Settings → 1 로 돌아가는지.
- [ ] (step 103) Edit Mesh > Bevel ❒ / Constrain > Parent ❒ 창의 필드 이름·기본값이 Maya 창과 같다고 느껴지는지 (research/maya/screens/step103/ 비교 그림). 회색 「Not in Blender」 목록이 거슬리는지.
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
- [ ] (step 109) Curves / Surfaces: 원 두 개 → Loft, 닫힌 커브 → Planar / Bevel Plus, 프로필 + 경로 → Extrude, 커브 → Offset Curve / Sweep Mesh, Pencil Curve Tool 로 그리기, Add Points Tool 로 끝점 연장이 Maya 손에 맞는지.
- [ ] (step 109) 아이콘 모양 (셸프마다 Maya 색, 도구 부분 회색) 이 125 % 와 100 % 에서 Maya 셸프와 같은 인상인지 (`research/maya/screens/step109/`).

### Step 110 — 모델링·리깅 기능

- [ ] (step 110) 실제 손으로: 구멍 테두리 / 면 묶음에 Circularize, 구 링을 줄였다가 Edit Edge Flow, 모서리 둘 → Connect, 면 두 개 → Make Hole 의 결과가 Maya 손에 맞는지 (뷰포트에서).
- [ ] (step 110) 조인트 체인에서 Reroot / Set·Assume Preferred Angle / Create IK Spline Handle (curve1 을 움직이면 체인이 따라오는지), Hammer Skin Weights 를 웨이트 페인트로 확인.
- [ ] (step 110) Cluster / Soft Modification 핸들을 W 로 움직이는 느낌 (Soft Mod 는 반경 5 안에서 부드럽게), Nonlinear Bend / Twist 값을 Channel Box 나 모디파이어에서 바꿀 때 핸들 기준으로 휘는지.

### Step 111 — 이름 변경 (Allset for Maya Users)

- [ ] (step 111) 깨끗한 설정에 `allset-0.1.0.zip` 을 끌어 놓아 설치: Preferences > Add-ons 에 「Allset for Maya Users」, 맨 위 About 상자 (설명 + 상표 고지문), 환영 창 제목·문구, 스플래시, File > New > Allset, 키맵 이름 「Maya-style」, 테마 이름 「Studio Grey (Maya-inspired)」.
- [ ] (step 111) 예전 Maya Kit 를 쓰던 설정: `bl_app_templates_user/MayaKit` 이 레이아웃 설치 / 제거 때 지워지는지 (표시 파일 `.maya_kit` 있을 때만).

### Step 112 — 불투명 도크, Tool Box 띠

- [ ] (step 112) 실제 설정 (자기 테마 그대로): Maya 로 전환 → Maya-style 레이아웃에서 오른쪽 Channel Box / Attribute Editor / Modeling Toolkit 탭 배경이 불투명하고 뷰포트가 그 왼쪽에서 끝나는지, 맨 왼쪽 열에 Select / Lasso / Paint / Move / Rotate / Scale 아이콘이 보이고 뷰포트 안에는 도구 줄이 없는지 (125 %, 창 크기 바꿔서도). UV Editor 사이드바도 불투명한지. 환경설정 「Solid Side Panels」를 끄면 Blender 의 Region Overlap 이 돌아오는지, Blender 로 전환해도 돌아오는지.

### Step 113 — 상단 (메뉴 막대, Status Line, 셸프, 패널 바)

- [ ] (step 113) 실제 125 % 화면, 자기 설정: Maya 로 전환 → 메뉴 막대에 File … Help 가 다 보이고 메뉴셋 드롭다운은 Status Line 맨 왼쪽, 오른쪽 Workspace: 드롭다운으로 작업 공간이 바뀌는지, Maya | Blender 글자가 눈에 덜 띄면서 눌리는지.
- [ ] (step 113) Status Line 의 ▷ 로 그룹 접기 / ▶ 로 펴기, 스냅 자석·선택 모드·렌더 아이콘 툴팁, 오른쪽 끝 사이드바 토글 (Modeling Toolkit / Attribute Editor / Tool Settings / Channel Box).
- [ ] (step 113) 셸프: 탭 클릭, ≡ (셸프 고르기), 톱니 (셸프 편집), 아이콘이 버튼마다 알아볼 만한지, 구분선 위치가 Maya 와 같은지.
- [ ] (step 113) 뷰 패널 툴바: 와이어 / 스무스 / 텍스처 / 모든 조명 / 그림자 / X-ray / 아이솔레이트 / 그리드가 그 뷰에서 켜고 꺼지는지, 노출·감마 칸, Blender 로 돌아가면 Blender 헤더와 테마가 돌아오는지.

### Step 115 — opt-in, 템플릿 정리

- [ ] (step 115) 실제 Blender 에서 Get Extensions 로 설치·활성화 → 그 자리에서 환영 창이 뜨고, 그 전에는 키맵·테마·레이아웃이 그대로인지. 「Make Blender feel like Maya」 → 저장 안 한 작업 중 파일이면 그 파일에 Maya-style 작업 공간만 붙고 데이터는 그대로, 새 빈 파일이면 Allset 레이아웃 파일로 바뀌는지. 취소하면 아무것도 안 바뀌고 다시 안 뜨는지 (환경설정의 같은 버튼은 남음).
- [ ] (step 115) Auto-Save Preferences 를 끈 설정: Maya 로 바꾸고 저장하지 않고 종료 → 다음 시작이 Blender 그대로인지 (킷이 혼자 저장하지 않음).
- [ ] (step 115) 확장을 끄거나 Remove → `scripts/startup/bl_app_templates_user/Allset` 이 지워지는지, 그냥 종료·재시작·확장 업데이트로는 남는지. File > New > Allset 뒤에도 Maya 키맵인지.

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

- [ ] (step 118) Blender 5.0 / 5.1 / 5.2 실제 화면 (사용자 Blender 5.x 설치본): 확장 설치 → 환영 창 → Make Blender Maya → Allset 레이아웃. 타임라인은 5.x 에서 사이드바가 열리지 않으므로 Range Slider 막대가 머리줄에 있고 재생 버튼 8 개는 그 줄 오른쪽 끝 — 막대 끌기 / 양 끝 핸들 / 더블클릭이 4.5 처럼 되는지.
- [ ] (step 118) 5.x: 관절 Channel Box Visibility off → 포즈·오브젝트 모드에서 그 본이 정말 숨는지 (5.0 의 `PoseBone.hide`), on → 다시 보이는지.
- [ ] (step 118) 5.2: 저장 안 된 이미지 (Texture Paint 한 획) 가 있는 채로 Ctrl+S → Blender 5.2 의 「수정된 이미지 저장」 창이 뜨는지.
- [ ] (step 118) 5.x 의 Maya 테마: 이음매 (빨강) / 날카로운 모서리 (청록) / 주름 (자홍) 색, Graph Editor 핸들 색, Properties 패널 머리·배경이 4.5 와 같은지. Blender 로 전환하면 사용자 테마로 돌아오는지.

### Step 119 — 5.x 색 일치

- [ ] (step 119) Blender 5.0 / 5.1 / 5.2 실제 화면에서 Make Blender Maya 뒤 4.5 와 나란히: 메뉴 막대·Status Line·셸프 (아이콘 밝기 — 5.x 는 `IMAGE_SCENE_LINEAR_TO_REC709_SRGB` 셰이더), Channel Box / AE 패널 배경·머리, 뷰포트 #5c5c5c, 격자 (주 격자선이 따로 밝지 않은지 — `grid_major`), 선택 흰색 / 리드 초록, 매니퓰레이터 축 색이 같은지.
- [ ] (step 119) 5.x Graph Editor / Dope Sheet: 채널 배경·선택 채널, 키 (보통 / 선택), 핸들 색, 재생 헤드, 미리보기 범위 어둡게가 4.5 Maya 테마와 같은지 (`common.anim.*`, `common.curves.*`).
- [ ] (step 119) 5.x 위젯 선택 외곽선 (`wcol_*.outline_sel`): 숫자칸·체크박스·메뉴를 눌렀을 때 Blender 기본 강조색 대신 Maya 처럼 외곽선이 그대로인지; Properties / 도크 패널의 활성 패널 표시 (`panel_active`).
- [ ] (step 119) 5.x Outliner 활성 행 외곽선 (테마 키 없음, 남은 것): Maya 와 얼마나 달라 보이는지 — 거슬리면 보고.
- [ ] (step 119) 5.x 에서 Blender 로 전환 → 사용자 테마로 돌아오는지, 다시 Maya → 버전 파일 (`studio_grey_5.<m>.xml`) 이 적용되는지 (Preferences > Themes 의 이름 "Maya").

### Step 120 — Maya 배경 · Alt+B

- [ ] (step 120) Allset 레이아웃 (Maya 테마) 에서 뷰포트 위 Alt+B 를 네 번: 회색 #5c5c5c → 밝은 회색 → 위 청회색·아래 검정 그라데이션 → 검정 → 회색, 네 분할 뷰 (Space 탭) 모두 함께 바뀌는지; Maya 와 나란히 볼 때 그라데이션 가운데가 조금 어두운 것 (ΔE00 ≈ 9, 남은 것) 이 거슬리는지.
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

- [ ] (step 125) 깨끗한 설정에 `maya-workflow-kit-<ver>.zip` 설치: Preferences > Add-ons 에 「Maya Workflow Kit」, 환영 창 제목 「Welcome to Maya Workflow Kit」, File > New 에 「Maya Workflow Kit」 템플릿, 핫박스 가운데 상자 「Maya Workflow Kit」; 화면 어디에도 「Allset」 글자가 남지 않는지 (내부 id `allset` 은 Get Extensions 의 정보에만).
- [ ] (step 125) 이전 (Allset) 빌드에서 이 빌드로 업데이트: 같은 id `allset` 이라 업데이트로 보이고, 옛 `bl_app_templates_user/Allset` 템플릿이 남아 File > New 에 두 개가 보이지 않는지.
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
- [ ] (step 129) Hold B, drag with the **middle** mouse (and with the left) left / right: a white circle of the radius around the selection + "Falloff Radius: x" next to the mouse, the view does not orbit, releasing B keeps soft select on. Judge whether ×2 per 100 px feels like Maya (Maya's rate is not measured: synthetic drags don't reach its screen slider).
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
- [ ] (step 129) Layer Editor: 행의 V / P / T 상자 클릭, 이름 더블클릭 이름 바꾸기, 상자 위 RMB → Maya 레이어 메뉴, 화살표로 순서 이동 (새 레이어가 맨 위). Maya 캡처 `research/maya/screens/le129/le02_dock.png` 와 나란히.

### Step 131 — Hypershade

- [ ] (step 131, #25) Windows > Rendering Editors > Hypershade (그리고 Status Line 아이콘, 핫박스 Windows 메뉴) → 새 창이 Maya 배치로 열리는지: 맨 위 Maya 메뉴 줄 (File … Help), 왼쪽 위 Browser, 오른쪽 위 Material Viewer, 왼쪽 아래 Create, 가운데 Graph (툴바 + "Untitled_1" 탭), 오른쪽 아래 Property Editor. `research/maya/screens/hypershade131/hypershade_graph_screen.png` 와 나란히 (`tmp/hyper131/hypershade_side_by_side.png`). 창을 크게 늘렸을 때 비율이 맞는지 (Blender 영역 경계는 창 크기에 비례).
- [ ] (step 131) 창이 만들어지는 동안 (한 틱에 한 번 나누기, 약 0.2 s) 깜빡임이 거슬리지 않는지; 125 % / 100 % UI 배율에서 메뉴 줄이 헤더 한 줄 높이로 보이고 (본문이 비치지 않음) 메뉴가 열리는지.
- [ ] (step 131) Browser 스와치 클릭 → Graph · Material Viewer · Property Editor 가 같은 재질로 바뀌는지; 검색 칸에 글자 입력 시 바로 걸러지는지; Bake Sets / Projects / Asset Nodes 탭, Show, 일시정지 버튼은 회색 + 툴팁 안내.
- [ ] (step 131) Create: Favorites / Maya / 카테고리 클릭으로 목록이 바뀌는지, 검색 칸으로 전체에서 찾기, Blinn 클릭 = 할당 안 된 새 재질, Checker 클릭 = 현재 재질 그래프에 노드, Point Light = 씬에 라이트; 회색 항목 툴팁.
- [ ] (step 131) Material Viewer: 모양 (Sphere / Shader Ball …) · World 토글 · EEVEE 미리보기가 그려지는지 (Workbench 면 안내 문구); 미리보기 아래 ::: 로 크기 조절.
- [ ] (step 131) Graph 툴바: 입력 / 입출력 / 출력 연결 = 네트워크 선택 + 화면 맞춤, Hide / Show connected / Show primary attributes, swatch 토글; 회색 버튼 툴팁. View > Frame All / Frame Selected 가 메뉴 줄이 아니라 Graph 에서 동작하는지.
- [ ] (step 131) Hypershade 를 연 채 메인 창에서 다시 열기 → 이전 창이 닫히고 새 창이 앞에 하나만; Hypershade 창의 Window > Browser… 는 아무 창도 새로 열지 않음. 파일 저장 → 다시 열기 후에도 패널들이 Hypershade 로 그려지는지 (메뉴 줄 / Graph 인식은 패널 표식 기준).

### Step 131 — menu icons

- [ ] (step 131, #23) Create > Polygon Primitives / NURBS Primitives, Mesh, Edit Mesh, Mesh Tools, Deform, Constrain, Key, Windows > General Editors 를 실제 마우스로 열어 Maya 2022 메뉴 (`tmp/maya_icons131/grab`) 와 나란히: 아이콘이 있는 줄이 Maya 와 같은 명령인지, 16 px 에서 한눈에 구분되는지 (같은 메뉴 안에서 서로 다른 그림).
- [ ] (step 131) 아이콘이 있는 줄 / 없는 줄의 글자가 한 열에서 시작하는지, Maya 단축키 (Ctrl+B, Ctrl+Shift+X …) 와 ❒ 옵션 상자 열이 그대로 오른쪽에 맞는지 — 100 % 와 125 % UI 배율, 그리고 Preferences 에서 Resolution Scale 을 바꾼 직후 (잠깐 이전 크기 그림이 쓰이다가 새 크기로 바뀜).
- [ ] (step 131) Maya 모드를 켠 직후 처음 여는 메뉴에도 아이콘이 있는지 (미리 만들어 둠), 회색 항목 (Super Ellipse 등) 의 아이콘이 흐리게 보이는지.

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

- [ ] (step 134, #58) Maya 레이아웃에서 큐브를 만들고 1 / 2 / 3, 4 / 5 / 6 / 7, F8, F9 / F10 / F11, Alt+A, Alt+P 를 실제 키보드로 눌러: 뷰포트 왼쪽 아래에 Adjust Last Operation 패널 (「Component Mode」, 「Smooth Mesh Preview」 등) 이 뜨지 않는지. 다른 연산 (예: Shift+H) 의 패널이 떠 있을 때 3 / F9 를 누르면 그 패널이 닫히는지.
- [ ] (step 134) F9 → Ctrl+Z 가 오브젝트 모드로 돌아가는지, 3 → 이동 → Ctrl+Z 가 이동만 되돌리고 미리보기는 남는지.
- [ ] (step 134, #61) Create > Polygon Primitives 의 Cube / Cylinder / Pipe 에 3: 미리보기가 매끈한 음영 (면 경계가 보이지 않음), 1 로 돌아오면 Maya 처럼 각진 hard edge. 0.2.x 에서 3 을 켜고 저장한 파일을 열어 3 을 다시 누르면 매끈해지는지.
### Step 134 — selection colours

- [ ] (step 134 SEL) 오브젝트 모드에서 큐브 둘을 Shift 클릭: 마지막에 고른 것 (리드) 의 모든 엣지가 Maya 연두 #43ffa3, 다른 선택은 흰색, 선택 안 된 것은 와이어 없음 — Blender 기본 테마 (주황) 그대로인 사용자 설정에서도. 와이어프레임 (4) 에서도 같은 색. Maya 레이아웃 밖의 뷰 (사용자 화면) 는 Blender 주황 외곽선이 와이어 바깥에 남는다 (의도, `docs/steps/step_134_sel.md`).
- [ ] (step 134) 편집 모드 F9 / F10 / F11 을 오가며: 엣지 연파랑 #64dcff, 정점 모드 = 보라 점 + 선택 노랑 점 (조금 큼), 엣지 모드 = 선택 엣지 주황 #e3ac79, 면 모드 = 선택 면이 주황 점묘. 가려진 뒤쪽 정점 · 엣지는 셰이딩 모드에서 안 보이고 X-ray (Alt+Z) 에서는 보이는지. 100 % / 125 %.
- [ ] (step 134) 10 만 정점 메시 편집 모드에서 정점 선택 · G 드래그가 느려지지 않는지 (변경마다 캐시 약 30 ms), Smooth Preview 3 을 켠 메시는 케이지 위에 색이 그려지는지 (5 만 정점 초과 + 편집 모드 모디파이어면 Blender 색으로 돌아감). Preferences > Component Colors 끄면 Blender 색.
- [ ] (step 134) Soft Select (b) 켬: 거짓 색 (노랑-빨강-검정) 이 킷 컴포넌트 색 위에 보이는지; 마우스 아래 프리셀렉트 빨강도 그 위에.

## Step 135 — dock width

- [ ] (step 135 WIDTH, #60) Windows 100 % / 125 % / 150 % (또는 Preferences > Interface > Resolution Scale 1.0 / 1.25 / 1.5) 에서 새 Maya 장면을 열고 마우스를 가만히 둔다: 오른쪽 탭 스택 폭이 약 466 / 574 / 672 px 로 맞춰지고 (커서가 잠깐 영역 틈으로 갔다 돌아옴), 탭 「Channel Box / Layer Editor」 「Attribute Editor」 「Modeling Toolkit」 이 「…」 없이 보이는지 (레인 CB 의 자연 폭 탭과 병합 뒤), 큐브를 만들면 「Subdivisions Height」 가 잘리지 않는지, AE 탭의 메뉴 줄 (List … Help) 이 한 줄인지. 뷰포트가 아웃라이너와 독 사이 남은 폭을 다 차지하는지.
- [ ] (step 135) 맞춘 뒤 독 왼쪽 모서리를 직접 끌어 좁히거나 넓혀도 다시 되돌아가지 않는지 (#53 규칙), Tool Settings 를 열고 닫아도 뷰포트 폭이 그대로인지, UI 배율을 바꾸면 다시 맞춰지는지.

## Step 135 — Channel Box / Layer Editor

- [ ] (step 135 CB, #55) Maya 레이아웃 새 장면, 100 % / 125 % / 150 %: Create > Polygon Primitives > Cube → Channel Box INPUTS 에 `polyCube1` 한 줄만 (접힘), 오른쪽 독 아래 절반에 Layer Editor (Display / Anim 탭, Layers / Options / Help, 빈 목록) 가 보이는지 (Maya `research/maya/screens/11_channel_box.png`).
- [ ] (step 135) `polyCube1` 을 클릭 → Width … 행이 그 아래 펼쳐지고, Layer Editor 는 같은 자리에 그대로; 다시 클릭 → 접힘. 펼침은 Ctrl+Z 단계를 남기지 않는지 (Ctrl+Z 가 큐브 생성을 되돌림).
- [ ] (step 135) 펼친 채 두 번째 큐브를 만들거나 다른 오브젝트를 고른 뒤 첫 큐브로 돌아오면 다시 접혀 있는지 (Maya `cb135/d04_first_again.png`). 압출 (polyExtrudeFace1), modifier, 제약 노드도 접힌 채 시작하는지.
- [ ] (step 135) INPUTS 를 여러 개 펼쳐 Channel Box 가 길어지면: 마지막 줄에 ▲ ▼ 단추, Channel Box 위에서 마우스 휠로 행이 스크롤되고 Layer Editor 위의 휠은 Layer Editor 목록에만 작동하는지. Properties 의 modifier 패널 접힘 (show_expanded) 이 Channel Box 클릭으로 바뀌지 않는지.
- [ ] (step 135) 독 위 탭 줄: 손잡이 「::::::::」 다음에 탭 세 개가 글자 폭대로 왼쪽부터 놓이고 「…」 가 없는지 (100 / 125 / 150 %).

## Step 136 — marking menus inside the window

- [ ] Cube near the bottom of the view, hold RMB: no list row is cut by the 3D View / Time Slider border; Time Slider numbers don't show on top of the menu.
- [ ] Same near the left (Outliner) and right (dock) edges, and Shift+RMB / Ctrl+RMB in object, vertex, edge and face mode: everything readable, gestures still go to the right item.
- [ ] Component mode (F9 / F10 / F11), RMB: Select All / Deselect All / Select Hierarchy / Invert Selection are not greyed and work like the Select menu.
- [ ] Hover a greyed item (e.g. RMB > Time Editor): its notice appears in the Help Line.
- [ ] Ctrl+RMB on a mesh in object mode: the convert menu; To Vertices / To Faces select every component of the object in component mode.
- [ ] Select tool, q hold + LMB (Select options): Camera-Based Selection shows a check box that follows the setting.

## Step 137 — animation / render basics

- [ ] Maya layout, key Translate X 0 → 5 (cm), Graph Editor, frame all: with the mouse over the curves the value axis reads 0–5; moving the mouse to the channel list shows Blender's 0.00–0.05 again (Blender limit) — is the switch distracting?
- [ ] Translate + Rotate curves shown together: Blender's numbers stay (no wrong cm labels on degrees).
- [ ] File > New Scene → Cube → Render > Render Current Frame: Render View opens with the cube framed like the viewport; the Outliner shows persp once.
- [ ] Look through a camera (Panels > Perspective > camera) and render: that camera is used.
- [ ] Assign New Material > Blinn: AE Color grey 0.5, Incandescence black, Eccentricity 0.3, Specular Roll Off 0.7.
- [ ] Create > Lights > Point Light: AE Intensity 1, Decay Rate No Decay; Cycles render lights a surface 10 units away like Maya.
