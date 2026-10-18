# Step 91 — 뷰 표시 수정 (부모 관계 점선, RMB 목록 위 HUD, AE 전환 때 탭 순서)

재점검 6차 backlog 2 (docs/PLAN.md 「재점검 6차」 새 발견; docs/steps/step_89.md 스크린샷 `a6_04`, `a6_05`, `a6_08`).

## 근거

- **Maya 는 부모–자식 선을 그리지 않는다** — 팩토리 Maya 2022 실행 (MAYA_APP_DIR = `tmp/maya_app`, 스크립트
  `research/scripts/maya_parent/parent.py`, 끝나면 스스로 종료): 그룹 피벗 (원점) 에서 4 단위 떨어진 pCube1, pCube2 아래 떨어진 pCube3 —
  선택 없음 / 자식 선택 / 부모 선택 세 장 (`research/maya/screens/parent/parent_01..03_*.png`) 어디에도 선 없음. Blender 는
  `overlay.show_relationship_lines` (기본 켬) 로 점선을 그림.
- **HUD**: Adjust Last Operation 패널은 3D View 의 'HUD' 영역 (뷰 위에 겹쳐 그려짐). `marking/draw.REGION_TYPES` 에 없어서 마킹 메뉴
  그림이 그 밑에 깔림 (step 52 는 창 전체 영역마다 POST_PIXEL 핸들러).
- **탭 순서**: Blender 는 사이드바 탭을 영역이 이미 가진 패널 인스턴스 순서로 그린다. 템플릿에는 Channel Box 패널 인스턴스만 저장돼
  있고 AE / Modeling Toolkit 패널은 처음 전환할 때 새로 생겨 목록 끝 (C 패널 Item > Transform 뒤) 에 붙음 → "Item" 탭이 위로.

## 계획 (delegated)

1. 부모 관계 점선: `tools/make_startup.py` `maya_views()` 에서 모든 3D 뷰 `overlay.show_relationship_lines = False` → 다시 생성.
   Maya 모드 전환 (`switch.enter_layout`) 은 템플릿의 Maya 레이아웃 워크스페이스를 붙이고, Blender 로 돌아가면 사용자의 원래 워크스페이스로
   돌아간다 — 그래서 템플릿 뷰만 끄면 "Maya 모드 동안" 이 되고, 사용자 자신의 뷰 (공간 데이터) 는 건드리지 않아 되돌릴 것도 없다
   (결정 7 사용자 설정 보호와 같은 방향). 키 하나로 전체 뷰를 바꾸는 장치는 만들지 않음.
2. HUD: `REGION_TYPES` 에 'HUD' 추가 (`draw_handler_add` 가 받는지, 그 영역에서 콜백이 실제로 도는지 4.5 / 5.x GUI 에서 측정).
3. 탭 순서: Channel Box 패널을 독 패널 하나로 — 항상 poll 되고 `maya_kit_dock` 에 따라 CB / AE / Modeling Toolkit 을 그림
   (`attribute_editor.draw_panel`, `modeling_toolkit.draw`). AE / MTK 패널 클래스는 없앰 (AE 의 접히는 "Attribute Editor" 제목 줄도 사라짐 —
   Maya AE 에는 없음). "Channel Box" 카테고리 인스턴스가 늘 있으므로 탭 위치가 바뀌지 않음.
4. 다음 단계 고려: 93 (Shift+Q 체크 표시) 은 `draw.checked` — 이번 변경과 겹치지 않음. 94 (피벗 RMB 메뉴) 도 같은 draw 경로를 쓰므로
   HUD 위 그리기 혜택을 그대로 받음.

## 한 것

- `tools/make_startup.py`: 3D 뷰 `show_relationship_lines = False` (근거 주석), `startup.blend` 다시 생성.
- `marking/draw.py`: `REGION_TYPES` 에 'HUD'.
- `ui/channel_box.py` `MAYAKIT_PT_channel_box`: poll 없음, draw 가 독 모드별로 AE (`attribute_editor.draw_panel`, 새 함수) / MTK
  (`modeling_toolkit.draw`) / CB. `MAYAKIT_PT_attribute_editor`, `MAYAKIT_PT_modeling_toolkit` 삭제. 테스트 (step 11 / 55 / 63) 를 새 구조로.
- `research/scripts/maya_parent/` (launch.ps1, userSetup.py, parent.py) + `research/maya/screens/parent/` (research 는 git 밖).

## 검증

- GUI `tests/gui/gui_step91_view_chrome.py` 8/8 (4.5 와 5.2.2 둘 다): 템플릿 3D 뷰 15 개 모두 선 꺼짐; 3 키 → HUD (398, 99, 200, 30);
  RMB 목록이 HUD 를 가로지르는 점 (545, 112) 의 스크린샷 픽셀 = 목록 배경 (0.322) — **대조 실험**: 'HUD' 를 빼고 돌리면 같은 점이 0.592
  (HUD 패널) 로 FAIL; Ctrl+G 그룹; Ctrl+A → AE, 사이드바는 Channel Box 탭.
- 스크린샷 직접 확인 (`tmp/shots91/`): `gui_step91_rmb_over_hud.png` (HUD 가 목록에 가려 안 보임), `gui_step91_group_no_line.png` (그룹 피벗과
  큐브 사이 점선 없음), `gui_step91_ae_tabs.png` (Channel Box 탭이 맨 위, Item 아래, AE 제목 줄 없음).
- 헤드리스 관련: step 11 15/15, 55 10/10, 63 10/10, 50 7/7, enable_disable 4/4, step 8 11/11, step 52 8/8.
- 전체 헤드리스 `python tests/run.py`: **685/685** (82 파일). 전체 GUI `python tests/gui/run.py`: **685/685** (72 파일).
- `python tools/dogfood.py`: **47/47**, 콘솔 0 (`11_attribute_editor.png`: Channel Box 탭 맨 위, AE 제목 줄 없음).

## 남은 것

- 템플릿이 아닌 3D 뷰 (사용자가 직접 만든 워크스페이스, 예전 kit 로 저장된 파일) 는 부모 관계 점선이 그대로 — 사용자 공간 데이터는 건드리지
  않기로 함 (delegated). 이미 설치된 템플릿 사본은 「Install Maya Layout」 을 다시 눌러야 바뀜 (step 81 과 같은 한계).
- 그룹 (Empty) 을 선택하면 Blender 가 엠프티 축을 주황으로 그림 — Maya 그룹은 선택해도 그려지는 모양이 없음 (그룹 표시 = 다음 재점검 후보).
- 다음: step 92 = Graph Editor 키 묶음 (t, Alt+/, i Insert Key 툴).
