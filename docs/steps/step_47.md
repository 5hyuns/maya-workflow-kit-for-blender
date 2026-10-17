# Step 47 — 선택 와이어: 셰이딩 위 선택 오브젝트 와이어 (리드 연두 / 나머지 흰색)

backlog 7 (`docs/PLAN.md` 「Maya 동일화 계획」, 테마 (step 43) 다음). 근거: `research/maya/screens/02_cube_selected_move.png`
(셰이딩 위 pCube1 의 모든 엣지가 연두 #43ffa3, 외곽선 강조 없음), `04_wire_selected_lead.png` (리드 연두, 다른 선택 흰색),
`research/maya/colors.json` viewport displayColor lead 19 / active 16, step_40.md blindspot 6.

## 실측 (step 47)

- 프로브 (GUI 1600×900, 99 856 폴리 격자 하나 선택, Maya 테마, `wm.redraw_timer` DRAW 60 회 평균):

  | 상태 | ms / 그리기 |
  |---|---|
  | 선택 없음, 와이어 없음 | 1.244 |
  | 선택 (Blender 외곽선만) | 1.295 |
  | **B** `Object.show_wire` (Blender 오버레이 와이어) | 1.338 (+3.3 %) |
  | **A** Python POST_VIEW `LINES` 배치 (평가된 메시 엣지) | 1.327 (+2.5 %), 배치 만들기 **489 ms** (메시가 바뀔 때마다) |

- A 는 깊이 바이어스가 없어 면과 z-fighting (스크린샷이 점박이), 모디파이어·편집마다 배치를 다시 만들어야 하고 (0.5 s), 변형 행렬도
  따로 따라가야 한다. B 는 Blender 가 평가된 메시 그대로 깊이 오프셋을 넣어 그리고, 선택 오브젝트의 와이어 색이 테마
  `object_active` / `object_selected` = step 43 의 Maya 리드 연두 / 흰색이다.
- B 의 문제: `show_wire` 는 ID 데이터 (파일 저장·언두 스냅샷에 들어감) 이고, 스무스 프리뷰 2 (`operators/display.py` `_WIRE_FLAG`) 도 같은
  플래그를 쓴다.

- **B 를 처음 구현해 보니 색이 안 맞음**: 셰이딩 위 리드 와이어 최댓값 #37cf95 = 0.81·#43ffa3 + 0.19·#000460 — Blender 는 선택 오브젝트의
  와이어를 엣지가 뷰를 향한 정도에 따라 테마 `wire` (비선택 와이어 어두운 파랑) 쪽으로 최대 약 19 % 섞는다 (팩토리 큐브의 실루엣 엣지만
  순수 색). 테마로는 못 고친다 (`wire` 를 연두로 하면 와이어프레임 모드의 비선택 와이어가 연두). → **A 로 바꿈.**
- A 다시 재기: numpy `foreach_get` 으로 배치 만들기 **28 ms** (10 만 폴리; 목록 변환이 489 ms 의 원인), 깊이 바이어스 (클립 공간
  z −= b·w): 0 이면 cm 템플릿 1 cm 큐브에서 선이 끊김, 5e-5 / 2e-4 는 이어짐 → 1e-4. 사용자 셰이더는 색을 변환하지 않아 테마 sRGB 를
  그대로 쓰면 #43ffa3 이 #8bffd0 (한 번 더 감마) — `Color.from_srgb_to_scene_linear()` 로 넘김 (`blender_srgb_to_framebuffer_space` 는
  Python 셰이더에서 컴파일 안 됨).

## 계획 (delegated, A 로 확정)

1. `src/maya_kit/ui/selection_wire.py`: POST_VIEW 핸들러 하나. 선택된 오브젝트 모드 오브젝트 (MESH, CURVE, SURFACE, FONT, META, 보이는 것) 의
   평가된 메시 엣지를 오브젝트별 캐시 배치 (session_uid) 로, 오브젝트 행렬 × 뷰 투영, 깊이 바이어스 1e-4, 리드 = 테마 `object_active`,
   다른 선택 = `object_selected` (선형으로 변환). 편집 모드 오브젝트는 Blender 편집 메시 그리기에 맡김. RENDERED 셰이딩·오버레이 끔이면 안 그림.
2. 캐시: `depsgraph_update_post` 에서 `is_updated_geometry` 인 오브젝트의 배치만 버림 (편집·모디파이어·셰이프 키); 이동·회전은 행렬이라
   다시 안 만듦. load / undo / redo 에서 모두 비움.
3. **ID 데이터에 아무것도 쓰지 않음** → 저장 파일·언두 스냅샷에 남는 것 없음, 스무스 프리뷰 2 (`_WIRE_FLAG`) 와 충돌 없음 (그 위에 그대로 그림).
   스무스 프리뷰 3 (GPU 서브디비전) 은 CPU 평가 메시가 케이지라 케이지 엣지를 그림 (Maya 기본 "Display Subdivisions" 끔 = 케이지 엣지와 같은 뜻, delegated).
4. 환경설정 「Selection Wireframe」 `maya_selection_wire` (기본 켬 = Maya 기본, Blender 설정 아님). 템플릿 뷰 `show_outline_selected` 끔
   (Maya 는 외곽선 없이 와이어로 강조; Show > Selection Highlighting 로 다시 켬).
5. 검증: 헤드리스 (선택·모드·편집 모드, 모디파이어 포함 엣지, 지오메트리 변경 시 캐시 버림, **저장 파일 show_wire / maya_kit_ 속성 0**, 옵션·해제),
   look_compare viewport 표 (02 셰이딩 위 리드, kit 전용 02b 다른 선택 흰색, 04 와이어프레임), GUI 10 만 폴리 프레임 시간 < 20 %.

## 한 것

- `src/maya_kit/ui/selection_wire.py` (새): 위 계획 그대로 (사용자 셰이더 + 깊이 바이어스, numpy 배치 캐시, 지오메트리 변경 시 버림, 선형 색).
  그리기 콜백 안에서는 `context.view_layer.depsgraph` 를 쓴다 (`evaluated_depsgraph_get()` 은 그리는 중 다시 평가함).
- 환경설정 `maya_selection_wire` (UI Elements 상자), `ui/__init__.py` 등록, 템플릿 `show_outline_selected` 끔 → startup.blend 재생성.
- look_shots kit 전용 샷 `02b_two_selected_shaded`, look_data VIEW_SAMPLES 2 행 (셰이딩 위 리드 / 다른 선택; "best" + kit 샷 이름).
- 테스트: `tests/test_step47_selection_wire.py` (5), `tests/gui/gui_step47_selection_wire.py` (4).
- `tests/gui/gui_step11_outliner_ae.py`: Ctrl+A 사이드바 확인을 한 틱 뒤로 — 사이드바는 타이머로 열리는데 같은 틱에 확인해서 HEAD
  (step 46) 에서도 실패하게 됨 (이번 단계 코드와 무관함을 worktree 로 확인; 이 PC 의 이벤트 처리 순서가 달라진 것).
- 처음 만든 B (show_wire + ID 표시, display.py 넘겨받기) 는 색 때문에 버리고 되돌림.

## 검증

- 헤드리스 `python tests/run.py`: **374/374** (새 5: 선택·편집 모드, 모디파이어 포함 평가 엣지 (subsurf 1 → 12 엣지), 지오메트리 변경 시 그 오브젝트
  배치만 버림, **저장한 .blend 의 show_wire / maya_kit_ 속성 0** (메모리에도), 옵션·해제 시 핸들러 정리).
- GUI `python tests/gui/run.py`: **293/293**, `--ui-scale 0.8`: **293/293** (step 11 고친 뒤 7/7 두 배율, step 47 은 마지막 코드로 다시 4/4 두 배율).
  10 만 폴리 (100 489) 선택 프레임 시간: 1.694 → 1.821 (+7.5 %), 1.742 → 1.993 (+14.4 %), 1.669 → 1.792 (+7.3 %), 1.759 → 1.809 (+2.9 %),
  1.683 → 1.896 (+12.7 %) ms — 모두 < 20 %.
- `python tools/look_compare.py` → `viewport.md` **10/12** (step 46: 8/10): 셰이딩 위 리드 와이어 #45ffa2 vs Maya #43ffa3 **0.2**, 다른 선택
  #ffffff **0.0** (kit 02b vs Maya 04 의 흰 픽셀), 와이어프레임 04 리드 0.2 / 흰색 0.0. 남은 ✗ 2 = 비선택 와이어 5.8, 매니퓰레이터 Z 5.1 (step 44 「남은 것」).
  grid ok·4/4, density 3/3, furniture 3/3.
- `python tools/dogfood.py`: **47/47**, 콘솔 오류 0.
- 스크린샷 직접 확인: kit 02 (리드 큐브 모든 엣지 연두, 외곽선 없음), 02b (리드 연두 + 오른쪽 큐브 흰색).

## 남은 것

- 큰 메시를 처음 고를 때 배치 만들기 (10 만 폴리 약 30 ms, 첫 그리기는 셰이더 컴파일 포함 약 70 ms) — 수백만 폴리면 눈에 띌 수 있음.
- 스무스 프리뷰 3 은 케이지 엣지 (매끈한 면에서 뜸); 커브·텍스트는 `to_mesh` 엣지.
- 선 굵기 1 px 고정 (Maya 도 1 px). 비선택 와이어 (와이어프레임 모드) 는 여전히 Blender 것 (ΔE 5.8).
