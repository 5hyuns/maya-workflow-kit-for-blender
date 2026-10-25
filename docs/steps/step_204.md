# Step 204 — Animation layers 4 (backlog #3, Issue #111)

## 계획

근거: `docs/steps/step_201_remaining.md` §3 애니메이션 / §8 #3, `research/maya/re/anim_layers_180.md` · `anim_layers_193.md`.
대상: Maya Anim 탭 Layers 메뉴의 Extract Selected (Extract Selected Objects / Attributes), Copy Layer, Delete Empty Layers, Zero Weight /
Full Weight key (레이어 weight 를 현재 시각에 0 / 1 로 키), Layer Editor Anim 탭 Ctrl / Shift 여러 레이어 선택 → Graph Editor 가 선택
레이어들의 커브를 보임. 검증: mayapy 1e-5, GUI 두 레이어 선택 = Graph Editor 커브 둘, 되돌리기 한 단계.

설계 한계 (측정 전 판단, delegated): Blender Graph Editor 는 오브젝트당 **활성 action 하나**의 커브만 그리고 고친다 (step 194: 보이는
레이어 = 활성 action, influence 0). 여러 레이어 선택은 (a) 마지막으로 고른 레이어 = 활성 action (편집 가능), (b) 나머지 선택 레이어의
커브 = 킷이 Graph Editor WINDOW 에 POST_VIEW 로 그림 (Maya 는 둘 다 편집 가능하지만 Blender 는 한 action 만: 그려진 커브는 읽기 전용,
그 행 / 커브를 고르면 그 레이어가 활성), kit outliner 는 선택 레이어마다 행. 다른 방법 (임시 action 합치기, NLA tweak 여럿) 은 Blender
4.5 에 없음 (tweak 은 strip 하나).

레인 (레인 ≤ 4, Blender ≤ 2 = `blender_slots`, Maya ≤ 1):
- **M** (에이전트, Maya 만): mayapy `animLayer` 로 Extract / Copy / Delete Empty / Zero·Full Weight 결과, GUI Maya 로 여러 레이어
  선택 시 Graph Editor / Channel Box / 키 동작 → `research/maya/re/anim_layers_201.md` + `tests/maya204_layers_data.py`.
- **I** (에이전트, Blender 헤드리스): `operators/anim_layers_204.py` (명령), `ui/layer_editor.py` (메뉴 · 여러 선택), Graph Editor 그림
  (`ui/graph_layers.py`) — [K] 로 먼저, 가정 목록.
- 그다음 메인 = M 명세에 맞춤, GUI 확인.
