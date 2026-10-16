# Step 32 — 재점검 3차

## 계획 (delegated)

1. 전체 테스트 (헤드리스·dogfood) + 깨끗한 설정에서 Maya 사용자 탐색 세션. 세션은 step 24–31 에서 새로 생긴 것을 실제 키·마우스로
   눌러 본다: RMB 재질, Ctrl+A AE, Space 핫박스/탭, 마키 관통, Shift+T 면 지정, z, Delete, =, W 홀드 메뉴, 2차 blindspot 의 박스 줌·T.
   스크린샷은 직접 확인한다.
2. research 대응표·PLAN·step 「남은 것」·manual_checks 수집 + blindspot. 서브에이전트 1개(읽기 전용)에 맡기고, 주장은 직접 grep 으로 재확인한다.
3. PLAN 「재점검 3차」, HANDOFF, backlog (5–8개, Maya 사용자가 체감하는 것 우선).

## 한 것

- 탐색 세션 `tmp/audit3_session.py` (일회성, 저장소 밖), `python tools/dogfood.py --session tmp/audit3_session.py`.
- 수집 결과는 `docs/PLAN.md` 「재점검 3차」.
- 종료 시 메모리 경고 원인 분리: `invoke_search_popup` 은 kit 밖의 일반 Python 오퍼레이터에서도 같은 경고를 낸다 (임시 GUI 프로브 4개, 삭제함).
  → Blender 쪽 문제로 판단, 기록만 함.

## 검증

- 헤드리스 `python tests/run.py`: **281/281** (30 파일). GUI 전체는 HEAD `91606bb` (step 31, 이후 `src/` 변경 없음)에서 **239/239**.
- `python tools/dogfood.py`: **47/47**, 콘솔 오류/경고 0.
- 탐색 세션: **15 중 13**, 콘솔 1줄 (`Not freed memory blocks: 5`, 아래).
  - 통과: 클릭 선택, RMB 클릭 → Assign Favorite Material ▸ Lambert (선택 없이 커서 아래 큐브에 lambert1), Ctrl+A → AE 재질 탭,
    Space 홀드 핫박스, Space 탭 4분할 ↔ 단일, F9 + 마키 = cm 큐브 정점 8/8 (뒤쪽 포함), F11 + Shift+T "blinn" Enter = 면 하나만 blinn1,
    z = 그 지정 취소, = 매니퓰레이터 75 → 94, T = Show Manipulator (builtin.transform).
  - 실패 1 (세션 탓): Delete 가 면 6개를 모두 지움. 세션이 bmesh 로 면 하나를 고르면 언두 단계가 생기지 않아서, z 가 "전체 선택" 상태로
    되돌렸다. 실제 클릭 선택이면 언두 단계가 있다. kit 버그 아님.
  - 실패 2 (알려진 blindspot): **Ctrl+Alt+LMB 드래그 = 박스 줌 없음.** 뷰 거리가 그대로이고, 대신 박스 선택이 되어 pSphere1 까지 선택됨.
  - 콘솔: Shift+T 검색 팝업 (`WindowManager.invoke_search_popup`) 을 연 세션은 종료 때 `Not freed memory blocks: 5` (0.0005 MB).
    kit 없이 같은 API 를 쓰는 오퍼레이터로도 재현 → Blender 문제. 대안은 팝업 메뉴로 바꾸는 것뿐 (검색 필드를 잃음).
- 화면에서 본 것 (스크린샷 직접 확인):
  - **RMB 마킹 메뉴 목록이 뷰 아래로 잘림.** 화면 가운데 큐브에서 열어도 "Assign Existing Material" 이 타임라인 밑으로 들어간다
    (`a3_02_rmb_menu.png`). step 29 는 하위 메뉴만 영역 안으로 밀었고 루트 목록은 그대로다.
  - **AE 재질 탭 라벨**이 Lambert 재질을 "standardSurface:" 로 보여 준다 (`a3_03_attribute_editor.png`; `ui/attribute_editor.py:102` 가
    Principled 면 모두 standardSurface).
  - 레이아웃·Channel Box·핫박스·W 홀드 메뉴 체크·Outliner (이름 전체) 는 의도대로.

## 남은 것

- `docs/PLAN.md` 「재점검 3차」 우선순위 목록과 backlog (step 33+).
