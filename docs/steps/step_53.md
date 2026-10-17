# Step 53 — Blender 5.x 호환 점검과 안전한 설치 (경쟁 우위 ③)

근거: `research/competitors.md` §6 (흔한 불만: Blender 업데이트마다 깨짐, 기존 애드온 삭제, 다른 에디터를 깨뜨림 — Graph Editor
탐색), §2 (경쟁 제품: Maya Config Pro/Lite 5.0–5.2, Hot Box·Maya Groups·Friendly Pivot 4.2–5.2). 결정 4 (대상 Blender 4.5) 는 그대로 —
이번 단계는 5.x 점검과 그것이 드러낸 부분의 최소 대응만.

## 계획

1. 공식 zip (download.blender.org, sha256 확인) 을 `tmp/blender5/` 에 풀어 (포터블, 설치 없음) `python tests/run.py --blender ...`
   로 헤드리스 전체. 샌드박스는 그대로 `tmp/test_env` (BLENDER_USER_* 폴더를 먼저 만듦) — 사용자 실제 설정 안 건드림.
2. 깨지는 API 를 원인별로 묶어 대응 범위를 정함 (delegated): **4.5 동작은 그대로, 5.x 에서는 같은 기능을 그 버전의 API 로** (얇은
   분기). 고치기 어려운 것은 「5.x 에서 부분」 으로 남김. 매니페스트 `blender_version_max` = 확인한 범위의 바로 다음 (`5.3.0`,
   exclusive): 확인 안 된 Blender 에서는 반쯤 깨진 kit 대신 확장 시스템의 「호환 안 됨」 이 나옴 (§6 「업데이트마다 깨짐」).
3. kit 을 켠 뒤 다른 에디터 기본 조작 GUI 테스트 (`tests/gui/gui_step53_editors.py`): Text Editor 입력 (kit 이 다른 곳에 묶은 z / h /
   Space / q w e r / f 포함), Graph Editor A 프레임·클릭 선택·Alt+MMB 팬·Alt+RMB 줌, Node Editor 클릭 선택·Alt+MMB 팬. 4.5 와 5.2.
4. release_check: 「설치가 사용자 애드온·키맵 설정을 바꾸지 않음」. 따로 만든 샌드박스 (`tmp/release_env_user`) 에 사용자 설정을
   심고 (`tools/release_probe.py seed`: 사용자 애드온 켬, 입력·인터페이스 환경설정·undo 단계·테마 바꿈, 저장) → 설치 + 켜기 →
   스냅숏 → kit 끄기 → 스냅숏. 단언: 사용자 애드온·파일 유지, 추가된 애드온 = kit 하나, 테마·인터페이스 그대로, 바뀐 입력 환경설정은
   kit 이 선언한 탐색 프리셋 (`prefs_preset.PRESET`) 안에서만, 활성 키맵 Blender → Maya (선언, step 7), **kit 을 끄면 전부 원래대로**.
   kit 이 켜질 때 Maya 키맵·탐색 프리셋을 쓰는 것은 제품 약속 (step 7·13·30) 이라 그대로 두고, 「되돌릴 수 있음 + 선언된 것만」 을
   단언 (delegated).

## 실측

| | 헤드리스 (처음) | 원인 |
|---|---|---|
| 4.5.x | 407/407 | — |
| 5.2.2 (shim 전) | 5/407 | 켜기 실패: `bl_ui.space_time.TIME_MT_editor_menus` 없음 (5.x 의 Timeline = Dope Sheet 모드) |
| 5.2.2 (켜기 고친 뒤) | 386/407 | 아래 표 |

5.x 에서 깨진 것 (원인별):

| 원인 | 영향 | 대응 |
|---|---|---|
| Timeline 이 Dope Sheet 모드: `TIME_HT_editor_buttons` / `TIME_MT_editor_menus` 없음 ($S52 space_dopesheet.py:198-230, 395-412) | 켜기 실패 (전부) | `ui/time_slider.py` `header_classes()` — 5.x 는 `DOPESHEET_HT_editor_buttons.draw_header` / `DOPESHEET_MT_editor_menus.draw_collapsible` 를 감싸 `mode == 'TIMELINE'` 일 때만 kit 것 |
| IC 키맵 차이: Ctrl+G 가 `wm.call_menu(OBJECT_MT_move_to_collection)`, Node Editor Z `node.viewer_border` 없음, Sculpt 에 Ctrl+Alt+LMB | 키맵 빌드 실패 (엄격 패치) / 충돌 3 | `keymap/patch.STRICT` (4.5 에서만 엄격, 그 밖은 `patch.DRIFT` 에 기록), Ctrl+G 는 연산자와 무관하게 이벤트로 제거, 박스 줌 Sculpt 가림 선언 |
| `rna_xml` → `_rna_xml` | 테마 적용·복원 실패 | `theme._rna_xml()` 둘 다 |
| 테마 구조 재편: 906 값 중 352 개가 5.x 에 없음 (탭·패널·영역 색은 `theme.regions`, 애니 색은 `theme.common.anim`, 새 위젯 `wcol_curve`) | Maya 테마 부분 적용 | `theme.MOVED`: 같은 maya.xml 값을 5.x 위치로 (playhead, 키프레임·채널 21, 사이드바·채널·스크럽 영역), 모든 `wcol_*` 각지고 평평 |
| `mesh.loop_multi_select` 없음 (→ `select_edge_loop_multi` / `select_edge_ring_multi`) | 메뉴·마킹 메뉴 3 항목 | `maya_kit.select_loops(ring)` 이 버전에 맞는 것을 부름 |
| 새 재질은 항상 노드 (Principled) | AE 재질 종류 「material」 → 「standardSurface」 | 5.x 에서 올바른 동작 (테스트만 버전별) |
| `view_layer.objects` 가 동기화 전 지운 오브젝트를 None 으로 줌 | 테스트 도우미 | 테스트만 |
| Python 3.13+: docstring 의 `\s` 경고 | 경고 (나중엔 오류) | 고침 + 새 테스트 (src 전체 컴파일 경고 0) |

## 한 것
- `ui/time_slider.py` 5.x Timeline 분기, `keymap/patch.py` STRICT/DRIFT + `keymap/__init__.py` (`TARGET_VERSION` (4, 5), 드리프트는
  콘솔에 출력), `keymap/maya_patches.py` (Ctrl+G 이벤트 제거, 드리프트 허용, 박스 줌 Sculpt), `theme/__init__.py` (`_rna_xml`, `MOVED`,
  위젯 평평), `operators/component.py` `maya_kit.select_loops`, `menu_map` / `marking/menus.py` 그것을 씀, `status_line.py` 이스케이프.
- 매니페스트 `blender_version_max = "5.3.0"` (4.2 – 5.2.x).
- `tools/release_probe.py` (새) + `tools/release_check.py` 사용자 설정 단언 8 개 (따로 만든 샌드박스), `--shots DIR` (5.x 스크린샷을
  docs 밖에).
- 테스트: 새 `test_step53_compat` (7: 키맵 엄격/드리프트, 테마 왕복 = 사용자 테마 전부 그대로, 옮긴 테마 값, 매니페스트 범위, Timeline
  분기, select_loops, 컴파일 경고), `gui_step53_editors` (9); `tests/kit.py` 스냅숏·test_step5/11/20/38/43/50 버전별.
- 5.x GUI 에서 드러난 것: 영역이 창 가장자리에서 2 px 안쪽 (테스트만 허용 범위), 4.5 템플릿의 타임라인 사이드바가 1 px 로
  로드됨 → Time Slider 버튼 (현재 프레임 + 재생 8) 이 사라짐 → `time_slider.has_slider_panel(space, area)` 가 사이드바 폭까지 보고,
  좁으면 버튼을 Range Slider 줄 (헤더) 에 그림 (스크린샷 확인).

## 검증

| Blender | 헤드리스 (처음) | 헤드리스 (끝) | GUI | 비고 |
|---|---|---|---|---|
| 4.5.x (대상) | 407/407 | **414/414** | **337/337** (0.8) · **336/336** (1.25) | release_check PASS, dogfood 47/47 (콘솔 오류 0) |
| 5.0.1 | — | **414/414** | — | 키맵 드리프트 1 (Node Editor Z) |
| 5.1.2 | — | **414/414** | — | 〃 |
| 5.2.2 LTS | 5/407 (켜기 실패) → 386/407 | **414/414** | **337/337** (0.8, layout 3 파일 다시 돌림) | release_check PASS (사용자 설정 8 단언 포함, 스크린샷 tmp/shots_b52) |

(「끝」 숫자: 전체 실행 뒤 남은 실패 3 (step11 AE 재질 탭 5.x 기대값, select_loops 의 연산자 찾기) 를 고치고 해당 파일을 네 버전 모두
다시 돌림 — 다른 파일은 전체 실행 그대로 통과.) 공식 zip 은 sha256 확인 (5.0.1, 5.1.2, 5.2.2).
- release_check 사용자 설정 단언 (4.5·5.2 모두 PASS): 사용자 애드온 유지·파일 유지·추가 = kit 하나·테마 그대로·인터페이스 그대로·
  바뀐 입력 = 선언된 탐색 프리셋 3 개 (`use_zoom_to_mouse`, `view_rotate_method`, `view_zoom_axis`)·활성 키맵 Blender → Maya (선언)·
  **kit 끄면 전부 원래대로**.
- GUI `gui_step53_editors` 9/9 (4.5·5.2): Text Editor 「azh qwerf」 입력, 마킹 메뉴 안 뜸, Graph Editor A/클릭 선택/Alt+MMB 팬/Alt+RMB 줌,
  Node Editor 클릭 선택/Alt+MMB 팬.
- 스크린샷 직접 확인: 5.2 레이아웃·핫박스·Maya 테마 (`tmp/shots_b52`, `tmp/theme_b52.png` vs `theme_b45.png`), 5.2 Range Slider 줄의 재생 버튼.

## 남은 것
- 5.x 의 Maya 테마는 4.5 용 maya.xml + 옮긴 값 — 5.x 에만 있는 테마 값 (예: `regions.asset_shelf`, 5.x 새 영역·편집기 색) 은 Blender
  기본. 5.x 용 테마 파일을 따로 만들지 않음 (결정 4).
- 5.x 에서 셸프 아이콘이 4.5 보다 어둡게 보임 (이미지 편집기 POST_PIXEL 텍스처 색 공간 차이로 보임, 측정 안 함).
- 5.x 에서 타임라인 사이드바 (Time Slider 버튼 칸) 가 접혀 버튼이 Range Slider 줄로 감 (기능은 같음, 위치만 Maya 와 다름).
  5.x 에서 템플릿을 다시 만들면 해결될 수 있으나 템플릿은 4.5 에서 만듦.
- 키맵 드리프트 (5.x): Node Editor Z (`node.viewer_border`) 없음 → kit 의 Z (Maya 언두) 가 Node Editor 에서 그대로 작동 (문제 없음).
- 5.3 이후: `blender_version_max = "5.3.0"` 때문에 설치 안 됨 — 새 버전이 나오면 이 단계의 실행 (`tmp/run53.sh` 같은 순서, step_53 표)
  을 다시 하고 올림.
- GUI 전체를 5.0 / 5.1 에서 돌리지 않음 (헤드리스만).
- 수동 확인: `docs/manual_checks.md` 「Step 53」.
