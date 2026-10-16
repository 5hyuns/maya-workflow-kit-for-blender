# HANDOFF

## 현재 작업

- Step 2 (M1-a Maya 키컨피그 기반) 완료 — `docs/steps/step_2.md`. `python tests/run.py` 23/23 PASS, `docs/keymap_mapping.md` 468행 생성.
- 키맵 구조: IC 데이터(설치본) → `keymap/maya_patches.py` 패치 → "Maya" 키컨피그. 새 바인딩은 `_add()` 로 넣어야 가림 검사가 본다. 상태표는 `keymap/mapping.py`.

## 바로 다음 할 일

- **Step 3 — M1-b 홀드/탭 프레임워크** (`docs/PLAN.md` #3).
  - 근거: `research/maya/interaction.md` §0 (두 패턴), §5 스냅, §6 소프트 셀렉트; `research/maya/hotkeys_default.json` 의 press/release 쌍 (SnapToGridPress/Release 등, 대응표 "계획 Step 3" 행).
  - ① 누르는 동안만: X 그리드, C 커브(Blender 대응 결정 필요: edge/vertex snap?), V 점, J 스텝 스냅, B 소프트 셀렉트(+ 반경 드래그) → PRESS/RELEASE 키맵 쌍. IC 의 X(스냅 토글, IC:780)·B(proportional 토글, IC:2517)·Shift+X 스냅 파이 충돌 처리 필요.
  - ② 탭 vs 홀드: A 탭 = Frame All, 홀드 = 마킹메뉴 (메뉴 자체는 Step 10, 이번엔 프레임워크만).
  - 모달·키맵 충돌 설계 → 먼저 `docs/steps/step_3.md` 「계획」. 트랜스폼 모달 중 X/C/V 는 "Transform Modal Map" 에 걸려 축 제한이 되는 점 주의 (`research/blender/industry_compatible_vs_maya.md` §3).
  - 테스트는 PRESS/RELEASE 쌍 존재 + 상태 토글 함수 단위, 감각은 manual_checks.
- Step 5 후보로 미룬 것: Outliner/Graph Ctrl 클릭 해제·Ctrl+Shift 추가 정확 구현, 비-3D 마키 Shift 토글.
