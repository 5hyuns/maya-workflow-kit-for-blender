# Step 27 — 매니퓰레이터 크기·뷰 키 (= - PgUp PgDn 0 Home Alt+5)

## 계획 (delegated)

근거: research/maya/hotkeys_default.json (hotkeySetup.mel 줄), research/maya/interaction.md.

| Maya 키 | runTimeCommand | Maya 동작 | Blender (킷) |
|---|---|---|---|
| `=`, `Shift++` | IncreaseManipulatorSize (:388-389) | `manipOptions -r -s 2.0` | `maya_kit.manip_size(factor=1.25)`: `preferences.view.gizmo_size` × 1.25 (10–200 px) |
| `-` | DecreaseManipulatorSize (:387) | `manipOptions -r -s 0.5` | ÷ 1.25 |
| PgUp / PgDn | SmoothingLevelIncrease/Decrease (:678-679) | `changeSmoothingLevel 1/0` (smooth preview 단계) | `maya_kit.smooth_level(delta=±1)`: 미리보기 Subsurf levels 0–4 (없으면 숨긴 채 만들어 단계만 저장 — Maya 도 smoothLevel 은 3 을 눌러야 보임) |
| `0` | DefaultQualityDisplay (:336) | `setDisplaySmoothness 0` (거친 표시) | `maya_kit.smooth_preview(level=1)` (1 과 같음) |
| Home | GoToDefaultView (:238) | `viewSet -home` (애니메이션 없음, interaction.md:50) | `maya_kit.view_home`: 원근 = Maya 새 씬 persp (28, 21, 28 cm × Maya 단위, `units.PERSP_EYE`), 정사영 = 방향 유지·원점·같은 거리; 카메라 뷰는 그대로 |
| Alt+5 | ToggleWireframeOnShadedCmd (:738) | Wireframe on Shaded 토글 (interaction.md:179) | `wm.context_toggle space_data.overlay.show_wireframes` |

- 배율 (delegated): Maya 는 상대 배율 2.0 / 0.5 지만 Blender gizmo_size 는 10–200 px 라 75 px 에서 한 번에 상한에 닿는다 → 1.25 배씩.
- 환경설정 값 (gizmo_size) 은 사용자 설정이므로 `prefs_preset.set_runtime()` 으로 바꾸고 원래 값을 애드온 환경설정 `runtime_backup`
  (JSON) 에 한 번 저장 → 애드온을 끄면 `prefs_preset.unregister` 가 복원 (`tests/kit.py` 가 `prefs.view` 스냅샷).
- 키맵 patch 23: 3D View 에 = / Shift+= / - / Home / Alt+5, Object Mode·Mesh 에 PgUp / PgDn / 0. IC 의 같은 이벤트 항목은 shadowing
  테스트로 찾아 지운다.
- F2–F6 (메뉴 셋) 은 이번 범위 밖.

## 한 것

- `prefs_preset.set_runtime()` / `restore_runtime()`: 키로 바꾸는 Blender 환경설정의 원래 값을 애드온 환경설정 `runtime_backup` 에 한 번
  저장, 애드온을 끄면 복원.
- `maya_kit.manip_size(factor)` (operators/manip.py): gizmo_size × factor, 10–200 px, 같은 값이면 1 px 이동.
- `maya_kit.smooth_level(delta)` (operators/display.py): 미리보기 Subsurf levels 0–4, 없으면 숨긴 채 만듦.
- `maya_kit.view_home` (operators/view.py `home_view`): 원근 = Maya persp (28, 21, 28) × Maya 단위, 정사영 = 방향 유지·원점.
- 키맵 patch 23 (`patch_view_keys`): 3D View `=` / Shift+`=` / `-` / Home / Alt+5, Object Mode·Mesh PgUp / PgDn (반복) / 0. Home 은 텍스트
  편집 모드(Font 키맵, 줄 처음)와 겹침을 의도로 선언.
- `keymap/mapping.py` 7행 계획 → 구현, `docs/keymap_mapping.md` 재생성: 구현 79 → **87**, 계획 13 → **5** (F2–F6 만).

## 검증

- 헤드리스 `python tests/run.py`: **260/260** (26 파일, 새 `test_step27_view_keys.py` 4개: 키맵 항목, gizmo_size 단계·상한 200·disable 시
  원래 값 복원·백업 비움, 스무스 단계 증감·범위·0, Home 원근/정사영 계산; `test_keymap_maya` 의 shadowing·mapping 통과).
- GUI `python tests/gui/run.py`: **202/202** (20 파일, 새 `gui_step27_view_keys.py` 7개: = 75 → 94, - 94 → 75, Alt+5 와이어프레임 켬,
  Home → 거리 44.82 / 원점 (팩토리 m 씬 = Maya 단위 m), 3 다음 PgUp 2 → 3, PgDn 두 번 → 1, 0 → 프리뷰 끔).
- `python tools/dogfood.py`: **47/47** (`'=' grows the manipulator` 이제 PASS), 콘솔 오류 0.

## 남은 것

- F2–F6 메뉴 셋 키 (IC F1–F4 뷰 키와 충돌 정리 필요).
- Maya 의 배율 2.0 / 0.5 대신 1.25 / 0.8 (delegated) — 손 감각은 manual_checks.
- Alt+5 는 뷰포트 전체 와이어프레임 오버레이 (Maya 의 패널 Wireframe on Shaded 와 같음); Maya 기본 "선택만 와이어" (wireframeOnShadedActive 1,
  defaults.json:139) 는 Blender 선택 외곽선으로 대신.
