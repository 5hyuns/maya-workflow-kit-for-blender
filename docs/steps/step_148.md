# Step 148 — Channel Box finish (#87 #85 #83 #95, light Intensity)

## 계획

측정 먼저 (GUI 탐침 `tests/gui/gui_step148_probe.py`, 끝난 뒤 지움; mayapy; 스크린샷 1.0 / 1.25 / 1.5):

- **#87**: Channel Box 이름 위 RMB 의 `UI_MT_button_context_menu` 에서 `is_cb_button` 은 True (`button_pointer` =
  `ALLSET_PG_channel_box`, `button_prop` = `rz_sel`) — 탐지는 맞다. 진짜 원인: Blender 는 버튼 메뉴의 **C 항목 15 줄
  (Insert Keyframe, Add Driver ...) 을 먼저 그리고 Python 메뉴는 그 뒤에** 붙인다 → `prepend` 한 Maya Channels 항목이 맨 아래.
  클립이 고른 첫 줄 = Insert Keyframe (스크린샷 `tmp/shots148/148_menu_rz_name.png`). Python 은 C 항목을 지울 수 없다.
- **#83**: 1.0 / 1.25 / 1.5 에서 값 열 픽셀을 따라 잰 고정 줄 (메뉴 막대 + 이름 줄 + 여백 + LE 분할선) = 4.9 / 4.8 / 4.8 U,
  모델 (`3.0 + 0.3 + PANE_TOP 2.2`) = 5.5 U → 0.6-0.7 U 과대 → 1.0 과 1.5 에서 한 줄을 잃고 1.5 줄 정도 비었다.
  `PANE_TOP` 2.2 는 step 99 에서 3D View 사이드바로 잰 값 (지금 dock 은 Properties 영역).
- **#85**: step 142 의 dock 폭 (탭별 Maya 폭) 뒤로 Channel Box 메뉴 막대 "Channels" 는 1.0 / 1.25 / 1.5 모두 다 보인다.
  남은 것: AE Translate / Rotate / Scale = Blender 벡터 필드 (단위 "62 cm", 좁으면 "62 c"), Maya AE 는 단위 없는 숫자.
- **#95**: mayapy `lattice -dv 2 5 2 -oc` (반지름 1 polySphere) → ffd1Lattice Scale 2 2 2. 킷은 cm 장면에서 0.02 (월드 m).
- **조명**: mayapy `listAttr -keyable` = 모든 light 종류가 Color R / G / B, Intensity (그 다음 그림자 속성). 킷 SHAPES 는
  `energy` (Blender Power), `color` (배열이라 `kind_of_rna` 가 버려 안 보임), `shadow_soft_size`.

결정 (delegated):
1. RMB 는 Channel Box 칸 위에서 이미 돌고 있는 창 모달 `allset.cb_channel_drag` (영역 버튼 처리보다 먼저) 이 받아 Maya 의
   Channels 메뉴 (`ALLSET_MT_cb_channels`) 를 연다. 선택 안 된 채널이면 먼저 그 채널을 선택 (Key Selected 가 누른 채널을 키).
   `UI_MT_button_context_menu` prepend 는 그대로 둔다 (다른 경로의 대비).
2. `PANE_TOP` 1.6 (잰 값).
3. AE Transform Attributes: AE 의 노드가 lead 이고 혼자 선택일 때 Channel Box 텍스트 프록시 (`allset_cb.tx_text` ...) 로
   그린다 — Maya 숫자 형식, 단위 없음, Maya `+=` 입력. 여러 개 선택 / 뼈 / 쿼터니언은 예전 필드 (프록시는 선택된 모두에 입력).
4. 격자: `delta_scale` = `maya_unit()`, `scale` = 상자 크기 / `maya_unit()` → Scale 이 Maya 숫자, 월드 크기 그대로
   (Lattice 모디파이어와 기준 Hook 은 월드 행렬만 쓴다).
5. 조명 SHAPES = `maya:colorR / G / B` (가상 속성, `operators/lights.channel_attrs`, `_virtual` 확장) + `allset_intensity`.

순서 이유: 다섯 항목이 거의 `ui/channel_box.py` 한 파일이고 같은 GUI 샌드박스로 재므로 메인에서 차례로 (PC 부하 규칙 ≤ 2 Blender).

## 한 일

- `ui/channel_box.py`: `ALLSET_OT_cb_channel_drag._on_rmb` (RMB → Channels 메뉴), `PANE_TOP` 1.6, `_round_half_up`
  (위젯 단위 = C `roundf(18 × scale)`: Python `round(22.5)` = 22 라서 UI 1.25 에서 U 가 24 px (Blender 25), 0.8 U 줄마다
  0.8 px 모자라 줄 수가 많을수록 어긋났다 — `layer_editor.list_rows` 도 같은 식으로), `_virtual` 이 조명의
  `maya:color*` 도, SHAPES 행이 가상 속성을 받음 (`wanted_rows` / `row_owner` / 그리기 / `shape_label`), `SHAPE_PROPS['LIGHT']`,
  SHAPES / INPUTS 텍스트 행을 채널 행과 같은 모양으로 (이름 가운데, 값, 상태 아이콘 칸).
- `operators/lights.py`: `channel_attrs` / `channel_attr` (Color R / G / B).
- `operators/deformers.py`: 격자 `delta_scale` / `scale`.
- `ui/attribute_editor.py`: `_maya_number_rows`.
- 테스트: `tests/test_step148_cb.py` (5), `tests/gui/gui_step148_cb.py` (6 × 3 배율), `test_step11_outliner_ae` 의 AE Translate
  검사가 프록시도 받게.

## 검증

- 헤드리스 전체 1324/1324 (step11 AE 검사 고친 뒤); 관련 21 파일 202/202.
- GUI `gui_step148_cb` UI 1.0 / 1.25 / 1.5 각각 6/6: RMB → Maya Channels 메뉴, 첫 줄 Key Selected 가 Rotate Z 를 12 프레임에
  키, AE Translate / Scale "62" / "1.5", 격자 Scale 1 (1 단위 polyCube; 구 2 는 헤드리스), 조명 행 Color R / G / B, Intensity.
  긴 Channel Box (사용자 속성 12 개): 보이는 줄 1.0 14 → 15, 1.25 14, 1.5 9 → 10, 마지막 줄 아래 빈 곳 = 여백 + 한 줄 미만.
  스크린샷 (`tmp/shots148/`: rmb_menu, cb_long, ae, lattice, light) 직접 봄.
- 관련 GUI: step129_channel_box / 135 / 142_ui / 144_deform / 55_pose / 62_sdk / 99 / 106 / 137 / 116 / 11 / 38 159/161 →
  실패 2 = step135 "Layer Editor 가 제자리" (20 px) → 위 반올림 버그로 찾음, 고친 뒤 step135 + 148 19/19, step148 + 142_ui
  1.0 · 1.5 각 18/18, step129_channel_box / 62_sdk / 99 / 116 / 142_ui / 55_pose 82/82. 헤드리스 다시 1324/1324.

## 남은 것

- SHAPES / INPUTS 값 칸이 위 채널 값 칸보다 약 7 px 오른쪽에서 시작한다 (이름이 버튼이 아니라 label 이라 분할 여백이 다름).
- 조명 Intensity 는 계산 속성 (Power 에서 읽음) 이라 Channel Box 에서 키를 줄 수 없다 (Maya 는 키 가능) — Power 에 키를 주는 대리가 필요.
- 격자의 선택 색은 아직 Blender 주황 (#95 본문, step 149 선택 와이어와 함께).
- Spot light 의 Cone Angle / Penumbra / Dropoff 행은 없다 (Blender spot_size / spot_blend 의 의미가 달라 따로 변환 필요).
