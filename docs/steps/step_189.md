# Step 189 — Mesh Display and greyed twins

backlog_183.json #7: audit 13 #6 + #10 + BS1 / BS5 (`docs/steps/step_182_quant.md`, `step_182_remaining.md`).

## 계획

| 레인 | 내용 | 파일 | 누가 |
|---|---|---|---|
| A | 노멀 (Set Vertex Normal + Lock / Unlock / Average / Set to Face mayapy 대조), 메인 UV > Delete UVs 연결 + `menu_consistency` runtime 별칭, 패널 Show IK Handles / NURBS CVs / NURBS Hulls / Image Planes, Surfaces > Insert Isoparms 옵션 창 | `operators/normals_maya.py`, `tools/menu_consistency.py`, `ui/panel_menu_data.py`, `option_windows_surfaces.py` | 서브에이전트 (worktree) |
| B | 색: Apply Color, Rename / Modify Current Set, Set Keyframe for Vertex Color, Prelight + bake sets, Per Instance Sharing | `operators/color_sets_maya.py` (창은 둘 다 `option_windows_mesh_display.py`) | 서브에이전트 (worktree) |
| C | BS5 Status Line Construction History 토글 (mayapy 측정) | `operators/prim_history.py`, `operators/extrude.py`, `ui/input_line.py`, `ui/status_line.py` | 메인 |

A / B 는 같은 `menu_map.py` / `notices.py` / `operators/__init__.py` 를 다른 줄에서 고치므로 worktree 로 나누고 메인이 합침.
mayapy 측정 → 구현 순서는 레인 안에서만 순차 (측정값이 구현 규칙).

검증: `tools/menu_count.py` Mesh Display ≥ 60 %, `tools/menu_consistency.py` 0 (별칭 포함), 헤드리스 전체, `tests/gui/run.py -k step177`.

진행 메모: 처음 띄운 두 레인 서브에이전트 (A 노멀 + 쌍둥이, B 색) 는 세션이 끊기며 멈춤 — A 는 `tools/menu_consistency.py`
별칭 규칙만, B 는 mayapy 색 측정 JSON 3 개 (`research/maya/re/mesh_display_184_colors*.json`) 만 남김. 둘 다 메인으로 가져와
나머지는 메인에서 순차로 끝냄 (사용자 지시: 백그라운드 서브에이전트 대기 금지). 두 worktree
(`.claude/worktrees/agent-a1d69614…`, `agent-aed8f880…`) 는 삭제가 훅에 막혀 남아 있음 (내용은 반영됨).

## 한 것

### Mesh Display 15 → 25 / 39 (38 → 64 %)

- 노멀 (`operators/normals_maya.py`, mayapy 95 경우 `research/maya/re/mesh_display_184.md` / `_normals.json`):
  Set Vertex Normal (새, ❒ Maya 창 X/Y/Z 1 0 0), Lock / Unlock Normals (이제 선택한 정점만 — 이전 Blender op 는 메시 전체),
  Average (Maya 거리 0.1 규칙: 선택 정점 + 거리 안 정점을 묶어 단위 코너 노멀 합, shell 사이도; 이전 `mesh.average_normals` 는
  거리 규칙 없음), Set to Face (Maya: 면 노멀 + 하드 엣지 + 잠금 해제, ❒ Set user normal = 잠금). Maya 잠금 = Blender custom
  split normal, 해제 = 계산 노멀. 0 벡터는 하드 엣지에서 "auto" 로 안 읽혀 (측정) 해제 코너엔 계산 노멀을 씀.
- 색 (`operators/color_sets_maya.py`, `research/maya/re/mesh_display_184_colors.md`): Apply Color (Replace / Add / Subtract /
  Remove, 정점 / 면 / 오브젝트, 값 안 자름, 세트 없으면 colorSet1 — mayapy 일치), Rename Current Set (Maya 이름 규칙),
  Modify Current Set (polyColorMod 규칙을 13 경우에서 역산: clamp → HSV (채도 안 자름) → 채널 램프 → intensityScale(max) 곱 —
  13 / 13 일치), Set Keyframe for Vertex Color, Prelight (Cycles diffuse bake → 현재 세트, 엔진 복원; ❒ Maya 창), Assign New /
  Existing Set, Edit Assigned Set (vertexBakeSetN, Maya 공장 속성), Per Instance Sharing > Select Shared Instances.
- 남은 회색 14 (notice): Color Material Channel 6, Material Blend Setting 7 (Blender 는 재질의 Color Attribute 노드로 섞음),
  Share Instances (Blender 인스턴스는 늘 공유). 쓰이지 않게 된 "Mesh Display" 범주 notice 삭제.

### 회색 쌍둥이 (BS1 / #10)

- `tools/menu_consistency.py`: 서명 = 키 집합 (annotation + `cmd:<명령 문자열>`, 명령 문자열이 같은 runTimeCommand 의
  annotation, `…WithoutHotkey` = 그 이름) — 라벨이 같고 키가 하나라도 겹치면 쌍둥이. 새로 찾은 3 개 연결: 메인 UV > Delete UVs
  (= `allset.uv_delete`, 틀린 "UV map 지우기" notice 문구 고침), nHair > Modify Curves > Smooth / Straighten (= Curves 의
  SmoothHairCurves / StraightenCurves). `menu_consistency` 0.
- 패널 Show: IK Handles (kit IK 핸들 empty 를 뷰 레이어에서 숨김 + 표식, 표식 있는 것만 되돌림), Image Planes (Alt+4 와 같은
  image empty 표시 플래그) 작동. NURBS CVs / Hulls 는 Blender 가 Edit Mode 에서만, 늘 그리므로 회색 유지 (구체 notice).
  패널 메뉴 67 → 69 / 111.
- Surfaces > Insert Isoparms ❒ = Maya 창 (Insert location At selection / Between selections, Multiplicity Set / Increase,
  개수, Keep original — insertKnotSetOptionVars.mel:50-66); 옵션 상자 generic 목록에서 빠짐.

### Construction History (BS5)

- mayapy (`research/scripts/construction_history_189_mayapy.py`): 토글을 끄면 메뉴 runtime 명령이 `-ch 0` — 프리미티브에
  polyCube1 / makeNurb* 노드 없음, PolyExtrude / BevelPolygon 노드 없음; 직접 부른 `cmds.polyCube()` 는 토글 무시; File > New
  뒤에도 유지 (optionVar 아님). kit: `WindowManager.allset_construction_history` + Status Line 버튼
  `allset.construction_history` (회색 → 실제 토글), 끄면 `prim_history.create_object` 가 노드를 안 남기고 `extrude.keep` 이
  polyExtrude / polyBevel 기록을 안 남김.

## 검증

- `tools/menu_count.py`: Mesh Display 25 / 39 (64 %), Modeling 192 → 203 (58 %), 전체 837 → 850 / 1486 (57.2 %), 회색 notice 없음 0;
  패널 메뉴 69 / 111, Status Line 회색 9 → 8. `--options`: Insert Isoparms 는 generic 이 아님 (창), kit 옵션 창 110 + Prelight. (정정, step 190: 처음 적은 "generic 0" 은 출력 필터 실수 — generic 전체는 34.)
- `tools/menu_consistency.py`: 0 (별칭 포함; 별칭 전에는 3).
- 헤드리스: 새 test_step189_{normals,colors,twins,history} 20 / 20 (노멀 66 mayapy 경우, 색 Apply 14 / Modify 13 경우);
  전체 1725 / 1727 → 실패 2 (step177 / step75: 회색 Construction History 가정) 고친 뒤 마지막 전체 1727 / 1727.
- GUI: `-k step177` 9 / 9, 새 `gui_step189_mesh_display` 3 / 3 + 스크린샷 (Show 메뉴: IK Handles / Image Planes 체크 행,
  Status Line: history 버튼 꺼짐) 눈으로 확인.

## 남은 것 / 한계

- Blender custom normal 은 16 bit 각도 2 개 저장 (~3e-4 오차, 테스트 허용 1e-3); 계산 노멀과 같은 잠금은 저장 못 함.
  Maya 의 부드러운 노멀은 면적 가중, Blender 는 코너 각 가중 (Mesh Display 명령 밖의 차이, 기록만).
- Set to Face: Maya 가 굽은 strip / 컴포넌트 선택에서 아무것도 안 바꾼 이유 [U] — kit 은 큐브 규칙을 선택 면에 적용 (delegated).
- Prelight 결과는 mayapy 로 못 잼 (렌더러 없음) [U]; Modify Current Set 은 한 번 적용 (Maya 는 살아 있는 노드), 램프 2 점 선형만.
- Apply Color 의 Individual channels, Color Material Channel / Material Blend Setting / Share Instances 는 notice.
- Prelight ❒ 창 값을 저장한 뒤의 일반 클릭은 bake set 대신 창 값을 씀 (delegated).
