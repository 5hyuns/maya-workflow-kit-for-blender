# Step 163 — 재점검 11차 (사용자 지시의 「재점검 10차」)

## 계획

사용자 지시 (2026-10-24): 정한 일 (backlog_155, steps 155–162) 이 모두 끝남 — 헤드리스 전체 + 깨끗한 설정 설치 dogfood + GUI 를 Maya
사용자 눈으로, 「남은 것」·manual_checks 정리 (blindspot 포함), PLAN 절, HANDOFF, backlog 5–8 개. 기준: 「기본 Maya 에 Blender 기능이 붙은
모습」, 차이만. 「재점검 10차」 는 step 154 이므로 이번은 11차로 번호 매김 (delegated, step 154 와 같은 방식).

레인 (step 154 와 같음; 포그라운드 에이전트 2 개 동시, Blender 최대 2 개):
- **A — 문서 정리** (에이전트, Blender 없음): README 대응표, 155–162 「남은 것」 + step 154 목록 대조, GitHub 이슈, blindspot,
  manual_checks → `docs/steps/step_163_remaining.md`, `docs/manual_checks.md`.
- **B — 수치** (에이전트, Blender 1 개): menu_count / 옵션 상자 / 마킹 메뉴 / 셸프 / 단축키 / look_compare → `docs/steps/step_163_quant.md`.
- **메인**: 헤드리스 전체 (백그라운드, sandbox `h163`) → 레인 뒤 dogfood → 스크린샷 직접 보기 → 합치기, PLAN · HANDOFF · backlog, 커밋.
  dogfood 가 레인 뒤인 이유: Blender 2 개 상한.

## 한 일 · 검증

- 헤드리스 전체 4.5: **1518 / 1518** (184 파일, HEAD 2cd3406).
- dogfood (`tools/dogfood.py`, 깨끗한 설정에 zip 설치 → Maya 모드 → 스크립트 세션): **48 / 48**, 콘솔 오류 / 경고 0. 스크린샷 12 장
  `tmp/dogfood/shots/` 직접 봄.
- 레인 A: 대응표 **29 / 2 / 0 / 2 (88 %)** — 움직인 행 없음. 열린 이슈 20 개 중 19 개가 코드에서 고쳐짐 (#81 step 160, #97 step 158 이
  새로; 릴리스 때 닫음), 열린 것 #89 하나. step 154 의 G1–G4 · G6 · BS1 (셸프 추가) · BS3 (Hypershade 드래그) 끝. manual_checks
  620 / 81 → **620 / 86** (GUI 테스트가 다 검사하는 5 체크, 낡은 문구 8 고침, "Allset" 16 곳 이름 바꿈). 새 blindspot: **DAG 상속 없음**
  (h / Ctrl+H / layer V / Delete / Export Selection / Ctrl+1 이 자손에 안 미침 — 킷 안에서도 Ctrl+X · Duplicate · 와이어는 자손 포함이라
  어긋남), 셸프 더블클릭 = `redo_last` (step 147 뒤 의미 없음), Smooth Mesh Preview to Polygons = `object.convert` (모든 modifier 굽힘,
  skinCluster 포함). 자세히 `step_163_remaining.md`.
- 레인 B: 메뉴 600 → **649 / 1318 (49.2 %)** (Skeleton 24 → 94 %, Curves 44 → 58 %), 편집기 메뉴 517 → **545 / 914**, 옵션 상자 Maya 창
  78 → **85 경로** (서로 다른 창 83 → 90), dead 232 → 225, generic 43 → 44, 셸프 153 → 155 / 203, 단축키 202 → 209, 마킹 메뉴 364 → 368;
  look_compare (실효 1.0) 킷 픽셀 5/6 → **6/6**, 뷰포트 11/12 (선택 면 stipple), rects 5/12, 밀도 5/6. 네 감사째 그대로인 메뉴: Control 7 %,
  Visualize 20 %, nConstraint 0 %, nCache 15 %, Effects 18 %, Texturing 12 %; Modify 41 % · Mesh Display 38 % · Surfaces 세 감사째. 자세히
  `step_163_quant.md`.

## 메인 GUI 관찰 (dogfood 스크린샷, Maya 2022 `research/maya/screens/` 와 나란히) — 차이만

| # | 차이 | 근거 |
|---|---|---|
| G1 | RMB 목록의 DG Traversal / Inputs / Outputs 가 회색 (Maya 는 노드 목록 하위 메뉴) | `05_rmb_marking_menu.png`, 레인 B §5c-1 |
| G2 | RMB 목록이 아래 공간이 모자라면 링 왼쪽에 (step 161 delegated: 링을 가리지 않게) — Maya 는 링 아래에 두고 창 밖으로 넘침. 레인 B 는 Maya 처럼 아래 + 잘림을 권함; 판단 보류, manual_checks Step 161 로 손 확인 | `05`, `14_marking_menu_object` 비교 |
| G3 | 정사영 칸 이름 "top -Z" / "front +Y" (Maya "top -Y" / "front -Z") 와 ViewCube 위치 (Maya top 칸) | `08_four_views.png` vs `16_four_view.png` |
| G4 | 컴포넌트 모드 Channel Box 가 transform 행을 그대로 보임 (Maya: shape + INPUTS) | 레인 B §5c-4, look_compare 08 |
| G5 | Command Line 언어 "Python" (Maya 기본 MEL) — 결정 5 (MEL 안 돌림) 그대로 | `01_first_start.png` |

## 차이 우선순위 (점수 = 심각도 × 빈도; 레인 A + B + 메인)

| 점수 | 차이 | 출처 |
|---|---|---|
| 9 | DAG 상속 없음: 부모 숨김 / 삭제 / 내보내기 / 고립이 자손에 안 미침 | A BS1 |
| 7 | 컴포넌트 모드 Channel Box (transform 행), RMB DG Traversal / Inputs / Outputs 회색 | B #5 #6, 메인 G1 G4 |
| 6 | 메뉴 어긋남: UV Editor Tools 의 Unfold / Cut / Sew / Pin 회색 (메인 UV 메뉴는 작동), Dope Sheet Curves 필터 회색 (Graph Editor 는 작동), Select / Delete All by Type > IK Handles / Clusters 회색 + 틀린 notice | B #9 #10, A #7 |
| 6 | 셸프 더블클릭 = redo_last (옵션 아님), 긴 탭 스크롤 없음 (추가 버튼이 화면 밖) | A #2 |
| 6 | Modify 41 % (53 회색), Smooth Mesh Preview to Polygons 가 skinCluster 까지 굽힘 | B #2, A #6 |
| 6 | Deform 41 %: Wire / ShrinkWrap 편집 dead 20, Paint Weights generic 9 | B #4 |
| 6 | 3D View 밖 선택 수정키 (Outliner Shift 범위, Ctrl 해제, 박스 XOR) — 대응표 Partial | A #5 |
| 6 | Visualize 20 % (Animation Snapshot, Ghosting) 네 감사째, Key 51 % (Scene Time Warp) | B #8 |
| 6 | UV Editor 나머지, Graph Editor 2 (Buffer Curves, Weighted Tangents), Surfaces 8 / 41, Curves 남은 것 | A #3 #4 #8, B #7 |
| 5 | 옵션 상자 ❒ 클릭 = 창 (#82: Blender 가 메뉴 항목 클릭 위치를 안 줌, C 벽 — 측정됨, hold / Shift·Ctrl 로 대체) | B #1, step 146 |
| 4 | 렌더 (lambert1 1.25 배, F12 기본 조명), Preferences 창, 선택 면 stipple, 네 뷰 이름표 | A #9 #10, B #11, 메인 G3 |

## 남은 것 / backlog

`C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 8 개 (steps 164–171) — PLAN 「재점검 11차」. 고쳐진 이슈 19 개는 다음
릴리스에서 닫음 (원격 작업이라 이번엔 안 함). 5.x 는 step 153 뒤 안 돌림 (158–162 기록 없음) — 다음 릴리스 준비 때.
