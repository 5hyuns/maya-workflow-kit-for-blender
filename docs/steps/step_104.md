# Step 104 — Editor chrome: Graph Editor, Dope Sheet, UV Editor with Maya menus

Backlog 6 of audit 7 (step_98.md #24, #26; PLAN 「재점검 7차」 6).

## 계획

Evidence first: the three editors' menu bars and icon rows are captured in a Maya 2022 GUI
(`research/scripts/maya_editors104/`: Qt menus popped up so their postMenuCommand fills them, `cmds.menuItem`
flags for option boxes / check / radio items, the icon-row widgets with their Maya control names; output
`research/maya/screens/editors104/_editors104.json` + menu and window shots). Measured: Graph Editor 9 menus
(Edit / View / Select / Curves / Keys / Tangents / List / Show / Help), Dope Sheet 8 (no Select), UV Editor 11
(Edit / Create / Select / Cut/Sew / Modify / Tools / View / Image / Textures / UV Sets / Help) + UV Toolkit 2
(Options / Help). Option boxes are hidden Qt actions after their item (`optionBox` true).

1. **Menu data** — `tools/gen_editor_menu_data.py` turns the capture into `ui/editor_menu_data.py`
   (labels and structure only, like `menu_data.py`): `EDITORS[editor] = [(title, items)]`, `OPTION_BOXES`,
   `CHECKS` (Maya check / radio items). Paths are `<Editor>/<Menu>/<item>` ("Graph Editor/Keys/Insert Key Tool").
   `menu_sets.iter_items()` walks them too, so the step 101 rules apply unchanged: every leaf is mapped
   (`ui/editor_menu_map.py`, merged into `menu_map.MAP`) or greyed with a notice (`notices.CATEGORIES` rules for
   editor paths). One `Menu` class per editor menu (`MAYAKIT_MT_ed_<editor>_<n>`), option boxes keep the ❒ mark.
2. **Check items** — a new mapping kind `("prop", "<context path>", {"value": ...})` draws `layout.prop` /
   `prop_enum` (a real Blender check box / radio state, e.g. View > Show Play Range Shades, Tangents > Default In
   Tangent); `run_action` toggles / sets it.
3. **Headers** (header draw override, restored on unregister, snapshotted in `tests/kit.py`):
   `GRAPH_HT_header.draw` (FCURVES mode) and `DOPESHEET_HT_header.draw` (Dope Sheet / Action modes; TIMELINE and
   the rest stay Blender's: the kit Time Slider lives there) draw editor-type button, Maya menus, a 「Blender」 menu
   with Blender's own editor menus, the Maya icon row (captured order), then Blender's filter popover at the right
   end. Graph / Dope Sheet areas have one header row only (no tool header, measured: `show_region_*`), so menus and
   icons share it (delegated). UV Editor: `IMAGE_HT_header` (the `ui/shelf.py` wrapper) draws the Maya menus in UV
   mode and the tool header draws the Maya icon row (Maya's second row), Blender's pivot / snap / image / UV map
   controls after it.
4. **Icon rows** — one spec list per editor (Maya control name → icon, action, Maya tooltip); buttons without a
   Blender counterpart draw greyed with a notice tooltip (`maya_kit.editor_icon_unavailable`). Stats fields =
   selected key time / value (Scene string proxies with get/set, undo like Channel Box entry).
5. **Channel list** — Graph Editor: Blender's rows (object → action → group → F-curve "X Location") can't be
   relabelled or removed from Python, so the kit draws the Maya list over the channel region (CHANNELS
   POST_PIXEL): object rows, then attribute rows "Translate X" in Maya's axis colours (no Action / group rows).
   Clicks on it are kit keymap items placed first in "Animation Channels" (PASS_THROUGH outside the overlay):
   click = select that curve (and show only the selected rows' curves, like Maya), Ctrl = toggle, Shift = add,
   object row = all its curves, +/- = expand. Dope Sheet rows must line up with the key rows, so the Dope Sheet
   keeps Blender's list, collapsed to object rows on open (= Maya's Dopesheet Summary + pCube1).
6. **Out-of-range shading / frame 0** — the brown is the theme's `preview_range` (the kit keeps the Maya playback
   range in the preview range): alpha 0 in the Maya theme for Graph Editor / Dope Sheet. On open, the view is
   framed on the playback range starting at frame 1 (`view2d.pan` after `anim.scene_range_frame`), so frame 0 and
   the area before it don't show.
7. **UV Editor** — on open: sidebar shown on the UV Toolkit tab (`menu_extras.sidebar_tab_later`), the toolkit
   gets Maya's Options / Help menu row at its top; the Blender toolbar stays hidden.

Verification: headless `tests/test_step104_editor_chrome.py` (menu counts = capture, every editor leaf mapped or
noticed, check items, icon rows, header draw restored, curve infinity / in-out tangents / stats fields / channel
rows), GUI `tests/gui/gui_step104_editors.py` with shots side by side with the Maya capture (e02 / e03 / d01).

## 한 것

- **Maya 측정** (`research/scripts/maya_editors104/`, Maya 2022 GUI, factory prefs): Graph Editor / Dope Sheet / UV Editor
  창의 메뉴 막대를 Qt 로 펼쳐 `cmds.menuItem` 플래그와 함께 기록 (`research/maya/screens/editors104/_editors104.json`, 메뉴
  그림 70 여 장). 옵션 상자는 항목 뒤의 숨은 Qt action (`optionBox` true) 이라 처음 캡처에서 빠졌다가 다시 잼. 라디오 항목은
  `radioButton` 이 켜진 항목에만 답하므로 구분선 사이 묶음 단위로 판정 (`tools/gen_editor_menu_data.py`).
- **메뉴 데이터**: `ui/editor_menu_data.py` (생성) — 4 막대 30 메뉴, 잎 585, 옵션 상자 120, 체크 / 라디오 169.
  `menu_sets.iter_items()` 가 같이 돌므로 step 101 규칙 (잎마다 매핑 또는 안내) 이 그대로 적용.
- **매핑** `ui/editor_menu_map.py` (menu_map.MAP 에 합침): 339 / 585 작동 — Graph Editor 137/229, Dope Sheet 117/181,
  UV Editor 84/172, UV Toolkit 1/3. 회색 246 은 모두 안내 (`notices.CATEGORIES` 편집기 규칙 + Auto Ease/Mix/Custom
  NOTICES). 새 매핑 종류 `("prop", 경로, {"value"})` = Maya 체크 / 라디오 항목을 Blender 속성 체크박스 / 라디오로
  (`menu_sets.draw_prop` / `set_prop`, `maya_kit.menu_set_value`): View > Infinity = 외삽 표시, Default In/Out Tangent =
  Preferences 새 키 핸들 / 보간, Show > Objects / Attributes = 도프시트 필터 (Translate → 이름 필터 "Location"),
  List > Auto Load Selected Objects = Only Show Selected 등.
- **새 / 확장 연산자** (`operators/graph_keys.py`): `maya_kit.curve_infinity` (Pre / Post Infinity: Cycle / Cycle with
  Offset / Oscillate = Cycles 모디파이어의 그 쪽 모드, Linear / Constant = 커브 외삽 — Blender 는 양쪽 공통, INFO 로 알림),
  `maya_kit.curve_color` (Change / Remove Curve Color), `set_tangent` 에 `side` (In / Out Tangent: 핸들 형은 그 쪽만, Linear /
  Stepped 는 구간 소유 키 = In 이면 앞 키), `set_tangent` / `key_edit` 가 Dope Sheet 에서도 선택 키에 (action.copy / paste /
  delete).
- **헤더** (`ui/editor_chrome.py`): `GRAPH_HT_header.draw` (FCURVES), `DOPESHEET_HT_header.draw` (Dope Sheet / Action;
  Timeline 등은 Blender 것 그대로 — kit Time Slider) 교체, unregister 에서 복원, `tests/kit.py` 스냅샷. 편집기 버튼 + Maya
  메뉴 + 「Blender」 메뉴 (Blender 원래 메뉴, Dope Sheet 모드 선택 포함) + Maya 아이콘 줄 + 오른쪽 필터. 헤더가 한 줄뿐이라
  (영역에 tool header 없음, 측정) 메뉴와 아이콘이 한 줄 (delegated). 헤더 메뉴 접힘 (Collapse Menus) 은 한 메뉴로.
  UV Editor: `ui/shelf.py` 의 IMAGE 헤더 래퍼에서 1 줄 = Maya 메뉴, tool header (둘째 줄) = Maya 아이콘 줄 + 이미지 칸 +
  UV 맵 이름 + Blender 피벗 / 스냅 / 소프트 선택.
- **아이콘 줄**: 캡처의 컨트롤 이름 순서대로 (Graph 43, Dope 13, UV 14 버튼 + Stats / 이미지 / UV 맵). Blender 대응이 없는
  버튼은 회색 + 안내 툴팁 (`maya_kit.editor_icon_unavailable`). Stats = 선택 키 시간 / 값 (Scene 문자열 프록시, Channel Box
  입력처럼 `+=5` / `*=2`, 값은 표시 단위 cm).
- **Graph Editor 채널 목록**: Blender 행 (오브젝트 → 액션 → 그룹 → "X Location") 은 Python 으로 이름을 바꾸거나 뺄 수 없어,
  kit 가 채널 영역 위에 Maya 목록을 그림 (CHANNELS POST_PIXEL): 오브젝트 행 + "Translate X" (빨강) / "Translate Y" (초록) /
  Z (파랑), 액션 / 그룹 행 없음. 클릭 = "Animation Channels" 맨 앞의 `maya_kit.graph_channel_click` (PRESS: Blender 의
  channels_click 이 PRESS 라 처리된 PRESS 뒤에는 CLICK 이 안 옴 — 측정): 행 = 그 커브만 선택·표시 (Maya 처럼 나머지는 숨김),
  Ctrl 토글, Shift 추가, 오브젝트 행 = 모든 커브, −/+ = 접기. 검색칸 위는 통과.
- **Dope Sheet**: 열 때 채널을 접고 Summary 만 펼침 → Maya 의 Dopesheet Summary + pCube1 과 같은 두 줄 (키 줄과 맞아야 해서
  Blender 목록 유지).
- **범위 밖 음영 / 0 프레임**: 갈색은 테마 `preview_range` (kit 는 Maya 재생 범위를 미리보기 범위로 둠, step 20) → Maya 테마에서
  Graph Editor / Dope Sheet 투명 (`tools/make_theme.py`). 열 때 재생 범위를 1 프레임부터 보이게 (`anim.scene_range_frame` 뒤
  `view2d.pan`, 측정 view 0.49 … 128.5), Graph Editor / Dope Sheet 사이드바 숨김 (F-Curve 패널 / RNA Array Index — Maya 에 없음).
- **UV Editor**: 열 때 tool header 켜고 사이드바를 UV Toolkit 탭으로 (`sidebar_tab_later`), 툴킷 맨 위에 Maya 의 Options / Help
  메뉴.
- `tools/menu_count.py` 가 편집기 메뉴 막대도 셈.

## 검증

- 헤드리스 `tests/test_step104_editor_chrome.py` 12/12: 메뉴 제목 = Maya 캡처, 잎 수 585 = 캡처의 보이는 항목 수, 옵션 상자 120,
  안내 없는 회색 0, 매핑 연산자 존재, 메뉴 클래스 / 하위 메뉴 등록, 체크 항목 = 속성, 아이콘 = Blender 아이콘 이름 + Maya 순서,
  헤더 교체, Infinity / In·Out 탄젠트, Stats 읽기·쓰기 (+=6 → 30 프레임, 값 7 cm), Graph 목록 행 (액션 / 그룹 행 없음),
  테마 음영 0, 키맵 항목.
- GUI `tests/gui/gui_step104_editors.py` 10/10 (Graph / Dope 1 프레임부터, Translate Y 클릭 → 그 커브만, Tangents 메뉴 열림,
  Dope Summary + 접힌 pCube1, UV 아이콘 줄 + UV Toolkit 탭). 나란히 그림 `research/maya/screens/step104/`
  (e02_graph_editor / e02_graph_tangents_menu / e03_dope_sheet / d01_uv_editor `_pair.png`, 왼쪽 Maya audit7 캡처).
- 메뉴 수 (Maya 캡처 대비): 메뉴 30/30 같은 제목·순서, 잎 585/585.
- 헤드리스 전체 769/769 (전 757 + step 104 12), GUI 전체 1041/1041 (전 1031 + step 104 10). 처음 돌렸을 때 3 실패 → 고침: `test_keymap_maya` 에 "Animation Channels"
  키맵 스택, step 51 옵션 상자 비교를 `menu_sets.OPTION_BOXES` (편집기 막대 포함) 로, step 70 툴바 — `draw` 를 통째로 바꾸면
  다른 곳에서 append 한 헤더 UI 가 사라져 **클래스 자신의 draw (`_draw_funcs[0]`) 만 교체** 하도록 (delegated), step 70 의 탄젠트
  버튼은 kit 크롬이 켜져 있으면 아이콘 줄이 대신 그림.

## 남은 것

- Graph Editor kit 목록은 Blender 채널 영역의 스크롤을 따라가지 않음 (행이 영역 높이를 넘으면 잘림), 드래그로 여러 행 고르기
  (Maya 마키) 없음, 조인트 (포즈 본) / 셰이프 키 커브는 오브젝트 행 밑에 따로 나오지 않음 (오브젝트 자신의 커브만).
  Maya 의 이탤릭 이름 (선택되지 않은 속성) 은 blf 기본 글꼴에 이탤릭이 없어 그대로.
- Dope Sheet 는 Blender 목록 (Summary 라벨 「Summary」, 펼치면 액션 / 그룹 행) — 키 줄과 맞춰야 해서 덧그리지 않음.
  Maya Dope Sheet 의 밝은 회색 캔버스는 타임라인과 같은 테마 (`dopesheet_editor.space.back`) 라 못 바꿈.
- Graph / Dope 헤더 한 줄: 아이콘 줄이 길어 664 px Maya 크기 창에서는 오른쪽이 가려짐 (헤더 스크롤). 시뮬레이션에서는 헤더
  메뉴 클릭이 열리지 않아 GUI 테스트는 `wm.call_menu` 로 메뉴를 염 (manual_checks).
- 회색 246: Region / Retime / Lattice 키 툴, Scene Time Warp, 키 단위 Mute, 가중치 탄젠트, Show 필터 대부분, UV Best Plane /
  Contour Stretch / Stack·Snap 계열, Isolate Select, PSD 등 (모두 안내 있음).
- 다음: step 105 Hypershade / Render Settings / Script Editor 모양 (step_98.md #31–#33).
