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

- [ ] (step 5) 애드온 환경설정 「Install Maya Layout」 → File > New 에 MayaKit 이 보이고, 선택하면 General 레이아웃(좌 Outliner / 가운데 뷰포트 / 우 Layer Editor·Properties / 아래 타임라인)으로 새 파일.
- [ ] (step 5) 「New File with Maya Layout」 → 확인 창 후 같은 결과. 「Remove Maya Layout」 → File > New 목록에서 사라짐.
- [ ] (step 5) 「Apply Maya Theme」 → Maya 와 나란히 놓고 회색·선택 색·그라디언트 비교 ([K] 값 조정 필요 여부). 「Restore Previous Theme」 → 원래 테마.
- [ ] (step 5) Maya Kit 을 끈 상태에서 MayaKit 템플릿으로 새 파일 → Maya Kit 이 다시 켜짐.
- [ ] (step 5) 오브젝트 와이어프레임(4) 색: 비선택 짙은 파랑, 선택 초록, 리드 흰색이 Maya 와 비슷한지.

### Step 6 — Channel Box / Layer Editor

- [ ] (step 6) 사이드바(N)에서 "Channel Box" 탭 한 번 클릭 -> 이후 그 화면은 Channel Box 를 기억 (템플릿에서 자동 지정 불가).
- [ ] (step 6) 오브젝트 3개 선택 -> Translate X 에 값 입력 -> 셋 다 같은 값; Ctrl+Z 한 번에 되돌림.
- [ ] (step 6) Translate X 이름 클릭 -> 뷰포트 MMB 좌우 드래그로 값 변화 (Ctrl 느리게, Shift 빠르게), 커서가 화면 끝에서 감겨도 계속; ESC 로 취소. 채널 선택 해제 후 MMB -> Move 툴 드래그.
- [ ] (step 6) Channels 메뉴: Key Selected -> 타임라인에 키, 필드 붉게; Lock Selected -> 회색·편집 불가; Hide Selected -> 행 사라짐, Show All -> 복귀.
- [ ] (step 6) Settings 메뉴 속도 Slowest~Fast, Hyperbolic -> 슬라이더 감도 (Maya 와 체감 비교).
- [ ] (step 6) Layer Editor: 선택으로 새 레이어 -> V 끄면 숨김, T -> 와이어·선택 불가, R -> 선택 불가, P 끄고 재생(Alt+V) -> 재생 중만 숨김. 레이어 삭제 -> 원상.

### Step 7 — 메뉴바·메뉴셋, Status Line, 커맨드 라인, Help Line

- [ ] (step 7) 저장한 사용자 환경설정으로 Blender 시작 → File > New > MayaKit: 활성 키맵이 계속 "Maya" 인지 (GUI 테스트의 `--factory-startup` 에서는 Blender 로 돌아감).
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

- [ ] (step 12) MayaKit 레이아웃: 메뉴바 아래 Status Line, 그 아래 셸프 (Maya 와 같은 순서), 창 크기를 바꿔도 띠가 두 줄 높이로 남는지.
- [ ] (step 12) Poly Modeling 큐브 버튼 클릭 → pCube1, **더블클릭** → 큐브 하나 + Adjust Last Operation 팝업 (두 개 생기지 않음), Ctrl+클릭 → 옵션.
- [ ] (step 12) 탭 드롭다운 / ◀ ▶ 로 Rigging·Animation·Rendering 전환, 다시 시작해도 마지막 탭 유지 (환경설정 저장 시).
- [ ] (step 12) 톱니 > New Shelf → Add Button(스크립트 한 줄, 아이콘 이름) → 클릭 실행, Edit/Delete Button, Add Last Command (커맨드 라인 실행 후), 다시 시작해도 사용자 셸프가 남음.
- [ ] (step 12) 팩토리 레이아웃에서 Windows > UI Elements > Shelf 로 띠 추가/제거, 다른 Image Editor 는 평소처럼 보임.

### Step 13 — 배포

- [ ] (step 13) 실제 사용자 설정(새 프로필)에서 zip 을 끌어다 놓아 설치: Maya 키맵·내비게이션 적용, Quick Setup 창에서 Continue 를 눌렀을 때 키맵이 Blender 로 바뀌는지 (바뀌면 Activate Maya Keymap).
- [ ] (step 13) Install Maya Layout → File > New > MayaKit → Blender 재시작 뒤에도 레이아웃·키맵 유지, Remove Maya Layout 후 템플릿 목록에서 사라짐.
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
