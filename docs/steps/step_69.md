# Step 69 — 씬 관리: Set Project · Ctrl+Alt+S 증분 · Create Reference + 네임스페이스 · Reference Editor

근거: `research/maya/workflows/scene.md` (§3 갭 표: Set Project 16, Ctrl+Alt+S 12, Create Reference 12, Reference Editor 12, Namespace 9;
§4 개념 결정 1–3, 6; §5 후보 1–2), shots scene_01_win1 (Project Window 폴더 규칙), scene_03_win1 (Reference Editor), scene_04_win1.

## 계획

### 측정 (`tmp/exp69/ref.py`, 헤드리스)
- `bpy.app.handlers.save_pre` 는 `(저장할 파일 경로, None)` 을 받는다 → 저장 직전에 렌더 출력 경로를 프로젝트 기준으로 바꿀 수 있다.
- Blender 기본 렌더 출력 = `'/tmp\\'` (팩토리).
- 레퍼런스: `bpy.data.libraries.load(link=True)` 로 원본 파일의 첫 장면을 링크 → 그 장면의 최상위 컬렉션을 현재 장면의 네임스페이스 컬렉션 `prop`
  아래에 링크 → `Collection.override_hierarchy_create(scene, view_layer, do_fully_editable=True)` → 편집 가능한 override (링크만 하고 장면에 없으면 None 을
  돌려줌, 측정). override 뒤 링크 원본은 그 컬렉션에서 뺀다 (안 빼면 원본도 같이 보임). 이름 `prop:pCube1` 로 바꿔도 저장·다시 열기 후 유지,
  override 오브젝트를 옮긴 값 (x = 3) 도 유지, 원본 파일은 그대로. 같은 파일 두 번째 = 같은 라이브러리의 새 override (`prop1:`).

### 설계 (모두 delegated)
1. **프로젝트** (`operators/project.py`): Blender 에 프로젝트가 없으므로 kit 프로젝트 = 루트 폴더 + Maya 기본 하위 폴더 (scene_01_win1:
   `scenes`, `assets`, `images`, `sourceimages`, `renderData`, `clips`, `sound`, `scripts`, `data`, `movies`, `cache`, `autosave`).
   - 현재 프로젝트 + 최근 목록 = add-on 환경설정 (`project_root`, `recent_projects`; CORE 의 `preferences.py`, Blender 설정 자체는 안 바꿈).
   - Set Project = 폴더 고르기 (`maya_kit.set_project`), Project Window = 이름 + 위치 + 폴더 목록 대화상자, Accept = 폴더 만들기 + 표시 파일
     `maya_kit_project.json` (폴더 이름 기록) + 현재 프로젝트로 (`maya_kit.project_window`), Recent Projects = 메뉴.
   - 열린 `.blend` 가 `<root>/scenes/` 아래에 있고 `<root>` 에 표시 파일이 있으면 load_post 에서 그 root 를 현재 프로젝트로 (Maya 가 씬에서
     workspace 를 찾는 것처럼 [I]).
   - **파일 창 시작 폴더**: Ctrl+O / Ctrl+S (처음 저장) / Ctrl+Shift+S / 메뉴 / Status Line 을 kit 연산자 `maya_kit.open_scene` / `save_scene` /
     `save_scene_as` 로: 프로젝트가 있으면 `wm.open_mainfile` / `wm.save_as_mainfile` 를 `filepath = <root>/scenes/…` 로 INVOKE (Blender 는
     filepath 가 설정돼 있으면 그 폴더로 연다 — GUI 테스트로 확인), 없으면 Blender 그대로. Create Reference 도 scenes 에서 시작.
   - **렌더 출력**: `save_pre` 에서 저장할 파일이 현재 프로젝트 안이고 렌더 경로가 Blender 기본 (`/tmp\`, `/tmp/`, 빈 값) 이면
     `<root>/images/` 를 파일 기준 상대 경로 (`//../images/`) 로.
   - 안내 (Project Window 맨 위, notices): "Blender has no project system: Maya Kit keeps this folder as your project…".
2. **Ctrl+Alt+S = `maya_kit.increment_save`** (Maya 규칙 `shot_v001.0001` 하나로, scene.md §4.6): "Window" 키맵의 IC 항목
   (`wm.save_mainfile(incremental)`, Ctrl+O / Ctrl+S / Ctrl+Shift+S) 을 지우고 같은 키맵 같은 자리에 kit 연산자 (`_add`, 키맵 행 KIT).
3. **Create Reference = `maya_kit.create_reference`** (Ctrl+R, Window 키맵): `.blend` 고르기 (scenes 에서 시작) + Namespace (기본 = 파일 이름,
   Maya 기본 [K]; 이미 쓰면 `prop1`, `prop2` …) → 위 측정 방식으로 링크 + override, 컬렉션 `<ns>` 아래, 오브젝트·컬렉션 이름 `ns:이름`.
   옵션 Editable (override, 기본 켬) 끄면 링크만 (편집 불가, Maya Unload 비슷). `.ma/.fbx` 는 안 됨 → 안내 (Import 사용).
   편집 모드의 Ctrl+R (메쉬 키맵 등) 처럼 에디터 키맵이 먼저 잡는 것은 그대로 (shadows 기록).
4. **Reference Editor** = Outliner 새 창, 표시 모드 Blender File (`open_editor(ui_type='OUTLINER', display_mode='LIBRARIES')`): 라이브러리 행,
   우클릭 Reload / Relocate. 안내 notice.
5. Namespace Editor / Recent Increments / Outliner Sets / Hypergraph 는 이번 범위 밖 (PLAN 「남긴 것」).

검증: 헤드리스 `tests/test_step69_scene.py` (폴더 만들기·표시 파일·최근 목록·자동 인식, 대화상자 경로 함수, save_pre 렌더 경로, 증분 키,
레퍼런스 이름·override·편집·재열기·두 번째 ns, 키맵 행), GUI `tests/gui/gui_step69_scene.py` (Project Window → 폴더 → Save As 파일 창이 scenes →
Ctrl+Alt+S → .0001 → Create Reference prop → Outliner `prop:pCube1` → Reference Editor 창 Blender File 모드), dogfood.

## 한 것

- `operators/project.py`:
  - Project Window (`maya_kit.project_window`, 안내 글 + 이름 + 위치 + Maya 폴더 12 개, Accept = 폴더 + 표시 파일 + 현재 프로젝트), Set Project
    (`maya_kit.set_project`, 폴더 고르기 + Create Default Folders), Recent Projects (`MAYAKIT_MT_recent_projects` / `maya_kit.project_recent`, 10 개).
    현재 프로젝트·최근 목록 = add-on 환경설정 `project_root` / `recent_projects` (Scene Concepts 상자에 표시).
  - `maya_kit.open_scene` / `save_scene` / `save_scene_as`: 프로젝트가 있으면 파일 창이 `<root>/scenes` 에서 (이미 프로젝트 안 파일은 그 자리), 없으면 Blender 그대로.
  - `save_pre` 핸들러: 프로젝트 안에 저장할 때 렌더 출력이 Blender 기본이면 `//../images/`. `load_post`: `<root>/scenes` 아래 파일 → 그 프로젝트가 현재.
  - Create Reference (`maya_kit.create_reference`, Ctrl+R): `.blend` + Namespace (빈칸 = 파일 이름, 겹치면 `prop1`…) + Editable (override, 기본 켬)
    → `ns` 컬렉션 아래 `ns:원래이름` (로컬 이름이 겹쳐도 원본 이름 사용), `.blend` 아님 / 자기 자신 = 오류 안내.
- 키맵 (`maya_patches.patch_scene_files`, "Window" 키맵의 IC 항목 교체): Ctrl+O / Ctrl+S / Ctrl+Shift+S / Ctrl+Alt+S (= `maya_kit.increment_save`,
  Maya 규칙 `shot_v001.0001`) / Ctrl+R. 키맵 행 5 개 KIT (`docs/keymap_mapping.md` 구현 110). `test_keymap_maya` 에 Window 스택 (모든 키맵) 추가,
  Ctrl+R 은 이미지 에디터·파일 브라우저·시퀀서의 새로고침을 그대로 둠 (shadows).
- 메뉴: File Open / Save / Save As / Create Reference / Reference Editor (= `open_editor(OUTLINER, display_mode=LIBRARIES)`) / Project Window /
  Set Project / Recent Projects. Status Line 열기·저장 아이콘도 kit 연산자. 안내 (notices) 4 개 갱신.
- `chrome.paragraph(width=)`: 대화상자 안 줄 바꿈 (GUI 스크린샷에서 잘린 안내 발견 → 수정).

## 검증

- 헤드리스 `tests/test_step69_scene.py` 6/6 (폴더·표시 파일·현재·최근, 대화상자 경로, save_pre 렌더 경로 + 사용자 경로 유지 + 자동 인식, Ctrl+Alt+S 키·행·
  Maya 규칙, 레퍼런스 ns·override·편집·두 번째 ns·편집 불가 링크·저장 재열기·오류, 메뉴·안내·최근 메뉴). step 7 / 54 / keymap 기대 갱신.
  전체 헤드리스 566/566.
- GUI `tests/gui/gui_step69_scene.py` 7/7: Project Window 대화상자 (스크린샷) → 폴더 → Ctrl+Shift+S 파일 창이 `…\proj69\scenes` (스크린샷) → 저장 →
  렌더 출력 `//../images/` → Ctrl+Alt+S → `shot_v001.0001.blend` → Ctrl+R 파일 창 scenes → `prop:pCube1` override → Reference Editor 창
  Blender File 모드에 `shot_v001.blend` (스크린샷). GUI 전체 ui 0.8: 477/477. dogfood 47/47, 콘솔 오류 0. `docs/manual_checks.md` 「Step 69」 5 항목.

## 남은 것

- Import / 이미지 열기 / 텍스처 파일 창의 시작 폴더 (Blender 메뉴 그대로라 sourceimages 로 못 보냄), Project Window 폴더 이름 편집.
- Reference Editor 의 Unload (체크 해제) · Replace · Import Objects from Reference: Blender File 보기의 Reload / Relocate 만.
- Recent Increments, Namespace Editor, Outliner Sets, Hypergraph (PLAN 「남긴 것」).
- Maya 에서 Increment 결과 파일 실측은 여전히 [U] (규칙은 MEL 주석 근거, step 34).
