# Step 154 lane A — 끝난 것, 남은 것, blindspot (재점검 10차 = 사용자 지시의 「재점검 9차」)

User request (2026-10-24, item 2): "research/README.md 대응표·docs/PLAN.md·docs/steps/*.md 「남은 것」·docs/manual_checks.md를 모아
끝난 것 지우고 남은 것 정리 (know-your-unknowns blindspot으로 놓친 것 보완)" — 비판 기준: "기본 Maya에 Blender 기능이 붙은 모습",
칭찬 말고 차이만.

Paper lane, Blender 실행 없음. 입력: `docs/steps/step_145_remaining.md` (감사 9 의 정리 목록), `docs/steps/step_146.md` …
`step_153.md` + `step_152_render_b.md` 의 「남은 것」, `docs/PLAN.md` 「재점검 9차」, `docs/HANDOFF.md`, `docs/manual_checks.md`,
`gh issue list --state open` (2026-10-24). 판정은 모두 HEAD e26b969 의 `src/allset` 을 grep 으로 다시 확인 ("[I]" = 코드를 읽은 것,
돌린 것 아님). 메뉴 수치 = `python tools/menu_count.py` (Blender 없이 돎) + `tmp/audit154a/greyed.py` (같은 함수로 메뉴별 회색 목록).
판정은 delegated.

## 1. 구현률 — research/README.md 대응표 (33 행)

| 묶음 | Done | Partial | Not started | Not possible (C) |
|---|---|---|---|---|
| 조작 / 단축키 (13) | 12 | 1 — 3D View 밖 선택 수정키 | 0 | 0 |
| UI (9) | 8 | 1 — 테마 (Maya 회색) | 0 | 0 |
| 개념 (11) | 9 | 0 | 0 | 2 — 분리 rotate / scale pivot, Y-up |
| **합계 (33)** | **29 (88 %)** | **2 (6 %)** | **0** | **2 (6 %)** |

감사 9 (step 145) 와 같음 — **움직인 행 없음**. 146–153 은 기존 Done 행의 깊이 (옵션 상자, undo, Channel Box, Graph Editor, 렌더)
였다.

- **선택 수정키 (Partial, 그대로)**: `keymap/maya_patches.py:52-62` — Outliner / Graph click 의 Ctrl · Ctrl+Shift 는 toggle 로
  대체 (`_OUTLINER_CLICK`, `_GRAPH_CLICK`), uv / outliner / graph / action / nla `select_box` 는 XOR 없음 (`_BOX_NO_XOR`), Node
  Ctrl-marquee = Blender link cut (`_NODE_BOX`). 146–153 에 변경 없음.
- **테마 (Partial, 조금 좁아짐)**: step 149 가 선택된 격자도 Maya 초록 / 흰 와이어 (`ui/selection_wire.py`), step 151 이 매니퓰레이터
  툴팁을 끔 (`ui/manipulator.py:459`). 여전히 사용자 테마: 모든 위젯 / 메뉴 / 패널 배경, Outliner 선택, Dope Sheet / Graph 키 색,
  Rotate gizmo, 격자 / 메쉬 밑 Blender 주황 1 px 윤곽 (step_149.md 「남은 것」, Python 이 끌 수 없음).
- 나머지 31 행은 step_145_remaining.md §1 의 근거 그대로 (재확인: `operators/view.py` dolly, `operators/hold.py`, `marking/`,
  `ui/channel_box.py`, `ui/attribute_editor.py`, `switch.enter_layout`).

## 2. 감사 9 뒤 끝난 것 — 목록에서 지움

| 항목 (출처) | 끝낸 것 (근거) |
|---|---|
| #82 옵션 상자가 누르고-끌기로만 열림 (step_145 §3 #1) | step 146: 0.2 s 누르면 포인터가 hold 메뉴의 "Option Box ❒" 줄로 (`ui/menu_sets.py:665-698`, `allset.option_box_point`), Shift / Ctrl+클릭 = 옵션 상자 (`:677-678`). **남은 부분은 §3 #1** (❒ 만 클릭은 C 벽) |
| #88 Mesh Tools 가 undo step 없음, #92 / #86 Adjust Last Operation (§3 #2, #11) | step 147: `undo_steps.py` (`ed.undo_push`), `@undo_steps.no_redo_panel`; `test_step147_undo`, `gui_step147_hud` |
| #87 CB RMB = Blender 메뉴 (§3 #3) | step 148: 창 모달이 RMB 를 먼저 받음 `ui/channel_box.py:1029-1057` → `ALLSET_MT_cb_channels` (:1301) |
| #85 좁은 도크 잘림 (§3 #4) | step 148: 메뉴 막대 "Channels" 는 세 배율에서 다 보임 (측정), AE Translate / Rotate / Scale = CB 프록시 숫자 (`attribute_editor._maya_number_rows`). AE 노드 탭 / 헤더 버튼 ("pC…", "Sele…") 은 재측정 안 됨 → §6 미확인 |
| #83 UI 1.5 빈 두 줄 (§3 #21) | step 148: `PANE_TOP = 1.6` (`ui/channel_box.py:2012`), `_round_half_up` (:946) |
| #95 격자 Scale 0.02 | step 148: `operators/deformers.py:335-337` (`delta_scale = maya_unit()`) |
| 조명 SHAPES = Blender Power (§3 #13 일부) | step 148: Color R / G / B + Intensity (`operators/lights.channel_attrs`) |
| #91 재생 중 선택 와이어 | step 149: `frame_change_post` + `time_dependent` (`ui/selection_wire.py:23,240`) |
| #93 Delete 뒤 pCube2 | step 149: `operators/naming.py:41` `drop_orphans` |
| #94 비균일 스케일 Bind 가 joint 를 잃음 | step 149: Maya Closest distance `operators/skin.py:359` (mayapy ≤ 2e-5) |
| #96 Graph Editor 이름 / 강조 / 스크롤 (§3 #8 일부) | step 150: Maya 채널 이름, 고른 줄만 강조, joint / blendShape 노드, 휠, View > Auto Frame / Curve Name; Show 회색 92 → 84 |
| 2D 편집기 Ctrl+A (§3 #12 일부) | step 150: Graph Editor / Dopesheet / NLA / Animation Channels (`keymap/maya_patches.py:426-429`) |
| #98 매니퓰레이터 툴팁, #99 RMB 링 크기, #100 상태 줄 Blender 문구, 압출 매니퓰레이터 한 화살표 | step 151: `ui/manipulator.py:459`, `marking/engine.Layout.ring_rect` (R 55, 21 px), 상태 줄에 `template_status_info` 없음, Ctrl+E = polyExtrudeFace 매니퓰레이터 (`ui/in_view.py`) |
| #101 렌더 기본 (§3 #5 대부분): 기본 조명, Render Sequence / Batch Render ❒, Render Current Frame ❒ 경고, Test Resolution, Batch Render | step 152: `operators/default_light.py`, `operators/render_batch.py:45`, `operators/option_windows_render.py`, `ui/menu_map.py:496-504` |
| Grid Options (§3 #14, 감사 9 BS3) | step 152: `operators/option_windows_display.py`, `ui/maya_grid.py` 가 값을 따름; `gui_step152_grid` |
| #90 5.x Paint Skin Weights ❒ (§3 #23), 감사 9 BS8 (5.x 전체 실행) | step 153: `compat.py:283` `unified_paint_settings`, `:309` `menus_close_on_leave`; 헤드리스 4.5 / 5.0.1 / 5.1.2 / 5.2.3 각 1398, GUI 5.2.3 전체 |

**GitHub 정리**: 위 17 개 이슈 (#82 #83 #85 #86 #87 #88 #90 #91 #92 #93 #94 #95 #96 #98 #99 #100 #101) 는 코드로는 끝났지만 아직
**OPEN** — 이 프로젝트는 릴리스 때 닫는다 (step_143.md:11, :22). 0.4.0 릴리스 때 닫을 것. 코드로도 열린 이슈는 **#81 #89 #97** 셋.

## 3. 남은 것 한 목록 (Maya 사용자 영향 순)

점수 = 하루 빈도 F (1–5) × 심각도 S (1–4), 등급 외형 / 조작 / 기능 / 없음 (step 98 기준). "출처" = 처음 적힌 곳.

| # | 영역 | 항목 | 등급 | F×S | 출처 |
|---|---|---|---|---|---|
| 1 | UV | **UV Editor 도구**: Tools > Unfold / Move UV Shell / Cut / Sew / Pin / Symmetrize 회색 (Tools 10 / 19), Modify > Stack / Snap Together / Distribute / Orient Shells / Straighten / Map Border 회색 (14 / 31), Cut/Sew > Auto Seams / Create Shell, Edit > Delete (UV), View > Toggle Shell Borders / Isolate Select (7 / 20), UV Toolkit 1 / 3; 키 4 / 6 / 8 / 9 / Ctrl+1 / Delete 해당 없음. Maya UV 작업의 핵심 (Unfold) 이 없음 | 기능 | 3×3 = **9** | step_133_quant §9 #4, step_145 §3 #7 (변경 없음) |
| 2 | 모델링 | **Curves / Surfaces**: Curves 16 / 36 (EP Curve Tool, Rebuild, Fillet, Edit Curve Tool, Cut, Intersect, Straighten, Align 회색), Surfaces 8 / 41, Create > Curve Tools > EP Curve Tool 회색 | 없음 | 3×3 = **9** | step_145 §3 #6 (변경 없음) |
| 3 | 애니메이션 | **Graph Editor 남은 깊이**: Key 메뉴 명령이 Graph Editor 선택 키가 아니라 Channel Box 노드 기준 (step_140.md:93 — `graph_keys.py` 는 tangent / key_edit 만 선택 키); 섞인 곡선에서 Translate 가 미터라 납작 (Blender 에 곡선별 배율 없음, C); 길이 눈금은 마우스가 편집기 위일 때만 (step 137); Select 2 / 8 (Curve / Key / In / Out Tangent), Keys > Mute Key / Add Key Tool, Default In / Out Tangent > Flat, View 20 / 40, Curves 23 / 39 회색; Dope Sheet View > Auto Frame 회색; 킷 outliner 에 노드 아이콘 / 기울임꼴 없음, joint / blendShape 위계 없음 | 기능 | 3×3 = **9** | step_140.md:93, step_150.md 「남은 것」, menu_count |
| 4 | UI | **#81 Maya UI 되돌리기 / 워크스페이스**: 기본 Maya 레이아웃으로 돌아가는 길이 재시작뿐, Windows > Workspaces = Blender 메뉴 (`ui/menu_map.py:280`), 워크스페이스는 "General" 하나 (`tools/make_startup.py:300`), Panels > Saved Layouts 회색 (`ui/panel_menus.py` `_grey`) | 조작 | 3×3 = **9** | #81 (사용자), step_145 §3 #9 |
| 5 | 리깅 | **가중치 / 리그 도구**: Skeleton 13 / 54, Skin 18 / 28 (Export / Import Weight Maps, Interactive Bind, Move Weights, Post Normalization), Deform > Export / Import Weights, Joint Labelling 35 항목, Key > IK/FK Keys 4 항목, Edit > Delete All by Type > IK Handles 회색; Bind 는 rest 포즈 기준 (Maya 는 지금 포즈), Closest in hierarchy / Geodesic Voxel 없음 | 없음 | 2×4 = **8** | step_110 「남은 것」, step_149.md 「남은 것」 |
| 6 | UI | **Channel Box 차이**: 상태 색이 하나 (모든 애니 상태 = `alert` 빨강, `ui/channel_box.py:1534`; Maya keyed 빨강 / driven 노랑 / expression 보라 / muted 갈색, research/maya/channel_box.md:138-139); 조명 Intensity 는 계산 속성이라 키 불가 (step 148); Spot Cone Angle / Penumbra / Dropoff 행 없음; SHAPES / INPUTS 값 칸이 7 px 오른쪽; RMB 메뉴 / Ctrl+RMB 는 §4 BS2 | 외형 | 4×2 = **8** | step_148.md 「남은 것」, 감사 8 B5 |
| 7 | 리깅 | **#97 Bind Skin 뒤 INPUTS = "Armature"** (Maya skinCluster1) + Blender modifier 눈 아이콘 — `operators/skin.py:399` 가 modifier 이름을 "Armature" 로 두고 `ui/channel_box.py:1904` 가 `mod.name` 을 그림 (AE 는 `MODIFIER_NODES` 로 skinCluster). **감사 9 에서 등록됐지만 backlog_146 / PLAN 「재점검 9차」 어디에도 안 들어가 빠짐** | 외형 | 2×3 = **6** | #97 |
| 8 | 렌더 | **렌더 남은 것**: 킷 lambert1 이 Maya 보다 1.25 배 밝음 (Diffuse 0.8 없음) + 템플릿 world 가 ~6.5 / 255 주변광; Blender 자체 F12 / Ctrl+Alt+Enter 에는 기본 조명 없음; Render Sequence 의 All Render-Enabled Layers / Cameras, Render Region, Add to Render View 없음; Run Render Diagnostics, Render Setup (Status Line, `ui/status_line.py:543`) 회색; render layers = Properties View Layer 탭 (감사 9 BS5) | 기능 | 3×2 = **6** | step_152.md, step_152_render_b.md 「Left」, step_145 BS5 |
| 9 | 렌더 | **Hypershade**: Create 91 / 160 회색, Tabs / Options 0 / 12, Graph Clear / Add / Remove / Rearrange 회색, 그래프 키 25 개 해당 없음; 스와치 **MMB 드래그로 오브젝트에 할당 없음** (step_67.md:80 에 적힌 뒤 133 / 145 목록에서 빠짐 — §4 BS3) | 조작 | 2×3 = **6** | step_133_quant §9 #9, step_67.md:80 |
| 10 | 조작 | **다른 편집기의 선택 / 내비게이션**: box XOR 없음, Outliner / Graph Ctrl-click = toggle (§1), **Outliner Shift+click = 범위 선택 아님** (감사 9 BS6, `maya_patches.py:52-55`), Graph Editor / Node Editor Alt+RMB 는 킷 dolly 아님 (Node = IC link cut) | 조작 | 3×2 = **6** | README Partial 행, step_141 「남은 것」, step_145 BS6 |
| 11 | UI | **Maya Preferences / Hotkey Editor** (감사 9 BS1 / BS2): Windows > Settings/Preferences > Preferences / Hotkey Editor = Blender Preferences (`ui/menu_map.py:287-288`); Working Units / fps / up axis / undo 를 한 곳에서 못 바꿈; 사용자가 Maya 키를 바꾼 것이 재시작 / 전환 뒤 남는지 시험 없음 | 기능 | 2×3 = **6** | step_145 BS1, BS2 (변경 없음) |
| 12 | 파일 | **Reference Editor** (감사 9 BS4): File > Reference Editor = Outliner Blender File 모드 (`ui/menu_map.py:133`), Reload / Unload / Replace / Import Objects from Reference 없음, Namespace Editor 회색 | 기능 | 2×3 = **6** | step_145 BS4 |
| 13 | UI | **옵션 상자 몸짓**: 그냥 클릭 = 명령 (Maya: ❒ 클릭 = 창), ❒ 부분 클릭은 Blender 가 버튼 안 위치를 안 줘서 불가 (C); 0.2 s 누르기 / Shift·Ctrl+클릭으로 대체. 실제 하드웨어 느낌 미확인 (manual_checks Step 146); 5.x 는 Maya 메뉴가 옵션 창 아래 열린 채 (step 153); 마킹 메뉴 / 셸프 옵션 상자는 자기 경로 (step 146 범위 밖); Shift / Ctrl 이 Maya 의 Ctrl+Shift+클릭 (셸프에 추가) 과 겹침 (§4 BS1) | 조작 | 5×1 = **5** | step_146.md, step_153.md 「남은 것」 |
| 14 | 애니메이션 | **Visualize** 2 / 10: Ghost Selected / Ghosting Editor, Create / Update Animation Snapshot | 없음 | 2×2 = **4** | step_145 §3 #15 (변경 없음) |
| 15 | 모델링 | **#89 Quad Draw 남은 것** (overlay 색, Tab+MMB strip, Ctrl+Shift+RMB 메뉴), Insert Edge Loop Auto complete / Fix Quads, Lattice local, nonlinear 근사 | 기능 | 2×2 = **4** | #89, step_144.md |
| 16 | 모델링 | **Mesh / Edit Mesh 정확도**: Connect ≥ 4 점, Automatic "Less distortion", Contour Stretch, Bevel Chamfer off / Mitering, 원시 근사 | 기능 | 2×2 = **4** | step_139*.md (변경 없음) |
| 17 | UI | **Script Editor**: History 0 / 13 (Echo All Commands …), File > Save Script to Shelf / Source Script 회색, Tabs 2 / 6 | 기능 | 2×2 = **4** | step_105, menu_count |
| 18 | UI | **매니퓰레이터 / 링 세부** (step 151): 링 목록 줄 22 vs Maya 20 px, 가운데 원 / dead zone, ❒ 글리프 8 vs 11 px, Shift+RMB 아이콘; 압출 매니퓰레이터에 회전 고리 / world·local 토글 없음, Local Translate X/Y · Local Scale 이 In-View Editor / CB 에 안 보임, 비균일 스케일 근사; 엣지 / 정점 압출 · 베벨은 화살표 하나 | 외형 | 3×1 = **3** | step_151.md 「남은 것」 |
| 19 | UI | **HUD / 상태 줄**: Display > Heads Up Display > Poly Count / Object Details / Selection Details = Blender 장면 통계 오버레이 (`ui/menu_map.py:558,624-625`, Blender 글 모양, Maya 의 Verts / Edges / Faces / Tris / UVs 표 아님); step 151 뒤 상태 줄의 Blender 통계도 사라짐 ("152 에서 볼 것" 이었으나 152 가 안 봄); Frame Rate = Preferences 열기 (`:623`) | 외형 | 3×1 = **3** | step_151.md 「남은 것」 |
| 20 | 기타 | 열기 대화 문구 (Blender "Save changes before closing?"), 두 번째 창의 레이아웃, 도구 설정이 세션 사이에 안 남음 | 외형 | 2×1 = 2 | step_138*.md |
| 21 | 기타 | Undo 세부 (step 147): 옵션 창 Apply 는 따로 undo step 아님; Edit > Undo History 이름 = Maya 메뉴 라벨 (Maya 는 polyCube 같은 명령 이름); HIDDEN 속성은 Preferences 키맵 편집기에서 안 보임 | 외형 | 1×1 = 1 | step_147.md 「남은 것」 |
| 22 | 외형 | 선택된 격자 / 메쉬 밑 Blender 주황 1 px (C), 편집 모드 재생 중 성분 색 캐시, Grid 의 Axes / Thicker off 미측정 · 격자 숫자 없음 | 외형 | 1×1 = 1 | step_149.md, step_152.md 「남은 것」 |
| 23 | FX | FX / Generate / Toon / nHair / nConstraint (0–18 %): Blender 대응 없는 시스템 — notice 만 | 없음 | 1×4 = 4 | step_145 §3 #22 |

검증 / 정리 빚 (Maya 사용자에게 안 보임):

- **5.x**: 5.0.1 / 5.1.2 GUI 전체는 안 돌림 (153 은 5.2.3 GUI); 5.1.2 수동 스윕 한 세션 멈춤 (step 118) 미확정;
  `gui_step129_panel_toolbar` 는 다른 Blender 와 동시에 돌면 흔들림 (step_153.md).
- `docs/compat_5x.md` 의 테마 행 / 「테마 차이」 / 「남은 것」 테마 bullet (:30-31, :108-146, :195-198) 은 step 130 뒤 없는 기능 — 지울 글.
- 코드 정리 이월 (재확인): `ui/outliner.py:9,133-137` 아무도 안 그리는 `allset_outliner_rows` 재빌드, `marking/rmb_items.py:207-208,321`
  옛 VERTEX_PERIMETER / SHELL_BORDER 규칙.
- 열린 이슈 17 개를 0.4.0 릴리스 때 닫기 (§2). 사용자 / Hermes: v0.3.0 초안 릴리스 publish + 스토어 업로드 (HANDOFF step 148).
- `[K]` 동작을 실제 Maya 와 비교 안 함: Quad Draw 클릭 규칙, Symmetrize 클릭 쪽, B-drag 속도, Ctrl+Shift+클릭 셸프 추가 (§4).

## 4. Blindspot (어느 「남은 것」 / 이슈 / backlog 에도 없던 것, grep 확인)

| # | Maya 동작 | 킷 지금 (근거) | F×S |
|---|---|---|---|
| BS1 | **메뉴 항목 Ctrl+Shift+클릭 = 지금 셸프에 추가** (research/maya/shelves.md:17, :86) — Maya 사용자가 셸프를 채우는 기본 방법 | step 146 이 메뉴 항목의 Shift / Ctrl+클릭을 옵션 상자로 씀: `ui/menu_sets.py:677-678` (`any(... SHIFT ... CTRL ...)`) → Ctrl+Shift+클릭은 옵션 창을 엶. 셸프 추가는 셸프 톱니 메뉴의 Add Button / Add Last Command (`ui/shelf.py:357,563`) 뿐. Maya 에서 Shift 만 / Ctrl 만 클릭이 옵션 상자인지도 확인 안 함 [U] | 2×3 = 6 |
| BS2 | **Channel Box 메뉴 전체**: RMB Channels 팝업 (research/maya/channel_box.md:95-121) + **Ctrl+RMB = Edit 팝업** (:35, :124-133) | 킷 팝업 `ALLSET_MT_cb_channels` (`ui/channel_box.py:1301-1325`) 에 Breakdown All, Mute All / Unmute All, Sync Selection in Graph Editor / Timeline, Cut / Copy / Paste Selected, Freeze >, Select Connection, Add to / Remove From Selected Layers 없음; Ctrl+RMB 는 `:1031` (`not (event.shift or event.ctrl or event.alt)`) 로 지나가 Blender 버튼 메뉴 (Insert Keyframe …) 가 뜸 — `ALLSET_MT_cb_edit` (:1374) 은 있는데 거기로 안 감; 채널 칸 밖 RMB (빈 곳) 도 Blender 메뉴 | 3×2 = 6 |
| BS3 | **Hypershade 스와치를 MMB 로 끌어 뷰포트 오브젝트에 놓기 = 할당** (research/maya/workflows/render.md:27) | Browser 는 Properties 버튼 (`ui/hypershade.py:806` Assign Material To Selection 버튼만), 끌어 놓기 코드 없음 (grep "drag" / "drop" 0). step_67.md:80 에 "없음" 으로 적혔으나 step_133 / 145 목록에서 빠짐 → 다시 올림 | 3×2 = 6 |
| BS4 | **#97 처럼 등록됐지만 backlog 에서 빠진 이슈** | #97 은 감사 9 lane A 가 등록했는데 PLAN 「재점검 9차」 Top differences / backlog_146 어디에도 없음 (§3 #7). 다음 backlog 는 `gh issue list` 에서 다시 만들 것 | — |
| BS5 | **HUD Poly Count** (모델러가 늘 켜 둠) | Blender `overlay.show_stats` 토글 (`ui/menu_map.py:558,624-625`) — 글 모양 / 위치 / 내용이 Blender 의 것; step 151 이 상태 줄 통계도 지움 (§3 #19) | 3×1 = 3 |
| BS6 | **"작동" 으로 세는 메뉴가 Blender 창만 엶** (감사 9 BS7 그대로) | 예: Display > Heads Up Display > Frame Rate, Windows > Settings/Preferences > Hotkey Editor → `screen.userpref_show` (`ui/menu_map.py:287-288,623`). 메뉴 작동률 45.5 % (unique) 는 이것들을 포함 | 2×2 = 4 |

확인했고 blindspot 아님: 툴 아이콘 더블클릭 = Tool Settings (`ui/toolbox.py:126-145`, step 129), Ctrl+1 Isolate (`view3d.localview`,
keymap_mapping), Outliner F (`outliner.show_active`), Wireframe on Shaded / X-Ray / Backface Culling (`ui/panel_menus.py:95-102`),
Edit > Repeat / Recent Commands List (`ui/menu_map.py:142-143`), Maya 핫키 468 개 모두 분류 (구현 202 / IC 27 / 해당 없음 171 /
macOS 68, `docs/keymap_mapping.md`).

## 5. 수치 (감사 9 → 지금)

| 수치 | step 145 | 지금 (e26b969) |
|---|---|---|
| 대응표 | 29 / 2 / 0 / 2 | **29 / 2 / 0 / 2** |
| 메뉴 leaves 작동 (unique) | 596 / 1318 (45.2 %) | **600 / 1318 (45.5 %)** (`tools/menu_count.py`) |
| 회색 + notice 없음 | 0 | 0 |
| Graph Editor 메뉴 막대 | 137 / 229 (회색 92) | **145 / 229** (회색 84) |
| 핫키 구현 | 199 | **202** |
| 열린 이슈 | #81–#100 중 열림 19 (#84 닫힘) | 20 개 열림 (#81–#101, #84 닫힘) — 코드로 열린 것은 #81 #89 #97 셋 |

메뉴별 약한 곳 (작동 / 전체): Generate 2 / 50, nHair 2 / 54, nConstraint 0 / 19, Toon 1 / 20, Control 1 / 14, Texturing 1 / 8,
Visualize 2 / 10, Surfaces 8 / 41, Skeleton 13 / 54, Fluids 4 / 25, nCache 3 / 20, Lighting 5 / 14, Fields 14 / 38, Deform 28 / 74,
Mesh Display 15 / 39, Modify 37 / 90, Curves 16 / 36.

## 6. Manual checks 정리 (`docs/manual_checks.md`)

- 전: **582 항목, 79 체크, 503 열림** (step 145 뒤 548 / 78 / 470 에 146–153 이 34 항목 추가, 1 체크).
- 후: **579 항목, 81 체크, 498 열림**.
- **지움 3** (기능이 바뀌어 없는 것):
  - Step 99 「도크 오른쪽 세로 탭 … Blender Item 탭이 네 번째로 생김」 — step 116 에서 도크가 사이드바를 떠나 Properties 영역이 되어
    Item 탭이 생길 수 없고, 세로 탭은 step 142 의 strip (Step 142 항목 둘이 같은 클릭 / Ctrl+A 를 봄).
  - Step 135 WIDTH 「탭 스택 폭 466 / 574 / 672 px」 — step 142 부터 폭은 올라온 탭에 따름 (Channel Box ≈ 277 × scale, AE 480 × scale,
    `toolbox.dock_width(kind=)`); Step 142 항목이 새 폭 / Subdivisions Height / AE 메뉴 줄을 봄.
  - Step 135 「독 위 탭 줄: 손잡이 다음에 탭 세 개」 — step 142 부터 STACK 은 위 탭 줄을 안 그림 (`ui/maya_dock.py:938`
    `draw_handle(layout, context)` 에 `tabs=True` 없음).
- **체크 2** (모든 조건을 GUI 테스트가 확인):
  - Step 136 「회색 항목 (RMB > Time Editor) 위에 마우스 → Help Line 에 notice」 (`gui_step136_items` `s_notice`, `notices.current()`).
  - Step 137 「Translate + Rotate 곡선을 같이 보면 Blender 숫자 그대로」 (`gui_step137_graph_units` `s_mixed_check`).
- **낡은 구절만 고침 9** (항목은 남김): Step 13 비활성화 (내비게이션 — 킷이 더는 안 바꿈), Step 42 설치 (테마 → 없음; "환경설정 >
  Allset" → Add-ons > Maya Workflow Kit), Step 49 / 99 "Maya Density" (step 130 에서 없어짐), Step 53 5.x "Maya 테마 색" → 킷이 그리는
  뷰포트 색, Step 60 스위치의 "테마", Step 125 "File > New 에 템플릿" (step 130: 템플릿을 설치 안 함), Step 134 "Shift+H 의 패널" →
  Alt+W (step 147 뒤 Shift+H 는 패널을 안 엶).
- **체크 안 함 (GUI 테스트는 있지만 일부만)**: Step 147 Ctrl+E / Ctrl+B / IK / Joints 패널 없음 (`gui_step147_hud`; "G 가 반복" 안 봄),
  Step 148 RMB 메뉴 ("선택된 채널" 경우 안 봄) / AE 숫자 (`+=5` 안 봄) / 격자 (구가 아니라 큐브) / 조명 (Intensity 입력 안 봄), Step 150
  Curve Name (Always 만) / Auto Frame (off 경우 안 봄), Step 151 압출 매니퓰레이터 (평면 사각형 / 프리셀렉트 안 봄), Step 144 Insert Edge
  Loop (Esc / RMB 취소 안 봄), Step 134 grid (테마 바꿈 안 봄) / Insert 커서 (D hold · 클릭 안 봄), Step 135 dock (배율 하나), Step 141
  select (항목의 두 번째 경우 안 봄), Step 142 UI (잘림 / » 하위 메뉴 동작 안 봄).
- 그대로 둔 의심 항목 (확인 못 함): Step 9 마킹 메뉴 `[]` → Adjust Last Operation, Step 12 셸프 더블클릭 → Adjust Last Operation,
  Step 51 "길게 누르기 = Option Box → Adjust Last Operation" — step 147 (명령은 등록 안 됨, "redo" 종류만 HUD) 과 step 103 / 146
  (옵션 창) 뒤 기대 결과가 바뀌었을 수 있음. 손으로 한 번 보고 고칠 것.
