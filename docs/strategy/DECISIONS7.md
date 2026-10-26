# DECISIONS7 — 설계 결정 7개 (know-your-unknowns, 2026-10-26)

대상: Maya Workflow Kit (`C:/Repos/blender-maya-kit`, 읽기만). 기준 Maya 2026, Blender 4.5 (지원 4.5–5.2).
방법: know-your-unknowns 플러그인 0.8.1 의 `loop` 중 이 일에 맞는 단계만 썼다 — ② blindspot(알려진 것 / 가정 / 모르는 것), ⑤ 위험한 가정 하나를 가장 싸게 확인하는 실험, ⑥ tweakable plan(선택지·되돌리기 비용·뒤집을 신호). 사용자 지시가 "질문하지 말고 끝까지"라서 ③ interview, 단계별 체크포인트, scorecard 행은 **건너뛰었다**(scorecard 의 두 질문 "몰랐던 것을 드러냈나 / 결정을 바꿨나"는 사용자만 답할 수 있어 비워 둔다).
실험 스크립트·결과: `docs/strategy/kyu7/` (`e1_fbx.py`…`e6_read.py`, `m2.py`–`m4.py`, 결과 `out/*.json`). 모든 Blender 실행은 `--factory-startup` + `BLENDER_USER_*` = `kyu7/cfg/*`(미리 만듦), mayapy 는 `MAYA_APP_DIR` = `kyu7/mayaapp`. GUI Blender 는 E5 한 번(스스로 종료). 표기: [실측] [파일] [웹] [추정] [U].

---

## 먼저: 요청이 작아 보인 이유 vs 실제로 들어간 곳

- **요청**: 권장안이 이미 적힌 7개 결정에 도장 찍기.
- **실제**: 실험 3개가 전제를 바꿨다.
  1. **쿼터니언은 예외가 아니라 Blender 의 기본값이다.** 새 본, FBX 로 가져온 본은 모두 `QUATERNION` 이다. Rigify 사람 리그에서는 보이는 컨트롤 212개 중 174개(82 %)가 쿼터니언이다 [실측 E4]. 지금 키트는 이 본들의 Rotate 칸을 숨기고, S 키가 회전을 키하지 않는다. 그래서 L19 는 "사슬 ⑤의 한 고리"가 아니다. 받은 리그로 일하는 모든 사용자를 막는 문제다 → **순서를 당긴다**.
  2. **Maya 그대로의 pick walk 는 Rigify 에서 쓸 수 없다.** 보이는 컨트롤 212개 중 134개(63 %)는 바로 위 부모가 숨은 MCH/ORG 본이다 [실측 E4]. Maya 는 숨은 노드와 숨은 디스플레이 레이어 노드로도 들어가고, Tag As Controller 는 부모를 **스스로 정하지 않는다**: 태그만 붙이면 여전히 DAG 를 따라 숨은 조인트로 들어간다 [실측 mayapy M3, M4]. 따라서 "Maya 그대로 + 컨트롤러 태그"만으로는 Rigify 사용자가 컨트롤마다 손으로 Parent Controller 를 해야 한다.
  3. **FBX 후처리는 생각보다 싸다.** Blender 에 들어 있는 `io_scene_fbx.parse_fbx` / `encode_bin` 은 4.5 와 5.0 이 바이트 단위로 같고, 5.1–5.2 는 assert 괄호와 주석만 다르다. FBX 애드온을 꺼도 import 된다. 이 모듈로 다시 쓴 파일을 Maya 2026 에서 열면 jointOrient 에 방향이 들어가고 rotate 가 0 이며, 월드 위치가 f1·f10 모두 원본과 같다 [실측 E2 + M2].

알려진 것 / 가정 / 모르는 것은 결정마다 아래에 적었다.

---

## 결정 1 — 컨트롤: **본 Custom Shape** (커브 오브젝트는 "모양 원본"으로만 남김) · 확신도 **높음-중**

**알려진 것**
- 받은 리그는 모두 Custom Shape 컨트롤이다: Rigify, Auto-Rig Pro, Game Rig Tools 가 쓰는 컨트롤 리그 [웹: cgdive Game Rig Tools, ARP 문서]. 그래서 키트는 Custom Shape 컨트롤을 어차피 Channel Box / S / pick walk / 선택 우선순위로 다뤄야 한다.
- FBX: 컨트롤 오브젝트는 Custom Shape 원본이든 컨스트레인트용 컨트롤 커브든 Export All 에 넣으면 **Mesh 로 나간다**(`spine_shape`, `head_ctrl` → Model "Mesh") [실측 E1]. 두 안 모두 `object_types` 에서 커브('OTHER')를 빼야 하므로 FBX 쪽에서는 차이가 없다.
- Blender FBX 익스포터는 프레임마다 평가된 포즈를 샘플한다(bake_anim). 컨트롤 본이든 커브 오브젝트든, 컨스트레인트로 움직이는 디폼 본은 따로 굽지 않아도 나간다 [추정: 익스포터가 프레임마다 샘플하는 방식에서 나온 결론. E1 에서 커브 내용은 확인하지 않음 — L11 테스트에서 확인].

**가정 (가장 위험한 것 먼저)**
1. "Maya 사용자 손이 Custom Shape 에서도 맞는다" — 오브젝트 모드에서 컨트롤을 클릭하면 바로 그 본이 선택되는가. 결정 16(자동 Pose)과 `select_priority` 의 조인트 히트는 **본 팔면체 폭**(`BONE_WIDTH`)으로 판정한다. Custom Shape 의 그려진 와이어로 판정하지 않는다 [파일 `bmk-pr125/src/allset/operators/select_priority.py:22-40`]. → 구현 조건이 하나 생긴다(아래 메모).
2. Maya 습관(Group / Freeze / offset 그룹 / `parent -s`)이 본 위에서 번역되는가 — 그룹 = 부모 본(오프셋 본), Freeze = rest 에 적용. ATTACH_PLAN L1·L3 의 번역으로 충분하다고 본다 [추정].

**선택지별 결과**
| | A Custom Shape | B 커브 오브젝트 + 컨스트레인트 | C 혼합(둘 다 키트가 만듦) |
|---|---|---|---|
| 손 | 클릭 → 본(자동 Pose) — 히트 판정을 와이어로 바꾸면 Maya 와 같음 | Maya 와 가장 같음(오브젝트 모드, 모드 없음) | 사용자가 둘을 구분해야 함 |
| 받은 리그와 같은 길 | **같음**(코드 경로 하나) | 다름(두 경로) | 두 경로 |
| 애니 데이터 | 아마추어 액션 1개 → 클립(L24), NLA, 레이어, 포즈 복사·대칭 그대로 | 컨트롤마다 오브젝트 액션 → 클립·레이어가 흩어짐 | 섞임 |
| 엔진 FBX | 디폼 본만 + 샘플(후처리에서 비디폼 제거) | 같음(커브 제외 필요) | 같음 |
| Maya 왕복 | 컨트롤은 어느 쪽이든 안 감 | 같음 | 같음 |
| 구현 / 되돌리기 | M / 쌈(데이터는 Blender 표준) | M+ / 비쌈(사용자 파일에 오브젝트 리그가 쌓임) | L |

**선택**: A. 키트가 컨트롤을 만드는 모든 길(`cmds.parent(s=True)`, Display as Control Shape, Wireframe Color)은 본 Custom Shape 로 번역한다. 사용자가 손으로 본을 커브 오브젝트에 컨스트레인트하는 길은 막지 않는다. L4 는 이미 그 길을 다룬다. 다만 키트가 그 구조를 만들어 주지는 않는다.

**뒤집을 신호**: 본인 녹화(에셋 하나 끝까지)에서 "컨트롤 클릭이 본을 못 고름 / Pose 들어가고 나가기가 거슬림" 이 AWKWARD 2회 이상 나오면 → 결정 16 쪽을 고친다(그래도 안 되면 B). 또는 Maya 습관 Freeze / 오프셋 그룹을 본에서 재현하지 못해 막힘(BLOCKED)이 나오면.

**구현 메모**: ① `select_priority` 의 조인트 히트에 Custom Shape 와이어 투영(preselect 의 선분 거리 재사용)을 넣는다. `custom_shape` 가 있으면 팔면체 대신 그것으로 판정한다. ② Export All / Selection 에서 Custom Shape 원본과 컨트롤 커브는 빼고(`object_types` 또는 선택 필터), 아마추어는 deform-only 로 내보낸다. ③ Custom Shape 원본 커브는 숨김 컬렉션 + fake user 에 둔다(ATTACH_PLAN L1).

---

## 결정 2 — Y-up: **Z-up 유지, Channel Box 축은 바꾸지 않음 + "위 = Z" 안내** · 확신도: 축을 바꾸지 않는 것 **높음**, 안내 방식 **중**

**알려진 것**
- 첫 1시간 측정 #30(바운스: Translate Y 가 위가 아님)은 AWKWARD 1위다 [파일 FEATURES.md 0-4, IDENTITY.md:88]. 수요는 진짜다.
- 키트 전체가 Blender 축을 쓴다: `cmds_shim` 은 "숫자는 Blender 축 그대로, Channel Box 규약" 이다 [파일 `src/allset/command_line/cmds_shim.py:8`]. Graph Editor 채널 이름, 매니퓰레이터, N 패널, Python 도 모두 Blender 축이다.
- FBX 는 이미 Y-up 으로 변환해 나간다 [실측 E1: GlobalSettings / 메시 −90].

**가장 위험한 가정**: "CB 만 Maya 축으로 보이면 싸고 안전하다." 확인해 보니 **틀렸다.** Maya X→X, Y→Z, Z→−Y 로 놓으면, Blender XYZ 오일러는 Maya 축으로 **xzy 순서 + rz 부호 반전**이 된다(축 치환, 계산으로 확인). 그러면 기본 오브젝트의 Rotate Order 가 Maya 에서 "xzy" 로 보인다. Translate 칸은 Graph Editor 커브, 기즈모 색, cmds, 스크립트와 모두 어긋난다. 비용은 L 이고, 되돌리기는 사용자 키 데이터를 해석하는 방식이 바뀌어 비싸다.

**선택**: 축 치환은 하지 않는다(ATTACH_PLAN (d) 유지). 대신 S 비용의 **안내**를 붙인다:
- CB 의 Translate Y / Z 행 툴팁과 Help Line: "Blender is Z-up: Maya Translate Y = Translate Z here".
- 웰컴 Tip 한 줄.
- Maya 레이아웃 뷰의 축 표시는 기존 그대로.

"두 언어" 원칙(user_decisions 2026-10-26)에도 맞는다.

**뒤집을 신호**: 안내를 넣은 뒤 본인 녹화에서도 Y 로 키하는 실수가 2회 이상 나오거나, 외부 이슈에서 "Y-up 옵션"을 3건 이상 따로 요구하면 → CB 표시 옵션을 다시 검토한다(그때는 Rotate Order 표시까지 포함한 L 비용으로).

---

## 결정 3 — L11 리그 FBX 후처리: **허용. Blender 동봉 `io_scene_fbx.parse_fbx` / `encode_bin` 으로 내보낸 파일을 다시 씀** · 확신도 **높음** (방식), 범위는 **중**

**확인한 실험**
- E1: Blender 익스포터는 rest 회전을 `Lcl Rotation` 에 쓰고 **PreRotation 은 쓰지 않는다**. 아마추어 오브젝트가 `Null` 노드로 남고(rotate −90 / scale 100), `armature_nodetype` 를 바꿔도 이 노드는 사라지지 않는다. `primary_bone_axis='X'` 로 하면 Lcl Translation 이 Maya 와 같은 (5.385, 0, 0) 이 된다.
- E2 + M2 (핵심): 내보낸 파일을 parse_fbx 로 읽어, LimbNode 마다 rest 회전을 `PreRotation` 으로 옮기고(`RotationActive 1`), `Lcl Rotation` 을 0 으로 했다. 회전 커브는 프레임마다 Pre⁻¹·R(t) 로 다시 계산했다(이전 값 기준 compat 오일러). 그 결과를 encode_bin 으로 썼다. Maya 2026 에서 열면:
  - spine jointOrient = (0, 43.6, 0), rotate 0.
  - head jointOrient = (0, −21.8, 0), rotate 0.
  - 세 조인트의 월드 위치가 f1·f10 에서 **원본 파일과 소수 3자리까지 같다**.
  - 원본 파일은 jointOrient 0, rotate 에 방향이 들어간다(= first_hour #39 의 증상).
- 모듈 안정성: 4.5 = 5.0 (md5 같음), 5.1–5.2 는 assert/주석만 다름. FBX 애드온을 꺼도 `from io_scene_fbx import parse_fbx, encode_bin` 이 된다 [실측 e3]. `json2fbx.py` 가 같은 트리 → encode_bin 경로를 쓰는 동봉 도구다.
- 스토어 규칙: exec / eval / sys.path / importlib 없이 일반 import 만 쓴다. 쓰는 곳은 사용자가 고른 내보내기 경로뿐이고, 설정은 건드리지 않는다. → `test_step130_package_scan` 금지 목록에 걸리지 않는다 [추정, 구현 때 스캔 실행].
- 엔진: Maya 가 내보낸 FBX(PreRotation 포함)는 Unity / Unreal 이 가장 많이 받아 본 입력이다. 두 엔진 모두 FBX SDK 로 읽는다 [추정]. Unreal 은 루트 노드 이름이 "Armature" 면 지운다 [웹 krisredbeard 2017]. Blender 쪽 관행으로는 이렇게 하거나 별도 디폼 리그를 쓴다(Game Rig Tools).

**실험이 드러낸 함정**
- PreRotation 은 파일의 `Lcl Rotation` 기본값에서 가져오면 안 된다. 그 값은 **내보낼 때의 현재 프레임 포즈**다. E2 에서 root 가 f10 포즈를 jointOrient 로 가져갔다. rest 는 `bone.matrix_local`(또는 BindPose 행렬)에서 계산해야 한다.
- 후처리한 파일을 Blender 로 다시 가져오면 spine f10 이 0.27 cm 어긋났다. Maya 는 정확했으므로 파일은 맞다. 원인은 Blender 임포터 쪽으로 보이며 L12 의 [U] 다. 원본 파일을 다시 가져왔을 때와의 비교는 아직 안 했다.

**선택지**: A 후처리(선택) / B 익스포터 옵션만(Maya 에서 rotate ≠ 0, skeleton1 −90/100 감수 = 지금의 BLOCKED) / C 키트 자체 FBX 리더·라이터(약 700줄, 의존 없음) / D 익스포터 함수 몽키패치(다른 애드온 내부를 바꿈 → 스토어·안정성 모두 나쁨).
A 를 고르고, C 는 동봉 모듈이 깨질 때의 대안으로 남긴다. `compat.py` 에 `fbx_tree()` 하나를 두고, import 에 실패하면 후처리 없이 내보낸 뒤 결과 줄에 경고를 낸다.

**후처리 범위 (L11 「계획」 에 넣을 것)**:
1. rest → PreRotation + 커브 재계산.
2. 아마추어 Null 노드 제거: 변환을 루트 조인트에 접어 넣는다. 단위는 scale 이 아니라 translation 에 곱해 cm 로 쓴다 [U, 미실험].
3. 비디폼 본 제거(`use_armature_deform_only` 로 먼저).
4. InheritType 2 (segmentScaleCompensate) 는 선택(Blender 본은 스케일 상속이 다름 → mayapy 로 확인 후).

검증: mayapy 왕복(이번 `m2.py` 를 테스트로 승격) 4.5 / 5.2.

**뒤집을 신호**: ① 5.x 새 버전에서 parse_fbx/encode_bin 의 시그니처가 바뀌면 → C(자체 리더·라이터). ② 스토어 심사자가 다른 애드온 모듈 import 를 지적하면 → C. ③ Unity / Unreal 에서 PreRotation 파일이 다르게 보이면(실기 확인 [U]) → 엔진용 프리셋에서는 후처리를 끈다.

---

## 결정 4 — 쿼터니언 본: **오일러로 보이고 쿼터니언으로 씀(받은 리그) + 키트 File > Import 는 Maya 처럼 오일러로 변환 + "Convert to Euler" 버튼(키 포함)** · 확신도 **높음**

**알려진 것**
- Maya 회전 채널은 언제나 Rotate X/Y/Z 다. Maya FBX 가져오기는 쿼터니언을 오일러 키로 resample 한다 [파일 maya2026_anim.md L19, engine_fbx L11-3].
- Blender: 새 본, FBX 가져온 본 = QUATERNION. Rigify 보이는 컨트롤의 82 % = QUATERNION, 나머지는 ZXY 32개, YXZ 6개 [실측 E4]. 키트 조인트는 XYZ [파일 `operators/joints.py:115,491`].
- 키트: 비오일러 본이면 Rotate 칸을 숨기고(`ui/channel_box.py:291`), S 가 회전을 키하지 않는다(`time_keys.py:123-142` 의 `has_channel`).

**가장 위험한 가정**: "오일러 표시가 흔들리거나 뒤집히지 않는다." 확인 결과:
- 입력값을 compat 기준으로 쓰면 2000개 무작위 입력(−360…360°)이 최대 0.002° 차이로 그대로 보인다.
- compat 없이 보이면 1878/2000 이 다른 숫자로 보인다(Maya 사용자가 친 270 이 −90 으로).
- 0→170° slerp 애니를 직전 프레임 compat 로 보이면 10° 넘는 점프가 0회다 [실측 E4].
→ **구현 조건**: 본마다 "마지막으로 보인 오일러"를 키트 상태로 기억해 compat 기준으로 쓴다(파일에는 쓰지 않음).

**선택지**: A 보이기 오일러 / 쓰기 쿼터니언 · B 변환 버튼만(사용자가 리그를 바꿔야 S 가 동작) · C 첫 키 때 자동 변환(리그 스크립트·IK/FK 스냅이 쿼터니언을 읽을 수 있음 → 받은 리그를 망가뜨릴 위험) · D 가져오기 때만 변환.
- 받은 리그(Rigify / ARP / 남의 .blend): **A**. 리그를 바꾸지 않는다. S / Shift+E = `rotation_quaternion` 4채널 키. Graph Editor 키트 아웃라이너는 "Rotate (Quaternion) W/X/Y/Z" 로 이름을 붙인다.
- 키트 File > Import(FBX): **D** — Maya 의 resample 과 같게 가져온 본을 XYZ 로 바꾸고 키를 오일러로 변환한다(L12 에 넣음). 가져오는 순간이라 망가뜨릴 리그 스크립트가 없다.
- 버튼: CB 회전 행 RMB / Modify 에 "Convert Rotation to Euler"(자세·키 유지, Rigify 의 Rotation Mode Converter 와 같은 뜻) — 선택 사항.

**의존(1↔3↔4)**: 결정 1(A)로 애니가 컨트롤 본에 있다. 익스포터는 디폼 본의 최종 포즈를 오일러로 샘플하므로 쿼터니언 컨트롤도 엔진에 문제없이 간다. 결정 3 의 커브 재계산은 compat 오일러 연쇄를 쓴다(E2 와 같은 방식). 그래서 세 결정이 서로 맞는다.

**뒤집을 신호**: 쿼터니언 커브 4개를 Graph Editor 에서 다루기 어렵다는 AWKWARD 가 녹화에서 나오면 → "첫 키 때 변환할까요?" 질문(Maya 문구 아님, delegated)을 넣는 쪽으로 간다.

---

## 결정 5 — 한 메시 여러 skinCluster: **지원하지 않음(안내 + 있는 것은 보여 줌)** · 확신도 **중-높음**

**확인**: Armature 모디파이어 2개(아마추어 2개)를 FBX 로 내보내면 Skin 디포머 2개와 BindPose 2개가 써진다. 그런데 **Blender 로 다시 가져오면 Armature 모디파이어가 1개만 남는다**(rig2 연결이 사라짐) [실측 E1]. 엔진은 스켈레탈 메시 하나에 스켈레톤 하나다(Unreal FBX 임포트 구조 [웹, 추정]). 게임 에셋을 끝까지 가져가는 대상(DIRECTION)에게 두 번째 스킨은 엔진에서 사라지는 데이터다. Maya 에서도 `-multi` 는 대화상자를 거쳐야 하는 드문 기능이다.

**선택**:
- 스킨이 있는 메시에 Bind Skin 을 하면 Maya 문구 그대로 묻는다("There is already a skin cluster on …"). 키트 답: **Yes 는 비활성 + 안내**("Blender: a second Armature modifier can be added in Properties > Modifiers; FBX / engines keep one skin"), No = 취소, 그리고 Edit > Add Influence 를 권한다.
- Skin Clusters 카드는 메시에 있는 Armature 모디파이어를 **모두 읽기 전용으로 보여 준다**(받은 파일에 이미 둘이 있을 때 정직하게). 고른 것의 본만 영향 목록에 보인다(ATTACH_PLAN A4 의 목록 부분, S).
- 내보내기 때 Armature 모디파이어가 2개 이상이면 경고한다.

**뒤집을 신호**: 본인이나 외부 사용자가 레이어드 스킨(얼굴·옷 분리)을 Blender 안에서만 쓰겠다고 요청하면 → Yes = 두 번째 모디파이어(ATTACH_PLAN A4 원안, M).

---

## 결정 6 — Pick walk: **컨트롤러 태그 우선 → 태그 없는 아마추어에서는 숨은 본 컬렉션의 본을 건너뜀 → 오브젝트와 개별로 숨긴 본(h)은 Maya 그대로 들어감** · 확신도 **중**

**확인**
- Maya 2026 pickWalk 는 visibility 0, 숨긴 디스플레이 레이어, Template 레이어 노드 모두로 들어간다 [실측 M3].
- Tag As Controller(`controller`)를 여러 개에 한 번에 붙이든 하나씩 붙이든 **부모 컨트롤러는 비어 있다**. 그래서 j3 ↑ 가 숨은 j2 로 간다. Parent Controller(`controller -p`)를 해야 j3 ↑ = j1 이 된다 [실측 M4].
- Rigify: 보이는 컨트롤 63 % 의 부모가 숨은 MCH, `torso` 는 보이는 조상이 없다 [실측 E4].

**선택지**: A Maya 그대로 + 태그(Rigify 사용자는 컨트롤 수십 개를 손으로 Parent Controller 해야 함 → 사실상 못 씀) · B 숨은 것은 모두 건너뜀(Maya 와 다름: 사용자가 h 로 숨긴 조인트도 건너뜀) · **C 선택**: Blender 에는 컨트롤러 태그가 없고, 리그 제작자의 "애니메이터용 세트" 표시는 **본 컬렉션의 보임/숨김**이다(Rigify / ARP 관례). 그래서 그것을 Maya 컨트롤러 태그의 Blender 번역으로 본다:
- 아마추어에 키트 컨트롤러 태그가 있으면 → Maya 규칙(태그 계층, 부모 없으면 DAG).
- 없으면 → ↑ = 가장 가까운 "숨은 컬렉션이 아닌" 조상, ↓ = 가장 가까운 그런 자손들, ←→ = 그 트리의 형제.
- 개별 `bone.hide`(Maya h)와 오브젝트 → Maya 대로 들어감.
- 리거가 MCH 컬렉션을 보이게 켜면 그 본들도 걷는다. 그래서 리그 작업 손을 잃지 않는다.
- 애드온 환경설정 "Pick walk skips hidden bone collections"(기본 켬)를 둔다.

[delegated] Maya 와 다른 점(숨은 디스플레이 레이어 ≈ 숨은 컬렉션인데 Maya 는 들어감)은 문서와 툴팁에 적는다.

**뒤집을 신호**: 결과가 엉뚱하다는 보고 — 예: `shin_tweak.L` ↑ = `tweak_spine` [실측 E4 예시]. 이런 보고가 나오면 Rigify 전용 규칙(ORG 계층 투영)이나 A 로 간다. 리거가 숨긴 컬렉션 안으로 걷고 싶다는 보고가 나오면 기본값을 끈다.

---

## 결정 7 — 숫자 가중치 표시 상한: **메시 정점 수 상한은 두지 않음. 화면 안에 그리는 숫자 2,000개 상한, 넘으면 브러시 주변만** · 확신도 **중**

**측정** (이 PC, 4.5, UI 1.25, 3D View 영역 2114×1190) [실측 E5, E6]:
- `blf` 숫자 그리기: 500 → 1.1 ms, 1,000 → 2.2 ms, 2,000 → 4.4 ms, 5,000 → 11 ms, 20,000 → 44 ms (≈ 2.2 µs/개).
- numpy 투영: 50k 정점 2.0 ms, 200k 7.6 ms.
- 가중치 읽기: `VertexGroup.weight(i)` ≈ 1 µs/정점(25,921 정점 24.8 ms). `v.groups` 루프는 그보다 2.8배 느리다.

**판단**
- 게임 캐릭터는 정점이 5k–30k 개다. 그래서 ATTACH_PLAN 의 예시 "5,000 정점 이하"는 주 대상 메시에서 기능을 끄게 된다 → 버린다.
- 비용은 메시 크기가 아니라 **화면 안 숫자 개수**로 정해진다. 투영은 전체에 하고(캐시: 뷰·변형이 바뀔 때만), 화면 안 정점만 가중치를 읽고 그린다. 2,000개면 그리기 4.4 ms + 읽기 2 ms ≈ 프레임(16.7 ms)의 40 %, 이 영역 크기에서 겹치지 않고 읽을 수 있는 수와도 비슷하다 [추정: 라벨 ≈ 28×14 px].
- 2,000개를 넘으면 브러시 반경 × 2 안의 정점만 그리고, Help Line 에 "N vertices in view — zoom in to see all weights" 를 낸다(Maya 는 상한 없이 다 그림 → 키트 차이, delegated). Maya 처럼 뒤쪽 정점도 그린다.
- 스트로크 중에는 숫자를 갱신하지 않고, 스트로크가 끝나면 그 영역만 다시 읽는다.

**뒤집을 신호**: 다른 PC(노트북 iGPU)에서 2,000개가 8 ms 를 넘거나, 사용자가 줌아웃 상태에서 전체 숫자를 원하면 → 상한을 환경설정 값으로 노출한다(기본 2,000).

---

## 결정끼리의 의존 정리
- **1 ↔ 3 ↔ 4**: Custom Shape(1) → 애니는 아마추어 안 컨트롤 본 → 내보내기 = deform-only + 익스포터 샘플 → 후처리(3)가 rest → PreRotation 과 compat 오일러 커브 재계산을 한다 → 쿼터니언 컨트롤(4)도 같은 길로 오일러 커브가 된다. Custom Shape 원본 커브는 내보내기에서 뺀다(E1: 안 빼면 Mesh 로 나감).
- **4 → L12**: 키트 FBX 가져오기는 Maya 처럼 오일러로 변환한다. 이것이 결정 4 의 "가져오기" 부분이다.
- **6 ↔ 1**: Custom Shape 컨트롤 리그(키트가 만든 것 포함)는 MCH / 오프셋 본을 숨은 컬렉션에 두면 pick walk 가 컨트롤만 걷는다. 키트가 컨트롤을 만들 때 오프셋 본은 숨은 "MCH" 컬렉션에 둔다(delegated).
- **5 ↔ 3**: 후처리는 Skin 디포머가 2개인 파일을 만들지 않는다(결정 5 경고).

## 이 문서에서 가장 약한 근거
결정 6 의 C 안. Maya 와 다르고(숨은 레이어 노드에도 들어감), Rigify 에서 "가장 가까운 보이는 조상"이 사람 눈에 맞는지는 예시 12개만 봤다. 본인 녹화로 먼저 확인할 것.
