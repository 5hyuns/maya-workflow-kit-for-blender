# Step 159 — Skin weights export / import + Skeleton gaps

Backlog `autodrive_bmk/backlog_155.json` #5.

## 계획

- 레인 W (서브에이전트, `operators/deformer_weights.py`): Maya `deformerWeights` XML 을 mayapy 로 측정해
  `research/maya/re/skin_weights_159.md` 에 기록, 같은 구조로 쓰고 Maya 파일을 읽는 Deform > Export / Import Weights.
- 레인 L (서브에이전트, `operators/joint_labels.py` + `skin.py` Mirror): Joint Labelling (bone ID 속성), 라벨 그리기,
  Rename Joints From Labels / Label Based on Joint Names, Mirror Skin Weights Label 연결, Enable / Disable Selected IK Handles
  — Maya MEL 읽기 + mayapy 측정 → `research/maya/re/joint_labels_159.md`.
- 메인: 두 레인 파일 stub 등록 (충돌 방지), 메뉴 연결 · 알림 · Reset Default Weights · 문서 · GUI.
- 두 레인은 파일이 겹치지 않아 동시에 (포그라운드 Agent 2 개, Blender 샌드박스 w159 / l159).

## 한 것

- **Deform > Export / Import Weights** (`allset.export_deformer_weights` / `import_deformer_weights`): Maya
  `<deformerWeight>` XML (headerInfo + world matrix, shape 점 (Maya Y-up cm 객체 공간), 영향마다 `<weights>` 0 아닌 점만)
  그대로 씀 — 정밀도 9 자리 (Maya 기본 3), Maya 파일 (XML / JSON) 읽음. Import Index (Maya 기본: 파일의 영향 = 전체
  교체, 없는 영향은 유지, 모르는 이름은 Maya 경고) / Nearest (파일 점 위치), Normalize 기본 on. 기본 폴더 = 프로젝트 `data`,
  이름 `<deformer>.xml`. skinClusterN (Armature modifier) + 킷 deformer (자기 vertex group, source baseLayer).
- **Skeleton > Joint Labelling** 전체 (38 항목): `allset.joint_label(side / type)` (bone ID 속성 `allset_side` / `allset_type` /
  `allset_other_type` / `allset_draw_label`, Maya 값 그대로; 첫 Label Shoulder / Label Hip = Maya 팔 / 다리 묶음 라벨
  FBIKLabelArm / Leg; Left / Right / 손가락 · 발가락 = 아래 관절까지 — Maya MEL 규칙), Toggle Selected / Show All / Hide All
  Labels, Rename Joints From Labels (`LeftHip`, 겹치면 `LeftHip1`), Label Based on Joint Names (Maya 문자열 규칙, 24 이름
  mayapy 측정). 뷰포트 라벨 = POST_PIXEL ("Hip (L)", Maya 색 Left #747bca / Right #8ec28d / Center #2e0f46 / None #a70009).
- **Mirror Skin Weights**: Influence Association 1 / 2 (Closest joint 기본 / Label / None) — Label 은 반대 쪽 같은 type
  끼리. Closest joint 는 Maya 처럼 거울 위치에 가장 가까운 관절 (전에는 정확히 대칭일 때만 짝 — delegated: Maya 측정값을
  따름, 대칭 골격은 결과 같음).
- **Enable / Disable Selected IK Handles** (`allset.ik_handle_enable`): 선택한 ikHandle 이 끄는 IK constraint 의
  influence 1 / 0 (mayapy: Maya `ikHandle -e -eh/-dh` = ikBlend 1 / 0; delegated: 브리프의 "mute" 대신 측정값 — mute 는
  기존 solverEnable 대응으로 남김). 손잡이 없이 고르면 Maya "No handle selected." 오류.
- **Skin > Reset Default Weights** (`allset.reset_skin_weights`): 지금 묶인 관절로 closest distance bind 가중치를 다시.
- 알림: Interactive Bind Skin / Tool → Bind Skin + Paint Skin Weights, Export / Import Weight Maps → Deform > Export /
  Import Weights. 낡은 "Skeleton/Joint Labelling" 알림 제거.
- 근거: `research/maya/re/skin_weights_159.md`, `research/maya/re/joint_labels_159.md` (MEL 파일:줄 + mayapy 측정, 코드
  복사 없음).

## 검증

- 레인 W `tests/test_step159_weights.py` 10/10: Maya XML 샘플 2 개 파싱, 왕복 export → 그룹 삭제 → import 1e-6, Maya 9 자리
  파일을 같은 평면에 Index 로, 영향 유지 / 모르는 이름 경고, Nearest (재정렬 + cm 장면, 축 · 단위), 킷 Bend 왕복, 연산자 양방향.
- 레인 L `tests/test_step159_labels.py` 15/15 (라벨 · 묶음 규칙 · 이름 바꾸기 · 이름에서 라벨 · 토글 · Mirror Label · IK).
- `tests/test_step159_menus.py` 2/2 (메뉴 경로 · enum 값 · 알림, Reset Default Weights 가 bind 가중치를 되돌림).
- 헤드리스 전체 **1487 / 1487**.
- menu_count: Skeleton 13 → **51 / 54**, Skin 18 → **19 / 28**, Deform 28 → **30 / 74**, Rigging 메뉴 세트 71 → **112 / 190
  (59 %)**, 전체 675 → 720 / 1486 (48.5 %), 알림 없는 회색 0.
- GUI `-k gui_step159,gui_step58_skin` 9/9 — 새 `gui_step159_labels`: Label Left + Hip + Toggle → "Hip (L)" 가 joint2 옆에
  그려짐 (픽셀 변화 0.52, 스크린샷 `tmp/shots159/gui_step159_labels.png` 눈으로 확인: joint3 도 Left 라 "None (L)").
- GUI 전체 묶음은 돌리지 않음 (사용자 규칙: release prep 에서만).

## 남은 것

- 킷이 쓴 XML 을 Maya 가 다시 읽는지 mayapy 확인은 아직 (구조는 Maya 그대로).
- Import 의 Over / barycentric / bilinear 방법 없음; Nearest 의 공간 (객체 vs 월드) 미확정 [U].
- Skin: Move Skinned Joints, Move Weights to Influences, Substitute Geometry, Bake Deformation, Weight Post Normalization,
  Interactive Bind — 회색 + 알림. Skeleton: IK Handle Snap, IK/FK Control, HumanIK — 회색 + 알림.
- 라벨 글자 크기 / 위치는 추정 (11 px, 관절 위 10 px).
