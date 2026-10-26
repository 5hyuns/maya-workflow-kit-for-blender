# 요약 6 — Maya 2026 역공학과 키트에 붙이는 방법 (2026-10-26)

기준은 **Maya 2026** 하나다(2022 비교는 빼라는 지시에 따라 뺐다). 키트가 2022 를 따르고 2026 이 다른 곳은 "바꿀 것"으로 적었다.
자세한 내용: 명세 `C:/Repos/blender-maya-kit/research/maya/re/maya2026_*.md` (7개 + `.json` 원자료), 설계 `ATTACH_PLAN.md`, 측정 스크립트·캡처 `maya2026_re/`.
근거: Maya 2026 설치본 MEL / Python 읽기 + **maya.exe GUI 실측 4회**(합성 Qt 이벤트, factory prefs, 별도 MAYA_APP_DIR) + **mayapy 실측 6개 스크립트**. REA(바이너리 분석)는 필요 없었다: 다룬 기능이 모두 스크립트로 공개되어 있다. 라이선스 막힘은 없었다.

## 실측으로 새로 알게 된 것 Top 10
1. **Bake Simulation 의 "Keep unbaked keys" 는 범위 밖 키 보존 옵션이다.** 컨스트레인트는 어떤 설정에서도 지우지 않는다. Disable implicit control(기본 켬)은 컨스트레인트를 남기고 연결만 끊는다. 키트는 이 옵션을 끄면 컨스트레인트를 지운다 → **잘못**.
2. **Flood 는 Opacity 를 곱한다.** Replace = old + o(v − old), Add = old + o·v, Scale = old·(1 − o(1 − v)), Smooth = 평균 × o 이고 Value 는 무시한다. 나머지 영향은 비율대로 재분배하고, 잠금을 지키며, 선택된 정점에만 적용한다. 키트 수식은 같다. 다만 **Alt+F 가 키트 Flood 가 아니고**, 선택 정점 제한은 마스크가 켜졌을 때만 된다.
3. 영향 목록 RMB 는 정확히 7 항목이다: Lock/Unlock Selected, **Lock/Unlock Inverse Selection**, **Select Vertices / Add / Remove Affected Vertices**(가중치 > 0).
4. 한 메시에 skinCluster 여러 개를 둘 수 있다(대화상자로 확인). 목록은 체인 순서이고 처음 것이 선택된다. 둘을 고르면 영향 목록이 합집합이 된다. 숫자 가중치 표시는 소수 2자리 노란 숫자다.
5. **Joint Tool 이 끝나면 새 체인의 루트**(분기였으면 그 부모 조인트)가 선택되고, Enter 뒤에는 **Select Tool** 이 된다. 키트는 마지막 조인트를 선택한다.
6. 기존 조인트를 클릭하면 분기한다. 히트 영역은 **그려진 조인트 구(radius × 화면 배율)** 이고 고정 픽셀이 아니다. 키트는 10 px 고정이다.
7. Maya FBX 는 **jointOrient 를 PreRotation 으로** 쓰고 rest 회전을 0 으로 둔다. segmentScaleCompensate 는 InheritType 2 로 쓴다. 기본값이 Bake 끔·Constraints 끔이라 컨스트레인트로 구동되는 애니는 Bake 하지 않으면 **사라진다**.
8. Maya pickWalk 는 **숨은 노드로도 들어간다**. 따라서 CHAINS 의 L20 은 끊김이 아니다. 건너뛰기는 컨트롤러 태그로 한다.
9. 여러 타깃 컨스트레인트의 결과는 **가중 평균**이다. 두 번째 SDK 드라이버는 `blendWeighted` 로 **더한다**. SDK 는 블렌드셰이프 가중치·ikBlend·컨스트레인트 가중치도 구동한다.
10. 메뉴 결과도 잴 수 있었다: 인비트윈 0.5 는 조각 선형이고, Combination 기본은 곱이다. Pose Interpolator 는 −45° 에서 0.5, −90° 에서 1.0 이다. 메뉴 Blend Shape 는 스킨 앞에, Cluster 는 맨 뒤에 들어간다. `reorderDeformers A B` 는 A 를 B 뒤로 보낸다.

## 키트가 2022 를 따르고 있어 2026 에 맞게 바꿀 것
- **메뉴 구조**가 Maya 2022 정적 파싱이다. 2026 에서 달라진 것:
  - Deform: ML Deformer, Paint Membership, Pose Editor 가 생겼다.
  - Visualize: Motion Trail Editor·Blue Pencil·Ghosting Editor 가 생겼고, "Create Editable Motion Trail" 은 **없어졌다**.
  - Create: Polygon Type 이 생겼고, Subdiv Primitives 는 없어졌다.
  - Mesh: Booleans 6개와 Unsmooth 가 생겼다. Edit Mesh 에는 Smart Extrude 가 생겼다.
  - Modify: Reorder Rotation, Zero Pivot 이 생겼다.
  - 전체 목록: `maya2026_menu_diff.txt`
- 이미 2026 과 같은 것: Paint Skin Weights 섹션 순서(2024+), Bind Skin Max Influences 5, Skeleton/Skin/Constrain/Key/Control 메뉴 항목.

## 붙이는 방식 요약 (ATTACH_PLAN 표)
- **(a) Maya 손을 씌움**:
  - 페인트: Alt+F, RMB 7항목, Ctrl+Alt+C/V, Ctrl+./,
  - 조인트: 루트 선택, Enter → Select, 구 반경
  - Match 에 본 대상, Spline IK 에 기존 커브, 디포머 순서 바꾸기
- **(b) Blender 데이터로 번역**:
  - 컨트롤 모양 = 본 Custom Shape, 색 = Object/Bone 색 + 뷰 와이어 Object 모드
  - 클러스터 = Hook(CV 인덱스), Motion Path = Follow Path(offset_factor 키)
  - 여러 skinCluster = Armature 모디파이어 여러 개
  - ikBlend = IK influence
  - 인비트윈·조합·PSD = 셰이프 키 + 단순 식 드라이버(Python 자동실행 불필요)
  - Bake 의 implicit control = 컨스트레인트 mute
- **(c) 키트 구현**:
  - 숫자 가중치 표시, Motion Trail Editor 창, Game Exporter 클립
  - **FBX 후처리**(rest 회전 → PreRotation)
  - 메뉴 2026 재생성
- **(d) 하지 않음**: Y-up 전환, Offset Parent Matrix, Shift+B 아래 반경, DQ 정점별 가중치.

## 구현 순서 (SUMMARY5 대비 바꾼 점)
0. 모델링 손 버그
1. **S 묶음**: L18, #126 작은 것(A1 A2 A5 A6), 조인트 B1–B4, L6, L7, L15b, L17
   - **L20 은 뺐다**(Maya 와 같은 동작).
   - 조인트·페인트 항목을 넣었다.
2. **메뉴를 Maya 2026 구조로** (새로 넣음)
3. L11 리그 FBX(「계획」 + mayapy 왕복, 해법 = FBX 후처리) → L12 → L14
4. #126 나머지(숫자 표시, 여러 skinCluster, Tool Settings 필드)
5. 사슬 ⑤(L19, L24, L21 설정)
6. 사슬 ①(L1–L5)
7. 사슬 ④(L15, L16)
8. 사슬 ② 나머지(L8–L10, 편집형 트레일)

## 사용자가 결정할 것
1. 컨트롤 = 본 Custom Shape(권장) vs 커브 오브젝트 + 컨스트레인트
2. Y-up: Z-up 유지(권장) vs Channel Box 만 Maya 축 표시
3. L11 에서 Blender 동봉 FBX 모듈로 파일을 고쳐 쓰는 후처리를 허용할지
4. 쿼터니언 본: 오일러로 보이고 쿼터니언으로 쓰기(권장) vs 변환 버튼만
5. 여러 skinCluster 를 지원할지(엔진 FBX 에선 하나만 됨)
6. Pick walk: Maya 그대로 + 컨트롤러 태그 vs Rigify 숨은 컬렉션 자동 건너뛰기
7. 숫자 가중치 표시의 정점 수 상한

## 측정 한계
- L15b(Set Blend Shape Target Weight Keys)의 정확한 대상: 메시나 노드를 선택해서는 키가 생기지 않았다 [U].
- Game Exporter 클립 목록 UI, Pose Editor 창, Motion Trail 끌기 편집은 GUI 로 재지 않았다.
- 기본(Bake 끔) FBX 를 다시 가져올 때 spine 위치가 달라진 원인은 확인하지 못했다 [U].

## 진행 메모
이 세션이 다시 이어지는 동안 원래의 헤드리스 실행(PID 5764, 2022 비교를 포함한 옛 지시)이 같은 폴더에서 계속 돌며 스크립트를 덮어쓰고 있었다. 그래서 그 프로세스를 멈췄다. 그 실행이 남긴 Paint Skin Weights GUI 측정(`maya2026_re/out/paint/`)은 Maya 2026 실측이라 그대로 썼다.

DONE
