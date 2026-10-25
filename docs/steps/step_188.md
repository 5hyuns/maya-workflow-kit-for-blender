# Step 188 — Animation layer follow-ups (backlog_183.json #6, audit 13 lane A #1 + BS2)

## 계획

step 180 의 남은 것 세 가지: kit Auto Key 가 레이어 오브젝트에 키를 안 넣음 (활성 액션 없음), Windows > Relationship Editors >
Animation Layers 가 아직 NLA + 「Blender has no animation layers」, Channel Box > Channels > Add to / Remove From Selected Layers 회색.
먼저 mayapy 로 속성 단위 멤버 규칙과 Auto Key 규칙을 잼 (`research/maya/re/anim_layers_188.md`) → 구현 → 테스트. 측정이 규칙을
정해서 순차.

## 측정

- 레이어 멤버 = 속성 (animLayer -attribute / -removeAttribute); 키 있는 속성을 빼면 레이어 커브가 지워짐.
- 레이어가 선택돼 있어도 멤버가 아닌 속성의 S 키는 BaseAnimation 으로.
- Auto Key 는 그 속성에 **선택 레이어의 키가 이미 있을 때만** 그 레이어에 (값 = 결과가 되게 푼 값, 10 − 2.085 = 7.915); BaseAnimation
  에만 키가 있으면 안 넣음.

## 한 일

- `operators/anim_layers.py`: 속성 멤버 — 오브젝트 ID prop `allset_layer_attrs` {layer: "tx,ry"} (Add / Remove 로 고친 뒤에만;
  없으면 지금처럼 모든 속성 = Add Selected Objects), `is_member` / `member_keys` / `add_attrs` / `remove_attrs` (키 커브 삭제,
  남은 속성 없으면 레이어에서 빠짐), `target_layer(scene, ob, path, index)` (비멤버 = BaseAnimation, `key()` 가 사용),
  `result` (레이어 결과값), `layer_curves`, 연산자 `allset.anim_layer_attrs(add)`.
- `operators/auto_key.py`: 레이어 오브젝트 = `changed_layer_channels` (목표 레이어에 키가 있는 채널 중 값이 결과와 다른 것) →
  `anim_layers.key` (S 와 같은 풀이); depsgraph 핸들러가 액션 없이 NLA 만 있는 오브젝트도 봄.
- Channel Box > Channels 두 항목 = `allset.anim_layer_attrs` (`ui/channel_box.py`, `ui/cb_channels.py` notice 제거).
- Windows > Relationship Editors > Animation Layers = `allset.dock_show(dock=CHANNEL_BOX, le_tab=ANIM)` (Layer Editor Anim
  탭; Display Layer Editor 는 DISPLAY 탭), NLA notice 제거 (`ui/notices.py`, `ui/menu_map.py`, `ui/attribute_editor.py`).
- 테스트 `tests/test_step188_anim_layer_followups.py` (4), `test_step158_cb_menus.py` / `test_step54_units_notices.py` 갱신.

## 검증

- 헤드리스 step188 4 / 4 (Auto Key = Maya 값, 레이어 키 없으면 안 넣음, Add / Remove + 비멤버 키 = Base, 키 있는 속성 제거 =
  커브 삭제 · Base 값, Relationship Editor → Anim 탭), 관련 step180 · 158 · 54 · 101 통과, 전체 **1707 / 1707**.
- GUI `-k step180,step158` 14 / 14.
- menu_count 변화 없음 (Relationship Editor 는 전에도 매핑, Channels 행은 메뉴 수에 안 들어감).

## 남은 것

- 「Selected Layers」 = kit 의 선택 레이어 하나 (Maya 는 여러 레이어 동시 선택).
- Blender 자체 키 (I 키, Blender autokey) 는 여전히 레이어를 모름 (tweak 모드 한계, step 180).
