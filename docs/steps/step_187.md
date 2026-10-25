# Step 187 — Character Sets on Keying Sets (backlog_183.json #5, audit 13 #5)

## 계획

문제 (`docs/steps/step_182_quant.md` §1b): Key 54 %, Control 7 % — Character Set 항목 대부분이 회색, Time Slider 의
`No Character Set` 칸은 비활성 라벨. 목표: Maya Character Set 을 Blender (absolute) Keying Set 위에, S 가 현재 캐릭터를 키,
Key ≥ 70 %.

레인 (순서 이유: 측정이 규칙을 정함): (1) mayapy 측정 → (2) GUI Maya 측정 (current character 는 UI 의 highlightList 에만 있어
mayapy 에서 못 잼) 과 그 사이 kit 구현을 겹쳐 진행 → (3) 테스트 · 메뉴 수 · GUI 샷.

## 측정 (`research/maya/re/character_sets_183.md`)

- mayapy (`research/scripts/character_sets_187_mayapy.py`): Create (factory) = `character -name "character1" -excludeVisibility
  -excludeScale` (scale / visibility 빼고 keyable 전부, custom 포함), 아무것도 선택 안 함 = 빈 character1, 이름 character2 …;
  Merge = 마지막 선택으로.
- GUI Maya (`research/scripts/maya_char187/`, 두 번): 만든 set 이 current (Time Slider `characterField`); current 가 있으면 S 는
  선택과 상관없이 그 캐릭터 멤버만 키 (다른 오브젝트 선택 / 아무것도 없음 둘 다), Shift+W/E 는 선택을 키; current 없음 = 선택의 모든
  keyable (scale / visibility 포함); Subcharacter = 선택으로 subCharacter1, current 의 멤버, current 그대로; Add / Remove =
  Channel Box 에서 고른 plug (없으면 "No attributes are selected in the Channel Box."), 대상 = 선택한 character node 또는 current
  ("Must have a current character or select a character."). Maya 메시지 문구는 mayapy `uiRes` 로 읽음.

## 한 일

- `src/allset/operators/character_sets.py`: 장면의 모든 Keying Set = kit character set (이름 `bl_label`, current =
  `keying_sets.active`), 멤버 = keying set path (Maya 이름 `pCube1.translateX`), subcharacter = 장면 ID prop
  `allset_character_parent` (Blender keying set 은 중첩 없음 — delegated), 「선택한 character node」 = `WindowManager.
  allset_character_nodes` (오브젝트가 선택되지 않은 동안만, Maya 는 한 선택). 연산자: create (+ sub), edit (Add / Remove),
  merge, set_current, select (멤버 / node, Ctrl·Shift = 추가), attributes (현재 캐릭터 멤버 팝업 + 지우기 = Maya AE 대신),
  메뉴 Select Node / Select Members / Set Current (Maya 처럼 열 때 만들어지는 목록, "No Character Sets Defined", "None").
  Keying set 지우기는 `anim.keying_set_remove` (Python 의 `KeyingSets` 에 remove 없음, 측정).
- `operators/time_keys.set_key`: current 가 있으면 `character_sets.key_current` (멤버마다 kit `channel_box.keyframe` —
  Maya 탄젠트 · 애니 레이어 그대로; 전에는 Blender `anim.keyframe_insert`).
- `ui/menu_map.py`: Control 9 항목 + Key 쌍둥이 (`TWINS`); Character Mapper / Redirect 는 notice 그대로. Create 의 옛 notice 제거.
- `ui/time_slider.py`: `No Character Set` 칸 = `ALLSET_MT_character_set_current` 드롭다운 (현재 이름 / "No Character Set").
- 테스트 `tests/test_step187_character_sets.py` (Maya 측정값 7), `tests/gui/gui_step187_character_sets.py`,
  `tests/test_step54_units_notices.py` (Create notice 대신 Windows > Relationship Editors > Character Sets).

## 검증

- 헤드리스 step187 **7 / 7** (Create 멤버 · 이름 · current, S 규칙 3 가지, Shift+W/E, Subcharacter, Add / Remove, Merge,
  오류 문구), 전체 **1703 / 1703**.
- menu_count: Key **54 → 73 %** (30 / 41), Control 7 → 64 %, Rigging 73 %, Animation 67 %; unique 714 → **730**, 회색 notice 없음 0.
- GUI step187 4 / 4 + 샷 `tmp/probe187/gui_step187_dropdown.png` (직접 봄: Time Slider 칸 "character1", 드롭다운 = character1
  ● / None), 관련 GUI step56 · 73 · 180 26 / 26.

## 남은 것

- Character Mapper, Redirect (Key / Control 2 개씩) 은 notice — Blender 에 대응 없음.
- Maya 의 character node 는 Outliner / Channel Box 에 node 로 보이지만 kit 은 메뉴로만 고름 (Outliner 행 없음).
- Create Character Set ❒ 는 일반 redo — Maya 옵션 창 (이름 · 포함 속성) 은 아직 없음.
