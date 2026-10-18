# Step 98 — 재점검 7차 (정밀 비판: "이건 Maya여야 한다")

사용자 요청 (2026-10-19 00시) 요지: 「다시 한 번 세밀하게 점검. 사용성부터 UI·UX·기능, 딱 봤을 때 Maya 같아야 한다. 파일 임포트/익스포트,
애니메이션, 리깅, 모델링, UV, FX 등등. 이건 진짜 '기본 Maya에 Blender 기능이 붙은 모습'이어야 한다. 비판적으로 보고 비교해라.」
점검·목록화 단계 (작은 수정 가능).

## 계획 (delegated)

1. **같은 장면을 양쪽에서 실제로 띄워 찍는다.** Maya 2022 GUI (factory prefs, `MAYA_APP_DIR` = `tmp/maya_app_a7`) 를
   `research/scripts/maya_audit7/audit7.py` 로, kit 은 깨끗한 설정 설치 + GUI 세션 `tmp/audit7_session.py` (저장소 밖,
   `python tools/dogfood.py --session ...`) 로. 둘 다 창 1600x900. 장면: 첫 화면, 5 메뉴 세트의 모든 최상위 메뉴, 셸프 탭 전부,
   File 대화상자 · 옵션 박스 · Project Window, 모델링 (Extrude + Tool Settings + AE), UV Editor, 애니메이션 (키 + Graph Editor /
   Dope Sheet / Time Editor), 리깅 (조인트 + Bind Skin), FX (nCloth), 렌더 (Hypershade / Node Editor / Render Settings / Render View /
   Script Editor / Preferences). Maya 는 창 위젯을 Qt `grab()` (+ 뷰포트 컬러 버퍼) 으로, 떠 있는 창은 따로, 모달 대화상자는 타이머로 잡고 닫는다.
2. **수치 대조는 읽기 전용 서브에이전트 1개** (menus.json · shelves.json · keymap_mapping 대 menu_data · menu_map · notices · shelf_*):
   메뉴 세트별 작동 / 회색 / 안내 유무, 옵션 박스 종류, File 메뉴, 셸프, 키맵 미검토 우선순위, Windows 편집기. 주장은 grep 으로 표본 재확인.
3. 실제 Maya 메뉴 (Qt 에서 읽은 항목 이름) 와 kit 메뉴 데이터 비교 — menus.json 정적 파싱이 놓친 항목 찾기.
4. 항목마다 등급 (외형 / 조작 / 기능 / 없음) × 체감 빈도 1–5 × 심각도 1–5 → 점수 = 빈도 × 심각도. `docs/PLAN.md` 「재점검 7차(정밀 비판)」,
   backlog 8–12 개.
5. 찾은 kit 버그 중 작은 것은 고친다.

**배율 주의 (측정으로 정함)**: 이 PC 는 Windows 125 %. Maya `grab()` 은 논리 픽셀 (1600x900 논리 = 실제 2000x1125) 이고 kit GUI 세션은
기본 effective scale 1.25 (실제 1600x900) 라 같은 1600x900 그림에서 kit 글자가 1.25 배 크다. 공정한 나란히 비교는 kit 을
`MAYA_KIT_GUI_UI_SCALE=0.8` (effective 1.0) 로 찍었다 (`research/maya/screens/audit7/kit/`). 또 dogfood 는 `MAYA_KIT_NO_WELCOME=1`
이라 환영 대화상자의 Make Blender Maya 가 안 돌아 Maya 테마가 없다 (선택 = Blender 주황) — 최종 세션은 먼저 `maya_kit.make_maya`
를 불러 새 사용자가 받는 상태로 찍었다 (로그 `theme Maya ui_scale 1.0`).

## 한 것

- Maya 촬영 스크립트 `research/scripts/maya_audit7/` (launch.ps1 · userSetup.py · audit7.py; research/ 는 추적 안 함). 결과
  `research/maya/screens/audit7/maya/` 146 장 + `_audit7.json` (메뉴별 실제 항목 이름, 셸프 버튼 수, 창 제목/크기, 로드된 파일 변환기).
- kit 세션 3 회: effective 1.25 테마 없음 (첫 실행, 버그 발견) → 1.0 테마 없음 → **1.0 + Make Blender Maya (최종)**. 최종 125 장
  `research/maya/screens/audit7/kit/`, 125 % 첫 화면 `kit_scale125/a01_first_screen.png`.
- 나란히 비교 113 쌍 `research/maya/screens/audit7/pairs/` (왼쪽 Maya, 오른쪽 kit; `tmp/audit7_pairs.py`, blender -b numpy).
- 수치 부록 `docs/steps/step_98_quant.md` (서브에이전트; 표본 재확인: Modify > Naming 은 menu_data 에 없음 — `grep -c Naming
  src/maya_kit/ui/menu_data.py` = 0, `project.py:420` 문구, keymap_mapping.md:393 Alt+R = `object.scale_clear`).
- 실제 Maya 메뉴 대 kit: 최상위 항목 746 개 중 kit 에 없는 것 — File 의 Game Exporter / Send To Unity / Send To Unreal, Modify 의
  Naming (Prefix Hierarchy Names / Search and Replace Names), **Audio 7 개 · Stereo 4 개 (kit 은 빈 메뉴)**, Visualize 의 Ghosting 4 +
  Time Slider Bookmarks, Create 의 Sweep Mesh / USD, Select 의 USD Selection Mode, Playback 의 Cached Playback, Generate 의 XGen 17,
  nCloth / nConstraint 의 Convert Texture↔Vertex Map, Help 3 (`tmp/audit7/live_vs_kit.txt`; 섹션 중첩 때문에 자동 비교가 틀리게 센 항목
  — Modify Center/Bake Pivot, Add/Edit/Delete Attribute — 은 화면으로 확인해 뺐다).
- **고친 kit 버그 3**:
  1. Channel Box depsgraph 핸들러가 File Browser / Preferences 창 컨텍스트에서 `AttributeError: 'Context' object has no attribute
     'active_object'` (첫 세션 콘솔 4 traceback, `channel_box.pose_armature`). `channel_box.active_object()` (없으면 view layer 의 active)
     로 바꿈. 헤드리스 회귀 `tests/test_step98_audit_fixes.py`. 수정 후 세션 콘솔 traceback 0.
  2. Create Reference 에 .blend 아닌 파일을 주면 「use File > Import for .ma」 라고 안내 — kit 은 .ma 를 못 읽음. 문구를
     「.fbx / .obj / .abc / .usd (Maya .ma / .mb can't be read)」 로 (`operators/project.py:420`).
  3. (이어서) Render Settings 등 Properties 창을 열 때 rna enum WARN 2 줄 — `operators/menu_extras.properties_tab_later` 가 탭 목록이
     생기기 전에 `space.context` 를 읽음. 대입이 성공했을 때만 읽도록 고침 (probe 세션 콘솔 0 줄).

## 발견 (차이만, 등급 · 빈도 F · 심각도 S · 점수 = F×S)

근거 그림은 `research/maya/screens/audit7/pairs/<이름>.png`.

### 첫 화면 (`a01_first_screen`, 125 % 는 `kit_scale125/a01_first_screen`)

| # | 차이 | 등급 | F | S | 점 |
|---|---|---|---|---|---|
| 1 | **Outliner 가 빈 회색 줄무늬 열.** Maya 는 새 장면에도 persp / top / front / side (회색 = 숨은 카메라), defaultLightSet, defaultObjectSet 을 보여 준다. kit 은 오브젝트가 생겨야 행이 생기고, Maya 에 없는 교대 줄무늬 배경. (step 41 look_compare: 요소 rects 5/12, 픽셀 5/31, kit 에 없는 요소 7) | 외형 | 5 | 4 | 20 |
| 2 | **Windows 125 % (이 PC 의 실제 배율) 에서 Tool Box 열이 비고, 툴이 뷰포트 안 Blender 툴바로 뜬다.** 열 너비 56 px < 툴바 한 칸 (effective 1.25), `toolbox.fit_columns` 의 `screen.area_move` 가 마우스가 어느 영역 위에 있어도 poll False 라 넓히지 못하고 메인 뷰 툴바 fallback 만 켜짐 (probe: TOOLS region 1x1, 메인 뷰 TOOLS 70 px). audit 6 의 `a6_01` 도 같은 상태였는데 못 봤다 | 외형/조작 | 5 | 4 | 20 |
| 3 | 도크: CB / AE / MTK 가 사이드바 위 가로 버튼 (「Channel Box /...」 잘림) + 오른쪽 끝 Blender 세로 탭 「Channel Box」「Item」. Maya 는 오른쪽 끝 세로 탭 「Channel Box / Layer Editor · Attribute Editor · Modeling Toolkit」 만. CB 와 Layer Editor 높이 비율도 다름 | 외형 | 5 | 3 | 15 |
| 4 | 뷰 패널: Maya 아이콘 바 (패널 툴바) 없음. 대신 Blender 헤더 (Object Mode, Global, 스냅, 오버레이, 셰이딩 공) 와 kit 메뉴 「Blender」 | 외형 | 5 | 3 | 15 |
| 5 | 메뉴 세트 드롭다운이 메인 메뉴 바 안 (Maya: Status Line 왼쪽 끝). 오른쪽 위 Blender 작업공간 선택기 + Maya/Blender 버튼 (Maya: 「Workspace: General*」) | 외형 | 5 | 2 | 10 |
| 6 | 기본 재질 없음: Maya 는 모든 새 메시에 lambert1 (initialShadingGroup). kit 은 재질 없음 → Hypershade 「No materials in the scene」, AE 에 재질 탭 없음 | 기능 | 4 | 4 | 16 |
| 7 | 셸프: 탭 9 (Maya 13 — 플러그인 탭 포함), 아이콘이 납작한 주황 그림 (Maya 회백 아이콘), 버튼 203 중 98 만 그림 (105 는 흔적 없이 빠져 순서에 빈틈) | 외형/기능 | 4 | 3 | 12 |
| 8 | Command Line 이 「Python」 버튼 + 입력 (Maya 「MEL」 + 입력 + 결과 칸) | 외형 | 2 | 1 | 2 |

### 메뉴 (`menu_*`, 부록 §1)

| # | 차이 | 등급 | F | S | 점 |
|---|---|---|---|---|---|
| 9 | **kit 메뉴 1251 항목 중 881 (70 %) 회색, 그중 866 은 이유 표시 없음.** 세트별 작동률 Common 44 · Animation 32 · Modeling 22 · Rigging 21 · Rendering 21 · FX 14 %. Surfaces / Generate / Toon / Cache / Help / nConstraint 는 0 % | 기능 | 5 | 4 | 20 |
| 10 | **매핑된 항목도 회색**: 오브젝트 모드에서 Edit Mesh 의 Collapse · Merge to Center · Flip · Delete Edge/Vertex · Spin Edge 등이 Blender 연산자 poll 실패로 흐리게 (`pairs/menu_Modeling_Edit_Mesh`). Maya 는 모두 활성 (선택이 없으면 실행 후 경고) | 외형 | 5 | 3 | 15 |
| 11 | **옵션 박스**: Maya 625 / kit 표시 500, 진짜 옵션 창은 6. 323 은 회색 항목의 죽은 아이콘. 모양도 Maya 오른쪽 ❑ 대신 왼쪽 「창」 아이콘, 툴팁 「Press and hold: Option Box」 | 외형/기능 | 5 | 4 | 20 |
| 12 | 메뉴에 Maya 단축키 표시 없음 (Ctrl+N/O/S, Ctrl+B Bevel, Ctrl+E Extrude, Ctrl+Del …), 대신 Blender 키가 보임 (Recent Files 「Shift Ctrl O」). Maya 항목 아이콘 없음 | 외형 | 4 | 2 | 8 |
| 13 | 실제 Maya 에 있는데 kit 메뉴에 없는 최상위 항목 (위 「한 것」): Audio · Stereo 는 빈 메뉴, Modify > Naming, File > Game Exporter / Send To … | 없음 | 3 | 3 | 9 |
| 14 | 125 % 에서 File 메뉴가 화면보다 길어 Exit 가 스크롤 화살표 뒤로 (Maya 는 한 화면) | 외형 | 2 | 2 | 4 |

### 파일 (`b01`–`b07`, 부록 §2)

| # | 차이 | 등급 | F | S | 점 |
|---|---|---|---|---|---|
| 15 | **Open / Save As 가 Blender 파일 브라우저 (별도 창 1325x750)**: Maya 의 Look in 경로, Folder Bookmarks, Current Project 드롭다운 + 프로젝트 폴더 목록, Options 패널, Files of type, Set Project 버튼이 없다. 프로젝트가 없으면 Documents 에서 시작 (Maya: 항상 default 프로젝트의 scenes) | 외형/조작 | 5 | 4 | 20 |
| 16 | **Import / Export All / Export Selection 이 형식 하위 메뉴** (FBX / OBJ / glTF / USD / Alembic). Maya 는 파일 대화상자 + Files of type + 옵션; 옵션 박스 아이콘은 있으나 상자가 없다. 내보내기에 Maya 축 / 단위 프리셋 (Y-up, cm) 없음 | 조작/기능 | 4 | 4 | 16 |
| 17 | Cache 메뉴 0/13 — Blender 는 Alembic / USD 읽기·쓰기가 되는데 Maya 의 캐시 경로가 막힘 | 기능 | 3 | 3 | 9 |
| 18 | .ma / .mb 읽기 불가 (Maya 사용자가 가장 먼저 시도). 변환 경로 안내 없음 | 기능 | 3 | 4 | 12 |
| 19 | Project Window 에 「Blender has no project system …」 설명, 현재 프로젝트 「new_project」 (Maya 「default」), 폴더 행 편집 불가. Save Scene As / Open 옵션 창 없음, Archive Scene · View Image/Sequence · Recent Increments · ATOM 회색 (안내 없음) | 외형 | 2 | 2 | 4 |

### 모델링 / UV (`c01`–`c03`, `d01`)

| # | 차이 | 등급 | F | S | 점 |
|---|---|---|---|---|---|
| 20 | **Tool Settings 가 뷰포트 위 팝오버** (Orientation · Drag Tweak · Retain Component Spacing — Blender 필드). Maya 는 왼쪽 도크 창: Move Settings (Axis Orientation, Edit Pivot, Pin, Transform Constraint, Step Snap, Preserve Children/UVs, Tweak Mode) + Joint Orient / Move Snap / Common Selection / Soft Selection / Symmetry / Smart Duplicate 섹션. 메뉴로 두 번 토글해도 팝오버가 다음 장면까지 남음 (`c03` 에 겹침) | 외형/조작 | 4 | 3 | 12 |
| 21 | **AE**: 탭이 transform + shape 둘뿐 (Maya: + polyExtrudeFace1 · polyCube1 · initialShadingGroup 이력/재질 탭), shape 섹션 6/12, 메뉴 바 (List / Selected / Focus / Attributes / Display / Show / Help) · Focus / Presets / Show / Hide · Notes · 아래 Select / Load Attributes / Copy Tab 없음 | 외형/기능 | 4 | 3 | 12 |
| 22 | Channel Box INPUTS 아래 「Blender keeps no edit-mode history …」 설명문 (Maya 에 없는 문장). Hypershade · Project Window 도 같은 종류의 설명문 | 외형 | 3 | 2 | 6 |
| 23 | 노멀 (Soften/Harden, Set/Lock Normals), Edit Mesh Detach / Flip / Circularize / Edit Edge Flow / Wedge, Mesh Tools Connect / Make Hole / Append, Sculpting 툴 21 개 회색 (Blender 에 비슷한 기능 있음) | 기능 | 4 | 4 | 16 |
| 24 | **UV Editor 가 Blender Image Editor 헤더** (View / Select / Image / UV, New / Open, UVMap). Maya: 메뉴 바 Edit / Create / Select / Cut/Sew / Modify / Tools / View / Image / Textures / UV Sets / Help + 아이콘 줄 + 오른쪽 UV Toolkit 패널 | 외형 | 4 | 4 | 16 |
| 25 | UV 키: Ctrl+1 = 정점 모드 (Maya: UV isolate), Delete 없음, 4–9 표시 키 없음/다름. Split UVs · Best Plane · Contour Stretch · Checker 회색 | 조작/기능 | 3 | 3 | 9 |

### 애니메이션 (`e01`–`e04`)

| # | 차이 | 등급 | F | S | 점 |
|---|---|---|---|---|---|
| 26 | **Graph Editor / Dope Sheet 가 Blender 헤더·메뉴** (View / Select / Marker / Channel / Key, Normalize, Playhead). Maya: Edit / View / Select / Curves / Keys / Tangents / List / Show / Help + 아이콘 줄. 채널 목록에 Blender 개념 「pCube1Action」 행, 채널 이름이 Translate X (빨강) / Translate Y (초록) 가 아님, 사이드바 F-Curve 패널 (RNA Array Index), 재생 범위 밖 갈색 음영과 0 프레임 (Maya 없음) | 외형 | 4 | 4 | 16 |
| 27 | Time Editor = NLA, Audio 메뉴 빈 것, Ghosting / Time Slider Bookmarks 없음 | 없음 | 2 | 3 | 6 |

### 리깅 / FX (`f01`, `g01`)

| # | 차이 | 등급 | F | S | 점 |
|---|---|---|---|---|---|
| 28 | Skeleton 13 % · Skin 43 % · Deform 15 % 작동 (Insert Joints, Reroot, Preferred Angle, IK Spline, Joint Labelling 39, Add/Remove Influence, Hammer, Cluster, Wire, Nonlinear, Soft Mod, Paint Weights 11 회색) | 기능 | 3 | 4 | 12 |
| 29 | FX: Outliner 에 nucleus1 / nCloth1 노드 행이 없다 (AE 탭에는 있음). nHair 2 % · Fluids 8 % · nConstraint 0 % | 외형/기능 | 2 | 3 | 6 |
| 30 | ~~(미확인) 메뉴로 띄운 Joint Tool 에 조인트 0~~ → **차이 아님** (이어서 한 확인, `tmp/audit7_probe2.py`): Skeleton > Create Joints 로 띄운 Joint Tool 에 틱마다 클릭 3 번 + Enter = skeleton1 본 3 개 (kit 규칙: N 클릭 = N 본, 끝 조인트는 짧은 tail). 첫 세션은 한 틱에 두 번 클릭해 모달이 놓친 것 | – | – | – | – |

### 렌더 / 기타 창 (`h01`–`h06`)

| # | 차이 | 등급 | F | S | 점 |
|---|---|---|---|---|---|
| 31 | **Hypershade = Shader Editor + 사이드바 탭**: Maya 의 Browser 견본 탭 (Materials / Textures / Utilities / Rendering / Lights / Cameras / Shading Groups …), Material Viewer, Create 목록 (Maya ≈ 25, kit 6), Property Editor (빈 「Pick a material」), Maya 메뉴 바 없음, Blender 헤더 (Slot / New) | 외형 | 4 | 4 | 16 |
| 32 | **Render Settings = Blender Properties** (Render Engine EEVEE, Sampling…). Maya: Render Layer / Render Using + Common 탭 (경로, 이미지 크기, File Output, Frame Range, Renderable Cameras) | 외형 | 4 | 3 | 12 |
| 33 | Script Editor = Blender Python 콘솔 (Maya: 기록 창 + MEL / Python 입력 탭 + 메뉴·아이콘), Render View = Image Editor, Preferences = Blender 환경설정, Node Editor = Hypershade 와 같은 Shader Editor | 외형 | 3 | 2 | 6 |
| 34 | Windows 의 Component Editor · Connection Editor · Shape Editor · Render Layer Editor · Light Linking · Sets 회색, 안내 없음 (Blender Spreadsheet · Shape Keys · View Layers · Light Linking, kit sets 가 있음) | 기능 | 2 | 3 | 6 |

### 단축키 (부록 §4; 468 행 = 구현 155 · IC 15 · 해당 없음 11 · **미검토 219** · macOS 68)

| # | 차이 | 등급 | F | S | 점 |
|---|---|---|---|---|---|
| 35 | **잘못된 동작**: Alt+R = 스케일 초기화 (Maya ToggleReflection), Ctrl+I = 선택 반전, F1 = 앞 뷰 (Maya Help), Alt+C = 루프 컷 툴, m = 측정 툴, Ctrl+PgUp/PgDn = 작업공간 순환, Ctrl+, = 환경설정 | 조작 | 4 | 3 | 12 |
| 36 | **없음**: Ctrl+M / Shift+M / Ctrl+Shift+M (메뉴 바 토글), Alt+B (배경색 순환), 페인트 u / n / Shift+B / Alt+F / Ctrl+Alt+C·V, 스컬프트 Ctrl+1–9 / b / m, Graph Editor h / j / l, Time Slider 북마크 | 조작 | 3 | 3 | 9 |

### 콘솔 · 속도

- 첫 세션 콘솔: Channel Box 핸들러 AttributeError 4 (고침, 위). 그다음 `WARN pyrna_enum_to_py: current value '3' matches no enum in
  'SpaceProperties' … 'context'` 2 줄 — 원인: `menu_extras.properties_tab_later` 가 새 Properties 창이 그려지기 전 (탭 목록 없음) `space.context` 를 읽음 (대입 시도 뒤 1 번 + 타이머 등록 판단 1 번). **고침**: 대입이 성공했을 때만 다시 읽음 → probe 세션 콘솔 0 줄. 종료 시 Blender 의
  「Not freed memory blocks: 26」.
- 속도 (`tmp/audit7_probe2.py`, effective 1.0, 큐브 1 개): create 1.6 ms, 6 면 extrude 2.5 ms, Mesh > Smooth 0.7 ms, Hypershade 창 57.7 ms, Render Settings 창 65.3 ms — 체감 지연 없음. 세션 단계 간격 0.6 s 안에서 멈춤도 없었다.

## 검증

- Maya 촬영: `_log.txt` 끝 「done」, 146 장, 모달 대화상자 3 개 (Open / Save As / Import) 잡고 닫음.
- kit 세션 (최종, effective 1.0 + Maya 테마): `PASS audit7 session reached the end`, 125 장, 콘솔 오류 0 (위 WARN 2 + 종료 메모리 1).
- 나란히 비교 113 쌍 생성 (`A7PAIRS 113`). 그림은 직접 열어 보고 위 표를 적었다 (첫 화면, File 메뉴, Mesh / Edit Mesh / Modify 메뉴, Open
  대화상자, Export Selection, Project Window, Tool Settings, AE, UV, Graph Editor, Dope Sheet, Hypershade, Render Settings, Script
  Editor, 리깅, FX).
- 헤드리스: `python tests/run.py` **719/719** (88 파일; `-k step98` 1/1 — 수정 전 코드로는 AttributeError). 버그 3 수정 뒤 다시 719/719.
- 이어서 한 probe 세션 `tmp/audit7_probe2.py`: Render Settings 창 RENDER 탭 PASS, Joint Tool 모달 PASS, 본 3 개 (기대값을 2 로 잘못 적은 검사만 FAIL — kit 규칙은 N 클릭 = N 본), 콘솔 0 줄.

## 남은 것

- `docs/PLAN.md` 「재점검 7차(정밀 비판)」 우선순위 1–12 (= backlog.json).
- (이어서 끝냄) 표 #30 확인, SpaceProperties WARN 고침, 속도 측정 — 위 「콘솔 · 속도」.
- 하위 메뉴 그림 비교는 최상위 메뉴만 찍었다 (하위 메뉴는 부록의 수치 비교로 대신).
