# Step 156 — Curves tools (backlog 154 #2)

## 계획

Maya 2022 Create > Curve Tools (CV / EP Curve Tool, Three / Two Point Circular Arc) 와 Curves 메뉴 (Rebuild, Fillet, Cut, Attach /
Detach, Edit Curve Tool …) — Curves 44 % (16/36) 가 두 감사째 그대로 (step_154_quant.md).

표현 (delegated, 측정): Blender 레거시 NURBS 는 임의 knot 을 못 담지만 `use_endpoint_u` + order 4 = 표준 clamped uniform 3차
B-spline (tmp/probe156/knots.py: Blender 평가점과 직접 계산한 곡선의 거리가 표본 간격과 함께 0 으로 — 20000 표본 4.4e-4).
Maya CV / EP Curve Tool 의 공장값 knot 간격 Uniform, Rebuild 공장값 Uniform → Maya 결과를 CV 그대로 Blender NURBS 에 담을 수 있다.
비균일 knot 이 나오는 명령 (Chord length 옵션 등) 은 knot 삽입으로 Bezier 로 바꿔 모양을 정확히 (필요할 때만).

레인 (포그라운드 에이전트 2 개 동시, Blender 최대 2 개):
- **M — mayapy 측정**: 각 명령의 공장 옵션과 시험 곡선에서의 결과 (degree, knots, CV) → `research/maya/re/curves_156.md/.json`,
  `research/scripts/curves_156_mayapy.py`.
- **T — 그리기 도구** (새 파일만): CV / EP Curve Tool, 3 / 2 점 원호 도구 = 창 모달 (클릭 = 바닥 평면 / 표면 점, Enter = 끝, Maya
  단위), `operators/curve_draw.py` + GUI 테스트 `gui_step156_curves.py`; 곡선 만들기는 `operators/curves_maya.py` 의 함수
  (`make_cv_curve` / `make_ep_curve` / `make_arc3` / `make_arc2`) 를 부름 — 메인이 M 의 수치로 속을 채움 (그래서 T 의 검사는 점 수 · 끝점
  · 도구 흐름, 모양 수치는 메인의 헤드리스 테스트).
- **메인**: `curves_maya.py` 수학 (EP 보간, 원호, Rebuild, Fillet, Cut, Attach / Detach …), 메뉴 / 옵션 창 / 마킹 메뉴 연결, 검증, 커밋.
  M 이 끝난 뒤 (수치가 필요해서).

## 한 일

**그리기 도구** (레인 T, `operators/curve_draw.py`): Create > Curve Tools > CV Curve Tool / EP Curve Tool / Three Point Circular
Arc / Two Point Circular Arc = 창 모달 (Joint Tool 처럼 메뉴 · 선반에서 어디서나). 클릭 = persp 에서 바닥 (z = 0), ortho · 지평선 위는
원점을 지나는 뷰 평면; 누른 채 끌면 점 이동, Enter 끝 (CV 는 차수 + 1 점부터), Backspace / Delete 마지막 점 지움, Esc 취소, X 누르고 있으면
격자 스냅; 그리는 동안 POST_VIEW 미리보기. 이름 `curveN`, 결과는 Command Line 결과 칸 (`Result: curve3`, step 151 규칙).

**측정** (레인 M, `research/maya/re/curves_156.md/.json` 147 경우 + GUI 도구 15, `research/scripts/curves_156_mayapy.py`): 메뉴 항목
→ 명령 · 공장 옵션 (file:line), 결과의 차수 · knot · CV · 표본.

**수학** (`operators/curves_math.py`, bpy 없음 — de Boor / 기저 미분 / Boehm 삽입 / 보간 / 분해):
- EP Curve Tool: 공장값 Uniform = 점 k 를 u = k 에서 지나는 3차, 양 끝 자연 조건 (C'' = 0); Chord length 옵션 = 누적 현 길이 knot.
- 3 점 / 2 점 원호: 원 위의 s + 1 점 (s = 8 구간) 을 같은 각으로, 끝 도함수 = 접선 × 현 (chord = 2r sin(sweep / 2s)); 2 점은 원이
  d 와 n × d 의 평면에 있고 짧은 호 (toggle = 긴 호), 기본 반지름 = 현 / 2 (반원).
- Attach (Blend, bias 0.5 / Connect): 가까운 끝끼리, A 끝 ceil(d/2) · B 앞 d//2 + 1 CV 를 빼고 사이에 bias 혼합 CV 하나 (차수 1 / 2 / 3
  측정), B 의 knot 은 A 끝에서 이어짐. Detach / Cut = knot 을 차수만큼 삽입해 자름 (Cut 은 3D 교점, 모든 조각). Fillet (원, 반지름 1) =
  유리 3차 Bezier (가중치 1, (1+2w)/3, (1+2w)/3, 1, w = cos(θ/2)) 를 두 곡선의 교점 접선에, 각 곡선의 시작 쪽 (시작이 교점이면 끝 쪽).
  Straighten (CV 다리 길이 유지, CV0→CV1 직선), Move Seam (닫힌 곡선의 CV 목록을 고른 점으로 돌림).
- Rebuild (공장 Uniform 4 span, 3차, 0–1, 끝 유지): Maya 의 정확한 알고리즘은 [U] — 같은 호 길이 점들의 최소제곱, 끝점 고정, 끝 다리는
  원래 끝 접선 위 (모양 차 ≤ 곡선 길이의 0.6 %).

**Blender 표현** (`operators/curves_maya.py`): clamped uniform = NURBS Endpoint (order = 차수 + 1, 측정: 표준 B-spline 과 같음),
periodic = cyclic NURBS, 차수 1 = POLY, 그 밖의 비균일 3차 (점 사이에서 Detach / Cut 한 조각) = 정확한 Bezier 분해. 연산자
`allset.curve_rebuild` / `curve_attach` / `curve_detach` (편집 모드에서 고른 CV 의 Greville 매개변수에 가장 가까운 edit point 에서 —
Blender 에서는 곡선 위 매개변수를 직접 고를 수 없어서, delegated) / `curve_cut` / `curve_fillet` / `curve_straighten` /
`curve_move_seam`; 이름 Maya 식 (`curveAattachedCurve1`, `curveAdetachedCurve2`, `filletedCurve1`).

**옵션 창** (`operators/option_windows_curves.py`, 공장값 curves_156.md §1): Rebuild Curve Options, Attach Curves Options, Fillet
Curve Options, CV / EP Curve Tool (Tool Settings: 차수). 메뉴 연결: Create > Curve Tools 4, Curves > Rebuild / Fillet / Cut /
Straighten / Move Seam / Attach / Detach (Attach / Detach 는 Blender make_segment / split 이던 것을 바꿈), 선반 EP Curve Tool / Three
Point Circular Arc / Attach / Detach / Rebuild (메뉴 항목을 거쳐).

delegated: Fillet 은 교점 접선 기준 (직선에서 정확, 휜 곡선은 근사); Open/Close 는 Blender cyclic 토글 그대로 (Maya Preserve 규칙 [U]);
Edit Curve Tool, Lock Length, Bend / Curl / Scale Curvature, Fit B-spline, CV Hardness, Extend, Align, Intersect 는 회색 + notice 그대로.

## 검증

- `tests/test_step156_curves_maya.py` 11 / 11: mayapy 정답과 CV · knot · 가중치 비교 — EP (Uniform / Chord) 1e-5, 3 점 원호 16 경우 ·
  2 점 원호 15 경우 · Attach 11 경우 · Detach 4 · Cut 4 (2 · 3 곡선, 3D) · Straighten 2 · Move Seam 2 · Fillet 4 모두 1e-6 이내 (실제
  오차 1e-7 수준), Rebuild 7 경우 knot · 끝점 정확 + 모양 0.6 %, Blender 가 그린 점 = Maya 곡선 (NURBS / 유리 / Bezier / POLY / cyclic),
  연산자 6 개 끝까지.
- `tests/test_step156_curve_draw.py` 7 / 7 (레인 T), GUI `gui_step156_curves` 36 / 36 — EP 4 클릭 + Enter, CV 3 클릭 대기 → 4 번째,
  3 점 원호; 스크린샷 직접 봄 (매끈한 EP · CV 곡선, 반원 호가 lead 초록, Outliner curve1–3, Channel Box curveShape3).
- 헤드리스 전체 4.5: 1435 / 1436 → 실패 1 = `test_step21_units` 가 CV Curve Tool / EPCurveTool 선반을 `allset.create` 로 검사 (도구로
  바뀜, 고침) → 46 / 46. Blender 5.2.3 `-k step156,step21_units,step101` 40 / 40.
- `python tools/menu_count.py`: Curves 16 → **21 / 36 (58 %)**, Create 37 → 40 / 70.
- GUI 전체 4.5 (단계 끝 한 번): **1688 / 1691** (148 파일, 2 GUI_SKIP). 실패 3 = `gui_step129_panel_toolbar` (툴 머리 버튼 29 / 25,
  popover 클릭 한 칸 밀림) — 혼자 돌려도 실패지만 **step 155 커밋 (a895042) 을 worktree 로 빌드해 돌려도 똑같이 실패** (머리 폭 850 / 895 px,
  step 155 전체 실행 때 954): 이 단계의 회귀가 아니라 오늘 창 · 머리 폭이 달라진 것 — 테스트가 읽는 폭과 머리가 그려진 폭이 어긋남.

## 남은 것

- Rebuild 의 Maya 알고리즘 [U] (모양 0.6 % 이내), 비균일 Rebuild 종류 (Reduce / Match knots / Curvature …) 와 Keep CVs / Tangents.
- Detach 는 고른 CV 근처의 edit point 에서만 (Maya 는 곡선 위 임의 점); Edit Curve Tool (곡선 위 점 매니퓰레이터), Intersect, Extend,
  Fit B-spline, CV Hardness, Align, Bend / Curl / Scale Curvature, Lock Length — 회색 + notice.
- 그리기 도구: 한 곡선 뒤 끝남 (Maya 는 다음 곡선을 계속), 원호의 반지름 조절 매니퓰레이터 없음, V / C 스냅 없음, 표면 위 그리기 없음.
- `gui_step129_panel_toolbar` 는 머리 폭에 민감 (그려진 버튼 수 ≠ 테스트가 계산한 `fit`): 폭이 정해진 뒤 다시 읽게 고칠 것.
- manual_checks 「Step 156」.
