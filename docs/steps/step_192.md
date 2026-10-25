# Step 192 — 재점검 14차 (사용자 지시의 「재점검 13차」)

## 계획

사용자 지시 (2026-10-25): 정한 일 (backlog_183, steps 183–190, 출시 0.4.1 = 191) 이 모두 끝남 — 헤드리스 전체 + 깨끗한 설정 설치
dogfood + GUI 를 Maya 사용자 눈으로, 「남은 것」·manual_checks 정리 (blindspot 포함), PLAN 절, HANDOFF, backlog 5–8 개. 기준: 「기본
Maya 에 Blender 기능이 붙은 모습」, 차이만. PLAN 의 「재점검 13차」 는 이미 step 182 이므로 이번은 **14차** 로 번호 매김 (delegated,
steps 163 / 173 / 182 와 같은 방식). Hermes 10-25: HANDOFF 의 끝난 0.2.1 사용자 할 일 줄은 지우고 0.4.1 스토어 업로드만 남김.

레인 (step 182 와 같음; 포그라운드 에이전트 2 개 동시, Blender 최대 2 개):
- **A — 문서 정리** (에이전트, Blender 없음): README 대응표, 183–191 「남은 것」 + step 182 목록 대조, GitHub 이슈, blindspot,
  manual_checks → `docs/steps/step_192_remaining.md`, `docs/manual_checks.md`.
- **B — 수치** (에이전트, Blender 1 개, sandbox `q192`): menu_count / 옵션 상자 / 마킹 메뉴 / 셸프 / 단축키 / look_compare →
  `docs/steps/step_192_quant.md`.
- **메인**: 빌드 한 번 → 헤드리스 전체 (sandbox `h192`, `--no-build`, 셸 백그라운드 명령 — 서브에이전트 아님) → 레인 뒤 dogfood
  (Blender 2 개 상한 때문에 B · 헤드리스가 끝난 뒤: 순서 필요) → 스크린샷 직접 보기 → 합치기, PLAN · HANDOFF · backlog, 커밋.
  GUI 전체 묶음은 돌리지 않는다: 이 단계는 src 를 고치지 않는 감사 (사용자 10-23 규칙: 전체 GUI 는 출시 준비 때).

진행 메모 (delegated): 레인 A · B 에이전트는 Agent 기본값 때문에 백그라운드로 떴다 (foreground 지정 빠뜨림) — ScheduleWakeup 없이 완료
알림으로 합쳤고 둘 다 끝까지 돌았다. 헤드리스 로그를 sandbox 폴더 안 (`tmp/h192/run.log`) 에 썼더니 run.py 의 sandbox 정리가 지움 —
결과는 `tmp/h192/results/*.json` 으로 셈.

## 한 일 · 검증

- 헤드리스 전체 4.5: **1731 / 1731** (215 파일, HEAD 13d2153, sandbox h192, zip = src 바이트 동일).
- dogfood (`tools/dogfood.py`, 깨끗한 설정에 zip 설치 → Maya 모드 → 스크립트 세션): **43 / 48** — 실패 5 개 중 4 개 (F8, CB 가운데
  끌기, Delete, h) 는 첫 실패 (RMB > Vertex) 가 edit 모드에 남긴 연쇄. 첫 실패 뒤 모드를 되돌리는 사본 (`tmp/audit192_recover.py`) 으로
  다시: **47 / 48**, 남은 실패 = **RMB 서쪽 flick → Vertex** (G1). 콘솔 오류 / 경고 0. step 182 는 48 / 48 이었다 → step 184 회귀.
- 추가 세션 `tmp/audit192_session.py` (183–190 기능: Gear + INPUTS, 키 + Time Slider, Mesh 메뉴, Graph Editor, UV Editor): 2 / 2, 콘솔 0,
  샷 6 장 `tmp/dogfood/audit192_session/shots/`. 스크린샷 18 장 직접 봄.
- 레인 A (`step_192_remaining.md`): 대응표 **30 / 1 / 0 / 2 (91 %)** 그대로 (세 감사째). step 182 목록 중 13 개 끝 (지움), ~40 개 남음,
  새 blindspot NB1–NB6 (NB1 애니 레이어에 넣은 오브젝트의 키가 CB · Time Slider · Graph Editor 에서 사라짐, NB2 옛 "no character sets"
  문구, NB3 primitive ❒ 창, NB4 5.x 헤드리스 154–190 안 돌림). 열린 이슈 #89 하나. manual_checks 705 / 107 → **709 / 107** (옛 문구 5 곳
  고침, 「Step 192」 4 개).
- 레인 B (`step_192_quant.md`): 메뉴 714 → **750 / 1318 (56.9 %)** (Key 73 %, Control 64 %, Mesh Display 64 %, Create 67 %), 편집기
  메뉴 578 / 914 그대로, 옵션 상자 Maya 창 114 → **120 경로** (dead 207 → 193), 셸프 160 / 203, 단축키 210 그대로, 마킹 368 / 55 →
  **371 / 52**. look_compare 1.0: 뷰포트 20 / 20 (새 표본 8: 선택 edge, 평면 핸들, 가운데 상자), 킷 픽셀 7 / 7, rects 5 / 12 그대로. 회귀 0
  (수치상).

## 메인 GUI 관찰 (dogfood 스크린샷 vs Maya 2022) — 차이만

| # | 차이 | 근거 |
|---|---|---|
| G1 | **RMB 서쪽 끌기가 Vertex 를 안 고름**: 1600 × 900 창 뷰 가운데에서 RMB → 목록이 아래에 안 들어가 링 + 목록이 ~340 px 위로 (링이 Status Line · 셸프 위). step 184 규칙 (lift 아래로는 방향 없음) 이라 가장 흔한 Maya 동작 (RMB → Vertex / Face / Edge) 이 죽음. Maya 는 **화면** (1440) 경계에서만 올림 → 보통 위치에서 링은 누른 점 | `05_rmb_marking_menu.png`, dogfood FAIL, `research/maya/re/rmb_list_184.md` |
| G2 | 핫박스 위에 in-view 메시지 ("Component selection on…") 와 **In-View Editor 상자 (polyExtrudeFace1)** 가 겹쳐 핫박스 줄 글자가 섞임 (step 182 G2 그대로 + 새로 In-View Editor) | `07_hotbox.png` |
| G3 | AE 탭 · 메뉴 잘림 ("pCu…", "Sele…", "Fo…", "Pre…") — step 182 G3 그대로 | `11_attribute_editor.png` |
| G4 | 결과 칸 `Undo: Group` 이 P / F8 / Ctrl+E / Delete 를 지나도 그대로 — step 182 G4 그대로 | `07`, `11` |
| G5 | Mesh > Cleanup… 에 ❒ 옆 ▸ 하위 메뉴 화살표 (Maya: ❒ 만 있는 leaf) | `b03_mesh_menu.png` |
| G6 | 주 창을 Graph Editor 로 바꾸면 Blender 사이드바 (Active F-Curve, "RNA Array Index", Handle Smoothing) 가 열려 있음 (Maya Graph Editor 에 없음); 범위 밖 주황 띠 | `b04_graph_editor.png` |
| G7 | [U] 키 1 / 10 / 24 중 Time Slider 에 frame 1 빨간 눈금이 안 보임 (10 은 현재 프레임 상자 밑) — 측정 안 함 | `b02_time_slider_keys.png` |

## 차이 우선순위 (점수 = 심각도 × 빈도, 1–3 척도)

| 점수 | 차이 | 출처 |
|---|---|---|
| 9 | RMB flick 이 lift 된 메뉴에서 죽음 (G1) | 메인 dogfood |
| 6 | 애니 레이어 오브젝트 키 표시 사라짐 (NB1) | A #1 |
| 6 | Channel Box 모양 · Time Slider 현재 프레임 파란 말풍선 | B #1 #2 |
| 6 | primitive / Character Set / Curves ❒ = Blender redo / generic (Maya 창) | B #3, A NB3 |
| 6 | Graph Editor 154 / 229 + Blender 사이드바 (G6) | A #2, G6 |
| 6 | 리그 나머지 Skin 68 % · Constrain 55 % | A #3, B #7 #8 |
| 6 | FX 19 % (일곱 감사째) — backlog 밖 (Maya 사용자 체감 빈도 낮음, delegated) | B #4 |
| 4 | 작은 것: G2 G3 G4 G5, 옛 character set 문구 (NB2), NURBS CVs / Hulls 회색 | 메인, A #4, B #5 #9 |
| 4 | 5.x 헤드리스 154–190 (NB4) | A #7 |
| 4 | maya.cmds 17 함수, 렌더 lambert1 1.25 배, Reference Editor, ❒ 클릭 (메뉴바 밖) | A #8–#10, B #10 |

## 남은 것 / backlog

`C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 8 개 (steps 193–200) — PLAN 「재점검 14차」. FX, maya.cmds, 렌더 밝기,
Reference Editor, ❒ 클릭 나머지 입구는 다음 감사로. G7 은 manual_checks 「Step 192」 대신 다음 Time Slider 단계에서 확인.
