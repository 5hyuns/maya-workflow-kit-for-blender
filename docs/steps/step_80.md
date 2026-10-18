# Step 80 — 재점검 5차

## 계획 (delegated)

1. 전체 헤드리스 테스트 + 깨끗한 설정 설치 dogfood (기본 47 항목) + 탐색 세션 `tmp/audit5_session.py` (일회성, 저장소 밖).
   세션은 MayaKit 템플릿 (cm) 에서 step 72–79 에 생긴 것을 실제 키·마우스로 누른다: 선택 우선순위 (메시 앞 NURBS 원), F3 메뉴 바,
   F8 인뷰 메시지, F10 + W 엣지 프리셀렉트, 편집 모드 Insert, UV > 3D Cut and Sew 드래그, S 키 두 번 → 타임 슬라이더 틱,
   Input Line Abs X, Alt+Q 마킹 메뉴, Ctrl+Shift+C, Space 핫박스. 스크린샷은 직접 확인한다.
2. research 대응표·PLAN·step 72–79 「남은 것」·manual_checks·keymap_mapping 수집 + blindspot. 읽기 전용 서브에이전트 1개,
   "없다" 주장은 직접 grep 으로 재확인.
3. PLAN 「재점검 5차」, HANDOFF, backlog (5–8개, Maya 사용자가 매일 체감하는 것 우선) → `hermes/autodrive_bmk/backlog.json`.

## 한 것

- 탐색 세션 `tmp/audit5_session.py` (저장소 밖), `python tools/dogfood.py --session tmp/audit5_session.py`.
- 수집 (읽기 전용 서브에이전트) + grep 재확인 → `docs/PLAN.md` 「재점검 5차」: 대응표 28/3/0/2 (85 %), 키맵 구현 125 · IC 10 ·
  해당 없음 11 · 미검토 254, manual_checks 320 열림 (체크 0), 4차 backlog 종결, 새 발견, blindspot, 우선순위.
- 다음 할 일 8개 → `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` (PLAN 「재점검 5차」 우선순위 1–8 과 같음).

## 검증

- 헤드리스 `python tests/run.py`: **634/634** (74 파일).
- `python tools/dogfood.py`: **47/47**, 콘솔 오류/경고 0.
- 탐색 세션 (두 번째 실행, 첫 실행은 장면이 너무 작아 클릭이 원에 걸림 — 세션을 A 프레이밍 + 원 25 % 로 고침): **16 중 15**, 콘솔 0.
  - 통과: 메시 앞 NURBS 원 클릭 = 원 (선택 우선순위), 메시 클릭 = 메시, F3 → riggingMenuSet 이고 상단 바가 바로 "Rigging" (`a5_03`),
    F8 = 편집 모드 + 인뷰 메시지, Insert = 커서 툴 + CURSOR 피벗 → Insert = Move 복귀, UV > 3D Cut and Sew → 윗면 둘레 드래그 1 → 2 셸,
    F8 오브젝트 모드, S 두 번 = 1·12 키 + 타임 슬라이더 빨간 틱 (`a5_07`), Input Line Abs X 20 = 20 cm, Alt+Q 메뉴, Ctrl+Shift+C = camera1,
    Space 핫박스.
  - 실패 1 (세션 탓): F10 + W 엣지 호버 (Move 매니퓰레이터가 작은 큐브 전체를 덮어 프리셀렉트가 설계대로 양보, step 74).
    첫 실행의 실패 (메시 클릭이 원에 걸림, 그 뒤 단계가 곡선 편집 모드로 멈춤) 도 세션 탓.
- 화면에서 본 것 (스크린샷 직접 확인):
  - **persp 뷰가 Maya 의 두 배 광각**: 템플릿 렌즈 35 (`tools/make_startup.py:37`) 는 Blender 뷰포트에서 수평 91.6°, Maya persp 54.4°
    (Blender 렌즈 70 이 같음). 1 cm 큐브가 아주 작고 원근이 강함 (`a5_01`), Ctrl+Shift+C 카메라 Focal Length 17.5 (`a5_09`, Maya 는 35).
    step 41 이 렌즈 50 일 때 지적했지만 (step_41.md:52) 고치지 않음 → backlog 1.
  - Channel Box (키 붉은 칸), Outliner, 핫박스, Alt+Q 메뉴, 셸프·Status Line 은 의도대로.

## 남은 것

- `docs/PLAN.md` 「재점검 5차」 우선순위 1–8 (backlog.json) 과 9 (나중 후보).
- manual_checks 320 항목 손 검증 0 — backlog 8 이 자동화 가능한 것부터 줄인다.
- `docs/keymap_mapping.md` 의 `Shift+\` 행 표 깨짐 (생성기 이스케이프) — backlog 7 에 포함.
