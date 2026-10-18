# Step 88 — manual_checks → GUI 테스트 정리

재점검 5차 backlog 8 (docs/PLAN.md 「재점검 5차」 우선순위 8): `docs/manual_checks.md` 348 항목 중 체크 0.

## 계획

- step 59–79 절 (101 항목) 에서 이벤트 시뮬레이션 + 상태 확인으로 **항목 문구 전부**를 증명할 수 있는 것을 골라
  `tests/gui/gui_manual_sweep.py` 하나에 (MayaKit 템플릿 한 세션) 옮긴다. 검사 이름 앞에 항목 id `[M<step>-<n>]` (n = 그 절 안의 순서).
- 그 항목의 검사가 모두 통과하면 `[x]` + `(gui_manual_sweep)`. 문구 일부만 확인되면 체크하지 않는다.
- 키·클릭·드래그는 simulated event; 필드에 Enter 하는 동작은 그 속성의 setter (= Enter 경로) 로 — 실제 입력은 gui_step75 가 증명.
- 문서 맨 위에 자동 / 수동 수, 수동으로 남긴 이유 분류 (아래).

## 한 것

- `tests/gui/gui_manual_sweep.py` (새): 13 항목, 46 검사.
  - [M59-7] 여러 오브젝트 = lead 피벗, 편집 모드 = Bounding Box Center + 선택 bbox 중심.
  - [M63-5] Combine (pCube2, Translate 0, 피벗 = 합친 상자 중심) / Separate (pCube2 그룹 + polySurface1·2, Translate 0) / 편집 모드
    Separate = Blender (loose parts, `.001`, 그룹 없음).
  - [M69-3] Ctrl+Alt+S → `shot_v001.0001.blend` 로 저장하고 그 파일에서 계속, 원본 유지.
  - [M70-3] Graph Editor G (재생 범위) / D (Auto) / F / A, 3D View G = Repeat Last.
  - [M70-4] Maya Auto Key: 이동 키만 있는 큐브 회전 (매니퓰레이터 변환 + CB 입력) = 회전 키 없음, 환경설정 끔 = 모든 채널.
  - [M75-1..4] 입력 줄 Abs X / Rotate / Scale + Ctrl+Z, 편집 모드 Abs Z 0 / Rel, Rename (리드 이름, crate…, 잘못된 이름 Help Line),
    Select by Name (와일드카드, 없는 이름 = Help Line + 글자 남음, History 툴팁).
  - [M77-2] Insert 켬 + D = 끔, Insert 두 번 = 사용자 피벗 없음 (bbox 중심).
  - [M78-3] Ctrl+Alt+→ / ← 스핀 엣지 + 메뉴 Forward / Backward 와 같은 방향.
  - [M78-6] Graph Editor 3 / 1 / 2 (2 = Stacked → Normalized + 안내 report).
  - [M79-3] Cut and Sew 툴 안 x / s / d, 툴 밖 X (그리드 스냅 홀드) / D (피벗 홀드) / S (꿰매지 않음).
- `docs/manual_checks.md`: 13 항목 `[x] … (gui_manual_sweep)` (+ 69-3, 78-6 은 report 를 Python 이 못 읽는다는 주석), 맨 위 자동 / 수동 수.
- 테스트 작성 중 알게 된 것: Maya 이름 (`pCube1`) 은 셰이프 이름까지 세므로 오브젝트만 지우면 다음 큐브가 pCube3 — 절마다 메시 데이터도 지움.

## 분류 (step 59–79, 101 항목: 자동 13, 수동 88)

- **사람 판단 (23)** — 느낌·색·Maya 화면과 나란히 비교·다른 UI 배율·큰 장면 성능: 59-1, 59-3, 60-1, 63-1, 64-4, 65-1, 66-2, 66-4, 67-1, 67-6,
  67-7, 68-1, 68-3, 69-1, 70-1, 70-5, 72-2, 73-1, 73-4, 74-1, 74-2, 74-4, 79-4.
- **event_simulate / 테스트 환경으로 못 함 (7)**: 73-3 (DOUBLE_CLICK 이벤트를 만들 수 없음, step 73), 60-5 (Blender 재시작·작업 관리자 강제
  종료), 60-6 (Extensions 창의 끄기 / Remove — 실행 중 확장 제거), 61-1 / 61-2 / 61-3 (브라우저에서 링크 끌어 놓기, 원격 저장소 시작 알림,
  설치기 exe·SmartScreen), 62-7 (Rigify 켜기 확인 대화상자 — 팝업 확인 버튼은 시뮬레이션해도 사용자 환경설정에 애드온을 켬).
- **시뮬레이션 가능, 아직 안 옮김 (58)**: 나머지 (59-2, 59-4..6, 59-8, 59-9, 60-2..4, 62-1..6, 63-2..4, 63-6, 64-1..3, 64-5, 65-2..5, 66-1, 66-3,
  67-2..5, 68-2, 68-4..6, 69-2, 69-4, 69-5, 70-2, 72-1, 72-3, 72-4, 73-2, 75 없음, 76-1..4, 77-1, 77-3, 78-1, 78-2, 78-4, 78-5, 79-1, 79-2).
  대부분은 그 step 의 GUI 테스트 (gui_step59 … gui_step79) 가 핵심 동작을 이미 확인하지만 항목 문구 전부 (메뉴·셸프·툴팁 경로, 시각
  요소) 는 아님 — 다음 정리 후보.

## 검증

- GUI `tests/gui/gui_manual_sweep.py` 46/46 (13 항목). 처음 실행 43/45 → 테스트 쪽 수정 (이름 카운터, 편집 모드 Separate 는 loose parts,
  Stacked 안내는 report) 뒤 통과; 기능 코드는 바꾸지 않음.
- `docs/manual_checks.md`: 348 항목 중 [x] 13 (전엔 0).
- 전체: 헤드리스 677/677, GUI (기본 배율) 667/667 (621 + sweep 46), dogfood 47/47 (콘솔 0).

## 남은 것

- 「시뮬레이션 가능, 아직 안 옮김」 58 항목 (위 분류) — 다음 정리 때 같은 파일에 `[M<step>-<n>]` 으로 이어 붙이면 됨.
- step 2–58, 80–87 절 (247 항목) 은 이번 범위 밖 (step 82–87 항목은 그 step 의 GUI 테스트가 대부분 다룸; 문구 전부 확인 뒤 체크).
- 사람 판단 23 / 환경 불가 7 항목은 손 확인으로 남음.
- 재점검 5차 backlog (81–88) 끝. 다음 할 일은 사용자 결정 (배포 decision 11) 또는 재점검 6차.

