# Step 154 — 재점검 10차 (사용자 지시의 「재점검 9차」)

## 계획

사용자 지시 (2026-10-24): 정한 일이 모두 끝남 — 헤드리스 전체 + 깨끗한 설정 설치 dogfood + GUI 를 Maya 사용자 눈으로, 「남은 것」·
manual_checks 정리 (blindspot 포함), PLAN 절, HANDOFF, backlog 5–8 개. 기준: 「기본 Maya 에 Blender 기능이 붙은 모습」, 차이만.
「재점검 9차」 는 step 145 이므로 이번은 10차로 번호 매김 (delegated, step 133 / 145 와 같은 방식).

레인 (delegated; 포그라운드 에이전트 2 개 동시, Blender 최대 2 개):
- **A — 문서 정리** (에이전트, Blender 없음): README 대응표, 146–153 「남은 것」 + step 145 목록 대조, blindspot, manual_checks 정리
  → `docs/steps/step_154_remaining.md`, `docs/manual_checks.md`.
- **B — 수치** (에이전트, Blender 1 개): menu_count / 옵션 상자 종류 / 마킹 메뉴 / 선반 / 단축키 / look_compare (실효 배율 1.0)
  → `docs/steps/step_154_quant.md`.
- **메인**: 헤드리스 전체 (백그라운드, Blender 1 개) → 레인이 끝난 뒤 dogfood (깨끗한 설정 설치 + Maya 사용자 세션) → 스크린샷을 직접
  보고 차이 기록 → 합치기, PLAN · HANDOFF · backlog, 커밋. dogfood 가 레인 뒤인 이유: Blender 2 개 상한.

## 한 일 · 검증

- 헤드리스 전체 4.5: **1398 / 1398** (169 파일, HEAD e26b969).
- dogfood (`tools/dogfood.py`, 깨끗한 설정에 zip 설치 → Maya 모드 → 스크립트 세션): **48 / 48**, 콘솔 오류 / 경고 0. 스크린샷 12 장
  `tmp/dogfood/shots/` 을 직접 봄.
- 레인 A: 대응표 **29 / 2 / 0 / 2 (88 %)** — 감사 9 와 같음, 움직인 행 없음. 열린 이슈 20 중 17 개는 코드에서 고쳐졌고 (#82–#101 중)
  릴리스 때 닫음 (step_143 방식); 코드에서도 열린 것 #81 #89 #97. manual_checks 582 / 79 ticked → **579 / 81** (낡은 3 삭제, GUI
  테스트가 다 검사하는 2 체크, 낡은 문구 9 고침). 자세히 `step_154_remaining.md`.
- 레인 B: 메뉴 596 → **600 / 1318 (45.5 %)**, 편집기 메뉴 506 → 517 / 914, 옵션 상자 Maya 창 80 → 83 (서로 다른 것), 선반 151 → 153,
  단축키 199 → 202, 마킹 메뉴 363 → 364 작동; look_compare 뷰포트 11/12, 킷 픽셀 5/6 (마킹 메뉴 표본점이 step 151 의 작은 링 밖 —
  색 회귀 아님, `tools/look_data.py` KIT_POINTS 다시 고름 필요), rects 5/12, 밀도 5/6. 자세히 `step_154_quant.md`.

## 메인 GUI 관찰 (dogfood 스크린샷, Maya 2022 `research/maya/screens/` 와 나란히) — 차이만

| # | 차이 | 근거 |
|---|---|---|
| G1 | 킷 명령 결과가 Blender 보고 (상태 줄 ⓘ "Grouped 2 object(s) into group1") — Maya 는 Command Line 결과 칸 / Script Editor 에 한 줄. `self.report({'INFO'}, ...)` 99 곳, `command_line.show_result` 3 곳 | `05_rmb_marking_menu.png`, `operators/group.py:158` |
| G2 | RMB 목록이 화면 아래에서 3 열로 나뉨 (Maya 는 한 열, 위로 밀림) | `05_rmb_marking_menu.png`, 레인 B 이미지 6 |
| G3 | Space 로 연 네 뷰: 정사영 뷰가 Maya 보다 약 10 배 확대 (큐브가 칸을 채움, 격자 칸 안 보임), 머리줄 / 툴바가 하나 (Maya 는 칸마다) | `08_four_views.png` vs `16_four_view.png` |
| G4 | 네 뷰에서 Space 로 키운 side 뷰: 선택된 lead 큐브의 초록 와이어가 안 보임 (네 뷰에서는 보임) — 확인 필요 | `09_channel_box.png`, `11_attribute_editor.png` |
| G5 | Command Line 언어 "Python" (Maya 기본 MEL) — 킷이 MEL 을 돌리지 않음 (step 105 결정) | `01_first_start.png` |
| G6 | 옵션 상자 두 개가 step 147 뒤 "Blender has no settings" 창으로 (Display > Toggle Show/Hide ❒, Edit > Delete by Type > Non-Deformer History ❒) — props 를 HIDDEN 으로 바꿔 `option_kind` 가 generic 이 됨 | 레인 B, `ui/menu_sets.py:846` |

## 차이 우선순위 (점수 = 심각도 × 빈도; 레인 A + B + 메인)

| 점수 | 차이 | 출처 |
|---|---|---|
| 9 | UV Editor 도구 빈칸: Unfold, Move / Stack / Snap Together / Orient Shells, Delete UVs, Shell Borders, UV 키 4/6/8/9/Ctrl+1 | A #1 |
| 9 | Curves 16/36 (EP Curve, 원호, Rebuild, Fillet, Cut, Edit Curve Tool) · Surfaces 8/41 — 두 감사째 그대로 | A #2, B |
| 9 | Graph Editor Key 메뉴가 선택 키가 아니라 Channel Box 노드에 작동, Select 2/8, Mute Key, Default Tangent | A #3 |
| 9 | #81 Maya UI 초기화 없음, 작업 공간 하나 (General) | A #4 |
| 8 | Channel Box 메뉴: RMB Breakdown / Mute / Cut·Copy·Paste Selected / Freeze / Sync 없음, Ctrl+RMB · 빈 곳 RMB = Blender 메뉴, 조명 Intensity 키 불가, spot Cone / Penumbra 행 없음, #97 INPUTS "Armature" | A #6 #7, BS2 |
| 8 | Skin / Skeleton: 가중치 내보내기 / 가져오기, Interactive Bind, Joint Labelling, IK 켜기 / 끄기 (Skeleton 24 %) | A #5, B |
| 6 | 뷰 / 메시지: G1 Blender 보고, G2 RMB 목록 열, G3 네 뷰 정사영 확대 · 칸마다 머리줄, G4 와이어, look_compare 표본점 | 메인 |
| 6 | 옵션 / 메뉴 동작: G6 회귀 2, Ctrl+Shift+click = 선반에 추가 (Maya) 가 옵션 상자로 감 (BS1), Hypershade 견본 MMB 끌어 지정 | A BS1 BS3, 메인 |
| 6 | 렌더: lambert1 1.25 배 밝음, Blender F12 에 기본 조명 없음, Render Setup 회색 | A #8 |
| 5 | Maya Preferences 창 / Hotkey Editor = Blender Preferences, Reference Editor reload / unload / replace | A #11 #12 |
| 4 | Visualize (ghosting, snapshot) 2/10, #89 Quad Draw 남은 것 | A #14 #15 |
| — | 테마 (위젯 · 메뉴 · Outliner 색) — 스토어 규칙 (결정 13), 구현 안 함 | B 이미지 1 |

## 남은 것 / backlog

`C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 8 개 (steps 155–162) — PLAN 「재점검 10차」. 고쳐진 이슈 17 개는
다음 릴리스에서 닫음 (`gh issue close`, 원격 작업이라 이번엔 안 함).
