# HANDOFF

## 현재 작업

- Step 14 (재점검 1차) 완료 — `docs/steps/step_14.md`, `docs/PLAN.md` 「재점검 1차」. 코드(`src/`) 변경 없음.
  헤드리스 188/188, GUI 115/115. 새 도구 `tools/dogfood.py` (깨끗한 설치 + Maya 사용자 첫 세션 이벤트 재생):
  체크 43개 중 35 통과, 실패 8 = 아직 없는 Maya 키(z, Shift+Z, h, Ctrl+1, `.`, `=`, Shift+>) + Ctrl+D 이름 `pCube1.001`; 콘솔 오류 0.
- 구현률 (research 대응표 33행): 완료 21, 부분 8, 미착수 2, 불가 2. 키맵 468행: 구현 51 + IC 8, 계획 26, 미검토 306.
- 발견: PLAN 8행(M1-d 나머지 키 25개)이 번호 변경 때 빠져 미구현; blindspot 14건 (Delete History 가 스무스 프리뷰를 구움,
  생성 경로 단위 100배 차이, 편집 모드 D/Ctrl+Shift+A 충돌, Shift+매니퓰레이터 복제 미계획 등).
- Step 13 (통합·배포) 완료 — release 0.1.0 (`c0f37b0`).

## 바로 다음 할 일

- `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 8개를 순서대로 (PLAN 「재점검 1차」 우선순위):
  1 스무스 프리뷰/Delete History 버그 → 2 z/h/Ctrl+1 등 일상 키 → 3 F 프레이밍·핫박스 잘림 → 4 편집 모드 키·즉시 Extrude/Bevel →
  5 복제 이름 pCube2 → 6 타임라인(. , 키, 재생 범위, Range Slider) → 7 생성 단위 통일 → 8 Shift+매니퓰레이터 복제 계획.
- 각 수정 후 `python tools/dogfood.py` 의 해당 체크가 PASS 로 바뀌는지 확인.
