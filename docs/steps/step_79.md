# Step 79 — 3D Cut and Sew UV Tool

재점검 4차 backlog 8 (PLAN 「Left out of steps 54–67」 최고 점수 20, research/maya/workflows/uv.md:111 4b).

## 근거

- `UV > 3D Cut and Sew UV Tool` / UV Toolkit > Cut and Sew > 3D Cut and Sew Tool (rtc `SetCutSewUVTool`,
  defaultRunTimeCommands.mel:21871): 컨텍스트 `superCutUVContext`, 엣지 선택 모드로 바뀜, 뷰포트 아래 툴 이름 [O]
  research/maya/workflows/uv.md:30-32 (uv_02 스크린샷).
- 툴 안에서 LMB 드래그 = 엣지를 따라 자르기, Ctrl+드래그 = 꿰매기 [K] (uv.md:33). 툴 키 `x` CutUVs3D · `s` SewUVs3D ·
  `d` Unfold + Layout (현재 타일) · `Shift+d` 빈 타일에 [O] hotkeySetup.mel:539-542 (`docs/keymap_mapping.md:345-348`).
- 툴 마킹 메뉴 `polyCutUVOptionsPopup` (polyCutUVOptionsPopup.mel:179-210): NE Unfold and Layout = `UnfoldUV` + `LayoutUV`,
  E Cut UVs = `CutUVs` (+ `CreateUVShellAlongBorder`), W Sew UVs = `SewUVs`, S Exit Tool, Show Texture Borders 옵션
  [O] research/maya/marking_menus.json.
- Maya Cut 은 그 자리에서 UV 를 끊고 셸 경계가 바로 굵게 보인다 [K] (uv.md:39).
- kit 재료 (step 66): `operators/uv_tools.cut` / `sew` (bmesh; Blender 섬 계산이 솔기를 무시해서 작은 쪽을 2e-4 밀어 진짜로 나눔),
  `unfold`, `layout`, `islands()`; 프리셀렉트 기즈모 `operators/preselect.pick` (step 74, 엣지 모드에서 가려진 엣지 제외).

## 계획

1. **툴** = `bpy.utils.register_tool` WorkSpaceTool `maya_kit.cut_sew_tool` (`ui/mesh_tools.py` 방식, EDIT_MESH,
   `KEYMAP_FALLBACK`): 키맵
   - LMB PRESS → `maya_kit.cut_sew_stroke` (자르기), Ctrl+LMB → (꿰매기), Shift+LMB → (엣지 선택에 더하기, x/s/d 용).
   - X / S / D = `maya_kit.uv_cut` / `maya_kit.uv_sew` / `maya_kit.uv_unfold_layout` (툴 키맵이라 툴이 켜져 있을 때만 —
     Mesh 의 X 삭제 · S 스케일 · D 피벗보다 먼저).
   - Shift+D (빈 타일) 는 Blender 에 UDIM 타일 배치 개념이 없어 안 함 (delegated, 대응표 메모).
2. **스트로크 모달** `maya_kit.cut_sew_stroke`: 누른 곳의 엣지를 `preselect.pick` (엣지 모드 규칙: 가려진 엣지 제외, 반경 16 px)
   으로 찾는다. 없으면 PASS_THROUGH (Blender 선택 폴백). 드래그 중에는 이전 마우스와 지금 사이를 4 px 간격으로 나눠
   각 점의 엣지를 모은다 (빠른 드래그에도 빠지지 않게). 모은 엣지는 노란 선으로 그린다 (POST_VIEW). 놓으면 자르기 / 꿰매기
   (`uv_tools.cut` / `sew`) 를 오브젝트별로 한 번 — 언두 한 단계. Esc / RMB = 취소.
3. **진입** `maya_kit.cut_sew_tool_set`: 활성 메시 → 편집 모드, 엣지 선택 모드 (Maya 컨텍스트가 엣지 모드로 바꿈), 툴 켜기
   (3D View 를 찾아서; UV Editor 마킹 메뉴에서 불러도). 연결: 메뉴 `UV/3D Cut and Sew UV Tool`, 셸프 `SetCutSewUVTool`,
   UV Toolkit 버튼, UV / UV Shell 마킹 메뉴 NW, 그리고 회색 안내 (`notices`) 제거.
4. **보이기**: 툴이 켜져 있는 동안 UV 셸 경계 (섬이 갈리는 엣지 = Maya Texture Borders) 를 굵은 선으로 그린다
   (POST_VIEW, 메시 상태마다 캐시, 프리셀렉트와 같은 depsgraph 무효화). 프리셀렉트 하이라이트는 이 툴에서도 켬
   (`preselect.SELECT_TOOLS` 에 추가) → 누르기 전에 어느 엣지가 잘릴지 빨갛게 보임.
5. `d` = Unfold + Layout (`cutUVToolDoUnfoldLayoutUVs` = UnfoldUV + LayoutUV): 새 연산 `maya_kit.uv_unfold_layout`
   (기존 unfold → layout).
6. 대응표: `polyCutUV:CutUVs3D` / `SewUVs3D` / `UnfoldPackUVs3DInCurrentTile` → KIT, Shift+D 메모.

판단 (delegated): 드래그 중 바로 자르지 않고 놓을 때 한 번 (언두 한 단계, 그리는 선으로 미리 보임); 툴 마킹 메뉴와
Steady Stroke, Symmetry, 더블클릭 루프 자르기는 다음으로.

## 검증 계획

- 헤드리스: 스트로크 엣지 모으기 (점 나누기 순수 함수), 큐브 UV (Smart/Unwrap 한 섬) 에 엣지 고리 자르기 → `islands()` 2,
  꿰매기 → 1; 셸 경계 계산 (`border_edges`), 툴 등록·키맵, 메뉴/셸프/마킹 메뉴 연결, `uv_unfold_layout`.
- GUI: 메뉴로 툴 진입 → 엣지 모드 + 툴; 큐브 윗면 네 엣지를 드래그 → 섬 개수 증가; Ctrl+드래그 → 다시 하나; x / s 키;
  스크린샷 (경계 선 + 하이라이트).
- 전체 테스트, dogfood, manual_checks.

## 한 것

- `operators/cut_sew.py`: `maya_kit.cut_sew_stroke` (모달: 누른 엣지 → 드래그 4 px 표본마다 `preselect.pick` → 놓으면 Cut / Sew /
  Select, 언두 한 단계, Esc / RMB 취소), `maya_kit.uv_unfold_layout` (d), `maya_kit.cut_sew_tool_set` (편집 모드 + 엣지 모드 + 툴,
  3D View 를 찾아서), POST_VIEW 그리기 (셸 경계 흰 굵은 선 = `border_edges`, 스트로크 노란 선), 경계 캐시 depsgraph 무효화.
  순수 함수 `stroke_points`, `near_end`, `border_edges`, `apply`.
- 계획에 없던 것 (GUI 에서 찾음): 모서리를 돌 때 옆 세로 엣지까지 잡혀서, 엣지 끝 6 px 안의 드래그 표본은 세지 않음 (첫 누름은 셈).
  UV Sync 꺼짐에서 `uv_cut` / `uv_sew` 가 UV 선택만 봐서 툴의 x / s 가 안 먹음 → `mesh_select` 속성 (툴 키맵·툴 설정 버튼이 True).
- 툴 `maya_kit.cut_sew_tool` (`ui/mesh_tools.py`, 키 LMB / Ctrl / Shift, X / S / D), 프리셀렉트 `SELECT_TOOLS` 에 추가.
- 연결: 메뉴 `UV/3D Cut and Sew UV Tool`, 셸프 `SetCutSewUVTool`, UV Toolkit 버튼, UV / UV Shell 마킹 메뉴 NW; 「Blender 에 없음」 안내 두 개 제거
  (test_step66 기대 갱신).
- 대응표 polyCutUV x / s / d → 구현 (툴 키맵은 addon 키컨피그라 생성기 검사 없음, 헤드리스 테스트가 확인), Shift+D → 해당 없음 (UDIM 빈 타일).
  구현 122 → 125.
- manual_checks 4 항목, PLAN 재점검 4차 8 = 완료 (backlog 72–79 끝), CLAUDE.md 한 줄.

## 검증

- 헤드리스 `tests/test_step79_cut_sew.py` 7/7: stroke_points, near_end, 큐브 윗면 네 엣지 Cut → `islands()` 1 → 2 (경계 엣지 늘어남), Sew → 1 + 솔기 없음,
  Select 는 선택만, 툴·키맵 (`keyconfigs.addon`), 진입점 4 곳, Unfold + Layout 후 0-1 안 2 셸. step 66 10/10.
- GUI `tests/gui/gui_step79_cut_sew.py` 6/6: 메뉴 → 편집 + 엣지 모드 + 툴, 윗면 둘레 드래그 → 셸 1 → 2 이고 솔기 = 윗면 4 엣지만, Ctrl+드래그 → 1 + 솔기 없음,
  Shift+드래그 → 4 엣지 선택 (셸 그대로), x → 2. 스크린샷 (경계 흰 선, 솔기 빨강, 툴바 아이콘) 확인.
- 전체: 헤드리스 634/634, GUI (기본 배율) 555/555, dogfood 47/47 (콘솔 오류 0).

## 남은 것

- 툴 마킹 메뉴 (`polyCutUVOptionsPopup`: Steady Stroke, Symmetry, Show checker map / Texture Borders / Shell Coloring 토글, Exit Tool) 없음.
- 더블클릭 엣지 루프 자르기 (Maya [K]) 없음 — `event_simulate` 가 DOUBLE_CLICK 을 못 보내 GUI 로 확인도 못 함.
- 드래그 중 바로 자르지 않고 놓을 때 한 번 (delegated). Maya 의 셸 색칠·체커 표시는 Blender UV Editor 쪽 기능으로 대신.
- 재점검 4차 backlog (step 72–79) 끝. 다음은 사용자 결정: 배포 (decision 11) 또는 재점검 5차 / PLAN 「Left out」 나머지.
