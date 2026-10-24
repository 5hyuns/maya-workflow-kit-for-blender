# Step 178 — UV Editor finish

Backlog `C:/Users/ohnsk/AppData/Local/hermes/autodrive_bmk/backlog_174.json` 5 번째 (재점검 12차 step_173_quant.md §7 #6,
step_173_remaining.md R3). 시작: UV Editor 메뉴 118 / 172 동작 → 목표 ≥ 135.

## 계획 (레인)

| 레인 | 내용 | 파일 | 누가 |
|---|---|---|---|
| A Modify | mayapy 측정 + 구현: Map Border, Straighten Border, Match Grid, Layout Along, Stack Similar Shells, Distribute UVs, Symmetrize | `operators/uv_modify.py`, `tests/test_step178_uv_modify.py`, `research/maya/re/uv_modify_178.*`, `research/scripts/uv_modify_178_mayapy.py` | 서브에이전트 (포그라운드) |
| B Select / View | mayapy 규칙 측정 + 구현: Unmapped Faces, Back-Facing / Front-Facing, Texture Borders, Non-Overlapping, Filter Connected / Contained Faces, To Connected Faces, Unpin All, Isolate Select Add / Remove / Remove All | `operators/uv_select_178.py`, `ui/uv_display.py` (isolate), `tests/test_step178_uv_select.py`, `research/maya/re/uv_select_178.*` | 서브에이전트 (포그라운드) |
| C 연결 | `ui/editor_menu_map.py` 매핑, notice 정리, 마킹 메뉴 `("item", path)`, menu_count, GUI 샷 (Map Border 뒤 UV Editor) | 메인 | A · B 뒤 (그들의 연산자 이름이 필요해서 순차) |

A · B 는 파일이 겹치지 않음 (각자 새 모듈; 등록은 메인이 `operators/__init__` 에 추가 — 레인이 그 파일을 안 건드리게).
Blender 는 레인마다 한 번에 1 개 (동시에 2 개 이하).

## 한 것

### A Modify (`operators/uv_modify.py`, mayapy `research/maya/re/uv_modify_178.md` / `.json`, 스크립트 `research/scripts/uv_modify_178_mayapy*.py`)

| 항목 | Maya (factory) | 규칙 | mayapy 대비 최대 오차 |
|---|---|---|---|
| Distribute UVs | `texDistributeUVs "U" -1` | 선택 UV 필요, 간격 = bbox 폭 / (n−1), Maya 글자 정렬의 첫 UV 고정, u 만 | 5.0e-8 |
| Match Grid | `polyGridUV 256 256 1` | 선택 UV 를 1/256 칸 중심으로 (격자선 위면 u 는 아래 칸, v 는 위 칸 — MEL 버릇, 측정) | 4.8e-8 |
| Layout Along | `polyLayoutUV -l 1 -sc 1 -rbf 1 -fr 1` | 뒤집힌 셸 v 반전, 가로가 긴 셸 −90°, 한 줄 · 큰 것부터 · v=0 바닥 · 간격 0, 배율 1/max(폭 합, 최대 높이) | 1.4e-7 |
| Stack Similar Shells | `polyUVStackSimilarShells -to 0.1` | 같은 경계 모양의 뒤 셸을 첫 셸 위로 (이동 + 회전 + 균등 배율), 거울 / 다른 모양은 그대로 | 9.9e-8 |
| Map Border | `untangleUV -mb square -sd 0` | 경계 UV 를 0-1 사각형에: 가장 낮은 UV id = (0,0), 반시계, **3D** 변 길이 간격, 안쪽 UV 그대로 | 1.9e-7 |
| Straighten Border | `polyStraightenUVBorder -bo 0 -pl 1 -c 0 -gt 5` | 선택 경계 UV 사슬 (빈 칸 5 개까지 메움), 끝 고정, 안쪽은 직선 위에 원래 UV 길이 비율로 | 9.1e-8 (49 경우) |

Symmetrize (Modify / Tools) 는 안 함: `symmetrizeUV` 는 GUI Maya 의 modelingToolkit 명령이고, GUI 세션 5 번 (대칭 끔 /
topo symmetry 켬 / 직접 · evalDeferred 호출) 모두 UV 가 바뀌지 않음 — Symmetrize UV 브러시의 이음 변 클릭 뒤에만 동작하는
것으로 보임 (`research/scripts/maya_uvsym178/`, md §4). 측정 규칙이 없어 notice (Flip + Match UVs / Mirror modifier Mirror U).

### B Select / Edit / View (`operators/uv_select_178.py`, `ui/uv_display.py`, mayapy `research/maya/re/uv_select_178.md` / `.json`)

- Back-Facing / Front-Facing (`selectUVFaceOrientationComponents`): 음 / 양 UV 면적의 면이 쓰는 UV; 면은 모든 UV, 변은 양쪽, 점 / UV 는
  하나라도 [O] (Maya 툴팁의 앞 / 뒤 설명은 반대 — 측정이 맞음). 34 경우 일치.
- Texture Borders (`selectUVBorderComponents`): UV 셸 경계 (메시 경계 + 이음) [O]; UV Shell 마스크에서는 Maya 도 아무것도 안 함 → 경고.
- Non-Overlapping (`selectUVOverlappingComponents 0 0`): 양의 넓이로 겹치지 않는 면 / 교차 · 겹침 없는 변 / 같은 자리 다른 UV 없는 UV [O].
- Unmapped Faces (`selectUnmappedFaces` = polyCleanup 넓이 0, 허용 1e-6) [O]; delegated: kit 의 Delete UVs (UV 를 (0,0) 으로) 와 맞음.
- Filter Selection Connected / Contained Faces (`textureWindow -rf / -if`, GUI 전용) [I]; delegated: 켤 때의 선택으로 고정 (Maya 는 선택을 따라감).
- Convert Selection > To Connected Faces (`polyListComponentConversion -tf`) [O], Edit > Unpin All (`polyPinUV -op 2`) [O].
- View > Isolate Select > Add / Remove / Remove All (`textureEditorIsolateSelect 1 / 2 / 0`) [O 집합, I 표시]; Ctrl+1 = Remove All + Add + 보기.

### C 연결 (메인)

- `ui/editor_menu_map.py` 18 행 매핑; `ui/notices.py`: 쓰는 회색이 없어진 규칙 (`UV Editor/Edit`, `UV Editor/Select/Convert Selection`)
  지움, `UV Editor/Select` · `View/Isolate Select` 문구 고침, Symmetrize 2 개 notice.
- 마킹 메뉴: 이 명령들의 회색 항목이 없음 (UV 마킹 메뉴의 Texture Borders / Unpin 은 이미 동작) — 연결할 것 없음.
- 모듈 자리 (`uv_modify.py`, `uv_select_178.py`) 는 레인 시작 전에 메인이 만들어 `operators/__init__` 에 등록 (두 레인이 같은 파일을 안 고치게).

## 검증

- menu_count: UV Editor **136 / 172** (118 → 136, 목표 ≥ 135), 회색 notice 없음 0, menu_consistency 0 쌍.
- 헤드리스 전체 `ALLSET_SANDBOX=s178full python tests/run.py`: **1649 / 1649** (177 끝 1628 + `test_step178_uv_modify` 8 +
  `test_step178_uv_select` 13). UV 좌표는 재구성한 Maya 메시에서 mayapy 와 1e-4 안 (최대 2e-7), 선택 규칙은 정확히 같은 성분.
- GUI `gui_step178_uv_map_border` 5 / 5: 줄이고 돌린 pPlane UV → Map Border 뒤 경계 UV 40 / 40 이 사각형 위 + 꼭짓점 4 개,
  Texture Borders / Back-Facing / Match Grid 메뉴 실행. 샷 (`tmp/s178/shots/gui_step178_map_border.png`) 직접 봄: 경계가 0-1 사각형,
  안쪽 UV 그대로 (Maya Map Border 와 같은 모양).
- GUI 전체 묶음은 돌리지 않음 (CLAUDE.md step 141 규칙).

## 남은 것

- Symmetrize (Modify / Tools): Maya 동작을 측정 못 함 → notice.
- UV Sync 꺼진 채 메시 면만 선택하고 UV 는 선택 안 했을 때 Map Border 가 FINISHED 를 내지만 바꾸는 것이 없음 (GUI 테스트 첫
  실행에서 봄) — Maya 라면 선택이 없다는 경고; 경고로 바꾸는 것은 다음에.
- Distribute UVs / Match Grid 의 "면만 선택" 오류 경우는 UV Sync 꺼진 kit 선택과 구분이 안 돼 테스트 안 함.
- Filter Selection 은 켤 때의 선택으로 고정 (Maya 는 이후 선택 변경을 따라감).
