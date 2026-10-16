# HANDOFF

## 현재 작업

- Step 6 (M2-b Channel Box + Layer Editor) 완료 — `docs/steps/step_6.md`. 헤드리스 79/79, GUI 52/52.
- Channel Box: `src/maya_kit/ui/channel_box.py` (프록시 `Scene.maya_kit_cb`, 채널 선택 `WindowManager.maya_kit_cb_selected`, MMB 슬라이더). Layer Editor: `src/maya_kit/ui/layer_editor.py` (`Collection.maya_kit_layer`, "Display Layers" 루트).

## 바로 다음 할 일

- **Step 7 — M2-c 상단 UI** (`docs/PLAN.md` #7): Status Line(메뉴셋 드롭다운, 선택 마스크, 스냅 토글 버튼, 렌더 버튼 — TOPBAR/헤더 확장), 커맨드 라인(Python 입력 → exec, 결과/오류 표시, 'MEL은 지원 안 함' 안내, 자주 쓰는 Maya 명령 Python 별칭), Range Slider, 타임라인 모양, `.` `,` Alt+`.` Alt+`,` 키/프레임 이동.
  - 근거: `research/maya/ui_layout.md` §4.1–4.2 (메뉴셋·Status Line 그룹 :193-235), §4.10–4.13 (Time/Range Slider, Command Line, Help Line), `research/blender/api_limits.md` #10 #12 #13 #14, `research/maya/hotkeys_default.json` (`.`/`,` NextKey/PreviousKey, Alt+`.`/Alt+`,` NextFrame/PreviousFrame — 대응표 "계획 Step 7" 행).
  - TOPBAR/STATUSBAR `.append()` 는 unregister 에서 `.remove()` (스냅샷의 `ui_extensions` 가 검사). 커맨드 라인 exec 는 사용자 입력 실행이므로 결과/예외를 캡처해 표시.
  - 스냅 토글 버튼은 Step 3 홀드 상태(`operators/hold.py`)와 같은 tool_settings 를 쓰므로 홀드 중 표시가 바뀌는 점 확인.
  - GUI 스크린샷으로 상단 바·커맨드 라인 직접 확인 (`tests/gui/gui_step7_*.py`).
