# HANDOFF

## 현재 작업

- Step 3 (M1-b 홀드/탭, D/Insert 피벗, pick-walk) 완료 — `docs/steps/step_3.md`. 헤드리스 39/39, GUI 이벤트 테스트 17/17 (`python tests/gui/run.py`).
- 키 동작 구조: 홀드 = `operators/hold.py` (PRESS → 모달, OS 키 상태 폴백), 탭/홀드 = `operators/taphold.py` (`TapHoldBinding` 서브클래스 등록 → `maya_kit.tap_hold(binding=...)`). 키맵 패치는 `keymap/maya_patches.py` `_add(..., shadows=...)`.

## 바로 다음 할 일

- **Step 4 — M1-c 카메라·뷰 조작감** (`docs/PLAN.md` #4).
  - 근거: `research/maya/interaction.md` §1 (카메라: COI 텀블, 줌 방향, ortho), §8 (프레이밍), `research/maya/defaults.json` (텀블 관련 기본값), `research/blender/industry_compatible_vs_maya.md` §1–2 (Alt+마우스 IC 일치, use_rotate_around_active), `research/blender/preferences_rna.json` (inputs.*).
  - Alt+LMB/MMB/RMB 세부: orbit around selection 끔(COI 유지), 줌 방향·zoom to mouse 끔, ortho 뷰 텀블 잠금, F/A/Shift+F/Shift+A 프레이밍(자식 제외 여부, 모든 뷰), `[` `]` 뷰 변경 언두 스택(Alt+Z/Alt+Y 포함).
  - 환경설정 값 변경은 사용자 설정을 바꾸므로 애드온 활성화 시 저장·비활성화 시 복원 (test_enable_disable 스냅샷에 prefs 값 추가 고려).
  - A 는 이제 `tap_hold(select_all)` — Frame All 변경 시 `taphold.SelectAllBinding.tap` 을 고칠 것.
  - 모달·뷰 행렬 설계 → 먼저 `docs/steps/step_4.md` 「계획」. GUI 검증은 `tests/gui/` 에 `gui_step4_*.py` 추가.
