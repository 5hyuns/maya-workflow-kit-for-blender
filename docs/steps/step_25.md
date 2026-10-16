# Step 25 — cm 그리드와 그리드 스냅

## 계획 (측정 먼저, delegated)

- 증상 (step_23): MayaKit 템플릿(m + cm 표시) persp 뷰에 그리드 선이 없고, X 홀드 + 기즈모 드래그가 사본을 10.44 cm → 0 cm 로 스냅.
- 측정 (임시 GUI 프로브, 템플릿 General 3D 뷰): `show_floor` True, `grid_scale` 1.0, `grid_subdivisions` 10, `grid_scale_unit` 1.0,
  클립 0.001 / 100, 거리 0.4482. 클립을 0.01 로 바꿔도 그리드 없음; `grid_scale` = 0.01 이면 그리드가 보임 (스크린샷 비교).
- 원인 [K, 측정과 일치]: Blender 는 단위계가 있으면 그리드 단계를 단위 목록으로 만들고, 사용자 원근 뷰에서는 기본 단위(1 m)보다
  작은 단계를 건너뛰며, 단계 = 단위 × `grid_scale` / `scale_length` (BU). 그래서 cm 표시여도 원근 그리드의 가장 작은 단계가 1 m 이고,
  GRID 스냅도 그 단계를 쓴다 → 45 cm 거리에서는 선이 안 보이고 스냅은 0 m. (`grid_subdivisions` 는 단위계가 있으면 쓰이지 않음.)
- 해결: `grid_scale` = 표시 단위의 미터 값 (cm → 0.01). 그러면 가장 작은 원근 단계 = 0.01 m = 1 Maya 단위 (템플릿: 0.01 BU, Maya Units:
  0.01 / 0.01 = 1 BU). 단계는 ×10 (1 cm, 10 cm, 1 m …): Maya 의 5 cm 굵은 선(research/maya/defaults.json:29-31)과 그리드 크기 ±12 는
  단위계 그리드에서 만들 수 없음 (delegated: 1 cm / 10 cm 로 둠).
  - `operators/units.py` `grid_scale(scene)`; `apply_file` 이 3D 뷰 `overlay.grid_scale` 을 설정하고 백업, `restore_file` 이 복원.
  - `tools/make_startup.py` `maya_views()`: 모든 3D 뷰 `overlay.grid_scale = MAYA_UNIT` (0.01), startup.blend 재생성.
  - 팩토리 m 씬은 그대로 (1.0 = 1 m 단계).

## 한 것

- 위 「해결」 그대로. `units.grid_scale()` 은 `system == 'NONE'` 이면 1.
- `tools/release_check.py` 로 `docs/screenshots/` 재생성 (01_layout 에 그리드 선이 보임).

## 검증

- 헤드리스 `python tests/run.py`: **249/249** (24 파일, 새 `test_step25_grid.py` 3개: 단위 설정별 grid_scale 과 "가장 작은 원근 단계 =
  1 Maya 단위", 템플릿의 모든 3D 뷰 0.01 + Maya Units 적용/복원 후 유지, 팩토리 씬 Maya Units 적용 시 1 → 0.01 → 복원).
- GUI `python tests/gui/run.py`: **187/187** (18 파일, 새 `gui_step25_grid_snap.py` 8개: 템플릿 grid_scale 0.01; X 홀드 + 기즈모 X 화살표
  110 px 드래그 → 템플릿 **9 cm**, Maya Units **9 cm** (1 BU = 1 cm), 팩토리 **3 m** — 모두 정수 단위·0 아님).
  스크린샷 `tmp/shots25/gui_step25_snapped_cm.png`: 그리드 선 보임, Channel Box Translate X "9 cm".
- `python tools/dogfood.py`: **46/47** (남은 실패 `=`), 콘솔 오류 0. `python tools/release_check.py` PASS.

## 남은 것

- Maya 그리드의 5 cm 굵은 선 / ±12 크기는 Blender 단위계 그리드로는 불가 (단계 ×10, 무한 바닥).
- 이미 저장된 파일(그리드 1.0)은 그대로 — 열 때 바꾸지 않는다 (decision 1/8 의 "저장된 파일은 안 바꿈").
- 정사영 뷰는 단위 단계 전체를 써서 원래도 cm 선이 보임; X 스냅 손 감각 (확대/축소 시 단계 변화) 은 manual_checks.
