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

진행 메모 (delegated): 순서 — 헤드리스 (백그라운드 셸) 와 레인 A · B (포그라운드 에이전트 2 개) 동시, dogfood 는 레인 B 의 Blender 가
끝난 뒤 (Blender 2 개 상한). 레인 결과는 WIP 커밋 71622ad.

## 한 일 · 검증

- 헤드리스 전체 4.5: **1844 / 1844** (226 파일, HEAD 0d75f44, sandbox h201, zip = src 바이트 동일 245 파일 — 레인 B 확인).
- dogfood (`tools/dogfood.py`, 깨끗한 설정에 zip 설치 → Maya 모드 → 스크립트 세션): **48 / 48** (step 192 47 / 48 → RMB flick 회귀 고쳐짐,
  step 193), 콘솔 오류 / 경고 0. 스크린샷 12 장 중 7 장 직접 봄.
- 레인 A (`step_201_remaining.md`): 대응표 **30 / 1 / 0 / 2 (91 %)** 그대로 (네 감사째). step 192 목록 중 16 개 끝, ~45 개 남음, 새
  blindspot NB7–NB11. manual_checks 726 / 107 → **731 / 107** (옛 문구 9 곳 고침, 「Step 201」 5 개).
- 레인 B (`step_201_quant.md`): 메뉴 750 → **762 / 1318 (57.8 %)**, 편집기 메뉴 578 → **600 / 914**, 옵션 상자 Maya 창 120 → **164 경로**
  (redo 127 → 104, generic 34 → 19, dead 193 → 187), 셸프 160 / 단축키 210 / 마킹 371 그대로. look_compare kit-drawn 1.0 **12 / 12**, 1.25
  **11 / 12** (time_slider_current ΔE 13.8 — 회귀).
- GitHub: backlog 단계마다 이슈 #109–#116 (라벨 roadmap + maya-parity + found-by-audit, 마일스톤 0.5.0), #108 본문 숫자표 · Planned next 갱신.

## 메인 GUI 관찰 (dogfood 스크린샷 vs Maya 2022) — 차이만

| # | 차이 | 근거 |
|---|---|---|
| G1 | Channel Box 메뉴 바 첫 메뉴가 "Chann..." 로 잘림 (Maya: Channels Edit Object Show 한 줄) | `01`, `05`, `09` |
| G2 | 컴포넌트 모드에서 kit Outliner 왼쪽에 Blender 모드 열 (pCube1 모드 아이콘, pCube2 점) — Maya Outliner 에 없음 | `06_shift_rmb_vertex_tools.png` |
| G3 | RMB 목록이 링 서쪽 한 열 (Maya: 링 아래) 로 Outliner 가장자리 · Time Slider 를 덮음 — step 193 결정 (창 높이 900 에선 아래에 안 들어감), 남은 차이 | `05_rmb_marking_menu.png` |
| G4 | AE 를 열어도 dock 폭이 Channel Box 폭 그대로라 AE 메뉴 바가 3 줄, Hide 가 따로 한 줄, 아래 Select / Load Attributes 잘림 — event-simulated 세션은 `ALLSET_FIT_WARP` 가 꺼져 폭 맞춤이 안 돎 (실사용과 다를 수 있음, 측정 안 함) | `11_attribute_editor.png` |
| G5 | dogfood 샷 12 (Insert pivot) 는 side 뷰에서 큐브가 화면 밖이라 pivot 편집이 안 보임 — 도구 빚 (dogfood 스크립트), 킷 차이 아님 | `12_insert_pivot.png` |

G1 · G2 와 레인 결과 NB7–NB10, 1.25 Time Slider 회귀는 backlog #1 「Audit 15 fix batch」 (#109) 로.

## 남은 것

- 남은 차이 전체 목록: `step_201_remaining.md` §3 (~45 개) / §8, `step_201_quant.md` §1b · §5.
- backlog 밖 다음 후보: Maya Preferences 창, 렌더 기본 (lambert1 1.25 배), FX 메뉴 (19 %, 세 감사째), Surfaces 37 %, Script Editor History 0 / 13.
- G4 (AE dock 폭) 는 `ALLSET_FIT_WARP=1` 로 GUI 에서 재확인 필요 — #109 에서 같이 봄.
- 정리 (사용자 확인 필요, 손대지 않음): `.claude/worktrees` 아래 에이전트 worktree 63 개 + `C:/Repos/bmk-hotfix`.
- 이슈 #103–#107 은 로컬 커밋으로 고쳐졌고 push 해야 닫힘. 사용자 할 일: 스토어에 0.4.1 zip 업로드.
