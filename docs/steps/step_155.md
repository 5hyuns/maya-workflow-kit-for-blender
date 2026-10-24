# Step 155 — UV Editor shell tools (backlog 154 #1)

## 계획

Maya 2022 UV 작업에서 매번 쓰는 셸 명령 · 표시 · 키 (step_154_remaining.md 항목 1, 점수 9). 레인 (delegated; 포그라운드 에이전트 2 개):
- **M — mayapy 측정** (Blender 없음): 메뉴 항목 → 명령 · 공장 옵션, 시험 메시 11 개 / 경우 43 개의 결과 UV →
  `research/maya/re/uv_shells_155.md` (동작 명세), `uv_shells_155.json` (정답), `research/scripts/uv_shells_155_mayapy.py`.
- **D — UV Editor 표시 · 키** (새 파일만): 4 / 5 / 6 / 8 / 9 / Ctrl+1, Move UV Shell → `ui/uv_display.py`, 테스트 2 개.
- **메인**: M 의 수치로 셸 명령 구현 (`operators/uv_shells.py`, M 의 결과가 있어야 해서 그 뒤), 메뉴 · 키 · UV Toolkit · 마킹 메뉴
  연결, 검증, 커밋.

## 한 일

**셸 명령** (`operators/uv_shells.py`, 셸 = step-66 섬 규칙, 선택된 UV / 모서리 / 면이 셸 전체를 고름; 규칙 = uv_shells_155.md §4):
- Stack Shells (bbox 중심을 전체 bbox 중심으로), Stack and Orient Shells, Orient Shells (반시계 0–90°, bbox 의 작은 변이 가장
  짧은 각 = 최소 캘리퍼 폭, UV 평균 중심; 볼록 껍질 변을 축에 맞추는 각만 후보), Orient Shells to Edges (선택 모서리 / UV 두 개를 ≤ 45°
  돌려 수평 · 수직, bbox 중심), Snap and Stack, Snap Together (UV 두 개, 첫째 셸이 둘째로; method 1 반대), Distribute Shells (넓은
  것부터 오른쪽으로 붙여), Normalize (선택 bbox → 그 중심의 타일, u · v 따로), Unstack Shells (Blender Pack Islands 축척 없이 + 무리
  중심 유지), Move and Sew (면이 적은 셸이 강체로 이동 — 2D Kabsch, 축척 없음 — 이음 UV 쌍은 평균에서 합침), Create UV Shell (선택
  면의 테두리를 step-66 Cut 으로), Delete UVs.
- Unfold (`uv_tools.unfold`): Maya Unfold3D 처럼 펼친 셸들의 UV 넓이 합과 셸마다 UV 평균을 유지 (전에는 bbox 중심만). 넓이는 한 배율로
  (셸마다 따로 맞추면 Blender unwrap 이 준 고른 텍셀 밀도가 깨져 수동 스윕 M66-3 이 실패 — 측정은 셸 하나짜리라 둘 다 맞음, delegated).
- delegated: **Delete UVs** — Blender 는 UV 없는 면이 없어 그 면의 UV 를 (0, 0) 한 점으로 모음 (Maya 의 unmapped 대신). Orient 의
  정확한 각 (Maya 는 최대 0.19° 어긋남) 은 정확한 최적을 씀. Move and Sew 에서 면 수가 같으면 나중 셸이 움직임 (Maya [U]).
  Unstack 배치는 Blender Pack Islands (Maya 패커 [U]). Distribute 정렬은 숫자 폭 (Maya 의 문자열 정렬 기벽은 따르지 않음).

**표시 · 키** (레인 D, `ui/uv_display.py`): 4 와이어프레임 (`uv_editor.show_faces` 끔 — `uv_face_opacity 0` 은 면을 그대로
그렸음), 5 음영, 6 텍스처 이미지 보이기 / 숨기기 (편집기마다 이미지 기억), 8 셸 테두리 (3 px, #40BFFF — 색은 측정 안 함), 9 Texture
Borders (UV 셸 테두리를 굵게, Maya 공장값 켬; Maya 의 "texture border" = 맵 테두리, 0–1 타일 외곽선 아님), Ctrl+1 고른 UV 만 보이기
(킷 상태 — `uv.reveal` 이 UV 선택을 잃어서), Tools > Move UV Shell (셸 고르기 모드 + Move 도구).

**연결**: UV Editor 메뉴 Modify 9 · Cut/Sew 2 · Edit > Delete · Tools > Move UV Shell · View 3 · Image > Display; Wireframe /
Shaded 항목과 머리 아이콘이 `show_faces`, 텍스처 / 셸 테두리 · Isolate 아이콘 연결; UV Toolkit (Create UV Shell, Move and Sew, Snap
Together, Snap and Stack, Orient Shells / to Edges, Stack / Unstack, Distribute / Normalize); Shift+RMB UV 마킹 메뉴 Create UV Shell /
Delete UVs / Texture Borders; 키 (`keymap/maya_patches.py`) 4 5 6 8 9 Ctrl+1 Delete Ctrl+Shift+X, IC 의 UV Editor 4 (섬 고르기) ·
Ctrl+1 (정점 모드) 제거 (Maya UV 구성요소 키는 F9–F12); mapping 행 7 개 KIT.

## 검증

- `tests/test_step155_uv_shells.py` 14 / 14: mayapy 정답 (uv_shells_155.json) 과 모든 면 꼭짓점 UV 비교 — Stack · Snap · Distribute ·
  Normalize · Move and Sew · Orient to Edges 1e-4, Orient / Stack and Orient 6e-4 (Maya 의 각 탐색 오차 3.5e-4, 명세 §4), Create UV
  Shell 3e-4 + 셸 수 (step-66 Cut 이 2e-4 밀어냄), Delete UVs 면 단위, Unfold 넓이 · UV 평균, Unstack 겹침 없음 + 중심. 비교하는 모든
  경우가 UV 를 실제로 바꿈 (0.04–0.75).
- `tests/test_step155_uv_display.py` 6 / 6 (레인 D), 관련 헤드리스 17 파일 (keymap, step66, step8, step54, step101, step136, step147,
  enable_disable, step104, step118, step130 …) 통과. 헤드리스 전체 4.5: 1417 / 1418 → 실패 1 = `test_step107_keys` 가 키 5 의 옛
  바인딩을 검사 (새 바인딩으로 고침) → 13 / 13. Blender 5.2.3 의 `-k step155,keymap,step107_keys,step118` 56 / 56 — 5.x 에서 고친 것:
  IC 키 4 = `wm.context_toggle use_uv_select_island` (있는 쪽을 지움), 면의 UV 선택은 5.x 의 `BMFace.uv_select` 도 (UV 선택 모드
  변경이 그 깃발에서 다시 퍼뜨림) → `compat.set_uv_face_selected`.
- GUI 전체 4.5 (단계 끝 한 번): 1654 / 1655 — 실패 1 = 수동 스윕 M66-3 (Unfold 다음 Layout 의 텍셀 밀도, 위 Unfold 의 한 배율로
  고침) → `ALLSET_SWEEP_ONLY=m66_` 10 / 10.
- GUI `-k gui_step66,gui_step155` 17 / 17; 스크린샷 직접 봄 — 셸 테두리 파랑 3 px, 텍스처 테두리 밝은 회색, Isolate 는 윗면 셸만,
  UV Toolkit 의 새 버튼.
- `python tools/menu_count.py`: UV Editor 95 → **110 / 172 (64 %)**; 단축키 구현 202 → 209 (`docs/keymap_mapping.md`).

## 남은 것

- Select > Unmapped Faces (Delete UVs 가 모은 (0, 0) 면을 고르는 것), Tools > Unfold / Cut / Sew / Pin 브러시, Stack Similar,
  Distribute UVs, Layout Along, Map / Straighten Border, Isolate Select 의 Load Set / Add / Remove — 회색 + notice 그대로.
- 셸 테두리는 UV Editor 에서만 굵게 (Maya 는 3D View 에도); 셸 테두리 색 미측정 (GUI Maya 캡처 필요).
- Move UV Shell 은 UV 도구가 바뀔 때만 UV 고르기로 돌아감; Maya 의 Prevent Overlap 옵션 없음.
- manual_checks 「Step 155」.
