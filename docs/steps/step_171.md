# Step 171 — Animation Snapshot / Ghosting (Visualize)

backlog_164 #8 (마지막), 감사 11 `step_163_quant.md` §6 #8: Visualize 20 % (2 / 10) 가 네 감사 연속 그대로.

## 계획

측정 먼저 (모두 Maya 2022 팩토리, `research/maya/re/visualize_171.md`):
- mayapy `research/scripts/visualize171_mayapy.py` / `_mayapy2.py` / `_mayapy3.py`: 스냅숏 이름 · 개수 · 정점, 옵션 기본값,
  Update Snapshot 동작, 고스트 속성 기본값, 모드 / 프리셋별 고스트 프레임.
- GUI Maya `research/scripts/maya_ghost171/` (`readColorBuffer`): 고스트 픽셀 · 알파 (셰이드 / 와이어), Ghosting Editor 와
  Animation Snapshot Options 창.

구현 (레인 / 파일):
1. `operators/anim_snapshot.py` — `allset.animation_snapshot` (Window 옵션 상자 "Animation Snapshot Options"),
   `allset.update_snapshot`; 프레임마다 `scene.frame_set` → evaluated mesh 를 월드 공간 메시로 복사, 이름 = Maya
   (`snapshotNGroup` / `transformN_k` / `transformN_Shapek`); 그룹 empty 의 ID 속성 = 원본 포인터 + 범위 + 갱신 방식.
   Fast (키프레임이 바뀔 때) / Slow (항상) 자동 갱신 = depsgraph handler → 0.2 s 타이머 재생성 (재생 중 · 재생성 중 무시),
   On demand = 메뉴만. Modify > Evaluate Nodes > Snapshots = 자동 갱신 스위치.
2. `ui/ghosting.py` — `Object.allset_ghost` (Maya ghosting 속성 그대로: 모드 6, Pre / Post Frames, Step, Custom Frames,
   색 두 개, Near / Far Opacity), `allset.ghost` (GHOST / UNGHOST / UNGHOST_ALL, Include Hierarchy), 고스트 프레임 규칙은
   bpy 없는 `ghost_frames()`. 그리기 = POST_VIEW: 절대 프레임별 월드 공간 삼각형 · 모서리 캐시 (현재 프레임이 바뀌어도
   유효), 없는 프레임은 타이머가 `frame_set` 으로 채움 (재생 중 · 변환 모달 중 안 함), depsgraph 갱신 (변환 / 기하 / Action)
   에서 버림. 셰이드 = 앞 · 뒷면 두 겹 알파 a (Maya 측정 1 − (1 − a)²), 와이어프레임 = 모서리 한 겹.
3. Ghosting Editor = Window "Ghosting Editor" (명령 Create Ghost from Selection, Apply = 지금 고스트 모두에 적용); Ghost
   Selected 는 저장된 편집기 값을 쓴다.
4. menu_map / notices / menu_count / 테스트.

순서가 필요한 것: 측정 → 구현 (색 · 프레임 규칙이 측정값에 의존). 공유 파일 (menu_map, notices, operators/__init__,
option_windows) 이 많아 구현 · 테스트 모두 메인에서 순차 (delegated); Maya GUI 캡처는 별도 프로세스로 구현과 동시에 돌렸다.

## 한 것

- 측정 `research/maya/re/visualize_171.md`: mayapy 3 개 스크립트 + GUI Maya 캡처 (`research/maya/screens/ghost171/`).
  고스트 불투명도 = near 0.5 → far 0.15 선형 (와이어 알파 127 / 83 / 38), 셰이드 = 앞 · 뒷면 두 겹 (191 / 139 / 71),
  Maya 색 관리 ACEScg → 고스트 색 모델 = ACEScg→Rec.709 × 보정 (셰이드 0.34, 와이어 0.78, delegated).
- `operators/anim_snapshot.py`: `allset.animation_snapshot` / `allset.update_snapshot`, Maya 이름 · 월드 공간 정점 ·
  범위 · 증분 · 오류 문구 그대로, Fast / Slow / On demand 자동 갱신, 스무스 프리뷰 제외. Modify > Evaluate Nodes >
  Snapshots = `Scene.allset_eval.snapshot` (자동 갱신 스위치).
- `ui/ghosting.py`: `Object.allset_ghost`, `allset.ghost` (GHOST / UNGHOST / UNGHOST_ALL, Include Hierarchy), 프레임 규칙
  6 모드 + 프리셋, 절대 프레임 캐시 + 타이머 채우기, POST_VIEW 그리기 (셰이드 / 와이어프레임).
- `operators/option_windows_visualize.py`: "Animation Snapshot Options" (Snapshot / Apply / Close), "Ghosting Editor"
  (Create Ghost from Selection, Apply to All Ghosts = `Window.apply_run`, option_windows 에 작은 훅 추가).
- menu_map 6 + Evaluate Nodes 1, notices 갱신 (Visualize 범주 = Turntable / Animated Sweep 만).

## 검증

- 헤드리스 `test_step171_visualize.py` 14 / 14 (Maya 정점값 f1 / f2 / f5 / f10, 증분 3, 그룹 자식 월드 공간, 오류, Update
  선택 규칙, Fast 자동 갱신, 고스트 프레임 = mayapy3 전부, 캐시). 전체 헤드리스 1600 / 1600 (step103 테스트에 Ghosting
  Editor 패널 예외 추가 후).
- menu_count: Visualize 2 → **8 / 10 (80 %)**, 전체 54.2 %.
- GUI `gui_step171_ghost.py` 13 / 13: 고스트 6 개 픽셀이 Maya 캡처와 채널당 최대 11 / 255 차, 와이어프레임 · Unghost All.
  관련 GUI step103 / step152 / step168 17 / 17. GUI 전체 묶음은 돌리지 않음 (CLAUDE.md: 릴리스 준비 때만).

## 남은 것

- Create Turntable..., Create Animated Sweep (notice 유지).
- Ghosting Editor 의 오브젝트 타입 필터, Ghosted Objects 목록 / Show-Hide, Ghost Driver (창의 Not in Blender 줄).
- 재생 중에는 없는 고스트 프레임을 채우지 않음 (frame_set 이 재생을 깨므로), Maya 는 재생 중에도 그림.
- 셰이드 고스트 색은 가까운 것이 Maya 보다 조금 어둡다 (한 보정값의 한계, ≤ 11 / 255).
