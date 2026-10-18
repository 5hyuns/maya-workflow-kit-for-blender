# Step 84 — 타임 슬라이더 Shift 범위 키 이동·늘이기

재점검 5차 backlog 4 (docs/PLAN.md 「재점검 5차」 우선순위 4, 대응표 92행 타임라인; step_56.md:113, step_73.md:121 「남은 것」).

## 근거

- research/maya/workflows/animation.md:22 [K]: Time Slider 에서 **Shift+LMB 드래그** = 빨간 범위, **가운데 화살표 드래그** = 범위 안 키 이동,
  **끝 화살표** = 스케일. 범위 위에 ◀ ▶ (끝) 과 ◀▶ (가운데) 화살표가 그려진다 [K].
- [K] 이동·스케일은 Time Slider 의 키 = 선택 노드의 키 (timeSliderShowKeys active, step 73), 정수 프레임에 붙는다 (Time Slider 기본
  스냅), 범위도 같이 따라간다. 범위 밖 클릭 = 범위 해제 + 시간 이동 (step 56 그대로).
- kit 상태: 범위 = `WindowManager.maya_kit_time_range(_on)` (ui/time_slider.py, step 56), 키 = `time_keys.keys_in(node, a, b)`,
  Channel Box 노드 = `time_keys.nodes`, 이동 = `time_keys._move`, 도착 자리 덮어쓰기 = `key_insert.move_keys` 규칙 (Maya `-o over`, step 83).

## 계획

1. **순수 함수** (`operators/time_range.py`, bpy 없이 테스트):
   - `zone(x, x0, x1, edge)`: 범위 사각형 (x0..x1, `range_rect`) 안에서 'LEFT' / 'RIGHT' (끝에서 edge px 안) / 'MOVE' / None (밖).
     범위가 3 × edge 보다 좁으면 전부 MOVE.
   - `map_frame(t, a, b, mode, f)`: 원래 범위 a..b 의 키 시간 t → 새 시간. MOVE: t + d (d = 정수 프레임 차); RIGHT: 고정점 a,
     a + (t − a)(b' − a)/(b − a); LEFT: 고정점 b. 결과는 정수 프레임으로 반올림. `new_range(a, b, mode, f)` = 새 범위
     (스케일 끝은 반대 끝을 넘지 않게 a+1 / b−1 로 막음; a == b 면 스케일 안 함 → MOVE).
   - 핸들: 이동 = 같이 이동, 스케일 = 키 기준 x 오프셋 × 비율 (곡선이 시간으로 늘어남).
2. **연산자** `maya_kit.time_range_drag` (ui/time_slider.py, REGISTER | UNDO):
   - "Dopesheet" LMB PRESS 맨 앞 (time_scrub 보다 앞, PASS_THROUGH_FIRST). TIMELINE 모드 WINDOW + 범위 켜짐 + 커서가 범위 안이 아니면
     PASS_THROUGH (→ time_scrub: 범위 해제 + 시간).
   - 누를 때: 노드의 범위 안 키가 있는 곡선마다 **모든 키의 원본** (co, 핸들, 타입, 보간, easing, 선택 …) 을 순서대로 저장하고 범위
     안 키의 인덱스를 기억.
   - 움직일 때마다: 각 곡선을 원본으로 되쓰고 (인덱스 그대로) 범위 안 키만 새 시간으로 → `fc.update()` (정렬). 원본에서 다시 계산하므로
     키가 다른 키를 지나가도 참조가 꼬이지 않는다 (update 가 배열을 정렬해 KeyframePoint 참조가 다른 키를 가리키게 되므로 참조를 들고
     있지 않는다).
   - 놓을 때: 범위 안 키가 내려앉은 자리의 다른 키 (0.5 프레임 안) 를 지움 (`-o over`), 범위 키끼리 같은 프레임이면 나중 것만 → 인덱스
     큰 것부터 지움. 범위 = 새 범위. 한 번도 안 움직였으면 = 보통 클릭 (범위 해제 + 시간 이동, CANCELLED → 언두 단계 없음).
   - ESC / RMB = 원본 복원 + 범위 복원.
3. **그리기** (`_draw_range`): 범위 띠 위에 흰 삼각형 — 끝 영역 가운데 바깥쪽 ◀ / ▶, 가운데 ◀▶. 끝 영역 폭 = 8 px × UI 배율.
4. 다음 단계 고려: 85 (매니퓰레이터 Ctrl) · 86 (Dope Sheet 수식) 과 이벤트가 다르다. 86 이 Dopesheet LMB 클릭 선택 수식을 바꿀 때
   이 항목 (TIMELINE 모드만, 그 밖 PASS_THROUGH) 이 앞에 있다는 것을 고려.

판단 (delegated): 스냅 = 정수 프레임 (Maya Time Slider 기본 [K]); 범위 위 클릭만 = 보통 클릭; 키가 없어도 범위는 옮겨짐;
스케일된 키가 겹치면 나중 키만 남김.

## 검증 계획

- 헤드리스 `tests/test_step84_time_range.py`: zone (끝 / 가운데 / 밖 / 좁은 범위), map_frame (이동, 오른쪽·왼쪽 스케일, 반올림),
  new_range (반대 끝 넘지 않음), 연산자 함수로 곡선 이동 (원본에서 다시 계산, 다른 키를 지나가도 값 유지) · 놓을 때 덮어쓰기 ·
  스케일 핸들 비율 · 취소 복원.
- GUI `tests/gui/gui_step84_time_range.py`: Shift 드래그 10–20 → 가운데 드래그 +5 → 키 15/25 (범위 15–25), 오른쪽 끝 드래그 → 늘이기,
  Ctrl+Z 한 번 = 직전, 범위 밖 클릭 = 해제 + 시간, 스크린샷 (화살표).
- 대응표 타임라인 행 재평가, 전체 헤드리스·GUI, dogfood, manual_checks.

## 한 것

- `src/maya_kit/operators/time_range.py` (새 파일): `zone`, `new_range`, `map_frame`, `clashes` (bpy 없음) + `Drag` (누를 때 곡선의 모든
  키를 스냅샷, 움직일 때마다 스냅샷을 칸 그대로 되쓰고 범위 키만 다시 놓음, 놓을 때 덮어쓰기 정리, 취소 복원).
  - **측정**: `FCurve.update()` 는 같은 프레임 키를 합친다 → 드래그 중 범위가 다른 키를 지나가면 키가 사라졌다. 드래그 중에는
    `keyframe_points.sort()` + `handles_recalc()` 만, 놓을 때 덮어쓰기 정리 뒤 `update()`.
- `ui/time_slider.py`: `MAYAKIT_OT_time_range_drag` (REGISTER | UNDO, 범위 밖 / 범위 없음 = PASS_THROUGH, 안 움직인 클릭 = 보통 클릭
  CANCELLED), `range_zone`, 범위 띠 위 흰 화살표 (끝 ◀ ▶ 영역 8 px × 배율, 가운데 ◀▶).
- **측정 (GUI `--debug-handlers`)**: MayaKit Time Slider 줄 (WINDOW 29 px @1.25) 은 전부 Blender 의 스크럽 띠라 LMB 는 "Dopesheet"
  보다 먼저 "Time Scrub" 키맵 (`anim.change_frame`, blender_default.py:1171-1183) 이 받는다. IC 데이터에 "Time Scrub" 이 없어 Blender
  기본 키맵이 쓰이고 있었다 — step 56 의 「범위 밖 클릭 = 범위 해제」 도 템플릿에서는 실제로 안 되고 있었음 (팩토리 레이아웃 GUI 테스트만
  통과). `keymap/patch.py` `KeyconfigData.ensure` 로 Maya 키컨피그에 "Time Scrub" 을 만들고 (change_frame 유지) 그 앞에
  `time_range_drag`, `time_scrub` (둘 다 Time Slider 밖에서 PASS_THROUGH) — `maya_patches.py` 40 `patch_time_range`.
  "Dopesheet" 에도 `time_range_drag` 를 맨 앞에 (PASS_THROUGH_FIRST).
- `tests/test_keymap_maya.py` 섀도잉 스택에 "Time Scrub", `tests/test_step56_time_keys.py` 첫 항목 목록에 `time_range_drag`.
- 대응표 (PLAN 「재점검 5차」 UI 행) 타임라인: 키 틱 (73) · 레인지 바 (73) · Shift 범위 이동/늘이기 (84) 끝 → 남은 것은 Once / Oscillate
  (Blender 재생 한계, 「불가능」 목록) 뿐이라 **Done** 으로 볼 수 있다. Outliner (Sets) 가 남아 UI 행 Partial 은 1.
- 판단 (delegated): 위 「계획」 판단 그대로 + 템플릿 Time Slider 의 보통 클릭도 kit `time_scrub` 이 받음 (범위 해제, Maya 와 같음).

## 검증

- 헤드리스 `tests/test_step84_time_range.py` 6/6: zone (끝 / 가운데 / 밖 / 좁은 범위), new_range (반대 끝 안 넘음, 한 프레임 = 이동),
  map_frame (이동, 좌우 스케일 고정점, 반올림), clashes (덮어쓰기, 스케일 겹침 = 나중 것), Drag 이동이 다른 키를 지나갔다 돌아와도 키 유지 +
  놓을 때 덮어쓰기, 스케일 핸들 비율, 취소 = 원래 그대로, 키맵 순서.
- GUI `tests/gui/gui_step84_time_range.py` 7/7 (MayaKit 템플릿): Shift 드래그 10–16 → 가운데 +5 → 키 17 / 20 (옛 20 덮어씀), 범위 15–21,
  Ctrl+Z 한 번 = 드래그 전, 오른쪽 끝 16 → 22 = ×2 (14, 20), 범위 클릭 = 범위 해제 + 시간 15. 스크린샷 `gui_step84_range_arrows.png`
  에서 빨간 범위 위 흰 화살표 확인.
- 전체: 헤드리스 662/662 (처음 661/662 — step 56 테스트의 Dopesheet 첫 항목 목록에 새 항목 추가), GUI (기본 배율) 594/594, dogfood 47/47
  (콘솔 0). `docs/manual_checks.md` 「Step 84」 4 항목.

## 남은 것

- Maya 실행으로 화살표 모양·끝 영역 크기·스냅 규칙을 확인하지 않음 ([K]); 손 확인 항목.
- 범위 위 호버 때 커서 모양 / 하이라이트 없음. Maya 의 선택 키 노란 표시 (timeSliderActiveKey) 없음 (step 73 남은 것 그대로).
- 다른 UI 배율 (0.8) GUI 실행은 이번에 안 함 (기본 배율만).
- 85 (매니퓰레이터 Ctrl 평면 / Shift+MMB) 다음.

