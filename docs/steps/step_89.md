# Step 89 — 재점검 6차

## 계획 (delegated)

1. 전체 헤드리스 테스트 + 깨끗한 설정 설치 dogfood (기본 47 항목) + 탐색 세션 `tmp/audit6_session.py` (일회성, 저장소 밖).
   세션은 MayaKit 템플릿 (cm) 에서 Maya 사용자의 하루 흐름을 실제 키·마우스로 누른다: 큐브·구 만들기, 클릭 선택, Channel Box
   `+=5`, 3 / 1 Smooth Preview, A 프레임, RMB 마킹 메뉴 (서쪽 = Vertex), F8, Ctrl+D, Ctrl+G, S 키 두 번, Alt+I (중간 키),
   Shift+) 넛지, Alt+P, Ctrl+A (AE), Space 핫박스. step 81–87 이 만든 것 (렌즈 70, Alt+I, Shift+), Alt+P) 이 섞여 있다.
   스크린샷은 직접 확인한다.
2. research 대응표·PLAN·step 80–88 「남은 것」·manual_checks·keymap_mapping 수집 + blindspot. 읽기 전용 서브에이전트 1개,
   "없다" 주장은 직접 grep 으로 재확인.
3. PLAN 「재점검 6차」, HANDOFF, backlog (5–8개, Maya 사용자가 매일 체감하는 것 우선) → `hermes/autodrive_bmk/backlog.json`.

## 한 것

- 탐색 세션 `tmp/audit6_session.py` (저장소 밖), `python tools/dogfood.py --session tmp/audit6_session.py`.
- 수집 (읽기 전용 서브에이전트) + grep 재확인 → `docs/PLAN.md` 「재점검 6차」: 대응표 29/2/0/2 (88 %; 타임라인 Partial → Done,
  step 84), 키맵 구현 142 · IC 10 · 해당 없음 11 · 미검토 237, manual_checks 348 중 [x] 13, 5차 backlog 종결, 새 발견, blindspot 7,
  우선순위. 서브에이전트의 research 줄 번호 일부가 틀려 (interaction.md:56 → :51 등) 직접 찾아 고침.
- 다음 할 일 8개 → `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` (사본 `backlog_90.json`; PLAN 「재점검 6차」
  우선순위 1–8 과 같음).

## 검증

- 헤드리스 `python tests/run.py`: **677/677** (81 파일).
- `python tools/dogfood.py`: **47/47**, 콘솔 오류/경고 0.
- `python tools/gen_keymap_mapping.py`: 468 행, 문서 변화 없음 (exit 0).
- 탐색 세션: **19/19**, 콘솔 0. 처음 두 실행의 실패는 세션 탓 (Channel Box 로 큐브를 5 cm 올린 뒤 다시 프레이밍하지 않아 RMB 가 화면 밖
  y 1403 에 눌림 → 뒤 단계가 편집 모드로 밀림; Alt+I 를 키가 없는 큐브에 눌렀는데 Maya Insert Key 는 기존 곡선에만 키를 넣으므로 [] 가
  맞음 — 세션을 S 두 번 + 가운데 Alt+I 로 고침).
- 화면에서 본 것 (스크린샷 직접 확인, `tmp/dogfood/audit6_session/shots/`):
  - `a6_01` 렌즈 70 persp, 큐브·구 크기 Maya 비율. `a6_02` Channel Box Translate Z 5. `a6_04` RMB 마킹 메뉴 (Vertex/Edge/Face/UV…,
    pCube1… 목록) — **목록이 Adjust Last Operation 패널 밑에 그려짐** (`draw.REGION_TYPES` 에 HUD 없음).
  - `a6_05` Ctrl+G → group1, 인뷰 메시지 "group1 grouped." — **Blender 부모 관계 점선이 그려짐** (Maya 는 없음 [K];
    `show_relationship_lines` 는 src / make_startup 어디에도 없음).
  - `a6_06` 키 1·6·10 빨간 틱 (잘라 확대해 확인), 모든 채널 빨강 (키 있음). `a6_07` ortho. `a6_08` AE (pCubeShape1 탭) — 사이드바
    탭 순서가 Item 위 / Channel Box 아래로 바뀜 (작음). `a6_09` 핫박스.

## 남은 것

- `docs/PLAN.md` 「재점검 6차」 우선순위 1–8 (backlog.json) 과 9 (나중 후보).
- manual_checks 335 항목 손 검증 — backlog 8 이 자동화 가능한 58 개부터 줄인다. 이번 발견은 모두 backlog 로 (새 manual check 없음).
- 배포 결정 (decision 11) 은 여전히 사용자 대기.
