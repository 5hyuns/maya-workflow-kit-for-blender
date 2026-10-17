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

### Step 18 — 편집 모드 키

- [ ] (step 18) 편집 모드에서 D 를 누른 채 클릭/드래그로 피벗(3D 커서) 배치 → D 놓고 W 로 이동·회전 시 그 점 기준; D 탭으로 원래 피벗. V 홀드와 함께 정점에 피벗 스냅.
- [ ] (step 18) Ctrl+E (면/엣지/정점), Ctrl+B (정점 모드 = 정점 베벨) 드래그 감각을 Maya 와 비교. Shift+> / Shift+< 반복, Ctrl+F9–F11 변환 결과를 Maya 와 비교.

### Step 19 — 복제

- [ ] (step 19) 애니메이션이 있는 객체를 Ctrl+D: 사본도 같은 액션을 공유하는지(Blender) / Maya 2022 는 사본에 애니메이션이 없는지 비교해 규칙 확정. 그룹 Ctrl+D 후 Outliner 이름 (group2, pCube2 …).

### Step 20 — 타임라인

- [ ] (step 20) 키가 있는 객체에서 `.` / `,` / Alt+`.` / Alt+`,` 를 3D 뷰·타임라인·그래프 에디터 위에서. Range Slider 네 필드를 바꾸면 재생 범위·타임라인 뷰가 Maya 처럼 따라가는지, 재생 범위 토글을 끄면 애니메이션 범위 전체가 재생되는지.

### Step 21 — 단위

- [ ] (step 21) MayaKit 레이아웃 새 씬에서 Create > Polygon Primitives > Cube 의 화면 크기를 Maya 2022 새 씬 기본 persp 와 비교 (뷰 거리·클립은 Maya 값이지만 Blender 뷰포트 렌즈 화각이 다를 수 있음). 1 cm 큐브를 가까이 텀블·돌리·W 이동 했을 때 클립 잘림·그리드(cm 간격)·매니퓰레이터 감각.
- [ ] (step 21) Maya 에서 내보낸 FBX(cm)를 File > Import 로 가져와 Create 큐브와 같은 크기인지, Maya Units 켬/끔 둘 다.

### Step 22 — 매니퓰레이터 Shift+드래그 복제

- [ ] (step 22) W/E/R 툴에서 기즈모 화살표·평면·중앙·회전 링·스케일 핸들을 Shift+드래그 → 사본이 변환되고 원본 제자리. Shift 를 끝까지 누른 채 끌어도 느려지지 않는지, 드래그 도중 Shift 를 떼었다 다시 누르면 Blender 정밀 모드가 되는지. Maya 2022 의 같은 동작과 손 감각 비교.
- [ ] (step 22) Shift+클릭(드래그 없음), 드래그 중 RMB/Esc 취소 때 사본이 남는지 Maya 와 비교. Ctrl+Z 한 번에 사본까지 사라지는지.
- [ ] (step 22) 라이트(스포트 크기 등) 기즈모를 Shift+드래그 했을 때 복제가 일어나지 않아야 함.

### Step 24 — 컴포넌트 Delete

- [ ] (step 24) Maya 2022 와 같은 메시에서 면·엣지·정점(모서리 정점, 3개 이상 엣지 정점, 경계 정점) Delete 결과 비교. 경계 엣지만 선택하고 Delete 했을 때 Maya 경고와 비교.

### Step 25 — cm 그리드·스냅

- [ ] (step 25) MayaKit 레이아웃에서 확대/축소하며 그리드 단계(1 cm → 10 cm → 1 m)가 바뀔 때 X 홀드 스냅 간격이 따라 바뀌는지, Maya 2022 그리드 스냅 감각과 비교.

### Step 26 — Smart Extrude

- [ ] (step 26) 면·엣지 선택에서 이동/회전/스케일 기즈모 Shift+드래그 → 압출 후 변환; Shift+클릭, RMB/Esc 취소 → 아무것도 남지 않음; 그 뒤 Ctrl+Z / Ctrl+Shift+Z 가 앞 작업을 망가뜨리지 않는지. Maya 2022 와 손 감각 비교.
- [ ] (step 26) 스포트 라이트 선택 + 라이트 기즈모(크기·블렌드) Shift+드래그 → 복제 안 됨.

### Step 27 — 매니퓰레이터 크기·뷰 키

- [ ] (step 27) = / - 몇 번 눌러 매니퓰레이터 크기 변화 폭을 Maya 2022 와 비교; 애드온을 껐다 켜면 원래 크기. Home 이 Maya 기본 뷰처럼 느껴지는지 (MayaKit 레이아웃 cm 장면에서). PgUp/PgDn 단계 변화를 3 모드에서 비교.

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

- [ ] (step 31) MayaKit 레이아웃 왼쪽 Outliner 에서 긴 이름(pCylinder12, group3 아래 3 단계)이 잘리지 않는지, 컬렉션 행 없이 오브젝트만 보이는 것이 Maya Outliner 처럼 느껴지는지. 새 컬렉션을 만든 경우 Layer Editor 쪽에서만 보이는 것이 혼란스럽지 않은지.
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

- [ ] (step 38) Channel Box 값 필드를 클릭해 숫자 입력 → Enter: Maya 처럼 바로 적용되는지. `+=5`, `-=2`, `*=2`, `/=2` 가 여러 오브젝트에서 오브젝트마다 자기 값 기준으로 적용되는지. 단위 없는 숫자 = cm (MayaKit 템플릿), `5 m` 도 되는지.
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
- [ ] (step 42) zip 을 Blender 창으로 끌어 놓아 설치해도 같은지. Cancel 을 누르면 다시 묻지 않고, 환경설정 > Maya Kit 맨 위 버튼으로 할 수 있는지.
- [ ] (step 42) Blender 를 껐다 켜면 (파일 없이) Maya 레이아웃으로 열리는지; .blend 를 더블클릭해 열면 그 파일이 그대로 열리는지; 세션 중 File > New > General 은 General 인지.
- [ ] (step 42) Revert Maya Look → 원래 테마·스플래시 설정이 돌아오고 File > New 목록에서 MayaKit 이 사라지는지. Maya Kit 을 끄면 원래 테마로, 다시 켜면 Maya 테마로 돌아오는지.
- [ ] (step 42) 다른 애드온 (예: Node Wrangler) 이 Make Blender Maya 전후로 그대로 켜져 있는지.

### Step 44 — Maya 위젯 감각 (평면 위젯·밀도·Segoe UI)

- [ ] (step 44) Make Blender Maya 뒤 글자·행 크기가 같은 모니터의 Maya 2022 와 같아 보이는지 (125 % 화면: Resolution Scale 0.8). 100 %·150 % 모니터에서도 (0.8 이 아니라 1.0 / 0.667 이 되는지).
- [ ] (step 44) 실제 모니터 배율을 Blender 실행 중에 바꾸면 (노트북 ↔ 외부 모니터) 밀도는 처음 계산한 값 그대로 (delegated: 다시 켜면 새로 계산). 작아서 불편한지.
- [ ] (step 44) Segoe UI: 한글·특수문자 (°, ×) 가 빠지지 않고 보이는지 (Blender 가 빠진 글자는 기본 글꼴로 채우는지), 마킹 메뉴·핫박스 글자도 Segoe UI 인지.
- [ ] (step 44) 각진 평면 위젯이 Maya 처럼 읽히는지; 버튼·필드 경계가 너무 안 보이지 않는지 (엠보스 없음). 메뉴 그림자 없음이 어색하지 않은지.
- [ ] (step 44) Revert Maya Look / Maya Kit 끄기 → Resolution Scale·글꼴·와이어 부드럽게가 원래대로 돌아오는지.

### Step 45 — Maya 그리드

- [ ] (step 45) MayaKit 레이아웃 persp: 그리드가 ±12 cm 에서 끝나고 5 cm 마다 굵은 선, 축선도 굵은 회색 (빨강/초록 아님). 확대·축소·텀블해도 깜빡이거나 끊기지 않는지, 큐브가 그리드 뒤를 가리는지.
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

- [ ] (step 49) MayaKit 레이아웃: 위에서 아래로 메뉴바 / Status Line / Shelf / [툴박스 | Outliner | 뷰 | Channel Box 도크] / Time Slider / Range Slider / Help Line + Command Line 한 줄. Maya 를 옆에 띄워 놓고 배치가 같게 읽히는지.
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
