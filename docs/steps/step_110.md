# Step 110 — Modeling and rigging function gaps (daily items)

Backlog: step_98.md #23 (normals, Edit Mesh Detach / Flip / Circularize / Edit Edge Flow / Wedge, Mesh Tools Connect /
Make Hole / Append), #28 (Skeleton / Skin / Deform gaps). Maya behaviour measured first with mayapy:
`research/maya/re/modeling_rigging_110.md`.

## 계획

Already mapped before this step (step 101 / 63 / 58, kept): Soften / Harden (polySoftEdge angle 30, mayapy), Lock /
Unlock Normals, Set to Face / Average / Conform / Reverse, Vertex Normal Edit Tool, Detach, Flip, Wedge, Append to
Polygon, Insert Joints (`armature.subdivide`), Normalize / Prune / Set Max Influences, Remove Influence. Menu working
share before: Modeling 47 %, Rigging 36 % (`tools/menu_count.py`), so the step is about Maya-correct results.

1. **Circularize** (`maya_kit.circularize`, replaces To Sphere): selected faces → their border loops, edges → their
   loops, vertices → loops through selected edges; per loop: centroid, plane normal (Newell), radius = mean
   distance, vertices evenly spaced keeping the loop's mean angular offset; interior vertices of a face selection
   move with the same radial scale (relaxInterior 1 — the measured centre vertex stays put). Object mode = every
   border loop of the mesh (menu_map.OBJECT_MODE already says all components).
2. **Edit Edge Flow**: Catmull-Rom (0.951 on the measured sphere, Maya 0.9983) → cubic Hermite between the two ring
   neighbours with tangents along the circle through (outer neighbour, neighbour, other neighbour) and length = the
   chord (0.9971). Straight neighbours stay straight.
3. **Connect** (`maya_kit.connect`): edges → split at midpoints and joined across each face with two cut edges
   (`bmesh.ops.subdivide_edges`, 1 cut); vertices → `connect_vert_pair` per face. Counts as measured.
4. **Make Hole** (`maya_kit.make_hole`): two selected faces of one mesh, the active one is the stamp: both faces go,
   the outer loop is bridged to the stamp loop with quads (Blender faces can't have holes); stamp vertices keep their
   position (Maya mode 6).
5. **Skeleton** (`operators/rig_maya.py`): Reroot (bones on the path to the selected joint reversed, parents
   re-pointed, joint positions unchanged), Set / Assume Preferred Angle (pose bone ID property
   `maya_kit_preferred_angle`, rotation of the bone and its children; Blender IK does not read it — notice), IK Spline
   Handle (two selected joints → `curve1` NURBS 4 CVs = 1 span degree 3, ends on the joints, middle CVs a
   least-squares fit of the joint polyline; Spline IK constraint `ikHandle1`, no stretch).
6. **Skin**: Hammer (selected vertices ← average of edge neighbours' weights), Add Influence (vertex group for the
   selected joint, weight 0 everywhere), Remove Influence (the selected joints' groups removed, weights renormalised),
   Remove Unused Influences (groups of bones with zero weight everywhere).
7. **Deform**: Cluster (`cluster1` Hook modifier + `cluster1Handle` empty at the components' centroid), Nonlinear
   Bend / Twist / Squash / Flare (Simple Deform with a `bend1Handle` empty at the bounding-box centre, scale = half
   height, as the deform origin, limits = the handle's −1..1 range), Soft Modification (`softMod1` Hook on the whole
   mesh + `softMod1Handle` at the selection, falloff radius 5 Maya units, curve falloff = (1 + cos πd/r) / 2).
8. Verify: headless tests against the mayapy numbers; menu working share Modeling ≥ 35 %, Rigging ≥ 35 %.

Unknowns kept open: Maya's exact edge-flow and IK-spline curve-fit rules (step_110.md 「검증」 gives the residuals).

## 한 것

- mayapy 측정 명세 `research/maya/re/modeling_rigging_110.md` (Circularize, Edit Edge Flow, Connect, Make Hole, Reroot,
  Preferred Angle, IK Spline Handle, Hammer / Add / Remove Unused Influence, Cluster, Nonlinear 4 종, Soft Mod).
- 모델링 (`operators/poly_maya.py`, `menu_items.edge_flow`):
  - **Circularize** = `maya_kit.circularize` (To Sphere 대신): 면 → 테두리 루프, 모서리·정점 → 닫힌 루프, 오브젝트 모드 = 메시
    테두리. 중심 = 무게중심, 반지름 = 평균 거리, 등간격, 루프의 평균 각 위치 유지 (Maya 측정값 그대로).
  - **Edit Edge Flow**: Catmull-Rom → 링 이웃 사이 Hermite (접선 = 바깥 이웃을 지나는 원의 접선, 길이 = 현).
  - **Connect** = `maya_kit.connect`: 모서리 → 가운데에서 잘라 면마다 잇기, 정점 → 같은 면 안에서 잇기 (Maya 개수 일치).
  - **Make Hole** = `maya_kit.make_hole` (새로): 대상 면 + 스탬프 면 (활성) → 두 루프를 쿼드로 이음, 스탬프 정점 위치 유지.
- 리깅 (`operators/rig_maya.py`):
  - Skeleton: **Reroot Skeleton** (경로의 본을 뒤집고 부모 재지정, 조인트 위치 그대로, 본 이름 유지), **Set / Assume Preferred
    Angle** (자식 포함, 포즈 본 ID 속성), **Create IK Spline Handle** (`curve1` NURBS 4 CV = 1 span 3 차, Spline IK `ikHandle1`,
    늘어남 없음).
  - Skin: **Hammer Skin Weights** (이웃 평균), **Add Influence** (가중치 0), **Remove Influence** (선택 조인트 그룹 제거 +
    재정규화, 전엔 활성 그룹만 지웠음), **Remove Unused Influences**.
  - Deform: **Cluster** = Hook `cluster1` + `cluster1Handle` (선택 무게중심 / 오브젝트 중심; 전엔 Blender `hook_add_newob` 의
    "Empty"), **Nonlinear** Bend / Twist (새로) / Squash / Flare = Simple Deform + `<type>1Handle` (bbox 중심, 높이 절반 크기,
    deform origin), **Soft Modification** = 메시 전체 Hook `softMod1` + `softMod1Handle`, 반경 5 × Maya 단위, 코사인 곡선
    (전엔 비례 편집 토글).
- 메뉴: 14 항목 매핑 (`menu_map` step 110 블록, 예전 항목 6 개 대체), 결과가 다른 5 개는 `notices.NOTICES`, 범주 안내 2 개
  (Skeleton, Mesh Tools) 에서 이제 되는 기능 문장 제거.

delegated:
- Reroot 은 본 이름을 그대로 둠 (Maya 는 조인트 = 점이라 이름이 점을 따라감; Blender 본은 선분이라 경로의 본 방향만 뒤집음).
- Preferred Angle 은 저장·복원만 (Blender IK 솔버는 읽지 않음, 안내).
- Make Hole 은 구멍 난 면 대신 쿼드 4 개 (Blender 면은 구멍을 가질 수 없음).
- Circularize 의 relaxInterior: 내부 정점은 움직이지 않음 (측정 장면의 중심 정점도 그대로였음).
- IK Spline 커브: 끝 CV 두 개는 Maya 와 같고, 가운데 CV 두 개는 조인트 폴리라인 최소제곱 맞춤 (Maya 규칙 미복원, 아래).

## 검증

- 헤드리스 `tests/test_step110_model_rig.py` 16/16 (mayapy 값과 비교):
  - Circularize 반지름 1.2071, 8 점 위치 = Maya, 중심 정점 고정, 위상 그대로.
  - Edit Edge Flow 구 적도 0.9971 (Maya 0.9983, 차 0.0012; 이전 규칙 0.951), 직선은 그대로.
  - Connect 10 / 7 / 15, 링 12 / 10, 대각 정점 7 면 = Maya. Make Hole 정점 8, 스탬프 위치 유지.
  - Reroot 부모 관계 = Maya, 조인트 위치 그대로. Preferred Angle (0, 0, 30) 저장·복원, 자식 0.
  - IK Spline: 4 CV, 차수 4 (3 차), 끝점 = 조인트, 체인 3. 가운데 CV (−1.924, 6.111), (4.704, 7.284) vs Maya (−1.377, 6.758),
    (3.940, 6.885) — Maya 맞춤 규칙 (균일 / 현 / 구심 보간, 조밀 폴리라인 최소제곱, 자연 스플라인 후 재구성) 모두 불일치.
  - Hammer (0.9808, 0.0192) = Maya. Add Influence 가중치 0, 미사용 제거, Remove 재정규화.
  - Cluster 핸들 = 무게중심 (3, 0, 0.5) [Maya (3, 0.5, 0)], 해당 점만 움직임; 오브젝트 모드 = 중심.
  - Nonlinear 4 종 핸들 = bbox 중심, 크기 2 (높이 4), 중립값.
  - Soft Mod 거리 0–5 높이 1, 0.9045, 0.6545, 0.3455, 0.0955, 0 = Maya (소수 넷째 자리까지).
  - 메뉴 작동: Modeling 164 / 349 = **47 %**, Rigging 75 / 190 = **39.5 %** (전 36 %), 전체 44.5 %.
- 헤드리스 전체 **846/846** (99 파일), GUI 전체 **1074/1074** (86 파일).
- REA: `PolyEngine.dll` (polyEditEdgeFlow) 열기까지 됨, 디컴파일 제공자 없음 (Ghidra 미설치·IDA 미설정) → 막힘, 관찰 기반으로 진행
  (`research/maya/re/modeling_rigging_110.md` §9).

## 남은 것

- Edit Edge Flow 와 IK Spline 커브 맞춤의 Maya 정확한 규칙 (REA 제공자 설치 후 PolyEngine.dll / ikSplineSolver 분석).
- Make Hole 의 다른 merge 모드 (first / middle / second), Circularize 의 옵션 (radialOffset, twist, divisions, supportingEdges),
  Soft Mod 의 falloffMode surface / 마스크, Cluster 가중치 페인트, Nonlinear 핸들의 low / high bound 를 Channel Box 에서.
- Skin: Move Weights to Influences, Enable Weight Post Normalization, Joint Labelling 39 (안내만).
- Flip (dR_performSymmetryFlip) 은 GUI Maya 측정이 필요 (지금은 Local X 미러).
