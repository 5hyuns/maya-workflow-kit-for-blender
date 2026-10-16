# HANDOFF

## 현재 작업

- Step 1 (프로젝트 골격) 완료 — `docs/steps/step_1.md`. 하네스 `python tests/run.py` 4/4 PASS.

## 바로 다음 할 일

- **Step 2 — M1-a Maya 키컨피그 생성기** (`docs/PLAN.md` #2).
  - 입력: `research/blender/keymap_industry_compatible.json`, `$S\presets\keyconfig\keymap_data\industry_compatible_data.py` (`generate_keymaps`, IC:3862-3889), `research/blender/industry_compatible_vs_maya.md` §2 갭 표, `research/maya/hotkeys_default.json`.
  - 위치: `src/maya_kit/keymap/` (생성기 + 패치 테이블, 패치마다 근거 file:line 주석).
  - 키맵 충돌이 많으므로 먼저 `docs/steps/step_2.md` 「계획」 작성 후 구현.
  - 헤드리스 주의: `-b` 에서는 기본 키컨피그가 비어 있음 → 데이터에서 직접 생성해 검증.
  - 테스트: 생성된 키컨피그에서 바인딩을 이름으로 조회하는 `tests/test_keymap_*.py`, 그리고 비활성화 시 키컨피그 제거가 `test_enable_disable` 를 계속 통과해야 함.
