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
