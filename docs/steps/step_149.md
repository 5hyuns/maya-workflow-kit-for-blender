# Step 149 — Deformed selection wire, names, bind (#91 #93 #94)

## 계획

측정 먼저:

- **#91**: `ui/selection_wire.py` 는 물체마다 edge batch 를 캐시하고 `depsgraph_update_post` 의 `is_updated_geometry` 에서만
  버린다. 프레임이 바뀌면 (재생, 스크럽, `frame_set`) depsgraph 는 그 처리기 없이 평가되어 첫 평가 모양이 남는다.
- **#93**: `operators/naming.apply_maya_name` 은 모든 mesh 이름을 "쓰임" 으로 센다. Blender 는 물체를 지워도 mesh 를 users 0 으로
  파일 저장 / purge 때까지 남기므로 `pCubeShape1` 이 남아 다음 큐브가 `pCube2`.
- **#94**: 킷 Bind Skin = Blender bone heat (`ARMATURE_AUTO`). 킷 기본 실린더 (높이 분할 1, 정점은 위 / 아래 고리뿐) 로 재현:
  bone heat 는 mesh 가 닿지 않는 joint 를 떨어뜨린다 (cm / m 장면 모두, 스케일 (1, 1, 1) 이면 joint3 없음; 감사 9 에서는
  Scale Y ~8 에서 joint2). 같은 실린더를 Maya 는 세 joint 모두에 묶는다. Maya 의 기본 Bind method 는 Closest distance
  (option_boxes_140.md:32). mayapy 로 측정 (`research/scripts/skin_bind_149_mayapy.py`, 명세
  `research/maya/re/skin_bind_149.md`): w_i = d_i^-4 (d_i = 월드 정점에서 joint i 의 자식 joint 까지 선분들 중 최소 거리, end
  joint 는 점), 큰 순서로 max influences 개, 정규화 — 측정한 모든 정점에서 오차 ≤ 2e-5 (dropoff 1 / 4 / 10, max 2, 가지 skeleton).

결정 (delegated):
1. 프레임 변경 (`frame_change_post`) 때 시간에 따라 모양이 바뀔 수 있는 물체 (`time_dependent`: modifier, shape key, 애니메이션
   있는 data) 의 batch 만 버린다 — 정적 mesh 는 캐시 유지 (빠름). 평가 mesh 를 다음 그리기에서 다시 읽는다.
2. 이름: 킷이 쓰려는 이름 (`<base><N>`, `<base>Shape<N>`) 을 가진 orphan (로컬, users 0, fake user 없음 — Blender 가 저장하지
   않는 것) 을 이름 정하기 전에 지운다 (`naming.drop_orphans`). Delete 경로마다 고치는 대신 이름 쪽에서 — 메뉴 · 키 · Outliner
   어떤 Delete 뒤에도 같다. fake user / 사용 중인 data 는 그대로 "쓰임".
3. Bind Skin 기본 = Maya Closest distance (월드 공간이라 물체 스케일 무관, 모든 joint 에 그룹), Bind Skin Options 에
   "Bind method" (Closest distance / Heat Map = Blender bone heat). Armature modifier 는 `modifiers.new` (Blender 의 parent
   경로와 같은 스택 위치), 부모 설정 없음.

순서: 세 이슈가 서로 다른 파일 (selection_wire / naming / skin) 이지만 각각 작고 같은 테스트 샌드박스를 쓰므로 메인에서 차례로
(PC 부하 규칙: Blender ≤ 2, mayapy 측정이 #94 의 선행).

## 한 일

- `ui/selection_wire.py`: `time_dependent`, `_on_frame` (`frame_change_post`).
- `ui/selection_wire.py`: 선택된 격자도 Maya 와이어 (`WIRE_TYPES`, `lattice_edges` = U / V / W 격자 이웃, 평가된 `co_deform`).
  Maya 값: displayColor lattice -active 16 (흰색), lead 19 (초록) — `research/maya/screens/_maya_ui_dump.json` (step 148 남은 것).
- `tests/gui/gui_step91_view_chrome.py`: Adjust Last Operation 을 여는 키를 Shift+H → Alt+W 로 (step 147 이 Shift+H 의 패널을 없앰;
  전체 GUI 묶음에서 실패 2 로 드러남, 149 와 무관).
- `operators/naming.py`: `orphan`, `drop_orphans`, `apply_maya_name` 이 먼저 지움; `operators/mesh_maya._maya_rename` 도.
- `operators/skin.py`: `BIND_METHODS`, `joint_segments`, `closest_distance_weights` (numpy), `_bind_closest`, `bind_skin(method=)`,
  `allset.bind_skin` 의 `bind_method`; `operators/option_windows_rig.py` Bind method 칸.
- 테스트: `tests/test_step149_wire_names_bind.py`, `tests/gui/gui_step149_wire.py`; `test_step140_rig` 의 Bind Skin 칸 목록.
- 근거: `research/maya/re/skin_bind_149.md`, `research/scripts/skin_bind_149_mayapy.py`.

## 검증

- mayapy 측정 → 규칙 맞춤 (`closest_distance_weights`) 모든 측정 정점 오차 ≤ 2e-5 (실린더 2 종, 평면 dropoff 1 / 4 / 10,
  max 2, 가지 skeleton).
- 헤드리스 `test_step149_wire_names_bind` 5/5: Maya 평면 값 6 점 + max 2 + joint 위 정점, #94 재현 실린더가 joint1 / 2 / 3 모두
  + 아래 고리 0.49994 / 0.49994, 위 고리 0.99975 / 0.00024 (Maya 값 ±1e-4), Heat Map 선택 가능 + 옵션 창 칸, #93 Delete 뒤
  pCube1 / pCubeShape1 다시 (fake user data 는 계속 쓰임 → pCube3), #91 `frame_set` 뒤 변형 물체 batch 만 버림 + 평가 mesh 가
  움직임. 관련 skin / 옵션 창 파일 (step58 / 140_rig / 129_audit_p1 / 103) 통과 (step140 Bind Skin 칸 목록에 Bind method 추가).
- 헤드리스 전체 1329/1329.
- 격자 와이어 추가 뒤 헤드리스 `test_step149_wire_names_bind` 6/6 (격자 edge 36 개 = 이웃만), step58_skin / step140_rig 통과.
- GUI 전체 묶음 (커밋 전 한 번): 1595 통과 / 실패 3 / 139 파일 (GUI_SKIP 2) — 실패 = gui_step149_wire (격자 단계가 격자 코드 전
  zip 으로 돎) + gui_step91_view_chrome 2 (위 Shift+H). 다시 빌드 뒤 `-k step149,step91_view,step58_skin,step129_rig_paint,
  step134,step142_ui,step47` 81/81.
- GUI `gui_step149_wire` 5/5 (UI 1.25): 재생 중 (프레임 83) / 멈춘 뒤 (프레임 10) 초록 lead wire 가 변형된 아래 고리 위
  (점 95 %), rest 고리 위 0 %. 스크린샷 `tmp/shots149/gui_step149_stopped_125.png` 직접 봄 (옆 뷰에서 굽은 실린더 위 초록 선); 격자 lead 초록 edge 중점 78 %, `gui_step149_lattice_125.png` 확대해 Blender 격자 선과 겹침 확인
  (주황은 1 px 테두리만 — 메쉬의 Blender 윤곽선과 같은 상태).

## 남은 것
- 선택된 격자 밑의 Blender 주황 선이 1 px 비침 (Python 은 Blender 의 물체 윤곽 / 격자 그리기를 끌 수 없음, 메쉬와 같음).

- `ui/component_colors.py` (편집 모드 성분 색) 도 같은 캐시 방식 — 편집 모드에서 재생하는 경우는 드물어 그대로 둠.
- Bind 는 skeleton 의 rest 위치 기준 (Maya 는 지금 포즈가 bind pose). Closest in hierarchy / Geodesic Voxel 은 없음.
