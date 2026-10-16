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
