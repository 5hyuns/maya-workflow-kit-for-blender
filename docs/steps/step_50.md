# Step 50 — 에디터 크롬 (Channel Box / Layer Editor · Outliner · Time Slider)

backlog 9 (`docs/PLAN.md` 「Maya 동일화 계획」). 근거: Maya 크롭 `research/maya/screens/11b_channel_box_crop.png`,
`17_outliner_crop.png`, `20_time_slider_crop.png`, `21_range_slider_crop.png`; compare/02·07·11·12·16;
`research/maya/channel_box.md:20-35` (CB 메뉴 줄 Channels/Edit/Object/Show), `:95-135` (메뉴 항목), `:137-170` (Layer Editor
탭 Display/Anim, 메뉴 Layers/Options/Help, 툴바); `research/maya/ui_layout.md:258-264` (Outliner), `:272-286` (Time/Range Slider).

## 계획

### 결정 (delegated)
1. **Channel Box**: 패널 머리 (접는 화살표 + 「Channels」 + 톱니) 없앰 (`HIDE_HEADER`). 맨 위 메뉴 줄 Channels / Edit / Object / Show
   (`MENU_BAR`): Channels = 기존 메뉴, Edit = Maya Edit 메뉴 중 대응되는 것 (Graph Editor, Attribute Editor, Material Attributes,
   Delete History, Select Node, Delete Node, Settings ▸ = 톱니에 있던 것; 나머지 회색), Object = 선택된 오브젝트 목록 (고르면 리드),
   Show = Show All (숨긴 채널 다시) + 회색 필터. 이름 줄은 상자 없는 굵은 이름, SHAPES / INPUTS 는 상자 없이 머리 글자 + 들여쓴 행.
   선택 없음 = Maya 문구 'Select objects in the scene to view, edit and set keyframes on channels (attributes)' 가운데 정렬.
2. **Layer Editor**: 패널 머리 없앰; Display / Anim 탭 (`WindowManager.maya_kit_le_tab`), 메뉴 줄 Layers / Options / Help,
   아이콘 버튼은 오른쪽 정렬. Anim 탭 = Blender 에 애니메이션 레이어가 없어 안내 + NLA 편집기 열기 (delegated).
3. **Outliner**: Maya 식 Outliner (`display_mode` VIEW_LAYER, 컬렉션 행 없음, 오브젝트 내용 없음 = 템플릿·Windows > Outliner) 의
   머리를 `OUTLINER_HT_header.draw` 교체로 Display / Show / Help 메뉴 + 검색 칸으로. 눈 아이콘 열 숨김 (Maya 에 없음; H 키로 숨김).
   persp/top/front/side 카메라 행과 defaultLightSet/defaultObjectSet 은 Blender 장면에 그런 오브젝트가 없어 그리지 못함 (C 목록) — 남은 것.
4. **Time Slider / Range Slider**: 템플릿 타임라인의 사이드바 (Time Slider 줄 오른쪽, 높이 36) 에 현재 프레임 칸 + 재생 버튼 8 개
   (`DOPESHEET_EDITOR` UI 패널). 헤더 (= Range Slider 줄): Maya 순서 [시작][재생 시작][범위 막대][재생 끝][끝] | 자동 키 | No Character
   Set (회색) | No Anim Layer (회색) | fps 메뉴 | 반복 (회색: Blender 는 늘 반복) | 소리 | 애니메이션 설정 (Playback / Keying / View /
   Marker 를 모은 메뉴). Blender 의 Playback/Keying/View/Marker 메뉴는 `TIME_MT_editor_menus.draw_collapsible` 덮어쓰기로 뺌.
   사이드바가 없는 타임라인 (팩토리 레이아웃) 은 재생 버튼을 헤더에 그대로 둔다.
5. 검증: 헤드리스 = 메뉴 줄 라벨 목록 (기록용 가짜 layout 으로 draw 실행), 교체한 draw 복원 (`tests/kit.py`), 템플릿 타임라인 사이드바;
   GUI = 스크린샷 + Maya 크롭 비교, CB 행 간격 (density.md), CB 배경 ΔE (pixels.md).

### 구현 중 바뀐 것 (delegated)
- 도크 전환 줄 (Channel Box / Layer Editor | Attribute Editor) 은 머리 없는 패널끼리 `bl_order` 가 지켜지지 않아 (실측: CB 아래로 감)
  CB·AE 패널 안 맨 위에 그림 (`attribute_editor.draw_dock_switch`); 따로 있던 `MAYAKIT_PT_dock_tabs` 제거.
- 메뉴 줄은 왼쪽 정렬 (기본 정렬은 칸을 늘려 「Chann...」 로 잘림).
- Range Slider 막대 = 재생 범위 토글 (왼쪽 손잡이 아이콘) + 범위를 보여 주고 누르면 타임라인을 그 범위에 맞추는 버튼
  (토글 하나로 그리면 켜졌을 때 파랗게 칠해짐).
- Layer Editor 는 레이어가 없어도 빈 목록 칸을 그림 (Maya 처럼). 목록 바탕색은 테마의 상자 색 (#444) 이라 Maya #2a2a2a 와 다름 —
  상자 색을 바꾸면 다른 상자도 바뀌어 남김.

## 한 것
- `ui/chrome.py` (새): 메뉴 줄·회색 항목·여러 줄 라벨.
- Channel Box (`ui/channel_box.py`): 머리·톱니 없음, 메뉴 줄 Channels / Edit / Object / Show (새 메뉴 Edit·Object·Show,
  `maya_kit.cb_make_lead`), 이름·SHAPES·INPUTS 상자 없음, 빈 선택 Maya 문구 세 줄.
- Layer Editor: 머리 없음, Display / Anim 탭 (`WindowManager.maya_kit_le_tab`), 메뉴 줄 Layers / Options / Help, 아이콘 오른쪽 정렬,
  빈 목록 칸, Anim 탭 = 안내 + NLA 편집기.
- Outliner (`ui/maya_outliner.py`, 새): Maya 식 Outliner 의 머리 = Display / Show / Help + 검색 칸 (`OUTLINER_HT_header.draw` 교체),
  눈 열 숨김 (템플릿, Windows > Outliner).
- Time Slider (`ui/time_slider.py`): 템플릿 타임라인 사이드바 (300 px) = 현재 프레임 칸 + 재생 버튼 8 개
  (`MAYAKIT_PT_time_slider`); 헤더 = Range Slider (시작·재생 시작·막대·재생 끝·끝 | 자동 키 | No Character Set | No Anim Layer |
  fps | 반복 (회색) | 소리 | 애니메이션 설정 메뉴 = Playback/Keying/View/Marker). `TIME_MT_editor_menus.draw_collapsible` 덮어씀.
- 생성기: 타임라인 사이드바 표시 + 폭 드래그 (`drag_region_edge`), Outliner 눈 열 끔.
- 테스트: 새 `test_step50_chrome` (7, 기록용 가짜 layout 으로 메뉴 줄 라벨·빈 문구·Range 순서), `gui_step50_chrome`;
  test_step49 (타임라인 사이드바), gui_step38 (TX 칸 위치), `tests/kit.py` 스냅숏 (Outliner 머리, 타임라인 메뉴), look_data 지점 재선택.

## 검증
- 헤드리스 **392/392** (step 49: 385). `test_enable_disable` 누수 0.
- GUI 전체 **309/309** (`--ui-scale 0.8`); 1.25 전체 307/309 → 실패 2 (gui_step38 의 고정 픽셀 위치) 고친 뒤 step38·6·11·20·49·50 다시
  모두 통과.
- look_compare: 메뉴 줄 텍스트·순서 = Maya (헤드리스 단언), density CB 행 간격 **16.0 vs 16.2** (±1 ✓), 픽셀 ΔE>5 **7 → 5**/28:
  cb_bg 0.0, cb_field 0.0 (전 8.1), time_field 0.0, range_slider_field 0.0 (전 8.1), outliner 머리 0.0 / 검색 칸 0.0 / 목록 1.0,
  Range 줄 바탕 0.0. 남은 ✗: layer_editor_list 8.4 (상자 색), cb_shape_row 4.3 (Maya 행 바탕 #373737).
- dogfood 47/47 (콘솔 오류 0), release_check PASS (스크린샷 7장 재생성).
- 스크린샷 직접 확인: crop_channel_box / crop_outliner / crop_time_slider / crop_range_slider, gui_step50_chrome.

## 남은 것
- Outliner: Maya 의 회색 카메라 행 (persp/top/front/side) 과 defaultLightSet/defaultObjectSet — Blender 장면에 그런 오브젝트가 없음
  (C 목록, 가짜 오브젝트는 만들지 않음, delegated). 아이콘은 Blender 것.
- Layer Editor 목록 바탕 #444 (Maya #2a2a2a), SHAPES 행 바탕. Maya CB 오른쪽 위 작은 아이콘 3 개 (매니퓰레이터 모드 등) 없음.
- Range Slider 막대는 끌어서 범위를 바꿀 수 없음 (Blender 위젯 없음). 반복 모드 (once/oscillate) 없음.
- 타임라인 왼쪽 편집기 종류 아이콘은 Blender 헤더가 그림 (남음).
- 수동 확인: `docs/manual_checks.md` 「Step 50」.
