# Step 72 — 메뉴 세트 상단 바 다시 그리기 + Maya 인뷰 메시지

## 계획 (delegated)

### 1. 상단 바 다시 그리기 (재점검 4차 발견, step_71.md)

`maya_kit.menu_set` (F2–F6, `operators/tool_keys.py`) 은 `window.screen.areas` 만 다시 그린다. Maya 메뉴 바가 있는 상단 바는
전역 영역이라 그 목록에 없어서, 마우스가 상단 바에 갈 때까지 "Modeling" 이 그대로 남는다.

- `ui/status_line.draw_left` (상단 바를 그리는 함수) 가 그리는 동안 `context.area` 를 창 포인터별로 기억한다
  (`ui/notices.remember_status_area` 와 같은 방식).
- `status_line.redraw_top_bars()` 는 지금 열려 있는 창의 것만 tag_redraw 한다. 닫힌 창의 전역 영역은 해제되므로,
  창 포인터가 `wm.windows` 에 없으면 지운다.
- menu_set 이 이 함수를 부른다.
- 검증: gui_step35 에서 상단 바 호버를 빼고 F3 스크린샷 → "Rigging" + Skeleton/Skin 메뉴.

### 2. Maya 인뷰 메시지 (research/maya/interaction.md:30)

Maya 실측 (Maya 2022 GUI, `research/scripts/maya_ivm/ivm.py` 실행, 화면 `research/maya/screens/ivm/`, 저장소 밖):

- 기본값: `inViewMessageEnable 1`, 표시 시간 2.0 s, 불투명도 75 (PREF:214-220, 실행 중 optionVar 로 다시 확인).
- 모양: 둥근 회색 상자, 흰 글자, `<hl>` 강조 단어는 노란색.
  - 상자 #484848, 불투명도 0.75: #5c5c5c 뷰 위에서 #4d4d4d 로 측정.
  - 노랑 #eded08.
  - 글자 위젯 불투명도 0.9.
  - 한 줄 높이 25 px, 안쪽 여백 10 px.
- 위치:
  - 기본 위치 (doGroup / doHideObjects) 는 뷰 왼쪽 위에서 (10, 11) px.
  - `-pos topCenter` (F8 / 소프트 선택 / Make Live) 는 뷰 가운데, 같은 높이.
- 시간: 0.25 s 에 0.72, 1.5–2.6 s 에 최대, 3.6 s 에 0.17.
  - 그래서 페이드 인 0.3 s → 2.0 s 유지 → 페이드 아웃 1.5 s 로 근사 [I].

Maya 가 메시지를 띄우는 곳 (Maya 2022 scripts 를 grep `inViewMessage`) 중 kit 에 같은 동작이 있는 것만 붙인다:

| Maya | 근거 | kit |
|---|---|---|
| F8 오브젝트 ↔ 컴포넌트 | toggleSelMode.mel:28-30 (topCenter) | F8 = 새 `maya_kit.toggle_sel_mode` (editmode_toggle + 메시지) |
| 그룹 성공 / 선택 없음 | doGroup.mel:19-38 | `maya_kit.group` |
| 숨김 (Ctrl+H, Alt+H), 숨길 것 없음 | doHideObjects.mel:76-90 | `maya_kit.visibility` HIDE / HIDE_UNSELECTED |
| h 토글할 것 없음 | toggleVisibilityAndKeepSelection.mel:124-125 | `maya_kit.visibility` TOGGLE |
| 소프트 선택 켬 (b) | showSoftSelectEnabledMsg.mel:10 (topCenter) | `taphold.SoftSelectBinding.tap` (켤 때만) |
| Make Live 켬 / 끔 | statusLine.mel:1891-1900 (topCenter) | `maya_kit.make_live` |

- 대칭 토글과 메뉴 세트 전환: Maya 는 메시지를 띄우지 않는다 (grep 결과 없음). 그래서 붙이지 않는다.
- Shift+M / Ctrl+M 메뉴 바 숨김 메시지: kit 에 그 키가 없어서 붙이지 않는다.
- 문구는 Maya 문자열을 복사하지 않고 같은 뜻을 kit 말로 쓴다 (decision 6). 안내하는 키는 kit 의 실제 키로 쓴다.

설계:

- `ui/view_message.py`:
  - `show(context, text, pos)`: text 는 `<hl>…</hl>` 와 `\n` 을 쓴다.
    - 메시지는 부른 연산자의 3D View 에 뜬다 (context.area / region).
    - 3D View 밖 (메뉴, 핫박스) 에서 불렸으면 창의 주 3D View 에 뜬다 (`status_line.main_view3d`).
    - Tool Box 열 (`toolbox.is_toolbox`) 은 제외한다.
  - 새 메시지는 이전 메시지를 바꾼다 (Maya 도 하나씩).
  - 그 지역에만 POST_PIXEL 로 그린다. 타이머가 0.05 s 마다 다시 그리고, 끝나면 멈춘다.
  - 순수 함수 (bpy 없음): `parse(text)` → 줄별 (글자, 강조) 조각, `alpha(t)` → 페이드 곡선. 헤드리스로 테스트한다.
- add-on 환경설정 `in_view_messages` (Maya inViewMessageEnable, 기본 켬, CORE `preferences.py`).
- Maya 굵은 글꼴 대신 Blender UI 글꼴 (blf 0) 을 쓴다. 굵게 그리는 방법이 없음 [delegated].

## 한 것

- 상단 바 (`ui/status_line.py`): `draw_left` 가 창별로 상단 바 영역을 기억하고, `redraw_top_bars()` 는 열린 창의 것만 다시 그린다.
  `maya_kit.menu_set` 이 이 함수를 부른다.
- `ui/view_message.py`: 위 「계획」의 모양·위치·시간대로 그린다.
  - 왼쪽 위 메시지가 Blender 텍스트 정보 (User Perspective…) 가 켜진 뷰에서는 가운데 위로 간다 [delegated].
    MayaKit 템플릿은 그 정보를 끈다.
- 트리거:
  - F8 = 새 `maya_kit.toggle_sel_mode` (`operators/tool_keys.py`). F8 키 / `Select > Object/Component` / mapping 의 `SelectToggleMode`.
  - `maya_kit.group` (성공 / 빈 그룹), `maya_kit.visibility` (`message()`: Ctrl+H, Alt+H, 할 것 없는 h),
    b 탭으로 소프트 선택 켤 때 (`taphold.SoftSelectBinding`), `maya_kit.make_live`.
- 환경설정 UI Elements 「In-View Messages」 (`in_view_messages`, 기본 켬).
- Maya 실측 스크립트 `research/scripts/maya_ivm/` + 화면 `research/maya/screens/ivm/` (저장소 밖).
  `research/maya/interaction.md:30` 에 측정값을 더했다.
- 사고: 첫 실측 실행이 출력 경로를 잘못 받아 step 40 의 `research/maya/screens/_log.txt` (촬영 로그, 미추적) 를 비웠다.
  - 그 Maya PID 만 바로 끝냈다.
  - 로그는 이날 앞서 읽은 부분 (shot 01–12) 으로 되살리고 표시해 두었다.
  - PNG 는 그대로다.

## 검증

- 헤드리스 `python tests/run.py`: **581/581** (67 파일; 새 `test_step72_view_message.py` 7).
- GUI `python tests/gui/run.py`: **496/496** (55 파일).
  - 새 `gui_step72_view_message.py` 12: F8 두 번, Ctrl+G, Ctrl+H (선택 있음 / 없음), b 켬 / 끔, 4 초 뒤 사라짐.
  - `gui_step35` 는 상단 바 호버를 뺐다. 상단 바 draw 를 기록해서 F3 뒤 `riggingMenuSet` 으로 다시 그려졌는지 확인한다.
- `python tools/dogfood.py`: **47/47**, 콘솔 0.
- 재점검 4차 세션 다시 실행 (MayaKit 템플릿): 14/15.
  - 실패 1 은 step 71 과 같은 세션 확인 오류다.
  - `a4_05_menuset_f3.png` 에 "Rigging" + Skeleton / Skin / Deform / Constrain / Control 이 호버 없이 보인다.
  - `a4_02_group_outliner.png` 에 "group1 grouped." 가 뷰 왼쪽 위에 보인다.
- 스크린샷 직접 확인: `gui_step72_f8_component.png` (가운데 위, 두 줄, "on" 노랑), `gui_step72_hide.png`, `gui_step72_group.png`.

## 남은 것

- Maya 굵은 글꼴, 메시지 드래그로 끄기 (`-dragKill`) 는 없다. 페이드 시간은 3 장 사이에서 근사했다 [I].
- Maya 메뉴 바 숨김 (Ctrl+M / Shift+M) 메시지: 그 키가 아직 없다 (keymap 미검토 행).
- 컴포넌트 숨김 메시지 (Mesh 편집 모드 Ctrl+H 등) 는 붙이지 않았다. kit 편집 모드 숨김은 Blender 키다.
- 손 확인: `docs/manual_checks.md` 「Step 72」.
