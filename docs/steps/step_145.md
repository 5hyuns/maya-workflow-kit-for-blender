# Step 145 — 재점검 9차 (사용자 지시의 「재점검 8차」; 8차 = step 133)

## 계획

비판 기준 (사용자 2026-10-19): '기본 Maya 에 Blender 기능이 붙은 모습' 이어야 한다 — 칭찬 없이 차이만, Maya 2022 와 같은 시나리오를
나란히 따라 하며 시각 · 조작 · 기능에서 Maya 가 아닌 곳을 우선순위로.

| 레인 | 내용 | 산출물 |
|---|---|---|
| A 살아 있는 세션 (포그라운드) | 헤드리스 전체, 깨끗한 설정 설치 + dogfood, GUI 로 Maya 사용자 시나리오 (레이아웃, Channel Box, 마킹 메뉴, 핫박스, 키, 모델링 · UV · 애니 · 리깅 · FX · 렌더 · 파일) 를 Maya 캡처 (`research/maya/screens/`) 와 나란히, look_compare, 콘솔 오류 | `docs/steps/step_145_ui.md` (점수 매긴 차이 표 + 스크린샷 경로) |
| B 문서 감사 (포그라운드) | 대응표 / PLAN / steps 「남은 것」 / manual_checks / 열린 이슈 모으기, 끝난 것 지우기, 수치 다시 세기 (menu_count, 옵션 상자, 키맵, 마킹 메뉴, 셸프), blindspot | `docs/steps/step_145_remaining.md`, `step_145_quant.md` |
| 메인 | PLAN 「재점검 9차」 절, HANDOFF, backlog.json, 커밋 | |

결정 (delegated): 사용자 위임으로 brainstorm 의 승인 · /sc:review 관문은 건너뛰고 산출물은 step 문서로 (discovery spec 파일 없음).
번호: step 133 이 이미 「재점검 8차」 라서 이번 절 이름은 「재점검 9차」.

## 한 일

- 레인 A (`step_145_ui.md`): 헤드리스 1307/1307, dogfood 48/48 (콘솔 오류 0), 시나리오 GUI 206/206, look_compare (실효 1.0)
  viewport 11/12 · 킷 픽셀 6/6 · rects 5/12, Maya 캡처와 나란히 본 차이 표 + 새 이슈 #91–#100.
- 레인 B (`step_145_quant.md`, `step_145_remaining.md`): 수치 (메뉴 작동 596/1318, 옵션 상자 window 75 / dialog 22 / generic 43 /
  dead 233, 마킹 메뉴 회색 128 → 69), 대응표 29/2/0/2, 남은 일 통합 · 우선순위, blindspot, manual_checks 정리 (580 → 548,
  ticked 70 → 78), 5.2.2 헤드리스 1305/1308 → #90.
- PLAN 「재점검 9차」 절, backlog.json 8 개 (`C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json`).

## 검증

- 숫자는 위 (레인 문서에 명령 · 로그 경로). backlog.json = 8 개, JSON 로드 확인.

## 남은 것

- backlog 1–8 (PLAN 「재점검 9차」 Backlog). look_compare 1.25 배율, 5.x GUI 실행, Maya 를 다시 띄운 나란한 비교는 이번에 안 함.
