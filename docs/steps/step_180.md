# Step 180 — Animation Layers on NLA

Backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_174.json` 7 번째 (재점검 12차 BS3; research/maya/workflows/animation.md:106
은 측정 없이 "impossible" 이라 적었음).

## 계획

### 측정 (끝남)

- Maya (mayapy, `research/maya/re/anim_layers_180.md` / `.json`, `research/scripts/anim_layers_180_mayapy.py`):
  Additive = 아래 결과 + w · 레이어 커브 (회전 기본 = Euler 성분별 더하기), 스케일 기본 = 곱하기 (아래 × 레이어^w), Override = (1−w) ·
  아래 + w · 레이어, mute = 레이어 빠짐, solo = BaseAnimation + solo 레이어만, `setKeyframe -v` 와 선택된 레이어에 놓는 키는 **결과가 그
  값이 되도록** 레이어 커브 값을 거꾸로 계산 (AnimLayer1 @5 = 20 − base 4.4444 = 15.5556; Base 선택 = 20 − 레이어 0.5556 = 19.4444).
- Blender (`tmp/s180/probe_nla.py`): Maya 의 레이어 커브 그대로 NLA 트랙 — Base = REPLACE 띠, Additive = **COMBINE** (위치 / Euler 더하기,
  스케일 곱하기에 influence 거듭제곱), Override = REPLACE, 스케일 Additive 모드 = ADD, weight = strip influence (animated influence 켜고 키
  지움), mute = track.mute → 6 경우 모두 Maya 값과 최대 4e-6 (float32 회전). 띠 구간 = 넓은 고정 범위 [−1000, 1000] (1:1 시간).
- Blender 키 넣기 (`tmp/s180/probe_tweak.py`): 레이어 띠 tweak 모드 + `keyframe_insert` = Maya 와 같은 15.5556 (Blender NLA 역산).
  하지만 tweak 모드는 **아래 쌓임만** 평가 (Base 를 tweak 하면 위 레이어 무시 → 20, Maya 19.4444) — 위 쌓임 평가는 RNA 에 없고
  NLA 편집기 문맥의 연산자 옵션뿐.

### 설계 (delegated)

- `operators/anim_layers.py`: 레이어 = 씬 수준 목록 `Scene.allset_anim_layers` (PropertyGroup: name, weight, mute, solo, lock, override;
  첫 항목 = BaseAnimation), 선택 = `Scene.allset_anim_layer_index`. 오브젝트마다 같은 이름의 NLA 트랙 + 액션 (`<layer>_<object>`, ID prop
  `allset_anim_layer`), Base 트랙 = 오브젝트가 레이어에 처음 들어갈 때 그 활성 액션을 옮긴 것 (active action = None).
- `sync(scene)`: 목록 → 트랙 (blend: Base REPLACE, Additive COMBINE, Override REPLACE; strip influence = weight; mute = mute or (solo 있음 and
  solo 아님); 트랙 순서 = 목록 순서).
- 키: tweak 모드 안 씀 (위 쌓임 평가가 없어서). `channel_box.keyframe` (S, Shift+W/E/R, Channel Box) 이 레이어가 있는 오브젝트면
  `anim_layers.key()` — 측정한 합성 규칙으로 선택 레이어 아래 결과와 위 레이어의 아핀 변환을 계산해 화면 값이 되도록 그 레이어 커브에
  키. 레이어에 없는 오브젝트는 Base 에. Lock 된 레이어는 키 거부 (Maya UI 처럼; mayapy `-animLayer` 명시 키는 lock 이어도 들어감 [O]).
- UI: Layer Editor Anim 탭 = Maya 처럼 레이어 목록 (위가 맨 위 레이어, 아래 BaseAnimation), 행 = 이름 (클릭 = 선택) + M / S / L, 툴바
  Create Empty Layer / Create Layer from Selected, 선택 레이어 Weight + Additive / Override.

### 레인

- 메인: 핵심 모듈 + 헤드리스 테스트 (Maya 값과 비교).
- 서브에이전트 1: GUI Maya 로 Layer Editor Anim 탭 캡처 (레이어 2 개, 하나 선택, 하나 mute) — Maya 만 씀.
- 서브에이전트 2: Anim 탭 UI (`ui/layer_editor.py`) + GUI 테스트 — 핵심 모듈 API 가 정해진 뒤 (그래서 핵심 먼저, 순차).

## 한 것

- `operators/anim_layers.py` (메인): 레이어 목록 · NLA 트랙 · `sync` · `key()` (`solve`: 선택 레이어 아래 결과를 접고 위 레이어를 아핀
  변환으로 보고 거꾸로 풂), 연산자 Create (빈 / 선택에서), Add / Remove Selected Objects, Delete, Select. 빈 액션은 할당해도 슬롯이 안
  생겨서 `slots.new` 로 직접 만듦 (그러지 않으면 띠의 `action_slot` 이 None 이라 레이어가 평가되지 않음 — 첫 테스트 실패 원인).
- `ui/channel_box.keyframe`: 레이어가 있는 오브젝트는 `anim_layers.key` (S, Shift+W/E/R, Channel Box 키).
- `ui/layer_editor.py` (서브에이전트 + 메인 손질): Anim 탭 = 툴바 (Create Empty / from Selected, kit 아이콘), 행 = Lock / Solo / Mute
  (왼쪽, Maya 순서; BaseAnimation 은 Lock 만) + 이름 (선택 = 눌린 버튼, mute = 흐림), 아래 Weight 슬라이더 (Base 선택 때 흐림); Layers 메뉴
  = Create Empty Layer / Create Layer from Selected / Add · Remove Selected Objects / Delete Layer / Override · Additive.
- `ui/time_slider.py`: Range Slider 줄의 "No Anim Layer" 칸 = 선택 레이어 이름 (Maya 처럼).
- Maya GUI 캡처 (서브에이전트): `research/maya/screens/anim180/` (4 상태 × 6 PNG + 위젯 / 픽셀 JSON, `research/scripts/maya_anim180/`).

## 검증

- 헤드리스 `test_step180_anim_layers` 5 / 5: Maya 와 같은 순서로 키 → 레이어 커브 값 = mayapy (1e-5), translateX / rotateX / rotateY /
  rotateZ / scaleX 결과 (프레임 1·3·5·7·10) = mayapy (1e-5; 요구 1e-6 은 Blender float32 라디안 때문에 불가 — 프로브 최대 4e-6), weight 0.5 /
  mute / solo / override / override weight 0.5, 선택 레이어 키 (15.5556) 와 Base 선택 키 (19.4444), lock 거부, 목록 · 삭제.
- 헤드리스 전체 `ALLSET_SANDBOX=s180full python tests/run.py`: **1658 / 1658**.
- GUI `gui_step180_anim_layers` 9 / 9 (행 순서, 행 클릭 선택, Mute 토글, Weight = strip influence 0.4, mute 트랙, COMBINE), `gui_step135_dock` +
  `gui_step73_time_slider` 21 / 21. 샷 직접 봄 (Maya 캡처와 나란히 `tmp/s180/side2.png`): 행 순서 · 버튼 자리 (Lock / Solo / Mute 왼쪽, Base 는
  Lock 만) · 선택 행 파랑 · mute 흐림 · Weight 줄 = Maya.
- GUI 전체 묶음은 돌리지 않음 (CLAUDE.md step 141 규칙).

## 남은 것

- Blender tweak 모드는 아래 쌓임만 평가 → Blender 자체 키 (I 키, Blender autokey) 는 레이어를 모름; kit 키 경로 (S / Shift+W/E/R / CB) 만
  Maya 식. kit auto key (`operators/auto_key.py`) 는 레이어 오브젝트의 활성 액션이 없어 키를 안 넣음 — 다음에 `anim_layers.key` 로.
- 회전 누적 By Layer (쿼터니언), Ghost 버튼, Zero Key / Zero Weight 툴바, 레이어 순서 위 / 아래, Merge Layers, 오른쪽 점 (영향 받는 레이어),
  Weight 의 K (키 가능한 weight) 는 안 함. 행 이름은 가운데 정렬 (Blender 연산자 버튼은 정렬 옵션이 없음; Maya 는 왼쪽).
- 띠 범위 = [−1000, 1000] 프레임 고정 (밖의 키는 평가 안 됨).
