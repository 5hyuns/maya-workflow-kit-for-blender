# HANDOFF

## 현재 작업

- Step 206 (UV Editor depth 2, backlog #5, Issue #113) 완료 — `docs/steps/step_206.md`, Maya 측정 `research/maya/re/uv_201.md`
  (mayapy 4 패스 125 경우 + GUI Maya 3 세션). Modify > Cycle (Maya edge id 순서 걷기), Cut/Sew > Split (polyMapCut 부채꼴),
  Create Shell (Grid) (polyUVRectangle: 원점 = 낮은 정점 번호, U = 원점을 가진 첫 면 엣지), Auto Seams (가지치기한 cut graph,
  닫힌 genus 0 = 가장 먼 두 정점 최단 경로 — Maya 와 엣지 수 같음; Unfold3D 정확한 선택은 [U]), UV Editor HUD 셋 (UV Statistics /
  UV Position / Isolated Selection, Maya 공장값 켬), UV Sets Rename / Copy to map1 / map1, Warp Image notice; 메인 UV > Auto Seams ·
  Split UVs 와 UV 마킹 메뉴 Auto Seams 도 같은 명령. UV Editor 136 → **146 / 172**, unique 785. Cycle · Grid mayapy 2e-7 안
  (최대 5e-10), Split NUDGE 안 + UV · 셸 수 같음. 헤드리스 step206 17 / 17, 전체 1981 / 1981, GUI 관련 + 스모크 81 / 81.
  **바로 다음 할 일**: step 207 = backlog #6 「Curves 3」 (Issue #114). 그다음 208 (#115) · 209 (#116).

- **체크포인트 2026-10-26 (/sc:save, 205 후)** — 지금 단계: **205 완료 · 커밋 9d4c1c6** (Fixes #112, push 안 함). 이번 세션에 201 (ac5ea5d,
  감사 15) · 202 (fd1ad61, #109) · 203 (a162a62 Blender 슬롯 + b19ab5b, #110) · 204 (0147e5c, #111) · 205 (9d4c1c6, #112) 커밋. 진행 중인
  레인 · 테스트 없음, 작업 트리 깨끗 (research/ · .impeccable/ 추적 안 함). 숫자: 헤드리스 1964 / 1964, 메뉴 세트 합 922 / 1486 (62.0 %),
  Graph Editor 187 / 229, Dope Sheet 158 / 181, Deform 60 / 74, Constrain 18 / 20.
  **사용자 할 일**: 스토어에 0.4.1 zip 업로드; push 하면 #103–#112 닫힘; 에이전트 worktree 63 개 정리 여부.
  **바로 다음 할 일**: step 206 = backlog #5 「UV Editor depth 2」 (Issue #113) — 측정 레인 (mayapy) + [K] 구현 레인 동시, 그다음 맞춤 레인 +
  GUI 테스트 레인 (step 203–205 방식). 그다음 207 (#114) · 208 (#115) · 209 (#116).

- Step 205 (Deform 2, backlog #4, Issue #112) 완료 — `docs/steps/step_205.md`, Maya 측정 `research/maya/re/deform_205.md`. Tension · Solidify ·
  Sculpt · Morph · Jiggle (GN 디포머, Maya 이름 · INPUTS · AE · 옵션 창 · Paint Weights · Non-Deformer History 에서 남음), UV Pin · Proximity
  Pin, Display / Hide Intermediate Objects, Wrap Add / Remove Influence. mayapy O 경우 모두 1e-4 안 (최대 2.3e-6), Deform 60 / 74, 헤드리스
  1964 / 1964, GUI 관련 44 / 44.
  **바로 다음 할 일**: step 206 = backlog #5 「UV Editor depth 2」 (Issue #113). 그다음 207 (#114) · 208 (#115).

- Step 204 (Animation layers 4, backlog #3, Issue #111) 완료 — `docs/steps/step_204.md`, Maya 측정 `research/maya/re/anim_layers_201.md`.
  Extract / Duplicate (No Animation) / Empty / Delete Empty / Zero·Full Weight and Key, BaseAnimation 선택 시 회색, 레이어 RMB 메뉴,
  Ctrl / Shift 여러 레이어 선택 + Graph Editor 다른 레이어 커브 (그린 읽기 전용) + 그 커브 클릭 = 활성. mayapy 23 / 25 (1.55e-6),
  헤드리스 1918 / 1918, GUI 관련 통과.
  **바로 다음 할 일**: step 205 = backlog #4 「Deform 2」 (Issue #112). 그다음 206 (#113) · 207 (#114).

- Step 203 (Graph Editor depth 3, backlog #2, Issue #110) 완료 — `docs/steps/step_203.md`, Maya 측정 `research/maya/re/graph_editor_201.md`.
  먼저 공용 Blender 슬롯 잠금 `tools/blender_slots.py` (a162a62 「QA: blender slots」, 사용자 결정 10-25: 레인 ≤ 4, Blender ≤ 2).
  List Load / Add (Auto Load 동안 회색) · Pin / Unpin · Show > Attributes / Objects 필터 · Upstream / Hierarchy Below · Change Rotation
  Interp 5 · Key Sync / Peak Removal · Select Curve Nodes. Graph Editor 187 / 229, Dope Sheet 158 / 181. 헤드리스 전체 + GUI 관련 통과.
  **바로 다음 할 일**: step 204 = backlog #3 「Animation layers 4」 (Issue #111). 그다음 205 (#112) · 206 (#113).

- Step 202 (Audit 15 fix batch, backlog #1, Issue #109) 완료 — `docs/steps/step_202.md`, mayapy 명세 `research/maya/re/add_influence_202.md`.
  Non-Deformer History 가 킷 Wire / weight-sum 을 남김, 제약 helper 삭제, All by Type Wires / nCloths / nParticles / nRigids, Add Influence
  Maya 거리 가중치 (mayapy 8.1e-7), Time Slider 높이 UI scale 맞춤 (1.25 현재 칸 ΔE 13.8 → 0.3), CB 메뉴 바 줄바꿈, Outliner 모드 열
  끔 (템플릿 다시 만듦) + 그린 행 정렬. 헤드리스 1867 / 1867, look_compare kit-drawn 12 / 12 (1.0 · 1.25), GUI 관련 통과, dogfood 48 / 48.
  **바로 다음 할 일**: step 203 = backlog #2 「Graph Editor depth 3」 (Issue #110). 그다음 204 (#111) · 205 (#112).

- Step 201 (재점검 15차 = 드라이버 「AUDIT 14」, 감사 — src 변경 없음) 완료 — `docs/steps/step_201.md` (+ `step_201_remaining.md`,
  `step_201_quant.md`), PLAN 「재점검 15차」. 헤드리스 1844 / 1844, dogfood 48 / 48, 콘솔 0. 대응표 30 / 1 / 0 / 2 (91 %), 메뉴 762 / 1318
  (57.8 %), 편집기 메뉴 600 / 914, 옵션 창 164 경로, look_compare kit-drawn 1.0 12 / 12 · 1.25 11 / 12 (Time Slider 현재 칸 회귀).
  backlog 8 개 (steps 202–209) `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json`, 이슈 #109–#116 (마일스톤 0.5.0),
  #108 표 갱신. **사용자 할 일**: 스토어에 0.4.1 zip 업로드; push 하면 #103–#107 닫힘; 에이전트 worktree 63 개 정리 여부.
  **바로 다음 할 일**: step 202 = backlog #1 「Audit 15 fix batch」 (Issue #109) — Delete Non-Deformer History 가 킷 GN 디포머를 굽는 문제,
  제약 helper 고아, All by Type 연결, Add Influence 가중치, UI 1.25 Time Slider 현재 칸, CB "Chann..." · Outliner 모드 열.

- **체크포인트 2026-10-25 (/sc:save, 200 후)** — 지금 단계: **200 완료 · 커밋 0d75f44** (Fixes #107, push 안 함). 197 (beb75af, #104),
  198 (845230b, #105), 199 (51bc287, #106) 도 커밋됨 → backlog 8 (steps 193–200) 전부 끝. 진행 중인 레인 · 테스트 없음, 작업 트리
  깨끗 (research/ · .impeccable/ 추적 안 함). 숫자: 헤드리스 1844 / 1844 (4.5.4 · 5.0.1 · 5.1.2 · 5.2.3), 메뉴 unique 762 / 1318,
  Graph Editor 167 / 229, Skin 25 / 28, Constrain 16 / 20. 이슈 #104–#107 은 push 해야 닫힘.
  **사용자 할 일**: 스토어에 0.4.1 zip 업로드.
  **바로 다음 할 일**: 새 감사 (재점검 15차: dogfood · 대응표 · 메뉴 수 → 새 backlog 단계마다 GitHub 이슈, #108 표 / Planned next
  갱신) 또는 0.5.0 출시 준비 (그때만 GUI 전체 묶음).

- Step 200 (Blender 5.x test pass 2, backlog #8 = 마지막, Issue #107) 완료 — `docs/steps/step_200.md`, `docs/compat_5x.md`
  「step 200」. 헤드리스 전체 4.5.4 / 5.0.1 / 5.1.2 / 5.2.3 모두 **1844 / 1844** (첫 실행 1841 / 1840 / 1834). 고친 것 (compat):
  5.2 GN 모디파이어 입력 (`gn_input_*`, Wire), 5.x 메뉴 바 첫 메뉴 위치 (`MENU_BAR_LEAD_UNITS`, ❒ 클릭), `Bone.select` 직접
  읽기 2 곳 → shim. GUI 5.2.3 step183 / 187 28 / 28.
  **바로 다음 할 일**: backlog 8 (steps 193–200) 끝 — 새 감사 (재점검 15차) 로 새 backlog + 이슈 (#108 표 갱신), 또는 0.5.0 출시 준비.

- Step 199 (Skin and Constrain tools 2, backlog #7, Issue #106) 완료 — `docs/steps/step_199.md`, mayapy 명세
  `research/maya/re/skin_tools_199.md` · `constrain_199.md`. Move Weights to Influences, Normalize 세 모드 (Post 포함), Weight Maps
  내보내기 / 가져오기, Substitute Geometry, Bake Deformation, Constrain Normal / Tangent / Remove Target / Set Rest Position /
  Modify Constrained Axis + 옵션 창 5. Skin 19 → 25 / 28, Constrain 11 → 16 / 20, unique 762. 헤드리스 1841 / 1841, GUI 관련 100 / 100.
  **바로 다음 할 일**: step 200 = backlog #8 「Blender 5.x test pass 2」 (Issue #107) — backlog 마지막.

- Step 198 (Graph Editor depth 2, backlog #6, Issue #105) 완료 — `docs/steps/step_198.md`, Maya 측정
  `research/maya/re/graph_editor_193.md` (GUI Maya QTest Retime 드래그 + mayapy 가중 탄젠트 / 버퍼). Retime Tool (Graph Editor + Dope
  Sheet), 버퍼 커브 Snapshot / Swap / Show, Weighted / Non-weighted / Default Tangent Weight / Lock·Free Tangent Length, Select
  Unsnapped, Set Curve Colors..., Add Key Tool, 메인 패널 Graph Editor 사이드바 닫기. Graph Editor 155 → 167 / 229, Dope Sheet 130 → 139.
  헤드리스 1807 / 1807, GUI 관련 42 / 42 + 스모크 45 / 45. 남은 것: Pin / Load Selected.
  **바로 다음 할 일**: step 199 = backlog #7 「Skin and Constrain tools 2」 (Issue #106). 그다음 200 (#107).

- Step 197 (Small Maya polish batch, backlog #5, Issue #104) 완료 — `docs/steps/step_197.md`. 핫박스 / 마킹 메뉴가 떠 있는 동안
  in-view 메시지 · In-View Editor 안 그림, 결과 칸의 옛 `Undo: …` 를 새 명령이 지움 (F8 포함), AE 탭 · 메뉴 · 버튼 줄을 잰 폭으로 줄바꿈
  (잘린 글자 0), Mesh > Cleanup… = Maya 명령 `allset.poly_cleanup` + Cleanup Options 창, character set 옛 문구 제거 + Relationship
  Editors > Character Sets 팝업 + Graph Editor Show > Objects > Characters (kit outliner CHARACTER 줄), NURBS CVs / Hulls 는 측정상
  Blender 에 스위치가 없어 회색 유지 (delegated). 헤드리스 1778 / 1778, GUI 관련 138 / 138, dogfood 48 / 48, 메뉴 unique 751.
  **바로 다음 할 일**: step 198 = backlog #6 「Graph Editor depth 2」 (Issue #105). 그다음 199 (#106) · 200 (#107).

- **체크포인트 2026-10-25 (/sc:save, 196 후)** — 지금 단계: **196 완료 · 커밋 38a88d1** (Fixes #103, push 안 함). 193 (761a1aa),
  194 (8b78985), 195 (586eda2, #102 손으로 닫음) 도 커밋됨. 진행 중인 레인 · 테스트 없음, 작업 트리 깨끗 (research/ · .impeccable/ 추적 안 함).
  **사용자 할 일**: 스토어에 0.4.1 zip 업로드.
  **바로 다음 할 일**: step 197 = backlog #5 「Small Maya polish batch」 (Issue #104) — 핫박스를 덮는 in-view 메시지 · In-View Editor,
  결과 칸 "Undo:" 고정, AE 탭 잘림, Mesh > Cleanup… ▸, 옛 "no character sets" 문구, NURBS CVs / Hulls 회색. 그다음 198 (#105) · 199 (#106) · 200 (#107).

- Step 196 (Maya option windows for primitives and character sets, backlog #4, Issue #103) 완료 — `docs/steps/step_196.md`.
  새 Maya 옵션 창 34 개 (`option_windows_prims.py` 19: Polygon 11 + NURBS 8, `option_windows_misc196.py` 15: Character Set, Curves, arc,
  Merge UVs, Contour Stretch, Preferred Angle, Add Influence), Curves > Smooth / Merge UVs 그냥 클릭도 Maya 규칙. window 120 → 158,
  redo 127 → 104, generic 34 → 19. 헤드리스 1763 + 고친 파일 34 / 34, GUI 관련 65 / 65. **사용자 할 일**: 스토어에 0.4.1 zip 업로드.
  **바로 다음 할 일**: step 197 = backlog #5 「Small Maya polish batch」 (Issue #104).

- Step 195 (Channel Box and Time Slider look, backlog #3) 완료 — `docs/steps/step_195.md`. dock 를 Maya #444444 로 (ADDITIVE 한 겹,
  Layer Editor 목록 몸통 제외, 설정 `maya_dock_colors`), shape 이름 줄 필드, Time Slider 현재 칸 #525252 (18.4 %). look_compare 1.0
  kit-drawn 12 / 12 (cb_bg 6.5 → 0.0), 헤드리스 1740 / 1740, GUI 관련 75 / 75, dogfood 48 / 48.
  **바로 다음 할 일**: step 196 = backlog #4 「Maya option windows for primitives and character sets」.

- Step 194 (Animation layers: keys stay visible, backlog #2) 완료 — `docs/steps/step_194.md`, Maya 측정
  `research/maya/re/anim_layers_193.md`. 레이어 오브젝트의 활성 액션 = 선택 레이어 strip 액션 (influence 0, 평가 차이 0) → Graph
  Editor / Dope Sheet / Time Slider / CB 가 Maya 처럼 선택 레이어를 보임; CB 레이어 멤버 = LAYERED; Zero Key Layer · Merge Layers.
  헤드리스 1736 / 1736, GUI 관련 33 / 33.
  **바로 다음 할 일**: step 195 = backlog #3 「Channel Box and Time Slider look」 (CB teal 레이어 바탕도).

- Step 193 (RMB flick works when the menu is lifted, backlog #1) 완료 — `docs/steps/step_193.md`. 마킹 메뉴 링은 언제나 누른 점
  (`engine.fit_ring` 의 step 184 메뉴 전체 들어올리기 지움), 목록이 링 아래에 안 들어가면 목록만 링 옆 한 열. 헤드리스 1730 / 1730,
  GUI 관련 10 파일 103 / 103, dogfood 48 / 48 (UI 1.25 · 1.0).
  **바로 다음 할 일**: step 194 = backlog #2 「Animation layers: keys stay visible」 (먼저 GUI Maya 측정).

- Step 192 (재점검 14차 = 사용자 지시의 「재점검 13차」, 감사 — src 변경 없음) 완료 — `docs/steps/step_192.md` (+ `step_192_remaining.md`,
  `step_192_quant.md`), PLAN 「재점검 14차」. 헤드리스 1731 / 1731, dogfood 47 / 48 (RMB 서쪽 flick → Vertex 실패 = step 184 lift 회귀,
  처음 실행은 연쇄로 43 / 48), 추가 세션 2 / 2, 콘솔 0. 대응표 30 / 1 / 0 / 2 (91 %), 메뉴 750 / 1318 (56.9 %), 옵션 창 120 경로,
  look_compare 뷰포트 20 / 20. backlog 8 개 (steps 193–200) `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json`.
  **바로 다음 할 일**: step 193 = backlog #1 「RMB flick works when the menu is lifted」 (계획 먼저 `docs/steps/step_193.md`).
  남은 정리: 옛 worktree 2 개 (`.claude/worktrees/agent-a1d69614…`, `agent-aed8f880…`, 내용 반영됨, 삭제는 훅이 막음).

- Step 191 (0.4.1 출시 준비) 완료 — `docs/steps/step_191.md`. version 0.4.1, CHANGELOG [0.4.1], `release_notes_0.4.1.md`;
  release_check 4.5.4 / 5.2.2 각 14 PASS, 헤드리스 전체 1731 / 1731, GUI 전체 묶음 한 번 (15 덩어리) → 킷 버그 2 개 고침 (UV / Image Alt+RMB
  줌 = step 177 회귀, 위로 그린 마킹 메뉴의 그려지기 전 flick) + 옛 기대 GUI 테스트 갱신. master push, 태그 v0.4.1, 초안 릴리스.
  **바로 다음 할 일**: Hermes 가 초안 릴리스 v0.4.1 publish · 스토어 업로드; 개발은 새 감사 (재점검 14차) 로 새 backlog (step 192).

- Step 190 (Seven Polygon Primitives, backlog_183.json #8 = 마지막) 완료 — `docs/steps/step_190.md`, mayapy
  `research/maya/re/poly_prims_185.md`. Pipe / Helix / Gear / Soccer Ball (`operators/prim_shapes_more.py`) + Super Ellipse /
  Spherical Harmonics / Ultra Shape (`operators/prim_supershape.py`, polySuperShape 하나) 를 Maya 와 같은 정점 / 면 순서 / UV /
  딱딱한 엣지로 (순수 python 비교 89 / 90 + 253 / 253), `prim_history` 로 생성 + INPUTS 편집. Create 57 → 67 %.
  헤드리스 전체 1730 / 1730, GUI step190 2 / 2 + 샷.
  **바로 다음 할 일**: backlog_183 끝 — 새 감사 (재점검 14차) 로 새 backlog (step 191).

- Step 189 (Mesh Display and greyed twins, backlog_183.json #7) 완료 — `docs/steps/step_189.md`, mayapy
  `research/maya/re/mesh_display_184.md` (노멀 + Construction History) / `mesh_display_184_colors.md`. Mesh Display 15 → 25 / 39
  (64 %: Set Vertex Normal, 선택만 Lock / Unlock, Maya 거리 Average, Set to Face, Apply Color, Rename / Modify Current Set,
  색 키, Prelight + bake sets, Select Shared Instances), `menu_consistency` runtime 별칭 (메인 UV > Delete UVs, nHair Smooth /
  Straighten 연결 → 0), 패널 Show IK Handles / Image Planes, Insert Isoparms Maya 창, Status Line Construction History 실제 토글.
  헤드리스 전체 1727 / 1727, GUI step177 9 / 9 + step189 3 / 3.
  **바로 다음 할 일**: 190 Seven Polygon Primitives (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_183.json`
  8 번째 = 마지막: Pipe, Helix, Gear, Soccer Ball, Super Ellipse, Spherical Harmonics, Ultra Shape — mayapy 측정,
  `operators/prim_shapes.py` / `prim_history.KIND_NODES`), 그 뒤 새 감사 (재점검 14차).

- **체크포인트 2026-10-25 (/sc:save, 188 후)** — 지금 단계: **188 완료 · 커밋됨** (`71ad1bc`). 185 (`cb2bacb`), 186 (`bff9a3b`),
  187 (`c724160`), 188 모두 커밋; push 안 함. 진행 중인 레인 · 테스트 없음, 작업 트리 깨끗 (research/ · .impeccable/ 추적 안 함).
  헤드리스 전체 1707 / 1707 (188 끝), GUI 는 단계별 파일만.
  **바로 다음 할 일**: 189 Mesh Display and greyed twins (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_183.json`
  7 번째: Mesh Display 15 / 39 — Set Vertex Normal, Lock / Unlock / Average Normals 등 + 회색 쌍둥이), 그 뒤 190 Seven Polygon
  Primitives (8 번째 = backlog_183 마지막).

- Step 188 (Animation layer follow-ups, backlog_183.json #6) 완료 — `docs/steps/step_188.md`, mayapy `research/maya/re/anim_layers_188.md`.
  kit Auto Key 가 레이어 오브젝트를 Maya 처럼 (선택 레이어에 키가 있는 속성만, 푼 값), Channels > Add to / Remove From Selected Layers
  (속성 멤버 `allset_layer_attrs`, 비멤버 키 = Base), Relationship Editors > Animation Layers = Layer Editor Anim 탭. 헤드리스 1707 / 1707,
  GUI step180 · 158 14 / 14.
  **바로 다음 할 일**: 189 Mesh Display and greyed twins (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_183.json`
  7 번째).

- Step 187 (Character Sets on Keying Sets, backlog_183.json #5) 완료 — `docs/steps/step_187.md`, Maya 측정
  `research/maya/re/character_sets_183.md` (mayapy + GUI Maya 2 회). 모든 Keying Set = kit character set (current = active),
  S = current 캐릭터 멤버 키, Create / Subcharacter / Add / Remove / Merge / Select / Set Current / AE 팝업, Time Slider 드롭다운.
  Key 54 → 73 %, Control 7 → 64 %, unique 730. 헤드리스 1703 / 1703, GUI step187 4 / 4 (+ 56 · 73 · 180 26 / 26).
  **바로 다음 할 일**: 188 Animation layer follow-ups (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_183.json`
  6 번째).

- Step 186 (Time Slider ticks and playhead, backlog_183.json #4) 완료 — `docs/steps/step_186.md`, Maya 측정
  `research/maya/re/time_slider_186.md` (GUI Maya 43 경우 + 북마크 · 키). Maya 레이아웃 Time Slider 를 kit 이 Maya 자로 그림
  (`ui/time_slider._draw_ruler`: 배경, step 눈금 + 회색 라벨, 흰 25 % 현재 칸 + 번호, 북마크 띠, 키 = 눈금 자리). Blender 의 파란 현재
  프레임 상자는 C overlay 라 못 숨김 (기록). step 규칙 32 / 43 일치 [U]. 헤드리스 1696 / 1696, GUI step56 · 73 17 / 17.
  **바로 다음 할 일**: 187 Character Sets on Keying Sets (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_183.json`
  5 번째).

- Step 185 (Selected edges and manipulator look, backlog_183.json #3) 완료 — `docs/steps/step_185.md`. 「두꺼운 하늘색」 = Blender 의
  sharp 엣지 색 3 px (kit 큐브는 모든 엣지 sharp) → Maya 레이아웃 뷰에서 `show_edge_sharp` 도 끔, 와이어 1.5 px · bias 0.002, 선택 엣지
  2 px · bias 0.003; manipulator 평면 0.52–0.68 (Maya 02 측정) 테두리 + 채움, 활성 / 가운데 #fdff88 (축 활성 때 가운데 #64dcff).
  look_compare viewport 20 / 20 (1.0 · 1.25, 새 flank / area 샘플은 옛 kit 에서 ✗), 헤드리스 1693 / 1693.
  **바로 다음 할 일**: 186 Time Slider ticks and playhead (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_183.json`
  4 번째; 이전 메모의 `backlog.json` 경로는 `backlog_183.json` 이 맞음).

- **체크포인트 2026-10-25 (/sc:save, 184 후)** — 지금 단계: **184 완료 · 커밋됨** (`aa66c56`). 181 (`326f12f`), 182 재점검 13차
  (`3fad2f5`), 183 (`8b34806`, Fixes #82), 184 모두 커밋; push 안 함. 진행 중인 레인 · 테스트 없음, 작업 트리 깨끗 (research/ 추적 안 함).
  헤드리스 전체 1690 / 1690 (184 끝), GUI 는 단계별 파일만.
  **바로 다음 할 일**: 185 Selected edges and manipulator look (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json`
  3 번째: `ui/component_colors.py` 선택 edge, `ui/manipulator.py` 평면 핸들 · 가운데 색, look_data 샘플), 그 뒤 186–190.

- Step 184 (RMB list under the ring, backlog.json #2) 완료 — `docs/steps/step_184.md`, Maya 측정 `research/maya/re/rmb_list_184.md`:
  Maya 는 목록을 자르지도 옆으로 옮기지도 않고 메뉴 전체를 위로 그림 → `marking/engine.py` `lift_up` / `fit_ring` (창이 경계). 헤드리스 마킹
  76 / 76, GUI 관련 통과 (65 + 고친 27).
  **바로 다음 할 일**: 185 Selected edges and manipulator look (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 3 번째).

- Step 183 (Option box click opens the window, backlog.json #1, #82) 완료 — `docs/steps/step_183.md`, `research/blender/menu_click_183.md`.
  메뉴 바에서 연 Maya 메뉴 (와 서브메뉴) 에서 ❒ 클릭 = 옵션 창 (`ui/option_click.py`: execute 안 INVOKE 로 클릭 x, kit 메뉴 배치 모델로
  ❒ 칸), 라벨 클릭 = 명령; 핫박스 · 마킹 · 편집기 메뉴는 hold 그대로. GUI step183 24 / 24 (UI 1.0 · 1.25), 관련 GUI 61 / 61.
  **바로 다음 할 일**: 184 RMB list under the ring (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 2 번째).

- Step 182 (재점검 13차 = 사용자 지시의 「재점검 12차」) 완료 — `docs/steps/step_182.md` (+ `_remaining.md`, `_quant.md`), PLAN
  「재점검 13차」. 헤드리스 1683 / 1683, dogfood 48 / 48 (콘솔 오류 0), 메뉴 714 / 1318, 대응표 30 / 1 / 0 / 2, look_compare 뷰포트 12 / 12.
  **바로 다음 할 일**: backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 8 개 = steps 183–190 (첫째: Option box
  click opens the window, #82).

- Step 181 (Surfaces basics, backlog_174 #8 = 마지막) 완료 — `docs/steps/step_181.md`. Maya 측정 (`research/maya/re/surfaces_181.md/.json`,
  97 경우) + Blender 프로브 (`research/blender/nurbs_surface_181.md`): Maya NURBS 표면 = Blender 레거시 NURBS 표면 (균일 = Endpoint / Cyclic
  정확, 비균일 = Bezier 분해). `operators/surfaces_math.py` (bpy 없음, mayapy 대비 ≤ 1.2e-7) + `operators/surfaces_maya.py` (Loft, Revolve,
  Extrude, Birail 1, Boundary / Square, Attach, Detach, Insert Isoparms, Duplicate NURBS Patch, Reverse, Rebuild) + Maya 옵션 창 10
  (`operators/option_windows_surfaces.py`). Surfaces 메뉴 8 → **15 / 41**. 헤드리스 1683 / 1683, GUI step181 10 / 10 (+ 관련 50 / 50).
  **바로 다음 할 일**: backlog_174 끝 — 새 감사 (재점검 13차) 로 새 backlog (step 182).

- **체크포인트 2026-10-25 (/sc:save, 180 후)** — 지금 단계: **180 완료 · 커밋됨** (`f8113e7`). 176 (`722fa48`), 177 (`d462e16`),
  178 (`09b2d0a`), 179 (`b4fb15d`), 180 모두 커밋; 173–180 은 push 안 함. 진행 중인 레인 · 테스트 없음, 작업 트리 깨끗 (research/ 는 추적 안 함).
  헤드리스 전체 1658 / 1658 (180 끝), GUI 는 단계별 파일만 (전체 묶음 안 돌림; `gui_step129_panel_toolbar` 3 실패는 전부터, git stash 로 확인).
  **바로 다음 할 일**: 181 Surfaces basics (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_174.json` 8 번째 = 마지막:
  Surfaces 8 / 41, mayapy 측정 `research/maya/re/surfaces_181.md` — Loft, Planar, …), 그 뒤 새 감사 (재점검 13차) 로 새 backlog.

- Step 180 (Animation Layers on NLA, backlog_174 #7) 완료 — `docs/steps/step_180.md`. Maya 측정 (`research/maya/re/anim_layers_180.md`) +
  Blender 프로브: NLA COMBINE / REPLACE / influence = Maya Additive / Override / weight (4e-6). `operators/anim_layers.py` (레이어 목록 →
  NLA 트랙, 선택 레이어 키 = Maya 식 역산), Layer Editor Anim 탭 (Lock / Solo / Mute, Weight, Layers 메뉴), Maya Anim 탭 캡처
  `research/maya/screens/anim180/`. 헤드리스 1658 / 1658, GUI step180 9 / 9.
  **바로 다음 할 일**: 181 Surfaces basics (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_174.json` 8 번째 = 마지막),
  그 뒤 새 감사 (재점검 13차).

- Step 179 (Light Linking, backlog_174 #6) 완료 — `docs/steps/step_179.md`. Lighting/Shading 의 Make / Break Light · Shadow Links,
  Select Objects / Lights 4 개, Light Linking Editor (kit 팝오버) = Blender light linking 컬렉션 (`operators/light_links.py`,
  `ui/light_link_editor.py`; Maya mayapy 규칙 `research/maya/re/light_links_179.md`). Lighting/Shading 5 → 13 / 14. 헤드리스 1653 / 1653,
  Cycles 프로브 (끊은 큐브 0.004), GUI step179 3 / 3.
  **바로 다음 할 일**: 180 Animation Layers on NLA (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_174.json`
  7 번째), 그 뒤 181 Surfaces.

- Step 178 (UV Editor finish, backlog_174 #5) 완료 — `docs/steps/step_178.md`. UV Editor 메뉴 118 → **136 / 172**: Modify 6 개
  (Map Border, Straighten Border, Match Grid, Layout Along, Stack Similar Shells, Distribute UVs — mayapy 대비 최대 2e-7,
  `operators/uv_modify.py`), Select / Edit / View 12 개 (Back- / Front-Facing, Texture Borders, Non-Overlapping, Unmapped,
  Filter Connected / Contained, To Connected Faces, Unpin All, Isolate Add / Remove / Remove All — `operators/uv_select_178.py`,
  `ui/uv_display.py`). Symmetrize 는 Maya 에서 측정 안 돼 notice. 헤드리스 1649 / 1649, GUI step178 5 / 5.
  **바로 다음 할 일**: 179 Light Linking (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_174.json` 6 번째),
  그 뒤 180 Animation Layers, 181 Surfaces.

- Step 177 (Panel menus honesty and twins, backlog_174 #4) 완료 — `docs/steps/step_177.md`. 패널 메뉴 / 툴바 / Status Line 회색이
  이제 `tools/menu_count.py` (패널 줄 3 개), notice 규칙 (`notices.PANEL_MENU` 60, 회색 notice 없음 0), `tools/menu_consistency.py`
  (0 쌍) 안 — 데이터 `ui/panel_menu_data.py`. 연결: Center View of Selection (Maya viewFit -c mayapy 측정), Camera Attribute
  Editor / Camera Attributes (+ persp 팝오버), Tumble / Track / Dolly Tool (`ui/camera_tools.py`), Grease Pencil Tool. 헤드리스
  1628 / 1628, GUI step177 9 / 9.
  **바로 다음 할 일**: 178 UV Editor finish (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_174.json` 5 번째:
  UV Editor 메뉴 118 / 172, mayapy 측정), 그 뒤 179 Light Linking, 180 Animation Layers, 181 Surfaces.

- Step 176 (Selected-face look and dogfood fixes, backlog_174 #3) 완료 — `docs/steps/step_176.md`. 선택 면 주황 = Blender overlay
  `show_faces` 면 강조가 kit stipple 아래에 깔린 것 (화면 픽셀로 확인) → Maya 레이아웃 뷰에서 kit 이 그리는 동안 끔
  (`ui/component_colors.py`, 뷰 데이터만), look_compare viewport **12 / 12** (ΔE 40.5 → 2.3). G1 = kit 버그 아님 (dogfood 순서에
  Alt+Shift+D = Maya Delete History 가 polyCube1 을 지움; GUI 테스트로 남김). G2 = Ctrl+Z / Shift+Z 뒤 결과 칸 `Undo: <명령>` /
  `Redo: <명령>` (Maya GUI 측정 `research/maya/re/undo_result_176.md`, `command_line/undo_text.py`). 네 뷰 이름표 top -Y / front -Z /
  side -X. 헤드리스 1621 / 1621, 관련 GUI 통과.
  **바로 다음 할 일**: 177 Panel menus honesty and twins (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_174.json`
  4 번째: `ui/panel_menus.py` 회색 28 + `ui/panel_toolbar.py` 8), 그 뒤 178 UV Editor, 179 Light Linking, 180 Animation Layers, 181 Surfaces.

- **체크포인트 2026-10-25 (/sc:save, 175 후)** — 지금 단계: **175 완료 · 커밋됨** (`77a5263`). 171 (`801a18d`), 172 0.4.0 출시
  (`c8d006c`, push · 태그 v0.4.0 · 초안 릴리스 — Hermes 가 publish), 173 재점검 12차 (`b07f9a7`), 174 (`41e4715`), 175 모두 커밋;
  173–175 는 push 안 함 (origin 보다 3 개 앞). 진행 중인 레인 · 테스트 없음. 헤드리스 전체 1611 / 1611 (175 끝), GUI 는 단계별 파일만.
  **바로 다음 할 일**: 176 Selected-face look and dogfood fixes (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json`
  3 번째: look_compare 선택 면 ΔE 40.5, dogfood G1 INPUTS polyCube1 사라짐 · G2 Undo 뒤 결과 칸 · 네 뷰 Maya 축 이름표), 그 뒤 177–181
  (패널 메뉴, UV Editor, Light Linking, Animation Layers, Surfaces).

- Step 175 (Repeat Last for Maya commands, backlog #2) 완료 — `docs/steps/step_175.md`. Maya GUI 측정
  `research/maya/re/repeat_175.md`. `operators/repeat_maya.py`: G / Edit > Repeat / Recent Commands 가 메뉴 · 셸프 · 마킹 · 옵션 창
  명령도 반복. 헤드리스 1611 / 1611, GUI step175 5 / 5 + 관련 통과.
  **바로 다음 할 일**: 176 Selected-face look and dogfood fixes (backlog.json 3 번째).

- Step 174 (Component mode keeps the transform tool, backlog #1) 완료 — `docs/steps/step_174.md`. Maya GUI 측정
  `research/maya/re/tool_modes_174.md` (Q/W/E/R 유지, T → select). `operators/tool_keys.py` 모드 전환 뒤 도구 넘김. GUI step174
  21 / 21 (수정 전 8 실패), 관련 GUI 통과, 헤드리스 1603 / 1603.
  **바로 다음 할 일**: 175 Repeat Last for Maya commands (G) (backlog.json 2 번째).

- Step 173 (재점검 12차, 사용자 지시의 11차) 완료 — `docs/steps/step_173.md` + `step_173_remaining.md` / `step_173_quant.md`, PLAN
  「재점검 12차」. 헤드리스 1600 / 1600, dogfood 48 / 48 (콘솔 오류 0), 대응표 30 / 1 / 0 / 2 (91 %), 메뉴 699 / 1318 (53.0 %), 옵션 창
  104 경로, look_compare 그대로 (선택 면 ΔE 40.5). 새 차이: 컴포넌트 모드 → Select 도구, G 가 메뉴 명령 반복 안 함, 패널 메뉴 회색 36.
  **바로 다음 할 일**: backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 8 개 = steps 174–181 (첫째: 컴포넌트
  모드에서 변환 도구 유지).

- Step 172 (0.4.0 출시 준비) 완료 — `docs/steps/step_172.md`. version 0.4.0, CHANGELOG, `release_notes_0.4.0.md`; release_check
  4.5.4 / 5.2.2 각 14 PASS, 헤드리스 1600 / 1600, GUI 전체 1827 검사 (오래된 RMB 목록 테스트 2 파일 고침). master push,
  #81–#101 닫힘, #89 → 0.5.0, 태그 v0.4.0, 초안 릴리스 + 업로드 폴더.
  **바로 다음 할 일**: 새 감사 (재점검 12차).

- Step 171 (Animation Snapshot / ghosting, backlog_164 #8 = 마지막) 완료 — `docs/steps/step_171.md`. 측정
  `research/maya/re/visualize_171.md` (mayapy + GUI 캡처). `operators/anim_snapshot.py` (snapshot1Group / transform1_k,
  Fast / Slow / On demand), `ui/ghosting.py` (Ghost / Unghost, Maya 프레임 규칙 · 색 · 불투명도), Animation Snapshot
  Options / Ghosting Editor 창. Visualize 2 → 8 / 10 (80 %). 헤드리스 1600 / 1600, GUI step171 13/13 + 관련 17/17.
  **바로 다음 할 일**: backlog_164 끝 → 새 감사 (재점검 12차).

- **체크포인트 2026-10-25 (/sc:save, 170 후)** — 지금 단계: **170 완료 · 커밋됨** (`5bc798e`). 168 (`e899ecb`), 169 (`d063740`),
  170 (`bd0fb00` WIP + `5bc798e`) 모두 커밋, 진행 중인 레인 · 테스트 없음, push 안 함. 헤드리스 전체 1586 / 1586 (170 끝),
  GUI 는 단계별 파일만 (전체 묶음 안 돌림).
  **바로 다음 할 일**: 171 Animation Snapshot / Ghosting (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_164.json`
  8 번째 = 마지막 항목; Visualize 메뉴 20 %), 그 뒤 새 감사 (재점검 12차). 알려진 것: `gui_step52_hotbox_rmb` "list under the ring"
  2 실패 (step 161 보류 건), `gui_step129_panel_toolbar` 머리 폭 의존 실패, GUI 시뮬레이션은 Shift / Ctrl 드래그를 못 만든다
  (step 170, CLAUDE.md).

- Step 170 (Selection modifiers outside the 3D View, backlog_164 #7) 완료 — `docs/steps/step_170.md`. GUI Maya QTest 실측
  `research/maya/re/select_mods_170.md` (Graph Editor: 선택된 키 클릭 = 유지, Ctrl 클릭 = 일반 클릭, Shift 박스 = 토글;
  Dope Sheet / UV: 토글 / 해제 / 추가; Outliner: Shift = 범위, Ctrl = 토글). `operators/select_2d.py` 첫 자리 PASS_THROUGH
  연산자 + 키맵 props, README 대응표 행 Done. 헤드리스 1586 / 1586, GUI step170 10/10 + step86 10/10.
  **바로 다음 할 일**: 171 Animation Snapshot / Ghosting (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_164.json`
  8 번째 = 마지막 항목), 그 뒤 새 감사 (재점검 12차).

- Step 169 (Deform completion, backlog_164 #6) 완료 — `docs/steps/step_169.md`. mayapy 측정 `research/maya/re/deform_169.md`.
  Wire = 킷 디포머 (Geometry Nodes `wire1` + `curve1BaseWire`, Maya 규칙 그대로: mayapy 대비 최대 1.03e-5), Dropoff
  Locator, Wire > Add / Remove / Reset / Show Base / Parent Base, ShrinkWrap 대상 편집, Lattice Reset / Remove Tweaks,
  Prune Membership, Point On Curve, Paint Weights 상자 10 = Paint Attributes Tool 창. Deform 41 → 65 %, generic 9 → 0,
  dead 20 → 12, 옵션 상자 window 103. 헤드리스 1579 / 1579, GUI step169 + step144_deform 13/13.
  **바로 다음 할 일**: 170 3D View 밖 선택 수정키 (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_164.json`
  7 번째 항목), 그 뒤 171 Animation Snapshot / Ghosting.

- Step 168 (Modify menu and Smooth Mesh Preview to Polygons, backlog_164 #5) 완료 — `docs/steps/step_168.md`. mayapy 측정
  `research/maya/re/modify_168.md`. Smooth Mesh Preview to Polygons = 킷 preview modifier 만 적용 (`allset.smooth_to_polygons`,
  skinCluster1 유지, 면 × 4^level), Default Object Manipulator 5 + Show Manipulator Tool, Align Tool (팝업), Position Along
  Curve (mayapy 값 일치), Geometry to Bounding Box + Maya 옵션 창, Evaluate Nodes 체크 항목 9 + Evaluate / Ignore All
  (`Scene.allset_eval`). Modify 41 → 62 %, 옵션 상자 window 86 (Modify 회귀 0), 헤드리스 1566 / 1566, GUI step168 + 관련 2 파일 14/14.
  **바로 다음 할 일**: 169 Deform completion (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_164.json`
  6 번째 항목), 그 뒤 170 3D View 밖 선택 수정키, 171 Animation Snapshot / Ghosting.

- **체크포인트 2026-10-25 (/sc:save, 167 후)** — 지금 단계: **167 완료 · 커밋됨** (`7078c2a`). 165 (`a00f207`), 166 (`f0873e0`),
  167 (`7078c2a`) 모두 커밋, 작업 트리 깨끗, 진행 중인 레인 · 테스트 없음, push 안 함. 헤드리스 전체 1554 / 1554 (167 끝).
  **바로 다음 할 일**: 168 Modify menu and Smooth Mesh Preview to Polygons (backlog
  `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_164.json` 5 번째 항목), 그 뒤 169 Deform, 170 3D View 밖 선택 수정키,
  171 Animation Snapshot / Ghosting. 알려진 것: `gui_step52_hotbox_rmb` "list under the ring" 2 실패 (step 161 RMB 목록 위치 판단
  보류와 같은 건), `gui_step129_panel_toolbar` 머리 폭 의존 실패.

- Step 167 (Shelf double-click and overflow, backlog_164 #4) 완료 — `docs/steps/step_167.md`. Maya 측정
  `research/maya/re/shelf_overflow_167.md` (셸프는 줄로 넘김 + 12 px 세로 스크롤 막대, 휠 = 한 줄). 더블클릭 = 버튼의 옵션
  상자 (`allset.menu_option_box`, 첫 클릭은 한 번 실행), 셸프 줄 넘김 + ▲▼ + 휠 (`ui/shelf.py`), 셸프 줄의 navigate gizmo 끔
  (템플릿 재생성). 헤드리스 1554 / 1554, GUI step167 9/9 + 관련 5 파일 40/40.
  **바로 다음 할 일**: 168 Modify menu and Smooth Mesh Preview to Polygons (backlog
  `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_164.json` 5 번째 항목), 그 뒤 169 Deform, 170 3D View 밖 선택 수정키.

- Step 166 (Menu consistency, backlog_164 #3) 완료 — `docs/steps/step_166.md`. `tools/menu_consistency.py` (이름 + Maya 명령이
  같은데 한쪽만 회색인 항목: 10 → 0), `menu_map.TWINS`, Dope Sheet Curves 명령 = Graph Editor 명령 (`allset.dope_graph_op`),
  Dope Sheet Auto Frame (`dope_auto_frame`), Select / Delete All by Type > IK Handles / Clusters (`operators/by_type.py`).
  Dope Sheet 124 → 130, UV Editor 110 → 118. 헤드리스 1548 / 1548, GUI step166 7/7 + 관련 5 파일 32/32.
  **바로 다음 할 일**: 167 Shelf double-click and overflow (backlog
  `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_164.json` 4 번째 항목), 그 뒤 168 Modify + Smooth Mesh Preview
  to Polygons, 169 Deform.

- Step 165 (Component-mode Channel Box and RMB node submenus, backlog_164 #2) 완료 — `docs/steps/step_165.md`. Maya 측정
  `research/maya/re/cb_component_164.md` (GUI Maya, `research/scripts/maya_cb165/`). 편집 모드 Channel Box = shape 이름 +
  `CVs (click to show)` (선택 점 표, `ui/cb_points.py`) + INPUTS, 선택 없음 = 빈 안내; RMB DG Traversal / Inputs / Outputs =
  노드 목록 (`marking/rmb_nodes.py`, `menus.NodeList`), 노드 고르기 = Channel Box 에서 열고 스크롤 + AE 탭, Enable / Disable All,
  All Inputs... 창. 헤드리스 1540 / 1540, GUI step165 9/9 + 관련 7 파일 (gui_step52 "list under the ring" 2 실패는 165 이전부터).
  **바로 다음 할 일**: 166 Menu consistency (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_164.json`
  3 번째 항목), 그 뒤 167 셸프 더블클릭 / 넘침, 168 Modify + Smooth Mesh Preview to Polygons.

- **체크포인트 2026-10-24 (/sc:save, 164 후)** — 지금 단계: **164 완료 · 커밋됨** (`40ee970` + 문서 `22dafe3`). 161 (`99eedfa`),
  162 (`2cd3406`), 163 재점검 11차 (`416563f`), 164 (`40ee970`) 모두 커밋, 진행 중인 레인 · 테스트 없음, push 안 함. 헤드리스 전체
  1527 / 1527 (164 끝).
  **바로 다음 할 일**: 165 Component-mode Channel Box and RMB node submenus (backlog
  `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 2 번째 항목), 그 뒤 166 메뉴 어긋남, 167 셸프 더블클릭 / 넘침.
  알려진 것: `gui_step129_panel_toolbar` 머리 폭 의존 실패, RMB 목록 위치 (링 옆 vs Maya 아래 + 잘림) 판단 보류 (manual_checks Step 161).

- Step 164 (Maya DAG rules for parents, backlog #1) 완료 — `docs/steps/step_164.md`. 부모를 숨기면 자손도 안 그려짐 (자손 Visibility
  채널은 그대로, `operators/dag.py` sync), Delete / Export Selection / Ctrl+1 Isolate 가 선택의 계층을 가져감 (mayapy 측정
  `research/maya/re/dag_164.md`).
  **바로 다음 할 일**: 165 Component-mode Channel Box and RMB node submenus (backlog
  `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 2 번째 항목).

- Step 163 (재점검 11차 = 사용자 지시의 「재점검 10차」) 완료 — `docs/steps/step_163.md` (+ `step_163_remaining.md`, `step_163_quant.md`),
  PLAN 「재점검 11차」. 헤드리스 1518/1518, dogfood 48/48 (콘솔 오류 0), 대응표 29/2/0/2 (88 %), 메뉴 649/1318 (49.2 %), 옵션 상자 Maya 창
  85 경로, look_compare 킷 픽셀 6/6, 열린 이슈 20 중 19 코드에서 고쳐짐 (#89 만 열림, 릴리스 때 닫기), manual_checks 620 / 86 ticked.
  **바로 다음 할 일**: 새 backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 8 개 = steps 164–171 (Maya DAG 상속,
  컴포넌트 모드 Channel Box + RMB Inputs / Outputs, 메뉴 어긋남, 셸프 더블클릭 / 넘침, Modify + Smooth Mesh Preview to Polygons, Deform,
  3D View 밖 선택 수정키, Animation Snapshot / Ghosting). 규칙: GUI 전체 묶음은 릴리스 준비 때만, sleep 대기 금지, Blender 동시 2 개.

- Step 162 (Option box and menu gestures, backlog_155 #8 — 마지막 항목) 완료 — `docs/steps/step_162.md`. Toggle Show/Hide ❒ /
  Non-Deformer History ❒ = Maya 옵션 창 (GUI Maya 캡처 + mayapy 측정 `research/maya/re/options_162.md`; Non-Deformer 기본이 이제
  Maya 의 All), Ctrl+Shift+메뉴 클릭 = 현재 셸프에 버튼 (`shelves.json`, 팩토리 탭은 Maya 슬롯 뒤), Hypershade 스와치 MMB 드래그 →
  물체에 재질 (`ui/hs_drag.py`). 옵션 상자 window 78 → 85, 회귀 0.
  **바로 다음 할 일**: backlog_155 는 162 가 마지막 — 새 감사 (step 154 방식: dogfood · 열린 이슈 · manual_checks · 메뉴 / 옵션
  상자 수) 로 새 backlog 를 만들거나 사용자 지시. 알려진 것: `gui_step129_panel_toolbar` 머리 폭 의존 실패, Modeling - Expert
  뷰포트 머리줄 Blender 위젯, 긴 팩토리 셸프 탭의 추가 버튼이 화면 밖 (셸프 스크롤 없음).

- Step 161 (Viewport messages and views, backlog_155 #7 = step-154 dogfood G1–G4) 완료 — `docs/steps/step_161.md`.
  킷 명령 결과 = Command Line 결과 칸 (`results.result`, INFO 보고 99 곳; 상태 줄 폭을 창에 맞춰 나눠 결과 칸이 이제 보임),
  RMB 목록 한 열 (안 들어가면 하위 메뉴 없는 쪽 링 옆), Space 네 뷰 정사영 칸 = Maya 카메라 (30 단위, 칸마다 줌 기억, 자기 평면
  격자 가장자리까지, 머리줄 하나 알림), 선택 와이어 = Maya 계층 강조 (side 뷰에서 lead 초록이 사라지던 원인), look_compare
  marking 표본 다시 고름 (kit-drawn 6/6, 실제 상자 색).
  **바로 다음 할 일**: 162 Option box and menu gestures (backlog
  `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_155.json` 8 번째 항목).
  알려진 것: `gui_step129_panel_toolbar` 머리 폭 의존 실패, Modeling - Expert 뷰포트 머리줄에 Blender 위젯이 남음.

- Step 160 (Maya UI reset and workspaces, #81, backlog_155 #6) 완료 — `docs/steps/step_160.md`. 템플릿에 Maya 작업 공간 8 개
  (Maya Classic, Modeling - Standard / Expert, Sculpting, UV Editing, Rigging, Animation, Rendering - Standard), Windows >
  Workspaces 메뉴 + Status Line 드롭다운 (없으면 템플릿에서 덧붙임, 메뉴 세트 · 탭 적용), Reset Current Workspace
  (`switch.reset_workspace`, `ui/workspaces.py`).
  **바로 다음 할 일**: 161 Viewport messages and views (backlog
  `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_155.json` 7 번째 항목).

- Step 159 (Skin weights export / import + Skeleton gaps, backlog_155 #5) 완료 — `docs/steps/step_159.md`. Deform > Export /
  Import Weights = Maya deformerWeights XML (`operators/deformer_weights.py`), Joint Labelling 전체 + 라벨 그리기 + Mirror Skin
  Weights Label 모드 (`operators/joint_labels.py`), Enable / Disable IK Handles (influence = Maya ikBlend), Reset Default Weights.
  Skeleton 13 → 51 / 54, Rigging 59 %.
  **바로 다음 할 일**: 160 Maya UI reset and workspaces (#81) (backlog
  `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_155.json` 6 번째 항목).

- Step 158 (Channel Box 메뉴 완성 + #97, backlog_155 #4) 완료 — `docs/steps/step_158.md`. RMB 어디서나 (빈 곳 포함) = Maya
  Channels 메뉴, Ctrl+RMB = Edit 메뉴; Channels 메뉴 Maya 항목 전체 (Breakdown / Mute All, Sync Graph Editor / Timeline, Cut /
  Copy / Paste Selected (mayapy 규칙), Freeze, Select Connection, 레이어 알림) — `ui/cb_channels.py`; SHAPES 줄 = 채널 (`sh:`)
  이라 조명 Intensity / Color 키 가능, spot Cone / Penumbra 줄; #97 Bind Skin → skinCluster1 / 2.
  **바로 다음 할 일**: 159 Skin weights export / import + Skeleton gaps (backlog
  `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_155.json` 5 번째 항목).

- Step 157 (Graph Editor 키를 Maya 식으로, backlog_155 #3) 완료 — `docs/steps/step_157.md`. 편집기 Edit 메뉴의 키 창이
  선택 키에 (Maya fromGraphEditor), Add / Remove Inbetween = 편집기 곡선, 키별 Mute / Unmute = Stepped F-modifier
  "Maya mute" (mayapy 값과 같음), Select 마스크 (All / Only Curve / Curve / Key / In / Out), Default In / Out Tangent =
  add-on pref 로 킷 키에 적용 (`operators/graph_key_menu.py`). Graph Editor 메뉴 145 → 154 / 229, Dope Sheet 120 → 124.
  **바로 다음 할 일**: 158 Channel Box 메뉴 + #97 (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_155.json`
  4 번째 항목) — Mute 색 표시도 거기서. 알려진 것: `gui_step129_panel_toolbar` 폭 의존 실패 (아직).

- Step 156 (Curves 도구, backlog 154 #2) 완료 — `docs/steps/step_156.md`. CV / EP Curve Tool · 3 / 2 점 원호 = 클릭 도구
  (`operators/curve_draw.py`), Maya 곡선 수학 `operators/curves_math.py` (EP · 원호 · Attach · Detach · Cut · Fillet · Straighten · Move
  Seam 이 mayapy 정답 `research/maya/re/curves_156.json` 과 1e-6, Rebuild 는 모양 0.6 %), Blender 표현 `operators/curves_maya.py`
  (Endpoint NURBS / cyclic / POLY / Bezier), 옵션 창 5 개. Curves 메뉴 16 → 21 / 36.
  **바로 다음 할 일**: 157 Graph Editor 키 (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json`).

- Step 155 (UV Editor 셸 도구, backlog 154 #1) 완료 — `docs/steps/step_155.md`. Maya 셸 명령 12 개 (mayapy 정답
  `research/maya/re/uv_shells_155.json` 과 1e-4 / Orient 6e-4 일치, `operators/uv_shells.py`), Unfold 가 넓이 · UV 평균 유지, UV Editor
  키 4 5 6 8 9 Ctrl+1 Delete Ctrl+Shift+X, 셸 / 텍스처 테두리 그리기, Move UV Shell (`ui/uv_display.py`). UV Editor 메뉴 95 → 110 / 172.
  **바로 다음 할 일**: 156 Curves 도구 (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json`).

- Step 154 (재점검 10차 = 사용자 지시의 「재점검 9차」) 완료 — `docs/steps/step_154.md` (+ `step_154_remaining.md`, `step_154_quant.md`),
  PLAN 「재점검 10차」. 헤드리스 1398/1398, dogfood 48/48 (콘솔 오류 0), 대응표 29/2/0/2 (88 %, 변화 없음), 메뉴 600/1318 (45.5 %),
  manual_checks 579 / 81 ticked. 열린 이슈 20 중 17 은 코드에서 고쳐짐 (릴리스 때 닫기), 남은 것 #81 #89 #97.
  **바로 다음 할 일**: 새 backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 8 개 = steps 155–162 (UV 셸 도구,
  Curves, Graph Editor 키, Channel Box 메뉴 + #97, 스킨 가중치 내보내기, Maya UI 초기화 #81, 뷰 메시지 / 네 뷰, 옵션 상자 몸짓).
  규칙: GUI 전체 묶음은 단계 끝 한 번, sleep 대기 금지, Blender 동시 2 개.

- Step 153 (Blender 5.x pass, #90) 완료 — `docs/steps/step_153.md`, 결과 표 `docs/compat_5x.md` 「step 153」. Paint Skin Weights ❒ 가
  5.x 에서 `compat.unified_paint_settings` / `set_unprojected_radius` (5.x 는 페인트 모드마다, 크기 = 지름). GUI 전체 5.2.3 의 실패 15 개:
  step 151 뒤 회귀 (넓은 N 상자가 대각선 제스처에서 하위 메뉴를 엶 → 방사 하위 메뉴는 자기 구역에서만 열림; 테스트의 Maya 기하 가정 2 개),
  테스트의 5.x API 직접 사용, Blender 5.0 「메뉴는 클릭할 때까지 열림」 (`compat.menus_close_on_leave`, 옵션 상자 뒤 Maya 메뉴가 열린 채).
  헤드리스 4.5 / 5.0.1 / 5.1.2 / 5.2.3 = 1398 (4.5 는 1394 + 새 4), GUI 5.2.3 실패 7 파일 재실행 전부 통과.
  **바로 다음 할 일**: backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_146.json` 은 153 이 마지막 — 다음은 새 감사
  (열린 이슈 · manual_checks 정리) 로 새 backlog 를 만들거나 사용자 지시.
  규칙: GUI 전체 묶음은 단계 끝 한 번 (관련 파일 `-k`), sleep 대기 금지, Blender 동시 2 개.

- Step 152 (렌더 · 그리드 기본, #101 — 이슈 새로 만듦) 완료 — `docs/steps/step_152.md`. 조명 없는 장면은 Maya 기본 조명으로
  렌더 (킷 렌더 동안만 카메라 자식 Sun, Enable Default Light), Test Resolution / Batch Render 연결, Render Sequence ❒ / Batch Render ❒ =
  Maya 창, Render Current Frame ❒ = Maya 경고, Display > Grid ❒ = Maya Grid Options (격자가 따름). 헤드리스 1394/1394, GUI 관련
  3 파일 21/21. 남은 것: 킷 lambert1 이 Maya 보다 1.25 배 밝음 (Diffuse 0.8 없음).
  **바로 다음 할 일**: 153 Blender 5.x (#90) (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_146.json`).

- Step 151 (매니퓰레이터 · 링 · 문구, #98 #99 #100) 완료 — `docs/steps/step_151.md`. RMB 링 = Maya 측정 (R 55, 상자 21 px,
  글자 + 25 px, UV 하위 메뉴 화살표), Ctrl+E = Maya polyExtrudeFace 매니퓰레이터 (세 축 화살표 · 크기 상자 · 평면 · 가운데, Local
  Translate X/Y · Local Scale 을 mayapy 로 맞춤), 매니퓰레이터 툴팁 없음, 상태 줄의 Blender 문구 (keying set, effector, non-uniform scale,
  Anim Player, Pivot edit) 없음. 헤드리스 1368/1368, GUI 관련 11 파일 98/98 (GUI 전체 묶음은 안 돌림).
  **바로 다음 할 일**: 152 렌더 · 그리드 (이슈 먼저 만들기) → 153 Blender 5.x (#90)
  (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_146.json`).

- Step 150 (Graph Editor 를 Maya 말로, #96) 완료 — `docs/steps/step_150.md`. 킷 outliner: Visibility 같은 Maya 이름, 고른 줄만
  파랑, joint / blendShape 노드, 휠 스크롤; View > Auto Frame (켬) / Auto Frame Time / Curve Name, Show > Clear Below 등 연결 (Graph
  Editor 회색 92 → 84, 나머지는 notice); Graph Editor / Dope Sheet / NLA 에서도 Ctrl+A = AE / Channel Box. 길이 곡선 높이 (미터) 는
  Blender 에 곡선별 표시 배율이 없어 못 고침 (남은 것). 헤드리스 1345 + 고친 뒤 86/86, GUI 전체 1614 (불안정 1 은 혼자 15/15).
  **바로 다음 할 일**: 151 매니퓰레이터 · 링 · 문구 (#98 #99 #100) → 152 렌더 · 그리드 → 153 Blender 5.x (#90)
  (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_146.json`).

- Step 149 (선택 와이어 · 이름 · bind, #91 #93 #94) 완료 — `docs/steps/step_149.md`. 재생 / 프레임 변경 때 변형 물체의 초록
  선택 와이어가 평가된 모양을 따라감 (`frame_change_post`), 선택된 격자도 Maya 초록 / 흰 와이어, Delete 뒤 새 큐브가 다시
  pCube1 (이름을 잡고 있던 users 0 data 를 지움), Bind Skin = Maya Closest distance (mayapy 로 잰 규칙 d^-4, 월드 공간 — 스케일된
  mesh 도 모든 joint), Bind Skin Options 에 Bind method (Heat Map = Blender bone heat). 헤드리스 1329/1329 + 격자 뒤 관련 9 파일 53/53,
  GUI 전체 1595 + 고친 뒤 관련 81/81.
  **바로 다음 할 일**: 150 Graph Editor (#96) → 151 매니퓰레이터 · 링 · 문구 (#98 #99 #100) → 152 렌더 · 그리드 →
  153 Blender 5.x (#90) (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_146.json`).

- Step 148 (Channel Box 마무리, #87 #85 #83 #95) 완료 — `docs/steps/step_148.md`. Channel Box RMB = Maya Channels 메뉴
  (Blender 버튼 메뉴는 Python 항목을 C 항목 15 줄 뒤에 붙였다), UI 1.5 / 1.0 에서 Channel Box 가 한 줄 더 (PANE_TOP 재측정 +
  위젯 단위 반올림 버그: Python round(22.5) = 22), AE 변환 값 = Maya 숫자 (단위 없음), 격자 Scale = Maya 숫자 (delta_scale),
  조명 SHAPES = Color R / G / B + Intensity. 헤드리스 1324/1324, GUI step148 3 배율 각 6/6 + 관련 파일 통과.
  **바로 다음 할 일**: 149 와이어 · 이름 · bind (#91 #93 #94; 격자 선택 색도) → 150 Graph Editor (#96) → 151 매니퓰레이터 ·
  링 · 문구 (#98 #99 #100) → 152 렌더 · 그리드 → 153 Blender 5.x (#90)
  (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_146.json`).

- Step 147 (Undo step · redo 패널, #88 #92 #86) 완료 — `docs/steps/step_147.md`. 메뉴 · 셸프 · 마킹 메뉴 명령이 각자 undo step
  하나 (전에는 Python 호출이라 step 도 등록도 없었음, 측정), Mesh Tools 도구 항목 뒤 Ctrl+Z 가 편집 모드에 남음, Ctrl+E / Ctrl+B /
  Joint Tool / IK Handle / 옵션 창 뒤 Adjust Last Operation 없음 (Create Joints 뒤 셸프 클릭이 됨), "redo" 옵션 상자는 이제 정말
  설정을 보여 줌. 헤드리스 1319/1319, GUI 관련 24 파일 254/254.
  **바로 다음 할 일**: 148 Channel Box (#87 #85 #83 #95) → 149 와이어 · 이름 · bind (#91 #93 #94) → 150 Graph Editor (#96) →
  151 매니퓰레이터 · 링 · 문구 (#98 #99 #100) → 152 렌더 · 그리드 → 153 Blender 5.x (#90)
  (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_146.json`).

- Step 146 (옵션 상자 끌기 없이, #82) 완료 — `docs/steps/step_146.md`. ❒ 항목을 0.2 s 누르면 hold 메뉴의 "Option Box ❒" 줄로 포인터가
  옮겨져 그대로 놓으면 옵션 창 (Maya 메뉴는 포인터를 창 끝으로 보냈다 돌려놓아 닫음), Shift / Ctrl + 클릭 = 옵션 상자 (OS 키 상태),
  툴팁 끝에 방법 한 줄. ❒ 부분만 클릭은 Blender 가 위치를 안 줘서 불가 (측정). 헤드리스 1313/1313, GUI 바뀐 모듈 5 파일 51/52
  (step143 첫 클릭 흔들림, 혼자 통과). 실제 하드웨어 확인 = manual_checks Step 146.
  **바로 다음 할 일**: 147 되돌리기 · redo 패널 (#88 #92 #86) → 148 Channel Box (#87 #85 #83 #95) → 149 와이어 · 이름 · bind
  (#91 #93 #94) → 150 Graph Editor (#96) → 151 매니퓰레이터 · 링 · 문구 (#98 #99 #100) → 152 렌더 · 그리드 → 153 Blender 5.x (#90)
  (backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_146.json`).

- Step 145 (재점검 9차 — 사용자 지시의 「재점검 8차」) 완료 — `docs/steps/step_145.md` (+ `step_145_{ui,quant,remaining}.md`), PLAN
  「재점검 9차」. 헤드리스 1307/1307, dogfood 48/48, look_compare viewport 11/12, 대응표 29/2/0/2 (8차와 같음), 메뉴 작동 45.2 %,
  옵션 창 80 종, 마킹 메뉴 회색 69. 새 이슈 #90–#100 (0.4.0).
  **바로 다음 할 일**: backlog.json 8 개 = step 146 옵션 상자 클릭 (#82), 147 되돌리기 · redo 패널 (#88 #92 #86), 148 Channel Box
  마무리 (#87 #85 #83 #95), 149 변형 선택 와이어 · 이름 · bind (#91 #93 #94), 150 Graph Editor (#96), 151 매니퓰레이터 · 링 · 문구
  (#98 #99 #100), 152 렌더 · 그리드 기본, 153 Blender 5.x (#90).

- Step 144 (0.4.0 Maya 모델링 도구 · Deform, #30 #31 #34) 완료 — `docs/steps/step_144.md` (+ `step_144_{poly,loop,deform}.md`,
  `research/maya/re/{options_144,edge_loops_144}.md`). Quad Draw / Create Polygon / Append, Insert / Offset Edge Loop / Slide Edge 가
  Maya 클릭 · 수정키 · Tool Settings 의 킷 도구, Deform 메뉴가 Maya 같은 디포머 + 옵션 창 14 + INPUTS + Paint Weights 대상.
  헤드리스 1307/1307, 관련 GUI 89/89. 새 이슈 #88 (Mesh Tools 의 편집 모드 진입 되돌리기), #89 (Quad Draw 남은 것).
  **바로 다음 할 일**: 0.4.0 남은 이슈 — #81 (Maya UI 초기화) #82 (옵션 상자 열기) #83 #85 #86 #87 (step 142 후속) #88 #89.

- Step 143 (0.3.0 출시 준비) 완료 — `docs/steps/step_143.md` (+ `step_143_{compat79,user}.md`). 출시 전 사용자 보고 #79 (다른 애드온의
  Render 패널 때문에 Maya 모드 안 켜짐) #84 (5.1/5.2 더블클릭 루프 오류) #80 (Extrude 뒤 이동, F12 UV sync) 고침, #82 원인 댓글 →
  0.4.0. manifest 0.3.0, CHANGELOG [0.3.0], `docs/distribution/release_notes_0.3.0.md`. validate Success, release_check 4.5.4 /
  5.2.2 22 / 22, 헤드리스 1249/1249, GUI 전체 1500 + 1 (step55 테스트 좌표 고친 뒤 15/15), 2 격리. v0.3.0 태그 · push ·
  GitHub 초안 릴리스 (zip 2 개), 바탕화면 `MayaWorkflowKit_upload/` 에 0.3.0 zip + 문구.
  **바로 다음 할 일**: step 144 = 0.4.0 Maya 모델링 도구 (#30 Quad Draw / Create Polygon / Append, #31 Insert / Offset Edge Loop /
  Slide Edge, #34 Deform 메뉴). 0.4.0 에 함께: #81 #82 #83 #85 #86 #87.

- Step 142 (UI 모습 · 맞춤, #78 #77 #76 #54 #41) 완료 — `docs/steps/step_142.md` (+ `step_142_{ui,icons,media}.md`). Maya 세로 탭 띠
  dock (Channel Box 286 px at 1.0, 뷰포트 773 → 954 px), 메뉴 막대 » 넘침 + SDK 1.5 배율, Maya 매니퓰레이터 색 · 와이어 #000460
  (look_compare viewport 11/12), 메뉴 아이콘 190 → 675, 스토어 미디어 · 홍보 · 클립 · 사이트 미디어를 테마 없이 다시 찍음.
  헤드리스 1234/1234, 관련 GUI 59 + 32 + 1.5 배율 35 모두 통과. 새 이슈 #83 #85 #86 #87 (0.3.0).
  **바로 다음 할 일**: step 143 = 0.3.0 출시 준비 (버전 고정, GUI 전체 묶음, release_check, CHANGELOG, #83 #85 #86 #87 중 출시 전
  고칠 것 결정). 144 = 0.4.0 Maya 모델링 도구 (#30 #31 #34).

- Step 141 (키맵 · 선택 작은 묶음, #65 #72 #73, B4 B6, quant gap 3) 완료 — `docs/steps/step_141.md` (+ `step_141_{keys,select}.md`,
  `research/maya/re/{fields_141,select_convert_141}.md`). QA 먼저 (776dd37): GUI 실행기 파일당 시간제한 TIMEOUT 보고, `GUI_SKIP` 격리
  (gui_step75_input_line, gui_step63_mtk → manual_checks), unbuffered 로그, 실행당 19 s 고정 비용 → 실패 파일은 한 번의 `-k`.
  Ctrl+A 모든 3D 모드 + UV = AE / Channel Box, UV Alt+RMB = `allset.dolly_2d`, Undo 256 안내 (README + 환경설정 패널 + 환영 창),
  joint 이름 joint1 부터, Gravity 9.8 아래 / Newton 5 끌어당김, Select / Ctrl+RMB 변환 13 개 (mayapy 규칙). 헤드리스 1212/1212,
  관련 GUI 54/54, Select 메뉴 작동 39 → 50.
  **테스트 규칙 (사용자 10-23 / 10-24)**: 단계마다 GUI 전체 묶음 금지 — 기능 테스트 + 헤드리스 전체 + 바뀐 모듈 GUI / 스모크만,
  GUI 전체는 출시 준비에서만. 격리된 GUI 테스트는 다시 디버깅하지 않는다.
  **바로 다음 할 일**: step 142 UI 마감 → 0.3.0 출시 준비 (그때 GUI 전체 묶음). 남은 후보: 2D 편집기 Ctrl+A, Node Editor Alt+RMB,
  다른 필드 기본값 (step_141 「남은 것」).

- Step 140 (일상 옵션 창, #32 #33 #35) 완료 — `docs/steps/step_140.md` (+ `step_140_{rig,edit}.md`,
  `research/maya/re/option_boxes_140.md` · `option_boxes_140_edit.md`). Maya 2022 창 26 개 새로 (Window spec 26 → 50: Joint / IK /
  IK Spline Tool, Bind / Detach / Copy / Paint Skin Weights, Blend Shape, Aim / Pole Vector / Scale constraint, Delete / Cut / Copy /
  Paste / Scale / Snap Keys, Parent / Unparent / Ungroup, Duplicate Special, Connect, Circularize, Make Hole, Insert Edge Loop),
  Aim = Maya (+X 대상, 월드 up Y), Key > Scale Keys 새로. 옵션 상자 window 29 → 60, generic 65 → 47, dead 231 → 229
  (`python tools/menu_count.py --options`). 헤드리스 1191/1191, GUI step140 9/9 (샷 3 장), GUI 전체 1453 PASS (step63_mtk 흔들림 재실행 통과, step75_input_line 은 140 전에도 멈추는 환경 문제).
  **사용자 결정 (10-23)**: 0.3.0 버전 고정 = 140 · 141 · 142 끝난 뒤, 그다음 단계 = 0.3.0 출시 준비. #30 #31 #34 는 GitHub
  마일스톤 0.4.0 으로 옮김 (완료).
  **바로 다음 할 일**: step 141 키맵 · 선택 묶음 (#65 #72 #73, B4 B6) → 142 UI 마감 → 0.3.0 출시 준비.
  **진행 규칙 (Hermes 10-23)**: 백그라운드 서브에이전트 · ScheduleWakeup 금지 — 병렬은 포그라운드 동기 Agent 최대 2 개, Blender
  프로세스 최대 2 개, 레인 마일스톤마다 WIP 커밋, 단계 커밋에 `Fixes #N` 줄.

- Step 139 (Edit Mesh / UV 를 Maya 결과로, #70 #68 #16) 완료 — `docs/steps/step_139.md` (+ `step_139_{edit,shape,uv}.md`,
  `research/maya/re/edit_mesh_139.md`). Connect / Merge / Smooth / Symmetrize, Ctrl+E 엣지 · 정점, Ctrl+B 가 mayapy 측정과 같은 결과 (바로 실행,
  step 65 처럼 수정 가능), UV > Automatic / Contour Stretch 오브젝트 모드, UV Editor Best Plane / Contour Stretch.
  **바로 다음 할 일**: step 140 옵션 창 (#32 #33 #35) → 141 키맵 · 선택 묶음 (#65 #72 #73). 후보: 조명 없는 장면 렌더에 Maya 기본 조명 (137),
  Open 의 묻기 문구 (138), Connect 4 점 이상 (Maya 엣지 순서, M11), 구 · 토러스 Automatic 셸 크기 (Maya "Less distortion" 규칙).

- Step 138 (장면 · 파일, #57 #63 #64 #69) 완료 — `docs/steps/step_138.md` (+ `step_138_{prompt,carry,file_io}.md`). New Scene 에 Maya
  Save / Don't Save / Cancel (`ui/save_prompt.py`), Maya 모드에서 파일을 열면 Maya 레이아웃 (설정 `maya_layout_on_open`), Maya 도구 설정이
  New / Open 을 건너 유지 (`ui/scene_carry.py`), FBX / OBJ / Alembic / USD 가 Maya 와 채널 · 이름 그대로 왕복 (`operators/file_io.py`).
  **바로 다음 할 일**: step 139 Edit Mesh / UV (#70 #68 #16) → 140 옵션 창 (#32 #33 #35) → 141 키맵 · 선택 묶음 (#65 #72 #73).
  후보: 조명 없는 장면 렌더에 Maya 기본 조명 (137), Open 의 묻기 문구를 Maya 로 (킷 Open 브라우저 필요, 138), 도구 설정을 세션 사이에도 (138).

- Step 137 (애니 · 렌더 기본, #66 #67 #71) 완료 — `docs/steps/step_137.md` (+ `step_137_{graph,render,defaults}.md`). Graph Editor 값 눈금을
  표시 단위로 (`ui/graph_units.py`, draw cursor — 마우스가 곡선 영역에 있을 때만, Blender 한계), Render Current Frame / Sequence = 뷰 카메라 또는
  킷 `persp` 카메라 (`operators/render_persp.py`), Maya 재질 · 조명 기본값 (Blinn / Phong, Intensity / Decay Rate No Decay), 템플릿 960 × 540.
  **바로 다음 할 일**: step 138 장면 · 파일 (#57 #63 #64 #69) → 139 Edit Mesh / UV (#70 #68 #16) → 140 옵션 창 (#32 #33 #35) →
  141 키맵 · 선택 묶음 (#65 #72 #73). 후보 (137 에서 발견): 조명 없는 장면 렌더에 Maya 기본 조명 (default light) 이 없어 물체가 어둡다.

- Step 136 (마킹 메뉴 완성 · 창 안에, #56 #62 #74) 완료 — `docs/steps/step_136.md` (+ `step_136_{bounds,items}.md`). 목록 줄 · 방사 상자가
  영역 경계 띠를 피함 (`draw.window_edges` → `engine.fit_ring(..., edges)`), 메뉴가 다른 킷 POST_PIXEL 위에 그려짐; 마킹 항목
  `("item", 메뉴 경로)` = 메인 메뉴 항목 그대로 (컴포넌트 모드 규칙 포함), 회색 128 → 73 (모두 `notices.MARKING` 알림, Help Line),
  Ctrl+RMB 메시 오브젝트 = 변환 메뉴. 검증 수치는 step 문서.
  **바로 다음 할 일**: step 137 애니 · 렌더 기본 (#66 #67 #71) → 138 장면 · 파일 (#57 #63 #64 #69) → 139 Edit Mesh / UV (#70 #68 #16) →
  140 옵션 창 (#32 #33 #35) → 141 키맵 · 선택 묶음 (#65 #72 #73). backlog.json (`hermes/autodrive_bmk`) 은 사라졌다 — 이슈와 이 목록이 기준.
  백그라운드 레인을 기다리며 턴을 끝내지 말 것 (step 136: 레인이 중단됐는데 메인이 40 분 알림만 기다림) — 포그라운드로 돌리거나 WIP 커밋 확인.

- Step 135 (Dock / Channel Box, #55 #60) 완료 — `docs/steps/step_135.md` (+ `step_135_{cb,width,fix}.md`). INPUTS 접힘 + 이름 클릭 펼침,
  Channel Box 부분 스크롤 · Layer Editor 고정 분할, 휠 스크롤 (View2D Buttons List), dock 폭 배율별 (466 / 574 / 672 px). 헤드리스 1060/1060,
  GUI 전체 뒤 실패 파일 수정 → 416/416. 후속 #77 (1.5 배율 메뉴 줄 · SDK), #78 (dock 폭 vs Maya 세로 탭).
  **바로 다음 할 일**: step 136 = 마킹 메뉴 (#56 #62 #74), 그다음 137–141 (backlog.json).

- Step 134 (테마 없이 Maya 뷰포트 모습, #58 #59 #61 #75) 완료 — `docs/steps/step_134.md` (+ `step_134_{sel,grid,hud,look}.md`). 킷 고정 Maya
  선택 · 컴포넌트 색 (`ui/component_colors.py`), 그리드 #404040 + 커서 숨김, 디스플레이 키 뒤 Adjust Last Operation 없음, Smooth Preview 매끈,
  look_compare 도구 갱신 (viewport 1/12 → 7/12, grid FAIL → ok). 헤드리스 1046/1046, GUI 1345/1345. 후속 #76 (조작기 · 와이어 색).
  **바로 다음 할 일**: step 135 = Dock / Channel Box (INPUTS 접힘, Layer Editor 보임, 배율별 dock 폭; #55 #60), 그다음 136–141 (backlog.json).

- Step 133 (재점검 8차 — 사용자 지시의 「재점검 7차」) 완료 — `docs/steps/step_133.md` (+ `step_133_{ui,work,quant,remaining}.md`),
  PLAN 「재점검 8차」. 헤드리스 1025/1025, dogfood 48/48 (콘솔 오류 0), 구현률 29/2/0/2 (테마 행이 step 130 으로 부분), 메뉴 작동 44.5 %
  (step 98 29.6 %), 알림 없는 회색 0, 마킹 메뉴 회색 112 그대로. 새 이슈 #55–#75 (0.3.0).
  **바로 다음 할 일**: backlog.json 8 개 = step 134 Maya 뷰포트 모습 (선택 색 · 그리드 · HUD · 부드러운 미리보기), 135 Dock / Channel Box,
  136 마킹 메뉴, 137 애니 · 렌더 기본, 138 장면 · 파일, 139 Edit Mesh / UV 결과, 140 옵션 창, 141 키맵 · 선택 묶음.

- Step 132 (0.2.1 출시 준비) 완료 — `docs/steps/step_132.md` (+ `step_132_fix{44,52,53}.md`). #44 Ctrl+N = Maya 새 장면, #52 패널 툴바 »
  넘침 메뉴, #53 1.25 배율 레이아웃 재맞춤 수정; manifest 0.2.1, CHANGELOG, 스토어 릴리스 노트 `docs/distribution/release_notes_0.2.1.md`,
  GitHub 초안 릴리스 v0.2.1 (zip 2 개). validate PASS, release_check 4.5 22/22 · 5.2.2 14/14 (잔여 0), 헤드리스 1025/1025, GUI 1302/1302.
  **바로 다음 할 일**: 0.3.0 — #16 #30–#35 (Maya 옵션 창 · 도구), #41 (테마 없이 스토어 미디어 다시 찍기), #54 (남은 아이콘).

- Step 131 (아이콘 #23 + Hypershade #25) 완료 — `docs/steps/step_131.md` (+ `step_131_{icons,shelf,status,toolbox,menu,hypershade}.md`).
  셸프 203 버튼 · Status Line · 패널 툴바 · Tool Box · Layer Editor · 킷 Outliner 행을 Maya 2022 모양으로 다시 그림 (킷이 그린 numpy, 버튼마다
  고유, 16–64 px 힌팅), Maya 메뉴 항목 190 개에 아이콘, 콘택트 시트 `docs/icons/` (`tools/icon_sheet.py`), 고유성 테스트
  `tests/test_step131_icons.py`. Hypershade = Maya 배치의 별도 창 (Browser · Create · Graph · Material Viewer · Property Editor).
  Blender 4.5 `new_triangles` 아이콘 해제 크래시를 .dat 파일로 우회. 헤드리스 1011/1011, GUI 1307/1308 (실패 1 = #53). 후속 #54 (0.3.0).
  (다음은 step 132 였음.)
  손 확인 `docs/manual_checks.md` 「Step 131 — …」.

- Step 130 (스토어 심사 대응 #40) 완료 — `docs/steps/step_130.md` (+ `step_130_*.md`). exec/eval·import 훅·sys.* 0건, 테마 전부 삭제,
  환경설정·keyconfig 영구 변경 없음 (애드온 키맵), 앱 템플릿 설치·user_disabling·스냅숏 삭제, tags = User Interface. 결정 13·14,
  답글 초안 `docs/distribution/review_reply.md`. 헤드리스 전체 PASS, validate Success, dogfood 48/48, GUI 전체 948/957 → 실패 파일 재실행 후
  남은 1건 = #53 (1.25 배율 레이아웃 재조정).
  **바로 다음 할 일**: step 131 = #23 아이콘 + #25 Hypershade; 0.2.1 전에 #53 #52 #44 #41 (마일스톤 0.2.1).

- Step 129 (0.2.1 수정 배치) 완료 — `docs/steps/step_129.md` (+ 레인 문서 `step_129_*.md`). #36 크래시 핫픽스 병합 + 타이머 46곳
  전수 (`src/allset/live_refs.py`); user-report #1–#14 #22 #27 #28 #37 #38, P1 #19 #20 #26 #39, 같은 원인 #15 #17 #18 #21 #24 #29 수정.
  헤드리스 999/999, GUI 전체 1092/1102 → 통합 수정 후 실패 파일 재실행 모두 PASS. 마일스톤 0.2.1 / 0.3.0 배정.
  **바로 다음 할 일**: step 130 = #23 아이콘 + #25 Hypershade; 그다음 131 릴리스 준비. 새로 열린 #40 (스토어 심사 요구) 은 아직 미배정. 손 확인 `docs/manual_checks.md` 「Step 129」.

- Step 128 (0.2.1 버그 점검, 수정 없음) 완료 — `docs/steps/step_128.md`, 툴 전수 표 `docs/steps/step_128_tools.md`. GitHub 이슈
  #1–#39 (점검 18: #15–#21, #24, #26, #29–#36, #39; 나머지 사용자), #1–#4 에 근본 원인 코멘트. P0 = #36 (메뉴로 연 Properties 창을 2초 안에 닫으면 크래시); P1 = #39 (컴포넌트 모드 Edit/Select 메뉴 무반응), #19 (Maya→Blender 전환이 템플릿 화면을
  안 되돌림), #20 (Paint Skin Weights 정규화 없음), #26 (h / CB Visibility / 레이어 V 가 다른 플래그). 재현: `tests/gui/audit128/`
  (`python tests/gui/run.py --dir tests/gui/audit128 -k <이름>`).
  **바로 다음 할 일**: step 129 = #36 크래시부터, #1–#4 + P0/P1 이슈 수정 배치; 사용자 이슈 심각도 분류부터.

- Step 127 (제품 사이트 GitHub Pages, impeccable, 사용자 지시 10-20) 완료 — `docs/steps/step_127.md`. `site/` 정적 사이트 (셸프 탭 = 워크플로우
  6 묶음 + 클립 + Channel Box 사실 열, Maya | Blender 전환, 설치 · 한계 · FAQ · 상표 고지), `site/PRODUCT.md` · `DESIGN.md`, 미디어
  `tools/site/make_media.py`, 검사 `tools/site/check_site.py` (경로 PASS, 첫 화면 210 KiB), `.github/workflows/pages.yml`. push 안 함.
  **바로 다음 할 일**: Hermes/사용자 — 저장소 공개 + push 후 Pages 켜기; 그 밖에 step 125/127 「남은 것」.

- Step 126 (키 비주얼 기울인 화면 가로 늘어남, 사용자 버그 10-20) 완료 — `docs/steps/step_126.md`. `compose.tilted` = 실제 Y축 24° 회전 +
  핀홀 투영 (같은 θ·카메라, 2× 슈퍼샘플), `perspective_check.py` 5/5 (투영 폭 = 원본의 0.729, 기대 0.728), 키 비주얼 · 정사각 · 키트 6 ·
  스토어 featured · 트레일러 재생성. **바로 다음 할 일**: 사용자 결정 (업로드 또는 다음 단계); 열린 것: step 125 「남은 것」.

- Step 125 (홍보 장면 모델 교체 + 이름 Maya Workflow Kit + README, 사용자 지시 10-20) 완료 — `docs/steps/step_125.md`.
  - 이름: 보이는 글자 전부 Maya Workflow Kit (`src/allset/names.py`, 템플릿 폴더 `Maya_Workflow_Kit`, zip `maya-workflow-kit-<ver>.zip`),
    내부 id `allset` 그대로; 결정 12 개정 (사용자 결정, 상표 위험, 대체 이름 Workflow Kit for Maya Users); README = 「Maya Workflow Kit for
    Blender」 (https://github.com/5hyuns/maya-workflow-kit-for-blender, 비공개 예정, manifest website 없음).
  - 장면: Blender Studio Rain / Pack Bot / Security Bot 리그 + 4.5 스플래시 DOGWALK (CC BY 4.0), Cube Diorama · Poly Haven HDRI (CC0),
    `assets.json` 에 라이선스 문구, CREDITS.md, 이미지·영상에 작은 크레딧 + 상표 고지. 모든 Maya 모드 뷰포트 = Maya 그라디언트
    (`bg_check.py` 가 단색이면 FAIL).
  - 검증: 헤드리스 894/894, release_check / repo_check 11/11 / installer_check 9/9, 촬영·합성 검사 PASS.
  - 남은 것: pivot_snap 재녹화 불안정 (배포본은 정상 녹화본), manual_checks 「Step 125」.
  - **바로 다음 할 일**: step 126 = 키 비주얼 기울인 화면 가로 늘어남 (사용자 버그).

- Step 124 (홍보 디자인 재작업, 사용자 피드백 10-20) 완료 — `docs/steps/step_124.md`, 감수 `docs/distribution/marketing/design_review.md`.
  - impeccable critique (A/B 두 서브에이전트) 22/32 → 반영: accent = Maya 로고 틸 #00bcbb (설치본 아이콘 픽셀) + Autodesk Hello Yellow
    (동작 순간) + 검정, 대체 팔레트 `maya-ui`, 상표 메모 (`style.md`); 잠금업 `compose.lockup()` (for Maya Users = 0.66 ×) 모든 형식;
    영상 1.35 × · 가상 카메라 · 칩/클릭 펄스 · 전환 · 움직이는 타이틀/엔드 카드 (정적 ≤ 1.13 s, GIF ≤ 4 MB, 트레일러 33.5 s).
  - 킷 버그: 포즈/페인트 모드 「persp」 두 번 (에셋 셸프 헤더 띠, `ui/view_furniture.py`), 환영 창 본문 잘림 (`welcome.py`) + 테스트.
  - 남은 것: design_review 「Left」 (03 AE 초록 vs 캡션 빨강, 07 쿼터니언 행, 썸네일 핫박스 가독성 등), manual_checks 「Step 124」.
  - **바로 다음 할 일**: 사용자 결정 — 업로드 (manual_checks 117 / 123 / 124) 또는 다음 개발 단계. 열린 것: design_review Left, 툴바 떼기.

- Step 123 (클립 · 트레일러 · GIF · 마케팅 키트, 사용자 요청 10-19) 완료 — `docs/steps/step_123.md`, 결과 목록
  `docs/distribution/marketing/README.md`.
  - 클립 7 개 (hotbox, marking menu, Channel Box keys, navigation, pivot + V snap, Joint → IK → Paint Skin Weights, Maya ⇄ Blender
    스위치) = `clips/01–07_*.mp4` (1920 × 1080 H.264 30 fps, 0.4 – 1.3 MB) + `gif/01–07_*.gif` (960 px, 1.0 – 4.9 MB), 트레일러
    `clips/00_trailer.mp4` (38.8 초, 4.0 MB, 첫 프레임 = 키 비주얼). 키트 `kit/` (README 히어로, 소셜 프리뷰 1280 × 640, X 카드, Reddit
    두 장, YouTube 썸네일), `README_marketing.md`, `posts.md` (플랫폼 규칙 포함, 게시 안 함), listing.md C 갤러리 10.
  - 재생성: `python tools/marketing/make_clips.py` (녹화 `clips.py` = 틱마다 screenshot + 가상 시간, 합성 `clip_compose.py`),
    `python tools/marketing/kit.py`. 장면 도우미 `tools/marketing/scene.py` (shots.py 도 씀, step 122 이미지 바이트 동일 확인).
  - 남은 것: 다운로드 자리표시 · Reddit 규칙 직접 확인 (manual_checks 「Step 123」), 크로스페이드 중 캡션 띠 겹침 0.27 초.
  - **바로 다음 할 일**: 사용자 결정 — 업로드 (manual_checks 117 / 123: 버전 올리기, 자리표시 채우기) 또는 다음 개발 단계. 그 밖에
    열린 것: 환영 창 본문 잘림 · 「persp」 두 번 (122 에서 발견, 킷), 툴바 떼기, manual_checks 115–123.

- Step 122 (마케팅 카피 · 키 비주얼 · 캡션 스크린샷, 사용자 요청 10-19) 완료 — `docs/steps/step_122.md`, 결과
  `docs/distribution/marketing/` (copy.md, style.md, CREDITS.md, screens/01–10, key_visual(.png / _square), icon_256) + `docs/distribution/media/`.
  - 카피 = copy-masters 실행 (최종 「The tutorial ends. Your Channel Box comes back.」, 과정 점검 45/45), 디자인 = Maya 회색 + amber #ffb547 +
    Inter, 장면 = CC0 모델 (Poly Haven, Kenney, Quaternius), 재생성 `python tools/make_listing_media.py` (= tools/marketing/make_marketing.py).
  - 남은 것: 환영 창 본문 잘림, 「persp」 두 번 그려짐 (킷 쪽), 빈 폴더 `C:\previews` (사용자 삭제).
  - **바로 다음 할 일**: step 123 = 클립 6 + 트레일러 (MP4) + README 용 GIF + 마케팅 키트 (references.md §6, copy.md 캡션, style.md).
    그 밖에 열린 것: 사용자 업로드 (manual_checks 117), 툴바 떼기, manual_checks 115–120.

- Step 121 (인기 애드온 등록 페이지 레퍼런스 → 미디어 기준, 사용자 요청 10-19) 완료 — `docs/steps/step_121.md`,
  `docs/distribution/marketing/references.md` (원자료 `research/marketing_refs/`, 추적 안 함).
  - 공식 규칙 (사이트 소스): 미리보기 = JPEG / PNG / WebP 또는 **MP4** (GIF 불가), 16:9, 개수·크기 제한 없음, 영상 포스터 = 첫 프레임.
    `listing.md` C 의 「no GIF」 정정, 옛 사본 (5.0.0 문구) 삭제.
  - 미디어 기준 (§5): 대표 이미지 = 실제 화면 + 이름 + 한 줄, 갤러리 10 = 트레일러 30–45 초 + 클립 6 × 6–15 초 + 제목 정지 이미지 3, 캡션 전부,
    이미지 속 글자 제목만, extensions 설명에 GIF 없음.
  - 다음: step 122 (카피 · 키 비주얼).

- Step 120 (Maya 배경색 · Alt+B, 사용자 요청 10-19) 완료 — `docs/steps/step_120.md`, Maya 실측 `research/maya/re/background_120.md`.
  - Maya 2022: Alt+B = CycleBackgroundColor (전역: 0.36 → 0.631 → 그라데이션 #889db3/#0d0d0d → 검정), Ctrl+B = Bevel (그대로, 보조 연결 안 함
    delegated). 킷: 모든 3D View 에 같은 순환, 그라데이션 = Maya 테마의 LINEAR 그라데이션 (킷 테마일 때만, delegated), Windows >
    Settings/Preferences 하위 메뉴 + Color Settings 대화 상자 (`allset.color_settings`), 홍보 장면은 `reset_background()`.
  - 검증: 헤드리스 4.5 888/888 + 5.x 관련 41/41 × 3, GUI 4.5 전체 1135/1135, `gui_step120` 5.2.2 14/14; 화면 픽셀 ΔE00 팩토리 0.00,
    밝은 회색 0.61, 그라데이션 끝 ≤ 1.2, 가운데 ≈ 9 (Blender 의 섞기 곡선, 남은 것).
  - 다음: step 121 (미디어 레퍼런스).

- Step 119 (5.x 색 일치, 사용자 요청 10-19) 완료 — `docs/steps/step_119.md`, 테마 차이 `docs/compat_5x.md` 「테마 차이」.
  - 버전마다 테마 파일: `tools/make_theme.py` 가 각 Blender 에서 4.5 `studio_grey.xml` (그대로) + 5.x `studio_grey_5.0/5.1/5.2.xml`
    (4.5 값 + MOVED + `FIVE_X`, Blender 값으로 둔 10 키 `KEEP_FACTORY_5X`), `compat.theme_file` 이 고름. 5.0+ 셸프 아이콘 셰이더
    `compat.LINEAR_IMAGE_SHADER`, MOVED `channels_selected` 수정. 도구: `theme_diff.py`, `theme_xml_diff.py`, `version_compare.py`.
  - 검증: look_compare 네 버전 같음 (테마 0/38, 장면 3/3, 밀도 5/6, 격자 4/4), 4.5 대비 5.x ΔE00>5 0.83–0.97 % (배치만), 헤드리스
    880/880 × 4, GUI 4.5 1121/1121 + 5.x 색·레이아웃 6 파일 72/72 × 3, release_check 23/23 × 4.
  - 남은 것: 5.x Outliner 활성 행 외곽선 (테마 키 없음), manual_checks 「Step 119」.
  - 다음: step 120 (Maya 배경색 · Alt+B).

- Step 118 (Blender 5.x 호환, 사용자 요청 10-19) 완료 — `docs/steps/step_118.md`, 영향 목록·버전별 결과 `docs/compat_5x.md`.
  - 공식 5.x 마이너 최신 zip (5.0.1 / 5.1.2 / 5.2.2, sha256) → `C:/Users/ohnsk/AppData/Local/allset_blenders/` (저장소 밖, 설치기 없음).
  - 버전 분기는 `src/allset/compat.py` 한 곳 (기능 검사 우선, `test_step118_compat` 가 다른 곳의 `bpy.app.version` 을 막음): layered
    action F-curve, UV 섬 모드·루프 선택, `media_type`, `PoseBone.hide`, `pointmerge_facedata` 5.2, framebuffer 범위, 테마 MOVED =
    공식 5.0 이전 표 55 항목, Timeline 클래스·Marker 메뉴, 5.x Properties 새 탭 플래그 (템플릿 도크), 5.2 Ctrl+S 옵션, 재질 노드.
    버전 무관 수정: Maya → Blender 전환이 작업 공간을 창이 떠난 뒤 지움 (5.1.2 크래시), `preferences.set_quiet` (5.0 은 bpy.props dict 쓰기 불가), SDK 새 드라이버 키 삭제 + CONSTANT, 5.x IC 「Screen
    Editing」 Alt+F12 렌더 제거, 조각 브러시 3D View 문맥, 5.x 타임라인 = 한 줄 (사이드바가 열리지 않음).
  - 매니페스트 `blender_version_max = "5.3.0"` (4.5.x – 5.2.x), listing.md / DISTRIBUTION.md / audit / README / CLAUDE.md 갱신.
  - 검증: 헤드리스 877/877 (4.5.4, 5.0.1, 5.1.2, 5.2.2 각각), GUI 1121/1121 × 4 (5.1.2 는 수동 스윕을 두 세션으로 — 한 세션은 5.1.2 에서만 멈춤, 원인 미확정), release_check
    23/23 ×4, look_compare 테마 ΔE00 > 5 = 0/38 ×4 + 스크린샷 직접 확인.
  - **바로 다음 할 일**: step 119 = Maya 배경색·Alt+B 배경 순환 (hotkeySetup.mel 에서 실제 키 확인). 그 밖에 열린 것: 사용자 업로드
    (manual_checks 117; 0.2.0 → 지원 범위가 넓어졌으니 업로드 전 버전 올리기 권장), 툴바 떼기, manual_checks 115/116/118.

- Step 117 (배포 준비 4: 등록 자료 + 최종 검증, 0.2.0) 완료 — `docs/steps/step_117.md`. 업로드는 하지 않음 (사용자).
  - `docs/distribution/listing.md` = A 폼 필드 / B 긴 설명 (영어, "Not just a Maya keymap" 로 시작, 워크플로우 6 묶음, opt-in,
    되돌리기, 확장 밖 경로, exec·execfile·ctypes, 상표 고지) / C 미디어 표 / D 심사자용 고지. 미디어 `docs/distribution/media/`
    (아이콘 256, 대표 1920×1080, 묶음별 스크린샷 6장, Blender 로고 덮음) = `python tools/make_listing_media.py`.
  - manifest 0.2.0, tags + Rigging, `files` 사유 갱신, **지원 4.5.x 만** (4.2.23 25 실패, 5.0.1–5.2.2 19–23 실패 실측),
    `.ruff_cache/` 빌드 제외. moderation ruff 지적 10 건 수정. release_check 에 leftover_check (남는 파일 0).
    `extensions_audit.md` 「최종 상태」 표. CHANGELOG [0.2.0].
  - 검증: 헤드리스 4.5 869/869, release_check 24/24 (validate Success), GUI 전체 1121/1121.
  - **바로 다음 할 일**: 사용자 업로드 (manual_checks step 117). 개발은 step 118 = **Blender 5.x 호환** (layered actions 의
    `Action.fcurves`, 템플릿 도크 역할, 키맵 / UV / Target Weld — step_117.md 실패 목록) 후 `blender_version_max` 올리기. 그 밖에 열린 것:
    툴바 떼기, `ui/outliner.py` 안 쓰는 행 목록, manual_checks 115/116.

- Step 116 (사용자 지시 10-19: Maya 도킹 모델 — 패널마다 독립 창, ::::: 핸들로 떼기) 완료 — `docs/steps/step_116.md`.
  - CB/LE · AE · MTK 가 뷰포트 사이드바를 떠나 자기 영역 (`ui/maya_dock.py`: Tool 탭 Properties 편집기, 역할 = 숨은 탭 플래그,
    파일 저장·`area_dupli` 에도 유지). Allset 템플릿 = 뷰포트 오른쪽 탭 스택 (겹침 없음), 뷰포트 사이드바는 Blender 것.
  - 모든 Maya 패널 맨 위 ::::: 핸들: 클릭 = 떠 있는 창 (그 패널만), 떠 있는 창의 핸들 = Dock / Close, OS 창 닫기 = 자동 도킹.
    Tool Settings · Outliner 도 떼기·붙이기. 메뉴 맨 위 점선 = 떠 있는 메뉴 창. Windows 메뉴 / Ctrl+A / Status Line 토글 =
    Maya 처럼 탭 올리기, 스택이 없으면 떠 있는 창.
  - 검증: 헤드리스 869/869, GUI 전체 1119/1121 → 실패 2 파일 테스트 수정 후 단독 재실행 통과 (step54 5/5, step106 12/12),
    gui_step116_dock 20/20, release_check 전부 PASS, 스크린샷 직접 확인 (`tmp/shots116/`).
  - 남은 것: 툴바(Status Line·Shelf·Time Slider) 떼기, 끌어서 도킹(Python 불가), Maya 옆 탭(불가) — step_116.md.
  - **바로 다음 할 일**: step 117 = 배포 준비 4 (등록 자료 `docs/distribution/listing.md`, 최종 validate; 업로드는 사용자).

- Step 115 (배포 준비 3: no surprises — opt-in, 자동 저장 없음, 코드 없는 템플릿, draw 교체 정리) 완료 — `docs/steps/step_115.md`.
  - 활성화만으로는 아무것도 안 바뀜: `maya_mode` 기본 꺼짐, CORE = preferences / switch / 새 `welcome.py`. 환영 창·환경설정의
    「Make Blender feel like Maya」(`welcome.opt_in`) 또는 Maya | Blender 스위치로만 Maya 모드. 킷은 `save_userpref` 를 안 부름
    (Maya File > Save Preferences 메뉴만). 중단된 전환은 저장 없이 반복 복원, 낡은 스냅숏은 버림.
  - 앱 템플릿 = 데이터만 (`__init__.py` 삭제). 사용자 비활성화 / Remove (`addon_utils.disable(default_set=True)`) 때 마커 템플릿
    삭제, 종료·리로드·업데이트는 유지. Allset 템플릿 로드 뒤 키맵 재활성화는 keymap 모듈 (load_post + persistent 타이머).
  - draw: 덧붙이기만 하는 것은 prepend/append (Tool Box), 대신 그리는 것은 draw 목록의 Blender 자기 함수만 교체 (`ui/own_draw.py`:
    STATUSBAR / TOPBAR / OUTLINER / IMAGE 두 헤더), 나머지 (헬퍼·poll 래퍼) 는 `docs/distribution/listing.md` 에 이유·복원.
    ctypes keystate 는 None 대체 경로 확인·설명.
  - 검증: 헤드리스 864/864, GUI 1093/1093, release_check 전부 PASS, repo_check 11/11, installer_check 9/9, 환영 창 GUI 그림.
  - **바로 다음 할 일**: step 116 = 배포 준비 4 (등록 자료: `docs/distribution/listing.md` 에 이름·tagline·설명·태그·스크린샷,
    최종 validate; 업로드는 사용자).

- Step 114 (배포 준비 2: 확장 가이드라인 위반 2 건) 완료 — `docs/steps/step_114.md`.
  - `sys.modules["maya"]` 삽입 제거: `import maya.cmds` 는 Command Line / 셸프 / Script Editor 네임스페이스의 전용
    `__builtins__.__import__` (`command_line/runner._import`) 에서만 됨, 활성화·사용·끄기 뒤 `sys.modules` 에 maya 없음.
  - 자산: 패키지의 비코드 파일 5 개 모두 킷 생성물 → `src/allset/ASSETS_LICENSE.txt` (CC0-1.0), manifest `license` 에
    `SPDX:CC0-1.0` (validate PASS), README. 확장 zip 에서 `bl_info` 제거 (레거시 zip 은 build.py 가 manifest 로 붙임).
  - release_check 사이드바 탭 확인을 `allset_dock` 으로 → 전부 PASS, `docs/screenshots/` 다시 찍음.
  - 검증: 헤드리스 854/854, GUI 1093/1093, `extension validate` PASS.
  - **바로 다음 할 일**: step 115 = 배포 준비 3 (no surprises: opt-in — 설치 직후 키맵·환경설정·테마 적용 대신 환영 창에서
    확인 뒤, 자동 save_userpref 줄이기, 앱 템플릿 코드 최소화·제거 시 삭제, draw 교체를 가능한 곳은 append/prepend 로 —
    STATUSBAR / TOPBAR / IMAGE / VIEW3D 헤더, 남는 것은 설명에 이유·복원, keystate ctypes 설명, "Autodesk App Store" 라벨).
    그다음 116 (등록 자료, 업로드는 사용자).

- Step 113 (사용자 피드백: 상단이 Maya 같지 않음 — 메뉴 막대·Status Line·셸프·패널 바) 완료 — `docs/steps/step_113.md`.
  - Maya 2022 GUI 측정 (`research/maya/screens/top113/`: 1600×900 상단 그림, 위젯 위치, 셸프 8 개 구분선) → 차이 표 → 고침.
  - 메뉴 막대: 메뉴셋 드롭다운을 Status Line 맨 앞으로, 항목 폭 = 글자 + Maya 여백 (125 % 에서도 Help 까지), `Workspace:`
    드롭다운, Maya | Blender 는 테두리 없는 글자. Status Line: Maya 순서·그룹 (| … ▷), 접힌 그룹 공장값, 킷이 그린 Maya 풍
    아이콘 (`ui/status_icons.py`), 사이드바 토글 오른쪽 끝. 셸프: 머리 없이 WINDOW 에 18 px 탭 줄 + 아이콘 + 구분선,
    같은 그림이던 버튼에 새 글리프·배지. 패널 바 (`ui/panel_toolbar.py`): Allset 레이아웃 3D View = Maya 패널 메뉴 +
    패널 툴바 아이콘 줄. Maya 모드 전환 = Maya 테마 켬 (Blender 로 돌아가면 복원).
  - 검증: GUI `gui_step113_top` 10/10 (1.25 / 1.0, 화면 픽셀), 헤드리스 851/851, GUI 전체 1093/1093. 비교 그림
    `docs/steps/step_113/`.
  - 다음: step 114 (배포 준비 2).

- Step 112 (사용자 버그: 비치는 Channel Box 도크, 빈 Tool Box 띠; 2026-10-19 보고) 완료 — `docs/steps/step_112.md`.
  - 원인: Blender Region Overlap + Blender 테마의 영역 알파 0 → 도크 뒤로 뷰포트가 비침 (Maya 테마를 안 켠 사용자). 템플릿
    Tool Box 열 57 px < 125 % 의 도구 줄 70 px → Blender 가 도구 줄을 아예 안 그림, 커서 맞춤 실패 시 빈 띠 + 뷰포트 안 도구 줄.
  - 고침: Maya 모드 = Region Overlap 끔 (`prefs_preset` 그룹 `panels`, 「Solid Side Panels」, 백업·복원, FOOTPRINT), 템플릿
    열 90 px (`TOOLBOX_ROOM` 1.6), `toolbox.settle` (남는 폭 = 도구 줄 색, 오버레이 끔), `is_toolbox` 가 오버레이에 안 묶임.
  - 덤: 뷰가 도크 옆으로 좁아져 `framing.fit` 의 거리·이동 번갈아 맞추기가 진동 → 가운데 맞춘 상자에서 거리 탐색으로 다시 씀.
  - 검증: GUI `gui_step112_opaque` 9/9 (1.25 / 1.0, 화면 픽셀), 헤드리스 851/851, GUI 전체 1083/1083. 전후 그림
    `docs/steps/step_112/`.
  - 다음: step 113 (상단 Maya 모양) 이 끼어들어 배포 준비는 114–116 으로 밀림.

- Step 111 (배포 준비 1: 이름 변경 「Allset for Maya Users」 + 상표 정리; 사용자 결정 2026-10-19) 완료 — `docs/steps/step_111.md`.
  - 결정 12 (`docs/user_decisions.md`): extensions.blender.org 무료 배포, 이름 Allset for Maya Users, id `allset`, tagline
    "The whole Maya workflow in Blender, in one install". 근거 `docs/distribution/extensions_audit.md`, `naming.md`.
  - 패키지 `src/allset`, 연산자 `allset.` / 클래스 `ALLSET_` / 속성 `allset_*` / 환경 변수 `ALLSET_*`, 앱 템플릿 `Allset` (예전
    `MayaKit` 설치본 정리), 키맵 "Maya-style", 테마 "Studio Grey (Maya-inspired)", 핫박스 제목 "Allset", Help > Blender Extensions.
    README·환경설정 About·스플래시에 「한 조각씩이 아니라 워크플로우 전체를 한 번에」 메시지 + 영문 상표 고지문.
  - 검증: 옛 이름 0 (역사 문서·레거시 정리 줄 제외), 헤드리스 846/846, GUI 1074/1074, `extension validate` PASS. release_check 의
    사이드바 탭 확인 1 건 FAIL 은 이름 변경 전에도 같음 (남은 것).
  - **바로 다음 할 일**: step 112 = 배포 준비 2 (감사의 위반 2 건: `sys.modules["maya"]` 삽입 → exec 네임스페이스 전용, 자산 CC0
    표기). 그다음 113 (opt-in·정리·monkeypatch 줄이기), 114 (등록 자료, 업로드는 사용자).

- Step 110 (모델링·리깅 기능 빈틈; step_98.md #23, #28) 완료 — `docs/steps/step_110.md`.
  - mayapy 로 먼저 측정 (`research/maya/re/modeling_rigging_110.md`), 그 값으로 구현·테스트.
  - 모델링 (`operators/poly_maya.py`): Circularize (평균 반지름·등간격, Maya 값 일치), Connect (모서리 가운데 / 정점, 개수 일치),
    Make Hole (새로, 쿼드로 이음), Edit Edge Flow 규칙 개선 (구 적도 0.951 → 0.9971, Maya 0.9983).
  - 리깅 (`operators/rig_maya.py`): Reroot, Set / Assume Preferred Angle, Create IK Spline Handle, Hammer (= Maya), Add /
    Remove / Remove Unused Influence, Cluster (Hook + cluster1Handle), Nonlinear 4 종 핸들 + Twist, Soft Mod (Hook + Maya
    코사인 감쇠, 높이 Maya 와 소수 넷째 자리까지 같음).
  - 메뉴 작동: Modeling 47 %, Rigging 39.5 % (전 36 %). 검증: 헤드리스 846/846, GUI 1074/1074.
  - 남은 것: Edit Edge Flow 와 IK Spline 커브 맞춤의 정확한 Maya 규칙 (REA 디컴파일 제공자 미설치로 막힘), Make Hole 의 다른
    merge 모드, Flip 은 GUI Maya 측정 필요.
  - **바로 다음 할 일**: step_98 backlog 의 다음 항목 (`docs/PLAN.md` 「재점검 7차」 우선순위). 배포 결정 (decision 11) 은 사용자
    대기.

- Step 109 (셸프: Maya 순서, 회색 자리, 조각 브러시, Maya 풍 아이콘; step_98.md #7, quant §3) 완료 — `docs/steps/step_109.md`.
  - 공장 셸프 203 버튼이 모두 Maya 자리에 (탭별 38/43/26/18/14/25/29/10), 매핑 없는 52 개는 회색 + 안내 툴팁 / Help Line
    (`shelf_map.MENU` = 같은 runTimeCommand 의 Maya 메뉴 항목에서 동작·안내를 가져옴, 메뉴에 없는 3 개는 `shelf_map.NOTICES`).
  - 작동 98 → **151 / 203**: Sculpting 도구 = essentials 브러시 (Bulge = Inflate/Deflate, Freeze = Mask …), 새
    `operators/curve_tools.py` (Planar, Loft, Extrude, Bevel Plus, Offset Curve, Sweep Mesh, Pencil Curve, Add Points,
    NURBS Square / Cube / Cone — mayapy 측정 이름·값), FX 유체 용기 + 이미터 / Make Collide / nCloth 표시, 재질 5 종 등. 같은 동작을
    Maya 메뉴에도 매핑.
  - 아이콘 다시 그림: Maya 셸프에서 잰 셸프 색 + 도구 부분 #c0c0c0, 평면 2 톤. 첫 브러시 사용 시 에셋 로딩 취소 → 타이머 재시도.
  - 검증: 헤드리스 830/830, GUI 1074/1074, 나란히 그림 `research/maya/screens/step109/shelf_*.png` 8 장.
  - **바로 다음 할 일**: step 110 = 모델링·리깅 기능 (step_98.md #23, #28: Normals 도구 Soften/Harden·Set/Lock, …). 배포 결정
    (decision 11) 은 사용자 대기.

- Step 108 (메뉴의 Maya 단축키 글자와 Maya 메뉴 모양; step_98.md #12, #14) 완료 — `docs/steps/step_108.md`.
  - 메인 메뉴 57 항목에 Maya 키를 오른쪽 한 열로 (`ui/menu_hotkeys.py` ← `tools/gen_menu_hotkeys.py`; kit 이 Maya 뜻으로 묶은 키만),
    옵션 상자 표시도 그 열에. Blender 단축키는 안 보임 (연산자 항목은 `maya_kit.menu_item`, Blender Python 메뉴는 kit 하위 클래스,
    IC Shift+Ctrl+O 제거). File 메뉴는 1.25 배율 900 px 창에 Exit 까지 들어감.
  - 검증: 헤드리스 810/810, GUI 1063/1063, 나란히 그림 `research/maya/screens/step108/`.
  - **바로 다음 할 일**: step 109 = 셸프 (step_98.md #7: Maya 순서, 회색 자리, Sculpting 브러시). 그다음 110 모델링·리깅 기능.
    배포 결정 (decision 11) 은 사용자 대기.

- Step 107 (키맵: 틀린 일상 키, 없던 키, 미검토 분류; step_98.md #35–#36) 완료 — `docs/steps/step_107.md`.
  - 틀린 IC 키 제거 + Maya 뜻: Alt+R 대칭, Ctrl+I (반전 제거), F1 도움말, Alt+C 색 피드백, m 조각 세기, Ctrl+PgUp/PgDn 픽워크,
    Ctrl+, (환경설정 제거). 새 키: Ctrl+M / Shift+M / Ctrl+Shift+M, Alt+B, 스킨 페인트 u / n / b / Alt+F / Ctrl+Alt+C·V, 조각 Ctrl+0–9 /
    b / m, Graph Editor h / j, Time Slider 북마크 = 마커 (`operators/bookmarks.py`), Ctrl+F 검색.
  - `docs/keymap_mapping.md`: 구현 198 · IC 31 · 해당 없음 171 · **미검토 0** (219 에서).
  - 검증: 헤드리스 805/805, GUI 1060/1060.

- Step 106 (Tool Settings 도크 + Attribute Editor parity, step_98.md #20–#22) 완료 — `docs/steps/step_106.md`.
  - Maya 2022 GUI 측정 `research/scripts/maya_ts106/` → `research/maya/screens/ts106/` (Tool Settings 절·줄, 도크 자리, 토글, AE
    메뉴 막대·버튼·탭).
  - Tool Settings = 뷰포트 왼쪽 도크 (`ui/tool_dock.py`, Properties Tool 탭), 토글 두 번 → 닫힘. Move / Rotate / Scale 의 Maya 절이
    kit 상태에 묶임, 상태 없는 17 줄은 회색 + 툴팁 (`ui/tool_settings.py`).
  - AE: polyExtrudeFace1 기록 탭, 모디파이어 = Maya 노드 이름·타입, 메뉴 막대 7 개, Focus / Presets / Show / Hide, Notes, Select /
    Load Attributes / Copy Tab. Blender 설명문 (CB INPUTS, Project Window, AE nucleus / joint, Soft Selection) → 툴팁 (`notices.tip`).
  - 검증: 헤드리스 792/792, GUI 1060/1060 (sweep m68 재실행 포함), 나란히 그림 `research/maya/screens/step106/`.

- Step 105 (Hypershade / Render Settings / Script Editor 모양) 완료 — `docs/steps/step_105.md`.
  - Maya 2022 GUI 캡처 (`research/scripts/maya_editors105/`): 세 창 메뉴 막대 (329 잎), Hypershade Browser 탭, Render Settings
    공장값 (HD 540 960 × 540, PNG, padding 4, 단일 프레임) → `ui/editor_menu_data.py` 에 합침. 매핑 Hypershade 111/249,
    Render Settings 10/21, Script Editor 32/59, 회색은 모두 안내.
  - Hypershade: Shader Editor 헤더에 Maya 메뉴, Browser 견본 탭 7 + View 크기·정렬, Create 10 종 (Phong E, Anisotropic, Ramp,
    Layered, Use Background 새로), Create 메뉴 텍스처·유틸리티 → 노드. Render Settings: 표시한 Properties 창, Render Layer /
    Render Using, Common | 엔진 탭, Common 필드 → `scene.render`, Maya 프리셋 / Default Settings. Script Editor: Info 기록 위
    Text 입력, MEL / Python 탭, Ctrl+Enter / 숫자패드 Enter 실행 (IC 의 Ctrl+Enter 렌더 제거).
  - 검증: 헤드리스 777/777, GUI 1048/1048, 나란히 그림 `research/maya/screens/step105/`.
  - **바로 다음 할 일**: step 106 = backlog 8 「Tool Settings and Attribute Editor parity」 (step_98.md #20–#22). 그다음 107 키맵,
    108 메뉴 단축키 표시. 배포 결정 (decision 11) 은 사용자 대기.

- Step 104 (편집기 크롬: Graph Editor / Dope Sheet / UV Editor 의 Maya 메뉴 막대·아이콘 줄) 완료 — `docs/steps/step_104.md`.
  - Maya 2022 GUI 에서 세 창의 메뉴 막대·아이콘 줄을 캡처 (`research/scripts/maya_editors104/`, 메뉴 30, 잎 585, 옵션 상자 120,
    체크 169) → `ui/editor_menu_data.py` (생성). 매핑 339/585 (`ui/editor_menu_map.py`, 체크 항목 = Blender 속성
    `("prop", …)`), 회색 246 모두 안내. 새 연산자 `curve_infinity` / `curve_color`, In / Out Tangent, Dope Sheet 키 편집.
  - `ui/editor_chrome.py`: Graph / Dope 헤더 = 편집기 버튼 + Maya 메뉴 + 「Blender」 + 아이콘 줄 (클래스 자신의 draw 만 교체,
    복원, kit.py 스냅샷), UV = 메뉴 줄 + tool header 아이콘 줄 + 오른쪽 UV Toolkit (Options / Help). Graph Editor 채널 영역
    위에 Maya 목록 (pCube1 / Translate X 빨강 / Translate Y 초록, 액션·그룹 행 없음, 클릭 = 그 커브만). Dope Sheet 는 Summary
    + 접힌 오브젝트. 범위 밖 갈색 음영 0 (테마), 열 때 1 프레임부터, Graph / Dope 사이드바 숨김. Stats 칸 = 선택 키 시간 / 값.
  - 검증: 헤드리스 769/769, GUI 1041/1041 (step104 10), 나란히 그림 `research/maya/screens/step104/`.
  - **바로 다음 할 일**: step 105 = backlog 7 「Hypershade, Render Settings, Script Editor look」 (step_98.md #31–#33). 그다음
    106 Tool Settings · AE, 107 키맵. 배포 결정 (decision 11) 은 사용자 대기.

- Step 103 (진짜 옵션 창, Maya 모양) 완료 — `docs/steps/step_103.md`.
  - Maya 2022 GUI 에서 옵션 창 26 개를 열어 필드·기본값·버튼을 읽음 (`research/maya/re/option_boxes.md`). kit 옵션 창 26 개
    (`operators/option_windows.py`: 기본형 6, Duplicate Special, Group, Freeze, Reset, Combine, Smooth, Extrude, Bevel, Bridge,
    Merge, Bind Skin, Parent / Point / Orient, Set Key, Bake Simulation, UV Planar / Automatic, New Scene, Save Scene) —
    Maya 라벨·기본값, 명령 버튼 / Apply (창 유지) / Save · Reset Settings, 값 저장 후 메뉴 클릭도 그 값으로.
  - 옵션 상자 모양: 오른쪽 따로 누르는 □ 는 연속 메뉴 줄에서 계단 (재측정) → 버튼 하나 + 라벨 끝 ❒, 누르고 있기 = Option Box,
    왼쪽 창 아이콘 / Blender 말투 제거. 매핑된 옵션 상자 중 빈 것 0 (설정 없는 50 개는 「Blender 에 없음」 창).
  - 검증: 진짜 옵션 창 38 개, 헤드리스 757/757, GUI 1031/1031, 비교 그림 `research/maya/screens/step103/`.
  - **바로 다음 할 일**: step 104 = backlog 6 「Editor chrome: Graph Editor, Dope Sheet, UV Editor with Maya menus」
    (step_98.md #24, #26). 배포 결정 (decision 11) 은 사용자 대기.

- Step 102 (Maya 파일 I/O: 대화상자, Files of type, 프리셋, 기본 프로젝트) 완료 — `docs/steps/step_102.md`.
  - File > Import / Export All / Export Selection = 대화상자 하나 (`operators/file_io.py`): 오른쪽 Files of type (Maya Scenes
    .blend, FBX, OBJ, Alembic, USD, glTF, Import 는 Best Guess) + Maya cm / Y-up 프리셋 + Selection Only, 옵션 박스 = 그 패널.
    모든 파일 브라우저 왼쪽에 「Current Project」 (폴더 목록, Set Project...). 프로젝트가 없으면 기본 프로젝트
    `Documents/maya_kit/projects/default` (Maya `projects/default` 처럼), 시작 폴더 = Maya file rule.
  - mayapy 왕복 (`research/maya/re/file_io.md`): kit → Maya FBX / OBJ / ABC / USD 모두 10 × 20 × 5 cm Y-up, Maya → kit 네
    형식 모두 같은 크기. 검증: 헤드리스 747/747, GUI 1027/1027, 비교 그림 `research/maya/screens/step102/`.
  - **바로 다음 할 일**: step 103 = backlog 5 「Real option boxes for the top 30 commands, Maya look」 (step_98.md #11,
    quant §0). 배포 결정 (decision 11) 은 사용자 대기.

- Step 101 (메뉴 정직성: 회색마다 안내, 싼 매핑, 객체 모드에서도 활성) 완료 — `docs/steps/step_101.md`.
  - 메뉴 데이터: 생성기가 실행 시 항목을 채움 (Modify Naming / Pivot / Attributes, Help, Audio, Stereo, Cache = Alembic /
    Geometry / GPU Cache, #13 의 File Game Exporter·Create USD·Visualize Ghosting·Generate XGen 등; 라벨은 mayapy 측정,
    `research/maya/re/menu_honesty.md`). 회색 항목 = `notices.CATEGORIES` (경로 접두사 → 가장 가까운 Blender 기능).
  - 매핑 188 개 + kit 연산자 14 개 (`operators/menu_items.py`: Naming, Soften/Harden, Detach, Edge Flow, Wedge, Nonlinear,
    Template, Sculpting Tools, Checker, Audio, Stereo Camera …). 객체 모드 Edit Mesh = Maya 처럼 활성 (`menu_map.OBJECT_MODE`:
    전체 컴포넌트에 실행 또는 Maya 경고, mayapy 측정).
  - 검증: `tools/menu_count.py` 작동 42.5 % (전 29.6 %), 안내 없는 회색 0 (전 866); 헤드리스 739/739, GUI 1019/1019.
  - **바로 다음 할 일**: step 102 = backlog 4 「File I/O the Maya way」 (step_98.md #15–#19, quant §2: Open / Save As / Import /
    Export 대화상자, Files of type, 옵션, 기본 프로젝트). 배포 결정 (decision 11) 은 사용자 대기.

- Step 100 (기본 재질 lambert1 / initialShadingGroup) 완료 — `docs/steps/step_100.md`.
  - mayapy 측정: 새 shape → initialShadingGroup → lambert1 (color 0.5, incandescence 0, diffuse 0.8), Delete Unused 뒤에도 남음, 새
    Lambert = lambert2. kit: `operators/material.default_material` (표시 ID 속성 + fake user), 새 오브젝트 핸들러 + `create` 가
    MESH / SURFACE 에 넣음 (기존 오브젝트·사용자 파일은 그대로), 새 장면에 미리 생성, AE 에 shading group 탭 (initialShadingGroup /
    `<재질>SG`). Diffuse 0.8 은 Principled 입력이 없어 표현 못 함.
  - 검증: 헤드리스 725/725, GUI 1015/1015, dogfood 47/47, look_compare 그대로, 비교 그림 `research/maya/screens/step100/`.
  - **바로 다음 할 일**: step 101 = backlog 3 「Menu honesty: no unexplained greyed item, map the cheap ones」. backlog =
    `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 99 (첫 화면: Maya Outliner 기본 행, 125 % Tool Box, 도크 탭) 완료 — `docs/steps/step_99.md`.
  - Outliner: 새 장면에 persp / top / front / side (회색) + defaultLightSet / defaultObjectSet 를 그린 행으로 (`ui/outliner_sets.py`;
    진짜 카메라는 안 만듦, delegated), 줄무늬 없음. 오브젝트가 있으면 카메라 행이 DAG 행 뒤 (Blender C 행을 못 밂).
  - Tool Box: 커서를 영역 틈으로 잠깐 옮겨 area_move (`MAYAKIT_OT_fit_columns`), Outliner 도 260 × 배율 유지. 시뮬레이션 세션에선 꺼짐.
    타이머 `show_region_toolbar` 크래시 (닫힌 창) 수정.
  - 도크: Maya 이름의 사이드바 세로 탭 3 개 (`maya_kit_dock` 과 양방향), Maya 제목 줄 자리 빈 줄, CB / LE 절반 분할 + LE 목록 끝까지.
    Item 탭 (C 패널) 은 숨길 수 없음 (측정).
  - 검증: GUI step99 12/12 (1.25, 1.0), look_compare pixels 25/34 일치 (전 19/31), rects 5/12 (9/12 는 Blender 고정 높이 구조로 불가 —
    step_99.md 「남은 것」). 전체 테스트 수치는 step_99.md.
  - **바로 다음 할 일**: step 100 = backlog 2 「Default material lambert1 (initialShadingGroup) like Maya」. backlog =
    `hermes/autodrive_bmk/backlog.json` (step 98 의 12 개). 배포 결정 (decision 11) 은 사용자 대기.

- Step 98 (재점검 7차, 정밀 비판 「이건 Maya여야 한다」) 완료 — `docs/steps/step_98.md`, 수치 부록 `docs/steps/step_98_quant.md`,
  PLAN 「재점검 7차(정밀 비판)」.
  - Maya 2022 와 kit 를 1600x900 로 같은 장면 (첫 화면, 5 메뉴 세트 전 최상위 메뉴, 셸프 탭, File 대화상자·옵션, 모델링·UV·애니·리깅·FX·렌더
    창) 을 띄워 나란히 113 쌍 `research/maya/screens/audit7/pairs/` (Maya 스크립트 `research/scripts/maya_audit7/`, kit 세션
    `tmp/audit7_session.py`). 차이 36 항목 점수화.
  - 수치: 메뉴 1251 중 작동 370 (29.6 %), 회색 881 중 866 이유 없음, 진짜 옵션 창 6/500, 셸프 98/203, 키 미검토 219 (잘못된 동작 7),
    실제 Maya 메뉴 최상위 746 중 kit 에 없는 것 약 60 (Audio·Stereo 빈 메뉴).
  - 가장 큰 차이: 빈 Outliner, **125 % 에서 Tool Box 열이 빔** (이 PC 실제 배율), 회색 메뉴, 옵션 박스, Blender 파일 브라우저, lambert1 없음,
    Import/Export 하위 메뉴, UV / Graph / Hypershade 창이 Blender 모양.
  - 고친 버그 2: Channel Box 핸들러 AttributeError (File Browser / Preferences 창 컨텍스트, `tests/test_step98_audit_fixes.py`),
    Create Reference 의 「.ma 를 Import」 안내 문구.
  - 이어서 끝낸 것: Joint Tool 메뉴 실행은 정상 (첫 세션의 클릭 순서 탓), Properties 창 rna enum WARN 고침 (`menu_extras.properties_tab_later`),
    속도 측정 (create 1.6 ms · extrude 2.5 ms · Hypershade 창 58 ms · Render Settings 창 65 ms).
  - 검증: 헤드리스 719/719, kit 세션 PASS (콘솔 traceback 0), Maya 촬영 146 장.
  - **바로 다음 할 일**: step 99 = backlog 1 「First screen: Maya Outliner rows, Tool Box at 125 %, dock tabs」. backlog 12 개 =
    `hermes/autodrive_bmk/backlog.json` (사본 `backlog_98.json`), PLAN 「재점검 7차」 우선순위 1–12 와 같음. 배포 결정 (decision 11) 은 사용자 대기.

- Step 97 (manual_checks 정리 2) 완료 — `docs/steps/step_97.md`. **재점검 6차 backlog (90–97) 모두 끝.**
  - `tests/gui/gui_manual_sweep.py` 에 step 59–79 의 시뮬레이션 가능 57 항목 (`[M<step>-<n>]`) → `docs/manual_checks.md` 369 항목 중 [x] 70
    (전 13), 수동 299. step 81–96 절 분류 (사람 판단 10 · 불가 1 · 시뮬레이션 가능 38) 는 step_97.md 「분류」.
  - 찾아 고친 kit 버그 10 (step_97.md 「한 것」): 매니퓰레이터 누른 채 멈춤, Tweak 커브 / 본 드래그, Shift+Q 탭 툴, Shift+G 반복, SDK 1 cm 키 병합,
    CB 사용자 속성 clamp, 프리셀렉트가 압출 화살표 가로챔, J / Alt+J 렌더 슬롯 키 없음, Ctrl+O 가 프로젝트 scenes 에서 안 열림,
    「Maya Pivot」 Move 축이 다음 오브젝트에 남음. 헤드리스 회귀 `tests/test_step97_sweep_fixes.py`. `tests/gui/run.py` 에 파일별 `GUI_TIMEOUT`.
  - 검증: 헤드리스 718/718, GUI 1003/1003 (sweep 331), dogfood 47/47 (콘솔 0).
  - **바로 다음 할 일**: 계획된 단계 없음 (backlog 90–97 끝). 사용자 결정 대기 — (1) 배포 결정 (decision 11, `docs/DISTRIBUTION.md`),
    (2) 재점검 7차 (대응표·키맵 미검토 219 행·manual_checks), (3) manual_checks step 81–96 의 시뮬레이션 가능 38 항목 이어서 옮기기.

- Step 96 (Outliner Sets) 완료 — `docs/steps/step_96.md`. **대응표 UI 마지막 Partial 종결 (UI 9/0/0/0, 합계 30/1/0/2 = 91 %).**
  - 세트 = 씬에 연결 안 한 컬렉션 (`operators/sets.py`, mayapy 측정 `research/maya/re/sets.md`: set1/set2…, 선택 유지, select = 멤버). Create > Sets > Set (❑) /
    Quick Select Set..., Select > Quick Select Sets 매핑. 레이아웃 Outliner (Blender C 목록) 밑에 세트 행을 그림 (`ui/outliner_sets.py`: framebuffer 한 줄 + 이진 탐색으로
    마지막 행, 클릭 = 멤버 선택 / Ctrl 토글 / 삼각형 = 멤버 행, RMB = 세트 메뉴). 사이드바 kit Outliner 에도 SET 행.
  - 검증: 헤드리스 713/713, GUI 718/718, dogfood 47/47.
  - **바로 다음 할 일**: step 97 = manual checks 정리 2 (step_88.md 「분류」 의 step 59–79 시뮬레이션 가능 58 항목을 tests/gui 로, 체크 표시).
    backlog 의 마지막 항목. backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 95 (V 스냅 확대) 완료 — `docs/steps/step_95.md`.
  - step 81 의 「확대하면 V 스냅이 안 걸림」 은 kit · 확대 · 가림 검사 탓이 아니라 Blender 가 스냅 대상을 10 ms 에 한 번만 찾는 것
    (`transform_snap.cc` transform_snap_mixed_apply) + 시뮬레이션이 이동을 한 틱에 몰아 보낸 것. 확대하면 드래그가 길어 첫 이동이 정점에서 멀었음.
    `tests/gui/gui_step95_v_snap.py` (기본 / 확대 × X 화살표 → 앞·안쪽 정점, 가운데 핸들) 이동을 틱마다 → 모두 붙음. kit 코드 변경 없음 (delegated),
    manual check (빠르게 끌어 바로 놓기) 추가, CLAUDE.md 주의 한 줄.
  - 검증: 헤드리스 704/704, GUI 708/708.
  - **바로 다음 할 일**: step 96 = Outliner Sets (research/README.md 대응표의 Outliner 행이 Sets 없어서 Partial, step_82.md 「남은 것」).
    그다음 97 manual checks 정리 2. backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 94 (피벗 편집 RMB 마킹 메뉴) 완료 — `docs/steps/step_94.md`.
  - D / Insert 피벗 편집 중 RMB = Maya buildObjectMenuItemsNow 편집 모드 메뉴 (N Pin ☐ · NW/NE Snap Orientation/Position ☐ · S/SE/SW Reset ·
    E Exit, research 위치). Reset = 오브젝트 delta_location 0 / 컴포넌트 커서 → bbox 중심, Pin 꺼짐 (Maya 기본) = 선택이 바뀌면 사용자 컴포넌트
    피벗 해제 (`operators/pivot_menu.py`, `hold.ComponentPivotEdit`).
  - 검증: 헤드리스 704/704, GUI 702/702, dogfood 47/47.
  - **바로 다음 할 일**: step 95 = backlog 6 「V snap when zoomed in」 (step_81.md 「남은 것」: 확대 상태에서 V 점 스냅이 안 걸림 — GUI 재현, 원인,
    고치거나 한계로 문서화). backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 93 (선택 마스크 다듬기) 완료 — `docs/steps/step_93.md`.
  - Shift+Q 메뉴 체크 상자 (Poly Vertices / Poly Edges / Faces = 메시 선택 모드), **선택 마스크를 New / Open 너머로 유지** (Maya 2022 GUI 측정:
    마스크는 세션 상태라 초기화되지 않음 — backlog 문구와 반대, `research/maya/re/selection_masks.md`), Tool Settings 맨 위 Reset Tool
    (`ui/tool_settings.py`: 툴 옵션 기본값 + Maya Move/Rotate/Scale 기본값).
  - 검증: 헤드리스 698/698, GUI 698/698, dogfood 47/47.
  - **바로 다음 할 일**: step 94 = backlog 5 「Pivot-edit RMB marking menu」 (D / Insert 피벗 편집 중 RMB: N Pin, S Reset, NE Snap pivot position, NW Snap
    pivot orientation, E Exit). backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 92 (Graph Editor 키 묶음) 완료 — `docs/steps/step_92.md`.
  - t = 현재 시간 가운데 (가로만), Alt+/ = Snap Time To Selection **토글** (Maya 관찰: 켜면 키 선택마다 가장 이른 선택 키로 시간; View 메뉴 체크),
    i 홀드 = Insert Key 툴 (MMB → 정수 프레임에 모양 유지 키, 새 키만 선택). Maya 동작 명세 `research/maya/re/graph_editor_keys.md` (QTest 관찰).
    대응표 구현 155 · 미검토 219.
  - 검증: 헤드리스 692/692, GUI 693/693, dogfood 47/47.
  - **바로 다음 할 일**: step 93 = backlog 4 「Selection mask polish」 (Shift+Q 마킹 메뉴 체크 표시, 새 장면 / 열기에서 마스크 초기화, Tool Settings
    Reset Tool). backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 91 (뷰 표시 수정) 완료 — `docs/steps/step_91.md`.
  - 템플릿 3D 뷰 부모 관계 점선 끔 (Maya 2022 실행으로 선 없음 확인, `research/maya/screens/parent/`), 마킹 메뉴가 HUD (Adjust Last Operation) 위에
    그려짐 (`draw.REGION_TYPES` + 'HUD', 4.5 / 5.2 측정, 대조 실험), 독 = Channel Box 패널 하나가 CB / AE / MTK 를 그림 → Channel Box 탭이 Item 밑으로
    안 감 (AE 제목 줄도 없어짐).
  - 검증: 헤드리스 685/685, GUI 685/685, dogfood 47/47.
  - **바로 다음 할 일**: step 92 = backlog 3 「Graph Editor key batch」 (t = 현재 시간 가운데, Alt+/ = 선택 키로 시간, i 홀드 = Insert Key 툴).
    backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 90 (전역 키 묶음 4) 완료 — `docs/steps/step_90.md`.
  - Ctrl+X cut (계층째, 빈 data 도) + Ctrl+V paste (첫 노드 lead), Alt+X Walk (IC X-ray 제거), Alt+\ 재생 범위 = 애니메이션 범위, Alt+1/2/4 보이기
    토글, Ctrl+` / Shift+~ / Ctrl+Shift+~ 스무드 프록시 (`operators/global_keys4.py`), Edit > Cut / Paste. 대응표 구현 152 · IC 15 · 미검토 222.
  - 검증: 헤드리스 685/685, GUI 677/677, dogfood 47/47.
  - **바로 다음 할 일**: step 91 = backlog 2 「Viewport chrome fixes」 (부모 관계 점선 끄기, RMB 목록이 HUD 위로, AE 전환 때 사이드바 탭 순서).
    backlog = `hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 사용자 대기.

- Step 89 (재점검 6차) 완료 — `docs/steps/step_89.md`, `docs/PLAN.md` 「재점검 6차」.
  - 대응표 29/2/0/2 (88 %; 타임라인 Done), 키맵 구현 142 · 미검토 237, manual_checks [x] 13 / 348. 탐색 세션 19/19: 부모 관계 점선이
    그려짐, RMB 목록이 Adjust Last Operation 패널 밑, AE 전환 때 사이드바 탭 순서. blindspot 7 (Ctrl+X, Alt+X Walk, Alt+\, Graph t / Alt+/,
    Alt+1/2/4, 스무드 프록시 키, Ctrl+PgUp/Dn).
  - 검증: 헤드리스 677/677, dogfood 47/47, 세션 19/19 (콘솔 0).
  - **바로 다음 할 일**: step 90 = backlog 1 「Global key batch 4」 (Ctrl+X, Alt+X, Alt+\, Alt+1/2/4, 스무드 프록시 키 + IC 행 정리).
    backlog = `hermes/autodrive_bmk/backlog.json` (8개, 사본 backlog_90.json). 배포 결정 (decision 11) 은 사용자 대기.

- Step 88 (manual_checks → GUI 테스트 정리) 완료 — `docs/steps/step_88.md`. **재점검 5차 backlog (81–88) 모두 끝.**
  - `tests/gui/gui_manual_sweep.py` 46 검사로 step 59–79 의 13 항목 확인 → `docs/manual_checks.md` 348 항목 중 [x] 13 (맨 위 자동 / 수동 수).
    step 59–79 분류: 자동 13, 사람 판단 23, 시뮬레이션 불가 7, 시뮬레이션 가능하지만 아직 안 옮김 58.
  - 검증: 헤드리스 677/677, GUI 667/667, dogfood 47/47.
  - **바로 다음 할 일**: 계획된 단계 없음. 사용자 결정 대기 — (1) 배포 결정 (decision 11, `docs/DISTRIBUTION.md`), (2) 재점검 6차 (대응표·키맵 미검토
    237 행·manual_checks 다시 매기기), (3) manual_checks 의 시뮬레이션 가능 58 항목 이어서 옮기기 (step_88.md 「분류」).

- Step 87 (뷰 키 묶음 3) 완료 — `docs/steps/step_87.md`.
  - Alt+A 표시 순환 (X-ray 조인트 / 전부 / 메시만), Alt+P persp ↔ ortho, Alt+화살표 1 px 이동, ` 홀드 = Tweak 툴, \ 홀드 = 카메라 뷰 2D 팬/줌
    (`operators/view_keys3.py`). 대응표 생성기: 셀 `|` = `&#124;` + 열 수 검사. 키맵 구현 142, 미검토 237.
  - 검증: 헤드리스 677/677, GUI 621/621, dogfood 47/47.
  - **바로 다음 할 일**: step 88 manual_checks → GUI 테스트 정리 (재점검 5차 backlog 마지막; step 59–79 항목 중 시뮬레이션 가능한 것을
    tests/gui 로, 체크 표시). backlog = `hermes/autodrive_bmk/backlog_81.json`. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 86 (Dope Sheet · NLA · Node Editor 선택 수식) 완료 — `docs/steps/step_86.md`.
  - SELECT_RULES 에 action / nla / node 클릭·박스 6 규칙 + Ctrl+Shift+LMB 기존 항목 3 개 제거 (select_leftright ×2, node viewer). Node 는 Maya 그대로
    (deselect / toggle), Dope Sheet / NLA Ctrl 은 토글 (Graph 와 같은 한계), Node Ctrl+드래그 = Blender 링크 떼기 유지.
  - 검증: 헤드리스 671/671, GUI 611/611, dogfood 47/47.
  - **바로 다음 할 일**: step 87 뷰 키 묶음 3 (Alt+A CycleDisplayMode, Alt+P CameraModeToggle, Alt+화살표 뷰 nudge, backtick, 백슬래시 + `Shift+\`
    표 행 이스케이프). 그 뒤 88 manual_checks → GUI. backlog = `hermes/autodrive_bmk/backlog_81.json`. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 85 (매니퓰레이터 Ctrl+축 / Shift+MMB) 완료 — `docs/steps/step_85.md`.
  - W / R 매니퓰레이터 축 Ctrl+LMB 드래그 = 나머지 두 축 평면 이동 / 스케일 + 그 평면이 활성 핸들, Move 가운데 Ctrl+클릭 = 활성 핸들 해제,
    Shift+MMB 드래그 = 첫 움직임에 가까운 축 (`operators/manip.py` manip_ctrl / manip_mmb_auto). Rotate 는 C 기즈모 그대로.
  - 측정: Ctrl 을 누른 채 시작한 이동은 스냅 반전 안 됨; 시뮬레이션에서 MMB CLICK_DRAG 항목은 불리지 않음 → PRESS + 모달.
  - 검증: 헤드리스 667/667, GUI 601/601, dogfood 47/47.
  - **바로 다음 할 일**: step 86 Dope Sheet · NLA · Node Editor 선택 수식 (Shift 토글 / Ctrl 해제 / Ctrl+Shift 추가; keymap/maya_patches.py
    SELECT_RULES 확장, step 84 의 Dopesheet LMB PRESS 맨 앞 항목 (TIMELINE 만) 고려). 그 뒤 87 뷰 키 묶음 3, 88 manual_checks → GUI.
    backlog = `hermes/autodrive_bmk/backlog_81.json`. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 84 (타임 슬라이더 Shift 범위 키 이동·늘이기) 완료 — `docs/steps/step_84.md`.
  - Shift 범위 가운데 드래그 = 범위 안 키 이동, 끝 화살표 = 반대 끝 기준 늘이기, 덮어쓰기, 언두 한 단계, 흰 화살표 (`operators/time_range.py`,
    `ui/time_slider.py` `time_range_drag`). 측정: `FCurve.update()` 는 같은 프레임 키를 합침 → 드래그 중엔 sort + handles_recalc 만.
  - 측정: 템플릿 Time Slider 줄은 전부 Blender 스크럽 띠 ("Time Scrub" 키맵이 Dopesheet 보다 먼저, IC 엔 없어 Blender 기본 것이 쓰였음) →
    Maya 키컨피그에 "Time Scrub" 을 만들고 kit 항목을 앞에 (step 56 의 범위 밖 클릭 = 해제도 이제 템플릿에서 동작).
  - 검증: 헤드리스 662/662, GUI 594/594, dogfood 47/47. 대응표 타임라인 행 → Done (Once / Oscillate 는 Blender 한계).
  - **바로 다음 할 일**: step 85 매니퓰레이터 Ctrl+축 = 평면 이동, Shift+MMB 자동 축 (`ui/manipulator.py`; 기즈모 키맵이라 「계획」 먼저).
    그 뒤 86 Dope Sheet·NLA·Node 수식, 87 뷰 키 묶음 3, 88 manual_checks → GUI. backlog = `hermes/autodrive_bmk/backlog_81.json`.
    배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 83 (키 삽입·이동 묶음) 완료 — `docs/steps/step_83.md`.
  - Alt+I / Ctrl+Shift+W/E/R = 곡선 모양 그대로 키 삽입 (Blender insert 는 auto 구간만 지킴 → 그 밖은 de Casteljau 분할), Shift+( / ) = 키 1 프레임
    이동 (키 에디터 = 선택 키, 그 밖 = 현재 시간 키 + 시간), Ctrl+Alt+, / . = 이전 / 다음 키 선택 + 이동 (`operators/key_insert.py`). 키맵 구현 133.
  - 검증: 헤드리스 656/656, GUI 585/587 (gui_step26 RMB 취소 간헐 2, 단독 통과), dogfood 47/47.
  - **바로 다음 할 일**: step 84 타임 슬라이더 Shift 범위 키 이동·늘이기 (모달이라 「계획」 먼저; `key_insert.move_keys`, `time_keys.time_range` 재사용).
    그 뒤 85 매니퓰레이터 Ctrl 평면, 86 Dope Sheet·NLA·Node 수식, 87 뷰 키 묶음 3, 88 manual_checks → GUI.
    backlog = `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_81.json`. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 82 (Outliner 드래그 = Maya 부모 지정) 완료 — `docs/steps/step_82.md`.
  - Outliner MMB 드래그 = Maya: 항목 위 = 자식으로, 행 사이 = 그 자리 (정렬 끔일 때 순서까지), 빈 곳 = 월드. 월드 위치 유지, parent inverse
    identity, 선택 그대로 (`operators/outliner_drag.py`). Blender LMB 드롭도 언두 후 Maya 방식으로 다시 적용 (언두 한 단계).
  - 측정: Blender 의 정렬 끈 Outliner 는 목록의 첫 항목을 맨 뒤에 그림 → 템플릿 정렬은 켜 둠 (delegated).
  - 검증: 헤드리스 646/646, GUI 579/579, dogfood 47/47.
  - **바로 다음 할 일**: step 83 키 삽입·이동 묶음 (Alt+I, Ctrl+Shift+W/E/R, Shift+( ), Ctrl+Alt+, .; backlog_81.json 3번).
    그 뒤 84 Shift 범위 키 이동, 85 매니퓰레이터 Ctrl 평면, 86 Dope Sheet·NLA·Node 수식, 87 뷰 키 묶음 3, 88 manual_checks → GUI.
    backlog = `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_81.json` (backlog.json 은 없음). 배포 결정 (decision 11) 은 여전히 사용자 대기.

- **체크포인트 (2026-10-18, /sc:save) — 지금 단계 = 없음 (step 81 까지 완료, 다음 = step 82)**
  - HEAD `06bfd06` = step 81. 작업 트리는 깨끗하다 (research/ 는 원래 추적 안 함; 이 체크포인트 줄만 미커밋).
  - 이번 세션: step 76–79 (재점검 4차 backlog 끝) → step 80 재점검 5차 (c74dead, f45557c) → step 81 persp 화각 (06bfd06).
  - 검증 (HEAD): 헤드리스 637/637, GUI (기본 배율) 559/559, dogfood 47/47.
  - **바로 다음 할 일**: step 82 Outliner 드래그 = Maya 부모 지정 (드롭/키맵 충돌이라 `docs/steps/step_82.md` 「계획」 부터).
    그 뒤 83 키 삽입·이동, 84 Shift 범위 키 이동, 85 매니퓰레이터 Ctrl 평면, 86 Dope Sheet·NLA·Node 수식, 87 뷰 키 묶음 3, 88 manual_checks → GUI.
    backlog = `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json`. 배포 결정 (decision 11) 은 여전히 사용자 대기.
  - 열린 발견: 끌고 가는 오브젝트가 화면에서 크면 V 스냅이 안 걸림 (시뮬레이션, step_81.md 「남은 것」, 손 확인 필요).

- Step 81 (Maya persp 화각) 완료 — `docs/steps/step_81.md`.
  - 템플릿 뷰 렌즈 35 → 70 (Blender 72 mm 센서 기준 = Maya 35 mm / 36 mm, 수평 54.4°), 모든 3D 뷰. Create > Camera = Maya 35 mm / 36 mm,
    Ctrl+Shift+C 카메라도 35. 새 장면 그리드 크기가 Maya 와 같아짐 (뷰 폭의 0.75, Maya 0.73).
  - 검증: 헤드리스 637/637, GUI 559/559 (gui_step59 화면 크기 맞춘 뒤), dogfood 47/47.
  - 발견: 끌고 가는 큐브가 화면에서 크면 V 스냅이 안 걸림 (시뮬레이션) → manual_checks, step_81 「남은 것」.
  - **바로 다음 할 일**: backlog 2 = step 82 Outliner 드래그 = Maya 부모 지정 (키맵/드롭 충돌이라 「계획」 먼저). 그 뒤 83 키 삽입·이동,
    84 Shift 범위 키 이동, 85 매니퓰레이터 Ctrl 평면, 86 Dope Sheet·NLA·Node 수식, 87 뷰 키 묶음 3, 88 manual_checks → GUI.

- Step 80 (재점검 5차) 완료 — `docs/steps/step_80.md`, `docs/PLAN.md` 「재점검 5차」.
  - 대응표 28/3/0/2 (85 %), 키맵 구현 125 · 미검토 254, manual_checks 320 열림 (체크 0). 4차 backlog (72–79) 모두 종결.
  - 새 발견: MayaKit persp 가 Maya 의 두 배 광각 (템플릿 뷰 렌즈 35 = Blender 72 mm 센서 기준 91.6°, Maya 54.4° = Blender 70).
  - 검증: 헤드리스 634/634, dogfood 47/47, 탐색 세션 15/16 (실패 1 은 세션 탓), 콘솔 0.
  - **바로 다음 할 일**: `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 8개 순서대로 (step 81부터) —
    1 Maya persp 화각 (렌즈 70), 2 Outliner 드래그 = Maya 부모 지정, 3 키 삽입·이동 묶음, 4 타임 슬라이더 Shift 범위 키 이동,
    5 매니퓰레이터 Ctrl+축 평면 / Shift+MMB, 6 Dope Sheet·NLA·Node 선택 수식, 7 뷰 키 묶음 3, 8 manual_checks → GUI 테스트.
    배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 79 (3D Cut and Sew UV Tool) 완료 — `docs/steps/step_79.md`. **재점검 4차 backlog (72–79) 모두 끝.**
  - UV > 3D Cut and Sew UV Tool: 3D 뷰에서 엣지를 따라 드래그 = UV 자르기, Ctrl = 꿰매기, Shift = 선택, x / s / d = Cut / Sew / Unfold + Layout,
    셸 경계 흰 굵은 선, 누를 엣지는 빨간 프리셀렉트. 메뉴·셸프·UV Toolkit·UV 마킹 메뉴에서 진입.
  - 검증: 헤드리스 634/634, GUI 555/555, dogfood 47/47.
  - **바로 다음 할 일**: 계획된 단계 없음. 사용자 결정 대기 — (1) 배포 결정 (decision 11: 이름·id, 무료/유료, 계정, CC0, 서명;
    `docs/DISTRIBUTION.md`), (2) 재점검 5차 (대응표·키맵 미검토 254 행·manual_checks 다시 매기기), (3) PLAN 「Left out」 나머지와
    각 step 문서 「남은 것」 (예: Cut and Sew 툴 마킹 메뉴, Shift+Q 체크 표시, Graph Editor 보기 버튼, 피벗 편집 RMB 메뉴).

- Step 78 (키 묶음 2) 완료 — `docs/steps/step_78.md`.
  - Graph Editor 1/2/3 (Stacked = Normalized + 안내), Shift+Q / Alt+Q 선택 툴 마킹 메뉴 (픽 마스크 / 정점·엣지·면·UV), Ctrl+Alt+←/→ Spin Edge,
    Shift+G 마우스 위치 반복, Ctrl+Shift+C 뷰에서 카메라. 키맵 구현 113 → 122.
  - 검증: 헤드리스 627/627, GUI 549/549, dogfood 47/47.
  - **바로 다음 할 일**: step 79 3D Cut and Sew UV 툴 (PLAN 「Left out of steps 54–67」 점수 20; 3D 뷰 엣지 클릭/드래그 = 자르기,
    Ctrl = 꿰매기, x/s/d = Cut/Sew/Unfold; step 66 `operators/uv_tools.py` 의 uv_cut / sew 재사용). 툴 모달이라 「계획」 먼저.
    79 가 재점검 4차 backlog 의 마지막. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 77 (편집 모드 Insert / D 피벗) 완료 — `docs/steps/step_77.md`.
  - 메시 편집 모드 Insert = D 와 같은 피벗 편집 (커서 툴 + 3D 커서 피벗) 토글. 면을 클릭하면 피벗 방향도 맞고, 끝나면 Move 축 "Maya Pivot".
    탭 = 사용자 피벗 지움 (bbox 중심). 대응표 D/Insert → Done (85 %).
  - 검증: 헤드리스 619/619, GUI 539/539, dogfood 47/47.
  - **바로 다음 할 일**: step 78 키 묶음 (Graph Editor 1/2/3, Shift+Q / Alt+Q, Ctrl+Alt+←/→ Spin Edge, Shift+G, Ctrl+Shift+C;
    `docs/keymap_mapping.md` 미검토 행). 그 뒤 79 3D Cut and Sew. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 76 (선택 우선순위) 완료 — `docs/steps/step_76.md`.
  - 오브젝트 모드 클릭이 Maya 처럼 IK 핸들 (10) > 조인트 = 아마추어 (9) > 커브 (4) > 메시 (2) 순으로 겹친 것 중 고른다 (가려져도).
    `operators/select_priority.py`, "3D View" CLICK / Tweak PRESS 앞 PASS_THROUGH_FIRST, 환경설정 「Selection Priority」.
  - 검증: 헤드리스 612/612, GUI 528/528, dogfood 47/47.
  - **바로 다음 할 일**: step 77 편집 모드 Insert / D 피벗 (컴포넌트 매니퓰레이터 피벗, research/maya/interaction.md D/Insert 행).
    그 뒤 78 키 묶음 (Graph 1/2/3, Shift+Q / Alt+Q, Spin Edge, Shift+G, Ctrl+Shift+C), 79 3D Cut and Sew.
    backlog = `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_72.json`. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- **체크포인트 (2026-10-18, /sc:save) — 지금 단계 = 없음 (step 75 까지 완료, 다음 = step 76)**
  - HEAD `10e6fd5` = step 75. 작업 트리는 깨끗하다 (research/ 는 원래 추적 안 함).
  - 이번 세션: step 71 재점검 4차 (8f4b596) → backlog 8개 (step 72–79) 중 72 (90ec5db) · 73 (9936fef) · 74 (46e43c9) · 75 (10e6fd5) 완료, 각 STEP_DONE.
  - 검증 (HEAD): 헤드리스 604/604, GUI (기본 배율) 516/516, dogfood 47/47.
  - **바로 다음 할 일**: step 76 선택 우선순위 (클릭 시 핸들 10 > 조인트 9 > 커브 4 > 메시 2, research/maya/interaction.md:74, defaults.json:105).
    키맵 충돌 설계라 `docs/steps/step_76.md` 「계획」 부터.
  - 그 뒤 77 편집 모드 Insert, 78 키 묶음 (Graph 1/2/3, Shift+Q / Alt+Q, Spin Edge, Shift+G, Ctrl+Shift+C), 79 3D Cut and Sew.
    backlog.json = `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json`.
  - 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 75 (Status Line 입력 줄) 완료 — `docs/steps/step_75.md`.
  - Status Line 에 Maya 입력 줄 (Absolute / Relative X Y Z, Rename, Select by Name) 과 회색 Construction History 를 넣었다 (`ui/input_line.py`).
  - 검증: 헤드리스 604/604, GUI 516/516, dogfood 47/47.
  - **바로 다음 할 일**: step 76 선택 우선순위 (조인트·커브·핸들이 메시보다 먼저, research/maya/interaction.md:74). 키맵 충돌 설계라 「계획」 먼저.
    그 뒤 77 편집 모드 Insert, 78 키 묶음, 79 3D Cut and Sew.

- Step 74 (프리셀렉트 확대) 완료 — `docs/steps/step_74.md`.
  - 엣지 / 면 모드와 Move / Rotate / Scale 툴에서도 Maya 처럼 커서 아래 컴포넌트를 빨갛게 미리 보인다 (Python 기즈모 `operators/preselect.py`).
  - Maya 2022 실측: 오브젝트 모드에는 하이라이트가 없다.
  - 검증: 헤드리스 596/596, GUI 510/510, dogfood 47/47.
  - **바로 다음 할 일**: step 75 Status Line 입력 줄 (abs / rel / rename / select by name, research/maya/ui_layout.md:208-211).
    그 뒤 76 선택 우선순위, 77 편집 모드 Insert, 78 키 묶음, 79 3D Cut and Sew.

- Step 73 (타임 슬라이더 키 틱 + Range Slider 드래그) 완료 — `docs/steps/step_73.md`.
  - 선택 노드의 키가 Maya 처럼 1 px 빨간 선 (브레이크다운 초록).
  - MayaKit 타임라인 헤더의 Range Slider 바를 끌어 재생 범위를 옮기거나 끝을 바꾼다. 더블클릭 = 전체 범위.
    바는 `ui/range_bar.py` 가 헤더 한 줄을 읽어 자리를 찾고 직접 그린다.
  - 검증: 헤드리스 589/589, GUI 504/504, dogfood 47/47.
  - **바로 다음 할 일**: step 74 프리셀렉트 확대 (엣지·면·오브젝트, Move/Rotate/Scale 툴 중; step 30 기즈모). 그 뒤 75 Status Line 입력 줄,
    76 선택 우선순위, 77 편집 모드 Insert, 78 키 묶음, 79 3D Cut and Sew.

- Step 72 (상단 바 다시 그리기 + Maya 인뷰 메시지) 완료 — `docs/steps/step_72.md`.
  - F2–F6 이 상단 메뉴 바를 바로 다시 그린다 (`status_line.redraw_top_bars`).
  - Maya 실측대로 인뷰 메시지 (`ui/view_message.py`): F8 (`maya_kit.toggle_sel_mode`), Ctrl+G, Ctrl+H / Alt+H / h, b 소프트 선택 켬, Make Live.
  - 검증: 헤드리스 581/581, GUI 496/496, dogfood 47/47.
  - **바로 다음 할 일**: backlog 2 = step 73 타임 슬라이더 키 틱 + Range Slider 드래그 (모달이니 step_73 「계획」 먼저).
    그 뒤 74 프리셀렉트 확대, 75 Status Line 입력 줄, 76 선택 우선순위, 77 편집 모드 Insert, 78 키 묶음, 79 3D Cut and Sew.

- Step 71 (재점검 4차) 완료 — `docs/steps/step_71.md`, `docs/PLAN.md` 「재점검 4차」. 대응표 27/4/0/2 (82 %, 3차 25/6/0/2),
  키맵 구현 113 · IC 10 · 미검토 267, manual_checks 287 열림. 새 발견: F2–F6 이 상단 메뉴 바를 다시 그리지 않음 (전역 영역),
  타임 슬라이더 키 틱 없음. 헤드리스 574/574, GUI (기본 배율) 483/483, dogfood 47/47, 탐색 세션 14/15 (실패 1 = 세션 확인 오류).
  **바로 다음 할 일**: `hermes/autodrive_bmk/backlog.json` 8개 순서대로 (step 72부터) — 1 메뉴 바 다시 그리기 + 인뷰 메시지,
  2 키 틱 + Range Slider 드래그, 3 프리셀렉트 확대, 4 Status Line 입력 줄, 5 선택 우선순위, 6 편집 모드 Insert, 7 키 묶음,
  8 3D Cut and Sew. 배포 결정 (decision 11) 은 여전히 사용자 대기.

- Step 70 (Graph Editor 탄젠트 툴바 · Shift+S · G · Auto Key · Playblast) 완료 — `docs/steps/step_70.md`. Graph Editor 헤더 탄젠트 아이콘 줄 + 고스트 커브,
  `maya_kit.set_tangent` / `key_edit` (Graph Editor 선택 키, 그 밖은 현재 시간 키), Shift+S 홀드 = Keys / Tangents 마킹 메뉴, Graph Editor G = 재생 범위 · D = Auto,
  Maya Auto Key (Only Insert Available, 백업·복원), `maya_kit.playblast` (임시 동영상 + 플레이어, □ 옵션 대화상자).
  헤드리스 574/574, GUI 0.8 484/484, gui_step70 7/7, dogfood 47/47.
  **바로 다음 할 일**: PLAN 의 워크플로우 단계 (54–70) 가 모두 끝남. 다음은 사용자 결정: (1) 배포 결정 (이름·id, 무료/유료 — decision 11, `docs/DISTRIBUTION.md`),
  (2) 남긴 후보 (`docs/PLAN.md` 「Left out of steps 54–67」 + 각 step 문서 「남은 것」: 3D Cut and Sew, Quad Draw Make Live, Maya Animation 워크스페이스, MASH, 3D 유체,
  Outliner Sets, Hypergraph, Graph 1/2/3, 버퍼 커브 스왑 등) 중 고르기, 또는 재점검 4차 (전체 갭 표 다시 매기기).

- Step 69 (씬 관리: 프로젝트 · 증분 저장 · 레퍼런스) 완료 — `docs/steps/step_69.md`. `operators/project.py`: Project Window / Set Project / Recent Projects
  (루트 + Maya 폴더 + 표시 파일, add-on 환경설정), 파일 창이 `<root>/scenes` 에서 (Ctrl+O/S/Shift+S, 메뉴, Status Line), 프로젝트 안 저장 → 렌더 `//../images/`,
  Ctrl+Alt+S = Maya 증분 (`shot_v001.0001`), Ctrl+R Create Reference = 링크 + library override + `ns:` 이름, Reference Editor = Outliner Blender File 창.
  헤드리스 566/566, GUI 0.8 477/477, gui_step69 7/7, dogfood 47/47.
  **바로 다음 할 일**: step 70 — Graph Editor 탄젠트 툴바 · Shift+S · G · Auto Key · Playblast 플레이어 (근거 `research/maya/workflows/animation.md`;
  `operators/time_keys.TANGENTS` 표). `docs/steps/step_70.md` 「계획」 먼저 (키맵 충돌). 70 이 PLAN 의 마지막 워크플로우 단계.

- Step 68 (FX: 시뮬레이션 스케일 · nucleus · 이미터 · nCloth · nCache) 완료 — `docs/steps/step_68.md`. `operators/fx.py`: g = maya_unit / Space Scale
  (중력 9.8·g, 길이 × maya_unit, 천 강성·감쇠 × g — 측정), `Scene.maya_kit_nucleus` + AE 「nucleus1」 탭, Create Emitter (`emitter1` + `nParticle1`),
  Emit from Object, nCloth / Passive / Remove / 강체를 선택 전부에, `maya_kit.ncache` (포인트 캐시 · 강체 · GN · Mantaflow). 측정: 파티클·강체는 1 m 장면과
  정확히 같음, Blender 하한 0.001 m (충돌 거리·두께·파티클 크기 = 0.1 유닛). 헤드리스 560/560, GUI 0.8 470/470, gui_step68 8/8, dogfood 47/47.
  **바로 다음 할 일**: step 69 — 씬 관리: Set Project · Ctrl+Alt+S 증분 · Create Reference + 네임스페이스 · Reference Editor (근거
  `research/maya/workflows/scene.md`). `docs/steps/step_69.md` 「계획」 먼저. 그다음 70 Graph Editor.

- Step 67 (Hypershade · Light Editor · Render 메뉴 · Keep Image · AE 맵 버튼) 완료 — `docs/steps/step_67.md`. `maya_kit.hypershade` = Shader Editor 새 창 +
  사이드바 「Hypershade」 탭 (Browser 미리보기 · Create · Assign Material To Selection · Property Editor; 메뉴·Status Line·핫박스 Windows 메뉴 공통),
  `maya_kit.light_editor` = 3D View 새 창 + 「Light Editor」 탭 (이름·색·Intensity·켜기·Solo, AE 라이트 섹션), Render 메뉴 17 항목 복원 (gen_menu_data
  `PLACEHOLDERS`), Render Result 헤더 Keep / Remove Image (render slots), AE 소켓 행 맵 버튼 (File/Ramp/Noise/Checker, Bump, Break Connection),
  standardSurface 이름 표 + aiStandardSurface. 측정: `Region.active_panel_category` 는 탭이 그려진 뒤 설정 가능 (전엔 read-only 오류).
  이어서: Render Settings = 언제나 새 Properties 창 (Render 탭, 타이머로 탭 설정), AE 라이트 Decay Rate 회색 행.
  헤드리스 550/550, GUI 0.8 460/462 (gui_step26 RMB 취소 2 항목 — 혼자 3/3 통과, 전체 실행 때만 나는 간헐 실패), gui_step67 10/10, dogfood 47/47.
  **바로 다음 할 일**: step 68 — FX: Maya 시뮬레이션 스케일 · nucleus · nParticles 이미터 · nCloth · nCache (근거 `research/maya/workflows/fx.md`,
  결정 10). `docs/steps/step_68.md` 「계획」 먼저. 그다음 69 씬 관리, 70 Graph Editor.

- Step 66 (UV 워크플로우) 완료 — `docs/steps/step_66.md`. UV Editor 열기 = 편집 모드 + UV Sync (창 하나만), `maya_kit.uv_component`
  (F12 UV / Alt+F12 UV Shell / 3D RMB E UV), UV Editor RMB 마킹 메뉴 (Maya texturePanelMenus.mel 방향) + Shift+RMB UV / UV Shell 도구,
  Cut (솔기 + 2e-4 분리 — Blender 섬 계산은 솔기를 무시, 측정) / Sew (작은 셸 닮음 변환) / Unfold (Unwrap Minimum Stretch, 셸 자리 유지) /
  Layout (pack, 패딩 px) / Texel Density, 키 Shift+X · Shift+S · Ctrl+U · Ctrl+L, UV Toolkit 사이드바 탭. 헤드리스 539/539, GUI 0.8 452/452,
  gui_step66 6/6, dogfood 47/47.
  **바로 다음 할 일**: step 67 — Hypershade 창·Light Editor·Render 메뉴·Render View Keep Image·AE 맵 버튼 (근거 `research/maya/workflows/render.md`).
  계획 먼저.

- Step 65 (Extrude 매니퓰레이터·In-View Editor·마지막 연산 INPUTS) 완료 — `docs/steps/step_65.md`. `maya_kit.extrude` = Maya polyExtrudeFace
  (mayapy 8 경우와 좌표 일치: Thickness shell · Local Translate Z · Offset · Divisions · Keep Faces Together), Ctrl+E/메뉴/마킹 메뉴/셸프/MTK.
  마지막 압출 = `Record` (압출 전 BMesh, 상태 서명; 언두/리두 따라감) → `maya_kit.extrude_edit` 로 다시 만들기 (언두 한 단계, F9 = Maya 이름).
  파란 화살표 기즈모 (Local Translate Z), In-View Editor 상자 (행 드래그/클릭 입력/토글), Channel Box INPUTS 맨 위 polyExtrudeFace1 + 안내.
  발견: 파이썬 `bpy.ops` 호출은 `undo=True` 없이는 언두를 쌓지 않음. 헤드리스 529/529, GUI 0.8 445/446 (step 18 Ctrl+E 기대 갱신 후 14/14),
  gui_step65 7/7, dogfood 47/47.
  **바로 다음 할 일**: step 66 — UV 워크플로우 (UV Editor 진입·UV Toolkit·UV 마킹 메뉴·Cut/Sew/Unfold/Layout·Texel Density; 근거
  `research/maya/workflows/uv.md`). 계획 먼저.

- Step 64 (Target Weld · Crease Tool · Multi-Cut 감각) 완료 — `docs/steps/step_64.md`. Target Weld = 킷 툴 (`register_tool`, LMB 드래그 모달,
  선택된 정점도 함께, Target/Center, 엣지 짝 병합), Crease Tool = 킷 툴 (MMB 좌우 드래그, Maya 값 ↔ Blender √(c/10), 실측 sharpness 10·b²),
  Multi-Cut (knife) Ctrl+클릭 = 클릭 자리 엣지 루프 / Ctrl+MMB 가운데 / Shift+클릭 = Snap Step % 시작점 + Tool Settings Maya 항목. 메뉴·마킹 메뉴·
  셸프·MTK 연결. 키맵 매핑 nameCommand 조회 고침 (Ctrl+Shift+X/Q 구현). 헤드리스 516/516 (+1), GUI 0.8 439/439, gui_step64 12/12, dogfood 47/47.
  **바로 다음 할 일**: step 65 — Extrude 매니퓰레이터 (Python GizmoGroup) + In-View Editor + 마지막 연산 INPUTS 행 (근거
  `research/maya/workflows/modeling.md` A3·A4, 히스토리 사후 수정 20 / Ctrl+E 15). 계획 먼저 (GPU·모달).

- Step 63 (Modeling Toolkit 도크·소프트 선택 Maya 단위·Combine/Separate/Mirror/Boolean) 완료 — `docs/steps/step_63.md`. MTK = dock 세 번째 항목
  (modeling_03 순서, 버튼 = 메뉴 동작, Status Line 토글 맨 앞), Maya 실측 (mayapy): 소프트 선택 반경 5, Combine = pCube2 + bbox 중심 피벗, Separate =
  그룹 아래 polySurfaceN. Mirror = bmesh 적용 + □ Mirror Options (`run_action` 이 `option_box` 속성 연산자에 넘김). 헤드리스 505/505, GUI 0.8 426/427
  (step 3 B 드래그 기대값 갱신 후 17/17), gui_step63 8/8, dogfood 47/47.
  **바로 다음 할 일**: step 64 Target Weld·Crease 툴·Multi-Cut 감각 (근거 `research/maya/workflows/modeling.md` 갭 표; MTK Tools 의 Target Weld 회색을 연결).

- Step 62 (Set Driven Key·포즈 모드 제약·Add Attribute·Blend Shape·Quick Rig) 완료 — `docs/steps/step_62.md`. SDK 창 = dock 의 CB 아래
  (Driver/Driven 스크롤 목록, Key · Load Driver · Load Driven · Close; 결과 = 드라이버 F-커브 키 = Maya animCurveUU), 창이 열린 동안 CB 로 바꾼 피동 값은
  드라이버 mute 로 유지 → Key/Close 가 풂; Constrain 이 포즈 모드면 본에; Modify/CB Edit > Add·Edit·Delete Attribute (CB 라벨 = Maya nice name);
  Blend Shape = join_shapes; Quick Rig = Rigify 켜기 + 메타 리그. CB 커스텀 속성 쓰기가 이제 depsgraph 를 태그 (드라이버 갱신). 헤드리스 495/495,
  GUI 0.8 417/419 (step 26 간헐, 재실행 통과), gui_step62 9/9 (tx 0.5 → ry 45), dogfood 47/47.
  **바로 다음 할 일**: step 63 Modeling Toolkit 도크·소프트 선택 Maya 단위·Separate/Combine/Mirror Maya 의미 (근거 `research/maya/workflows/modeling.md`).

- Step 61 (배포 방식 조사·결정, 공개 안 함, 사용자 요청 2026-10-18) 완료 — `docs/steps/step_61.md`, 비교·추천 `docs/DISTRIBUTION.md`,
  결정 `docs/user_decisions.md` 11. 추천 (delegated): 무료 GPL 핵심판 = 자체 정적 저장소 먼저 (`tools/build_repo.py` → `dist/repo/index.json`)
  → extensions.blender.org 제출; exe 선택 (초안 `tools/installer/`, 컴파일·서명 안 함); 유료는 별도 상품; 포터블 묶음 안 함. 사용자 결정 대기:
  이름·id (Autodesk 지침상 제품 이름에 "Maya" 금지), 무료/유료, 계정·공개 이메일, 바이너리 CC0, exe 서명. 왕복 검증: release_check 11 PASS,
  `tools/repo_check.py` 10/10 (설치·업데이트 0.1.0→0.1.1·Remove), `tools/installer_check.py` 9/9, 헤드리스 486/486.
  **바로 다음 할 일**: step 62 Set Driven Key·포즈 모드 제약·Add Attribute·Blend Shape (근거 `research/maya/workflows/rigging.md` 후보 D).

- Step 60 (Maya ⇄ Blender 스위치·완전 되돌리기, 사용자 요청 2026-10-18) 완료 — `docs/steps/step_60.md`. 확장은 켜진 채 「Maya 모드」 =
  MODE 하위 패키지 register/unregister (`switch.py`, 재시작 없음). 전환: 상단 바 오른쪽 「Maya | Blender」 (두 모드), 환경설정 맨 위 스위치·
  「Restore Blender Settings」, Edit 「Switch to Maya Mode」 / Windows 「Switch to Blender」 (F3), Ctrl+Alt+Shift+M. 켜기 = 스냅숏
  (`switch_snapshot.json`) + 템플릿 레이아웃을 "Maya" 워크스페이스로, 끄기 = 이전 워크스페이스·스냅숏 복원 (아직 Maya 값인 것만).
  Maya 테마 표시 = 테마 이름 "Maya" (filepath 아님: 확장 Remove 가 filepath 파일이 사라지면 테마를 리셋, `bl_extension_ops.py:1233-1270`).
  헤드리스 482/482, GUI 0.8 410/410, release_check 전부 PASS, dogfood 47/47. 남은 것: 명령줄 `extension remove` 는 복원 불가 (안내 필요).
  **바로 다음 할 일**: step 61 배포 방식 조사 (공개는 안 함; 명령줄 Remove 안내 포함), 그다음 62 Set Driven Key …

- Step 59 (피벗 개념·스냅 전부·Maya 모양 매니퓰레이터, 사용자 요청 2026-10-18) 완료 — `docs/steps/step_59.md`, Maya 실측
  `research/maya/workflows/pivot_snap.md`. D / Insert = 피벗만 (Translate·형상·자식 불변, 피벗 회전 = 「Maya Pivot」 방향), Reset / Bake /
  Match Pivots, 오브젝트 = lead 피벗·컴포넌트 = bbox 중심, X/C/V/J = 매니퓰레이터 중심 스냅 (X 절대 그리드), Step Snap, Snap Align Objects,
  Snap Together Tool, Make Live (+ Status Line 칸), Move/Scale = Maya 모양 Python 기즈모 (Rotate 는 C 링 유지), Tool Settings 「Move Settings」,
  W/E/R 메뉴 = 툴별 축 슬롯. 헤드리스 478/478, GUI 399/399 (0.8; 1.25 는 step 37/51/9 기존 실패 — step 59 와 무관, 문서 참고), dogfood 47/47.
  **바로 다음 할 일**: step 60 「켜고 끄는 스위치·완전 되돌리기」 (사용자 요청 2026-10-18: 언제든지 Maya 모드로 / 원래로; 기존
  `maya_kit.make_maya` / `revert_maya` (`src/maya_kit/first_start.py`) 확인부터. step 59 가 바꾼 것 — 툴 위젯 교체, 템플릿 툴 기본값,
  pivot 감시자 — 도 되돌리기 대상). 그다음 61 배포 방식 조사 (공개는 안 함), 62 Set Driven Key·포즈 모드 제약·Add Attribute·Blend Shape
  (근거 `research/maya/workflows/rigging.md` 후보 D), 63 MTK 도크 … 70 Graph Editor (PLAN 표 번호를 3 씩 뒤로 미룸).

- Step 58 (IK Handle·Bind Skin·Paint Skin Weights·가중치 복사/미러) 완료 — `docs/steps/step_58.md`. `maya_kit.ik_handle` (시작·끝 조인트
  클릭 또는 두 조인트 선택 → 끝 조인트로 들어오는 본에 IK + chain_count, 목표 `ikHandleN`), Pole Vector (자세 유지 각), Bind Skin (순서 무관,
  메시 부모 안 됨, Max Influences, Selected Joints), Unbind, Paint Skin Weights (웨이트 페인트 + 아마추어 자동 포즈, 도크 맨 위 Influences 목록·
  Replace/Add/Scale/Smooth·Value·Flood), Copy / Mirror Skin Weights (반사 위치로 조인트 짝), Copy / Paste Vertex Weights.
  헤드리스 462/462, GUI 384/384 (0.8) · 383/383 (1.25), dogfood 47/47.
  **바로 다음 할 일**: step 59 「Set Driven Key·포즈 모드 제약·Add Attribute·Blend Shape」 (근거 `research/maya/workflows/rigging.md`
  후보 D). 그다음 60 … 67.

- Step 57 (Joint Tool·Orient/Mirror Joint·포즈 픽워크) 완료 — `docs/steps/step_57.md`. Skeleton > Create Joints / 셸프 = `maya_kit.joint_tool`
  (클릭마다 조인트, 정사영 = 원점 뷰 평면 / persp = 바닥, Enter → 포즈 모드, `skeleton1` / `jointN`, XYZ, CB lead = 마지막), Orient Joint /
  Mirror Joints = Maya 옵션 창 (`invoke_props_dialog`; Y 축 안내, 평면·Behavior·검색/치환), 포즈 모드 ↑↓←→ = 조인트 pick-walk, 포즈·아마추어
  편집 모드 P / Shift+P = 조인트 부모 지정 (제자리). 헤드리스 451/451, GUI 376/376 (0.8) · 375/375 (1.25), dogfood 47/47.

- Step 56 (Time Slider·키 감각) 완료 — `docs/steps/step_56.md`. 타임라인 LMB = 시간 (Shift = 빨간 범위, MMB = 시간 + 안내), RMB = Maya Time
  Slider 메뉴 (Cut/Copy/Paste/Delete/Snap/Keys/Tangents/Playback Speed/Looping/Set Range to/Playblast), K + 드래그 = 어디서나 시간 (Mesh
  knife K 제거), S = 키 가능한 채널 전부 (`maya_kit.set_key`), Set Breakdown Key, Key > Delete Keys = 모든 키 (`keyframe_clear_v3d`),
  Cut/Copy/Paste Keys, CB 버튼 RMB 메뉴 맨 위 Key Selected 류. 헤드리스 442/442, GUI 365/365 (0.8) · 364/364 (1.25), dogfood 47/47.
  67 의 Graph Editor 탄젠트는 `operators/time_keys.TANGENTS` 재사용.

- Step 55 (포즈 본 = Maya 조인트: CB·Outliner·AE·제약 가중치) 완료 — `docs/steps/step_55.md`. 포즈 모드에서 CB lead/targets = 활성/선택
  본 (경로 `pose.bones["n"].…`, 키·브레이크다운·뮤트·잠금·숨김·Key Selected·`+=` 입력·MMB 슬라이더가 본에), 쿼터니언 본 「Rotate Order
  XYZ」, 편집 모드 「Placing joints」, Ctrl+Tab 포즈 모드; INPUTS 제약 노드 `joint2_pointConstraint1` + `locator1W0` = influence, 제약
  채널 파랑 (눌린 버튼); kit Outliner JOINT 행 (클릭 = 포즈 모드 + 본); AE joint 탭 + 제약 탭. 헤드리스 430/430, GUI 356/356 (0.8) ·
  355/355 (1.25), dogfood 47/47.

- Step 54 (워크플로우 기반: 단위 생성 경로·조명·안내) 완료 — `docs/steps/step_54.md`. Create Joints / Type / Free Image Plane /
  필드 8 개 / 3D Container·Fire·Smoke 가 Maya 단위 (`create.KINDS`, `maya_kit.quick_smoke`), 조명 × maya_unit², 「Blender 에 없음」 안내 체계
  `ui/notices.py` (26 경로, 툴팁 + Help Line). 헤드리스 420/420, GUI 342/342 · 341/341, dogfood 47/47.
- Step 53 (Blender 5.x 호환·안전한 설치) 완료 — `docs/steps/step_53.md`. 대상 4.5 그대로, 매니페스트 `blender_version_max = "5.3.0"`.
  5.2.2 에서 처음엔 켜기 실패 (Timeline = Dope Sheet 모드) → 얇은 버전 분기 (time_slider, theme `_rna_xml` + MOVED, keymap STRICT/DRIFT,
  select_loops, 5.x 타임라인 버튼 위치). 헤드리스 4.5 / 5.0.1 / 5.1.2 / 5.2.2 모두 414/414, GUI 4.5 337/337 · 336/336, 5.2 337/337,
  다른 에디터 GUI 9/9 (두 버전), release_check: 설치가 사용자 애드온·테마·설정을 지키고 kit 을 끄면 전부 원래대로 (8 단언, 4.5·5.2),
  dogfood 47/47.
- Step 52 (핫박스·RMB 충실도) 완료 — `docs/steps/step_52.md`. 핫박스 = Maya 8 줄 (공통 + Cache/Help, 패널 메뉴, Recent | Maya | Controls,
  메뉴 세트 5 줄, Show All 기본), 대각 영역선, 영역 이름·어둡게 하기 없음; 마킹 메뉴·핫박스가 창 전체에 그려짐 (사이드바·타임라인 위);
  RMB 목록 = Maya 2022 순서 (「pCube1...」 → AE, Select All/Deselect All/Invert, Select Similar □, 회색 ▸ 9 개), 링 아래 (넘치면 열 나눔);
  버그: Segoe UI 에 ▸ 가 없어 목록 폭이 수백만 px (step 41 부터) → 화살표 삼각형. 헤드리스 407/407, GUI 328/328 · 327/327,
  픽셀 ΔE>5 5/31 (메뉴 3 지점 0.3), dogfood 47/47, release_check PASS.
- Step 51 (메뉴 옵션 박스·셸프 줄) 완료 — `docs/steps/step_51.md`. Maya 옵션 박스 494 항목 = 창 아이콘 + 길게 누르기 「Option Box」
  (같은 줄 두 번째 버튼은 메뉴가 계단처럼 깨짐), 셸프 줄 64 px = 탭 줄 (머리, #373737 로 어둡게) + kit 제작 32 px 컬러 아이콘 줄
  (`ui/shelf_icons.py`, 이미지 편집기 POST_PIXEL + 기즈모 풀 고르기). 헤드리스 398/398, GUI 314/314 (0.8) · 313/313 (1.25),
  look_compare density 6/6 (셸프 64, 아이콘 32), rects 5/12, 셸프 픽셀 4 지점 ΔE ≤ 2.4, dogfood 47/47, release_check PASS.
  후속: Status Line 그룹 접기 손잡이 (Maya openBar, `maya_kit.status_group`) — 헤드리스 399/399, GUI 316/316 · 315/315.
- Step 50 (에디터 크롬) 완료 — `docs/steps/step_50.md`. Channel Box: 패널 머리·톱니 대신 메뉴 줄 Channels/Edit/Object/Show, 상자 없는
  이름·SHAPES·INPUTS, Maya 빈 선택 문구; Layer Editor: Display/Anim 탭 + Layers/Options/Help; Outliner (Maya 식) 머리 = Display/Show/Help
  + 검색 (`ui/maya_outliner.py`), 눈 열 없음; Time Slider 오른쪽 (타임라인 사이드바) 현재 프레임 + 재생 버튼 8, 헤더 = Maya 순서 Range
  Slider (Blender 메뉴는 오른쪽 끝 설정 메뉴로). 헤드리스 392/392, GUI 309/309 (0.8; 1.25 고친 파일 다시 통과), 픽셀 ΔE>5 7 → 5/28,
  CB 행 16.0 px, dogfood 47/47.
- Step 49 (레이아웃 동등화) 완료 — `docs/steps/step_49.md`. MayaKit = Status Line 줄 / Shelf 줄 (헤더만 있는 두 영역) /
  [툴박스 열 (좁은 3D 뷰, Maya 툴만 그리기 필터, `ui/toolbox.py`) | Outliner 260 | 뷰 + 사이드바 도크 277] / Time Slider + 아래 Range
  Slider (헤더 뒤집음) / Help Line | Command Line 한 줄. 오른쪽 Outliner·Properties 열 없음 (AE = 도크, Render Settings = 새 창).
  사이드바 「Channel Box Dock Only」 (`ui/dock_tabs.py`, Item 의 C 패널은 남음). 생성기 `tools/make_startup.py` 는 이제 GUI Blender
  (헤드리스 area_close/join 불가). 헤드리스 385/385, GUI 307/307 (1.25·0.8), rects 1/12 → 4/12 (x/w 대부분 ✓, y 는 셸프 높이 = step 51).
  미해결 확인: step 42 사고로 사용자 실제 설정에서 node_wrangler 가 켜진 채 (사용자 확인 필요); step 40 의
  `research/scripts/maya_shots/shots.py` 는 화면 영역 캡처라 다시 돌리기 전에 위젯 캡처로 바꿀 것.
- Step 48 (Maya 고유 워크플로우 분석·계획) 완료 — `docs/steps/step_48.md`, `docs/PLAN.md` 「Maya 워크플로우 계획」, 결정 10
  (`docs/user_decisions.md`: 시뮬레이션 스케일 = Maya nucleus spaceScale 1 처럼). Maya 2022 를 실제로 띄워 7 분야 47 단계 기록
  (`research/scripts/maya_workflows/wf.py`, `research/maya/workflows/*.md` + shots, Maya 위젯만 찍음), 분야별 분석 7 개, blindspot 12 건,
  brainstorm (결정 8 개 delegated), 독립 검토 반영 (v2). backlog 14 개 → 단계 54–67 (큐의 49–53 뒤). 버그 수정: bevel exec 너비 Maya 단위.
  헤드리스 375/375, GUI step 18 14/14 (1.0·0.8), dogfood 47/47.
- Step 47 (선택 와이어) 완료 — `docs/steps/step_47.md`. `ui/selection_wire.py`: 선택 오브젝트의 평가된 엣지를 kit 이 직접 그림 (POST_VIEW,
  사용자 셰이더 + 깊이 바이어스, 오브젝트별 numpy 배치 캐시, 테마 리드/선택 색을 선형으로). Blender `show_wire` 는 선택 색을 테마 wire 쪽으로
  최대 19 % 섞어 (실측) 버림 — 그래서 ID 데이터에 아무것도 안 씀 (저장·언두 잔존 0). 템플릿 선택 외곽선 끔. viewport 10/12 (리드 0.2, 흰색 0.0),
  10 만 폴리 프레임 +3–14 %. 헤드리스 374/374, GUI 293/293 (1.0·0.8), dogfood 47/47.
- Step 46 (뷰 가구) 완료 — `docs/steps/step_46.md`. `ui/view_furniture.py`: ViewCube (Python 기즈모, 면 클릭 → view_axis, 평소 0.5,
  4 분할은 마우스가 있던 패널에만), 카메라 라벨 (persp / top −Z / front +Y / side −X, 카메라 이름), 축 삼각 (Blender 축) — Blender 내비 기즈모가
  꺼진 뷰에서; 템플릿은 내비 기즈모·텍스트 정보 끔. HUD 메뉴 Camera Names / View Axis / View Cube = 애드온 환경설정. look_compare
  `furniture.md` 3/3 ±10 px, 텍스트 오버레이 픽셀 0. 헤드리스 369/369, GUI 289/289 (1.0·0.8), dogfood 47/47.
- Step 45 (Maya 그리드) 완료 — `docs/steps/step_45.md`. 자체 GPU 그리드 `ui/maya_grid.py`: ±12 단위, 1 단위마다 1 px, 5 마다 2 px,
  축 2 px, 모두 테마 그리드 회색, 계단선, 깊이 검사. 바닥에만 (4 분할 front/side 는 그리드 없음 = Maya). 뷰별 상태 = Blender 바닥·정사영
  그리드 끔 + `overlay.grid_lines == 0` (delegated). Show > Grid / Display > Grid = `maya_kit.toggle_grid`. 템플릿 뷰 모두 켬.
  look_compare `grid.md`: 그리드선 200 점 ΔE00 0.7, 모서리 4/4 ±1 px. 그리기 0.22–0.27 ms. 헤드리스 362/362, GUI 283/283 (1.0·0.8),
  dogfood 47/47.
- Step 44 (Maya 위젯 감각) 완료 — `docs/steps/step_44.md`. 테마: 모든 위젯 각지고 평평 (roundness 0, shade·엠보스·메뉴 그림자 없음,
  panel_roundness 0). 환경설정 그룹 「Maya Density」 (`view.ui_scale` = 1 / OS 배율, 125 % 화면 → 0.8 = Maya 와 같은 픽셀), 「Maya Font」
  (Windows Segoe UI, 동봉 안 함), 「Aliased Wireframes」 — 백업/복원, Make Blender Maya 가 켬. CB 행 scale_y 0.8 (16 px). GUI 테스트
  `--ui-scale 0.8` + `sim.px()`. look_compare `density.md` 3/3 (메뉴바 26, 메뉴 항목 19.4, CB 행 16.0 px). 면 채움 α 재보정 0.28
  (step 43 기준 샷에 매니퓰레이터가 걸려 있었음). 헤드리스 356/356, GUI 1.0 281/281 · 0.8 281/281, dogfood 47/47.
  미해결 확인 (step 42): 사용자 실제 설정에서 node_wrangler 가 켜진 채 남음 (사용자 확인 필요).
- Step 43 (Maya 테마 v2 색) 완료 — `docs/steps/step_43.md`. 컴포넌트 (하늘색 와이어, 보라/연노랑 정점, 살구색 엣지·면 — 면은 Maya 점묘
  평균에 맞춘 알파), 매니퓰레이터 (Z = 실제로 그려지는 순파랑), Outliner (#373737, 리드 행 파랑, 이름 흰색), 탭, 현재 프레임 회색,
  3D 뷰 헤더·툴바·사이드바 불투명, 템플릿 빨강/초록 그리드 축선 끔, 프리셀렉트 빨강. 새 `viewport.md` (렌더 픽셀 10 요소).
  theme ΔE00 38/38 < 2, viewport 9/10 < 5, 헤드리스 349/349, GUI 281/281, dogfood 47/47.
- Step 42 (켜자마자 Maya) 완료 — `docs/steps/step_42.md`. 템플릿 `userpref.blend` 는 실측 후 기각 (템플릿 안에서 사용자 add-on 목록·테마·
  ui_scale 을 통째로 바꿈). 대신 첫 GUI 시작의 환영 대화상자 → 「Make Blender Maya」 1 번 = 레이아웃 설치·Maya 테마·스플래시 끔·
  다음부터 Maya 레이아웃으로 시작, 「Revert Maya Look」 으로 모두 되돌림 (`first_start.py`, 결정 3 개정 = user_decisions 9). 테마는 옵션 +
  끄면 복원. 버그 수정: 오퍼레이터 안 템플릿 전환이 Blender 를 죽이던 것 (layout_open 포함). kit 시작 화면 그림 `tools/make_splash.py`.
  뷰 배경 단색 #5c5c5c. 헤드리스 348/348, GUI 281/281, dogfood 47/47, look_compare 체크 9/9 (메뉴바·패널·뷰 배경 ΔE 0.0).
  **주의: 실험 중 사용자 실제 userpref.blend 를 덮어쓴 사고 — 3 값은 되돌렸고 node_wrangler 는 켜진 채 (step_42.md 「실측」).**
- Step 41 (비교 기준 정확화) 완료 — `docs/steps/step_41.md`. `tools/look_shots.py` 가 Maya 와 같은 카메라 (Maya f_px 973 px, pCube1 화면
  높이를 Maya 샷에 맞춘 거리)·같은 선택 상태·메뉴바에서 연 Create 메뉴로 찍고, `tools/look_compare.py` 가 `pixels.md` (렌더 픽셀 ΔE,
  kit 지점 = `tools/look_data.py` 앵커 표), `rects.md` (영역 ±10 px), `scene.md` (큐브 크기 ±10 %), `crop_*.png` 6장을 만든다.
  결과: 큐브 3/3 (−1.3 %), 픽셀 29 중 ΔE>5 9 + kit 에 없음 9, 사각형 12 중 1. 헤드리스 344/344.
- Step 40 (Maya 동일화 조사·계획) 완료 — `docs/steps/step_40.md`, `docs/PLAN.md` 「Maya 동일화 계획」. Maya 2022.4 를 팩토리 prefs 로 띄워
  스크린샷 22장 + 실측 색·크기 (`research/maya/colors.json`), kit 비교 도구 `tools/look_compare.py` (+ `look_shots.py`: 나란히 이미지,
  테마 ΔE00), 경쟁 제품 22개 (`research/competitors.md`), blindspot 18건, self-review 반영. 버그 수정: 리드(연두)/다른 선택(흰색)
  색이 반대였음 → ΔE 28.5 → 0. 테마 ΔE00>5 13/31 → 11/31. 헤드리스 339/339. backlog 12개 (`autodrive_bmk/backlog.json`).
- Step 39 (컴포넌트 픽워크 + Alt+Shift 축 고정) 완료 — `docs/steps/step_39.md`. 편집 모드 화살표 = `maya_kit.pick_walk_component`
  (엣지 루프/링, 정점·면은 화면 방향), Alt+Shift+LMB/MMB = `maya_kit.view_axis_lock` (처음 우세한 축으로 텀블/트랙).
  헤드리스 339/339, GUI 281/281, dogfood 47/47. **재점검 3차 backlog 7개 모두 처리 (step 33–39).**
- Step 38 (Channel Box 다중 선택·상대값, AE 재질 라벨) 완료 — `docs/steps/step_38.md`. CB 값 필드 = 텍스트 (Maya 숫자 표시,
  `+=5`/`*=2`, 모든 선택·고른 채널 모두), 사용자 속성/SHAPES/INPUTS 도 같은 이름 채널에 적용 (`Scene.maya_kit_cb.rows`),
  재질 `maya_kit_type` → AE `lambert: lambert1` + lambert/blinn/phong/surfaceShader 섹션. 헤드리스 333/333, GUI 277/277, dogfood 47/47.
  재점검 3차 backlog 7개 중 1–6 처리.
- Step 37 (뷰 패널 메뉴 바) 완료 — `docs/steps/step_37.md`. 3D 뷰 헤더 메뉴 = Maya View/Shading/Lighting/Show/Renderer/Panels
  (`ui/panel_menus.py`, `VIEW3D_MT_editor_menus.draw_collapsible` 덮어쓰기, Blender 메뉴는 「Blender ▸」, 환경설정 Panel Menus).
  매핑 67 / 회색 51. 헤드리스 322/322, GUI 272/272, dogfood 47/47. 재점검 3차 backlog 7개 중 1–5 처리.
- Step 36 (대칭 Symmetry) 완료 — `docs/steps/step_36.md`. 전역 Maya 대칭 상태 `Scene.maya_kit_symmetry` → 메시 `use_mirror_*`
  (`operators/symmetry.py`, 편집 모드 진입 시 적용 + 헤더 미러 버튼 역반영), Status Line 대칭 그룹 (토글 + ▾ Off/Object/World/Topology),
  Tool Settings 「Symmetry Settings」, W/E/R 홀드 N Symmetry ▸. 헤드리스 312/312, GUI 267/267, dogfood 47/47.
  재점검 3차 backlog (`C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_33.json`) 7개 중 1–4 처리.
- Step 35 (Maya 키 묶음) 완료 — `docs/steps/step_35.md`. Ctrl+Alt+LMB 박스 줌, Ctrl+T, Y (마지막 비 QWERT 툴), Ctrl+Shift+X/Q,
  F2–F6 메뉴 세트 (IC 3D 뷰 F2–F5 제거), 3D 뷰 Return 팝오버 제거. 키맵 대응표 구현 95 / 계획 0. 헤드리스 300/300, GUI 261/261, dogfood 47/47.
- Step 34 (메뉴 막다른 길) 완료 — `docs/steps/step_34.md`. `menu_map.CHILDREN` (Maya 가 실행 중에 만드는 하위 메뉴: Windows > ... Editors,
  HUD), 편집기는 새 창 (`maya_kit.open_editor`), Edit > Ungroup, UV Editor/Planar/Normal-Based, HUD Poly Count, Increment and Save
  (Maya 번호 규칙), Export Selection (선택만). 헤드리스 294/294, GUI 251/251, dogfood 47/47.
- Step 33 (메뉴가 화면 안에) 완료 — `docs/steps/step_33.md`. `engine.fit_ring`: 마킹 메뉴 중심(누른 점)은 그대로, 방사 상자는 안으로,
  목록은 링 아래/위/옆으로; 핫박스 행이 위로 넘치면 가운데 상자 아래로. 헤드리스 287/287, GUI 246/246, dogfood 47/47.
- Step 32 (재점검 3차) 완료 — `docs/steps/step_32.md`, `docs/PLAN.md` 「재점검 3차」. 코드(`src/`) 변경 없음. 헤드리스 281/281, dogfood 47/47,
  탐색 세션 15 중 13 (실패: 세션 bmesh 선택 탓 1, 박스 줌 미구현 1). 대응표 33행: 완료 25, 부분 6, 불가 2. 새 발견: RMB 루트 목록이 뷰 아래로 잘림,
  AE 재질 라벨이 모두 standardSurface, 메뉴 막다른 길 (Windows 편집기, UV, Ungroup, HUD, Increment and Save), 대칭 없음.
- Step 31 (레이아웃 다듬기) 완료 — `docs/steps/step_31.md`. MayaKit 템플릿 왼쪽 Outliner 폭 0.2 + 컬렉션 행·렌더 열 숨김 (Maya DAG),
  쿼드 → 단일 때 축 뷰 이름 유지 (`is_orthographic_side_view`), 홀드 메뉴 체크 켜짐 색 강조 + 파이 폴백 체크 아이콘, release 스크린샷 재생성.
  타임라인 프레임 상자 겹침은 C 그리기라 미해결. 헤드리스 281/281, GUI 239/239, dogfood 47/47. backlog.json 8 항목 모두 처리.
- Step 30 (선택 감각) 완료 — `docs/steps/step_30.md`. 편집 모드 박스/라쏘 = 가려진 요소까지 (드래그 동안만 X-Ray 플래그, `operators/marquee.py`),
  정점 모드 + 셀렉트 툴 프리셀렉트 하이라이트 (`operators/preselect.py`, C 기즈모 `GIZMO_GT_mesh_preselect_elem_3d`), 언두 256 단계
  (`prefs_preset.GROUPS["undo"]`, disable 시 복원, `tests/kit.py` 가 prefs.edit 스냅샷). 헤드리스 279/279, GUI 232/232, dogfood 47/47.
- Step 29 (Maya 식 재질 지정) 완료 — `docs/steps/step_29.md`. `operators/material.py`: Lighting/Shading Material Attributes /
  Assign New (검색 팝업, Shift+T) / Favorite ▸ / Existing ▸, RMB 목록 끝 같은 항목 (선택 없으면 커서 아래 오브젝트), 면 선택 모드 = 면에만,
  아니면 오브젝트 전체 (슬롯 1개). 엔진: 목록 하위 메뉴 영역 안으로, 클릭 모드 항목은 버튼을 뗄 때 실행. 헤드리스 274/274, GUI 218/218,
  dogfood 47/47.
- Step 28 (MMB = 마지막 핸들) 완료 — `docs/steps/step_28.md`. 기즈모 LMB 누름 감시 → 등록된 transform 의 제약을 툴별로 기억,
  Tool 키맵 MMB = `maya_kit.manip_mmb` (CB 슬라이더 우선), 같은 툴 키 재탭 = 리셋. 헤드리스 264/264, GUI 206/206, dogfood 47/47.
- Step 27 (매니퓰레이터 크기·뷰 키) 완료 — `docs/steps/step_27.md`. = / Shift+= / - gizmo_size (`prefs_preset.set_runtime`, disable 시 복원),
  PgUp/PgDn 스무스 단계, 0, Home (Maya persp), Alt+5 와이어프레임. 키맵 대응표 구현 87 / 계획 5 (F2–F6). 헤드리스 260/260, GUI 202/202,
  dogfood **47/47**.
- Step 26 (Smart Extrude) 완료 — `docs/steps/step_26.md`. 면/엣지 Shift+기즈모 드래그 = 압출 후 변환, 안 움직이면 (Shift+클릭·취소)
  사본/압출을 되돌림, xform 기즈모만 (`context.gizmo_group`), 홀드 메뉴 체크 상자. 헤드리스 256/256, GUI 195/195, dogfood 46/47.
- Step 25 (cm 그리드와 그리드 스냅) 완료 — `docs/steps/step_25.md`. 원인: Blender 원근 뷰는 1 m 아래 그리드 단계를 건너뜀 →
  `overlay.grid_scale` = 표시 단위의 미터 값 (`units.grid_scale`, 템플릿 0.01, Maya Units 적용/복원). X 스냅 템플릿 9 cm / Maya Units 9 cm /
  팩토리 3 m. 헤드리스 249/249, GUI 187/187, dogfood 46/47.
- Step 24 (컴포넌트 Delete) 완료 — `docs/steps/step_24.md`. 편집 모드 Delete / Backspace = `maya_kit.delete_components` (면 삭제,
  경계 아닌 엣지 dissolve + 정점 정리, 정점 dissolve, 메뉴 없음). Ctrl+Delete = IC dissolve. 헤드리스 246/246, GUI 179/179, dogfood 46/47.
- Step 23 (재점검 2차) 완료 — `docs/steps/step_23.md`, `docs/PLAN.md` 「재점검 2차」. 코드(`src/`) 변경 없음; `tools/dogfood.py --session`.
  헤드리스 239/239, GUI 172/172, dogfood 46/47, 탐색 세션 13 중 12 (면 Delete 가 메뉴), 콘솔 오류 0.
  대응표 33행: 완료 23, 부분 8, 미착수 0, 불가 2 (1차 21/8/2/2). 키맵 468행: 구현 79 + IC 6, 계획 13, 미검토 292.
  새 발견: 컴포넌트 Delete, cm 템플릿 그리드 안 보임 + X 스냅 0 cm, Outliner 이름 잘림; blindspot 8건 (MMB 마지막 핸들, 재질 지정 등).
- Step 22 (매니퓰레이터 Shift+드래그 = Smart Duplicate) 완료 — `docs/steps/step_22.md`. Maya 키컨피그의 기즈모 키맵
  (`Generic Gizmo Maybe Drag` / `Drag`) 맨 앞 Shift+LMB PRESS → `maya_kit.manip_duplicate` (복제 후 PASS_THROUGH → 기즈모가 사본 변환).
  Shift 정밀은 그대로 (실측: 누른 채 시작한 드래그는 정밀 아님). W/E/R 홀드 메뉴 Smart Duplicate = 환경설정 토글.
  헤드리스 239/239, GUI 172/172, dogfood 47 중 46 (남은 실패: `=`).
- Step 21 (생성 경로 단위 통일) 완료 — `docs/steps/step_21.md`, 결정 8 (`docs/user_decisions.md`). Maya 길이 1 = 씬 표시 단위 1
  (`operators/units.maya_unit()`): Create/셸프/메뉴/마킹 메뉴/핫박스/Ctrl+G/`cmds` 가 같은 크기, Maya FBX 임포트 크기와도 같음.
  MayaKit 템플릿 pCube1 = 0.01 BU = "1 cm", 템플릿 3D 뷰 = Maya persp (28, 21, 28 cm) + 클립 0.1 / 10000 cm; Maya Units 켬 = 1 BU = "1 cm".
  헤드리스 235/235, GUI 162/162, dogfood 47 중 46 (남은 실패: `=`).
- Step 20 (타임라인) 완료 — `docs/steps/step_20.md`. `.` `,` = 다음/이전 키, Alt+`.` Alt+`,` = 프레임 (Frames 키맵, 3D View 피벗/방향 파이 제거),
  타임라인 헤더 = Maya Time Slider 버튼 + Range Slider 4 필드, 타임라인 뷰가 재생 범위를 따라감, MayaKit 템플릿 애니메이션 1–200 / 재생 1–120.
  헤드리스 227/227, GUI 156/156, dogfood 47 중 46 (남은 실패: `=`).
- Step 19 (복제 이름) 완료 — `docs/steps/step_19.md`. Ctrl+D = `maya_kit.duplicate` (제자리, 하위 계층, pCube2 / pCubeShape2, group1 → group2,
  Shift+D 스마트 반복과 연결); 메뉴 Edit > Duplicate 도 같음. 헤드리스 223/223, GUI 147/147, dogfood 45 중 43 (남은 실패: `.`, `=`).
- Step 18 (편집 모드 키) 완료 — `docs/steps/step_18.md`. Mesh: D = 컴포넌트 피벗 홀드(3D 커서, 놓으면 유지 / 탭 = 리셋),
  Ctrl+Shift+A 전체 선택, Alt+D 해제 + 오브젝트 모드, Ctrl+E 즉시 압출, Ctrl+B 즉시 베벨(정점 모드 = 정점), Shift+> / < 확장·축소,
  Ctrl+F9–F11 닿는 요소로 변환 (`maya_kit.convert_selection`). 헤드리스 218/218, GUI 147/147, dogfood 45 중 42 (남은 실패: Ctrl+D 이름, `.`, `=`).
- Step 17 (Maya 프레이밍 여백 + 핫박스 잘림) 완료 — `docs/steps/step_17.md`. F/A/Shift+F/Shift+A/Ctrl+Shift+F 가 보이는 영역(사이드바·툴바·
  투명 헤더 제외)의 0.95 에 경계 상자를 맞춤 (`operators/framing.py`, `maya_kit.frame`); 핫박스 행은 보이는 영역 안으로 밀고 긴 행은 줄바꿈.
  헤드리스 211/211, GUI 133/133, dogfood 45 중 41 (남은 실패: Ctrl+D 이름, `.`, `=`, Shift+>).
- Step 16 (언두·가시성·아이솔레이트 키) 완료 — `docs/steps/step_16.md`. z/Shift+Z/Ctrl+Y (Screen, border 4개 제거), h·Ctrl+H·Alt+H·
  Shift+H·Ctrl+Shift+H (`maya_kit.visibility`, 오브젝트 모드; Mesh 는 hide/reveal), Ctrl+1 아이솔레이트(카메라 고정), Ctrl+Shift+I 반전.
  헤드리스 203/203, GUI 127/127, dogfood 45 중 41 (남은 실패: Ctrl+D 이름, `.`, `=`, Shift+>). 키맵 대응표 구현 51→63.
- Step 15 (스무스 프리뷰 = 표시 전용) 완료 — `docs/steps/step_15.md`. 3 이 Set Shade Smooth 노드 모디파이어 + 프리뷰 Subsurf(마지막)로
  매끈하게 보이고 메시 데이터는 그대로; Delete History 는 프리뷰를 굽지 않음; 1/2/3 은 사용자 Subsurf 를 건드리지 않음; INPUTS/AE 탭에서 숨김.
  헤드리스 196/196, GUI 115/115, dogfood 45 중 37 통과 (실패 8 = backlog 2·5 의 키·이름).
- Step 14 (재점검 1차) 완료 — `docs/steps/step_14.md`, `docs/PLAN.md` 「재점검 1차」. 코드(`src/`) 변경 없음.
  헤드리스 188/188, GUI 115/115. 새 도구 `tools/dogfood.py` (깨끗한 설치 + Maya 사용자 첫 세션 이벤트 재생):
  체크 43개 중 35 통과, 실패 8 = 아직 없는 Maya 키(z, Shift+Z, h, Ctrl+1, `.`, `=`, Shift+>) + Ctrl+D 이름 `pCube1.001`; 콘솔 오류 0.
- 구현률 (research 대응표 33행): 완료 21, 부분 8, 미착수 2, 불가 2. 키맵 468행: 구현 51 + IC 8, 계획 26, 미검토 306.
- 발견: PLAN 8행(M1-d 나머지 키 25개)이 번호 변경 때 빠져 미구현; blindspot 14건 (Delete History 가 스무스 프리뷰를 구움,
  생성 경로 단위 100배 차이, 편집 모드 D/Ctrl+Shift+A 충돌, Shift+매니퓰레이터 복제 미계획 등).
- Step 13 (통합·배포) 완료 — release 0.1.0 (`c0f37b0`).

## 바로 다음 할 일

- 드라이버 큐 순서: backlog.json 의 Maya 워크플로우 55–67 (PLAN 「Maya 워크플로우 계획」 표: 54 기반 (단위·안내),
  55 포즈 본 CB, 56 Time Slider·키, 57 Joint Tool, 58 IK·스킨, 59 SDK·제약, 60 MTK, 61 Target Weld, 62 Extrude/In-View, 63 UV, 64 Hypershade,
  65 FX, 66 씬 관리, 67 Graph Editor). 각 단계 근거 = `research/maya/workflows/<분야>.md` (research/ 는 추적 안 함 — 지우지 말 것).
- Maya 를 다시 띄울 때: `research/scripts/maya_workflows/launch.ps1` (스크린샷은 Maya 위젯만; 화면 영역 캡처 금지 — step 48 사고).
- 검증은 `python tools/look_compare.py` (`delta_e.md`, `pixels.md`, `viewport.md`, `rects.md`, `density.md`, `grid.md`, `furniture.md`); 샷은 Maya 밀도 (실효 배율 1.0)
  로 찍힌다. GUI 테스트는 두 배율로: `python tests/gui/run.py` 와 `--ui-scale 0.8` (새 고정 픽셀 좌표는 `sim.px()`).
- Blender 를 손으로 띄울 때는 `BLENDER_USER_*` 폴더를 먼저 만들 것 (CLAUDE.md, step 42 사고).
- 외형 검증: `python tools/look_compare.py` (Maya 자료 다시 찍기: `research/scripts/maya_shots/launch.ps1` → `mayapy research/scripts/maya_colors.py`).
- 이전 남은 항목: step_36–39 「남은 것」, PLAN 「재점검 3차」 8–9, step_49 「남은 것」 (Item 탭, AE 460), step_51 「남은 것」 (다른 배율의 셸프 줄 높이, Status Line 아이콘은 Blender 것), step_50 「남은 것」 (Outliner 카메라 행, 목록 바탕색).
