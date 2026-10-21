# Step 130 lane H — 테마 삭제 (#40, 결정 2)

심사자: "Modifying theme XML file is not allowed ... Everything related to theme should be removed."
사용자: "테마 관련 전부 삭제(theme/ 폴더, 테마 적용·저장·복원 코드, 키트 테마에 의존하는 색) — 사용자 테마에서도 보기 좋게,
설명·사이트에 추천 테마 문구".

## 한 것

- 삭제: `src/allset/theme/` (`__init__.py` + `studio_grey.xml`, `studio_grey_5.0/5.1/5.2.xml`), `ASSETS_LICENSE.txt` 의 네 줄,
  `tools/make_theme.py`, `tools/theme_diff.py`, `tools/theme_xml_diff.py`, `tests/test_step43_theme.py`, `tests/test_step119_theme_5x.py`.
- `compat.py`: `theme_file`, `rna_xml` 삭제. `toolbar_back` (사용자 테마를 **읽기만**: Tool Box 여백 색) 과
  `LINEAR_IMAGE_SHADER` (셸프 아이콘 셰이더, 테마와 무관) 는 유지.
- Alt+B / Color Settings (`operators/key_batch3.py`): 테마 그라디언트를 쓰지 않는다. Blender 의 그라디언트 배경은 테마에만 있으므로
  (`view_3d.space.gradients`; 뷰 자체 배경은 단색 `View3DShading.background_color` 하나) Maya 순환의 그라디언트 단계를 뺐다:
  뷰마다 `background_type = 'VIEWPORT'`, Maya 단색 회색 0.36 → 밝은 회색 0.631 → 검정 → 회색 (research/maya/re/background_120.md).
  `THEME` 배경인 뷰 (사용자 테마 색) 는 Maya 공장 상태(회색)로 읽어서 첫 Alt+B 가 Maya 처럼 밝은 회색. `reset_background()` = 모든 뷰 0.36
  단색. Color Settings 대화상자는 Background 색만 (Gradient 필드 삭제). Tool Box 열은 그대로 제외.
- 셸프 (`ui/shelf.py`, 색 부분만): 배경은 원래도 사용자 Image Editor 헤더색. 탭 글자·메뉴 글리프는 고정 밝은 회색 → 사용자 테마
  `header_text_hi` / `header_text` (밝은 테마에서도 읽힘), hover 상자는 배경 밝기에 따라 흰/검정, 구분선은 배경색 기준 어둡게/밝게.
  탭 줄은 Maya 비율 (#444444 → #373737) 로 헤더색을 어둡게 (어떤 테마든).
- 그 밖의 `ui/*` 는 이미 사용자 테마를 **읽기만** 한다 (쓰기 없음) — 확인 후 주석만 고침: `manipulator._theme_axis` (축 색),
  `maya_grid` (격자색), `selection_wire` (`object_active` / `object_selected`), `outliner_sets` (Outliner 글자·배경·선택색),
  `view_furniture` (뷰 축 색), `toolbox.settle` (툴바 배경), `channel_box` (constrained 채널 = 눌린 버튼 = 테마 선택색).
  킷이 자기 배경과 함께 그리는 것 (마킹 메뉴/핫박스, Graph Editor 아웃라이너 패널 #444444, Range Slider, In-View Editor, in-view 메시지,
  소프트 선택 원) 은 Maya 고정색 그대로 — 자기 배경 위라서 어떤 테마에서도 읽힌다.
- `ui/notices.py` Graph Editor/View/Theme 안내문: "Maya Workflow Kit applies a Maya theme" → 사용자가 테마를 설치하라는 문장.
- 도구: `look_compare.py` 의 테마 ΔE 표 (`PAIRS`, `delta_e.md`) 삭제 (픽셀 표는 유지), `look_shots.py` / `look_second_start.py` 의
  "Maya theme on" 확인 삭제, `look_data.MENU_BG["kit"]` = Blender 4.5 팩토리 메뉴색 #181818 (측정), `repo_check.py` /
  `installer_check.py` 는 "Make Maya 가 테마를 바꾼다" → "테마를 그대로 둔다", `tools/marketing/scene.py` 는 그라디언트를 스스로
  (샌드박스 테마에) 설정 (#41 에서 다시 찍을 때 판단).
- 테스트: `test_step120_background` (뷰별 단색 순환, 테마 해시 불변, Color Settings), `test_step107_keys`, `test_step5_layout`
  (`test_no_theme_in_the_kit`: 모듈·연산자·xml 0), `test_step53_compat` / `test_step44_widgets` / `test_step104_editor_chrome` /
  `test_step42_first_start` 의 테마 테스트 삭제·반전, `test_step114_guidelines` / `test_step61_distribution` 자산·쓰기 목록, GUI
  `gui_step120_background` (팩토리 테마에서 순환 픽셀 + 테마 불변), `gui_step113_top` (메뉴바 = 테마 top bar 색, 탭 줄 = 헤더 × Maya 비율,
  테마 이름 불변), `gui_step5_layout`.

## 없어진 이름 (레인 C 가 호출을 지워야 함)

`allset.theme` 모듈 전체: `apply`, `restore`, `is_applied`, `has_backup`, `save_backup`, `backup_path`, `forget_backup`, `THEME_NAME`,
`THEME_FILE`, `LEGACY_FILE`, `MOVED`, 연산자 `allset.theme_apply` / `allset.theme_restore` (`ALLSET_OT_theme_apply/restore`).
`compat.theme_file`, `compat.rna_xml`. `key_batch3.theme_gradients`, `gradient_allowed`, `set_gradient`, `GRADIENT_TOP`, `GRADIENT_BOTTOM`,
`next_state(gradient_ok=)` 인자, 상태 `"GRADIENT"`, `color_settings` 의 `gradient` / `gradient_top` / `gradient_bottom` 속성.
호출하는 곳 (이 레인은 손대지 않음): `__init__.py:18,25,56`, `preferences.py:119-132` (`maya_theme` 옵션), `switch.py:79-81,84-96,107-109,
136-140,192-208,489-493,515-517,549,561`, `first_start.py:34,59`, `welcome.py` 문구, `tests/test_step60_switch.py:69` (Maya 테마 이름 확인),
`tests/gui/sim.py` 등의 `set_mode(..., theme=False)`. 문서: `CLAUDE.md` (make_theme / studio_grey / theme.MOVED / compat.theme_file 줄),
`docs/compat_5x.md`, `docs/DISTRIBUTION.md:42`, `docs/distribution/marketing/references.md:176`, `docs/manual_checks.md:777`.

## 남는 시각 차이 (Blender 팩토리 테마 기준, 측정: 4.5 팩토리 테마 값)

| 무엇 | Maya 2022 | 이제 (Blender 팩토리 테마) |
|---|---|---|
| 리드 선택 / 다른 선택 (외곽선, 선택 와이어) | 연두 #43ffa3 / 흰색 | 주황 #ffa028 / 진한 주황 #ed5700 |
| 뷰포트 배경 (템플릿 뷰는 `THEME`) | 단색 #5c5c5c | #3d3d3d (Alt+B 한 바퀴 뒤 / `reset_background` 후엔 Maya #5c5c5c) |
| Alt+B 그라디언트 단계 | #889db3 → #0d0d0d | 없음 (회색 → 밝은 회색 → 검정 → 회색) |
| 위젯 모양 | 각지고 평평 | Blender 둥근 위젯 |
| 메뉴바 / Status Line / 셸프 줄 | #444444, 탭 줄 #373737 | 테마 헤더색 (#303030), 탭 줄 #282828 |
| 메뉴 배경 | #525252 | #181818 |
| Outliner 선택 줄 | Maya 파랑 | #1d314d |
| Constrained 채널 (눌린 버튼) | Maya 파랑 #5285a6 | 테마 선택색 #4772b3 (여전히 파랑) |
| Dope Sheet 키 / 현재 프레임 | 빨강 / 회색 | Blender 테마 키 색·파랑 플레이헤드 (Time Slider 위 킷 키 틱은 Maya 빨강 그대로) |
| Graph Editor / Dope Sheet 재생 범위 밖 | 음영 없음 | Blender 가 어둡게 칠함 (`preview_range` 테마 색) |
| 매니퓰레이터 축 색 | Maya 빨/초/파 | 테마 축 색 (#ff3352 / #8bdc00 / #2890ff — 거의 같음) |

조치 제안 (이 레인에서 안 함): 템플릿의 3D 뷰를 `VIEWPORT` + Maya 0.36 단색으로 저장하면 (뷰 데이터, 테마 아님) 첫 화면 배경이 Maya 와
같아진다 — `tools/make_startup.py` 는 레인 C (앱 템플릿 → 확장 안 startup.blend) 소유라 통합 때 판단.

## 추천 테마 문구 (리스팅·사이트용)

> Maya Workflow Kit keeps your Blender theme and never changes it. For Maya's colours — a flat grey viewport, light-green lead
> selection and white for the rest of the selection, square flat buttons — install any Maya-style theme you like from
> Preferences > Themes (or Get Extensions); the kit's own drawings (marking menus, hotbox, shelf, Channel Box) adapt to it.

한국어: "Maya Workflow Kit 은 사용자의 Blender 테마를 그대로 쓰고 바꾸지 않습니다. Maya 색 (단색 회색 뷰포트, 연두색 리드 선택, 흰색 나머지
선택, 각진 평평한 버튼) 을 원하면 환경설정 > 테마 (또는 Get Extensions) 에서 Maya 풍 테마를 설치하세요."

## 검증

레인 C 가 아직 `__init__` / `preferences` / `switch` 의 테마 호출을 지우지 않아서, 이 워크트리에서는 그 세 파일에 **커밋하지 않은 임시 shim**
(테마 import 제거, `maya_theme` 업데이트 no-op) 을 넣고 돌린 뒤 되돌렸다.

- 헤드리스 `ALLSET_SANDBOX=lane_h python tests/run.py`: 984 passed, 4 failed (117 파일). 실패 4:
  `test_step120_background::test_color_settings_operator` (테스트가 연산자 속성을 잘못 읽음 → 고침, 재실행 step120 + step107 20/20 통과),
  `test_step115_opt_in::test_opt_in_turns_maya_on_and_disable_restores` (Maya 테마 이름 기대), `test_step60_switch::test_round_trip_in_one_session`
  ("Maya theme not applied") 와 그 연쇄 `test_user_key_edit_and_other_keyconfig_kept` — 셋 다 스위치의 테마 동작이라 레인 C 몫.
- GUI `ALLSET_SANDBOX=lane_h_gui python tests/gui/run.py --shots tmp/lane_h_shots -k step113,step120,step12_,step49,step5_layout`:
  51 passed, 0 failed (5 파일). (`step40` 이름의 GUI 테스트는 없음; `step12` 는 step124/129 파일까지 잡아서 `step12_` 로 좁힘.)
  스크린샷 (팩토리 테마): step113_top (메뉴바·Status Line·셸프 탭/아이콘·Tool Box·Outliner·Channel Box·Layer Editor), gui_step5_object
  (Outliner 선택 줄, Channel Box), gui_step12_strip_* (셸프 3 종), step120_1..5 (배경 순환, Color Settings 대화상자) — 어두운 바탕에 어두운
  글자 같은 읽기 어려운 곳 없음. 마킹 메뉴는 이번 실행에서 찍지 않음 (자기 배경·글자색으로 그려서 테마 무관).
- 이슈: #45 (테마 없이 남는 Maya 와의 차이, maya-parity), 마케팅 재촬영은 기존 #41.
