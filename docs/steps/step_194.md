# Step 194 — Animation layers: keys stay visible (backlog.json #2, audit 14 NB1)

## 계획

문제 (재점검 14차 NB1): `anim_layers.ensure_base` 가 `ad.action = None` 으로 두어, 레이어에 넣은 오브젝트는 Channel Box 키 색 ·
Time Slider 눈금 · Graph Editor / Dope Sheet 커브가 모두 사라졌다 (모든 읽기가 활성 액션만 봄).

레인 (포그라운드 에이전트 2 개 동시, delegated):
- **M — Maya 측정** (GUI Maya 2022 + mayapy): `research/maya/re/anim_layers_193.md` (스크립트 `research/scripts/maya_anim193/`, 화면
  `research/maya/screens/anim193/`, mayapy `anim_layers_193_mayapy.json`).
- **P — Blender 탐침** (`tmp/p194/`): 「표시 액션」 (레이어 오브젝트의 활성 액션 = 그 레이어 strip 의 액션, action influence 0) 이
  평가를 안 바꾸는지, 대안 tweak mode.
- 메인: 두 결과를 보고 설계 → 구현 → 테스트 (순서 필요: 설계가 측정 결과에 달림).

측정 결과 (요약):
- Maya [O]: Channel Box — 레이어 멤버 채널은 **어느 상태든 teal #4db6ac** (키가 있어도 빨강 아님), 레이어 밖 채널은 Base 상태 (분홍 /
  빨강). Time Slider — 선택 레이어의 키 (Base 선택 1 · 12 · 24, AnimLayer1 선택 1 · 6 · 18 · 24 = 레이어 tx + 레이어 밖 ry 의 Base 키,
  mute 해도 보임). Graph Editor — 선택 레이어의 커브만, 레이어 자기 값 (결과 아님). Zero Key Layer = `setKeyframe -id -itt flat`
  (멤버 채널에 항등 키, 기존 키는 값만 덮음, Base 에선 경고). Merge Layers (Base + 레이어, 공장 옵션) = 멤버 채널을 매 프레임 구워 Base
  로, 레이어 지움, 결과 그대로.
- Blender [O] (`tmp/p194/headless_out.txt`, `gui_out.txt`): 표시 액션 + influence 0 → 모든 경우 (Base / Additive w 1 · 0.5 / Override /
  mute / 표시 = Base · 레이어) 평가 차이 **정확히 0**, 저장 · 불러오기 · undo 도 0; Graph Editor / Dope Sheet 에 그 레이어 커브; 키
  편집은 strip 으로 바로 반영. Blender 자기 I 키는 "Due to the NLA stack setup ..." 로 키를 안 넣음 (kit S 키는 `anim_layers.key`).
  tweak mode 는 위 스택 평가에도 HOLD_FORWARD 를 무시해 범위 밖이 0.1 달라지고 NLA 편집을 막아 버림.

결정 (delegated):
- **표시 액션**: 레이어가 있는 오브젝트의 `ad.action` = 표시 레이어 (선택 레이어에 들어 있으면 그것, 아니면 Base) 의 strip 액션,
  `action_influence = 0` (`anim_layers.show`, `sync` 끝 · 선택 레이어 index update · load_post). 그러면 Graph Editor / Dope Sheet /
  `compat.id_fcurves` / kit 키 읽기가 모두 그 레이어를 본다 (Maya 의 선택 레이어 표시). kit 은 레이어 선택이 하나라 Maya 의 「둘 다
  선택」 은 없음.
- Time Slider: 표시 레이어 키 + 그 레이어에 없는 채널의 Base 키 (`hidden_base_curves`).
- Channel Box: 레이어 멤버 = 상태 `LAYERED` — UILayout 은 teal 을 못 그려 빨강 (alert) 없이 NLA 아이콘만 (step 195 의 CB 모양 단계에서
  teal 칠하기 검토). 레이어 밖 채널은 Base 커브로 상태.
- Zero Key Layer / Merge Layers = Layers 메뉴 (Anim 탭). kit Merge = 선택 레이어를 Base 로 (Maya 의 Base + 레이어 선택 경우).
  Visibility 는 kit 레이어 NLA 가 안 다루므로 Zero Key 에서 뺌.

## 한 일

- `src/allset/operators/anim_layers.py`: `display_layer`, `show` (표시 액션 + influence 0), `base_curve`, `member_of_layer`,
  `hidden_base_curves`, `zero_key`, `merge_down`, 연산자 `allset.anim_layer_zero_key` / `allset.anim_layer_merge`; `sync` 끝에 `show`,
  `allset_anim_layer_index` update = `show`, load_post (0.4.x 파일), `remove_object` 는 표시 중인 액션을 먼저 놓음.
- `src/allset/ui/channel_box.py`: `channel_state` 의 `LAYERED` (레이어 멤버), 레이어 밖 채널은 Base 커브; `_ALERT_STATES`.
- `src/allset/ui/time_slider.py`: `key_frames` 에 `hidden_base_curves`.
- `src/allset/ui/layer_editor.py`: Anim 탭 Layers 메뉴에 Merge Layers · Zero Key Layer.
- 테스트: 새 `tests/test_step194_layer_display.py` (6 개: 평가 그대로, 읽기가 선택 레이어를 따름 (눈금 Maya 표 그대로), CB 상태,
  Zero Key, Merge, 레이어 지우기), `test_step180_anim_layers` 의 `ad.action is None` 기대를 새 규칙으로.

## 검증

- 레이어 테스트 (`-k step194,step180`): 11 / 11 (처음 step180 의 옛 `ad.action is None` 기대 1 개, 내 테스트의 지운 액션 참조 1 개 고침).
- 헤드리스 전체 4.5: **1736 / 1736** (216 파일).
- GUI `-k step180,step188,step186,step73_,step150`: **33 / 33** (5 파일).
- GUI 샷 (`tmp/s194_session.py`, UI 1.0, `tmp/dogfood/s194_session/shots/`) 직접 봄: AnimLayer1 선택 = Time Slider 눈금 1 · 6 · 18 · 24,
  Graph Editor 에 레이어 tx 커브만 (2 → −1 cm); BaseAnimation 선택 = 눈금 1 · 12 · 24, Graph Editor 에 tx + ry; Channel Box 레이어
  멤버는 빨강 없이 NLA 아이콘, ry (레이어 밖) 는 빨강. 콘솔 오류 0. Maya 측정표와 같음.

## 남은 것

- Channel Box teal (#4db6ac) 바탕은 UILayout 으로 못 그림 → 아이콘만; step 195 (CB 모양, POST_PIXEL) 에서 칠하기.
- kit 레이어 선택은 하나 — Maya 의 여러 레이어 선택 (Graph Editor 에 둘 다, Merge 의 여러 레이어) 은 아직 없음.
- Blender I 키는 레이어 오브젝트에 "NLA stack setup" 경고로 키를 안 넣음 (Maya S = kit 키는 됨).
- Extract / Copy / Delete Empty / Zero Weight / Full Weight 는 아직 (step 192 A #5 나머지).
- 실제 클릭 느낌 → manual_checks 「Step 194」.
