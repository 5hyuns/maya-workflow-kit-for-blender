# Step 201 — 재점검 15차 (드라이버 「AUDIT 14」 / 사용자 지시의 「재점검 14차」)

## 계획

사용자 지시 (2026-10-25): 정한 일 (backlog_193, steps 193–200) 이 모두 끝남 — 헤드리스 전체 + 깨끗한 설정 설치 dogfood + GUI 를 Maya
사용자 눈으로, 「남은 것」·manual_checks 정리 (blindspot 포함), PLAN 절, HANDOFF, backlog 5–8 개 + 단계마다 GitHub 이슈, #108 표 갱신.
기준: 「기본 Maya 에 Blender 기능이 붙은 모습」, 차이만. PLAN 의 「재점검 14차」 는 이미 step 192 이므로 이번은 **15차** 로 번호 매김
(delegated, steps 163 / 173 / 182 / 192 와 같은 방식).

레인 (step 192 와 같음; 포그라운드 에이전트 2 개 동시, Blender 최대 2 개):
- **A — 문서 정리** (에이전트, Blender 없음): README 대응표, 193–200 「남은 것」 + `step_192_remaining.md` 목록 대조, GitHub 이슈,
  blindspot, manual_checks → `docs/steps/step_201_remaining.md`, `docs/manual_checks.md`.
- **B — 수치** (에이전트, Blender 1 개, sandbox `q201`): menu_count / 옵션 상자 / 마킹 메뉴 / 셸프 / 단축키 / look_compare →
  `docs/steps/step_201_quant.md`.
- **메인**: 빌드 한 번 → 헤드리스 전체 (sandbox `h201`, `--no-build`, 셸 백그라운드 명령 — 서브에이전트 아님) → 레인 뒤 dogfood
  (Blender 2 개 상한 때문에 헤드리스 · B 가 끝난 뒤: 순서 필요) → 스크린샷 직접 보기 → 합치기, PLAN · HANDOFF · backlog · 이슈, 커밋.
  GUI 전체 묶음은 돌리지 않는다: src 를 고치지 않는 감사 (사용자 10-23 규칙: 전체 GUI 는 출시 준비 때).
