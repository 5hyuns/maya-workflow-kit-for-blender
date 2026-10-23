# Step 143 — 0.3.0 출시 준비

사용자 결정 10-23: 0.3.0 버전 고정 = 140 (옵션 창) · 141 (작은 묶음) · 142 (UI 모습) 뒤. #30 #31 #34 는 0.4.0.

## 계획

1. 출시 전 새 사용자 보고 처리 (포그라운드 레인 2 개): #79 (5.2.3 에서 Maya 모드 안 켜짐 — 출시 막는 것),
   #80 #82 #84 (작고 안전하면 고침, 아니면 0.4.0). 상세 `step_143_compat79.md`, `step_143_user.md`.
2. manifest 0.3.0, CHANGELOG [0.3.0], 짧은 스토어 문구 `docs/distribution/release_notes_0.3.0.md`.
3. build, `extension validate`, release_check 4.5.4 / 5.2.2, 헤드리스 전체, GUI 전체 묶음 (한 번).
4. v0.2.1 뒤 고친 이슈 닫기, 0.3.0 의 나머지는 0.4.0 으로.
5. v0.3.0 태그, push, `gh release create v0.3.0 --draft` (zip 2 개 + 문구), 바탕화면 업로드 폴더에 zip · 문구 복사.

## 한 일

- #79: 다른 애드온의 Render 탭 패널 모듈이 `classes` 를 하위 모듈로 두면 `render_settings.registration_key` 가 실패해 Maya 모드가
  반만 켜졌다 (5.2.3 자체 문제 아님 — 공식 5.2.3 빌드로 확인). 튜플 / 리스트만 쓰고 나머지는 Blender 패널 뒤로 (4.5 순서 그대로).
- #84: Blender 5.1 / 5.2 의 `mesh.loop_select` 에 `ring` 인자가 없음 → `loop_pick.loop_select_args()`.
- #80: Extrude 뒤 Q / W / E / R 가 extrude 기록을 닫아 Move 매니퓰레이터가 돌아옴; F12 가 UV sync 를 켠 채 두던 순서 고침.
- #82: 재현 — 옵션 상자는 한 버튼이라 클릭 = 명령, 길게 누름 → Option Box 만 창을 연다. 0.4.0 으로 (원인 · 제안을 이슈에 댓글).
- 버전 0.3.0, CHANGELOG, release_notes_0.3.0.md.
- 이슈: #70 #68 #16 (step 139 aef175f) 닫음; #81 #82 #83 #85 #86 #87 → 0.4.0; 0.3.0 열린 이슈 0.

## 검증

- `python tools/build.py` → `dist/maya-workflow-kit-0.3.0.zip` + `-legacy.zip`; `blender --command extension validate` Success.
- release_check: Blender 4.5.4 **22 PASS**, 5.2.2 **22 PASS** (exit 0; 설치 · Maya 모드 · 끄기 · Remove 가 사용자 설정을 안 바꿈).
- #79 레인: `-k step143,step105,step118,enable_disable` 4.5.4 / 5.2.2 / 5.2.3 각 22 / 22 (공식 5.2.3 빌드 sha256 확인).
- 헤드리스 전체: **1249 / 1249** (153 파일).
- GUI 전체 묶음 (한 번, 132 파일): **1500 통과, 1 실패, 2 격리 (GUI_SKIP)**. 실패 = `gui_step55_pose` — step 142 의 좁은 dock 에서
  값 칸을 찾는 세로 훑기 선 (폭의 0.8) 이 칸 오른쪽 끝에 걸려 클릭이 빗나감 (테스트 쪽). 0.7 로 고친 뒤 혼자 두 번 15 / 15.

## 남은 것

- 0.4.0: #30 #31 #34 (Maya 모델링 도구 · Deform), #81 (Maya UI 초기화), #82 (옵션 상자 열기), #83 #85 #86 #87 (step 142 후속).
- Hermes: 초안 릴리스 v0.3.0 확인 후 publish, 스토어에 0.3.0 zip 업로드 (`C:/Users/ohnsk/Desktop/MayaWorkflowKit_upload/`).
