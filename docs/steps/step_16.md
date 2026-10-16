# Step 16 — Maya 언두 / 가시성 / 아이솔레이트 키

재점검 1차 backlog 2 (`docs/steps/step_14.md` dogfood 실패: z, Shift+Z, h, Ctrl+1; blindspot B13).

## 계획

근거: research/maya/interaction.md §10 (:220-221 z/Ctrl+Z Undo, Shift+Z/Ctrl+Y Redo), §11 (:233-240 h, Ctrl+H,
Alt+H, Shift+H, Ctrl+Shift+H, Ctrl+Alt+H, Ctrl+1, Shift+I), §2 (:76 Ctrl+Shift+I); hotkeySetup.mel 줄은
docs/keymap_mapping.md (HK:67-69, :81, :223, :271-278, :346, :351).

현재 Maya 키컨피그(IC 기반)에서 같은 이벤트를 잡는 것 (실측, `maya_patches.apply(ic_data.generate())`):

| 키 | 지금 | 비고 |
|---|---|---|
| z | 3D View `view3d.zoom_border`, View2D `view2d.zoom_border`, Image `image.view_zoom_border`, Node Editor `node.viewer_border` | 에디터 키맵이 Screen 보다 먼저라 Undo 를 Screen 에 넣어도 가려짐 |
| Shift+Z, Ctrl+Y | 없음 | |
| h | Object Mode·Mesh 없음 (Sculpt·Grease Pencil·File Browser 에만) | |
| Shift+H | Object Mode `hide_view_set(unselected=True)`, Mesh `mesh.hide(unselected=True)` | Maya 와 반대 의미 |
| Alt+H | Object Mode `hide_view_clear`, Mesh `mesh.reveal` | Maya 와 반대 의미 |
| Ctrl+Shift+H | 없음 | |
| Ctrl+1 | Mesh `mesh.select_mode(VERT, use_expand)`, Sculpt `subdivision_set` | |
| Ctrl+Shift+I | 없음 (IC 반전은 Ctrl+I) | |

결정 (모두 delegated):

1. **Undo/Redo = "Screen" 키맵** (IC 의 Ctrl+Z 와 같은 곳, 어느 에디터에서나): z → `ed.undo`, Shift+Z·Ctrl+Y → `ed.redo`.
   z 를 가리는 zoom/viewer border 4개(3D View, View2D, Image, Node Editor)를 지운다. Blender zoom border 는 Shift+B 로 남음.
   텍스트 에디터·콘솔·UI 텍스트 필드는 TEXTINPUT 으로 먼저 받으므로 z 입력은 그대로. Outliner·Graph Editor 도 Screen 을 거쳐 언두.
2. **가시성 = 킷 연산자 `maya_kit.visibility(action)`** (`operators/visibility.py`), Object Mode:
   - h `TOGGLE` — Maya toggleVisibilityAndKeepSelection. Blender 는 숨기면 선택이 풀린다 (`hide_set` 실측) → 숨긴 객체에
     ID 속성 `maya_kit_kept` 를 달아 "선택 유지" 를 흉내: 보이는 선택이 있으면 그것을 숨기고 표시(이전 표시는 지움),
     보이는 선택이 없으면 표시된 객체를 다시 보이고 선택. (사용자가 다른 것을 고르면 그것이 새 대상.)
   - Ctrl+H `HIDE` (IC `hide_view_set` 대신 — "마지막 숨김" 기록 때문), Alt+H `HIDE_UNSELECTED`,
     Shift+H `SHOW_SELECTED` (선택 유지 표시가 있는 숨긴 객체 + 숨겨진 활성 객체), Ctrl+Shift+H `SHOW_LAST`
     (가장 최근 킷 숨김 동작이 숨긴 객체; ID 속성 `maya_kit_last_hidden`).
   - Mesh (컴포넌트): Ctrl+H `mesh.hide` 유지, Alt+H → `mesh.hide(unselected=True)`, Shift+H·Ctrl+Shift+H·Ctrl+Alt+H →
     `mesh.reveal` (Blender 는 숨긴 컴포넌트를 고를 수 없어 "선택된 것 보이기" 근사 = 전부 보이고 선택).
   - 다른 모드(커브·아마추어·포즈 등)와 Outliner 의 가시성 키는 이번 범위 밖 — 남은 것.
3. **Ctrl+1 Isolate Select** = "3D View" `view3d.localview(frame_selected=False)` (Maya 는 카메라를 옮기지 않음, 다시 누르면 해제).
   Mesh 의 Ctrl+1 제거. Sculpt 의 Ctrl+1 은 그대로 (shadows). Shift+I 는 IC 가 이미 `view3d.localview` → IC 일치로 표시.
4. **Ctrl+Shift+I 반전**: Object Mode `object.select_all(INVERT)`, Mesh `mesh.select_all(INVERT)`.
5. 테스트 지뢰 (step_14 B9): 새 Screen 바인딩은 `_STACKS["Screen"] = None` (모든 키맵) 으로 가림 검사 → 위 border 제거로 통과해야 함.
   Ctrl+H 매핑 행(IC `object.hide_view_set`)은 KIT `maya_kit.visibility` 로 바꾼다.

검증: 헤드리스 (키 바인딩·가림 검사·매핑 행, visibility 연산자 동작: h 두 번, Ctrl+Shift+H, Shift+H, Alt+H, 언두),
GUI 이벤트 테스트 (z 로 삭제 되돌림, Shift+Z 다시 실행, h 숨김/보임, Ctrl+1 local_view 들어감/나옴, Outliner 위 z),
`python tools/dogfood.py` 의 z/Shift+Z/h/Ctrl+1 체크 PASS.

## 한 것

- `keymap/maya_patches.py` 18 `patch_undo_visibility`: Screen z → `ed.undo`, Shift+Z·Ctrl+Y → `ed.redo`; z 를 가리던
  `view3d.zoom_border`·`view2d.zoom_border`·`image.view_zoom_border`·`node.viewer_border` 제거. Object Mode H 다섯 가지 →
  `maya_kit.visibility` (IC Ctrl+H/Shift+H/Alt+H 제거). Mesh Alt+H → `mesh.hide(unselected)`, Shift+H·Ctrl+Shift+H·Ctrl+Alt+H →
  `mesh.reveal`. 3D View Ctrl+1 → `view3d.localview(frame_selected=False)` (Mesh Ctrl+1 제거, Sculpt 는 shadows).
  Object Mode·Mesh Ctrl+Shift+I → 선택 반전.
- `operators/visibility.py` `maya_kit.visibility(action)`: TOGGLE / HIDE / HIDE_UNSELECTED / SHOW_SELECTED / SHOW_LAST,
  ID 속성 `maya_kit_kept`(h 로 숨긴 선택) · `maya_kit_last_hidden`(마지막 숨김).
- `keymap/mapping.py`: Undo, Redo, ToggleVisibilityAndKeepSelection, HideSelectedObjects(IC→KIT), HideUnselectedObjects,
  ShowSelectedObjects, ShowLastHidden, ShowAllPolyComponents, ToggleIsolateSelect, InvertSelection = KIT; SelectIsolate = IC.
  `docs/keymap_mapping.md` 재생성: 구현 63 (51→63), IC 8, 계획 22, 미검토 298.
- 테스트: `tests/test_step16_undo_visibility.py` 7개, `tests/gui/gui_step16_undo_visibility.py` 12개.

## 검증

- `python tests/run.py` → `203 passed, 0 failed, 16 file(s)` (가림 검사·충돌 검사·매핑 행 검사 포함, `_STACKS` 변경 없이 통과:
  Screen 은 이미 "모든 키맵" 검사였고 같은 z 를 잡던 border 4개를 지웠기 때문).
- `python tests/gui/run.py` → `127 passed, 0 failed, 11 file(s)`: 3D View 위 z 로 삭제 되돌림(모달 없음), Shift+Z 다시 실행,
  z 다시 → Ctrl+Y 다시 실행, Outliner 위 z 언두, h 숨김 → h 보임 + 선택 유지, Ctrl+1 로컬 뷰 들어감(라이트 안 보임) / 나옴.
- `python tools/dogfood.py` → 45 중 41 통과 (37→41): z, Shift+Z, h, Ctrl+1 PASS. 남은 실패 4 = Ctrl+D 이름, `.`, `=`, Shift+>
  (backlog 5, 6, 이후 키 묶음, 4). 콘솔 오류 0줄.

## 남은 것

- Curve·Armature·Pose·Outliner 의 Maya 가시성 키 (지금은 IC 그대로: Shift+H 선택 외 숨김, Alt+H 전부 보이기).
- Maya Ctrl+H 는 숨긴 객체 선택을 유지하는지 미확인 [K] — 여기서는 Blender 처럼 해제 (h 만 선택 유지).
- 언두 단계 수(Blender 32 vs Maya 무한, step_14 B8)는 `prefs_preset` 작업으로 따로.
- Blender zoom border 는 Shift+B 로만.
