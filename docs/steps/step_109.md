# Step 109 — Shelves: Maya order, greyed placeholders, Sculpting brushes, Maya-style icons

Backlog: step_98.md #7, step_98_quant.md §3 (98 of 203 factory buttons drawn; unmapped ones dropped, gaps in Maya's
order). Sources: research/maya/shelves.md §1–§3, research/maya/shelves.json (`factory`),
research/maya/screens/audit7/pairs/shelf_*.png (Maya 2022 shelf grabs, audit 7).

## 계획

1. **Every factory button keeps its slot.** `shelf.factory_buttons()` returns all buttons of the shelf in Maya order
   with `action None` for the unmapped ones. The icon row draws them greyed (icon desaturated, alpha 0.35); hover
   shows the tooltip "Maya: <label> (greyed) → <substitute>" + the line, and puts the line in the Help Line, like
   greyed menu items (step 101 `notices.tooltip`). A click shows the notice in the Help Line and runs nothing.
2. **Notices without new text where possible.** `shelf_map.MENU` maps a shelf button to the Maya menu item that runs
   the same runTimeCommand (`research/maya/menus.md` `rtc:` tags, `shelves.json` `command`). A button with a menu
   path takes the menu item's action (`menu_map.MAP`) if mapped, else its notice (`notices.greyed_notice`).
   Buttons that are in no menu (Super Shape, Human IK, Render Diagnostics, Convert To Frozen …) get
   `shelf_map.NOTICES`. Test: every unmapped factory button has a notice.
3. **Map what Blender can do** (task: Sculpting brushes, Curves / Surfaces and FX):
   - Sculpting 15 tools → the essentials brushes already behind Mesh Tools > Sculpting Tools (step 101
     `maya_kit.sculpt_tool`; Bulge = Inflate/Deflate, Freeze = Mask, …). Spray / Repeat get the keymap's step-107
     substitutes (Draw Sharp / Layer) with their notice. Shape Editor, Base Meshes (= Asset Browser) by menu path.
   - Curves / Surfaces: Attach / Detach / Extend Curve / Insert Isoparms by menu path; new kit operators measured
     against mayapy (below): Planar, Loft, Extrude, Bevel Plus, Pencil Curve Tool, Add Points Tool; new create kinds
     NURBS Square / Cube / Cone. The same operators fill the Create / Curves / Surfaces menu items (their notices go).
   - FX: 3D Fluid Container with Emitter, Emit Fluid from Object (quick smoke), Make Collide (fluid effector),
     Display Input / Current Mesh (cloth modifier viewport toggle), Paint Hair Tool (hair Curves sculpt mode).
   - Rigging / Animation / Rendering by menu path: Create Cluster, Pole Vector, Anisotropic / Phong E / Layered /
     Ramp / Use Background materials (step 105 kinds), Edit Material Attributes (AE), Show Batch Render.
4. **Icons closer to Maya's** (re-drawn, decision 6: no Maya artwork). Measured in the audit-7 grabs: one hue per shelf
   — Curves / Surfaces #58a8d0, Poly Modeling and Sculpting #d89058, Rigging #a898d8, Animation #e07040, Rendering
   #c0b038, FX and FX Caching #d88070 — and light grey #c0c0c0 for tool parts; flat two-tone pictograms. Objects
   (primitives, lights) stay in the shelf hue, tool glyphs become grey with a hue accent, no white highlights.
5. Verify: headless test (counts per tab = Maya factory counts 38/43/26/18/14/25/29/10, drawn mapped ≥ 150 / 203,
   every greyed one has a notice, new operators' results), GUI shots of the eight tabs side by side with the Maya
   grabs (`research/maya/screens/step109/`).

mayapy measurements (Maya 2022, defaults, `tmp/s109/maya_surf.py`):
- Planar on a closed circle → `planarTrimmedSurface1` (nurbsSurface), history `planarTrimSurface1`.
- Loft of two circles → `loftedSurface1` (nurbsSurface), loft node uniform off, close off, degree 3, sectionSpans 1.
- Extrude profile + path → `extrudedSurface1` (nurbsSurface), extrudeType 2 (tube: profile along the path).
- Bevel Plus on a circle → `bevelPolygon1` (**mesh**), curve kept; width 0.1, depth 0.1, extrudeDepth 0.25,
  capSides 4, joinSurfaces on.
- `nurbsSquare` → group `nurbsSquare1` with four curves top / left / bottom / right `…nurbsSquare1`;
  `nurbsCube` → group `nurbsCube1` with six surfaces top / bottom / left / right / front / back; `cone` →
  `nurbsCone1` (one nurbsSurface).

Delegated: the target counts are the Maya 2022 **factory** shelf files (203 buttons, no separators). The audit-7
Maya grab used shelves saved in the user's prefs (Animation 19 children incl. Ghost buttons and separators), which
are not the factory defaults (CLAUDE.md: Maya reference = factory prefs).

## 한 것

- **모든 공장 버튼이 Maya 자리에** (`ui/shelf.py`): `all_buttons()` = 셸프 전체 (Maya 순서), `factory_buttons()` = 매핑된 것만.
  아이콘 줄은 매핑 없는 버튼을 회색·흐리게 (`shelf_icons.GREYED_ALPHA` 0.35) 그 자리에 그림. 툴팁 = 「<라벨> (Maya shelf, greyed)
  → 대체 + 한 줄」 + Help Line (`button_tooltip`), 클릭 = 안내만 (`button_notice`). 매핑됐지만 결과가 다른 버튼도 툴팁에
  「→ Blender: …」.
- **안내는 메뉴와 공유** (`ui/shelf_map.py`): `MENU` = 셸프 버튼 → 같은 runTimeCommand 의 Maya 메뉴 항목 (93 개). 메뉴가 매핑돼
  있으면 그 동작, 회색이면 그 안내 (`notices.greyed_notice`). 메뉴에 없는 3 개 (Curve Editing Tool, Convert To Frozen, Render
  Diagnostics) 는 `shelf_map.NOTICES`.
- **새로 되는 버튼** (98 → **151 / 203**):
  - Sculpting 19 / 26: 15 도구 = essentials 브러시 (Smooth, Relax = Relax Slide, Grab, Pinch = Pinch/Magnify, Flatten = Flatten/
    Contrast, Foamy = Clay, Wax = Clay Strips, Scrape = Scrape/Fill, Fill = Fill/Deepen, Knife = Crease Sharp, Smear, Bulge =
    Inflate/Deflate, Amplify = Sharpen, Freeze = Mask), Spray = Draw Sharp / Repeat = Layer (step 107 키와 같은 대체, 안내 포함),
    Shape Editor, Base Meshes (= Asset Browser). 세션 첫 브러시는 에셋 라이브러리가 아직 로딩 중이라 취소됨 (GUI 측정) →
    `menu_items._retry_brush` 가 0.2 초마다 최대 5 초 재시도.
  - Curves / Surfaces 24 / 38: Attach / Detach / Extend Curve / Insert Isoparms (메뉴 경유), 새 `operators/curve_tools.py`:
    Planar (`planarTrimmedSurface1` = 2D 채운 커브 사본), Loft (`loftedSurface1` = 커브를 호 길이로 같은 점 수로 나눈 쿼드 메시),
    Extrude (`extrudedSurface1` = 경로 사본 + 프로필 bevel object), Bevel Plus (`bevelPolygon1` 메시, 커브 유지, Maya 값 0.1 / 0.1 /
    0.25), Offset Curve (`offsetNurbsCurve1`, 거리 1, 방향 = 법선 × 접선), Sweep Mesh (`sweep1`, 8 각 관), Pencil Curve Tool (새
    `curve1` + Draw 툴), Add Points Tool (끝점 extrude); create 종류 NURBS Square / Cube / Cone (Maya 그룹 구조와 이름, mayapy 크기).
  - FX 13 / 29: 3D Fluid Container with Emitter (`fluid1` 10 × 10 × 10, 해상도 10, `fluidEmitter1`; mayapy), Emit Fluid from Object
    (quick smoke), Make Collide (Fluid effector), Display Input / Current Mesh (Cloth 모디파이어 뷰포트 끔 / 켬), Paint Hair Tool
    Options (Hair Sculpt 모드).
  - Rigging / Animation: Create Cluster, Pole Vector Constraint ×2. Rendering: Anisotropic / Phong E / Layered / Ramp / Use
    Background 재질 (step 105 종류), Edit Material Attributes (AE 도크). Poly Modeling: SVG, Content Browser, Retopologize,
    Circularize, Contour Stretch.
  - 같은 동작을 Maya 메뉴에도 매핑 (`menu_map` step 109 블록, 차이는 `notices.NOTICES`). 「Create/Sweep Mesh」 범주 규칙은 이제
    쓰이지 않아 지움, 「Surfaces」 안내 문구에서 Loft 제거.
- **아이콘 다시 그림** (`ui/shelf_icons.py`): Maya 셸프 그림에서 잰 색 (Curves #58a8d0, Poly·Sculpt #d89058, Rigging #a898d8,
  Animation #e07040, Rendering #c0b038, FX·Caching #d88070), 도구 부분 #c0c0c0 회색, 흰 하이라이트·입체 그라데이션 없음, 재질은
  회색 셰이더 공 (Ramp 만 색), 창 버튼 = 창 그림 (Maya teal), Sculpting 도구 = 주황 공 + 도구마다 다른 회색 표시, 유체 = 용기.

delegated:
- 목표 개수 = Maya 2022 **공장** 셸프 파일 (203, 구분선 없음). audit 7 Maya 그림은 사용자 prefs 셸프 (Ghost 버튼, 구분선) 라 다름.
- Loft / Extrude 순서: Blender 오브젝트엔 선택 순서가 없어 활성 (마지막 선택) 이 마지막, 나머지는 이름 순.
- Loft 결과는 NURBS 가 아니라 메시 (Blender 는 NURBS 로프트 불가), Bevel Plus 는 커브 평면 양쪽으로 압출 (Maya 는 한쪽).
- 유체 이미터는 도메인의 자식으로 두지 않음 (도메인 크기가 스케일이라 자식이 같이 커짐).
- test_step51 의 글자 대체 예시를 「Use Background」 (이제 셰이더 공) 에서 「Convert To Frozen」 으로 바꿈.

## 검증

- 헤드리스: `tests/test_step109_shelves.py` 20/20 — 탭별 개수 = Maya (38/43/26/18/14/25/29/10, 라벨·순서 = shelves.json),
  매핑 151 ≥ 150, 회색마다 안내, MENU 경로 실재, 메뉴·셸프 동작 일치, 회색 클릭 = 안내, Bulge → Inflate/Deflate 브러시 실제
  활성, Planar / Loft / Extrude / Bevel Plus (두께 0.45) / Offset (Blender +Y = Maya −Z) / Sweep (8 각) / NURBS Square·Cube·Cone /
  Pencil / Add Points / 유체 용기 (10 × 10 × 10, 해상도 10) / Make Collide / nCloth 표시, 아이콘 색·회색 처리.
  전체 **830/830** (98 파일). GUI 전체 **1074/1074** (86 파일).
- GUI: `tests/gui/gui_step109_shelves.py` 11/11 (배율 0.8 = 유효 1.0) — 탭 8 개 자리 수 = Maya, 회색 Trim Tool 클릭 → Help Line
  안내, Sculpting Grab 아이콘 → 조각 모드 + Grab 브러시 (첫 사용 로딩 재시도 포함).
- 나란히 그림: `research/maya/screens/step109/shelf_<탭>.png` (위 Maya 2022 audit-7 그림, 아래 kit) 8 장을 직접 봄: 자리 수·
  순서가 같고 (Maya 쪽 구분선·Ghost 는 사용자 prefs 셸프), 색 계열 일치.

## 남은 것

- 회색 52 개: Blender 에 없는 NURBS 편집 (Rebuild, Trim / Untrim, Intersect, Project, Birail, Attach / Detach / Extend / Rebuild
  Surfaces, Three Point Arc, Curve / Surface Editing Tool), 조각 Imprint·블렌드셰이프 타깃 4 도구·Convert To Frozen·Pose Editor,
  Human IK, Ambient / Volume Light, Shading Map, Batch Render 관련 3, 2D 유체, nHair 표시·변환 14, FX Caching 6 (Initial State,
  캐시 켜기·끄기·병합·프레임 교체), Super Shape, 3D Grab UV Tool. 모두 안내 있음.
- Maya 플러그인 탭 (Arnold, Bifrost, MASH, Motion Graphics, XGen) 은 없음 (공장 기본 목록 밖, shelves.md §2).
- Loft 는 메시, Bevel Plus 는 양쪽 압출, Offset 결과는 poly 커브 (안내에 적음). 손으로 확인할 것은 `docs/manual_checks.md` step 109.
