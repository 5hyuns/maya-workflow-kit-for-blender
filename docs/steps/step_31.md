# Step 31 — Outliner 레이아웃 · 홀드 메뉴 표시 다듬기

## 계획 (delegated)

근거와 출발점: 재점검 2차 화면 관찰 (docs/steps/step_23.md:27), PLAN 10번 "Layout polish" (docs/PLAN.md:100-101, :165).

1. **왼쪽 Outliner**: Maya Outliner = DAG만 표시. 셰이프 없음, 월드부터 나열, 폭 260 px
   (research/maya/ui_layout.md:121, :259-262; `initOutliner.mel:84-122`).
   - 지금은 0.16 비율(약 210 px)인데, Blender 행에는 컬렉션 두 단계 들여쓰기와 눈·카메라 아이콘이 붙어 "pCube"처럼 이름이 잘린다.
   - `tools/make_startup.py`: `OUTLINER_FACTOR` 0.2 (약 264 px).
   - `use_filter_collection = False`: 컬렉션 행을 숨기고 오브젝트만 계층으로 보여 준다. 컬렉션은 오른쪽 Layer Editor의 디스플레이 레이어다.
   - `show_restrict_column_render = False`: Maya Outliner에는 행별 토글이 없다. 눈(숨김)은 남김.
   - 재생성 후 release_check 스크린샷도 다시 만든다.
2. **4분할 → 단일 헤더 이름**: Space 탭으로 쿼드에서 단일로 돌아올 때 커서 아래 뷰를 복사한다(step 4).
   - 회전을 복사하면 축 뷰 플래그가 빠져서 "Top Orthographic"이 "User Orthographic"이 된다(GUI 실측).
   - `RegionView3D.is_orthographic_side_view`를 같이 기록해 두고 다시 켠다. 4.5에서 쓰기 가능함을 실측했다.
   - Maya는 패널의 카메라(top/front/side)를 그대로 유지한다.
3. **홀드 메뉴 토글 표시**:
   - Maya 엔진의 체크 상자는 step 26에 있었다. 그런데 켜짐 채움색(선택 파랑 0.32/0.52/0.65)이 빈 상자와 거의 구분되지 않았다(스크린샷).
   - 켜짐 색을 밝은 파랑으로 바꾸고 채움을 키운다.
   - Blender 파이 폴백(환경설정 "Blender Pies")에는 상태 표시가 없었다. `marking.draw_entry`가 토글에 CHECKBOX 아이콘을 붙인다.
4. **타임라인 현재 프레임 상자**: Blender 스크럽 영역의 프레임 상자·눈금 숫자는 C(`ED_time_scrub_draw`)가 그린다.
   Python으로 숨기거나 옮길 방법이 없다(space_time.py 표시 옵션 확인). → 이번에는 기록만 한다(남은 것).

## 한 것

- `tools/make_startup.py`: `OUTLINER_FACTOR = 0.2`, 왼쪽 Outliner `use_filter_collection = False`,
  `show_restrict_column_render = False`. `startup.blend` 재생성.
- `operators/view.py` `toggle_quad_view`: 쿼드를 떠날 때 커서 아래 뷰가 축 뷰면 단일 뷰에서도 `is_orthographic_side_view = True`.
- `marking/draw.py`: 체크 켜짐 색 `CHECK` (0.45, 0.72, 0.95), 채움 여백 2→1 px.
- `marking/__init__.py` `draw_entry`: 토글 항목에 `CHECKBOX_HLT` / `CHECKBOX_DEHLT` 아이콘(파이·목록 하위 메뉴).
- `docs/screenshots/` 재생성 (`tools/release_check.py`).
- 테스트: `tests/test_step31_layout.py` (2), `tests/gui/gui_step31_layout.py` (7 체크, 스크린샷 6장).

## 검증

- `python tools/make_startup.py` 재생성, `python tools/release_check.py`: validate·설치·활성 PASS, 체크 8/8, 스크린샷 7장 재생성.
  `01_layout.png` / `07_outliner_rigging_shelf.png` 직접 확인: 왼쪽 Outliner 에 group1 / pCube1 이름 전체, 컬렉션 행 없음.
- GUI (`tmp/shots31/`) 직접 확인: Outliner 263 px, 쿼드 Top → 단일 = "Top Orthographic", W 홀드 메뉴 체크 (켜짐 밝은 파랑 / 꺼짐 빈 상자),
  파이 폴백 체크 아이콘, 프레임 8 타임라인 ("8" 상자가 "10" 을 반쯤 가림 — 그대로).
- 헤드리스 `python tests/run.py`: **281/281** (30 파일). GUI `python tests/gui/run.py`: **239/239** (24 파일). dogfood **47/47**, 콘솔 오류 0.

## 남은 것

- 타임라인 현재 프레임 상자가 옆 눈금 숫자를 가림: Blender C 그리기 (`ED_time_scrub_draw`), Python 에서 바꿀 방법 없음 (delegated:
  그대로 두고 manual_checks 에 기록). Maya 처럼 현재 프레임 숫자를 별도 필드에 보이는 것은 Range Slider 헤더의 현재 프레임 필드로 이미 있음.
- 왼쪽 Outliner 는 Blender Outliner 그대로 (드래그 재부모·세트·키보드 이동 등 Maya Outliner 동작은 사이드바 Outliner 탭 쪽, step 11).
- 사용자가 이미 설치한 MayaKit 템플릿은 "Reinstall" 해야 새 레이아웃이 적용됨.
