# Step 6 — M2-b Channel Box, Layer Editor

## 계획

근거: `research/maya/channel_box.md` (§1 구성, §2.1 섹션, §2.2 채널 선택, §2.3 MMB 가상 슬라이더, §2.4 Channels 메뉴, §2.6 필드 편집·색, §3.1 Display layers, §4 Blender 대응), `research/blender/api_limits.md` #1/1a/1b/1c.

### 위치

- 3D 뷰 사이드바 카테고리 **"Channel Box"**: 패널 "Channel Box"(위) + "Layer Editor"(아래) — Maya 의 CB 70% / LE 30% 도크 (`channel_box.md:15`). 템플릿(Step 5)의 General 화면 사이드바가 이 탭을 열도록 make_startup 에서 `region.active_panel_category` 설정 시도.

### 다중 선택 일괄 편집 (delegated)

- Maya: 값 입력은 **선택된 모든 객체**에 적용 (`channel_box.md:52-55`). Blender 필드는 그 속성의 소유자 하나만 바꾼다 (Alt 를 눌러야 전체).
- 선택: Translate/Rotate/Scale XYZ·Visibility 행은 **getter/setter 프록시 속성** (`Scene.maya_kit_cb`, PropertyGroup). getter = 리드(활성) 객체 값, setter = 선택된 모든 객체(잠긴 채널 제외)에 같은 값. Scene 에 두는 이유: UI 편집 시 언두 푸시가 되는 ID (WindowManager 는 언두 대상이 아님). 자동 키 켜져 있으면 setter 가 키를 넣는다.
- 단위: Translate = DISTANCE (씬 단위 cm 표시), Rotate = ANGLE (도), 정밀도 3 (Maya 기본, `channel_box.md:30`).
- 키 상태 표시: 프록시라 Blender 의 자동 필드 색이 없다 → 행 오른쪽에 **리드 객체 실제 속성의 데코레이터**(`prop_decorator`: 키 다이아몬드/드라이버, 클릭 = 키 삽입) + 키/애니메이션/드라이버가 있으면 행 `alert`(붉은 틴트 ≈ Maya 키 색), 잠금은 `enabled=False`(회색 ≈ Maya 잠금 색). 정확한 Maya RGB 는 [U].
- 커스텀 속성(Maya 추가 속성), SHAPES(데이터: 카메라 초점거리, 라이트 세기·색), INPUTS(모디파이어 = construction history, `channel_box.md:177-180`)는 리드 객체의 실제 속성을 그린다 (일괄 편집은 Blender 기본 Alt). OUTPUTS 는 Blender 대응 없음.

### 채널 선택과 MMB 가상 슬라이더

- 채널 이름 = 버튼 (`maya_kit.cb_select_channel`; 클릭 = 교체, Ctrl = 토글, Shift = 추가 — Maya Qt 목록 [I]). 선택 상태는 WindowManager 문자열 (언두 대상 아님, Maya 도 채널 선택은 언두 안 됨 [K]).
- `maya_kit.cb_virtual_slider` (모달, `GRAB_CURSOR_X`): 오브젝트 모드에서 채널이 선택돼 있으면 MMB 좌우 드래그로 선택 객체 전부의 선택 채널을 각자 시작값 + Δ 로. 아니면 `PASS_THROUGH` → MMB 툴 이동 그대로.
  - Δ = 픽셀 × 채널 기본 단위(이동 0.01 m = 1 cm, 회전 0.5°, 스케일·커스텀 0.01) × 속도(Slowest 0.01 / Slow 0.1 / **Medium 1** / Fast 10, `channel_box.md:83-88`) × (Ctrl 0.1, Shift 10 [I]); Hyperbolic = Δ·|Δ|/50 [I].
  - ESC/RMB 취소(시작값 복원), MMB 놓기 확정(언두 1단계). 헤더에 값 표시.
- **키맵 우선순위**: IC 는 Move/Rotate/Scale/Transform 툴 키맵에 MMB 를 넣었다(IC:3823). 툴 키맵이 "3D View" 보다 먼저 처리되므로 슬라이더 항목을 그 4개 툴 키맵 **맨 앞**에 넣고 "Object Mode" 에도 넣는다. 같은 키맵 안 같은 이벤트 = 충돌이지만 슬라이더가 조건부 PASS_THROUGH 이므로 의도된 것 → `maya_patches.PASS_THROUGH_FIRST` 로 선언하고 충돌 테스트에서 제외. GUI 테스트로 (a) 채널 선택 시 슬라이더, (b) 미선택 시 툴 MMB 이동 둘 다 확인.

### Channels 메뉴 (패널 메뉴 줄; Blender 버튼 RMB 메뉴는 교체 불가 → delegated)

선택 채널(없으면 메뉴에 따라 전체) 대상: Key Selected / Key All Keyable / Breakdown Selected / Mute·Unmute Selected / Delete Selected(애니 커브 삭제) / Break Connections(커브·드라이버 제거) / Lock·Unlock Selected (`lock_location/rotation/scale`; Visibility 잠금은 미지원) / Hide Selected / Lock and Hide / Show All / Make Selected Nonkeyable·Keyable (객체 커스텀 속성 목록, Key All 이 건너뜀) / Duplicate Values (리드 → 나머지). Settings: 속도, Hyperbolic. Freeze 는 Maya 의미(피벗 유지)가 Step 11 개념 작업이라 제외. Cut/Copy/Paste 는 제외.

### Layer Editor (Display Layers)

- 레이어 = **"Display Layers" 루트 컬렉션(모든 뷰 레이어에서 exclude) 아래 자식 컬렉션**, 객체는 원래 컬렉션에 그대로 두고 레이어에 추가 링크 → 레이어가 계층/가시성 구조를 바꾸지 않는 멤버 목록 (Maya 디스플레이 레이어도 계층과 독립, `concepts.md` §10). 객체당 레이어 하나 (Maya 와 같음, 추가 시 다른 레이어에서 빠짐).
- 상태(`Collection.maya_kit_layer`): V(visible) → 멤버 `hide_viewport`; 타입 Normal / Template(T: 선택 불가 + 와이어) / Reference(R: 선택 불가) → `hide_select`·`display_type` (`channel_box.md:150-152`); P(playback) 끄면 재생 중 숨김 → `animation_playback_pre/post` 핸들러.
- UIList 행: V, P, 타입 순환(공백/T/R), 이름. 버튼: 빈 레이어, 선택으로 새 레이어(이름 `layer1`…), 선택 추가/제거, 멤버 선택, 레이어 삭제(멤버 원상 복구).

### 테스트

- 헤드리스: 프록시 get/set·일괄 적용·잠금 건너뜀·도/cm·자동 키, 채널 선택 규칙, 슬라이더 값 계산·적용·취소, 채널 메뉴 각 동작, 키 상태 판정, INPUTS 속성 필터, Layer Editor 전부(멤버·배타·V/T/R·재생 핸들러·삭제 복구), 키맵(툴 키맵 맨 앞, 충돌 예외 선언), 활성화/비활성화 깨끗함(Scene/Collection/WindowManager 속성·핸들러).
- GUI: MMB 슬라이더 실이벤트(채널 선택/미선택), 패널 스크린샷(키 색·잠금 회색·섹션).

## 한 것

- `src/maya_kit/ui/channel_box.py`: 사이드바 "Channel Box" 패널 — 리드 이름(+선택 수), Translate/Rotate/Scale XYZ·Visibility 프록시 행(`Scene.maya_kit_cb`, 선택 전체 일괄 적용·잠금 건너뜀·자동 키), 커스텀 속성 행, SHAPES(데이터 이름, 카메라·라이트 주요 값), INPUTS(모디파이어 펼치기·뷰포트 토글·스칼라 속성), 빈 상태 "make a selection". 행 상태: 키/애니/드라이버 = 붉은 필드(`alert`) + 상태 아이콘, 잠금 = 회색, 선택 채널 = 눌린 파란 이름.
- 채널 선택 `maya_kit.cb_select_channel` (클릭 / Ctrl 토글 / Shift 추가), `cb_deselect_channels`.
- MMB 가상 슬라이더 `maya_kit.cb_virtual_slider` (모달, GRAB_CURSOR_X, Ctrl x0.1 / Shift x10, 속도 4단계·Hyperbolic = 애드온 환경설정·패널 Settings 메뉴, ESC/RMB 취소, 언두 1단계). 채널 미선택이면 PASS_THROUGH.
- Channels 메뉴: Key Selected, Key All Keyable, Breakdown Selected, Mute/Unmute, Delete Selected, Break Connections, Duplicate Values, Lock/Unlock, Hide, Lock and Hide, Show All, Make Nonkeyable/Keyable, Deselect.
- `src/maya_kit/ui/layer_editor.py`: Layer Editor 패널 (UIList: V, P, 타입 순환 T/R, 색 태그, 이름, 멤버 수; 버튼: 빈 레이어, 선택으로 새 레이어, 추가/제거, 선택, 삭제), 재생 핸들러.
- 키맵 패치 14: Move/Rotate/Scale/Transform 툴 키맵 맨 앞 + Object Mode 에 MMB 슬라이더; `patch.KeyconfigData.add(first=True)`, `maya_patches.PASS_THROUGH_FIRST`.
- `tests/kit.py` 스냅샷에 Collection 속성 추가.

## 검증

```
python tests/run.py        -> 79 passed, 0 failed, 7 file(s)
python tests/gui/run.py    -> 52 passed, 0 failed, 4 file(s)   (step 6: 5)
```

- 헤드리스 `test_step6_channel_box.py` (18): 프록시 getter=리드·setter=선택 전체(위치·회전 도·스케일·가시성), 잠긴 채널 건너뜀, 자동 키, 단위(LENGTH/ROTATION, 정밀도 3), 채널 선택 규칙, 키 상태(KEYED/ANIMATED/DRIVEN), 커스텀 속성 필터, 슬라이더 계산(100 px = 1 m, Ctrl/Shift/속도/hyperbolic)·대상(잠금·가시성 제외)·객체별 상대 적용, Key Selected/All(Nonkeyable 건너뜀), Breakdown 키 타입, Mute/Unmute, Delete, Break(드라이버), Lock/Hide/Show/Keyable, Duplicate Values, INPUTS 속성 필터(내부 `is_`/`open_`/`_panel` 제외), 레이어 생성(루트 exclude, 원래 컬렉션 유지, 가시성 불변)·V/T/R·타입 순환·배타 멤버십·삭제 복구·재생 핸들러·추가/제거/선택/삭제 오퍼레이터, 키맵 순서. `test_enable_disable`: Scene/Collection/WindowManager 속성·재생 핸들러까지 비활성화 후 원상.
- GUI (`gui_step6_channel_box.py`, Move 툴 활성): Translate X 선택 후 MMB 100 px 드래그 -> +1.000 (다른 채널 불변), 드래그 중 ESC -> 원래 값, **채널 미선택 -> MMB 드래그가 Move 툴 이동으로 통과**, 사이드바 Channel Box 탭.
- 스크린샷 직접 확인 (`gui_step6_channel_box.png`): 키 있는 Translate X 빨간 필드, 잠긴 Translate Y 회색, 선택 채널(Translate X, Rotate Z) 파란 이름, `speed` 커스텀 행, SHAPES / INPUTS 섹션, Outliner 에 "Display Layers > layer1".
- 첫 GUI 실행에서 발견해 고친 것: 시뮬레이션 이벤트는 `event.mouse_prev_x` 를 갱신하지 않아 슬라이더 값이 0 → 이전 x 를 직접 추적; INPUTS 에 내부 속성(`is_active`, `open_*_panel`)이 보임 → 필터; 프록시 행의 `prop_decorator` 가 키 상태를 점으로만 표시 → 자체 상태 아이콘.

## 결정 (delegated)

- 일괄 편집 = getter/setter 프록시 (Scene 에 둬서 UI 편집이 언두에 들어감). 대신 Blender 기본 키 색·우클릭 Insert Keyframe 은 프록시 필드에서 안 됨 -> 상태 아이콘·붉은 필드·Channels 메뉴로 대체.
- 우클릭 메뉴는 Blender 버튼 RMB 를 바꿀 수 없어 패널 헤더 "Channels" 메뉴로.
- 디스플레이 레이어 = exclude 된 "Display Layers" 아래 컬렉션 (멤버 목록), 상태는 객체 플래그에 적용.
- 슬라이더는 MMB 툴 키맵 앞에 두고 조건부 통과.

## 남은 것

- **템플릿 사이드바가 Channel Box 탭을 열게 할 수 없음**: `Region.active_panel_category` 는 헤드리스·GUI 모두 읽기 전용 (실측). 사용자가 탭을 한 번 누르면 영역에 기억됨 -> manual_checks.
- 커스텀 속성·SHAPES·INPUTS 는 리드만 편집 (Alt 로 Blender 다중 편집). Visibility 잠금 없음. Maya 필드 상대 수식(`+=5`) 미지원. OUTPUTS 섹션 없음.
- Channels 메뉴 Cut/Copy/Paste, Freeze(-> Step 11), Select Connection, Show 메뉴, 채널 이름 Nice/Long/Short 미구현. 채널 이름 드래그 다중 선택 없음.
- 레이어 색 = 컬렉션 색 태그만 (오브젝트 와이어 색에는 미적용). 애니메이션 레이어 탭 없음.
