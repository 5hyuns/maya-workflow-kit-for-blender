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
