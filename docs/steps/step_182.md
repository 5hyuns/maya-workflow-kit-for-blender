# Step 182 — 재점검 13차 (사용자 지시의 「재점검 12차」)

## 계획

사용자 지시 (2026-10-25): 정한 일 (backlog_174, steps 174–181) 이 모두 끝남 — 헤드리스 전체 + 깨끗한 설정 설치 dogfood + GUI 를 Maya
사용자 눈으로, 「남은 것」·manual_checks 정리 (blindspot 포함), PLAN 절, HANDOFF, backlog 5–8 개. 기준: 「기본 Maya 에 Blender 기능이
붙은 모습」, 차이만. 「재점검 12차」 는 step 173 이므로 이번은 13차로 번호 매김 (delegated, steps 163 / 173 과 같은 방식).

레인 (step 173 과 같음; 포그라운드 에이전트 2 개 동시, Blender 최대 2 개):
- **A — 문서 정리** (에이전트, Blender 없음): README 대응표, 174–181 「남은 것」 + step 173 목록 대조, GitHub 이슈, blindspot,
  manual_checks → `docs/steps/step_182_remaining.md`, `docs/manual_checks.md`.
- **B — 수치** (에이전트, Blender 1 개, sandbox `q182`): menu_count / 옵션 상자 / 마킹 메뉴 / 셸프 / 단축키 / look_compare →
  `docs/steps/step_182_quant.md`.
- **메인**: 헤드리스 전체 (sandbox `h182`, 셸 백그라운드 명령 — 서브에이전트 아님) → 레인 뒤 dogfood (Blender 2 개 상한 때문에 B 가
  끝난 뒤: 순서 필요) → 스크린샷 직접 보기 → 합치기, PLAN · HANDOFF · backlog, 커밋.

## 한 일 · 검증

- 헤드리스 전체 4.5: **1683 / 1683** (205 파일, HEAD 326f12f, sandbox h182).
- dogfood (`tools/dogfood.py`, 깨끗한 설정에 zip 설치 → Maya 모드 → 스크립트 세션): **48 / 48**, 콘솔 오류 / 경고 0, 스크린샷 12 장
  `tmp/dogfood/shots/` 직접 봄.
- 레인 A (`step_182_remaining.md`): 대응표 **30 / 1 / 0 / 2 (91 %)** — 그대로 (Done 행 아래 숨은 차이는 174–181 이 고침: G 반복,
  Anim 탭, F9 도구). 174–181 이 끝낸 것 지움 (G5 도구 유지, G 반복, 선택 면 ΔE 40.5 → 2.3, G2 Undo 결과, 네 뷰 이름표, 패널 메뉴 정직성,
  UV 대부분, Light Links, Animation Layers, Surfaces 일부). 열린 이슈 #89 하나. 새 blindspot: **UV > Delete UVs 회색** (kit 에
  `allset.uv_delete` 있음 — runtime 명령 이름이 달라 쌍둥이 검사가 놓침), **Animation Layers 옛 안내 두 곳** (Relationship Editors,
  Channel Box Add / Remove Layers), Auto Key 가 애니메이션 레이어를 모름, MASH 메뉴 없음 (플러그인 메뉴라 셈 밖), Hypershade 그래프
  단축키 ~56 NO, Construction History 토글 회색, Graph Editor Retime Tool. manual_checks 682 / 96 → **691 / 107**.
- 레인 B (`step_182_quant.md`): 메뉴 699 → **714 / 1318 (54.2 %)** (Lighting 36 → 93 %, Surfaces 20 → 37 %), 편집기 메뉴 560 → **578 /
  914** (UV Editor 79 %), 옵션 상자 Maya 창 104 → **114 경로** (dead 214 → 207; Insert Isoparms 가 redo → generic 으로 후퇴), 셸프 155 →
  **159 / 203**, 단축키 209 → **210**, 마킹 368 / 65 그대로 (세 감사째). look_compare: 뷰포트 11 → **12 / 12** (선택 면 ΔE 2.3), 킷 픽셀
  6 / 6, rects 5 / 12 그대로, 테마 색 20 개 (step 130 결정상 불가). 그대로인 메뉴: Key 54 %, Control 7 %, Mesh Display 38 %, Create 57 %,
  FX 전부 (여섯 감사째), Script Editor History 0 / 13.

## 메인 GUI 관찰 (dogfood 스크린샷 vs Maya 2022) — 차이만

| # | 차이 | 근거 |
|---|---|---|
| G1 | RMB 목록이 링 왼쪽 위에서 시작해 아래로 내려가 Time Slider 를 덮음 ("Assign Existing Material" 이 타임라인 위). Maya: 링 아래, 창 밖으로 잘림 | `05_rmb_marking_menu.png` |
| G2 | 핫박스 위에 in-view 메시지 "Object selection on. F8 goes back to components." 가 겹쳐 핫박스 윗줄을 가림 (Maya 메시지는 핫박스 뒤에서 사라짐) | `07_hotbox.png` |
| G3 | AE 탭 · 메뉴 잘림 ("Sele…", "Fo…", "Attrib…", "pCub…", "initial…", "lambe…", "Pre…") — step 173 G4 그대로 (event simulation 에서 dock fit 꺼짐; 실제 세션 미확인) | `11_attribute_editor.png` |
| G4 | 결과 칸이 Ctrl+Z 뒤 P / Shift+P / F8 / Delete 를 지나도 `Undo: Group` (Maya 는 parent 결과 등으로 바뀜) | `05`, `07`, `11` |
| G5 | 뷰 왼쪽 위에 이전 in-view 메시지 조각 ("gro…") 이 RMB 목록 뒤에 남음 | `05` |
| G6 | 선택한 edge 가 굵은 cyan wire 밑에서 거의 안 보임 (레인 B crop09), 매니퓰레이터 평면 핸들 작고 흐림 · 가운데 흰색 | 레인 B §5c |

## 차이 우선순위 (점수 = 심각도 × 빈도)

| 점수 | 차이 | 출처 |
|---|---|---|
| 16 | 옵션 상자 ❒ 클릭 = 명령 (#82, 여섯 감사째) | B #1 |
| 15 | RMB 목록 링 옆 · Time Slider 덮음 (Maya: 링 아래) | B #2, G1 |
| 12 | 선택 edge 안 보임, 매니퓰레이터 평면 · 가운데 색 | B #3 #7, G6 |
| 10 | Time Slider 칸 눈금 · 재생 위치 상자 | B #4 |
| 9 | Character Set 19 leaf + Time Slider 칸 | B #5 |
| 9 | Mesh Display 38 %, Delete UVs · 패널 Show 회색 쌍둥이, Insert Isoparms 창 후퇴 | B #6 #10, A BS1 BS5 |
| 6 | Auto Key 가 애니 레이어 모름, 옛 안내 두 곳 | A #1 BS2 |
| 6 | Polygon Primitives 7 회색 (Create 57 %) | B #9 |
| 6 | FX 18 % (여섯 감사째), Graph Editor 154 / 229, 리그 나머지 | B, A #2 #3 |
| 4 | 핫박스 위 in-view 메시지, 결과 칸 Undo 고정, AE 잘림 (G2–G5), Channel Box 행 배경 · 헤더, maya.cmds 17 함수 | 메인, B #8, A #4 |

## 남은 것 / backlog

`C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog.json` 8 개 (steps 183–190) — PLAN 「재점검 13차」. G2–G5 (작음) 는
manual_checks 「Step 182」 + 다음 감사. 5.x 헤드리스는 154–181 이 아직 안 돌았다 (다음 릴리스 준비 때; NLA slots, light linking,
NURBS 표면 확인 필요).
