# Step 20 — 타임라인: `.` `,` 키 이동, 재생 범위 뷰, Range Slider

재점검 1차 backlog 6 (`docs/steps/step_14.md` dogfood: `.` = 피벗 파이가 열려 이후 키를 먹음, 타임라인 눈금 0–250 vs 재생 1–120).

## 계획

근거: hotkeySetup.mel:358-361 via docs/keymap_mapping.md (`,` PreviousKey, Alt+`,` PreviousFrame, `.` NextKey, Alt+`.` NextFrame);
research/maya/ui_layout.md:106-108 (Time Slider / Range Slider 줄), :272-286 (§4.10 Time Slider 8 개 이동 버튼 순서, §4.11 Range Slider =
animation start · playback start · [range] · playback end · animation end, 자동 키 토글); research/maya/defaults.json:16-19 와
concepts.md:142 (재생 1–120, 애니메이션 범위 1–200, PREF:469-472).

현재 같은 이벤트 (실측): `.` = 3D View 피벗 파이, Image 피벗 파이, Clip Editor 피벗 파이, Outliner `show_active`; `,` = 3D View 방향 파이;
Alt+`.` / Alt+`,` 없음.

결정 (모두 delegated):

1. **키 = "Frames" 키맵** (3D View·Timeline·Graph·Dopesheet 등 대부분 에디터에 있음): `.` / `,` → `screen.keyframe_jump(next)`,
   Alt+`.` / Alt+`,` → `screen.frame_offset(±1)` (누르고 있으면 반복). 3D View 의 피벗·방향 파이와 Image 피벗 파이는 지운다 —
   헤더 드롭다운으로만 (Maya 도 피벗/방향은 툴 옵션). Outliner `.`(활성 보기)·Clip Editor 피벗 파이는 그쪽이 먼저 (shadows 로 명시).
2. **Range Slider = 타임라인 헤더** (`bl_ui.space_time.TIME_HT_editor_buttons.draw_header` 교체, 해제 시 복원, `tests/kit.py` 스냅샷):
   왼쪽 자동 키 토글 + Maya 순서 이동 버튼 8 개(처음, 한 프레임 뒤, 이전 키, 역재생, 재생, 다음 키, 한 프레임 앞, 끝) + 현재 프레임,
   오른쪽 Range Slider 4 필드: 애니메이션 시작 = `frame_start`, 재생 시작 = `frame_preview_start`, 재생 끝 = `frame_preview_end`,
   애니메이션 끝 = `frame_end`, 가운데 재생 범위 토글(`use_preview_range`; 끄면 안쪽 필드 흐림 = 재생 범위가 애니메이션 범위).
   Maya 처럼 별도 줄(31 px)은 영역을 하나 더 만들어야 해서(step 12 의 strip 같은 우회) 헤더 한 줄로 근사. 드래그 막대(rangeControl)는 없음.
3. **MayaKit 템플릿 범위** (`tools/make_startup.py`): 애니메이션 1–200, 재생(preview) 1–120 켬 — Maya 기본과 같음 (step 5 의 1–120 은
   재생 범위였던 것으로 보고 바꿈). 렌더 범위도 1–200 이 되는 것은 문서화.
4. **타임라인 뷰 = 재생 범위**: Maya 타임 슬라이더는 항상 재생 범위를 보여 줌. 파일을 열 때(load_post) 그리고 범위 값이 바뀔 때
   (msgbus: Scene frame_start/end, frame_preview_start/end, use_preview_range) 다음 틱 timer 로 모든 창의 Timeline(Dopesheet TIMELINE 모드)
   에서 `anim.scene_range_frame` (미리보기 범위가 켜져 있으면 그것). 그래프·도프시트는 그대로.

검증: 헤드리스 (키 바인딩·가림·매핑, 헤더 교체·복원 스냅샷, 템플릿 범위), GUI (키 두 개 → `.` / `,` / Alt+`.` / Alt+`,` 를 3D View 와 Timeline 위에서,
MayaKit 템플릿 타임라인 view2d 양 끝 ≈ 1 / 120, 재생 끝 필드 값을 바꾸면 뷰가 따라감, 헤더 스크린샷), dogfood `.` PASS.

## 한 것

- `keymap/maya_patches.py` 20 `patch_key_stepping`: Frames `.` / `,` → `screen.keyframe_jump(next)`, Alt+`.` / Alt+`,` →
  `screen.frame_offset(±1)` (repeat); 3D View 피벗·방향 파이와 Image 피벗 파이 제거; Outliner·Clip Editor 는 shadows.
  매핑 NextKey / PreviousKey / NextFrame / PreviousFrame = KIT (`docs/keymap_mapping.md` 재생성: 구현 75 → 79, 계획 17 → 13).
- `ui/time_slider.py` (새): `TIME_HT_editor_buttons.draw_header` 교체 (Maya 순서 이동 버튼 8 개, 현재 프레임, Range Slider 4 필드 + 재생 범위 토글,
  자동 키), `fit_timelines` (`anim.scene_range_frame`), msgbus 구독 5 개 + `load_post` 핸들러 → timer. `ui/__init__.py` 에 등록.
  `tests/kit.py` 스냅샷에 `draw_header` 추가 (해제 시 복원을 test_enable_disable 이 확인).
- `tools/make_startup.py`: 애니메이션 범위 1–200, 재생(preview) 1–120 켬; `startup.blend` 재생성. `tests/test_step5_layout.py` 기대값 갱신.
- 테스트: `tests/test_step20_timeline.py` 4개, `tests/gui/gui_step20_timeline.py` 9개; `tools/dogfood_session.py` `.` 체크에 키 두 개를 넣고
  `.` / Alt+`.` / `,` 3 단계로.

## 검증

- `python tests/run.py` → `227 passed, 0 failed, 20 file(s)` (가림·충돌·매핑·활성/비활성 스냅샷 포함).
- `python tests/gui/run.py` → `156 passed, 0 failed, 14 file(s)`: 3D View 위 `.` 1→10 (파이·모달 없음), `,` 10→1, Alt+`.` 1→2, Alt+`,` 2→1,
  Timeline 위 `.` 1→10; MayaKit 템플릿 범위 1–200 / 재생 1–120, 타임라인 뷰 −3.5 … 124.6, 재생 끝을 60 으로 바꾸면 뷰 −1.2 … 62.3.
- 스크린샷 `step20_timeline.png` 직접 확인: 헤더에 이동 버튼 8 개 + 현재 프레임, 오른쪽에 `1 | 1 [재생 범위] 120 | 200` + 자동 키, 눈금 1–120.
- `python tools/dogfood.py` → 47 중 46 (`.` / Alt+`.` / `,` PASS). 남은 실패 1 = `=` 매니퓰레이터 크기 (backlog 밖, PLAN 「재점검 1차」 2).
  콘솔 오류 0줄.

## 남은 것

- Range Slider 의 드래그 막대(rangeControl)와 별도 줄 — 헤더 한 줄 근사.
- Maya 타임 슬라이더의 키 틱 모양(붉은 선)·소리 스크럽 없음 (step 7 「남은 것」, C 에 가까움).
- 렌더 범위가 애니메이션 범위(1–200)를 따름 (Blender 는 하나의 frame range).
- 피벗/방향 파이 단축키가 없어짐 — 3D View 헤더 드롭다운 사용.
- Ctrl+Alt+`.` / `,` (SelectNext/PreviousKey) 미검토.
