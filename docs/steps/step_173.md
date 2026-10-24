# Step 173 — 재점검 12차 (사용자 지시의 「재점검 11차」)

## 계획

사용자 지시 (2026-10-25): 정한 일 (backlog_164, steps 164–171, 0.4.0 출시 step 172) 이 모두 끝남 — 헤드리스 전체 + 깨끗한 설정 설치
dogfood + GUI 를 Maya 사용자 눈으로, 「남은 것」·manual_checks 정리 (blindspot 포함), PLAN 절, HANDOFF, backlog 5–8 개. 기준: 「기본 Maya
에 Blender 기능이 붙은 모습」, 차이만. 「재점검 11차」 는 step 163 이므로 이번은 12차로 번호 매김 (delegated, steps 154 / 163 과 같은 방식).

레인 (step 163 과 같음; 에이전트 2 개 동시, Blender 최대 2 개):
- **A — 문서 정리** (에이전트, Blender 없음): README 대응표, 164–172 「남은 것」 + step 163 목록 대조, GitHub 이슈, blindspot,
  manual_checks → `docs/steps/step_173_remaining.md`, `docs/manual_checks.md`.
- **B — 수치** (에이전트, Blender 1 개, sandbox `q173`): menu_count / 옵션 상자 / 마킹 메뉴 / 셸프 / 단축키 / look_compare →
  `docs/steps/step_173_quant.md`.
- **메인**: 헤드리스 전체 (sandbox `h173`) → 헤드리스 뒤 dogfood (Blender 2 개 상한) → 스크린샷 직접 보기 → 합치기, PLAN · HANDOFF ·
  backlog, 커밋.

진행 기록: 두 레인 에이전트가 포그라운드가 아닌 기본값 (백그라운드) 으로 떴다 (`run_in_background: false` 빠뜨림 — Hermes 규칙 위반).
대기는 ScheduleWakeup 없이 완료 알림으로만 하고, 그동안 메인 레인 (헤드리스 · dogfood) 을 진행했다.

## 한 일 · 검증

- 헤드리스 전체 4.5: **1600 / 1600** (192 파일, HEAD c8d006c, sandbox h173).
- dogfood (`tools/dogfood.py`, 깨끗한 설정에 zip 설치 → Maya 모드 → 스크립트 세션): **48 / 48**, 콘솔 오류 / 경고 0, 스크린샷 12 장
  `tmp/dogfood/shots/` 직접 봄.
- 레인 A (`step_173_remaining.md`): 대응표 **30 / 1 / 0 / 2 (91 %)** — 3D View 밖 선택 수정키 Partial → Done (step 170). 열린 이슈 #89
  하나 (0.5.0). 164–171 이 끝낸 것 지움. 새 blindspot: **G (Repeat Last) 가 메뉴 · 셸프 · 마킹 명령을 반복 안 함** (`run_action` 은 등록
  안 됨, step 147), **패널 메뉴 / 패널 툴바 회색 36 이 셈 · notice · 쌍둥이 검사 밖** (상대가 있는 것 포함: Camera AE, Center View, Tumble /
  Track / Dolly Tool), Animation Layers 없음, 폴리곤 기본 도형 7 개, Transform Display. manual_checks 653 / 86 → 663 / 96 (GUI 테스트가
  검사하는 부분 10 개 쪼개 체크, 낡은 문구 3).
- 레인 B (`step_173_quant.md`): 메뉴 649 → **699 / 1318 (53.0 %)** (Modify 41 → 63 %, Deform 41 → 65 %, Visualize 20 → 80 %), 편집기 메뉴
  545 → **560 / 914**, 옵션 상자 Maya 창 85 → **104 경로** (dead 225 → 214), 셸프 155 / 203, 마킹 368 / 65, 단축키 209 (그대로).
  look_compare 결과표는 step 163 과 바이트까지 같음 (뷰포트 11 / 12 — 선택 면 ΔE 40.5 다섯 감사째, 킷 픽셀 6 / 6, rects 5 / 12).
  다섯 감사째 그대로인 메뉴: Control 7 %, nConstraint 0 %, nCache 15 %, Fields/Solvers 37 %, Effects 18 %, Texturing 12 %; Surfaces 20 % ·
  Mesh Display 38 % 네 감사째.

## 메인 GUI 관찰 (dogfood 스크린샷 vs Maya 2022) — 차이만

| # | 차이 | 근거 |
|---|---|---|
| G1 | pCube1 의 Channel Box `INPUTS polyCube1` 이 Ctrl+D → Ctrl+G → Ctrl+Z → P 세션 뒤 사라짐 (처음 `03_move_tool.png` 에는 있음, `05` · `08` 에는 없음). 헤드리스 탐침 (같은 순서, `allset.duplicate` / `group` / `ed.undo` / `parent`) 에서는 기록이 남음 → GUI 경로 (메모리 undo 또는 CB 행 캐시) 의심, 미확인 | `03` vs `05_rmb_marking_menu.png` |
| G2 | Undo 뒤에도 Command Line 결과 칸이 `Result: group1` (Maya 는 Undo 결과를 보여 줌) | `05`, `08` |
| G3 | 네 뷰 칸 이름 "top -Z" / "front +Y" (Maya "top -Y" / "front -Z") — step 163 G3 그대로 | `08_four_views.png` |
| G4 | AE 탭 · 메뉴가 잘림 ("pCub…", "initial…", "Sele…") — dock 이 AE 폭으로 넓어지지 않음 (event simulation 에서는 fit 이 꺼짐, `ALLSET_FIT_WARP`; 실제 세션 확인 필요) | `11_attribute_editor.png` |
| G5 | W 뒤 F9 → Select Tool (Maya 는 Move 유지) — 레인 B #1, 코드 확인 (`operators/display.py:253-260` 은 모드만 바꿈) | 레인 B |

## 차이 우선순위 (점수 = 심각도 × 빈도)

| 점수 | 차이 | 출처 |
|---|---|---|
| 9 | 컴포넌트 모드에 들어가면 도구가 Select 로 (Maya: Move / Rotate / Scale 유지) | B #1, 메인 G5 |
| 9 | G 가 메뉴 · 셸프 · 마킹 명령을 반복 안 함 | A BS1 |
| 6 | 선택 면이 거의 불투명 주황 (ΔE 40.5, 다섯 감사째); CB INPUTS 사라짐 · 결과 칸 Undo (G1 G2) | B #4, 메인 |
| 6 | 패널 메뉴 / 툴바 회색 36 이 감사 밖, 상대 있는데 회색 | A BS2 BS6 |
| 6 | UV Editor 69 % (Map / Straighten Border, Stack Similar, Match Grid ...) | A R3, B #6 |
| 6 | Light Links 8 회색 — Blender 4.5 `Object.light_linking` 있음 | B #7 |
| 6 | Animation Layers 없음 (Layer Editor Anim 탭 글만) | A BS3 |
| 6 | Surfaces 8 / 41 다섯 감사째 | A R7 |
| 5 | 옵션 상자 ❒ 클릭 = 명령 (#82, C 벽 — hold / Shift / Ctrl) | B #2 |
| 4 | RMB 목록 링 옆 (Maya: 밑에 두고 창 밖으로 넘침) — step 161 delegated 유지 | B #3 |
| 4 | 네 뷰 이름표, Transform Display, Character Sets, Mesh Display, 폴리곤 기본 도형 7, 렌더 lambert1, Preferences | A, B |

## 남은 것 / backlog

`C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 8 개 (steps 174–181) — PLAN 「재점검 12차」. 5.x 헤드리스는 157–171
이 아직 안 돌았다 (다음 릴리스 준비 때).
