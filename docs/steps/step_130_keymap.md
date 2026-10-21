# Step 130 lane K — Maya keymap without touching the active keyconfig (#40, #46)

## 계획

요구 (#40, decision 3): 활성 keyconfig·키맵 환경설정을 바꾸지 않는다, unregister 가 모든 것을 되돌린다, 런타임 exec 없음.
지금까지: IC 데이터 (`bpy.utils.execfile`) + `maya_patches` → keyconfig "Maya-style" 를 만들고 `kcs.active = kc` (이름이
userpref 에 저장되어 제거 후에도 남음), load_post + 영구 타이머가 다시 활성화.

## 측정 (Blender 4.5.4, GUI + `--enable-event-simulate`, 킷 없이: 테스트 연산자 `test.log130` 이 태그를 기록하고 PASS_THROUGH/FINISHED/… 를 돌려줌, scratch 스크립트는 tmp 에서 지워짐)

| # | 질문 | 결과 |
|---|---|---|
| a | 애드온 항목이 활성 keyconfig 의 같은 키맵 항목보다 먼저인가 | 예. `keyconfigs.user` 의 "Object Mode" 머리 = 애드온 항목. **하나씩 head 에 붙어 순서가 뒤집힌다**: 애드온 [a1, a2] → user [a2, a1, 프리셋...], G 누름 로그 `['a2', 'a1']` 후 프리셋 grab 시작 (둘 다 PASS_THROUGH). |
| b | 모달 키맵 애드온 항목 | **불가**: `keyconfigs.addon.keymaps.new(..., modal=True)` → `RuntimeError: Modal key-maps not supported for add-on key-config`. 활성 keyconfig 의 모달 맵에 런타임으로 `new_modal('CANCEL', 'F18')` 하면 user 맵에 반영되고 grab 중 F18 이 취소함. 프리셋 모달 항목 `active=False` (Transform X AXIS_X) → grab+X 가 축 고정 안 함. |
| c | 막는 항목의 반환값 | G (프리셋 grab 이 있는 키): 첫 애드온 항목 FINISHED → 이후 항목·키맵 (3D View, Window, Screen) 전부 실행 안 됨. PASS_THROUGH → 같은 키맵의 다음 항목 (프리셋 grab) 이 실행. **"이 키맵의 나머지만 건너뛰고 다음 키맵으로" 하는 반환값은 없다** (`wm_handler_operator_call`: PASS_THROUGH = 계속, 그 외 = 중단). F19 (아무 키맵에도 없는 키) 에서는 Python 연산자가 FINISHED/CANCELLED 를 돌려줘도 Window/Screen 항목까지 실행됨 — 원인 미확인 (`--debug-handlers` 로그로 확인: F19 PRESS 가 Object Mode 이후 Window/Screen 까지 검사됨), 설계에는 영향 없음. |
| d | `first=True` / PASS_THROUGH 순서 | 역순으로 넣으면 user 키맵 순서 = Maya 데이터 순서 (headless 테스트 `test_step130_keymap_lifecycle`: 3D View LMB CLICK = `allset.select_priority`, `allset.toolbox_guard`, `view3d.select`). |
| e | 프리셋 항목을 메모리에서 끄기 | 프리셋 "Object Mode" G `active=False` → G 가 grab 하지 않고 이벤트가 다음 키맵 (Window 애드온 항목) 으로 감. `keyconfigs.user` 키맵 `is_user_modified=False`. |
| f | 영구성 | 프리셋 항목을 끈 채 `wm.save_userpref` (샌드박스 config) → 재시작: 항목 active, user-modified 키맵 없음. 프리셋 keyconfig 는 시작할 때마다 프리셋 파일에서 다시 만들어지고, 저장되는 것은 사용자 편집 diff 와 이름뿐. |

데이터 크기 (4.5): Blender 기본 활성 항목 중 Maya 데이터와 같은 항목이 아닌 것 1417 개, 그중 1256 개는 이벤트를 Maya 가
**다른 키맵** 에서 쓴다 (예: Object Mode G = grab, Maya 는 Screen G = 반복). 소비하는 blocker 는 그 이벤트를 다음 키맵에
못 넘기므로 (c) 전역 키가 죽는다 → blocker 방식 (decision 3 문구) 대신 (e) 를 택함 (delegated).

## 설계 (delegated)

- `keymap/ic_<major>_<minor>.py` = IC 데이터 정적 파일 (`tools/gen_ic_data.py` 가 각 Blender 에서 `industry_compatible_data.py`
  의 `generate_keymaps(Params())` 를 돌려 리터럴로 씀, 파일에 Blender 빌드 기록; 4.5.4, 5.0.1, 5.1.2, 5.2.2). 이전 minor 와
  같으면 파일을 안 만든다. `ic_data.generate()` = 실행 Blender 이하 중 최신 파일의 deepcopy. 패키지 안에 execfile 없음.
  IC `Params.use_mouse_emulate_3_button` 는 IC 데이터에서 쓰이지 않음 (grep) → 기본값으로 생성.
- `keymap.activate()` (register / switch 가 호출, 멱등): `generate_data()` (IC + `maya_patches`, 5.x DRIFT 처리 그대로) →
  1. 모달이 아닌 키맵: 모든 Maya 항목을 **애드온 keyconfig** 같은 이름·space·region 키맵에 **역순** 으로 추가 (a, d).
  2. 활성 keyconfig 의 같은 키맵 항목 중 켜진 것을 메모리에서 끔 (e) — 기록은 (키맵, 인덱스, idname, 이벤트) 데이터만.
  3. 모달 키맵 (Transform / Knife 13 항목 차이): 활성 keyconfig 모달 맵에서 Maya 에 없는 항목을 끄고 없는 Maya 항목을
     `new_modal` 로 추가 (b). 맵이 없으면 (`-b`) 만들고 해제 때 지운다.
  4. 영구 타이머 `_watch` (1 s, 해제 때 unregister): 활성 keyconfig 가 바뀌거나 (사용자가 다른 프리셋 선택, keyconfig
     환경설정으로 프리셋 재생성, 시작 시 프리셋이 애드온보다 늦게 로드) 끈 항목이 다시 켜져 있으면 이전 것을 되돌리고
     새 활성 keyconfig 에 다시 적용. RNA 참조는 틱을 넘겨 보관하지 않음 (포인터로 다시 찾음, CLAUDE.md step 129 #36).
- `keymap.deactivate()` / `unregister()`: 애드온 항목 (포인터) 제거 + 만든 빈 애드온 키맵 제거, 끈 항목 다시 켬, 추가한
  모달 항목·만든 모달 맵 제거, 타이머 해제. keyconfig 목록·활성 keyconfig·저장된 이름 그대로.
- 삭제: `_keep_keyconfig` load_post, `_reactivate` 영구 타이머, `wants_maya`, `build_keyconfig`, `kcs.active = ...`.
- 유지: `KEYCONFIG_NAME` (switch 가 예전 버전의 저장된 이름 정리에 씀), `add_item`, `allset.keymap_activate` (GUI 테스트들이
  부름; 이제 "적용 확인"), `activate()` / `deactivate()` 시그니처 그대로 → 레인 C 변경 불필요. 새 `is_applied()`.
- `ui/tool_settings.py`: Reset Tool / Poly Build 키 목록이 `keyconfigs.active` 대신 `keyconfigs.user` (= 활성 + 애드온,
  Blender 가 실제로 쓰는 것) 를 읽음.
- 사용자 키맵 편집 (U.user_keymaps diff 의 추가/변경 항목) 은 켜진 채 남는다: 사용자가 직접 바꾼 키는 Maya 모드에서도
  동작 (예전 "Maya-style" 활성화 때도 user diff 는 키맵 이름으로 적용됐음).

## 테스트

- `tests/kit.py maya_kc()`: 테스트가 읽는 Maya 키맵 뷰 (애드온 키맵을 유효 순서로 + 활성 keyconfig 의 모달 맵 켜진 항목).
  `keyconfigs["Maya-style"]` 를 읽던 테스트 전부 이것으로; GUI 는 `sim.maya_keys()` / `sim.maya_kc()`.
- `tests/test_step130_keymap_lifecycle.py`: 기본 keyconfig 를 Blender 데이터로 채운 뒤 (`rt60_dump.populate`) enable → Maya
  모드 → 활성 이름·저장 이름·keyconfig 목록·user-modified 키맵 불변, 애드온 Maya 항목 > 2000, 프리셋 Object Mode 항목 전부
  꺼짐, 병합 순서 = Maya 데이터 순서, Transform 모달 맵에 Maya 항목, 활성 keyconfig 교체 따라감 → Maya 모드 끔 / disable →
  모든 항목 플래그·애드온 항목·핸들러가 이전과 같음.

## 남은 것 / 위험

- 프리셋 항목을 메모리에서 끄는 것은 "활성 keyconfig 의 내용" 을 런타임에 바꾸는 것 (저장·잔존 없음, 측정 f). 심사자가
  이것까지 문제 삼으면 대안은 blocker + 키맵 체인 지식 (위 c 때문에 부정확).
- Maya 모드 중 Preferences > Keymap 에서 Blender 항목이 꺼진 것으로 보인다. 사용자가 그때 항목을 켜면 그 diff 는 사용자
  편집으로 저장된다 (사용자 행동).
- 패키지 크기: IC 정적 데이터 4 파일 ≈ 1.5 MB (zip 압축 후 +0.1 MB).
