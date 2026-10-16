# Step 12 — M5 셸프

PLAN 표 #13 (사용자 번호 12).

## 계획

근거: `research/maya/shelves.md` (§1 동작 :8-23, §2 기본 탭 순서 :25-31, §3 셸프별 버튼 :33-78, §4 Blender 메모 :80-88),
`research/maya/shelves.json` (factory 셸프 버튼 label/command/doubleClickCommand), `research/maya/ui_layout.md` (메뉴바 → Status
Line → Shelf → 뷰포트 순서, 셸프는 창 전체 폭), `research/blender/api_limits.md` #11 (커스텀 영역 없음; 헤더를 가진 얇은 영역이
가장 맞음, Asset Shelf 는 에셋만).

### 1. 위치: Status Line + Shelf 띠 영역 (delegated)

- Maya 는 메뉴바 아래에 Status Line, 그 아래 Shelf(탭 + 아이콘, 64 px, `initShelf.mel:290-306`) 가 창 폭 전체에 놓인다. Step 7 은
  TOPBAR 한 줄에 둘을 넣을 수 없어 Status Line 을 메인 3D 뷰의 툴 헤더에 넣었다. 3D 뷰의 행은 헤더·툴 헤더 둘뿐이라 그 아래에
  행을 더할 수 없고, TOPBAR 에는 아래 줄이 없다 (`$S\startup\bl_ui\space_topbar.py` 에 TOPBAR_HT_upper_bar 만).
- 툴 헤더를 가진 에디터는 3D View·Image·Sequencer 뿐 (`$S\startup\bl_ui\space_image.py:692`). → **얇은 Image Editor 영역
  ("Maya 띠")**: 헤더 행 = Status Line, 툴 헤더 행 = Shelf. 실측(GUI, 1600×900): 3D 뷰를 HORIZONTAL factor 0.91 로 나누면 새 영역이
  **위쪽** 67 px, HEADER 32 + TOOL_HEADER 32 가 둘 다 보인다.
- 띠 표식: 그 Image Editor 의 `space.mask` = 숨은 Mask 데이터블록 `.MayaKitStrip` (파일에 저장, 이미지 표시 없음).
  `IMAGE_HT_header.draw` / `IMAGE_HT_tool_header.draw` 를 Step 7 TOPBAR 와 같은 방식으로 바꿔 끼우고, 표식 없는 Image Editor 는
  원래 그리기 그대로. unregister 에서 원복, `tests/kit.py` 스냅샷에 추가.
- 띠가 있는 화면에서는 메인 3D 뷰 툴 헤더의 Status Line 을 그리지 않는다 (하나만). 띠가 없는 레이아웃은 Step 7 그대로.
- App Template (`tools/make_startup.py`): 아웃라이너 분할 **전에** 3D 뷰를 위아래로 나눠 띠를 만든다 → 띠가 Outliner+뷰포트 폭 전체.
- 다른 레이아웃용: Maya Windows > UI Elements 에 **Shelf** 토글 (`maya_kit.shelf_strip_toggle`: 가장 큰 3D 뷰 위에 띠 생성 /
  띠 영역 닫기).

### 2. 셸프 데이터

- `tools/gen_shelf_data.py` → `ui/shelf_data.py` (생성 파일): Maya 기본 탭 순서(`initShelf.mel:458-485`)와 탭 이름
  (MayaStrings: "Poly Modeling" 등), 버튼마다 (label, runTimeCommand 이름 또는 None). MEL 명령 문자열은 넣지 않는다 (decision 6,
  Step 7 menu_data 와 같은 원칙): 인자 없는 식별자만 runTimeCommand 로 남김.
- `ui/shelf_map.py` (손으로 작성): runTimeCommand → (Blender 동작, Blender 내장 아이콘), 명령이 MEL 식인 버튼은 "탭/라벨" 키로.
  동작 값 형식은 `menu_map` 과 같음 (op / v3d / tool / menu) → 실행은 Step 9 `marking.modal.run_action` 재사용. Step 10 연산자
  (`maya_kit.create`, `center_pivot`, `delete_history`, `freeze_transform`) 연결. 대응 없는 버튼은 숨김 (Maya 아이콘을 대신할
  그림이 없고 회색 물음표 줄이 쓸모 없어서, delegated) — 테스트가 탭마다 대응 수를 센다.
- 아이콘: Blender 내장 아이콘 이름만 (Maya 아이콘 복사 금지, shelves.md:86-88). 테스트가 모든 이름이 Blender 아이콘 enum 에
  있는지 확인.

### 3. 동작

- 클릭 = 실행 (`-command`). **더블클릭 = 옵션** (`-doubleClickCommand` = `...Options` 관례, shelves.md:14-16): 버튼 연산자 invoke 에서
  `event.value == 'DOUBLE_CLICK'` 이면 다시 실행하지 않고 직전 실행의 Adjust Last Operation (`screen.redo_last`) — 첫 클릭이 이미
  실행했으므로 Maya 의 "만들고 옵션 열기"와 같은 흐름. Ctrl+클릭도 옵션 (더블클릭이 안 오는 환경 대비).
- 탭 전환: 띠 툴 헤더 왼쪽에 셸프 드롭다운(현재 셸프 이름) + ◀ ▶. 한 줄에 Status Line 과 탭을 모두 넣을 폭이 없어
  (1600 px 에서 Status Line ≈ 1000 px) Maya 처럼 탭을 늘어놓지 않는다 (delegated). 현재 셸프는 애드온 환경설정 `shelf_current`.
- 왼쪽 톱니 메뉴 (Maya 셸프 메뉴, shelves.md:23): New Shelf, Delete Shelf, Add Button…(이름·아이콘·Python 스크립트, 또는 Text 에디터의
  활성 텍스트), Add Last Command (Step 7 커맨드 라인 기록의 마지막 줄), Edit / Delete Button.
- 사용자 셸프: 버튼 = Python 스크립트 (`-sourceType python`). 저장 = 익스텐션 사용자 폴더의 `shelves.json`
  (`bpy.utils.extension_path_user`, 레거시 애드온이면 사용자 config 아래 `maya_kit`). 기본으로 Maya 의 빈 "Custom" 탭 하나.
  실행은 `exec` (bpy, C = context 를 넘김), 오류는 보고만 하고 계속.

### 4. 테스트

- 헤드리스 `test_step12_shelf.py`: shelf_data 탭 순서·버튼 수가 research JSON 과 같음, 모든 동작 대상 연산자·속성·도구·아이콘 존재,
  탭마다 대응 버튼 수 하한, Poly Modeling 큐브 버튼 → `pCube1`, 사용자 셸프 생성/버튼 추가/스크립트 실행/수정/삭제/JSON 저장·다시 읽기
  (샌드박스 경로), Add Last Command, 탭 전환 ◀ ▶, 그리기(FakeLayout), 템플릿에 표식 있는 띠 영역, Image 헤더 원복 (`test_enable_disable`).
- GUI `gui_step12_shelf.py`: 템플릿 로드 → 띠 위치(창 위쪽, 3D 뷰 위)·두 행 높이, 메인 3D 뷰 툴 헤더에 Status Line 이 없음, 스크린샷.

## 한 것

- `tools/gen_shelf_data.py` → `src/maya_kit/ui/shelf_data.py` (생성): Maya 기본 8탭(Curves / Surfaces … FX Caching), 버튼 203개의 label 과
  runTimeCommand 이름만 (MEL 식은 None).
- `src/maya_kit/ui/shelf_map.py`: runTimeCommand / "탭/라벨" → Blender 동작 + Blender 내장 아이콘. 대응 버튼 수: Curves/Surfaces 10,
  Poly Modeling 33/43, Sculpting 1, Rigging 13, Animation 13, Rendering 13, FX 5, FX Caching 4.
- `src/maya_kit/ui/shelf.py`: 버튼 연산자(클릭 = 실행, 더블클릭 = 그 실행의 Adjust Last Operation, Ctrl+클릭 = 옵션 실행), 탭 드롭다운 + ◀ ▶,
  톱니 메뉴(New/Delete Shelf, Add Button, Add Last Command, Edit/Delete Button), 사용자 셸프 `shelves.json`(익스텐션 사용자 폴더,
  기본 "Custom"), 버튼 = Python 스크립트(`exec`, 커맨드 라인과 같은 namespace: bpy/C/D/cmds), Rendering 재질 버튼용
  `maya_kit.shelf_material` (standardSurface/lambert/blinn/phong/surfaceShader → Principled BSDF, `lambert1` 명명).
- **Maya 띠**: 표식(Mask `.MayaKitStrip`) 있는 Image Editor 의 헤더 = Status Line, 툴 헤더 = Shelf (`IMAGE_HT_header/tool_header.draw` 교체·원복).
  띠가 있으면 메인 3D 뷰 툴 헤더의 Status Line 은 그리지 않음. `tools/make_startup.py` 가 띠를 Outliner 분할 전에 만들어 Outliner+뷰포트 폭 전체.
  Windows > UI Elements > **Shelf** = `maya_kit.shelf_strip_toggle` (다른 레이아웃에 띠 추가/제거).
- 환경설정 `shelf_current` (숨김). `tests/kit.py` 스냅샷에 Image 헤더 draw 추가. Step 5 레이아웃 테스트에 IMAGE_EDITOR 영역 반영.

## 검증

- 헤드리스 `python tests/run.py`: **185/185** (기존 175 + `test_step12_shelf.py` 10): 탭 순서·버튼 라벨이 research JSON 과 같음, 모든 동작의
  연산자·속성·도구·아이콘 존재, 매핑 키가 실제 버튼, 탭별 대응 수, Polygon Cube → `pCube1` 1×1×1, Freeze, Lambert → `lambert1` roughness 1,
  저장 경로가 샌드박스 안, 사용자 셸프 생성·버튼 추가(잘못된 아이콘 → SCRIPT)·스크립트 실행·오류 스크립트 CANCELLED·JSON 저장/다시 읽기·
  수정·삭제·Add Last Command·셸프 삭제, 탭 ◀ ▶ 순환, 그리기(아이콘만), Image 헤더 교체, 템플릿 띠 표식. `test_enable_disable` 통과(헤더 원복).
- GUI `python tests/gui/run.py`: **115/115** (기존 107 + `gui_step12_shelf.py` 8): 템플릿 띠가 3D 뷰 위·두 행 32/32 px·Outliner+뷰포트 폭,
  팩토리 레이아웃에 Shelf 토글로 추가/제거.
- 스크린샷 확인: `gui_step12_strip_poly.png` (메뉴바 → Status Line → Poly Modeling 셸프 → 3D 뷰, 메인 3D 뷰 툴 헤더엔 Status Line 없음),
  `gui_step12_strip_rigging.png` (탭 전환), `gui_step12_strip_factory.png` (팩토리 레이아웃에 추가한 띠).

## 결정 (delegated)

- 셸프 위치 = 얇은 Image Editor 띠 (위 「계획」 1). 띠는 오른쪽 열(Layer Editor/AE) 위로는 이어지지 않는다 (팩토리 오른쪽 열을 그대로 쓰는
  Step 5 결정). 창 크기를 바꾸면 Blender 가 영역을 비율로 늘려 띠 아래에 빈 줄이 조금 생길 수 있음 (manual check).
- 탭은 드롭다운 + ◀ ▶ (한 줄에 탭을 늘어놓을 폭 없음). 대응 없는 Maya 버튼은 그리지 않음. 더블클릭 = 첫 클릭 실행의 Adjust Last Operation.
- 사용자 셸프 버튼 삭제·편집은 톱니 메뉴 (Maya MMB 드래그·휴지통 없음). 메뉴 항목 Shift+Ctrl+클릭으로 셸프에 추가하는 기능 없음.

## 남은 것

- 버튼 드래그로 순서 바꾸기·셸프 사이 이동, 메뉴 항목을 셸프로 보내기, 버튼 그림(사용자 PNG) — Blender 헤더 버튼은 내장 아이콘/미리보기 아이콘만.
- Sculpting 탭: Blender 4.5 브러시가 에셋(`brush.asset_activate`)이라 Sculpt Tool(모드 전환)만 연결.
- 메뉴셋 F2–F6 키(PLAN #13 일부)는 Step 7 메뉴셋 드롭다운으로 대신, 키는 미구현 → Step 13 또는 이후.
