# Step 144 DEFORM — Maya Deform 메뉴 (#34)

## 계획

근거: `research/maya/re/options_144.md` (Maya 2022 GUI, 공장값; 창 = 「Deform option windows」 표, 생성 노드 · 선택 ·
CB · Paint Weights = 「Deformers created with factory options」 표), `research/maya/re/modeling_rigging_110.md` §8
(Cluster / Soft Mod / Nonlinear 핸들 위치 · 크기). 축: Maya X → Blender X, Y → Z, Z → −Y (step 57).

공통 규칙
- 생성은 `operators/deformers.py` 의 `create(context, kind, values)` 하나 (`allset.deformer(kind)` = 공장값으로,
  옵션 창 = `operators/option_windows_deform.py` 의 `Window` 가 값으로 부름). 이름은 Maya 노드 이름 (`ffd1`,
  `deltaMush1`, `bend1` …): 모디파이어 이름 = 노드 이름, 핸들 / 격자 오브젝트 = `<node>Handle` / `<node>Lattice`.
- 디포머 가중치 = 노드 이름의 버텍스 그룹 (Maya 공장 가중치 1; 에디트 모드면 선택한 점만 1, 나머지는 그룹 밖) →
  모디파이어의 `vertex_group`. Deform > Paint Weights > <디포머> = 그 그룹을 활성으로 Weight Paint
  (`allset.paint_deformer_weights`), 그 디포머가 없으면 Maya 식 경고.
- Channel Box INPUTS: 디포머 모디파이어는 Maya 노드 이름 + Maya 속성 줄 (`deformers.ATTRS`, 가상 속성
  `maya:<attr>` = 모디파이어 값의 변환, `ui/channel_box` 의 INPUT 줄이 읽고 씀). 핸들 / 격자 오브젝트가 리드이면
  그것이 움직이는 모디파이어가 INPUTS 에 나옴 (Maya: ffd1Lattice / bend1Handle 의 CB 에 ffd1 / bend1).
- 옵션 창 Advanced 탭 (Deformation order / Exclusive / Partition) 은 Blender 에 없음 → 모든 창의 `missing`.
- 선택 결과는 Maya 표의 「Selected after」 그대로 (모디파이어는 선택할 수 없으니 그 노드의 오브젝트).

| Maya | Blender | 이름 | INPUTS (Maya 속성 = Blender) | 없는 것 (missing / notice) |
|---|---|---|---|---|
| Lattice | Lattice 오브젝트 (선택의 월드 bbox 에 맞춤, 분할 S T U = points_u / w / v) + Lattice 모디파이어 | ffd1, ffd1Lattice, 데이터 ffd1LatticeShape | ffd1: Envelope = strength; SHAPES ffd1LatticeShape: S / T / U Divisions | ffd1Base (Blender 는 격자 자체가 기준), Local mode / Local divisions, Group, Freeze, Bind original, Outside lattice, Falloff |
| Delta Mush | Corrective Smooth (Simple, rest = 원래 좌표) | deltaMush1 | Smoothing Iterations = iterations, Smoothing Step = factor, Pin Border Vertices = use_pin_boundary | Envelope, Displacement, Inward / Outward constraint, Distance weight, Scale |
| Wrap | Surface Deform (bind), 영향 = 마지막 선택 | wrap1 | Envelope = strength | wrap1Base, Exclusive bind, weight threshold, max distance, falloff mode; 영향 오브젝트의 이동은 따라가지 않음 (Surface Deform 은 영향 메시 모양만 읽음) |
| Proximity Wrap | Surface Deform, 드라이버 = 마지막 선택 | proximityWrap1 | Envelope = strength | Wrap mode (Surface 만), Max drivers, Falloff scale, Smooth influences / normals |
| ShrinkWrap | Shrinkwrap 모디파이어, 타깃 = 마지막 선택 | shrinkWrap1 | Offset = offset, Bidirectional, Reverse, Along X / Y / Z | Envelope, Closest If No Intersection, Target Inflation, Bounding Box Center, Axis Reference, Single node; Toward Center |
| Cluster | Hook + 핸들 empty (step 110) | cluster1, cluster1Handle | Envelope = strength | Relative mode |
| Soft Modification | Hook (falloff 곡선 = Maya smooth, step 110) | softMod1, softMod1Handle | Envelope = strength, Falloff Radius = falloff_radius | Falloff curve 편집, Surface mode, Color feedback, Preserve history, Mask unselected, Falloff around selection, Falloff based on X/Y/Z |
| Bend / Twist / Squash / Flare | Simple Deform (origin = 핸들, 축 Z = Maya Y) + 핸들 empty (bbox 중심, 크기 = 높이 / 2) | bend1, bend1Handle … | Curvature = angle (라디안 그대로), End Angle = angle (Twist), Factor = factor (Squash), End Flare X / Z = 1 + factor (Flare), Low / High Bound = limits (−1..1 ↔ 0..1) | Envelope, Start angle, Expand / Max expand pos / smoothness, Start flare, Curve |
| Sine | Wave 모디파이어 X 방향만 (speed 0) + 핸들 | sine1, sine1Handle | Amplitude = height, Wavelength = width (핸들 크기 단위) | Envelope, Low / High bound, Dropoff, Offset; 모양이 사인이 아님 (Blender 파형) → notice |
| Wave | Wave 모디파이어 (원형, speed 0) + 핸들 | wave1, wave1Handle | Amplitude, Wavelength, Max Radius = falloff_radius | Envelope, Min radius, Dropoff, Offset |
| Texture | Displace (텍스처 = 빈 'NONE' 텍스처 → 처음엔 움직이지 않음, Maya 처럼) | textureDeformer1 | Strength = strength, Offset = −mid_level × strength | Envelope, Vector strength / offset, Vector space Tangent, textureDeformerHandle1 |
| Curve Warp | Curve 모디파이어, 커브 = 마지막 선택 | curveWarp1 | — | (옵션 창 없음, Maya 도 없음) |
| Tension, Solidify (Maya = 굳히기, Blender Solidify = 두께), Morph, Jiggle, Wire, Wrinkle, Sculpt, Point On Curve, Pose Interpolator | 없음 | — | — | 회색 + notice (가장 가까운 Blender 기능) |

Paint Weights 대상: Cluster / Delta Mush / Lattice / ShrinkWrap / Proximity Wrap / Nonlinear / Texture Deformer =
그 노드의 그룹; Blend Shape = 셰이프 키 데이터 (blendShapeN) 이름의 그룹을 모든 대상 키의 vertex_group 으로; Tension /
Wire / Jiggle = 회색 (디포머 없음). Lattice / Nonlinear 의 Maya 대상은 캡처에서 「unknown」 → `ffd` / `nonLinear`
가중치로 추정 [I] (delegated).

delegated
- Lattice: Maya ffd 는 월드 축 bbox 에 맞춘다고 봄; 「Center around selection」 끔 = 같은 크기로 월드 원점에.
  보간은 Blender 기본 B-Spline (Maya local mode 와 같지 않음, missing 에 적음). 납작한 축은 최대 크기의 1e-3.
- Bend Curvature 는 라디안 값 그대로 Simple Deform angle 로; Low / High Bound ↔ limits 는 선형 (Blender limits 는
  0..1 로 잘림). Sine / Wave 길이 값은 핸들 크기 (높이 / 2) 배.
- Texture Direction Handle = 로컬 Z (Maya 핸들 Y), Vector = RGB to XYZ.
- 경고 문구 (디포머 없음, 대상 선택 부족) 는 Maya 문구를 캡처하지 못해 kit 문구.

검증: `tests/test_step144_deform.py` (디포머마다 노드 · 이름 · 격자 bbox / 분할 · 모디파이어 값 = 창 공장값 · INPUTS 줄과 값
· Paint Weights 대상 · 창 제목 / 버튼 / 필드 / 공장값), `tests/gui/gui_step144_deform.py` (메뉴 → Lattice → 격자,
CB INPUTS 에 ffd1, 스크린샷).
