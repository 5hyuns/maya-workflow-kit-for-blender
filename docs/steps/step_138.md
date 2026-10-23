# Step 138 — Scenes and files the Maya way (#57 #63 #64 #69)

## 계획

backlog 5 (`step_133_ui.md` #6, `step_133_remaining.md` B1 B3, `step_133_work.md` I1–I4).

### 결정 (delegated)

- **저장 묻기 (#57)**: Ctrl+N / File > New Scene 에서 바뀐 장면이면 Maya 의 「Save changes to <장면>?」 Save / Don't Save / Cancel. Save =
  경로가 있으면 저장 후 새 장면, 없으면 Save As 브라우저 → 저장이 끝나면 새 장면 (취소면 아무것도 안 함). Don't Save = 새 장면, Cancel =
  그대로. File > Open 이 Blender 의 묻기를 이미 하는지 GUI 로 확인하고 Maya 문구와 다르면 같은 대화상자로.
- **Open 때 Maya 레이아웃 (#63)**: Maya 는 UI 가 장면 파일에서 오지 않는다 (research/maya/ui_layout.md:15-77). Maya 모드에서 파일을 열면
  load_post (→ 타이머) 에서 `switch.enter_layout` — add-on 설정 「Keep Maya layout when opening files」 (Maya 모드 기본 켬). 파일에 이미
  Maya 레이아웃 워크스페이스가 있으면 그것으로 (중복 추가 없음).
- **도구 설정 전역 (#64)**: Maya 도구 설정은 New / Open 을 건너 유지 (research/maya/interaction.md:31, :159). step 93 의 선택 마스크처럼
  load_pre 에서 읽고 load_post 에서 되돌림: Move / Rotate / Scale 축 (orientation slots), step snap (`allset.step_snap` 상태), 스냅 토글,
  soft select (켜짐 · 반경 · falloff), 대칭 (`Scene.allset_symmetry`), 피벗 / Preserve UVs · Children 등 킷이 Maya 도구 설정으로 쓰는 것.
- **파일 왕복 (#69)**: 목표 = mayapy 로 잰 왕복에서 pCube1 (1, 2, 3), rotate Y 28.6 이 양쪽으로 그대로 (FBX, OBJ, Alembic, USD), 이름
  (pCube1 / pCubeShape1), 단위 · 축이 변환 채널에 남지 않음 (Rotate X ±90, Scale 100 없음). `operators/file_io.py` `export_args` /
  `import_args` + 필요하면 내보내기 · 가져오기 뒤처리 (축 보정을 메시 · 루트가 아니라 채널에 안 남게). 측정 방법 = research/maya/re/file_io.md.

### 레인 (병렬, worktree, 포그라운드)

| 레인 | 이슈 | 파일 |
|---|---|---|
| PROMPT | #57 | `first_start.py` (`ALLSET_OT_new_maya_scene`), 필요하면 새 `ui/save_prompt.py`, `tests/test_step138_prompt.py`, `tests/gui/gui_step138_prompt.py` |
| CARRY | #63 #64 | 새 `ui/scene_carry.py` (+ `ui/__init__` 등록), `preferences.py` (설정 하나), `tests/test_step138_carry.py`, `tests/gui/gui_step138_open.py` |
| FILEIO | #69 | `operators/file_io.py`, `research/maya/re/file_io.md` (추가), `research/scripts/` mayapy 스크립트, `tests/test_step138_file_io.py` |

메인: 병합, 헤드리스 전체, GUI 전체 한 번, 커밋.

## 한 것

레인 3 개 (worktree, 포그라운드 동시). 레인 문서: `step_138_prompt.md`, `step_138_carry.md`, `step_138_file_io.md`.

- **PROMPT** (#57): `ui/save_prompt.ask` — Maya 2022 문구 그대로 (saveChanges.mel:43-89): 이름 없는 장면 「Warning: Scene Not Saved / Save
  changes to untitled scene?」, 저장된 장면 「Save Changes / Save changes to <경로>?」, Save / Don't Save / Cancel. Save = 경로 있으면 저장 후 새
  장면, 없으면 킷 Save As (프로젝트 scenes) → `save_post` 뒤에만 새 장면; 브라우저 취소 = 그대로. Ctrl+N, File > New Scene, Status Line,
  New Scene 옵션 창이 모두 거친다. 대화상자는 `wm.popup_menu` (`invoke_popup` 은 버튼을 눌러도 닫히지 않음, 측정; delegated).
  File > Open / Ctrl+O 는 Blender 가 이미 Save / Don't Save / Cancel 을 묻는다 (문구는 Blender 의 「Save changes before closing?」, 남은 것).
- **CARRY** (#63 #64): `ui/scene_carry.py` — load_pre / load_post 로 Maya 도구 설정을 모든 로드 (Open, 최근 파일, Revert, New Scene, Blender
  File > New) 를 건너 유지: Move / Rotate / Scale 축 (orientation slot 0–3), 스냅 (step snap · 요소 · 각도), 피벗 점, Preserve UVs / Children,
  soft select falloff · connected · projected · 반경 (Maya 단위로), 대칭 / 메시 도구 / UV / Auto Key 킷 속성, 피벗 메뉴 옵션. Maya 모드에서 경로가
  있는 파일을 열면 타이머로 Maya 레이아웃 (설정 「Keep Maya Layout When Opening Files」 기본 켬; 파일에 있는 Maya 워크스페이스 먼저).
  Maya 모드를 켠 직후 Blender 시작 장면에서는 옮기지 않음 (Blender 기본값이 템플릿의 Maya 기본값을 덮지 않게; delegated).
- **FILEIO** (#69): 프리셋 + 뒤처리 (`operators/file_io.py`): FBX `bake_space_transform` (+ 애니메이션: NLA 끔), OBJ `g` 줄 · `use_split_groups`,
  Alembic 은 루트 배율 대신 메시에 배율, USD 는 pxr 로 Y-up · metersPerUnit 0.01 · root / env_light 없음, 가져오기는 축 변환을 메시에 굽고
  캐시 변환은 키로, 이름은 Maya 식 (pCube2, pCubeShape1). mayapy 왕복 표 (전 / 후) = `step_138_file_io.md`, 방법 `research/maya/re/file_io.md` §4.
- **메인**: 병합 (`ui/__init__.py` 등록 목록 충돌 손으로), 손 확인 항목, CLAUDE.md 메모.

## 검증

- 헤드리스 전체 (병합 뒤): **1124 passed, 0 failed (140 files)** (FILEIO 레인의 마지막 커밋 3642021 도 여기서 처음 검증).
  레인별: PROMPT 45/45, CARRY 157/157, FILEIO 45/45 (`-k` 묶음).
- GUI 전체 (커밋 전 한 번): **1432 passed, 0 failed (123 files)** — `gui_step138_prompt` (Cancel / Don't Save / Save, 저장 경로 있음 · 없음),
  `gui_step138_open` (Maya 모드에서 Open = Maya 레이아웃, 설정 끔 = 파일 레이아웃), step 132 New Scene (D 로 Don't Save) 포함.
- mayapy 왕복 (`research/scripts/file_io_138_mayapy.py`, 표는 `step_138_file_io.md`): kit → Maya 4 형식 모두 pCube1 t (1, 2, 3) r (0, 28.6, 0)
  s 1 (OBJ 는 Maya → Maya 처럼 점이 월드 좌표, t 0), USD 의 root / env_light 없음, FBX · Alembic 애니메이션 키 유지; Maya → kit 4 형식 모두
  Channel Box (1, −3, 2) / r Z 28.6 / s 1 = Maya 값 (Z-up 변환), 이름 pCube1 / pCubeShape1. 부모 · 자식 (group1 + pCube1) 도 FBX / ABC / USD 같음.
- 그림 직접 확인: `gui_step138_prompt_untitled.png` (Maya 제목 · 문구 · 세 버튼), `gui_step138_open_maya.png` (Blender 레이아웃 파일이 Maya
  레이아웃으로 열림, Outliner 에 파일의 Camera / Cube / Light).

## 남은 것

- Open 의 묻기는 Blender 문구 (「Save changes before closing?」) — Maya 문구로 하려면 킷 Open 브라우저 + 타이머 열기 (`operators/project.py`).
  `project.browse_from_later` 가 Open 브라우저를 2 초만 기다려 Blender 묻기에서 오래 머물면 프로젝트 폴더로 안 갈 수 있음 (코드로 본 것, 미측정).
- 대화상자 버튼 폭이 같지 않음 (Maya 는 같음). 도구 설정은 세션 사이에는 유지 안 됨 (Maya 는 prefs). 명령줄로 연 첫 파일은 옮길 값이 없음.
  두 번째 창부터는 파일 레이아웃. m 파일을 Maya 레이아웃으로 열면 물체가 작게 보임 (프레이밍 필요).
- 파일: USD 재질의 셰이더 노드 이름 `Principled_BSDF`, FBX 빈 오브젝트가 Maya 에서 locator, USD / Alembic 의 카메라 · 조명 · 커브 · 스켈레톤 ·
  변형 메시는 미측정, FBX 는 m 장면에서 단위를 그대로 (step 102 결정).
