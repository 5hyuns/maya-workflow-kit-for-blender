# Step 77 — 편집 모드 Insert / D 컴포넌트 피벗 + 피벗 방향

재점검 4차 backlog 6 (docs/PLAN.md 「재점검 4차」 6, 대응표 D/Insert 가 Partial 로 남은 이유: 편집 모드 Insert 없음).

## 근거

- D 홀드 = 피벗 편집 (`ctxEditMode -buttonDown/-buttonUp`), Insert = 토글 (`ctxEditMode`) — research/maya/interaction.md:124-125.
  컴포넌트 모드에서도 같은 명령 (매니퓰레이터가 피벗 매니퓰레이터로 바뀜).
- D + 컴포넌트 클릭 = 피벗 위치 스냅, "Snap pivot orientation" 이 켜져 있으면 방향도 — interaction.md:127;
  Move 툴 피벗 옵션 팩토리 기본 snapPivotPos True, **snapPivotOri True** — research/maya/workflows/pivot_snap.md:27 (P13).
- 컴포넌트 매니퓰레이터는 bbox 중심 (P11, pivot_snap.md; `pivot.MAYA_PIVOT_POINT['EDIT_MESH']`).
- 피벗 방향 = Move 툴 Custom 축 (P8) — 오브젝트 모드는 step 59 의 "Maya Pivot" 오리엔테이션 (Move 슬롯 1).
- 지금 kit: Mesh D = `maya_kit.hold(component_pivot)` (3D 커서 피벗 + 커서 툴, step 18), Insert 는 Object Mode 만
  (`keymap/maya_patches.py:179`).

## 계획

1. **세션 정리** (`operators/hold.py`): 편집 모드 피벗 편집을 `ComponentPivotEdit` 하나로 — `start(context)` (영역·이전 툴·
   피벗 포인트·커서 위치/회전·커서 툴 방향 저장 → 피벗 = 3D 커서, 툴 = 커서 툴, 커서 툴 방향 = GEOM) / `finish(context)`
   (툴·커서 툴 방향 복원, 피벗 포인트 = `component_pivot_after`, 커서 회전이 바뀌었으면 "Maya Pivot" 오리엔테이션).
   D 홀드와 Insert 토글이 같은 세션을 쓴다.
2. **Insert 토글**: `maya_kit.pivot_toggle` 이 모드로 갈린다 — 오브젝트 모드 = 지금 그대로 (Affect Only Origins),
   메시 편집 모드 = 세션 켜기/끄기. 키맵 "Mesh" INSERT 추가 (IC Mesh 에 INSERT 없음 — 그림자 검사로 확인).
   - 세션이 켜진 동안 D 를 누르면 세션을 끈다 (Maya 에서 D 탭 = 토글 [I], interaction.md:124).
   - 세션 중 편집 모드를 떠나면 (Tab / F8 / 오브젝트 모드) 0.25 s 타이머가 세션을 닫는다: 피벗·커서 툴 방향은 바로,
     툴은 그 모드에서만 바꿀 수 있으므로 다음에 메시 편집 모드로 돌아올 때 복원.
3. **방향 (snapPivotOri True)**: 세션 동안 커서 툴 방향 = GEOM (클릭한 면 법선에 커서 축이 맞음, Blender 의 컴포넌트 클릭
   피벗 방향 대응). 끝날 때 커서 회전이 시작 때와 다르면 `pivot.set_custom_orientation(context, 커서 회전 3x3)` → Move 슬롯 1 =
   "Maya Pivot" (오브젝트 모드와 같은 개념이 편집 모드에서도 이어짐). 회전이 그대로면 방향은 건드리지 않는다.
4. **탭으로 지우기**: 커서를 옮기지 않고 끝내면 사용자 피벗을 지운다 — 이전이 CURSOR 면 Maya 컴포넌트 매니퓰레이터 위치
   **BOUNDING_BOX_CENTER** (P11; step 18 의 MEDIAN_POINT 는 step 59 이전 값이라 바꿈 — delegated), 아니면 이전 값.
5. 상태 표시: 세션이 켜져 있으면 툴바에 커서 툴, 인뷰 메시지 없음 (Maya 도 피벗 매니퓰레이터만 바뀜).
6. 다음 단계와의 관계: 78 키 묶음의 Shift+Q / Alt+Q 는 다른 키. 79 3D Cut and Sew 는 UV 툴 — 무관.

## 검증 계획

- 헤드리스: `component_pivot_after` (BBOX), 세션 start/finish 순수 부분 (툴·피벗·방향 결정), Mesh INSERT 키맵 항목,
  `pivot_toggle` 이 편집 모드에서 세션을 켜고 끔 (오버라이드), 회전이 바뀌면 "Maya Pivot" 슬롯 1.
- GUI: F9 + Insert → 커서 툴 + 피벗 CURSOR → 뷰포트 클릭/드래그 → 커서 위치 바뀜 → Insert → 이전 툴 (Move) 복귀, 피벗
  CURSOR 유지, 면 클릭이면 "Maya Pivot" 방향; Insert 켠 채 Tab → 피벗 복원, 다시 편집 모드 → 툴 복원.
- 전체 테스트, dogfood, 대응표 D/Insert 재평가 (`keymap/mapping.py` EnterEditMode, PLAN 대응표).

## 한 것

- `operators/hold.py`: 편집 모드 피벗 편집 = `ComponentPivotEdit` (`hold.COMPONENT`) — D 홀드와 Insert 토글이 공유 (계획 1-4).
  - start: 이전 툴·피벗 포인트·커서 위치/회전 저장 → 피벗 CURSOR, 커서 툴, **커서 툴이 활성이 된 뒤** 그 툴의 방향 = GEOM
    (툴 옵션은 툴마다 따로라 이전 툴에 쓰면 안 먹음 — 첫 헤드리스 실행에서 확인).
  - finish: 피벗 = `component_pivot_after` (탭 = BOUNDING_BOX_CENTER, step 18 의 MEDIAN_POINT 에서 바꿈 — delegated),
    커서 툴 방향 복원, 커서가 옮겨지고 회전도 바뀌었으면 `pivot.set_custom_orientation` → Move 슬롯 1 "Maya Pivot".
  - 편집 모드를 떠나면 0.25 s 타이머가 세션을 닫고, 툴은 다음 편집 모드 진입 때 복원 (`pending_tool`).
  - Insert 가 켠 세션 중 D = 세션 끔.
- `maya_kit.pivot_toggle`: 메시 편집 모드에서는 세션 토글, 오브젝트 모드는 그대로. 키맵 "Mesh" INSERT 추가.
- `pivot.set_custom_orientation`: 편집 모드 `create_orientation` 이 선택 때문에 실패하면 `use_view=True` 로 만든 뒤 행렬을 덮어씀.
- 대응표 `keymap/mapping.py` EnterEditMode / EnterEditModePress 메모, `docs/keymap_mapping.md` 재생성 (Insert = Object Mode + Mesh).
- PLAN 재점검 4차 6 = 완료, 대응표 D/Insert Partial → **Done** (조작 / 단축키 12/1/0/0, 합계 28/3/0/2 = 85 %).
- manual_checks 3 항목, CLAUDE.md 한 줄.

## 검증

- 헤드리스 `tests/test_step77_component_pivot.py` 7/7 (키맵, 탭 규칙, `turned`, Insert 켬/끔 + GEOM + 피벗 유지, 회전 → "Maya Pivot"
  행렬, 편집 모드 떠나면 닫힘 + 툴 복원 대기, 오브젝트 모드 Insert 그대로). step 18 / 59 테스트 갱신 후 통과.
- GUI `tests/gui/gui_step77_component_pivot.py` 11/11: F9 → W (Move) → Insert = 커서 툴 + CURSOR → +X 면 클릭 = 커서 x 1.0, 커서 Z 축 = 면 법선
  → 드래그 = 커서 이동 → Insert = Move 툴 복귀 + CURSOR 유지 + Move 축 "Maya Pivot" → Insert 켠 채 F8 = 닫힘 → F8 = Move 툴 복귀.
  스크린샷 2장 (커서 툴 / 피벗 위치·면 방향 매니퓰레이터) 확인.
- 전체: 헤드리스 619/619, GUI (기본 배율) 539/539, dogfood 47/47 (콘솔 오류 0).

## 남은 것

- Maya 피벗 편집 RMB 메뉴 (Pin component pivot, Reset, Snap pivot position/orientation 토글 — interaction.md:81) 없음.
- 커서 툴 클릭은 면 표면에 놓음: Maya 의 정점/엣지 클릭 스냅 (snapPivotPos) 은 V / C 홀드 스냅으로만.
- "Maya Pivot" 축은 탭으로 피벗을 지워도 남는다 (W 메뉴로 World 로). Pin (선택이 바뀌어도 피벗 유지) 은 Blender 커서 피벗이라 항상 유지.
