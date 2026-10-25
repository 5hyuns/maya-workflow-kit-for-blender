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

진행 메모: 1 차 M (측정) + I ([K] 구현) 동시 → WIP 103819a; 2 차 R (I 를 측정에 맞춤 + mayapy 대조 테스트 + 키) + G (GUI 테스트) 동시.

## 한 일

- **측정** (레인 M, mayapy 25 경우 + GUI Maya): `research/maya/re/anim_layers_201.md` / `.json`, 테스트 사본
  `tests/maya204_layers_data.py`. Maya 2022 에는 "Copy Layer" 가 없고 Duplicate Layer / Duplicate Layer (No Animation); Zero / Full
  Weight 는 메뉴가 아니라 툴 줄 버튼 (+ Weight 옆 K).
- **명령** (`operators/anim_layers_204.py`): Extract Selected Objects (`<L>_extract` 를 L 바로 위, 같은 mode · weight 1.0, 선택 오브젝트의
  속성과 커브만 옮김, L 이 비어도 남음; BaseAnimation / Extract Non-Layered = Override `BaseAnimation_extract`), Duplicate Layer /
  (No Animation) (`<L>_copy` 바로 위, 다시 = `<L>_copy1` 첫 사본 아래, weight 1.0, No Animation 의 Override 사본은 현재 시각 값을 고정 —
  NLA strip 에 고정값이 없어 키 하나 CONSTANT 커브, delegated), Empty, Delete Empty Layers (선택 무시, 멤버 속성 없는 레이어만, 키는
  안 셈), Zero / Full Weight and Key (weight 0 / 1 + 현재 시각 키, auto 탄젠트; BaseAnimation 은 weight 1 그대로 키만). 명령마다 되돌리기
  한 단계. BaseAnimation 이 선택에 있으면 Add / Remove Objects · Delete · Empty · Delete Empty · Layer Mode 회색 (`GREY_WITH_BASE`).
  레이어 행 RMB 메뉴 (`ANIM_ROW_MENU`).
- **여러 레이어 선택** (`ui/layer_editor.py`): Ctrl = 토글, Shift = 범위, 목록은 stack 순서. Graph Editor (`ui/graph_layers.py`): 마지막에
  고른 레이어 = 편집 가능한 활성 action (Blender 는 오브젝트당 action 하나), 나머지 선택 레이어 커브는 킷이 흐리게 그림 (읽기 전용) + kit
  outliner 에 레이어 행; 그 행 / 커브 클릭 (`allset.graph_layer_pick`, "Graph Editor" LEFTMOUSE PRESS 맨 앞, PASS_THROUGH) = 그 레이어를 활성.
- `anim_layers.py`: `order_tracks` 가 키 걸린 weight 를 버리던 것 고침 (`strip_state`), 평가가 키 걸린 weight 를 읽음; 레이어 커브를
  `AUTO_RGB` 로 (GUI 에서 Translate Y 가 빨강으로 그려지던 것 — Maya 처럼 X / Y / Z = 빨강 / 초록 / 파랑). Weight 줄 K 버튼을 작은 칸으로
  (반쪽을 차지해 step 180 GUI 테스트가 슬라이더를 못 찾음).

## 검증

- `test_step204_maya` (mayapy 대조): 25 경우 중 **23 일치** (최대 1.55e-6, 1e-5 안), 2 건 건너뜀 = "선택 레이어 없음" 상태가 킷에 없음;
  `delete_empty*` 는 레이어 부모 관계가 킷에 없어 평평한 레이어만 비교. 각 명령 뒤 되돌리기 한 번 = 원래 순서 · 결과.
- `test_step204_layers` 14 / 14, 헤드리스 전체 **1918 / 1918** (233 파일), K 수정 뒤 관련 31 / 31.
- GUI: 새 `gui_step204_layers` (실제 클릭 + Ctrl+클릭으로 두 레이어 선택 → kit outliner 두 레이어 행, Graph Editor 화면에 커브 둘 — 킷이
  그린 흐린 빨강 tx 934 px + Blender ty 2517 px, Zero Weight 뒤 되돌리기 한 번) + 관련 / 스모크 7 파일 68 / 69 → K 버튼 고친 뒤 30 / 30.
  샷 직접 봄 (초록 Translate Y, 흐린 빨강 AnimLayer1 Translate X).

## 남은 것

- Maya 는 선택한 모든 레이어의 커브를 편집 가능 — 킷은 마지막에 고른 하나만 (나머지는 그려진 읽기 전용, Blender 한계).
- Graph Editor View All / Frame 이 그려진 다른 레이어 커브를 포함하지 않음; 편집 가능한 레이어 행이 stack 위치가 아니라 맨 위.
- 레이어 부모 (자식 레이어), Exclusive solo, Select Objects / Branch / Layer Node, Export, Membership, Attribute Editor (RMB 메뉴).
- Channel Box 레이어 멤버 필드의 teal 바탕 (Maya) — 킷은 아이콘만 (step 194 결정, 확인 필요).
