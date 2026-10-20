# Step 126 — 키 비주얼의 기울인 화면이 가로로 늘어남 (사용자 버그 2026-10-20)

사용자 보고: 「퍼스펙티브 불량」 → 정정 「원근이 틀렸다는 건 이미지가 가로로 너무 늘어나 있다는 것」
(`C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/user_perspective_1020.png`, 빨간 선 = 창의 가로 길이).

## 원인

`tools/marketing/compose.tilted` 는 3D 회전이 아니었다: 출력 폭을 원본 폭 그대로 두고 먼 쪽 세로 변만 줄인 사다리꼴 (step 122).
돌아간 평면은 가로가 W·cosθ·d/(d+W·sinθ) 로 줄어야 하는데 W 그대로라 캡처 비율보다 넓고 납작하게 보였다.

## 한 것

- `compose.tilt_quad` / `tilted`: 캡처 크기 W×H 평면을 가까운 (왼쪽) 세로 변을 축으로 `TILT_DEG` = 24° 돌려 핀홀 카메라
  (가까운 변까지 거리 `TILT_DEPTH` = 1.6 W, 초점 거리 = 그 거리 → 가까운 변은 제 높이) 로 투영한 4 점으로 원근 변환, 2 배 슈퍼샘플 →
  Lanczos 축소. 모든 기울인 화면 (키 비주얼 앞·뒤, 정사각, README 히어로, 소셜, X, Reddit 정사각) 이 같은 θ·같은 카메라 (delegated:
  24° — 요청 범위 20–30° 가운데, 먼 변 0.80 배).
- 투영 폭이 0.73 배로 줄어 레이아웃 폭 조정: 정사각 1020 → 1400 (예전처럼 오른쪽 아래로 넘침), Reddit 정사각 1040 → 1400, README 히어로
  900 → 1080, 소셜 560 → 680, X 카드 740 → 890 (`kit.wide` 는 화면을 실제 폭으로 오른쪽 정렬).
- `tools/marketing/perspective_check.py` (새): 기울인 화면마다 알파 마스크로 가까운 변 높이 · 먼 변 높이 · 투영 폭을 재서 tilt_quad 기대값과
  비교, 투영 폭 < 같은 높이에서의 원본 폭이어야 PASS → `tmp/marketing/perspective_check.txt` / `.png` (원본을 같은 높이로 옆에).
- 재생성: key_visual / key_visual_square / kit 6 장 / `docs/distribution/media/featured.png` (+ 사본) / 트레일러 (타이틀 카드 = 키 비주얼 레이어).

## 검증

- `perspective_check.py` 5/5 PASS (tilt 24°, 거리 1.6 W): 예 key visual front — 캡처 1920×1080 (1.778), 평면 1160 px: 가까운 변 649 px
  (기대 649.4), 먼 변 523 (523.5), 투영 폭 845 (844.9) = 원본 폭의 0.729 (기대 cosθ·d/(d+W sinθ) = 0.728, < 1). 나머지 넷도 ±1 px.
  예전 함수는 같은 평면에서 투영 폭 = 1.0 (원본 폭 그대로).
- 직접 본 것: perspective_check.png (원본 vs 기울인 화면 5 쌍), key_visual 원본 크기, 정사각 + 키트 6 장 시트 (두 번: 폭 조정 전 / 후),
  트레일러 1.5 s 프레임. clip_compose 트레일러 PASS (33.5 s, 12.7 MB, 정적 0.3 s).
- src 변경 없음 → 테스트 묶음은 돌리지 않음.

## 남은 것

- README 히어로는 화면이 세로로 캔버스의 84 % 를 차지 (위아래 여백 좁음) — 필요하면 1000 으로.
