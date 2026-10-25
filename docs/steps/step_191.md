# Step 191 — 0.4.1 출시 준비

사용자 결정 10-25: 0.4.1 = 감사 13 묶음 (steps 173–190) 끝 (#82 옵션 상자 클릭 수정 183 포함).

## 계획

1. manifest 0.4.1; CHANGELOG [0.4.1] (git log v0.4.0..HEAD 22 커밋, 닫힌 이슈) + 짧은 스토어 문구 `release_notes_0.4.1.md`.
2. build, `extension validate`, release_check 4.5.4 / 5.2.2, 헤드리스 전체, GUI 전체 묶음 한 번 (`ALLSET_GUI_FULL=1`, 포그라운드).
3. 빨간 것 먼저 고침 (실패 파일만 `-k` 재실행, 원인은 git bisect).
4. master push, 태그 v0.4.1, `gh release create v0.4.1 --draft` (zip 2 개 + 문구), 바탕화면 업로드 폴더에 복사.

순서: 테스트 · 출시는 같은 zip · Blender 샌드박스를 쓰므로 순차. 헤드리스 전체는 GUI 와 다른 샌드박스 (`guifull`) 로 동시에 (Blender 2 개).

## 한 것

- `blender_manifest.toml` 0.4.1, CHANGELOG [0.4.1] (Added / Changed / Fixed), `docs/distribution/release_notes_0.4.1.md`.
- GUI 전체 묶음 (177 파일, 2 격리 GUI_SKIP) 은 포그라운드 10 분 한도 때문에 12 파일씩 15 덩어리 (`-k`, delegated, step 172 와
  같음). 실패 15 검사 / 9 파일 → 원인:
  - **킷 버그 1**: `allset.dolly_2d` (UV / Image Editor Alt+RMB 줌) — step 177 이 `modal()` 에서 `self._button` 을 읽게 했는데
    `invoke` 가 안 넣음 → 줌 안 됨. git bisect (v0.4.0 좋음 → d462e16 step 177 처음 나쁨). invoke 에서 설정.
  - **킷 버그 2 (step 184 의 빈틈)**: 메뉴를 위로 그린 (목록이 창 아래를 넘는) RMB 마킹 메뉴에서, 그려지기 전의 빠른 flick 이 보이지
    않는 올린 상자 기준으로 읽혀 엉뚱한 항목 (또는 없음). 이제 그려지기 전 (show delay 전) 표시는 누른 점에서 방향으로 (Maya 의
    mark 규칙; 그려진 뒤는 step 184 그대로) — `marking/engine.Session.move`, headless `test_lifted_menu_marks_read_from_the_press`.
  - **옛 기대 (킷은 옳음)**: step 184 (aa66c56, bisect) 이후 화면 가운데에서 누른 객체 메뉴도 위로 그려짐 → `gui_step8` /
    `gui_step9_hotbox` / `gui_step129_marking_bounds` / `gui_step91_view_chrome` 이 그려진 상자 / 행을 겨냥하도록; step 186 (bff9a3b,
    bisect) 이 키 눈금을 칸 왼쪽 끝에 그림 → `gui_step129_time` 은 `time_slider.key_x` 위치를 봄; `gui_manual_sweep` 의 M70-3 (step
    175: G = `allset.repeat_last`), M75-4 (step 189: Construction History 실제 토글).
  - `gui_step143_user` #82 박스 클릭 1 건: 묶음 안에서만 실패, 단독 재실행 통과 (0.4.0 때와 같은 불안정, 킷 변경 없음).

## 검증

- `python tools/build.py` → `dist/maya-workflow-kit-0.4.1.zip` + `-legacy.zip`; `blender --command extension validate` Success.
- release_check (`--no-shots`): Blender 4.5.4 **14 PASS**, 5.2.2 **14 PASS**, FAIL 0.
- 헤드리스 전체 (수정 전) **1730 / 1730**; 수정 뒤 **1731 / 1731**.
- GUI 전체 (177 파일): 1933 통과 · 15 실패 → 고친 뒤 실패 파일 + 마킹 관련 파일 다시: 9 파일 (sweep 포함) 357 / 357, 마킹 10 파일
  85 / 85, step8 / step129_bounds 24 / 24, step9 16 / 16.

## 남은 것

- #89 (Quad Draw 남은 것) → milestone 0.5.0 그대로.
- Hermes: 초안 릴리스 v0.4.1 확인 후 publish, 스토어에 0.4.1 zip 업로드 (`C:/Users/ohnsk/Desktop/MayaWorkflowKit_upload/`).
