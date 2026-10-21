# Step 133 — 재점검 8차 (사용자 지시의 「재점검 7차」)

## 계획

사용자 지시 (2026-10-22): 정한 할 일이 모두 끝났으니 다시 점검 — (1) 헤드리스 전체 + 깨끗한 설정에 설치해 GUI 로 Maya 사용자처럼 써 보기
(dogfood: 레이아웃, Channel Box, 마킹 메뉴, 핫박스, 키), (2) 대응표 · PLAN · 각 단계 「남은 것」 · manual_checks 정리 + blindspot,
(3) PLAN 에 재점검 절 (구현률, 우선순위), (4) 다음 할 일 5–8 개를 `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 에,
(5) 비판 기준: "기본 Maya 에 Blender 기능이 붙은 모습" — 칭찬 없이 차이만, Maya 2022 와 같은 시나리오를 나란히.

- 이름 (delegated): PLAN 에는 이미 「재점검 7차(정밀 비판)」 (step 98) 이 있다. 이번 절은 **「재점검 8차 (step 133)」** 로 적고 사용자 지시의
  「재점검 7차」 라는 말을 함께 적는다 (결정 12 의 번호 겹침 처리와 같은 방식).
- 새로 찾은 버그는 고치지 않고 (점검 단계) GitHub 이슈로 올린다 (사용자 규칙 2026-10-21: 고치기 전에 이슈; 라벨 bug / maya-parity /
  found-by-audit, 마일스톤 0.3.0).
- 등급 · 점수는 step 98 과 같게: look / operation / function / missing, 점수 = 하루 빈도 (1–5) × 심각도 (1–5).

### 레인 (병렬)

| 레인 | 할 일 | 산출 |
|---|---|---|
| MAIN | 헤드리스 전체, `tools/dogfood.py` (깨끗한 설정 설치 + 스크립트 세션) | 숫자, 콘솔 오류 |
| UI | 깨끗한 설정 GUI 세션 (Maya 사용자 관점): 첫 화면, Channel Box, 마킹 메뉴, 핫박스, 키, 도킹 — step 98 의 Maya 쪽 그림 (`research/maya/screens/audit7/pairs/`) 과 같은 장면을 다시 찍어 나란히, `tools/look_compare.py` 수치 | `docs/steps/step_133_ui.md` |
| WORK | 작업 흐름 시나리오 (모델링 · UV · 애니 · 리깅 · FX · 렌더 · 파일 입출력) 를 킷에서 하고 Maya 2022 (mayapy / GUI) 결과와 비교 | `docs/steps/step_133_work.md` |
| QUANT | 메뉴 전수 (`tools/menu_count.py`), 옵션 박스, 셸프, 단축키 행, Windows 메뉴 수치 — step 98 수치와 대비 | `docs/steps/step_133_quant.md` |
| DOCS | 대응표 · PLAN · step 99–132 「남은 것」 · manual_checks 를 모아 끝난 것 / 남은 것, blindspot | `docs/steps/step_133_remaining.md` |

UI / WORK / QUANT / DOCS 는 서로 파일이 겹치지 않는다 (각자 문서 하나 + `tmp/audit133_<lane>/`). 메인이 PLAN 절 · HANDOFF · backlog.json ·
이슈를 쓴다 (레인 결과가 다 모여야 우선순위를 정할 수 있어 마지막에 순차).

## 한 것

- 레인 4 개 (UI, WORK, QUANT, DOCS) 를 병렬로 돌리고, 메인은 헤드리스 전체 · dogfood · 결과 종합 · 이슈 · PLAN · backlog 를 했다.
  레인 결과: `step_133_ui.md` (look / 키, Maya 쌍 비교 21 건), `step_133_work.md` (작업 흐름 43 건, 버그 15), `step_133_quant.md`
  (step 98 → 지금 수치), `step_133_remaining.md` (구현률, 남은 것, manual checks, blindspot B1–B6).
- 새로 찾은 버그 · 차이는 고치지 않고 GitHub 이슈 **#55–#75** 로 올림 (found-by-audit, 마일스톤 0.3.0; 레인끼리 겹친 것은 합침).
- `docs/PLAN.md` 「재점검 8차 (step 133)」: 구현률 29/2/0/2, 수치 표, 점수 12 이상 차이, 우선순위.
- 다음 할 일 8 개 → `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` (step 134–141).

## 검증

- 헤드리스 전체 `python tests/run.py --no-build`: **1025 passed, 0 failed** (127 파일).
- `python tools/dogfood.py` (깨끗한 설정 설치 + Maya 사용자 세션): **48/48 PASS**, 콘솔 오류 · 경고 0, 스크린샷 12 장 (`tmp/dogfood/shots/`) — 핫박스,
  RMB 마킹 메뉴를 직접 봄 (RMB 목록이 뷰포트 아래로 잘림 → #56).
- UI 레인: 깨끗한 설치 GUI 세션 10 회 (1.0 / 1.25 / Region Overlap 켬), 콘솔 traceback 0, look_compare 1.0 rects 5/12 · 1.25 3/12.
  쌍 그림을 직접 봄 (`tmp/audit133_ui/pairs/vp_02_cube_selected_move.png`: 주황 선택 vs Maya 초록; `s125/shots/b11_channel_box.png`:
  큐브 선택 뒤 Layer Editor 없음 → #55).
- WORK 레인: 킷 헤드리스 + mayapy 같은 시나리오, GUI 워크플로 테스트 46/46.

## 남은 것

- backlog 8 개 (PLAN 「재점검 8차」 우선순위 1–8) = step 134–141. 그 밖은 PLAN 우선순위 9.
- 사용자 할 일 (step 132 그대로): 스토어에 0.2.1 zip 업로드, GitHub v0.2.1 초안 publish.
