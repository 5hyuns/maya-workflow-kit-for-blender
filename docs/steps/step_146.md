# Step 146 — Maya option boxes open without a drag (#82)

## 계획

문제 (#82, 재점검 9차 점수 15): Maya 메뉴 항목의 ❒ 를 클릭하면 명령이 실행되고, 옵션 창은 길게 누른 뒤 Blender 가 아래에 여는
"Option Box" 줄까지 끌어 내려가 놓아야만 열린다 → Maya 창 75 + 대화상자 22 가 사실상 숨겨져 있다.

먼저 잰 것 (GUI 탐침 `tests/gui/gui_step146_probe*.py`, 끝난 뒤 지움; Blender 4.5 소스 `interface_handlers.cc`,
`interface_layout.cc ui_item_menu_hold`, `interface_region_menu_popup.cc`):

1. 메뉴 항목 연산자는 EXEC 로 불린다 (`invoke` 가 안 불림) → 클릭 위치 · event 없음. 연산자 context 는 메뉴를 연 3D View WINDOW
   (step 143 측정과 같음). 팝업 메뉴의 위치 · 폭은 Python 에서 알 수 없다 → **❒ 부분만 클릭으로 구분하는 것은 불가**.
2. 시뮬레이션에서 Shift / Ctrl / Alt + 클릭 (마우스 이벤트에 수정키를 싣든, 키를 먼저 누르든) = 메뉴 항목이 **아무것도 실행 안 함**.
3. hold: `BUTTON_AUTO_OPEN_THRESH` 0.2 s 뒤 버튼은 취소되고 hold 함수가 hold 메뉴를 **따로 된 팝업**으로 연다 (`UI_popup_menu_end`,
   방향 DOWN). hold 메뉴의 `draw` 가 그 순간 불린다. `layout.activate_init` 은 줄을 강조만 할 뿐 실행하지 않는다. hold 메뉴 밖에서
   놓으면 `UI_BLOCK_POPUP_HOLD` → 취소.
4. 타이머에서 옵션 창 (`invoke_props_dialog`) 을 열면 열리지만 Maya 메뉴와 hold 메뉴가 그 아래 그대로 남는다.
5. Blender 의 hold 경로 (Option Box 줄에서 놓기) 도 **부모 Maya 메뉴를 닫지 않는다** — 옵션 창을 닫으면 메뉴가 그대로 (step 143 부터).
6. 메뉴는 마우스가 safety 사각형 밖으로 나가면 닫힌다 (`UI_BLOCK_MOVEMOUSE_QUIT`) — 단, 그 뒤에 만들어진 메뉴 (서브메뉴) 가
   열려 있으면 안 닫힌다 (`ui_mouse_motion_towards_check` "annoying fix"). 시뮬레이션 MOUSEMOVE 로 확인 (메뉴 픽셀 24 → 65).
7. `Window.cursor_warp` 는 `--enable-event-simulate` 에서는 이벤트를 만들지 않지만, 보통 GUI Blender 에서는 OS 이동이 들어와 메뉴가
   닫힌다 (`tmp/real146/` 스크립트로 확인: Display 메뉴 열고 AWAY warp → 닫힘).
8. 타이머에서 `INVOKE_DEFAULT` 로 부른 연산자의 event = 창의 최신 상태 → 지금 마우스 위치를 알 수 있다.

결정 (delegated):
- **hold = 끌기 없이**: hold 메뉴가 열리면 (draw → 0 s 타이머, 왼쪽 버튼이 아직 눌려 있을 때만) 포인터를 그 메뉴의 "Option Box ❒"
  줄로 옮긴다 (`allset.option_box_point move=HOLD_ROW`, 줄 높이 1.5 배라 항목 어디를 눌렀든 들어감, 아래 공간 없으면 위로). 그대로
  놓으면 Blender 자신의 메뉴 경로로 실행 → 사용자는 0.2 s 누르고 놓기만 하면 된다. 버튼을 누른 채로 팝업을 여는 일은 없다
  (안전: 놓기 이벤트를 받는 것은 Blender 의 hold 메뉴).
- **부모 메뉴 닫기**: hold 줄에서 실행된 option box (`from_hold=True`) 는 그 자리에서 포인터를 창 반대쪽 끝으로 보낸다 (AWAY;
  hold 메뉴가 닫힌 뒤 Blender 가 만드는 mouse move 가 그 점을 쓰므로 아래 줄의 서브메뉴가 열리기 전에 메뉴가 닫힌다), `AWAY_TICK`
  0.05 s 뒤 제자리로 (BACK) 돌려놓고 옵션 창을 그 자리에 연다. 배경 실행 (`bpy.app.background`) 은 바로 실행.
- **Shift / Ctrl + 클릭** = 옵션 상자: `menu_item.execute` 가 OS 키 상태 (`keystate`, Windows `GetAsyncKeyState`; VK 코드 추가) 로
  본다. 시뮬레이션에선 Blender 가 수정키 클릭을 실행하지 않으므로 실제 하드웨어 확인은 manual_checks.
- **툴팁**: ❒ 가 있는 항목 툴팁 끝에 `BOX_TIP` ("❒ Option box: press and hold the item, then let go (or Shift / Ctrl+click)").
- ❒ 부분 클릭 = 불가 (1). Maya 처럼 '클릭' 은 아니지만 0.2 s hold + 놓기가 가장 가까운 것.

순서 이유: 측정 → 설계 → 구현이 한 파일 (`ui/menu_sets.py`) 이라 레인을 나누지 않음 (병렬할 독립 작업 없음).

## 한 일

- `src/allset/ui/menu_sets.py`: `BOX_TIP`, `modifier_held()`, `_point_at_hold_row_later`, `_close_menu_then_open`,
  `ALLSET_OT_option_box_point` (HOLD_ROW / AWAY / BACK, `LAST_WARP` 기록), `ALLSET_MT_option_box` (줄 1.5 배, "Option Box ❒",
  `from_hold`), `ALLSET_OT_menu_option_box.from_hold`, `ALLSET_OT_menu_item` Shift/Ctrl 분기 + 툴팁 줄.
- `src/allset/operators/keystate.py`: LEFT/RIGHT_SHIFT, LEFT/RIGHT_CTRL VK 코드.
- 테스트: `tests/test_step146_option_box.py` (6), `tests/gui/gui_step146_option_box.py` (Display>Grid, Key>Set Key,
  Constrain>Parent, Key>Cut Keys hold → 놓기 = 옵션 상자, 메뉴 닫힘 픽셀 확인, 라벨 클릭 = 명령), `gui_step143_user.py` 문구.

## 검증

- 헤드리스: 관련 7 파일 69/69, 전체 **1313/1313** (157 파일).
- GUI (바뀐 모듈): step146_option_box 21/21, step103 / step108 / step140 옵션 창 · 메뉴, step143_user — 5 파일 51/52; 실패 1 =
  `gui_step143_user` 첫 클릭 (Display 메뉴가 가끔 한 줄 어긋나 열려 Heads Up Display 를 누름; 클릭 경로는 이번에 안 바뀜) →
  혼자 3 번 15/15, step140 + 143 함께 24/24 = 타이밍 흔들림 (약 6 번에 1 번). 스크린샷 (Set Key Options 창, 메뉴 닫힘) 직접 확인.
- 보통 GUI Blender (시뮬레이션 없음) 에서 AWAY warp 가 Display 메뉴를 닫는 것 확인 (`tmp/real146/`, 화면 2 장).

## 남은 것

- 실제 하드웨어: hold → 놓기, Shift / Ctrl + 클릭, AWAY/BACK 포인터 깜빡임 느낌 → `docs/manual_checks.md` Step 146.
- ❒ 부분만 클릭 (Maya 그대로) 은 Blender 가 버튼 안 위치를 Python 에 주지 않아 불가 — Blender 쪽 API (extra operator icon 의 Python
  노출) 가 생기면 다시.
- 마킹 메뉴 / 셸프의 옵션 상자는 이번 범위 밖 (각각 자기 경로).
- Wayland / 커서 이동이 막힌 환경에선 warp 가 안 되어 예전처럼 끌기 필요 (Windows 대상이라 확인 안 함).
