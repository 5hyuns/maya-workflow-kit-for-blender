# Step 119 — Blender 5.x 색 일치 (사용자 요청 2026-10-19: 「5.x 버전 할 때 컬러도 신경 써 줘」)

step 118 (5.x 호환) 의 연장. 5.0 은 테마 구조 (키 이름 변경·삭제·추가), 위젯 상태색, 일부 GPU 셰이더가 4.5 와 달라, 4.5 형식의 Maya
테마 (`theme/studio_grey.xml`) 에 이동 표 (`theme.MOVED`) 를 덧대는 것만으로는 5.x 에만 있는 키가 Blender 기본색으로 남는다. 이번
단계: 버전마다 팩토리 테마를 비교하고, 버전마다 테마 파일을 만들고, 화면을 4.5 와 Maya 에 대어 색이 같은지 잰다.

## 계획

1. `C:/Users/ohnsk/AppData/Local/allset_blenders/` 의 각 5.x (5.0.1 / 5.1.2 / 5.2.2) 와 4.5.4 에서 팩토리 테마를 XML 로 내보내 키 비교
   (새 키 / 없어진 키 / 공식 5.0 이동 표로 옮긴 키 / 후속 없음).
2. 테마 생성기 (`tools/make_theme.py`) 가 버전마다 파일을 만들게: 4.5 파일은 그대로, 5.x = 4.5 킷 값 + 이동 + 5.x 새 키의 Maya 값.
   Maya 에 대응이 없는 새 키는 이유를 적고 Blender 값으로 둔다 (`delegated`).
3. 실행 중인 Blender 가 자기 버전 파일을 고르는 길은 `compat.py` 한 곳 (step 118 규칙).
4. 테마 밖의 색 (셰이더, 오버레이 그리기) 은 4.5 대 5.x 같은 장면 스크린샷 차이 지도로 찾는다.
5. 검증: look_compare (Maya 대비) 네 버전, 4.5 대비 5.x 차이 지도, 생성 파일 테스트, 헤드리스·GUI·release_check.

## 한 것

- **`tools/theme_diff.py` (새)**: 각 Blender 에서 팩토리 테마를 `_rna_xml` / `rna_xml` 로 내보내 키 단위로 비교 →
  `tmp/theme_diff/report.json`, `--md` 요약. 4.5 1014 키, 5.0.1 696, 5.1.2 701, 5.2.2 703; 5.2.2 새 키 100, 없어진 키 411 (옮김·합침
  226, 후속 없음 185). 결과 표와 키 목록: `docs/compat_5x.md` 「테마 차이」.
- **`tools/make_theme.py`**: 설치된 각 Blender 에서 돈다. 4.5 → `studio_grey.xml` (바이트 그대로), 5.x → `studio_grey_<5.m>.xml`
  = 4.5 킷 XML 을 먼저 로드 (공유 키 = 4.5 값) + 색 표 (5.x 에 없는 4.5 경로는 `LEGACY_OK` 로 건너뜀) + `apply_5x`: MOVED 값은 4.5
  파일에서, `wcol_*.outline_sel` = 그 위젯의 `outline`, `wcol_curve` = `wcol_regular`, `FIVE_X` (`grid_major` 0.25 — Maya 격자는 한 색,
  `panel_active` = Maya 선택색, `panel_outline` 투명, `regions.scrubbing.text` = Dope Sheet 글자색). Blender 값으로 둔 10 키는
  `KEEP_FACTORY_5X` 에 이유와 함께 (`delegated`: link, axis_w, grid_axis_brightness, gp_wire_edit, node_outline, preferences.match,
  scene_strip_range, 5.2 anim_interpolation 3).
- **`compat.theme_file(folder)`**: 실행 버전 이하의 가장 새 `studio_grey_<maj>.<min>.xml`, 없으면 `studio_grey.xml`.
  `theme.THEME_FILE` 이 이것을 쓰고, `_apply_moved` 는 버전 파일이 없을 때만 (대체 경로).
- **MOVED 오류**: `common.anim.channel_selected` 의 원래 경로가 `dopesheet_editor.channels_selected` (전에는 없는 이름이라 값이 안 옮겨짐).
- **`compat.LINEAR_IMAGE_SHADER`**: 5.0 의 `IMAGE` 내장 셰이더는 선형 → sRGB 변환을 하지 않아 셸프 아이콘 (선형으로 바꾼 텍스처) 이
  어두웠음 → 5.0+ `IMAGE_SCENE_LINEAR_TO_REC709_SRGB` (`ui/shelf.py`). 잘라 낸 그림 비교로 4.5 와 같은 밝기 확인.
- **`tools/theme_xml_diff.py` (새)**: 생성된 5.x 파일과 4.5 파일의 공유 키 비교 — 661–662 개 중 다른 값 1 (freestyle 알파: 4.5 RGB,
  5.x RGBA).
- **`tools/version_compare.py` (새)**: look_compare 장면을 4.5 와 5.x 에서 같은 창 크기로 찍어 나란히 + ΔE00 지도 (±3 px 안에서 가장
  작은 값 — 5.x 영역은 2 px 안쪽에 있어 위젯이 조금 움직임) → `research/maya/screens/version_compare/<ver>/` (`table.md`).
- **look_compare 측정점 3 개** (`tools/look_data.py`, `tools/look_compare.py`): 5.x 한 줄 타임라인의 time_field 대체점 (머리줄 오른쪽 끝),
  Outliner 검색칸 측정점 (dx 207, r 0), 메뉴 탐지를 x 10 부터 (5.x 메뉴 그림자 가장자리를 다른 열로 잡던 것).
- `tests/test_step119_theme_5x.py` (새, 3): 실행 버전의 파일 선택, 모든 버전 파일이 공유 키에서 4.5 와 같음, 새 키에 Blender 기본값이
  남지 않음 (`KEEP_FACTORY_5X` 제외). `ASSETS_LICENSE.txt` 와 `test_step114_guidelines` 의 자산 목록에 새 XML 3 개.

## 검증

- look_compare (Maya 2022 대비) 네 버전 모두 같은 값: 테마 ΔE00 > 5 0 / 38, 픽셀 4 / 25, 뷰포트 11 / 12, 영역 5 / 12, 장면 3 / 3, 밀도
  5 / 6, 격자 4 / 4, 뷰 가구 2 / 3 (`tmp/r119/look_<ver>.txt`).
- version_compare: 레이아웃 장면 15 개에서 4.5 대비 ΔE00 > 5 픽셀 0.83–0.97 %, 평균 ΔE00 0.21–0.24 — 남은 것은 배치 (5.x 한 줄 타임라인,
  눈금 간격, Outliner 활성 행 외곽선). 첫 화면 17 % 는 opt-in 전 Blender 5.x 기본 화면 (킷 무관). 차이 지도 직접 확인.
- `test_step119_theme_5x` 3 / 3 × 4 버전.
- 헤드리스 전체, GUI 전체, release_check: 아래 「최종 측정」.

## 최종 측정

마지막 코드 기준 (2026-10-20):

| Blender | 헤드리스 (105 파일) | GUI | release_check |
|---|---|---|---|
| 4.5.4 | 880 / 880 | 전체 1121 / 1121 (89 파일) | 23 / 23 |
| 5.0.1 | 880 / 880 | 색·레이아웃 6 파일 72 / 72 (step49 / 51 / 60 / 112 / 113 / 116) | 23 / 23 |
| 5.1.2 | 880 / 880 | 72 / 72 | 23 / 23 |
| 5.2.2 | 880 / 880 | 72 / 72 | 23 / 23 |

- 5.x GUI 전체는 step 118 에서 1121 / 1121 × 4; 이 단계의 코드 변경은 테마 파일 선택과 셸프 셰이더뿐이라 그것을 그리는 GUI 파일만 다시 돌림.
- release_check 레이아웃 그림 (`tmp/r119/rc_shots_<ver>/`) 을 4.5 의 `docs/screenshots/` 와 나란히 봄: 색 같음, 차이는 5.x 한 줄
  타임라인과 눈금 간격 (step 118).

## 남은 것

- 5.x Outliner 활성 행 외곽선: 5.x 가 `outliner.active` 로 그리며 외곽선만의 테마 키가 없음 — 4.5 / Maya 와 조금 다름.
- `KEEP_FACTORY_5X` 10 키는 Blender 값 (Maya 대응 없음).
- 새 5.x 마이너: `python tools/make_theme.py` (allset_blenders 에 넣은 뒤) → 새 버전 파일, `tools/theme_diff.py` 로 새 키 확인,
  `test_step119` 가 남은 기본값을 잡음.
- 실제 화면 확인: `docs/manual_checks.md` 「Step 119」.
