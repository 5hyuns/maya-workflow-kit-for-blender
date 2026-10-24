# Step 172 — 0.4.0 출시 준비

사용자 결정 10-25: 재점검 묶음 하나 = 버전 하나. 0.4.0 = 감사 10 / 11 묶음 (steps 144–171) 끝.

## 계획

1. manifest 0.4.0; CHANGELOG [0.4.0] (git log v0.3.0..HEAD, 닫힌 이슈) + 짧은 스토어 문구 `docs/distribution/release_notes_0.4.0.md`.
2. build, `extension validate`, release_check 4.5.4 / 5.2.2, 헤드리스 전체, GUI 전체 묶음 (한 번, `ALLSET_GUI_FULL=1`).
3. master push → `Fixes #N` 커밋이 #81–#101 을 닫음; #89 → 새 milestone 0.5.0.
4. 태그 v0.4.0, push, `gh release create v0.4.0 --draft` (zip 2 개 + 문구), 바탕화면 업로드 폴더에 복사.

순서: 테스트 · 출시는 같은 zip · 같은 Blender 샌드박스를 쓰므로 순차; release_check 가 도는 동안 CHANGELOG / 문구를 썼다.

## 한 것

- `blender_manifest.toml` version 0.4.0, CHANGELOG [0.4.0] (Added / Changed / Fixed, #30 #31 #34 #81–#101), 스토어 문구
  `release_notes_0.4.0.md` (단계 번호 · 내부 경로 없음).
- GUI 전체 묶음의 실패 4 건:
  - `gui_step52_hotbox_rmb` 2 건, `gui_step91_view_chrome` 1 건 = step 161 의 RMB 목록 규칙 (밑에 자리가 없으면 링 옆 한 열)
    이전 가정 (항상 링 밑). 킷이 아니라 테스트를 새 규칙에 맞춤: step52 = "밑 또는 옆, 한 열", step91 = HUD 오른쪽 300 px 에서
    눌러 왼쪽 열이 HUD 위를 지나게 (의도 = 마킹 메뉴가 HUD 위에도 그려짐, 그대로).
  - `gui_step143_user` #82 박스 클릭 1 건 = 묶음 안에서만 한 번 실패, 단독 재실행 두 번 통과 (불안정, 킷 변경 없음).
- GUI 전체 묶음은 포그라운드 10 분 한도를 넘어 (약 80 분) 12 파일씩 13 덩어리로 나눠 포그라운드로 돌렸다 (delegated).

## 검증

- `python tools/build.py` → `dist/maya-workflow-kit-0.4.0.zip` + `-legacy.zip`; `blender --command extension validate` Success.
- release_check (`--no-shots`): Blender 4.5.4 **14 PASS**, 5.2.2 **14 PASS**, FAIL 0.
- 헤드리스 전체 **1600 / 1600** (192 파일).
- GUI 전체 (165 파일, 2 격리 GUI_SKIP): 검사 1827 개 중 처음 1823 통과 · 4 실패 → 위 수정 뒤 세 파일 함께 34 / 34.

## 남은 것

- #89 (Quad Draw 남은 것) → milestone 0.5.0.
- Hermes: 초안 릴리스 v0.4.0 확인 후 publish, 스토어에 0.4.0 zip 업로드 (`C:/Users/ohnsk/Desktop/MayaWorkflowKit_upload/`).
