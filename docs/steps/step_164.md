# Step 164 — Maya DAG rules for parents

Backlog `autodrive_bmk/backlog.json` #1 (audit 11, `docs/steps/step_163_remaining.md` §4 BS1, score 9).

## 계획

- 먼저 측정 (`research/maya/re/dag_164.md`):
  - Maya mayapy (`research/scripts/dag_164_mayapy.py`): 부모 visibility off → 자식 그려짐 (`MDagPath.isVisible`) / 자기 채널, h ·
    Ctrl+H · Shift+H 를 그룹에, delete / doDelete, exportSelected (ma / obj / fbx), display layer.
  - Blender 헤드리스 (`tmp/s164/dag_blender_probe.py`): 부모 `hide_viewport` / `hide_set` → 자식 `visible_get()`, `object.delete`.
- 모델 (delegated): Maya 의 "그려짐" = 자기 Visibility (`hide_viewport`, step 129) ∧ 레이어 V ∧ 모든 조상. Blender 는 상속이 없으니
  조상이 숨으면 자손에 view-layer `hide_set` + 표시 `allset_hidden_by_parent` (자손의 Visibility 채널은 그대로 1 = Maya). 킷이 숨긴
  것만 되돌림 (레이어 / 사용자의 `hide_set` 은 안 건드림). depsgraph 핸들러 + 킷 숨김 · 레이어 직후 `dag.sync`.
- Delete / Export Selection / Isolate = 선택 + 자손 (`dag.hierarchy`).
- 순차 진행 (레인 없음): 모든 변경이 한 모델 (`operators/dag.py`) 에 기대고 파일이 작아 나누면 합치기가 더 큼 (delegated).

## 측정 결과

- Maya: 부모 visibility 0 → 자식 채널 1, 그려지지 않음; h / Ctrl+H 가 그룹만 씀 (Ctrl+H 는 선택 해제); 스스로 숨긴 자식은 부모를
  다시 보여도 숨김; delete / doDelete = 그룹 · 자식 · shape · polyCube 노드 모두; exportSelected (ma / obj / fbx) = 그룹 + 자식;
  레이어 멤버 = 그룹만이지만 V off → 자식도 안 그려짐. Isolate 는 mayapy 에서 못 잼 (모델 패널 필요) — [K].
- Blender: 부모 `hide_viewport` / `hide_set` → 자식 보임; `object.delete` → 자식이 부모 없이 남음.

## 한 것

- `operators/dag.py`: `hierarchy`, `hidden_self` / `hidden_by_ancestor`, `sync` (+ depsgraph / load_post 핸들러, `release_all` =
  끌 때 되돌림), `delete_hierarchy` (자손부터 지우고 users 0 data 도 지움), `selected_hierarchy` (잠깐 자손도 선택, 끝나면 되돌림),
  `allset.delete`, `allset.isolate`.
- 연결: Object Mode Delete / Backspace = `allset.delete` (IC `object.delete` 대신), Outliner Delete / Backspace = `outliner.delete
  (hierarchy=True)`, Edit > Delete · Channel Box Delete Node = `allset.delete`; Ctrl+1 · Panels > Isolate Select > View Selected = `allset.isolate`
  (mapping 행 `ToggleIsolateSelect`, docs/keymap_mapping.md 다시 생성); File > Export Selection (모든 형식, .blend 포함) 과 Cache >
  Alembic / GPU Cache > Export Selection (이제 킷 Export Selection 창, ABC) 가 자손 포함; h / Ctrl+H / Alt+H / Shift+H 뒤
  `dag.sync`, Alt+H 는 선택의 계층 (자손 · 조상) 을 남김; 레이어 V 가 멤버의 자손도 숨김.

## 검증

- 헤드리스 `test_step164_dag` 9/9: group1 > pCube1 에서 h → pCube1 안 그려짐 + 채널 켜짐, h 다시 → 보임; CB Visibility 와 스스로
  숨긴 자식 (Maya 처럼 남음); Ctrl+H 선택 해제 + 되돌림; Alt+H 가 선택 계층을 남김; 레이어 V; Delete → pCube1 · pCubeShape1 없음 +
  메뉴 · Delete 키; FBX Export Selection 다시 가져오기 = 2 오브젝트 (group1, pCube1), 선택 되돌림; isolate 선택 범위 + Ctrl+1 키;
  끌 때 `release_all`. 관련 (keymap / step16 / step10 / step129 CB / file I/O / step161) 101/103 → 실패 2 (Ctrl+1 매핑 행과 옛
  step16 기대값) 고침. 헤드리스 전체: 아래 「최종」.
- GUI `gui_step164_dag` 9/9: 키 Ctrl+1 이 로컬 뷰 + pCube1 픽셀 그대로 (차 0.000) · pCube2 사라짐 (0.188), Ctrl+1 다시 = 해제, 키
  h → group1 숨김 + pCube1 안 그려짐 + 채널 켜짐, h 다시 → 보임. 관련 `gui_step16_undo_visibility`, `gui_step129_views`,
  `gui_step161_views` 통과 (44/45 에서 step164 파일만 고침). 스크린샷 `tmp/s164/gui_step164_isolate.png` 직접 봄 (pCube1 만 남음).
- 측정 함정: GUI 에서 `Object.local_view_get(space)` / `visible_in_viewport_get(space)` 가 로컬 뷰 안의 물체에도 False — 화면 픽셀로 판정.

## 남은 것

- Isolate 의 Maya 측 규칙은 [K] (mayapy 에 모델 패널 없음); GUI Maya 캡처로 확인할 수 있음.
- 부모가 숨으면 자손은 Blender 에서 선택할 수 없음 (Maya 는 Outliner 에서 선택 가능) — Blender `hide_set` 한계.
- Blender 의 자체 H / Alt+H (킷 키맵 밖) 나 Outliner 눈 아이콘은 `hide_set` 을 쓰므로 자손 규칙에 안 들어감 (킷 h 와 CB Visibility 만).
- 큰 장면에서 depsgraph 마다 `sync` 가 모든 물체를 한 번 훑음 (O(n)) — 체감 확인은 manual_checks.
