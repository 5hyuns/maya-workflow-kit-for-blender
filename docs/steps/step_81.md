# Step 81 — Maya persp 화각 (뷰 렌즈 70)

재점검 5차 backlog 1 (docs/PLAN.md 「재점검 5차」 새 발견).

## 근거

- Maya persp = focal length 35, film back 1.417 in (36 mm) — research/maya/concepts.md:163, `tools/look_data.py:25`
  (`MAYA_FOCAL_MM, MAYA_APERTURE_MM = 35.0, 36.0`) → 수평 화각 2·atan(18/35) = 54.4°, 화면 f_px = 폭 · 35/36.
- Blender 뷰포트 렌즈는 72 mm 센서 기준 (C `BKE_camera_params_compute_viewplane`: 센서 36 mm × zoom 2) → f_px = 폭 · lens/72
  (docs/steps/step_41.md:11-12). 같은 f_px 는 lens = 72 · 35/36 = **70**.
- 템플릿은 `MAYA_LENS = 35` (step 5 가 Maya 숫자를 그대로 넣음) → 수평 91.6°: Maya 의 거의 두 배 광각.
  step 41 이 지적 (step_41.md:52), look_compare 는 샷마다 렌즈를 Maya f_px 로 다시 맞춰서 숨겼다.

## 한 것 (작은 변경이라 「계획」 생략)

- `tools/make_startup.py`: `MAYA_LENS = 70` + `maya_views()` 가 모든 3D 뷰에 렌즈를 넣음 (Four View 의 persp 사분면은 같은 space 의
  렌즈를 씀). `make_startup.py` 재실행 (GUI) → `app_template/MayaKit/startup.blend`.
- `operators/create.py`: Create > Cameras > Camera (`create.KINDS['CAMERA']`, 셸프·마킹 메뉴·핫박스 공통) = Maya 카메라 35 mm /
  36 mm 필름 (Blender camera_add 는 50 mm 였음). Camera from View (Ctrl+Shift+C, step 78) 는 뷰 렌즈 × 36/72 이라 그대로 35.
- 확인한 것: `units.apply_file` / Maya Units 옵션은 거리·클립만 바꾸고 렌즈는 템플릿 값을 그대로 둠; `framing.fit` 은 창 행렬을 써서
  렌즈와 무관; 패널 메뉴 Perspective 에는 새 카메라 항목이 없음 (카메라 목록만) — 새 카메라 경로는 Create 하나.
- 테스트: `test_step5_layout` (렌즈 35 → 70, 모든 3D 뷰), `test_step21_units` (카메라 35 / 36), 새 `test_step81_view_lens.py`,
  `tests/gui/gui_step81_view_lens.py`.

## 검증

- 헤드리스 `test_step81_view_lens.py` 3/3 (look_data 의 Maya f_px = 킷 f_px, 54.43°, 카메라 35 / 36, Camera from View 규칙),
  step 5 6/6, step 21 8/8, step 78 8/8.
- GUI `gui_step81_view_lens.py` 4/4: MayaKit 템플릿 persp 렌즈 70 = 54.4°, pCube1 높이 = 뷰 폭의 0.034, Ctrl+Shift+C = camera1 35 mm /
  36 mm, Four View persp 사분면 렌즈 70.
- 스크린샷 `gui_step81_persp.png` 를 Maya `research/maya/screens/01_layout_empty.png` 와 나란히 봄: 그리드 폭이 뷰 폭의 Maya ≈ 0.73,
  킷 ≈ 0.75 (전에는 약 절반), 그리드 마름모 모양도 같아짐.
- `tools/look_compare.py`: 테마 0/38, 픽셀 5/31, 뷰포트 11/12, rects 5/12, 큐브 3/3, 그리드 코너 2/4 — 샷마다 렌즈를 Maya 값으로
  맞추므로 이번 변경과 무관 (회귀 없음 확인용).
- 전체: 헤드리스 **637/637** (75 파일), GUI (기본 배율) **558/559** → gui_step59 고친 뒤 그 파일 15/15 (전체로 치면 559/559),
  dogfood **47/47** (콘솔 오류 0).
- gui_step59 실패와 그 원인: 「V + 가운데 핸들 → pCube2 정점」 드래그가 렌즈 70 에서 스냅되지 않고 마우스만 따라감 (최종 위치 = 마우스 광선과
  pCube1 깊이 평면의 교점). 렌즈 35 로 되돌리거나 렌즈 70 + 뷰 거리 2 배 (같은 화면 크기) 면 통과 → 렌즈가 아니라 **끌고 가는 큐브가 화면에서
  클 때** 스냅이 안 걸림 (시뮬레이션). 테스트는 처음 측정한 화면 크기를 유지하도록 뷰 거리 2 배 + 카메라에 가까운 정점을 겨냥 + 누름과 이동을
  다른 틱으로 (step 28 규칙); 실제 손 확인은 manual_checks.

## 남은 것

- 이미 설치된 템플릿 사본 (`scripts/startup/bl_app_templates_user/MayaKit`) 은 확장 업데이트 때 자동으로 바뀌지 않음 — 「Install Maya
  Layout」 을 다시 눌러야 렌즈 70 이 됨. 아직 공개 전 (decision 11) 이라 영향 없음; 공개 전에 번들 템플릿이 다르면 다시 복사하는 장치를
  둘지 결정 (delegated: 지금은 안 함).
- 템플릿 없이 Blender 기본 장면에서 킷을 켠 경우 기존 뷰 렌즈 (50) 는 건드리지 않음 (사용자 설정 보호, 결정 7).
- Ortho 뷰 / 카메라 크기 규칙 (step 78 [I]) 은 그대로.
- **V 스냅이 큰 화면 크기에서 안 걸림** (위 검증): Blender 변환 스냅 (스냅 대상 가림 검사가 끌고 가는 오브젝트에 가리는지) 의 문제로 보임 —
  확대한 상태에서 Maya 사용자가 큐브를 다른 큐브 정점에 V 로 붙일 때 실제로도 그런지 손 확인 후, 그렇다면 다음 단계 후보 (pivot_snap.md S4).
  → **step 95 에서 해결**: 확대 탓이 아니라 Blender 의 10 ms 스냅 스로틀 + 시뮬레이션이 한 틱에 몰아 보낸 이동 탓 (docs/steps/step_95.md).
