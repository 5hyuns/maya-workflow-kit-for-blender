# Step 142 — 레인 ICONS: 남은 Maya 메뉴 아이콘 (#54)

요청 (#54): step 131 뒤 Maya 메뉴 항목 190 개에만 키트 아이콘이 있었다. Maya 2022 는 키트 메뉴에 있는 항목 679 개에
아이콘을 그린다 — 나머지 489 개 (Deform, Mesh Display, Effects / Fields, 셸프 버튼이 없는 Edit Mesh / Mesh Tools 도구
…) 를 키트 그림으로 채운다. Outliner 오브젝트 아이콘 오버레이는 싸고 믿을 만할 때만, Status Line 핸들 / 셸프 28 px 는
기록만.

## 계획

- 그림은 셸프와 같은 어휘 (`shelf_icons.Canvas`, 한 종류에 한 색, 어두운 외곽선, 왼쪽 위 빛, 도구 부품은 밝은 회색,
  동작 표시는 구석에 작게) 로 새로 그린다. Maya 아이콘은 `tmp/maya_icons131/` 에서 보기만 한다 (결정 6: 픽셀·좌표
  복사 없음). 비교 시트 (Maya 32 px 옆에 키트 32 / 16 px) 는 `tmp/icons142/` 에만.
- 새 모듈 `ui/menu_drawings.py` (레지스트리 + 공용 부품 + Deform) 와 메뉴 묶음별 `menu_drawings_{mesh,fx,select,build,misc}.py`.
  `@icon(path, ...)` 가 첫 경로 이름으로 그림을 등록, 나머지 경로는 Maya 가 같은 그림을 쓰는 항목.
- `tools/gen_menu_icons.py` 규칙 4: 데코레이터를 ast 로 읽어 `("menu", name)` 그림을 `menu_icon_data.ICONS` 에 쓴다;
  Maya 아이콘 파일이 그린 항목과 같은 항목도 같은 그림. 검사: 그린 경로가 Maya 아이콘 항목이 아니거나 이미 셸프 /
  글리프 그림이 있으면 실패.
- `menu_icons.picture` 가 `"menu"` 종류를 그린다 (미리보기 타이머·크기 규칙은 step 131 그대로).

## 한 일

- 그림 450 개 (`src/allset/ui/menu_drawings*.py`), 메뉴 항목 485 개에 연결 (484 = 데코레이터 경로, 1 = 같은 Maya
  그림 규칙: `Fields/Solvers/Volume Curve` → Volume Axis 그림).
- 메뉴: Deform, Mesh, Edit Mesh, Mesh Tools, Mesh Display, Effects, Fields / Solvers, Fluids, nParticles, nConstraint,
  nHair, nCache, Cache, Select, Modify, Create, Curves, Surfaces, Skeleton, Skin, UV, Windows, Playback, Constrain, Key,
  Visualize, Edit (LOD), Texturing, Toon, Generate, Stereo, Render.
- `tests/test_step142_icons.py` (먼저 작성): 우선 메뉴 147 항목 전부 아이콘, 그림 ↔ 표 일치, 개수 (≥ 675, step 131
  링크 190 그대로), 16 / 20 / 24 / 32 / 64 px, 2x = 1x 그림, 한 메뉴 안의 서로 다른 그림은 step 131 셸프 규칙
  (32 px 픽셀 4 % 이상이 0.25 넘게 다름) 으로 구별, 그림 450 개 서로 전부 구별.
- `tests/test_step131_menu_icons.py`: `"menu"` 종류 허용, 같은 그림 (생성기가 Maya 의 같은 아이콘 파일로 묶은 것) 은
  한 메뉴에 여러 번 허용 (Fields/Solvers 의 rigid body 제약 5 개, Select > Convert Selection 의 둘레 5 개, Stereo 4 개 등
  — Maya 도 같은 그림).
- `tools/icon_sheet.py`: 모듈별 시트 `docs/icons/menu_drawings_<group>.png` (32 / 24 / 16 px), `docs/icons/README.md` 표.
- `tests/gui/gui_step142_icons.py`: Deform, Deform > Nonlinear, Mesh Tools, Mesh Display, Effects, Fields/Solvers 메뉴를
  `wm.call_menu` 로 열어 스크린샷, 미리보기가 메뉴 아이콘 크기로 먼저 만들어졌는지 확인.

## 숫자

| | step 131 | step 142 |
|---|---|---|
| 아이콘 있는 키트 메뉴 항목 | 190 | **675** |
| Maya 가 아이콘을 그리는 키트 메뉴 항목 | 679 | 679 |
| 그 중 키트 그림 없음 | 489 | **4** |
| 메뉴 전용 그림 | 0 | 450 (485 항목) |

남은 4 개: `Create/Universal Scene Description (USD)`, `Generate/Convert to Interactive Groom...`,
`Generate/Import Collections or Descriptions...`, `Generate/XGen Library` — Maya 캡처에 그림 파일이 없다 (플러그인
아이콘, step 131 내보내기에서 빠짐). 따라 그릴 Maya 그림이 없어 비워 둠.

## 검증

- `python tests/run.py -k step131,step142_icons,step108,enable_disable`: 47 통과 (첫 실행에서 `test_drawings_distinct_overall`
  마지막 반복 빈 배열 버그 1 건 → 고침).
- 헤드리스 전체: 아래 「결과」.
- GUI: `python tests/gui/run.py -k step142_icons,step131_menu_icons` — 26 통과 (step 131 13, step 142 13; 첫 실행의
  `Fields/Solvers` 메뉴 id 오류는 고침). 스크린샷 `tmp/icons142/shots/` (UI 1.25): Deform / Nonlinear / Mesh Tools /
  Mesh Display 에서 아이콘이 기존 아이콘 열에 들어가고 라벨·단축키·❒ 정렬 그대로, 회색 항목은 Blender 가 아이콘도
  흐리게.
- 시트를 직접 봤다: `docs/icons/menu_drawings_*.png`, Maya 비교 `tmp/icons142/kit_*.png`.

## 결정 (delegated)

1. **그림은 메뉴 전용 모듈에.** `shelf_icons.py` 는 셸프 버튼 사전 (`ICONS`) 과 섞이지 않게 그대로 두고 부품만 import.
   같은 명령의 셸프 그림이 있으면 step 131 규칙 1–2 가 먼저 쓰고, 데코레이터가 같은 경로를 또 그리면 생성기가 실패.
2. **Maya 가 한 그림을 쓰는 항목은 한 그림.** 생성기가 Maya 아이콘 파일 이름이 같은 항목을 묶고, Curves > Bend 등과
   nHair > Modify Curves > Bend 등, Mesh Tools / Smooth Proxy Crease Tool, Deform / Modify Soft Modification Tool,
   Edit Mesh / Mesh Tools Connect (같은 명령) 는 데코레이터에 함께.
3. **글자는 Maya 그림이 글자일 때만** (field 공 F / G / N / D, hair 상태 C / S / R, PSD, AI, Reorder Vertices 0–3,
   Measure L / T / U, Modulate 2x). 16 px 에서는 읽히지 않지만 공·색이 구별을 맡는다.
4. **Outliner 오브젝트 종류 아이콘 오버레이: 하지 않음.** Blender C Outliner 의 행 → 오브젝트 대응을 Python 이 알 수
   없다 (TreeStore 펼침 상태, 검색 / 종류 필터, 정렬, 스크롤). step 131 의 후속 아이디어 (행 아이콘의 픽셀 들여쓰기 +
   계층 DFS 순서로 복원, 어긋나면 중단) 는 매 그리기마다 프레임버퍼를 행마다 읽어야 하고, Blender 아이콘을 덮을 배경
   색도 선택 / 호버 / 활성 행마다 달라 싸지도 확실하지도 않다. 틀린 아이콘이 Blender 아이콘보다 나쁘다 (step 131 결정 4
   그대로).
5. **Status Line 그룹 핸들 / 셸프 행 125 % 28 px: 그대로.** 핸들은 레이아웃 (아이콘 아님), 셸프 행 높이는 step 113 / 131
   의 헤더 높이 한계 — 이 레인 범위 밖, 기록만.

## 남은 것

- 위 4 항목 (Maya 그림 없음).
- 편집기 메뉴 막대 (Graph Editor, Hypershade …) 의 아이콘: Maya 메뉴 아이콘 캡처가 아직 없음 (step 131 과 같음).
- 마킹 메뉴 / 핫박스 목록: 아이콘 없음 (GPU 엔진, step 131 과 같음).
