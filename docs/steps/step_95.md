# Step 95 — V 스냅 (확대)

재점검 6차 backlog 6 (docs/steps/step_81.md 「남은 것」: 확대한 상태에서 V 점 스냅이 안 걸림).

## 근거

- Maya: V (point snap) + Move 축 핸들 드래그 → 정점을 그 축 위로 투영한 좌표, 스냅되는 것은 매니퓰레이터 중심 (피벗)
  (research/maya/workflows/pivot_snap.md:37 S4).
- kit: V 홀드 = `operators/hold.py` `SnapGroup` (snap_elements VERTEX, snap_target CENTER), Move 툴 = `ui/manipulator.py`
  (`target_set_operator("transform.translate")`).
- Blender 4.5: `source/blender/editors/transform/transform_snap.cc` `transform_snap_mixed_apply` (약 536–562 줄, blender-v4.5-release):
  `if (current - t->tsnap.last >= 0.01)` 일 때만 스냅 대상을 다시 찾음 (주석 "Time base quirky code to go around find-nearest slowness").
  10 ms 안에 들어온 다음 이동들은 앞에서 찾은 대상 (못 찾았으면 "없음") 을 그대로 씀.

## 재현과 원인 (측정)

`tests/gui/gui_step95_v_snap.py` (MayaKit cm 템플릿, pCube1 원점 · pCube2 x 3 cm, Move 툴, V + 드래그). 경우 이름 = 확대 / 핸들 / 목표 /
이동 방식 (`MAYA_KIT_STEP95_CASES` 로 골라 돌릴 수 있음):

| 경우 | 뷰 거리 (큐브 화면 크기) | 이동 | 결과 |
|---|---|---|---|
| 기본, X 화살표 → 앞 정점 / 안쪽 정점 | 44.8 cm (27 px) | 한 틱에 12 개 (burst) | 붙음 (첫 이동이 이미 정점 가까이) |
| 확대, X 화살표 → 안쪽 정점 | 6.7 cm (161 px) | burst | **안 붙음** (x 1.907 = 마지막 마우스 위치 그대로) |
| 확대, 가운데 핸들 → 앞 정점 | 6.7 cm | burst | **안 붙음** |
| 확대, 위 둘 | 6.7 cm | 한 번에 목표로 (jump, 이동 1 개) | 붙음 |
| 기본 · 확대 모두 (5 경우) | | 틱마다 1 개 (paced) | 모두 붙음 |
| 확대, burst 뒤 같은 자리로 이동 1 개 더 (다음 틱) | | | 붙음 |

→ **확대 / 가림 검사 / 스냅 픽셀 거리 / kit hold·pivot 재작성 탓이 아님.** 이벤트 시뮬레이션은 이동을 한 틱에 몰아 넣어 몇 ms 안에
처리되고, Blender 는 그중 첫 이동에서만 스냅 대상을 찾는다. 기본 확대에서는 드래그가 짧아 (38 px) 첫 이동이 이미 스냅 거리 안이라 붙었고,
확대하면 드래그가 길어 첫 이동이 정점에서 멀어 "대상 없음" 이 남았다 (step 81 이 "큰 화면 크기" 와 엮은 이유). 안쪽 정점이 끌고 가는 큐브에
가리는 경우도 붙음 (Blender 는 변환 중인 오브젝트를 스냅 대상·가림 검사에서 뺌) — step 81 의 「카메라에 가까운 정점」 우회도 필요 없었음.
`--debug-handlers` 는 필요 없었음: 드래그는 kit 매니퓰레이터 → `TRANSFORM_OT_translate` 모달 + `MAYA_KIT_OT_hold` (V) 로 정상 시작 (로그).

## 한 것

- `tests/gui/gui_step95_v_snap.py`: 기본 / 확대 (뷰 거리 0.15 배) × X 화살표 → 앞 정점 · 안쪽 정점, 확대 가운데 핸들 → 정점. 이동은 틱마다
  하나 (손처럼 10 ms 보다 띄엄띄엄). 확대 스크린샷 `gui_step95_close_inner_drag.png` 확인 (pCube1 이 pCube2 안쪽 정점 x 2.5 cm 에 붙고
  Channel Box Translate X 2.5).
- kit 코드는 바꾸지 않음 (delegated): 손 입력에서도 남는 것은 "마우스를 멈춘 마지막 이동이 직전 계산 뒤 10 ms 안이면 그 이동의 스냅이 계산되지
  않음" 뿐이고, 이는 Blender 의 모든 스냅에 똑같다. 고치려면 변환 모달에 이동 이벤트를 다시 넣어야 하는데 (`event_simulate` 는
  `--enable-event-simulate` 에서만, `cursor_warp` 는 사용자 커서를 되돌릴 위험) kit 에서 안전한 방법이 없음 → 알림 UI 는 두지 않고
  (실제로 거의 안 보이는 Blender 공통 동작이라 알림이 오히려 헷갈림, delegated) manual check 로 느낌 확인.
- `tests/gui/gui_step59_manip.py` 의 step 81 주석을 진짜 원인으로 고침 (테스트 동작은 그대로).
- `docs/manual_checks.md`: step 81 항목 문구 갱신, step 95 항목 (빠르게 휙 끌어 바로 놓기) 추가. research/blender/api_limits.md 에 스로틀 기록
  (로컬 자료).
- CLAUDE.md 에 GUI 테스트 주의 한 줄 (스냅 드래그는 이동을 틱마다).

## 검증

- `python tests/gui/run.py -k step95`: 6/6 (설치 + 5 경우). 측정용 burst 경우는 확대에서 2/2 실패 (위 표), jump 2/2 통과.
- 전체: 헤드리스 **704/704** (85 파일), GUI **708/708** (76 파일; 702 + step 95 의 6). `src/` 를 바꾸지 않아 dogfood 는 다시 돌리지 않음 (step 94: 47/47).

## 남은 것

- 손 확인 (manual_checks step 81 · 95): 실제 마우스로 확대 상태 V 스냅, 빠르게 끌어 바로 놓을 때 느낌.
- 다른 스냅 홀드 (X 그리드, C 커브) 도 같은 스로틀을 받음 (X 의 GRID 는 `SCE_SNAP_TO_INCREMENT` 가 아니라서 해당) — 시뮬레이션 테스트에서
  긴 드래그는 틱마다 이동할 것.
- 다음: step 96 Outliner Sets, 97 manual checks 정리 2.
