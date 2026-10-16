# Step 23 — 재점검 2차

## 계획 (delegated)

1. 전체 테스트 (헤드리스·GUI·dogfood) + 깨끗한 설정에서 Maya 사용자 탐색 세션 (dogfood 가 안 다루는 것: 클릭 선택, cm 스케일
   Shift+기즈모 복제, X 스냅, Shift+RMB Create, S 키, Alt+V, 상단 메뉴, W 홀드 메뉴, 면 Delete, Outliner) — 스크린샷 직접 확인.
2. research 대응표·PLAN·step 「남은 것」·manual_checks 수집 + blindspot (서브에이전트 1개, 읽기 전용; 주장은 직접 재확인).
3. PLAN 「재점검 2차」, HANDOFF, backlog (5–8개, Maya 사용자가 체감하는 것 우선).

## 한 것

- `tools/dogfood.py --session SCRIPT`: 다른 세션 스크립트를 같은 깨끗한 설치로 실행 (결과 `tmp/dogfood/<스크립트 이름>/`).
  탐색 세션은 `tmp/audit2_session.py` (일회성, 저장소 밖).
- 수집 결과는 `docs/PLAN.md` 「재점검 2차」.

## 검증

- 헤드리스 `python tests/run.py`: **239/239** (22 파일). GUI `python tests/gui/run.py`: **172/172** (16 파일).
- `python tools/dogfood.py`: **46/47** (남은 실패 `=` 매니퓰레이터 크기), 콘솔 오류/경고 0.
- 탐색 세션 `python tools/dogfood.py --session tmp/audit2_session.py`: **13 중 12**, 콘솔 오류 0.
  - 통과: 클릭 선택·Shift 추가·Ctrl 해제·빈 곳 해제, W, cm 스케일 Shift+기즈모 드래그 → pCube2 (10.44 cm), Shift+RMB(선택 없음) → S =
    Cube 1 cm, S 키 = 키 설정 (CB 채널 빨강), Alt+V 재생/정지, F11 면 모드.
  - 실패: **면 모드 Delete = Blender Delete 메뉴** (면 6 → 6, `a2_05_delete_faces.png`). Maya 는 선택 컴포넌트를 바로 삭제.
  - 체크는 통과했지만 실제로는 문제: **X 홀드 + 기즈모 드래그가 사본을 0 cm 로** (10.44 cm 에서 ~10 cm 더 끌었는데 x = 0) — 스냅
    간격이 cm 장면에 맞지 않음 (Blender GRID 스냅 = 보이는 그리드 단계). 같은 원인으로 보이는 것: **MayaKit 템플릿 뷰포트에 그리드 선이
    안 보임** (모든 스크린샷, Maya 는 1 cm / 5 cm 그리드, research/maya/defaults.json:29-31).
  - 화면에서 본 것: Outliner 이름이 잘림 ("pCube", "pSphe", 좁은 왼쪽 Outliner), W 홀드 메뉴 "Smart Duplicate" 에 켜짐 표시 없음,
    타임라인 프레임 번호와 현재 프레임 표시가 겹침 ("8|10").

## 남은 것

- `docs/PLAN.md` 「재점검 2차」 우선순위 목록과 backlog (step 24+).
