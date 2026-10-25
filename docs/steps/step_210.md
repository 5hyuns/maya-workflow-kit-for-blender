# Step 210 — 재점검 16차 (사용자 지시의 「재점검 15차」)

## 계획

사용자 지시 (2026-10-26): 정한 일 (감사 15 backlog, steps 202–209) 이 모두 끝남 — 헤드리스 전체 + 깨끗한 설정 설치 dogfood + GUI 를
Maya 사용자 눈으로, 「남은 것」·manual_checks 정리 (blindspot 포함), PLAN 절, HANDOFF, backlog 5–8 개 + 단계마다 GitHub 이슈, #108 표
갱신. 기준: 「기본 Maya 에 Blender 기능이 붙은 모습」, 차이만. PLAN 의 「재점검 15차」 는 이미 step 201 이므로 이번은 **16차** 로 번호
매김 (delegated, steps 182 / 192 / 201 과 같은 방식).

레인 (step 201 과 같음; 포그라운드 에이전트 2 개 동시, Blender 최대 2 개):
- **A — 문서 정리** (에이전트, Blender 없음): README 대응표, 202–209 「남은 것」 + `step_201_remaining.md` 목록 대조, GitHub 이슈,
  blindspot, manual_checks → `docs/steps/step_210_remaining.md`, `docs/manual_checks.md`.
- **B — 수치** (에이전트, Blender 1 개, sandbox `q210`): menu_count / 옵션 상자 / 마킹 메뉴 / 셸프 / 단축키 / look_compare →
  `docs/steps/step_210_quant.md`.
- **메인**: 빌드 한 번 → 헤드리스 전체 (sandbox `h210`, `--no-build`, 셸 백그라운드 명령 — 서브에이전트 아님) → 레인 뒤 dogfood
  (Blender 2 개 상한 때문에 헤드리스 · B 가 끝난 뒤: 순서 필요) → 스크린샷 직접 보기 → 합치기, PLAN · HANDOFF · backlog · 이슈, 커밋.
  GUI 전체 묶음은 돌리지 않는다: src 를 고치지 않는 감사 (사용자 10-23 규칙: 전체 GUI 는 출시 준비 때).

진행 메모 (delegated): 헤드리스 (백그라운드 셸) 와 레인 A · B (에이전트 2 개) 동시, dogfood 는 헤드리스와 레인 B 의 Blender 가 끝난 뒤
(Blender 2 개 상한: 순서 필요). 새 이슈의 마일스톤은 아직 내지 않은 다음 버전 0.5.0 (delegated, step 201 과 같음).

## 한 일 · 검증

- 헤드리스 전체 4.5: **2018 / 2018** (242 파일, HEAD 4dd0b14, sandbox h210, zip = src 바이트 동일 260 파일 — 레인 B 확인).
- dogfood (`tools/dogfood.py`, 깨끗한 설정에 zip 설치 → Maya 모드 → 스크립트 세션): **48 / 48**, 콘솔 오류 / 경고 0. 스크린샷 12 장 중
  01 / 05 / 06 / 07 / 08 / 11 직접 봄.
- 레인 A (`step_210_remaining.md`): 대응표 **30 / 1 / 0 / 2 (91 %)** 그대로 (다섯 감사째). step 201 목록 42 개 중 3 개 끝, 7 개 일부,
  32 개 그대로. 새 blindspot NB12–NB17 (Windows 메뉴 17 개가 Blender 기본 편집기만 엶, Light Linking 메뉴가 킷 편집기 아님, Namespace
  Editor 회색, 빈 번호 채우기 남은 곳 + 붙여넣기 `.001`, 202–209 5.x 미실행, Arnold 데이터 없음 [U]). manual_checks 753 / 107 →
  **757 / 106** (낡은 step 69 항목 지움, 문구 고침, 「Step 210」 5 개).
- 레인 B (`step_210_quant.md`): 메뉴 unique 762 → **803 / 1318 (60.9 %)**, 메뉴 세트 합 874 → **941 / 1486**, 편집기 메뉴 600 →
  **649 / 914** (+ Reference Editor 27 / 38 = 676 / 952), 옵션 상자 Maya 창 164 → **176**, dead 187 → 164, generic 19 → **28 (나빠짐)**,
  마킹 371 → 373, 셸프 160 / 단축키 210 그대로 (다섯 감사째). look_compare kit-drawn 1.0 **12 / 12**, 1.25 **12 / 12** (Time Slider
  현재 칸 회귀 고쳐짐, ΔE 13.8 → 0.3; 대신 Time Slider 45 px, Maya 36). 가장 낮은 영역: nConstraint 0 / 19, Generate 2 / 50, Toon
  1 / 20, Texturing 1 / 8, nCache 3 / 20.
- GitHub: backlog 단계마다 이슈 **#117–#124** (라벨 roadmap + maya-parity + found-by-audit, 마일스톤 0.5.0), #108 본문 숫자표 ·
  Planned next 갱신.

## 메인 GUI 관찰 (dogfood 스크린샷 vs Maya 2022) — 차이만

| # | 차이 | 근거 |
|---|---|---|
| G1 | AE 노드 탭 (pCube1 / pCubeShape1 / initialShadingGroup / lambert1) 이 dock 폭 버튼 4 줄로 세로로 쌓임 (Maya: 가로 탭 한 줄), AE 메뉴 바 3 줄, 아래 Select / Load Attributes 잘림 — dock 폭이 Channel Box 폭 그대로 (event-simulated 세션은 `ALLSET_FIT_WARP` 꺼짐; 실사용 폭 맞춤은 아직 미측정, step 201 G4 와 같음) | `11_attribute_editor.png` |
| G2 | 킷 Outliner 에 오브젝트 (pCube1, pCube2) 가 기본 카메라 위에 나옴 (Maya: persp / top / front / side 먼저, 그다음 오브젝트, 세트 마지막) | `05`, `06`, `07`, `08` |
| G3 | Help Line 이 Blender 도구 안내 ("Select Tool: click or drag to select. Shift toggles, Ctrl deselects, Ctrl+Shift adds") — Maya 는 짧은 도구 설명 | 모든 샷 |
| G4 | 현재 프레임 칸 위의 Blender 파란 "1" 상자, RMB 목록이 링 옆 (step 193 결정) — 남은 차이 (알려짐) | `01`, `05` |
| G5 | 테마 색 (메뉴 바 · 팝업 · Help Line #181818, Outliner 선택 #334d80): 킷은 테마를 안 바꿈 (결정 13) — look_compare theme 19 / 25 ΔE > 5 | 레인 B §4 |

G1 · G2 는 backlog #1 「Audit 16 fix batch」 (#117) 로. G3 은 다음 감사 후보 (Help Line 문구 = Maya annotation, 측정 필요).

## 남은 것

- 남은 차이 전체 목록: `step_210_remaining.md` §3 / §8, `step_210_quant.md` §5.
- backlog 밖 다음 후보: Arnold 메뉴 (먼저 측정, NB17 [U]), Channel Box look 2 (상태 색 칸 바탕), Hypershade depth 2 (115 / 249),
  Namespace Editor, Generate / Toon / Texturing (4–12 %), Help Line 문구.
- 정리 (사용자 확인 필요, 손대지 않음): `.claude/worktrees` 아래 에이전트 worktree 64 개 + `C:/Repos/bmk-hotfix`.
- 이슈 #103–#107, #109–#116 은 로컬 커밋으로 고쳐졌고 push 해야 닫힘. 사용자 할 일: 스토어에 0.4.1 zip 업로드.
