# Step 102 — File I/O the Maya way: dialogs, Files of type, options, default project

backlog 4 (docs/PLAN.md 「재점검 7차」 4): step_98.md #15–#19, docs/steps/step_98_quant.md §2.

## 계획

근거: `research/maya/re/file_io.md` (mayapy: 기본 프로젝트, file rule, 왕복), Maya 대화상자
`research/maya/screens/audit7/pairs/b01_file_open_dialog.png`.

1. **대화상자** — Blender 파일 브라우저는 C 라 Maya Qt 대화상자를 그대로 만들 수 없다. 대신 Blender 브라우저의 세 영역을
   Maya 의 세 부분으로 쓴다: 위 경로 = Look in, 왼쪽 열 (TOOLS) 에 Python 패널 「Current Project」 (프로젝트
   드롭다운 = Recent Projects, 프로젝트 폴더 목록 클릭 = 그 폴더로, Set Project... = 보고 있는 폴더를 프로젝트로),
   오른쪽 옵션 영역 (연산자 draw) = Maya Options (Files of type, General Options = Maya 단위·축 프리셋, Selection Only,
   File Type Specific Options).
   - Import / Export All / Export Selection = kit 연산자 하나의 세 이름 (`maya_kit.file_import` / `file_export_all` /
     `file_export_selection`; 브라우저 버튼 글자가 bl_label 이라 셋으로 나눔). Files of type = Maya Scenes (.blend),
     FBX, OBJ, Alembic, USD, glTF (+ Import 의 Best Guess = 확장자로). 실행 = 형식의 Blender 연산자에 프리셋 인자.
   - Open / Save As 는 Blender 자신의 `wm.open_mainfile` / `save_as_mainfile` 브라우저 그대로 (연산자 안에서 파일을
     여는 위험을 피함, CLAUDE.md step 42) — 왼쪽 프로젝트 패널은 모든 파일 브라우저에 나오고, 옵션 영역은 Blender 의
     Load UI / Compress 등 (Maya General Options 자리).
   - 옵션 박스: 다섯 항목 모두 `option_box` 속성 → `run_action` 이 redo 패널 대신 대화상자를 엶 (옵션은 그 오른쪽 패널).
2. **기본 프로젝트** — Maya 는 처음부터 `Documents/maya/projects/default` (mayapy). kit: 설정된 프로젝트가 없으면
   `Documents/maya_kit/projects/default` (사용자 Maya 폴더는 건드리지 않음), 처음 대화상자를 열 때 Maya 폴더를 만듦.
   `MAYA_KIT_PROJECTS_DIR` 가 위치를 바꿈 (테스트 샌드박스: tests/run.py, release_check.sandbox_env).
   대화상자 시작 폴더 = Maya file rule (OBJ = data, Alembic = cache/alembic, 그 밖 = scenes).
3. **프리셋** (`operators/file_io.import_args` / `export_args`, 순수 함수): Maya 장면 = cm, Y-up. FBX 는 단위·축을
   파일에 담으므로 Blender 변환 그대로, OBJ / Alembic 은 단위가 없어 숫자 = Maya 단위 (× 1/maya_unit), USD 는
   metersPerUnit = maya_unit. 검증 = mayapy 왕복.

## 한 것

- `operators/file_io.py`: FORMATS 표, 프리셋 함수, `preset_text` (옵션 패널 설명), .blend 를 Maya 장면처럼
  (Import = 오브젝트를 파일 이름 컬렉션으로 붙임, Export All = 사본 저장, Export Selection = `libraries.write`),
  대화상자 연산자 4 (file_dialog = mode 지정용 일반형 + 메뉴용 3), `file_goto`, `file_set_project`.
- `ui/file_project.py`: 파일 브라우저 왼쪽 「Current Project」 패널.
- `operators/project.py`: `default_root()` / `ensure_root()`, `current_root()` 가 기본 프로젝트를 돌려줌, Project Window
  의 이름 = 현재 프로젝트 (default; 전 "new_project"), Open / Save As 에 `option_box`.
- `menu_map`: File > Import / Export All / Export Selection = 새 대화상자 (전 Blender 형식 하위 메뉴).
- 결정 (delegated): Open / Save As 는 Blender 브라우저 유지; 프로젝트 패널은 Blender 북마크 아래 (bl_order 로 앞당길 수
  없음, 측정); glTF 는 프리셋 없음 (표준이 m, Y-up); USD 를 Maya Units 옵션 (1 BU = 1 cm) 에서 쓰면 metersPerUnit = 1 로
  적혀 Maya 가 100 배로 읽음 (템플릿 기본 cm 장면은 정확) — 남은 것.

## 검증

- mayapy 왕복 (`research/maya/re/file_io.md` §2): kit → Maya FBX / OBJ / Alembic / USD 모두 bbox 10 × 20 × 5 cm,
  Y-up; Maya → kit 네 형식 모두 0.1 × 0.05 × 0.2 BU (= 10 × 5 × 20 cm, Maya Y → Blender Z).
- 헤드리스 `tests/test_step102_file_io.py` 8/8 (프리셋 값과 연산자 속성 존재, Files of type / Best Guess, 메뉴 연결과
  옵션 박스, 기본 프로젝트 폴더, Blender 안 왕복 5 형식, OBJ 숫자 = cm·Y-up, Export Selection 은 선택만, Maya 가 쓴 파일
  4 개 크기). 전체 747/747, GUI 전체 1027/1027.
- GUI `tests/gui/gui_step102_file_dialog.py` 8/8: Import 대화상자가 기본 프로젝트 scenes 에서, Export Selection OBJ 는
  data 에서 .obj 이름으로, Open Scene 도 scenes 에서 시작 (Documents 아님). 비교 그림
  `research/maya/screens/step102/file_dialog_maya_vs_kit.png` (Maya 왼쪽, kit 오른쪽: 경로 줄, 왼쪽 프로젝트 목록, 오른쪽
  Files of type + 옵션, 아래 파일 이름 + Import).

## 남은 것

- Files of type 이 Maya 처럼 아래 줄이 아니라 오른쪽 옵션 위 (Blender 브라우저 아래 줄은 C 고정). 프로젝트 패널이
  Blender System / Volumes 목록 아래라 작은 창에서는 스크롤 필요.
- Maya 기본 폴더 중 「Time Editor」「sceneAssembly」 는 kit 프로젝트 폴더에 없음.
- Open 의 Files of type (FBX 를 새 장면으로 열기) 없음: Import 로.
- USD + Maya Units 옵션 의 metersPerUnit (위 결정). 옵션 창 다듬기는 step 103.
