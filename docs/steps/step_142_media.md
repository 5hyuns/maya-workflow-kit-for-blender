# Step 142 lane MEDIA — 테마 없이 스토어 미디어 · 홍보 샷 · 스크린샷 다시 찍기 (#41)

## 테마 결정 (delegated)

- 모든 미디어는 **Blender 공장 테마** 로 찍는다. 킷은 step 130 (#40) 부터 테마가 없고, 생성기도 테마를 쓰지 않는다.
  보이는 UI 크롬 (헤더 · 메뉴 · 버튼 색) 은 Blender 기본 테마이고, Maya 색은 킷이 직접 그린 것만 (뷰포트 평면 #5c5c5c,
  리드 초록 / 흰 선택 와이어, 컴포넌트 색, Maya 그리드, Maya 매니퓰레이터 색, dormant 와이어 — step 134 / 142).
  `docs/distribution/listing.md` (미디어 재생성 문단), `docs/distribution/marketing/README.md`, `style.md` 에 적음.
- step 125 의 Maya 그라디언트 배경은 테마로만 가능하므로 버림 (사용자 지시 2026-10-20 의 그라디언트는 테마가 있던 때의 것) →
  Maya 공장 평면 #5c5c5c 로 확인.

## 생성기 고친 것 (먼저)

| 파일 | 바뀐 것 |
|---|---|
| `tools/marketing/scene.py` | `apply_gradient` (샌드박스 테마 `view_3d.space.gradients` 쓰기) 삭제 → `apply_look` / `LOOK_KEEPER`: Solid 뷰 = 뷰 자체 배경 (`VIEWPORT`, 0.36 sRGB = #5c5c5c, `key_batch3.set_shading`), Material Preview = 씬 월드 `.Allset Marketing World` (HDRI 로 조명, Light Path "Is Camera Ray" 이면 평면 #5c5c5c). 측정: Material Preview 는 뷰의 `VIEWPORT` 색을 무시하고 테마 배경 (#3d3d3d 계열) 을 그림 (probe: `tmp/media142/probe_*.png`); 월드 트릭은 Standard 에서 #5c5c5c, AgX 에서 #5a5a5a (ΔE00 0.7). Blender 모드 (스위치 클립의 가운데) 에서는 스튜디오 라이트 + 배경 알파 0 (= Blender 자기 배경). `theme_signature()` / `theme_unchanged()`: `maya_look()` 때의 테마 해시를 기억, 캡처마다 확인. `template_name` 삭제 |
| `tools/marketing/bg_check.py` | 그라디언트 검사 → Maya 평면 #5c5c5c 검사 (위쪽 띠의 배경이 ΔE00 ≤ 3; Blender 공장 #3d3d3d 10.6, 그라디언트 위 #889db3 26.9 은 실패) |
| `tools/marketing/shots.py`, `clips.py` | `allset.layout_install` + `read_homefile(app_template=...)` (step 130 에서 없어짐 — 첫 실행이 `AttributeError` 로 멈춤) → `sim.load_maya_layout()`. 캡처마다 / 클립마다 "theme untouched" 검사 |
| `tools/marketing/shots.py` | AE 분할 0.55 → 0.62 (좁은 dock 에서 Channel Box 가 Scale X 에서 잘리던 것) |
| `tools/marketing/content.json` | 04 Option boxes 콜아웃 사각형을 아이콘 붙은 메뉴의 ❒ 열에 맞춤 (전에는 라벨 끝 글자를 덮음) |
| `tools/marketing/clips.py` | channel_box_keys: 채널 이름이 이제 `allset_cb.<key>_sel` 토글이라 찾기 조건 추가; RMB 메뉴에 Maya Channels 항목이 없어 (#87) Channels 메뉴 (`ALLSET_MT_cb_channels`) 로 Key Selected. rigging: Create Joints 뒤 Adjust Last Operation 패널이 셸프 아이콘을 덮어 (#86) IK Handle 을 Skeleton 메뉴 경로 (`allset.ik_handle`) 로 시작. 셸프 영역의 HUD 를 Python 으로 끄면 Blender 가 죽음 (ED_area_init, region_blend_end) — 쓰지 말 것 |
| `tests/gui/sim.py` | `find_button`: 버튼이 영역 왼쪽 끝까지 이어지면 (Channel Box 이름) 거기서 중심을 돌려줌 (전에는 None) |
| `tests/test_step142_media.py` (새) | 생성기 (tools/marketing/*.py, release_shots / release_check / make_listing_media, site/make_media) 의 테마 쓰기 정적 검사 (AST: 테마 경로·별칭 대입, setattr, rna_xml / make_maya / gradients 이름) + 스캐너 자체 시험 (step 125 코드 조각을 잡음) + bg_check 합성 이미지 시험 (평면 통과, 공장 테마 · 그라디언트 · 밝은 회색 실패, 아래쪽 땅은 통과). 3/3 PASS |

`tools/release_shots.py` 는 테마를 켜지 않음 (확인만; 템플릿 뷰가 이미 평면 #5c5c5c, #45).

## 다시 만든 것

- 스토어 미디어 `docs/distribution/media/`: 01–10 + featured.png (12 개 중 icon.png 는 그대로 — 테마와 무관, 바이트 동일).
- 홍보 스틸 `docs/distribution/marketing/screens/01–10`, `key_visual.png`, `key_visual_square.png`.
- `docs/screenshots/01–07` (`python tools/release_check.py`, 1600 × 900; release_check 전 항목 PASS).
- 클립: 7 개 MP4 + GIF + 트레일러 (`make_clips.py`; channel_box_keys / rigging 은 위 수정 뒤 다시 녹화), kit/*.png, site/media — 아래 「클립」.

모든 Maya 모드 캡처: bg_check PASS (스틸 10 / 10, 클립 프레임 전부), theme untouched PASS.

## 본 것 (이미지를 직접 열어 봄)

- raw hero, 스크린 01–10, key visual (가로 · 정사각형), docs/screenshots 01–07, 클립 5 개의 중간 · 끝 프레임 시트, rigging f0016, channel_box_keys f0011 / f0019.
- 고친 것: 03 Channel Box 가 Scale X 에서 잘림 (AE 분할), 04 콜아웃이 메뉴 글자 덮음, 클립 2 개 실패 (위).
- 새 이슈: #85 (좁은 dock 에서 "Chann...", AE Scale "1." 처럼 값이 잘림), #86 (Create Joints 뒤 HUD 가 셸프를 덮음), #87 (Channel Box RMB 에 Maya Channels 항목 없음).
- 그 밖에 보인 것 (이슈 아님): docs/screenshots 의 왼쪽 위 Blender 로고는 예전부터 (release_shots 는 로고를 가리지 않음 — 스토어 미디어만 가림). 05 의 Channel Box 파란 칸 = Pack Bot 몸통이 constraint 로 움직임 (Maya constraint 파랑).

## 클립

- `python tools/marketing/make_clips.py --no-build` (클립마다 GUI Blender 1 개): 5 개 바로 PASS, channel_box_keys (이름 찾기 실패 → 위 수정,
  RMB 메뉴 #87 → Channels 메뉴) · rigging (HUD #86 → Skeleton 메뉴 경로) 은 수정 뒤 `--only` 로 다시 녹화해 PASS.
- 인코딩 (`--no-record`): MP4 7 개 + GIF 7 개 + 트레일러 33.5 s 12.31 MB 모두 PASS (정지 구간 < 2 s, GIF ≤ 4 MB). 프레임 확인: 클립 5 개 시트, 03 / 06 의 합성 MP4 프레임.
- `python tools/marketing/kit.py`: kit/*.png 6 개 PASS. 캡션 문구 「right-click > Key Selected」 → 「Channels > Key Selected」 (listing.md, copy.md, content.json, README_marketing.md).
- `tools/site/make_media.py`: 사이트가 쓰는 것만 만들게 (클립 5 개 + 트레일러, 스틸 hero / menus_shelves / switch_before; 전체 목록이면 쓰지 않는 파일 32 개가 생김), `*.webp.json` (이미지 출처 메모) 을 목록에서 건너뜀 (전에는 PIL 오류로 media.json 을 못 씀). `python tools/site/check_site.py` PASS.

## 검증

- `python tests/run.py --no-build -k step142_media,step130_package_scan` → 9 passed.
- 모든 캡처의 bg_check / theme untouched PASS (shots.log, clip_*.log), release_check 전 항목 PASS.

## 남은 것

- #85, #86, #87 (킷 버그 — 이 레인에서 고치지 않음). #86 / #87 이 고쳐지면 클립 2 개의 우회 (Skeleton 메뉴 / Channels 메뉴) 를 셸프 클릭 / RMB 로 되돌릴 수 있음.
- site/media 의 `*.webp.json` 출처 메모는 그대로 (내용은 여전히 맞음, 날짜만 예전).
