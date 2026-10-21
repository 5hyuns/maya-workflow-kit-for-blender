# Step 134 — 레인 SEL: Maya 선택 색 (오브젝트 · 컴포넌트 · Outliner 행)

`step_134.md` 레인 SEL, `step_133_ui.md` 발견 #1 (점수 20). 결정 13: 킷 고정 색은 허용, 테마 · 환경설정 쓰기는 금지.

## 계획

### 근거 (Maya 2022 실측)

- `research/maya/colors.json` viewport: lead #43ffa3 (displayColor 19), 다른 선택 (active) #ffffff (16), hilite #64dcff (18),
  hiliteComponent #c800c8 (9), polyVertex #ffff00 (17), polyEdge / polyFace #e4ac79 (21).
- 스크린샷 픽셀 (`research/maya/screens/`, Maya UI 배율 1.0):
  - `08_verts_selected.png`: 편집 중 오브젝트의 모든 (보이는) 엣지 1 px #64dcff, 선택 안 된 정점 3×3 px #c800c8, 선택 정점
    **4×4 px #fdff88** (화면 값; colors.json 의 #ffff00 이 아니라 이 값을 쓴다). 가려진 정점 · 엣지는 셰이딩 모드에서 안 그림.
  - `09_edges_selected.png`: 선택 엣지 1 px #e3ac79, 나머지 엣지 #64dcff.
  - `07_faces_selected.png`: 선택 면 = **2 px 간격 점묘 (2×2 중 한 픽셀) #e3ac79** (면 채움 없음), 엣지 #64dcff.
  - `02_cube_selected_move.png` / `04_wire_selected_lead.png`: 오브젝트 모드 리드 = 모든 엣지 #43ffa3, 다른 선택 = #ffffff, 외곽선 없음.

### 오브젝트 모드 (`ui/selection_wire.py`)

- step 130 이후 와이어 색이 사용자 테마 `object_active` / `object_selected` (Blender 기본 = 주황) 였다 → **킷 고정 Maya 색**
  `LEAD = #43ffa3`, `OTHER = #ffffff` (sRGB → scene linear 변환은 그대로). 테마는 더 읽지 않는다.
- Blender 가 여전히 그리는 것: 선택 외곽선 (`View3DOverlay.show_outline_selected`, 테마 색), 원점 점. Maya 레이아웃 뷰는 step 47 부터
  외곽선 끔 (`tools/make_startup.py:338`, startup.blend 에 저장, step 130 `switch.enter_layout` 이 그 워크스페이스를 붙임) — 그대로.
  **사용자 파일의 뷰 (Maya 레이아웃 밖) 의 외곽선은 건드리지 않는다** (delegated: 화면 데이터라 쓰기는 가능하지만 사용자가 만든 뷰를
  킷이 몰래 바꾸는 것은 step 115 「no surprises」 에 어긋남; Maya 의 Show > Selection Highlighting 메뉴로 끌 수 있다). 와이어는 외곽선
  안쪽 엣지 위에 그려지므로 리드 = 초록 와이어 + 바깥 주황 테두리.

### 컴포넌트 모드 (새 `ui/component_colors.py`)

- POST_VIEW 핸들러 하나 (Maya 모드에서만 등록되는 `ui` 패키지). Edit Mesh 의 각 오브젝트 (`objects_in_mode_unique_data`):
  1. 숨기지 않은 모든 엣지 #64dcff (Maya hilite),
  2. 정점 선택 모드: 선택 안 된 정점 3 px #c800c8, 선택 정점 4 px #fdff88 (× UI 배율, 정사각 점),
  3. 엣지 선택 모드: 선택 엣지 #e3ac79,
  4. 면 선택 모드: 선택 면 점묘 #e3ac79 (사용자 셰이더, `gl_FragCoord` 2×2 중 하나만 남김).
  Blender 의 편집 메시 그리기 (테마 색) 는 그 아래에 남는다 — 같은 위치에 덮어 그림. 깊이: 셰이딩 모드는 깊이 테스트 + 투영 행렬
  깊이 바이어스 (soft_overlay 와 같은 방식), X-ray 는 깊이 테스트 없음.
- 데이터 읽기 (프로브 `tmp/p134/probe1-3.py`, 101 124 정점 격자): 편집 모드 평가 메시 `ev.data` 는 정점 0 (BMesh 래퍼),
  `ob.to_mesh()` (원본) 은 편집 전 데이터 (낡음), **`ev.to_mesh()` (평가된 오브젝트) = 현재 BMesh + `.select_vert/edge/poly` 4 ms**
  (첫 호출 14 ms), bmesh 파이썬 루프 = 좌표 256 ms + 엣지 141 ms + 선택 36 ms. 그래서:
  - 편집 모드에서 보이는 모디파이어 (`show_viewport and show_in_editmode`) 가 없으면 `ev.to_mesh()` (빠른 길).
  - 있으면 (예: Smooth Preview 3 의 Subsurf) 평가 메시는 케이지가 아니므로 bmesh 루프로 케이지를 읽되, **정점 50 000 개 이하만**
    (그 이상은 킷 색을 그리지 않고 Blender 그리기에 맡김 — delegated, 한 번 읽기 ~0.2 s 가 드래그 매 프레임에 생기는 것을 피함).
  - 캐시: 오브젝트별 (포인터 + 메시 포인터) 배열 + GPU 배치, depsgraph_update_post 가 그 오브젝트 / 메시 이름을 「더러움」 으로 표시하면
    다음 그리기에서 다시 읽음 (soft_overlay 와 같은 구조). 선택 모드가 바뀌면 배치만 다시.
- 순수 함수 (`layers(...)`, numpy, bpy 없음) 가 숨김 · 선택 모드에 따라 그릴 배열을 고른다 → 헤드리스 테스트.
- 환경설정 `maya_component_colors` (기본 켬 = Maya; 끄면 Blender 그리기만). 킷 환경설정이라 Blender 환경설정 쓰기 아님.
- Soft select 켬 (`soft_overlay`) 이면 그 거짓 색이 위에 그려진다 (등록 순서 뒤). 프리셀렉트 (operators/preselect.py) 는 기즈모라 맨 위.

### Outliner 선택 행

- Blender C Outliner 의 선택 행 · 글자는 테마 (`outliner.selected_highlight` / `active_highlight`, 글자 주황) 로 C 가 그린다.
  POST_PIXEL 은 모든 것 위에 그려지므로 행을 칠하면 아이콘 · 글자를 덮는다; Python 은 C 아이콘을 다시 그릴 수 없다. 프레임버퍼를
  읽어 색을 바꿔 그리는 방법은 행 배경이 줄무늬 위 반투명 하이라이트라 행마다 색이 다르고, 사용자 테마마다 달라 신뢰할 수 없다.
  → 시도 결과를 「한 것」 에 적고, 믿을 수 없으면 건너뜀 (delegated).

### 검증

- 헤드리스 `tests/test_step134_selection.py`: 고정 색 값 (hex → linear), 테마를 바꿔도 와이어 색 불변, `layers()` (숨김 제외,
  모드별 배열, 면 삼각형), 빠른 길 / bmesh 길 선택 규칙, 50 000 제한, 등록 / 해제.
- GUI `tests/gui/gui_step134_selection.py`: 리드 + 다른 선택 큐브 (와이어 픽셀 초록 / 흰색), 정점 · 엣지 · 면 선택 (픽셀 색) 샷,
  10 만 정점 편집 메시 프레임 시간.
- Maya 쌍과 나란히 (`tmp/sel134/`), UI 배율 1.0 / 1.25.

## 한 것

- `ui/selection_wire.py`: 와이어 색 = 킷 고정 `LEAD` #43ffa3 / `OTHER` #ffffff (`wire_colors()`), 테마 읽기 없앰.
- `ui/component_colors.py` (새, `ui/__init__` 에서 selection_wire 다음 등록): 위 계획대로. 실제 GUI 에서 바꾼 것:
  - **정점이 Blender 정점 아래에 묻힘** (첫 샷: 검정 / 주황 점 둘레에 노랑 테두리만) — Blender 편집 정점은 표면보다 꽤 앞에 깊이를
    쓴다. 정점만 바이어스 `POINT_BIAS` 0.003 (엣지 · 면 0.0005) → 보라 / 노랑이 위에 그려짐.
  - **엣지 1 px 은 Blender 엣지 사이에 묻힘**: Maya 레이아웃 큐브 (`allset.create`) 는 엣지가 sharp 라 Blender 가 sharp 색 (청록)
    으로 ~2 px 안티에일리어스 선을 그리고, 선택 엣지 주황이 그 가운데 1 px 로만 보였다. → 엣지는 `POLYLINE_UNIFORM_COLOR`
    `LINE_PX` 2 × UI 배율 (Maya 는 1 px; Blender 선을 덮는 쪽을 택함, delegated). 정점은 `UNIFORM_COLOR` POINTS (정사각, Maya 와 같음),
    면 점묘는 사용자 셰이더 (`gl_FragCoord` 2×2 중 하나, 색은 scene linear 로 변환).
  - 면 배열 (`polygons` / `loops`) 은 면 선택 모드일 때만 읽음 (정점 모드 재읽기 시간을 줄임).
- 환경설정 `maya_component_colors` 「Component Colors」 (UI Elements 상자, 기본 켬).
- Outliner 선택 행: **건너뜀 (delegated)**. kit 샷 (`tmp/sel134/z_outliner.png`, 1.25): 활성 행 #334d80 + 글자 #c68e63–#ffaf29,
  다른 선택 행 #1d314d + 글자 #df6704 (Blender 테마), Maya = #5285a6 + 흰 글자. POST_PIXEL 은 C 가 그린 아이콘 · 글자 위에 그려지므로
  행을 칠하면 그것들을 덮고, Python 은 C 아이콘을 다시 그릴 수 없다. 프레임버퍼를 읽어 행 배경 · 글자 색만 바꿔 텍스처로 다시 그리는
  방법은 (1) 행 색이 줄무늬 위 반투명 하이라이트라 행마다 · 테마마다 다르고, (2) 마우스를 올리면 호버 하이라이트로 색이 바뀌어 그 행만
  Blender 색으로 깜박이며, (3) 활성 행 아이콘의 둥근 밝은 상자와 아이콘 가장자리는 바꿀 수 없고, (4) UI 영역 텍스처 색 공간이
  4.5 / 5.x 에서 다르다 (`compat.LINEAR_IMAGE_SHADER`) — 믿을 수 있게 할 수 없어 건너뜀.

## Blender 가 여전히 그리는 것 (Python 으로 바꿀 수 없거나 이 레인 밖)

- 편집 메시: Blender 자신의 엣지 / 정점 / 면 틴트 (테마 색) 가 킷 색 아래에 남는다 — 킷 선 (2 px) · 점 (3/4 px × 배율) 이 덮지만
  가장자리 안티에일리어스 몇 픽셀, 선택 면의 옅은 주황 틴트 (점묘 사이), X-ray 면 모드의 면 중심 점은 Blender 색. 끄려면 뷰 오버레이
  (`show_faces`, `show_edge_sharp`) 를 Maya 레이아웃에서 꺼야 하는데 레이아웃 진입 뷰 설정은 GRID 레인 몫 — 메인에 제안.
- 오브젝트 모드: Maya 레이아웃 밖 뷰의 주황 외곽선 (위 결정), 오브젝트 원점 점 (주황, `show_object_origins`), 3D 커서 (GRID 레인).
- Outliner 선택 행 (위), UV 에디터 · 커브 · 아마추어 편집 모드 색 (이 레인 밖).
- 5 만 정점 초과 + 편집 모드 모디파이어 (Smooth Preview 3 등) 메시: 킷 색 없이 Blender 색.

## 검증

- 헤드리스 `ALLSET_SANDBOX=sel134 python tests/run.py -k step134,step47,enable_disable,step130`: **32/32** (새
  `tests/test_step134_selection.py` 7: 고정 색, 테마를 주황으로 바꿔도 와이어 색 불변, 컴포넌트 색 값, 부채꼴 삼각형, `layers()` 숨김 ·
  모드, 평가 / BMesh 읽기 일치 + Subsurf 케이지 + 5 만 제한, 환경설정 · 해제).
- GUI `ALLSET_SANDBOX=sel134 python tests/gui/run.py -k step134_selection,step47,step74`: 1.25 **20/20**, `--ui-scale 0.8` (실효 1.0)
  **20/20** (새 `tests/gui/gui_step134_selection.py` 11: 리드 9/12 엣지 연두 · 다른 선택 9/12 흰색 · 비선택 0, 리드 상자 안 Blender
  주황 8 px / 연두 751 px, 선택 정점 #fdff88 · 비선택 #c800c8 3/3 · 엣지 #64dcff, 선택 엣지 #e3ac79, 면 점묘 25 %, 10 만 정점 시간).
- 성능 (10 만 1 124 정점 격자, 편집 모드, 2 만 정점 선택, `wm.redraw_timer` DRAW 30 회 평균, 1600×900):

  | 배율 | 킷 색 끔 | 킷 색 켬 | 캐시 다시 만들기 (읽기 + 배치) |
  |---|---|---|---|
  | 1.25 | 1.81 ms | 2.95 ms | 36–42 ms (읽기 26–31 + 배치 9–10) |
  | 1.0 | 2.35 ms | 2.26 ms | 33–35 ms (읽기 25–26 + 배치 8–9) |

  (첫 실행 1 px LINES 판: 1.95 → 1.85 ms.) 다시 만들기는 선택 · 편집 · depsgraph 업데이트마다 한 번 (화면 이동 · 줌은 없음).
- 나란히 (왼쪽 Maya 2022, 오른쪽 kit; 직접 봄): `tmp/sel134/pair_{object,verts,edges,faces}_{125,100}.png` (`tmp/p134/pairs.py`),
  샷 원본 `tmp/sel134/shots125/`, `shots100/`. 리드 연두 / 다른 선택 흰색 / 엣지 연파랑 / 보라 · 노랑 정점 / 주황 엣지 / 주황 점묘가
  Maya 와 같은 자리에 같은 색. 차이: kit 선이 더 굵음 (2 px vs 1 px), Blender 원점 점 · 3D 커서.
