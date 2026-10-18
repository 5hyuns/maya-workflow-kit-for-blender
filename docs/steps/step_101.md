# Step 101 — Menu honesty: no unexplained greyed item, map the cheap ones

backlog 3 (docs/PLAN.md 「재점검 7차」 3): step_98.md #9, #10, #13; docs/steps/step_98_quant.md §1, §1b.
기준선 (step 98): 메뉴 1251 항목, 작동 370 (29.6 %), 회색 881 중 866 이 이유 없음.

## 계획

근거: `research/maya/re/menu_honesty.md` (mayapy 측정 + audit 7 실제 메뉴), research/maya/menus.md.

1. **메뉴 데이터 (tools/gen_menu_data.py)** — 정적 파싱이 놓친 실행 시 항목을 생성기에서 채운다.
   - `RUNTIME_LABELS`: 최상위 `<dynamic:...>` 라벨을 순서대로 채움. Modify = Center Pivot, Bake Pivot,
     Prefix Hierarchy Names..., Search and Replace Names..., Add / Edit / Delete Attribute... (그동안
     `menu_map.EXTRA` 로 넣던 Pivot·Attributes 는 생성기로 옮김), Help = Maya Help, YouTube Learning
     Channel, About Maya.
   - `RUNTIME_MENUS`: 빈 Audio / Stereo 를 Maya 2022 Python 메뉴 빌더의 라벨로 채움.
   - `CACHE`: Cache = Alembic Cache ▸ / Geometry Cache ▸ (지금의 13 항목) / GPU Cache ▸ (실제 Maya 순서).
   - `INSERTS`: 실제 Maya 에 있는데 데이터에 없는 최상위 항목 (#13): File Game Exporter / Send To Unity /
     Unreal, Create Sweep Mesh / USD, Select USD Selection Mode, Playback Cached Playback, Visualize Ghosting 4 +
     Time Slider Bookmarks, Deform Muscle, Generate XGen 17.
2. **회색 항목마다 안내 (a)** — `notices.CATEGORIES`: 경로 접두사 → (가장 가까운 Blender 기능, 한 줄). 가장 긴
   접두사가 이긴다 (NURBS 곡면, Paint Effects, XGen, Bifrost/nHair, nCloth/nucleus, Maya 전용 체계 …).
   `notices.notice(path)` = 명시 NOTICES (매핑된 항목에도), `notices.greyed_notice(path)` = NOTICES 또는 분류.
   테스트: 모든 회색 잎 항목에 안내가 있고, 분류 규칙마다 실제 경로가 하나 이상 걸린다 (죽은 규칙 금지).
3. **싼 매핑 (b)** — Blender 기능이 바로 있는 것은 MAP 에 (안내가 필요하면 NOTICES 도). Blender 에 없는 것 중
   작은 bmesh / 데이터 작업으로 Maya 결과가 나오는 것은 kit 연산자 (`operators/menu_items.py`):
   Prefix Hierarchy Names / Search and Replace Names, Soften/Harden Edges (객체 = 모든 모서리, 각도 30,
   mayapy `polySoftEdge -a 30`), Detach (정점 / 모서리 / 면 모드별), Edit Edge Flow (Set Flow 식 3 차 보간),
   Wedge (선택 모서리 축으로 면 회전 = mesh.spin), Nonlinear Bend / Flare / Squash (Simple Deform 방식),
   Object Display Template / Bounding Box, Sculpting Tools (essentials 브러시), Assign Checker Shader, Audio
   (VSE 사운드 스트립), Stereo Camera (multiview).
4. **매핑된 항목은 Maya 처럼 활성 (c)** — `menu_sets.draw_item`: Blender 연산자 poll 이 실패하면 회색 대신
   `maya_kit.menu_item` 으로 그림 (항상 활성). 실행 시 `menu_map.OBJECT_MODE` (mayapy 측정, re 문서 §2):
   - `ALL`: 객체 모드 + 선택 메시 → 편집 모드, 해당 요소 모두 선택, 실행 (`undo=True`), 객체 모드로.
   - 문자열: Maya 경고 그대로 WARNING 보고.
   - 그 밖에 poll 실패: "<라벨>: <무엇을> 먼저 선택" 경고 (mesh = 컴포넌트, curve = 커브 점, armature = 조인트).
5. **재집계** — `tools/menu_count.py` (bpy 없는 집계, tmp/audit7 과 같은 규칙, 안내는 greyed_notice 기준).
   목표: 작동 ≥ 40 %, 안내 없는 회색 0. GUI: 객체 모드 Edit Mesh 메뉴 스크린샷에 회색 매핑 항목 없음.

설계 결정 (delegated): 같은 Blender 기능을 여러 Maya 항목에 매핑하는 것은 그 항목이 Maya 에서 하는 일과 결과가
같거나 안내로 차이를 말할 때만 (예: Deform > Paint Weights 의 11 항목 = 그 변형기의 정점 그룹 칠하기). Blender
동작이 이미 Maya 항목 그 자체인 것 (Playback Looping > Continuous) 은 `maya_kit.menu_note` (안내만 보이고 끝남).

## 한 것

- **메뉴 데이터** (`tools/gen_menu_data.py` → `ui/menu_data.py`): `RUNTIME_LABELS` (Modify Pivot / Naming / Attributes,
  Help 의 Maya Help · YouTube Learning Channel · About Maya), `RUNTIME_MENUS` (Audio 9 항목, Stereo Editors / Create /
  Links), Cache = Alembic Cache ▸ / Geometry Cache ▸ / GPU Cache ▸ (mayapy 로 라벨 측정), `INSERTS` (#13: File Game
  Exporter / Send To Unity / Unreal, Create Sweep Mesh / USD, Select USD Selection Mode, Playback Cached Playback,
  Visualize Ghosting 4 + Time Slider Bookmarks, Deform Muscle ×3 메뉴, Generate XGen 17). `build()` / `option_boxes()`
  로 나눠 test_step51 이 같은 경로를 씀. Pivot / Attributes 의 `menu_map.EXTRA` 는 지움 (데이터로 옮김).
- **안내 (a)**: `notices.CATEGORIES` (경로 접두사 → 가장 가까운 Blender 기능 + 한 줄, 가장 긴 접두사), `greyed_notice()`;
  회색 항목 툴팁 / Help Line 에 분류 안내. 매핑했지만 뜻이 다른 항목 NOTICES 약 50 개 추가 (Archive = Pack, Game
  Exporter = FBX, Geometry / GPU Cache = Alembic, Cluster = Hook, Sine = Wave, Paint Weights = 정점 그룹 …).
- **매핑 (b)** 약 190 개 (`menu_map` 「step 101」 블록): 노멀 (Soften/Harden, Lock / Unlock, Vertex Normal Edit Tool),
  Edit Mesh Detach / Flip / Circularize / Edit Edge Flow / Wedge / Transform / Split with Projected Curve, Modify > Naming,
  Alembic / USD, Windows 편집기 (Component = Spreadsheet, Connection = Drivers, Shape Editor = Shape Keys (Data 탭),
  Render Layer = View Layer 탭, Light Linking, Sets = Outliner, Command Shell = Python Console, Content Browser = Asset
  Browser), Audio (VSE 사운드 스트립), Stereo Camera, Sculpting Tools 15 (essentials 브러시), Help (Blender 문서 URL,
  About), Bezier 앵커 / 탄젠트, Nonlinear Bend / Flare / Squash, 선택 변환 (Contained Edges / Faces, UV Shell), 커브 CV
  선택 등. 새 kit 연산자 14 개 `operators/menu_items.py` (prefix_hierarchy, search_replace_names, soften_harden, detach,
  edge_flow, wedge, nonlinear, object_display, sculpt_tool, checker_shader, import_audio, delete_sounds, stereo_camera,
  menu_note).
- **활성 (c)**: `menu_sets.draw_item` 이 Blender poll 이 실패하는 매핑 항목과 `menu_map.OBJECT_MODE` 항목을
  `maya_kit.menu_item` 으로 그림 (항상 활성). 객체 모드에서 `('ALL', 모드)` = `maya_kit.menu_whole_mesh` (편집 모드 →
  전체 선택 → 실행 → 객체 모드, undo 한 단계; Bevel 50 % / Chamfer 25 % / Average 10 회 = mayapy 값), 문자열 = Maya 경고
  그대로. 그 밖의 poll 실패 = "<라벨>: select <컴포넌트> first." 경고, `menu_run` 의 poll 오류도 같은 문장.
- 집계 도구 `tools/menu_count.py` (bpy 없이, audit 7 규칙).
- 결정 (delegated): Merge to Center 는 객체에서 Maya 처럼 오류 (전부 한 점으로 합치지 않음); Collapse 는 객체 = 모든 면
  [I] (performPolyCollapse.mel:24-45 의 면 기본값); Flip Triangle Edge / Spin Edge 는 Maya 가 조용히 아무것도 안
  하지만 kit 는 "Select edges" 경고를 보임; Untemplate 은 선택에 템플릿 오브젝트가 없으면 장면의 모든 템플릿 오브젝트
  (Blender 에선 템플릿 = 선택 불가라 고를 수 없음); Fields > Volume Curve 는 매핑하지 않음 (raw effector_add 금지, test_step54).

## 검증

- `python tools/menu_count.py`: 고유 경로 1312 중 작동 558 (**42.5 %**, 전 1251 중 370 = 29.6 %), 세트별 합 1480 중 633
  (42.8 %), **안내 없는 회색 0** (전 866).
- 헤드리스 `tests/test_step101_menu_honesty.py` 14/14 (모든 회색에 안내, 죽은 분류 규칙 0, 작동 ≥ 40 %, 실행 시 메뉴
  데이터, 새 연산자 결과, 객체 모드 Edit Mesh 회색 매핑 0, Poke 6 → 24 면 / Bevel / Bridge 경고). 전체 739/739, GUI 전체 1019/1019.
- GUI `tests/gui/gui_step101_menus.py` 4/4 + 스크린샷 (tmp/shots101): 객체 모드 Edit Mesh 메뉴에서 회색은 매핑 안 된
  Reorder Vertices / Assign Invisible Faces / Project Curve on Mesh 뿐, Cache 의 세 하위 메뉴, Audio 메뉴 + 툴팁.
- Maya 측정: `research/maya/re/menu_honesty.md` (mayapy 라벨 질의 + Edit Mesh 명령 객체 선택 실행).

## 남은 것

- 회색 754 개는 안내만 있음: NURBS 곡면·Paint Effects·XGen·nHair·nConstraint·Toon·Joint Labelling 처럼 Blender 에
  없는 체계. 다음 후보 (싼 순): Skin Edit Influences / Hammer, Select Grow / Shrink Along Loop, Visualize Snapshot,
  Curves Rebuild (Geometry Nodes Resample), Create EP / Pencil Curve (Draw 툴).
- Alembic / GPU Cache 옵션 박스는 표시만 (□ = run + Adjust Last Operation): 진짜 옵션 창은 step 103.
- Help 항목은 URL 을 브라우저로 엶 (네트워크 코드 없음, `wm.url_open`).
