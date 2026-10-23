# Step 138 — 레인 PROMPT: 저장 묻기 (#57)

## 한 것

- `src/allset/ui/save_prompt.py` (새, `ui/__init__` 에 등록): Maya `saveChanges.mel` 의 묻기.
  근거 = Maya 2022 `scripts/others/saveChanges.mel:43-89`, 문구 `resources/MayaStrings:36422-36425` (제목 「Save Changes」 /
  「Warning: Scene Not Saved」, 「Save changes to ^1s?」 / 「Save changes to untitled scene?」), 버튼 `:64898-64903`
  (Save / Don't Save / Cancel).
  - `ask(context, proceed)`: 바뀌지 않은 장면이면 바로 (타이머에서) `proceed`, 바뀌었으면 묻기. 파일 로드는 늘 타이머에서
    (operator 안에서 로드 안 함, step 42).
  - Save: 경로 있음 = `wm.save_mainfile` 후 새 장면 (저장 실패 = 아무것도 안 함, Maya 와 같음). 경로 없음 = `allset.save_scene_as`
    (프로젝트 scenes 폴더의 Save As) + `save_post` 와 0.1 s 타이머로 지켜봄: 실제로 저장되면 새 장면, 브라우저가 닫혔는데 저장이
    없으면 (취소) 아무것도 안 함, 3 s 안에 브라우저가 안 뜨면 포기.
  - Don't Save = 새 장면, Cancel / Esc / 마우스가 멀리 = 그대로 (Maya "dismiss" = Cancel).
- 묻기 UI = `wm.popup_menu` (제목 + 문구 + 테 있는 버튼 세 개 한 줄). **delegated**: `invoke_popup` 은 operator 버튼을 눌러도
  닫히지 않아 (측정, KEEP_OPEN) 메뉴로 바꿈. 메뉴라서 밑줄 글자 S / D / C 로도 답하고, 다음에 열 때 지난 답이 마우스 아래에
  옴 (Blender 메뉴 기억). 버튼 너비: 메뉴는 남는 폭을 첫 버튼 (Save) 에 줌 — row / split / grid_flow / column_flow 다 같음 (측정).
- 새 장면 경로가 모두 묻기를 거침: `allset.new_maya_scene` invoke (Ctrl+N, File > New Scene = `menu_map` 그대로, Status Line 「new」
  버튼), New Scene 옵션 창 (`operators/option_windows._run_new_scene`: 저장된 옵션으로 도는 File > New Scene 도 여기 — 한 곳만
  `save_prompt.ask` 로 바꿈, **delegated**: 지시의 편집 목록 밖이지만 「모든 경로」 요구 때문에).
- `tests/gui/gui_step132_new_scene.py`: 바뀐 파일이면 RET (예전 확인 창) 대신 D (Don't Save).

### File > Open (측정)

- Maya 모드 Ctrl+O / File > Open Scene (`allset.open_scene` → `wm.open_mainfile` INVOKE) 는 바뀐 파일이면 Blender 자체 대화상자를
  **먼저** 띄움 (파일 브라우저는 그 뒤): 물음표 아이콘, 「Save changes before closing?」, 둘째 줄 파일 이름 (「Untitled.blend」),
  버튼 Save / Don't Save / Cancel. 묻기는 있으므로 킷 묻기는 더하지 않음 (레인 지시: 「없으면 더하기」). 문구는 Maya 와 다름.

## 검증

- 헤드리스 `python tests/run.py -k step138,step132,step42,step115,enable_disable,step130`: **45 passed, 0 failed** (10 파일;
  `test_step138_prompt` 7 개: 문구, Cancel, Don't Save = Maya 레이아웃 파일 로드, 경로 있는 Save = 먼저 저장 (파일 안에 새 물체) 뒤
  동작, 제목 없는 Save 의 저장 대기 / 취소 / 시간 초과, Ctrl+N 연산자와 옵션 창 경로가 모두 묻기, 등록 해제 뒤 handler / timer 없음).
- GUI `python tests/gui/run.py -k step138_prompt,step132`: **21 passed, 0 failed** (step138 19, step132 2).
- 스크린샷 (`--shots tmp/shots138`, 직접 봄): `gui_step138_prompt_untitled.png` = 「Warning: Scene Not Saved」 / 「Save changes to
  untitled scene?」 / Save · Don't Save · Cancel; `gui_step138_prompt_saved.png` = 「Save Changes」 / 「Save changes to C:\...\prompt_saved.blend?」;
  Save As 브라우저는 별도 OS 창이라 `screen.screenshot` 에 안 나옴 (상태로 확인: `WM_OT_save_as_mainfile` 브라우저, 폴더 = 프로젝트 `scenes`).

## 남은 것

- File > Open 의 Blender 대화상자 문구 (「Save changes before closing?」) 는 Maya 문구가 아님. 바꾸려면 Blender 의 묻기를 건너뛰는
  킷 Open (자체 파일 브라우저 → 타이머에서 `wm.open_mainfile` exec) 이 필요 — `operators/project.py` 범위, 이 레인 밖.
- `project.browse_from_later` 는 브라우저를 ~2 s (40 × 0.05 s) 기다림: Open 전에 Blender 대화상자에서 2 s 넘게 고민하면 브라우저가
  프로젝트 scenes 폴더로 안 갈 수 있음 (코드로 본 것, GUI 로 재지 않음).
- 버튼 너비가 고르지 않음 (메뉴 레이아웃 제약), Maya 는 같은 너비.
- -b 에서는 불러온 / 저장한 파일도 `is_dirty` 가 참 (측정): 「안 바뀐 장면은 바로」 는 GUI 테스트로만 확인.
