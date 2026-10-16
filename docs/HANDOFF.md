# HANDOFF

## 현재 작업

- Step 4 (M1-c 카메라·뷰, 1/2/3, F7–F11, 환경설정 프리셋) 완료 — `docs/steps/step_4.md`. 헤드리스 55/55, GUI 36/36.
- `docs/PLAN.md` 재번호: 5 레이아웃(App Template) / 6 Channel Box / 7 상단 UI(Status Line·커맨드 라인·타임/레인지) / 8 남은 M1 키·계층 / 9 마킹메뉴 / 10 핫박스 / 11 개념 / 12 Outliner·AE / 13 셸프 / 14 릴리스.
- 구조 요약: 키맵 `keymap/maya_patches.py`, 홀드 `operators/hold.py`, 탭/홀드 `operators/taphold.py`, 뷰 `operators/view.py`, 환경설정 프리셋 `prefs_preset.py`.

## 바로 다음 할 일

- **Step 5 — M2-a 레이아웃 App Template** (`docs/PLAN.md` #5).
  - 근거: `research/maya/ui_layout.md` §2 (General 레이아웃 ASCII), §4 요소별, `research/maya/workspaces.json`, `research/blender/ui_architecture.md` §1–2 (app template 경로 `bl_app_templates_user`, `AppOverrideState`, startup.blend 권장), decisions 1 (cm 표시) · 3 (템플릿을 익스텐션에 넣고 설치/제거 버튼).
  - 좌 Outliner, 중앙 Persp 뷰포트, 우측 Channel Box/Layer Editor·AE 자리(패널은 Step 6 — 이번엔 자리/사이드바), 아래 타임/레인지 슬라이더 자리, 테마(Maya 회색) 프리셋, 단위 옵션.
  - startup.blend 는 헤드리스 스크립트로 생성(재현 가능하게 `tools/` 에 생성기) → `src/maya_kit/app_template/` 에 저장. 설치/제거 오퍼레이터는 사용자 scripts 경로에 쓰므로 manifest `[permissions] files` 필요.
  - 검증: 헤드리스(설치/제거 파일, 템플릿 로드 후 영역 구성), GUI 스크린샷(레이아웃이 Maya General 과 닮았는지 직접 보기).
