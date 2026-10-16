# Step 3 — M1-b 홀드/탭 프레임워크, 피벗 편집, pick-walk

## 계획

근거: `research/maya/interaction.md` §0 (press/release 관용구, 탭=동작·홀드+클릭=마킹메뉴), §4 피벗 (D 홀드, Insert 토글), §5 스냅 (X/C/V 홀드), §6 소프트 셀렉트 (B), §2 pick-walk (화살표); `research/blender/api_limits.md` §7 (Affect Only Origins 로 D 홀드 흉내).

### 문제와 선택 (delegated)

1. **RELEASE 가 사라지는 문제.** Maya 사용자는 X 를 누른 채 매니퓰레이터를 드래그한다. 그 사이 Blender 트랜스폼 모달이 핸들러 맨 위에 올라가 키 RELEASE 를 먼저 받는다. 키맵 PRESS/RELEASE 두 항목만 쓰면 RELEASE 를 놓쳐 스냅이 켜진 채 남는다.
   - 선택: PRESS 키맵 → **홀드 모달** (`maya_kit.hold`). 모달은 자기 키의 RELEASE 를 기다리고, 그 밖의 이벤트는 모두 PASS_THROUGH (기즈모·툴·트랜스폼 정상 동작).
   - 놓친 RELEASE 대비: 모달이 0.05 s 타이머로 **OS 키 상태**를 확인 (Windows `user32.GetAsyncKeyState`, `operators/keystate.py`). 다른 OS 는 이벤트에만 의존 (알려진 한계).
   - 키 반복(PRESS repeat)은 모달이 삼킨다.
2. **상태 복원.** 홀드 그룹(스냅 / 피벗)마다 첫 PRESS 때 원래 값을 저장하고, 그룹의 마지막 홀드가 끝날 때 복원. X+V 동시 홀드 = 스냅 요소 합집합. Maya 는 release 때 무조건 끔(`snapMode -grid 0`, interaction.md:141 [I]) 이지만 **원래 값 복원**을 택함 — 상태줄에서 켜 둔 스냅을 X 홀드가 꺼버리지 않게.
3. **스냅 대응** (Blender 4.5 `snap_elements` 열거: INCREMENT, GRID, VERTEX, EDGE, FACE, …, 헤드리스 확인):
   - X / Shift+X 그리드 → `{'GRID'}` (절대 그리드)
   - C / Shift+C 커브 → `{'EDGE'}` (Blender 에 NURBS 커브 전용 스냅 없음; 엣지·커브 선분 위 스냅, **W**)
   - V / Shift+V 점 → `{'VERTEX'}`
   - J / Shift+J 스텝 → `{'INCREMENT'}` (상대 증분; Maya J = 이동/회전/스케일 스텝 스냅 토글)
   - 한계: Blender 트랜스폼은 시작할 때 스냅 설정을 읽는다 → **드래그 시작 전에** 키를 눌러야 한다. 드래그 중 X/Y/Z 는 Transform Modal Map 의 축 제한 그대로 (`research/blender/industry_compatible_vs_maya.md` §3).
4. **D 홀드 / Insert** (오브젝트 모드): 홀드 동안 `tool_settings.use_transform_data_origin = True` (Affect Only Origins), 놓으면 복원. Insert = 같은 값 토글 (`maya_kit.pivot_toggle`). 편집 모드 컴포넌트 피벗은 커서 우회가 필요 → 범위 밖 (편집 모드 D 는 IC 그대로).
5. **탭 vs 홀드 범용 모달** (`maya_kit.tap_hold(binding=...)`, M3 마킹메뉴가 쓸 API):
   - `operators/taphold.py` 의 `TapHoldBinding` 서브클래스를 `register_binding()` 으로 등록. 메서드: `tap(context)`, `click(context, event)` (홀드 중 LMB 누름; `'DRAG'` 반환 시 드래그 시작), `drag(context, event, start)`, `drag_end(context)`, `drag_cancel(context)`.
   - 키 RELEASE 때 클릭이 한 번도 없었으면 `tap()`. 홀드 중 LMB 는 소비 (선택이 일어나지 않음). ESC 는 드래그 취소.
   - M3 는 `click()` 에서 자체 마킹메뉴 모달을 띄우면 된다.
   - 이번 단계 바인딩:
     - **A**: 탭 = `view3d.view_all(center=False)` (IC 와 같은 Frame All), 홀드+클릭 = 선택 메뉴 (`VIEW3D_MT_select_object`/모드별) — Maya `buildSelectAllMM` 자리, 진짜 마킹메뉴는 Step 10.
     - **B**: 탭 = 소프트 셀렉트(proportional editing) 토글 (오브젝트 모드는 `use_proportional_edit_objects`, 편집 모드는 `use_proportional_edit`), 홀드+LMB 좌우 드래그 = `proportional_size` 조절 (×2^(dx/100), 켜짐 보장, 헤더에 반경 표시, ESC 원복). interaction.md:155-156.
6. **Pick-walk** (`maya_kit.pick_walk(direction)`, 오브젝트 모드): ↑ 부모, ↓ 첫 자식, ←/→ 형제(이름순 = Outliner 기본 정렬, 끝에서 순환 [K]). 루트의 형제 = 뷰 레이어의 부모 없는 오브젝트. 선택된 각 오브젝트를 걸은 결과가 새 선택, 활성은 활성 오브젝트의 결과. 컴포넌트 pick-walk 는 다음 루프 (Mesh 화살표는 IC 그대로).

### 키맵 패치

| 키 | 키맵 | 새 바인딩 | 제거 (IC) |
|---|---|---|---|
| X, Shift+X | 3D View | `maya_kit.hold(name='grid')` | 3D View X 스냅 토글, Shift+X 스냅 파이 |
| C, Shift+C | 3D View | `hold(name='curve')` | Object Mode/Mesh/Curve/Curves/Armature/Metaball C 커서 툴 |
| V, Shift+V | 3D View | `hold(name='point')` | 3D View V 뷰 파이 |
| J, Shift+J | 3D View | `hold(name='step')` | — |
| B | 3D View | `tap_hold(binding='soft_select')` | Object Mode/Mesh/Curve/Curves/Metaball/Lattice/Particle B proportional 토글 |
| D | Object Mode | `hold(name='pivot')` | Object Mode D annotate |
| Insert | Object Mode | `pivot_toggle` | — |
| A | 3D View | `tap_hold(binding='select_all')` | 3D View A view_all |
| ↑↓←→ | Object Mode | `pick_walk` | Object Mode select_more/less, frame_offset |

- 페인트/스컬프트 모드 키맵(X 색 뒤집기, B 브러시 셸프, D/C 툴)은 3D View 보다 먼저 잡히도록 **그대로 둔다** (그 모드의 자체 동작). 가림 검사에서 의도된 가림으로 명시(`_add(..., shadows=...)`).
- IC 의 ←/→ 프레임 이동은 Frames 가 아니라 모드별 키맵마다 들어 있다 (IC:93-97 `_template_items_animation`). Object Mode 것만 pick-walk 로 교체 → 3D 뷰 오브젝트 모드에서는 화살표 프레임 이동이 없어진다 (Maya 는 Alt+,/. — Step 9).

### 테스트 (헤드리스)

- 홀드 매니저 begin/end: 저장·적용·합집합·복원, 중복 begin, 순서 뒤섞인 end.
- `keystate` 매핑 (Windows 에서 키 안 누른 상태 = False).
- 탭/홀드: 바인딩 레지스트리, B 탭 토글(모드별 속성), 반경 드래그 계산·ESC 복원 함수, A 탭.
- pivot_toggle, pick_walk (부모/첫 자식/형제 순환/루트/다중 선택).
- 키맵: 각 키 바인딩·제거 확인, 새 충돌 0, 가림 0 (의도된 가림 제외), 매핑 표 KIT 행.
- 모달 실제 입력(홀드 중 드래그, 놓친 RELEASE, B 드래그 감각)은 `docs/manual_checks.md`.

## 한 것

- `operators/hold.py`: 홀드 매니저(`begin`/`end`/`end_all`, 그룹별 저장·합집합·복원) + `maya_kit.hold` 모달 + `maya_kit.pivot_toggle`. 비활성화 중 홀드가 남아 있으면 복원.
- `operators/keystate.py`: Windows `GetAsyncKeyState` 로 놓친 RELEASE 감지.
- `operators/taphold.py`: `maya_kit.tap_hold` 모달 + `TapHoldBinding` API (`tap`/`click`/`drag`/`drag_end`/`drag_cancel`, `register_binding`). 바인딩: `soft_select`(B), `select_all`(A).
- `operators/pickwalk.py`: `maya_kit.pick_walk` (↑ 부모, ↓ 첫 자식, ←/→ 이름순 형제 순환).
- `keymap/maya_patches.py` 패치 5–8 (X/C/V/J + Shift, B, A, D, Insert, 화살표) + `_add(shadows=...)` 의도된 가림 선언. 대응표: 구현 8 → 24.
- `tests/gui/`: GUI 이벤트 시뮬레이션 러너(`run.py`), 공용 헬퍼(`sim.py`), `gui_step3_hold.py`.

## 검증

```
python tests/run.py        → 39 passed, 0 failed, 4 file(s)
python tests/gui/run.py    → 17 passed, 0 failed, 1 file(s)
python tools/gen_keymap_mapping.py → exit 0 (구현 24, IC 12, 계획 45)
```

- 헤드리스 `test_step3_hold.py` (16): 홀드 저장·적용·합집합·순서 뒤섞인 해제·중복 begin·스트레이 release, 스냅 이름→요소, 피벗/스냅 독립, end_all, **홀드 중 비활성화 시 복원**, keystate (Windows 에서 안 눌림=False), pivot_toggle, 탭/홀드 레지스트리, B 탭 모드별 속성, B 드래그 ×2/×0.5·ESC 원복, pick-walk (부모·첫 자식·형제 순환·제자리·다중 선택 합치기·활성), 키 바인딩/제거.
- `test_keymap_maya.py`: 새 충돌 0, 가림 0 (선언된 페인트 모드 가림 제외; Object Mode 항목은 오브젝트 모드 키맵 묶음 기준으로 검사).
- GUI (`--enable-event-simulate`, 샌드박스, 띄운 PID 만): X/V 홀드·합집합·복원, D 홀드, Insert, B 탭·B+LMB 드래그 반경 2배·드래그 후 놓아도 토글 안 됨, A 탭 Frame All, A 홀드+클릭 메뉴(선택 유지), ↓/↑ pick-walk, **X 를 누른 채 Move 툴로 드래그 → 드래그 중 X 를 놓음 → 드래그 후 스냅 복원** (keystate 폴백 경로).
- 스크린샷 확인: B 드래그 중 3D 뷰 헤더 "Soft Select radius: 2.000" + 헤더 proportional 아이콘 켜짐; A 홀드+클릭 후 Select 메뉴, 상태바 "Pivot edit on" 보고.

## 결정 (delegated)

- 키맵 PRESS/RELEASE 두 항목 대신 PRESS → 모달 방식 (트랜스폼 모달이 RELEASE 를 먹는 문제), + OS 키 상태 폴백.
- release 시 Maya 처럼 무조건 끄지 않고 원래 값 복원.
- C 커브 스냅 = EDGE (근사), J/Shift+J = INCREMENT.
- A 홀드+클릭 메뉴는 LMB **뗄 때** 연다 — 누를 때 열면 떼는 순간 커서 아래 첫 항목("All")이 실행됨 (GUI 테스트에서 발견).
- 페인트/스컬프트 모드의 X/B/C/D 는 그 모드 동작 유지 (선언된 가림).
- 3D 뷰 오브젝트 모드의 ←/→ 프레임 이동은 pick-walk 로 대체 (Maya 프레임 이동 Alt+,/. 는 Step 9).

## 남은 것

- 드래그 **중에** X/C/V 를 눌러 스냅을 켜는 것은 불가 (Blender 트랜스폼이 시작 시 스냅 설정을 읽고, 드래그 중 X 는 축 제한) — 문서화된 한계.
- Windows 외 OS 에서는 놓친 RELEASE 폴백 없음.
- 편집 모드 D (컴포넌트 피벗), 컴포넌트 pick-walk (엣지 링 등) → Step 6.
- A/W/E/R 진짜 마킹메뉴 → Step 10 (`TapHoldBinding.click()` 에서 마킹메뉴 모달 시작).
- B 반경 원 그리기(뷰포트 피드백) 없음 — 헤더 텍스트만.
