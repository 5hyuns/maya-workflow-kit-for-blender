# Step 43 — Maya 테마 v2 (색): 뷰포트·컴포넌트·매니퓰레이터·목록·타임라인

backlog 3 (`docs/PLAN.md` 「Maya 동일화 계획」). 근거: `research/maya/colors.json` (Maya 2022.4 팩토리 실측),
`research/maya/screens/compare/delta_e.md` (step 42 끝: 31 쌍 중 9 쌍 ΔE00 > 5), step_40.md blindspot 3·4·5·15.
뷰 배경 단색 #5c5c5c·그리드 #404040 은 step 42 에서 이미 넣음.

## 실측 (step 43)

- **Maya 면 선택은 점묘 (stipple)**: 선택 면 픽셀의 25 % 가 #e4ac79 (2×2 격자 중 1), 나머지는 셰이딩 그대로 (`07_faces_selected` 를
  3배 확대). Blender 는 균일 알파로 칠하므로 같은 평균색이 되는 알파 = **0.25** (07 과 02 의 같은 영역 평균: 채널별 0.248/0.250/0.250).
- Maya 정점 점 ≈ 4 px 사각 (100 %), 비선택 보라 #c800c8, 선택 노랑; Blender `vertex_size` 3 × 화면 배율 1.25 ≈ 3.75 px → 그대로.
- 컴포넌트 모드 와이어 = 하늘색 #64dcff (hilite), 선택 면 = 위 (+Y) 와 +X 면 (`f[1]`, `f[4]`).
- Blender 4.5 테마 필드: `edge_mode_select` / `face_mode_select` (선택 모드별 색) 이 따로 있음, Outliner 는 `selected_highlight` /
  `active` (행 배경) 와 `selected_object` / `active_object` (이름 글자 색, 기본 주황) — Maya 는 선택 행 글자가 흰색.

## 계획 (delegated)

1. `tools/make_theme.py` 표만 고치고 재생성:
   - 컴포넌트: `wire_edit` #64dcff, `vertex` #c800c8, `vertex_select` #ffff00, `edge_select`·`edge_mode_select` #e4ac79,
     `face_select`·`face_mode_select` #e4ac79 알파 0.25, `vertex_size` 3 유지.
   - 매니퓰레이터: `axis_x/y/z` #e60000 / #00e600 / #4a92ff (transformX/Y/Z), `gizmo_primary`·`gizmo_hi` #ffff00 (manipCurrent).
   - 목록: Outliner 배경·목록 항목 #373737, `active` = 선택 파랑 #5285a6 (Maya 리드도 같은 파랑), 이름 글자 흰색.
   - 탭: 비활성 #373737, 활성 #444444. 타임라인 현재 프레임 #c7c7c7 (timeSliderCurrentFrame 0.78).
2. 축선: `axis_x/y` 가 그리드 축선도 칠하므로 MayaKit 템플릿 뷰에서 `overlay.show_axis_x/y` 끔 (`tools/make_startup.py`).
   Maya 의 회색 굵은 축선은 step 45 (그리드) 에서 다시 그린다.
3. 프리셀렉트 하이라이트 (`operators/preselect.py`): 기즈모 색 = Maya preSelectHilite 빨강 (1, 0, 0).
4. 비교 도구:
   - `delta_e.md` 행 추가: `edge_mode_select`, `face_mode_select`, `gizmo_hi`, Outliner `active`·이름 글자, 현재 프레임; "그라디언트 아래"
     행은 Alt+B 용 backgroundBottom 과 비교 (단색이 기본이라 이전 비교는 의미 없음).
   - **뷰포트 렌더 픽셀 표** (`viewport.md`): 리드·다른 선택·비선택 와이어 (04), 컴포넌트 와이어·선택 면 (07), 정점 (08), 매니퓰레이터 X/Y/Z (02).
     kit 쪽은 look_shots 가 기록한 투영 점 (엣지 중점, 면 중심, 정점, 원점) 주변 상자에서 Maya 색과 가장 가까운 픽셀 (1 px 어긋남에
     강함), 면은 상자 평균 (점묘 평균과 비교). Maya 쪽은 뷰 안에서 가장 가까운 픽셀 / 같은 면 영역 평균.
   - look_shots 의 컴포넌트 선택을 Maya 번호와 같은 요소로 (위치로 찾기): `f[1]` 위, `f[4]` +X, `vtx[0:2]`, `e[0]`, `e[5]`.
5. 검증: `delta_e.md` 모든 행 ΔE00 < 2, `viewport.md` (뷰 배경·선택 와이어·선택 면·매니퓰레이터) < 5, 헤드리스·GUI 전체.

## 한 것

- `tools/make_theme.py` (재생성 `theme/maya.xml`):
  - 컴포넌트: `wire_edit` #64dcff, `vertex` #c800c8, `vertex_select` **#fdff88** (Maya 가 실제로 그리는 연노랑 — colorIndex 17 의 순노랑이
    아님, 08 샷), `edge_select`·`edge_mode_select` #e4ac79, `face_select` #e4ac79 α 0.25 + `face_mode_select` α **0.07** (아래 실측).
  - 매니퓰레이터: `axis_x` #e60000, `axis_y` #00e600, `axis_z` **#0000ff** (Move/Scale 의 Z 선 픽셀 = 순파랑; displayRGBColor transformZ
    #4a92ff 는 실제로 안 쓰임), `gizmo_primary`·`gizmo_hi` #ffff00.
  - Outliner 배경·목록 #373737, 리드 행 #5285a6 (전 #6b9dc0), 선택 이름 글자 흰색 (전 주황), 탭 #373737 / #444444, 사이드바 탭 띠
    #373737, 현재 프레임 #c7c7c7.
  - 3D 뷰 헤더·리전 (툴바·사이드바) 불투명 #444444 (Blender 기본: 헤더 α 0.7, 리전 0 → 뷰가 비침; step 41 발견).
- 템플릿 (`tools/make_startup.py`): 3D 뷰 `overlay.show_axis_x/y` 끔 (축 색이 그리드 축선도 빨강·초록으로 칠함). 회색 축선은 step 45.
- 프리셀렉트 기즈모 빨강 (`operators/preselect.py`, Maya preSelectHilite).
- `research/scripts/maya_colors.py` → colors.json 에 렌더 실측 `manip_z_rendered` #0000ff, `vertex_selected_rendered` #fdff88.
- 비교 도구: `delta_e.md` 38 쌍 (새 행: 모드별 선택색, 기즈모 hover, Outliner 리드 행·이름 글자, 현재 프레임; 그라디언트 아래 = Alt+B 용
  backgroundBottom), **`viewport.md`** (렌더된 뷰포트 요소 10: kit 투영 점 주변에서 Maya 색에 가장 가까운 픽셀 — RGB 거리 64 후보 중
  CIEDE2000 최소, 면은 채움 알파를 재서 Maya 바탕에 얹어 비교), look_shots 의 컴포넌트 선택을 Maya 번호와 같은 요소로 (위치로 찾음),
  툴팁이 샷에 안 나오도록 마우스를 뷰 구석으로.
- `tests/test_step43_theme.py`: 테마 v2 값 21 개 + 면 알파 + 불투명 헤더/리전.

## 실측: 면 채움 알파 (face select mode)

| `face_select` α | `face_mode_select` α | 실효 알파 (kit 07 vs 02) |
|---|---|---|
| 0.25 | 0.25 | 0.41 |
| 0.25 | 0 | 0.19 |
| 0.33 | 0 | 0.20 |
| 0.25 | **0.07** | **0.26** (Maya 점묘 평균 0.25) |

→ 면 모드에서는 `face_select` 알파와 거의 상관없이 약 0.19 가 칠해지고 `face_mode_select` 가 그 위에 한 번 더 칠해진다. 처음 측정은
샘플 상자를 매니퓰레이터 Z 선이 지나가 틀렸음 (윗면 중심 → 중심과 뒤-왼쪽 모서리 사이로 옮김).

## 검증

- `python tools/look_compare.py`: `delta_e.md` **38/38 행 ΔE00 < 2** (전 31 쌍 중 9 쌍 > 5). `viewport.md` **9/10 < 5**: 리드 와이어 1.4,
  다른 선택 0.2, 컴포넌트 와이어 0.8, 선택 면 0.4, 선택 정점 0.1, 비선택 정점 0.2, 매니퓰레이터 X 2.1 / Y 1.4 / Z 3.2; 실패 1 = 비선택
  와이어 6.9 (아래). `pixels.md` 뷰 배경 0.0, ΔE > 5 9 → **4** (툴바 0.0, 3D 뷰 헤더 0.0, 사이드바 탭 띠 0.0 이 새로 통과). 첫 시작 체크 9/9.
- 나란히 이미지 02 / 04 / 07 / 08 과 3배 확대 크롭 (Maya 07·08, kit 02·07) 을 직접 확인.
- 헤드리스 **349/349** (40 파일), GUI **281/281**, dogfood **47/47** (콘솔 오류 0).

## 남은 것

- 비선택 와이어 (어두운 파랑) ΔE 6.9: Blender 가 와이어를 안티에일리어싱해 1 px 선의 가장 진한 픽셀이 #151d5e (Maya 는 계단선 #000460).
  `preferences.system.use_overlay_smooth_wire` (전역 설정) 를 끄면 맞을 것 → step 44 (위젯 감각, prefs_preset 그룹) 에서.
- 3D 뷰 툴 헤더 줄 (Orientation / Drag / Options) 바탕은 여전히 비침 (`pixels.md` panel_toolbar_bg 8.3): 레이아웃 단계 (47) 에서 줄 자체를 숨김.
- 컴포넌트 모드에서 Maya 는 Outliner 선택 행을 어둡게 (#414d5a) — 테마는 모드를 모름 (21.5, 남김).
- 셰이딩 밝기: 같은 면의 바탕이 kit 이 더 밝음 (윗면 kit ≈ #8f9193 vs Maya #767676): Blender 스튜디오 조명 vs Maya 기본 조명 —
  뷰 셰이딩/조명 항목으로 남김 (backlog 후보).
- Layer Editor 목록 바탕 (#444444 vs Maya #2a2a2a) 은 CB/LE 크롬 단계 (48).
