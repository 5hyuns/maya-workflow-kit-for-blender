# Step 4 — M1-c 카메라·뷰 조작감

## 계획

근거: `research/maya/interaction.md` §1 카메라(:38-57), §7 1/2/3 (:166-172), §2 F8–F12 (:73-74), §8 프레이밍 (:189-196), §10 뷰 언두 (:216-225), §12 Space/Ctrl+Space (:248-249); `research/blender/industry_compatible_vs_maya.md` §1 (Alt+마우스 IC:674-680 일치), §2 (use_rotate_around_active).

### 1. 환경설정 프리셋 `prefs_preset.py` (delegated)

Maya 값 (헤드리스로 4.5 팩토리 값 확인 후 선택):

| 경로 | Maya 값 | 이유 |
|---|---|---|
| `inputs.view_rotate_method` | TURNTABLE | Maya 는 씬을 세운 채 월드 업축 기준 요 (interaction.md:57) |
| `inputs.use_rotate_around_active` | False | 팩토리 텀블 = Center of Interest (interaction.md:40) |
| `inputs.use_mouse_depth_navigate` | False | COI 유지 |
| `inputs.use_zoom_to_mouse` | False | Maya 돌리는 COI 방향 (커서 방향 아님) |
| `inputs.use_auto_perspective` | True | 정면/측면/윗면 = 직교 (Maya top/front/side 직교 카메라) |
| `inputs.view_zoom_method` | DOLLY | Maya dolly |
| `inputs.view_zoom_axis` | HORIZONTAL | Alt+RMB 좌우 드래그 = 돌리 [K] |
| `inputs.invert_mouse_zoom` | False | 오른쪽 드래그 = 돌리 인 [K]; GUI 실측 (True 면 오른쪽 = 돌리 아웃) |
| `inputs.invert_zoom_wheel` | False | 휠 위 = 돌리 인 (Blender 기본과 같음) |

- 적용/복원: 애드온 환경설정 `use_maya_navigation` (기본 True, 업데이트 콜백). 켤 때 사용자 원래 값을 애드온 환경설정의 숨은 문자열 `prefs_backup`(JSON)에 저장 후 Maya 값 적용, 끌 때 / 애드온 비활성화 시 복원. **백업이 이미 있으면 다시 적용하지 않는다** → 재시작 때마다 사용자가 바꾼 값을 덮어쓰지 않음 (키맵 자동 활성화와 같은 규칙).
- 테스트 스냅샷에 `preferences.inputs` / `preferences.view` 전체 값을 추가 → 활성화·비활성화 후 원래대로인지 확인.

### 2. 직교 뷰 텀블 잠금 `maya_kit.tumble`

- Alt+LMB (IC:674 `view3d.rotate`) 를 대체. 축 정렬 직교 뷰(`rv3d.view_perspective == 'ORTHO'` 이고 `is_orthographic_side_view`)이면 아무것도 안 함 (Maya top/front/side 는 텀블 잠김 — 팩토리 값 [U], 환경설정 `lock_ortho_tumble` 기본 True). 그 밖에는 `view3d.rotate('INVOKE_DEFAULT')`.
- 쿼드 뷰의 직교 영역은 Blender 가 이미 `lock_rotation` 으로 잠근다.

### 3. 프레이밍

- F = IC `view3d.view_selected` 유지 (선택만 = Maya "without children" 과 같음; 자식은 선택되지 않으면 포함 안 됨).
- A 탭 = Frame All (Step 3 `select_all` 바인딩).
- Shift+F / Shift+A = **모든 3D 뷰**(창의 모든 VIEW_3D 영역, 쿼드 영역 포함)에서 선택/전체 프레이밍: `maya_kit.frame_all_views(selected=...)`. IC Shift+F `view_center_pick`, Shift+A `view_all(use_all_regions)` 대체.

### 4. 뷰 변경 언두 `[` `]` / Alt+Z, Alt+Y

- Blender 뷰 변경은 언두에 안 들어간다 → 별도 스택이 필요.
- 기록 방법 (delegated): 내비게이션 모달 끝을 훅할 방법이 없으므로 **0.25 s 타이머가 모든 RegionView3D 상태를 폴링**. 상태가 바뀐 뒤 한 틱 동안 안정되면(드래그 끝) 이전 안정 상태를 언두 스택에 push. 키: `rv3d.as_pointer()`; 사라진 영역은 정리.
- 상태 = view_location, view_rotation, view_distance, view_perspective, view_camera_zoom/offset.
- `ViewHistory` 클래스는 bpy 없이 테스트 가능 (record/undo/redo, 최대 50, redo 는 새 기록 시 비움). 언두/리두로 설정한 상태는 기록하지 않음.
- IC `[` `]` (Object Mode select_hierarchy, IC:2506-2512) 는 Step 3 화살표 pick-walk 로 대체됐으므로 교체. 페인트 모드 `[` `]` 브러시 크기는 유지(선언된 가림).

### 5. Space 탭 = 4분할 ↔ 단일, Ctrl+Space

- Space 는 Step 11 핫박스(홀드) 자리 → `tap_hold(binding='space')`: 탭 = `maya_kit.toggle_quad_view`, 홀드+클릭 = (Step 11).
- `toggle_quad_view`: 쿼드 → 단일일 때 **커서 아래 영역의 뷰**(Maya 는 포인터 아래 패널을 최대화)를 메인 뷰에 복사. 단일 → 쿼드는 `screen.region_quadview`.
- Ctrl+Space = Maya 전체 화면(UI 숨김, interaction.md:249) → `screen.screen_full_area(use_hide_panels=True)` (IC 의 Ctrl+Space 최대화 대체).

### 6. 1/2/3 스무스 프리뷰 `maya_kit.smooth_preview(level)`

- 선택(편집 모드면 편집 중) 메시마다: 첫 Subsurf 모디파이어를 쓰고, 없으면 "Maya Smooth Preview" (levels 2 = Maya 기본 divisions, `show_render=False` — 렌더에는 영향 없음) 추가.
- 1 = 모디파이어 viewport 끔, 2 = 켬 + 오브젝트 와이어 표시(Maya 케이지+스무스 근사, **W**), 3 = 켬 + 와이어는 우리가 켠 경우만 끔.
- IC Object Mode 1/2/3 (컴포넌트 진입, IC:2558-2563), Mesh 1/2/3 (select_mode, IC:164-177) 대체 → 컴포넌트는 F9–F11.

### 7. F7 / F9 / F10 / F11 컴포넌트 모드 `maya_kit.component_mode(type)`

- F9 정점, F10 엣지, F11 면, F7 멀티(세 가지 동시), 오브젝트 모드면 편집 모드로 진입. F8 = Step 2 editmode_toggle. F12 UV = Blender 3D 뷰에 UV 컴포넌트 선택 없음 → 해당 없음.
- "Object Non-modal" (모든 오브젝트 모드에서 활성).

### 테스트

- 헤드리스: 프리셋 적용·백업·복원·재적용 안 함·비활성화 복원, ViewHistory 로직, 상태 캡처/적용, smooth_preview(모디파이어 생성/재사용/레벨), component_mode, tumble 잠금 판정, frame_all_views 가 영역 수만큼 실행, toggle_quad_view(쿼드 on/off, 뷰 복사), 키 바인딩·충돌·가림, 매핑 표.
- GUI(이벤트 시뮬레이션): Alt+RMB 드래그 방향, 직교 뷰 Alt+LMB 잠금, `[` `]` 실제 내비게이션 후 복원, Space 탭 쿼드 토글, 1/2/3, F9–F11.

## 한 것

- `src/maya_kit/prefs_preset.py`: Maya 내비게이션 환경설정 9개 적용, 원래 값 JSON 백업(`prefs_backup`)·복원, 한 번만 적용. 애드온 환경설정 `use_maya_navigation`(토글 시 적용/복원), `lock_ortho_tumble`.
- `operators/view.py`: `maya_kit.tumble`(직교 축 뷰 잠금), `maya_kit.frame_all_views`, `ViewHistory` + 0.25 s 폴링 타이머 + `maya_kit.view_history`, `maya_kit.toggle_quad_view`(떠날 때 커서 아래 쿼드의 뷰 유지).
- `operators/display.py`: `maya_kit.smooth_preview`(1/2/3), `maya_kit.component_mode`(F7/F9/F10/F11).
- `operators/taphold.py`: `space` 바인딩 (탭 = 4분할 토글, 홀드 = Step 10 핫박스 자리).
- 키맵 패치 9–13: Alt+LMB, Shift+F, Shift+A, `[` `]` Alt+Z Alt+Y, Space, Ctrl+Space(Screen), 1/2/3(Object Mode·Mesh), F7/F9/F10/F11. 대응표: 구현 24 → 38.
- `tests/kit.py` 스냅샷에 `preferences.inputs`/`view` 전체 값 추가.
- `docs/PLAN.md` 재번호 (사용자 순서 5 레이아웃 / 6 Channel Box / 7 상단 UI; 남은 M1 → 8).

## 검증

```
python tests/run.py        → 55 passed, 0 failed, 5 file(s)
python tests/gui/run.py    → 36 passed, 0 failed, 2 file(s)   (step 3: 17, step 4: 19)
python tools/gen_keymap_mapping.py → exit 0 (구현 38, IC 12, 계획 30, 해당 없음 9)
```

- 헤드리스 `test_step4_view.py` (16): 활성화 시 프리셋 값·백업, 옵션 끔→팩토리 복원·켬→재적용, 재시작(register 재호출) 때 사용자 변경 유지, 비활성화 복원, ViewHistory(안정화 후 기록·언두/리두·복원 상태 재기록 안 함·새 변경 시 redo 비움·미안정 변경 선기록·limit·미관측), capture/restore 왕복, 타이머 등록/해제, 텀블 잠금 규칙, 스무스 프리뷰(생성·렌더 끔·levels 2·와이어·재사용·사용자 Subsurf/와이어 보존), 컴포넌트 모드 4종, 키 바인딩. `test_enable_disable`: 환경설정 값까지 원상 복구.
- GUI (`gui_step4_view.py`, 19): Alt+RMB 오른쪽 드래그 = 돌리 인 / 왼쪽 = 아웃 (**실측으로 `invert_mouse_zoom=False` 결정**; True 였을 때 오른쪽 = 아웃), 정면 직교 Alt+LMB 잠금 / 원근 텀블, Alt+MMB 트랙 후 `[` 복원 `]` 재적용, Space 탭 4분할 → 좌상단(Top) 위에서 Space 탭 → 단일 Top 직교 뷰, Shift+A 프레이밍, 3 → Subsurf 켬 / 1 → 끔, F10 엣지·F9 정점·F8 오브젝트, Ctrl+Space 전체 화면 on/off.
- 스크린샷: 4분할(Top/User Persp/Front/Right), 3 누른 뒤 큐브가 매끄럽게 표시 + "Smooth Mesh Preview" 오퍼레이터 패널.

## 결정 (delegated)

- 프리셋은 한 번만 적용, 이후 사용자 변경 존중 (키맵 자동 활성화와 같은 규칙). 원래 값은 애드온 환경설정에 저장 → 재시작 후에도 복원 가능.
- 뷰 히스토리는 폴링 방식 (내비게이션 모달 종료 훅 없음). 0.25 s 동안 움직임이 없어야 한 단계로 기록 — 아주 빠른 연속 조작은 한 단계로 합쳐질 수 있음.
- 직교 텀블 잠금 기본 켬 (Maya 팩토리 값은 [U]), 환경설정으로 끌 수 있음.
- 스무스 프리뷰 모디파이어는 `show_render=False` (렌더 결과 불변). 2 = 와이어 표시로 케이지 근사.
- F12(UV), Alt+F9(vertex-face)는 Blender 에 대응 없음 → 해당 없음.
- PLAN 재번호.

## 남은 것

- 프레이밍 fit factor 0.95, Ctrl+Shift+F(자식 포함), Home, 0 → Step 8.
- Space 홀드 = 핫박스 → Step 10 (`taphold.SpaceBinding` 에 `click()` 추가).
- 다른 에디터(아웃라이너 등)에서 Space 탭 = 패널 최대화는 아직 없음 (Ctrl+Space 는 전체 화면).
- 돌리 축은 가로만 (Maya 는 세로 드래그도 돌리 [K]).
