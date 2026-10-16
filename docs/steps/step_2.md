# Step 2 — M1-a Maya 키컨피그 기반

## 계획

### 구조 (delegated)

| 파일 | 역할 |
|---|---|
| `src/maya_kit/keymap/ic_data.py` | 설치본 `$S\presets\keyconfig\keymap_data\industry_compatible_data.py` 를 `bpy.utils.execfile` 로 읽어 `generate_keymaps(Params())` 데이터를 **매번 새로** 만든다 (IC 프리셋 로더 `$S\presets\keyconfig\Industry_Compatible.py:21-34` 와 같은 방식). 저장소에 IC 사본을 두지 않는다 → Blender 패치 버전이 바뀌어도 따라간다. |
| `src/maya_kit/keymap/patch.py` | 키컨피그 데이터(`[(km_name, km_args, {"items": [(idname, event, props)]})]`) 조작 도구: 찾기·제거·추가·선택 규칙 재작성·충돌 검사. 순수 Python (bpy 불필요) → 문서 생성기·테스트가 같이 쓴다. |
| `src/maya_kit/keymap/maya_patches.py` | 이번 단계 패치 목록. 패치마다 근거 `research/...:line`. |
| `src/maya_kit/keymap/mapping.py` | Maya runTimeCommand → Blender 처리 표 (상태: IC 일치 / KIT 패치 / 계획 Step N / 불가). 문서 생성기와 테스트가 공유. |
| `src/maya_kit/keymap/__init__.py` | register: `keyconfigs.new("Maya")` + `keyconfig_init_from_data` + 활성화. unregister: 이전 키컨피그로 되돌리고 "Maya" 제거. |
| `tools/gen_keymap_mapping.py` | Blender 헤드리스로 실행. `research/maya/hotkeys_default.json` 468개 → Maya 키를 Blender 이벤트로 바꿔 생성된 Maya 키컨피그에서 실제 바인딩 조회 → `docs/keymap_mapping.md`. MEL 본문·Maya 설명 문자열은 옮기지 않는다 (decision 6) — 키, 컨텍스트, runTimeCommand 이름만. |

### 키컨피그 활성화 규칙 (delegated)

- 처음 켤 때(애드온 환경설정의 숨은 플래그 `keymap_auto_activated` 가 False) "Maya" 를 활성화하고 플래그를 켠다. 이후 재시작 때는 사용자가 마지막으로 고른 키컨피그 이름이 "Maya" 일 때만 다시 활성화한다 → 사용자가 다른 키맵으로 바꾸면 존중.
- 환경설정에 「Maya 키맵 활성화」 버튼 (`maya_kit.keymap_activate`). "Maya" 는 프리셋 파일이 아니라 키맵 드롭다운에 다시 나타나지 않기 때문.
- 비활성화: 활성 키컨피그가 "Maya" 면 켜기 전 키컨피그(없으면 기본)로 되돌린 뒤 제거.

### 패치 (이번 단계)

1. **선택 규칙** (`research/maya/interaction.md:68-70` Shift=토글, Ctrl=해제, Ctrl+Shift=추가). 모든 키맵에서 같은 오퍼레이터·같은 이벤트 값(CLICK/PRESS/CLICK_DRAG)의 LMB 항목 중 Alt 없는 것들을 지우고 4개(없음/Shift/Ctrl/Ctrl+Shift)로 다시 만든다. Alt 조합(enumerate, column 등)은 유지.
   - 클릭: `view3d.select`, `uv.select` → deselect_all / toggle / deselect / extend (정확히 P).
   - 클릭: `outliner.item_activate`, `graph.clickselect` 에는 `deselect` 속성이 없다 (`research/blender/operators.json`). Ctrl 은 토글(extend)로 근사, Ctrl+Shift 도 토글 → **W**, 정확한 해제/추가는 후속 래퍼 오퍼레이터 (Step 5 후보). 참고: Maya 실제 Outliner 는 Ctrl=토글, Shift=범위 [K, 미확인] — 사용자 지시(뷰포트와 동일 규칙)를 따름, manual_checks 에 확인 항목.
   - 박스: `view3d.select_box` → mode SET / XOR / SUB / ADD (정확히 P). `uv/outliner/graph.select_box` 는 mode 에 XOR 가 없어(SET/ADD/SUB, 헤드리스 확인) Shift 는 ADD 로 근사 (**W**). 빠진 Ctrl+Shift 변형도 추가.
   - Graph Editor IC:935 Ctrl+Shift+LMB `graph.select_leftright` 제거 (Ctrl+Shift 클릭 = 추가와 충돌).
2. **4/5/6/7 디스플레이** (`research/maya/interaction.md:174-177`): 새 오퍼레이터 `maya_kit.display_mode` (포인터 아래 3D 뷰 = 키맵이 "3D View" 라 자연히 그 영역).
   - 4 WIREFRAME → `shading.type='WIREFRAME'`
   - 5 SHADED → SOLID, `color_type='MATERIAL'`
   - 6 TEXTURED → SOLID, `color_type='TEXTURE'`
   - 7 LIGHTS → MATERIAL 미리보기, `use_scene_lights=True`, `use_scene_world=False` (Maya "Use All Lights" 근사, **W**)
   - 충돌 제거: IC "Object Non-modal" FOUR(object 모드)·FIVE(모드 파이) (`industry_compatible_vs_maya.md` IC:3458-3459). 오브젝트 모드 복귀 수단이 사라지므로 **F8 → `object.editmode_toggle`** (Maya F8 = 오브젝트↔마지막 컴포넌트, `interaction.md:73`) 를 같이 추가. F9-F12 는 Step 5.
3. **Ctrl+G 그룹** (`research/maya/concepts.md:89-91`): 새 오퍼레이터 `maya_kit.group`.
   - Empty 생성, 공통 부모가 있으면 그 아래(로컬 단위행렬 = 부모 원점), 아니면 월드 원점. 피벗 = 원점 (Maya zeroPivot).
   - 선택 객체를 그룹 자식으로: 월드 유지, `matrix_parent_inverse` = 단위행렬 (decision 2 Maya 방식).
   - 이름: `group1`, `group2` … 쓰이지 않은 가장 작은 번호 [K]. 선택 없음 → 빈 그룹 (Maya `-em`).
   - 결과: 그룹만 선택·활성 (Maya 와 동일 [K]).
   - 키: "Object Mode" Ctrl+G (`object.move_to_collection` 대체, IC:2547), "Outliner" Ctrl+G (같은 대체).
4. **Space 비우기** (핫박스 자리, Step 11): "Frames" SPACE → `screen.animation_play` 제거 (IC:2258). **Alt+V** → `screen.animation_play` (Maya PlaybackToggle), **Alt+Shift+V** → `screen.frame_jump(end=False)` (Maya GoToMinFrame). `research/maya/hotkeys_default.json` Alt+v / Alt+Shift+V.

### 충돌 검사 (테스트)

- 키맵 내부 충돌: 같은 키맵 안에서 이벤트(type, value, any, shift, ctrl, alt, oskey, key_modifier)가 같은 항목 쌍. **IC 에 원래 있던 충돌은 기준선**으로 빼고, Maya 키컨피그가 새로 만든 충돌이 0 이어야 한다.
- 가림(shadowing) 검사: 3D 뷰에서 동시에 걸리는 키맵 묶음(Object Mode, Mesh, Object Non-modal, 3D View, 3D View Generic, Frames, Screen, Window …)에서 우리가 추가한 이벤트가 다른 항목과 겹치면 실패.
- 매핑 표의 "KIT"/"IC" 행은 생성된 키컨피그에서 실제로 그 키로 그 오퍼레이터가 걸려 있어야 한다.

### 다음 단계 고려

- Step 3 홀드/탭: 같은 생성기에 PRESS/RELEASE 쌍을 추가하는 패치 함수 (`patch.add`) 재사용.
- Step 4/5: F/A, `[` `]`, 1/2/3, F9-F12 도 `maya_patches.py` 에 추가하고 `mapping.py` 상태만 바꾸면 문서가 갱신된다.

## 한 것

- `src/maya_kit/keymap/`: `ic_data.py` (설치본 IC 데이터 생성), `patch.py` (데이터 조작·충돌 검사, bpy 없음), `maya_patches.py` (이번 단계 패치 4종 + `ADDED` 기록), `mapping.py` (runTimeCommand → 상태 표, Maya 키 → Blender 이벤트 변환), `__init__.py` ("Maya" 키컨피그 생성·활성화·복원, `maya_kit.keymap_activate`).
- `src/maya_kit/operators/display.py` `maya_kit.display_mode` (4/5/6/7), `operators/group.py` `maya_kit.group` (Ctrl+G).
- `preferences.py`: 숨은 `keymap_auto_activated` 플래그, 활성 키맵 표시 + 「Activate Maya Keymap」 버튼.
- 키 변경: 선택 규칙(뷰포트 클릭·Tweak 툴·박스 선택 툴, UV, Outliner, Graph), 3D View 4/5/6/7, F8 오브젝트↔에디트, Object Mode·Outliner Ctrl+G, Frames Space 제거 → Alt+V 재생 / Alt+Shift+V 처음 프레임.
- `tools/gen_keymap_mapping.py` → `docs/keymap_mapping.md` (468행: 구현 8, IC 일치 13, 계획 59, 해당 없음 7, 미검토 313, macOS 전용 68). IC/KIT 행이 실제 바인딩과 다르면 exit 1.

## 검증

```
python tests/run.py
23 passed, 0 failed, 3 file(s)
```

- `test_keymap_maya.py` (12): Maya 키컨피그 활성·크기(≥240 keymaps, >2000 items), 선택 규칙 클릭/박스 전부, 4/5/6/7·F8, Ctrl+G, Space 비어 있음(11개 키맵)·Alt+V, **키맵 내부 새 충돌 0** (IC 기준선 대비), **추가 바인딩 가림 0** (3D 뷰 키맵 묶음·Outliner 묶음·Frames 는 전체), 매핑 표 IC/KIT 행 21개 실제 바인딩 일치, 비활성화 시 이전 키컨피그 복원·"Maya" 제거.
- `test_operators_step2.py` (7): 4개 모드 셰이딩 값, 3D 뷰 컨텍스트에서 오퍼레이터 실행 + 비 3D poll 거부, 그룹 월드 원점·공통 부모 아래(로컬 단위행렬)·자식 월드 행렬 유지·parent inverse 단위행렬·`group1/2` 최소 빈 번호·빈 선택·재그룹(중첩).
- `test_enable_disable.py` (4): 스냅샷에 키컨피그 목록·활성 키컨피그 추가 후에도 통과.
- GUI 스크린샷 (샌드박스 사용자 폴더, 띄운 PID 만 종료): 환경설정 Keymap 드롭다운 "Maya", Outliner `group1` (위치 0,0,0, Cube 자식), 뷰포트 헤더 와이어프레임 버튼 활성.
- `python tools/gen_keymap_mapping.py` exit 0.

## 결정 (delegated)

- IC 데이터는 저장소에 복사하지 않고 설치본에서 매번 생성 (`patch.remove` 가 대상이 사라지면 예외 → Blender 업데이트 때 바로 드러남).
- 4 = 오브젝트 모드 제거로 생기는 공백은 Maya F8 로 메움 (F9–F12 는 Step 5).
- 7 (All Lights) = Material Preview + 씬 라이트, 월드 HDRI 끔 — 근사.
- Outliner 도 사용자 지시대로 뷰포트 규칙 적용. 단 Maya 실제 Outliner 는 Ctrl=토글, Shift=범위일 수 있음 [K] → manual_checks 에서 Maya 로 확인 후 조정.
- 대응표에는 Maya 설명 문자열·MEL 을 넣지 않고 키·컨텍스트·runTimeCommand 이름·`hotkeySetup.mel` 줄만 (decision 6).

## 남은 것

- Outliner·Graph 의 Ctrl 클릭 = 해제, Ctrl+Shift = 추가 정확 구현 (해당 오퍼레이터에 deselect 옵션 없음) → 래퍼 오퍼레이터, Step 5 후보. UV/Outliner/Graph Shift 마키 토글(XOR 없음)도 같음.
- 편집 모드 Ctrl+Shift 클릭은 IC "Mesh" `mesh.shortest_path_pick` 이 먼저 잡음 (3D View 보다 우선) — Maya 와 비교 필요 (manual_checks).
- 대응표 미검토 313행 (대부분 노드/하이퍼셰이드/타임에디터/스컬프트 컨텍스트) — 각 단계에서 `mapping.py` 상태 갱신.
- 첫 실행(사용자 설정 없음) 스플래시 Quick Setup 의 Keymap 드롭다운은 "Blender" 로 보이고 Continue 시 프리셋을 적용할 수 있음 — 실제 사용자는 설정이 있어 대개 해당 없음, manual_checks 에 기록.
