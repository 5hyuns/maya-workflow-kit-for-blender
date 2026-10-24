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
