# Step 51 — 메뉴·셸프·Status Line 모양 (옵션 박스·메뉴 위치·컬러 셸프 아이콘)

backlog 10 (`docs/PLAN.md` 「Maya 동일화 계획」). 근거: compare/12_create_menu.png, `research/maya/screens/19_shelf_crop.png`,
`18_status_line_crop.png`, `research/maya/colors.json` (widget_size_histogram QPushButton 35x34 ×43), `research/maya/menus.json`
(항목의 `optionBox`: 621 개), `research/maya/ui_layout.md:219-222` (셸프 높이 64, 탭 줄 + 아이콘 줄, 아이콘만), `shelves.md`.

## 계획

### 실측 (계획 전)
- kit 의 Maya 메뉴는 이미 메뉴바 버튼 아래로 열림 (Blender 머리 풀다운): compare/12 의 kit Create 메뉴 위 끝 y 23, 메뉴바 아래 끝 26.
  메뉴 항목 높이 19.4 px (density.md). → 이번엔 측정 행만 추가.
- 32 px 아이콘: Blender 버튼은 `scale` 을 키워도 미리보기 (`bpy.utils.previews`) 아이콘을 16 px 로 그림 (실측: 이미지 편집기 사이드바
  프로토타입). 사이드바 폭은 1000 px 에서 멈춤 (실측) → Maya 셸프 (아이콘 33 개 이상, 1596 px) 가 안 들어감.
- 툴바식 삼각형 아이콘 (`bpy.app.icons.new_triangles`) 은 버튼 크기를 따라 커지지만 셸프 줄은 헤더 (26 px) 라 32 px 가 안 됨.

### 결정 (delegated)
1. **셸프 = 탭 줄 + 아이콘 줄, 높이 64** (Maya `initShelf.mel:290-306`): 셸프 영역 (`.MayaKitShelf`) 의 헤더 = Maya 탭 줄 (셸프마다
   납작한 탭, 고른 탭 강조, 맨 왼쪽 톱니 = 셸프 설정), WINDOW 영역 (38 px) = kit 이 GPU 로 그리는 아이콘 줄. 클릭 = 명령,
   더블클릭 = 옵션 (Adjust Last Operation), Ctrl+클릭 = 옵션으로 실행 (지금 셸프 버튼과 같은 규칙, `MAYAKIT_OT_shelf_button`).
   마우스를 올리면 칸 강조 + Help Line 에 버튼 이름 (Maya Help Line 이 툴팁을 보여 주는 것처럼). 입력은 "Image" 키맵 맨 앞
   (`shelf_click` / `shelf_hover`, 셸프 줄 밖에서는 PASS_THROUGH). 결정 6 의 "SVG→PNG, previews" 대신 (16 px 로만 그려짐) 이 방식.
2. **kit 제작 아이콘** (결정 6: Maya 아이콘 금지, 의미만 참고): `ui/shelf_icons.py` 가 numpy 로 32 px (×2 슈퍼샘플) RGBA 를 그림 —
   기본 도형 (큐브·구·원기둥·원뿔·토러스·평면·원판), 도구 기호 (화살표·칼·격자·사슬·전구·카메라·관절·다이아몬드 키 등), 셸프별 색;
   기호가 없는 버튼은 셸프 색 사각형 + 5x7 글자 두 개. 파일 없음 (등록 때 만들고 처음 그릴 때 GPU 텍스처). 사용자 셸프 버튼도 글자 아이콘.
3. **옵션 박스**: `tools/gen_menu_data.py` 가 `OPTION_BOXES` (옵션 박스가 있는 Maya 항목의 라벨 경로) 를 만들고, 메뉴는 그 항목 오른쪽에
   □ 버튼 (`maya_kit.menu_option_box` → `marking.modal.run_action(option=True)` = 실행 후 Adjust Last Operation, 마킹 메뉴 옵션 박스와 같음).
   대응 없는 항목은 □ 도 회색.
4. Status Line: 그룹·구분은 이미 있음 — 이번 단계는 셸프·메뉴만 (남은 것: kit 제작 컬러 아이콘·접기 손잡이).
5. 검증: 헤드리스 = 옵션 박스 수 (menus.json → 변환 후 남은 옵션 박스 항목 수 = kit 이 그리는 □ 수), 아이콘 모두 만들어짐
   (모양·알파·서로 다름), 키맵 항목·교체 복원; look_compare = 셸프 높이 64±2, 아이콘 32±2, 메뉴 항목 20±1, 메뉴 위 끝 = 메뉴바 아래 ±4;
   GUI = 아이콘 클릭으로 Polygon Cube 생성, 더블클릭 옵션, 탭 바꾸기, 스크린샷.

### 실측 (구현 중)
- 옵션 박스를 같은 줄 두 번째 버튼 (□) 으로 그리면 Blender 메뉴가 계단처럼 깨짐 (`row`, `split`, 두 열 모두 실측) → 결정 3 수정
  (delegated): 옵션 박스 항목 = `operator_menu_hold(maya_kit.menu_item)` 한 버튼 + 창 아이콘. 클릭 = 명령, 길게 누르기 = 한 항목
  메뉴 「Option Box」 (`MAYAKIT_MT_option_box` → `maya_kit.menu_option_box` = 실행 후 Adjust Last Operation). 하위 메뉴·대응 없는
  항목은 아이콘만.
- 이미지 편집기 WINDOW 에 Python 기즈모가 그린 것은 보이지 않음 (실측) → 아이콘은 `SpaceImageEditor` POST_PIXEL 핸들러가 그리고
  기즈모 풀 (`MAYAKIT_GGT_shelf`, 64 개) 은 고르기·툴팁·실행만. 텍스처 아이콘은 sRGB → 선형으로 올려야 Maya 색 (테마 단색 사각형은
  그대로 sRGB 값: 선형으로 바꾸면 #444444 → #161616, 실측).
- 셸프 줄 탭과 아이콘 줄은 같은 이미지 편집기 머리 색 (#444444) 을 씀. Maya 탭 줄은 #373737 → 머리 POST_PIXEL 에 검정 반투명
  (`shelf.TAB_DIM` = 1 − 0x37/0x44) 을 덮음: 탭 줄·안 고른 탭 #373737, 고른 탭 (wcol_tool) #4b4b4b, 글자도 19 % 어두워짐.
- 1.25 배율로 템플릿을 연 뒤 배율을 0.8 로 바꾸면 Status Line (머리만 있는 영역) 이 줄며 픽셀이 가운데 줄로 감; `toolbox.fit_columns`
  가 셸프 줄을 64 px × 배율로 되돌리지만 `screen.area_move` 는 마우스가 영역 위에 있으면 poll False → 마우스가 경계를 지날 때 맞춰짐.
  look_shots 는 템플릿을 연 뒤 마우스를 셸프 줄 아래 경계에 둠.

## 한 것
- `tools/gen_menu_data.py` → `ui/menu_data.OPTION_BOXES` (Maya `optionBox` 항목의 라벨 경로, 변환 후 494). `ui/menu_sets.py`: 옵션
  박스 항목 = 길게 누르기 버튼 + 창 아이콘, `MAYAKIT_MT_option_box`, `maya_kit.menu_option_box`.
- `ui/shelf_icons.py` (새): numpy 로 그린 kit 아이콘 (32 px, ×2 슈퍼샘플) — 기본 도형·도구 기호 키워드 표, 셸프별 색, 기호 없는 버튼 =
  셸프 색 + 5x7 글자 두 개, 처음 그릴 때 GPU 텍스처 (파일 없음, 결정 6).
- `ui/shelf.py`: `.MayaKitShelf` 영역 = 머리 (톱니 = 셸프 설정 + 셸프마다 납작한 탭, 고른 탭 강조, 탭 줄 어둡게) + WINDOW 아이콘 줄
  (`draw_row`, 35 px 간격 32 px 아이콘, 마우스 칸 강조), `MAYAKIT_GT_shelf_icon` / `MAYAKIT_GGT_shelf` / `maya_kit.shelf_slot`
  (클릭 = 명령, 0.35 s 안 두 번째 클릭·Ctrl+클릭 = 옵션).
- `tools/make_startup.py`: `SHELF_PX = 64`, 셸프 분할 뒤 `strip` 다시 찾기 (전엔 Status Line 마스크가 빠졌음); 템플릿 재생성.
  `ui/toolbox.fit_columns` 가 셸프 줄 높이도 맞춤.
- look_compare: density 에 메뉴 위 끝 − 메뉴바 아래, 셸프 높이, 셸프 아이콘; `look_data` 셸프 사각형·크롭 앵커 = `shelf` (영역 전체),
  셸프 탭 3 지점 새로 (전엔 「탭 없음」), 아이콘 줄 지점 = `shelf.WINDOW`; `look_shots` 셸프 높이 맞춤 + 단언.
- 테스트: 새 `test_step51_shelf_menus` (6), `gui_step51_shelf_menus`; test_step7/34 가짜 layout 갱신.

## 검증
- 헤드리스 **398/398** (step 50: 392). `test_enable_disable` 누수 0 (머리·WINDOW 핸들러 둘 다 제거).
- look_compare: density **6/6** (메뉴바 26, 항목 19.4, CB 16.0, 메뉴 위 끝 −3 (Maya 2), 셸프 **64** (Maya 64), 아이콘 **32**);
  rects 4 → **5/12** (Shelf [0, 63, 1600, 64] vs Maya [2, 62, 1596, 64] ✓); 픽셀 ΔE>5 5/28 → **5/31**, kit 에 없음 10 → 7:
  shelf_tab_bar_bg 0.0, shelf_tab_inactive 0.0, shelf_tab_active 2.4, shelf_icon_row_bg 0.7.
- GUI 전체 **314/314** (`--ui-scale 0.8`), **313/313** (1.25; 파일 36 개). gui_step51: 아이콘 클릭으로 Polygon Sphere 생성, 두 번째
  클릭 = 옵션, 탭 바꾸기, 메뉴바에서 연 Create 메뉴 스크린샷.
- release_check PASS (스크린샷 7 장 재생성), dogfood **47/47** (콘솔 오류 0).

## 남은 것
- 1.25 등 템플릿 저장 배율과 다른 배율에서 셸프 줄은 마우스가 그 아래 경계를 지날 때까지 낮음 (gui_step51 1.25: 56 px, 아이콘 20;
  release 스크린샷 `docs/screenshots/01_layout.png` 도 그 상태) — `screen.area_move` poll 이 마우스가 영역 위면 False (step 49 툴박스
  열과 같은 한계).
- Status Line: kit 제작 컬러 아이콘·그룹 접기 손잡이 (Maya 18_status_line_crop) 없음 — Blender 아이콘 그대로.
- 메뉴: Maya 끊어내기 (tear-off) 선 없음 (Blender 메뉴는 떼어 낼 수 없음); 옵션 박스는 오른쪽 □ 열이 아니라 왼쪽 아이콘 + 길게 누르기.
  고른 탭 #4b4b4b (Maya #444444, ΔE 2.4), 탭 글자도 어둡게 덮임.
- 셸프 아이콘 끌어 옮기기·가운데 버튼 끌어 셸프에 넣기 (Maya) 없음; 셸프가 줄보다 길면 Maya 의 위/아래 화살표 대신 잘림.
- 수동 확인: `docs/manual_checks.md` 「Step 51」.
