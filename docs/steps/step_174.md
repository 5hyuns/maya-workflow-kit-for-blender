# Step 174 — Component mode keeps the transform tool

Audit 12 (step_173.md G5, step_173_quant.md §7 #1): W then F9 / F10 / F11 / RMB Vertex entered edit mode with Blender's
Select Box and no manipulator; Maya keeps Move / Rotate / Scale / Select.

## 계획

1. Maya GUI 측정 (`currentCtx`) → `research/maya/re/tool_modes_174.md`.
2. 한 곳에서: 모드가 바뀌면 (어느 경로든 — F8 / F9–F11 / RMB 마킹 / Tab / 메뉴) 새 모드가 이전 모드의 Q / W / E / R 도구를 받는다
   (`operators/tool_keys.py`: depsgraph handler → 0 s 타이머 `tool_set_by_id`, 0.25 s 감시 타이머가 놓친 전환 보충). 경로마다 고치지
   않음 (delegated: 킷 · Blender 의 모드 전환 경로가 20 곳 넘음).
3. GUI 테스트 + 대조 실행 (수정 전 실패 확인), 헤드리스 규칙 테스트.

## 한 것

- 측정: Q / W / E / R 는 두 방향 모두 유지, 컴포넌트에서 고른 W 도 F8 뒤 유지, T (ShowManips) 는 F9 뒤 selectSuperContext.
- `tool_keys.carried_tool` (bpy 없는 규칙): CARRY_MODES (OBJECT, EDIT_MESH / CURVE / SURFACE / LATTICE / ARMATURE / METABALL, POSE)
  사이에서만, sacred 도구만, `builtin.transform` (킷 T) 는 Select Box 로.
- `_carry`: 전환한 명령이 새 모드의 도구를 직접 골랐으면 (Shift+RMB Target Weld, Multi-Cut 같은 `allset.menu_tool`) 넘기지 않음 —
  0.25 s 마다 모드별 도구를 기억 (`_seen`) 하고, 전환 뒤 다르면 일부러 고른 것; 처음 들어가는 모드는 Blender 기본 Select Box 가 아닌
  도구면 일부러 고른 것. D / Insert 피벗 편집 (`hold.COMPONENT`) 중에는 손대지 않음.
- 처음 구현은 gui_step64 의 Shift+RMB Target Weld 를 Select 로 덮었다 → 위 규칙으로 고침.

## 검증

- GUI `gui_step174_tool_modes.py` **21 / 21** (W F9 F8, E F10 F8, R F11, W in component F8, Q F9 F8, E + RMB Vertex; kit Move /
  Scale 매니퓰레이터 widget `ALLSET_GGT_xform`). 대조: 수정 전 코드로 같은 테스트 **8 실패** (F9 → select_box 등).
- 관련 GUI: step64 / step129_component_mode_menus / step144_poly / step77 / step18 / step57 / step134_display / step59 / step144_loop
  모두 통과 (83 + 73).
- 헤드리스 `test_step174_tool_modes.py` 3 / 3, 전체 **1603 / 1603**.

## 남은 것

- Maya Universal Manipulator (Ctrl+T) 는 측정 안 함 (킷 Ctrl+T = builtin.transform → T 와 같은 규칙).
- 손 확인: `docs/manual_checks.md` Step 174.
