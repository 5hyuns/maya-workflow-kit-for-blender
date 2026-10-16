# Step 5 — M2-a 레이아웃 App Template, Maya 테마

## 계획

근거: `research/maya/ui_layout.md` §2 (General 레이아웃·스플리터 트리 :78-139), §4.5–4.13 (요소별), `research/maya/concepts.md` §12 (cm, 24 fps, 재생 1–120) · §15 (빈 씬, persp 초점거리 35), `research/blender/ui_architecture.md` §1–2 (startup.blend 권장, `bl_app_templates_user`), decisions 1 (표시 단위 cm) · 3 (템플릿을 익스텐션에 넣고 설치/제거 버튼).

### 레이아웃 (Maya General → Blender, delegated)

```
+-- TOPBAR (Blender 메뉴 + 워크스페이스 탭; Status Line 은 Step 7) ---------------+
| Outliner |T| 3D View (Persp, lens 35)            |N: Channel Box | Outliner     |
| (16%,    |o|  툴바 = Maya Toolbox,               |  (사이드바,    | (Layer Editor:|
|  DAG만,  |o|  tool header 숨김                   |   Step 6 패널) |  컬렉션만 32%)|
|  데이터·  |l|                                     |               |--------------|
|  모디파이어|s|                                    |               | Properties   |
|  숨김)    | |                                     |               | (AE, 68%)    |
+----------+-+-------------------------------------+---------------+--------------+
| Timeline (Time Slider + 헤더의 시작/끝 = Range Slider 자리; 레인지 슬라이더는 Step 7) |
+-- STATUSBAR (= Help Line; Command Line 은 Step 7) ------------------------------+
```

- Maya 오른쪽은 CB/LE·AE 한 탭 스택. Blender 는 영역 탭이 없으므로: Channel Box = 3D 뷰 사이드바(뷰포트 옆, 전체 높이), Layer Editor = 컬렉션만 보이는 Outliner(오른쪽 위), AE = Properties 영역(오른쪽 아래, Object 탭).
- 오른쪽 열 순서는 Maya(위 CB, 아래 LE)와 다르다 (delegated): 팩토리 오른쪽 열(위 Outliner 32% / 아래 Properties 68%)을 그대로 쓴다. 헤드리스에서 `screen.area_close` 는 멈추고, `screen.area_move` 는 효과가 없고, 다른 에디터에서 바꾼 Properties 는 탭 목록이 비어 Object 탭을 지정할 수 없었다 (모두 실측).
- 워크스페이스 "Layout" → "General" (Maya 이름), 다른 Blender 워크스페이스는 유지.
- 씬: 표시 단위 cm (`length_unit='CENTIMETERS'`, `scale_length=1.0`, decision 1), 재생 1–120 (PREF:469-472), 24 fps, 빈 씬 (Cube/Light/Camera 삭제, concepts §15), 뷰포트 렌즈 35.

### 생성 방법

- `tools/make_startup.py`: `blender -b --factory-startup` 에서 팩토리 "Layout" 화면을 `screen.area_split`(창/화면 컨텍스트 오버라이드)로 나누고 `area.type` 변경 → `src/maya_kit/app_template/MayaKit/startup.blend` 저장. **헤드리스 확인**: `-b` 에서도 창 1개가 있어 분할이 되고, 저장한 파일을 GUI 로 열면 비율대로 배치됨 (분할 직후 `area.width` 는 0 으로 보이지만 로드 시 재계산).
- 템플릿 `__init__.py`: 템플릿을 고르면 Maya Kit 익스텐션이 꺼져 있을 때 켠다 (기본값 저장 안 함).
- 설치/제거 (`app_template/__init__.py`): 사용자 `scripts/startup/bl_app_templates_user/MayaKit` 로 복사, 표식 파일 `.maya_kit` 이 있는 폴더만 제거. 「Maya 레이아웃 열기」 = `wm.read_homefile(app_template="MayaKit")`. manifest `[permissions] files`.

### 테마

- `tools/make_theme.py`: 팩토리 테마로 리셋 → 색 표 적용 → `rna_xml.xml_file_write` (Blender 테마 프리셋과 같은 `preset_xml_map`) → `src/maya_kit/theme/maya.xml`.
- 색 근거: **[O]** 사용자 Maya 2022 prefs `~/Documents/maya/2022/prefs/userRGBColors2.mel` / `userPrefs.mel` (`displayViewportGradient 1`, `backgroundTop 0.535 0.617 0.702`, `backgroundBottom 0.052 0.052 0.052`, `timeSliderBackground 0.168627`, `timeSliderKey 1 0 0`, `timeSliderActiveKey 0.9 0.9 0`, `graphEditorGrid 0.325`, `graphEditorGridAxis 0.478`, `template 0.47`), `scripts/others/cycleBackgroundColor.mel:29` (단색 배경 기본 0.36), `research/maya/ui_layout.md:303` (#535353). **[K]** Maya UI 패널 회색 #444444, 버튼 #5D5D5D, 입력 필드 #2B2B2B, 선택 파랑 #5285A6, 오브젝트 와이어 짙은 파랑 / 선택 초록 / 리드 흰색 — Maya UI 팔레트는 텍스트 파일에 없음 (`ui_layout.md:303,310` [U]).
- 적용/복원 버튼: 적용 전 현재 테마를 익스텐션 사용자 폴더에 XML 로 백업 → `script.execute_preset(menu_idname="USERPREF_MT_interface_theme_presets")` (리셋 후 적용). 활성화 시 자동 적용하지 않음 (사용자 테마를 말없이 바꾸지 않기).

### 테스트

- 헤드리스: 템플릿 설치·재설치·제거·남의 폴더 제거 거부, startup.blend 로드 후 화면 구성(영역 종류·좌우 위치·필터·사이드바·렌즈)·씬 설정, 테마 XML 적용 값·백업 복원.
- GUI: 템플릿 로드 + 테마 적용 스크린샷을 직접 보고 확인, 영역 위치 검사.

## 한 것

- `tools/make_startup.py` (헤드리스) → `src/maya_kit/app_template/MayaKit/startup.blend` (86 KB): 워크스페이스 "General", 좌 Outliner(16%, 오브젝트 내용 숨김), 중앙 Persp 3D 뷰(렌즈 35, 사이드바 표시, 툴 헤더 숨김), 우상 Layer Editor(컬렉션만 Outliner), 우하 Properties(Object 탭), 하단 타임라인, cm 표시·1–120·24 fps·빈 씬.
- `app_template/MayaKit/__init__.py`: 템플릿 선택 시 Maya Kit 이 꺼져 있으면 켬.
- `app_template/__init__.py`: `maya_kit.layout_install` / `layout_remove` (표식 `.maya_kit` 있는 폴더만) / `layout_open` (확인 후 `read_homefile(app_template="MayaKit")`).
- `tools/make_theme.py` → `src/maya_kit/theme/maya.xml` (50 KB, Blender 테마 프리셋 형식). `theme/__init__.py`: `maya_kit.theme_apply` (첫 적용 전 현재 테마를 익스텐션 사용자 폴더에 백업) / `theme_restore`.
- 환경설정: 레이아웃 설치/재설치/제거/열기, 테마 적용/복원 버튼. manifest `[permissions] files`, 빌드 제외 `*.blend1`.
- `tests/gui/sim.py` 타이머를 persistent 로 (템플릿 로드 = `read_homefile` 후에도 테스트 계속).

## 검증

```
python tests/run.py        → 61 passed, 0 failed, 6 file(s)
python tests/gui/run.py    → 47 passed, 0 failed, 3 file(s)   (step 5: 11)
```

- 헤드리스 `test_step5_layout.py` (6): 설치 위치가 샌드박스 `BLENDER_USER_SCRIPTS` 안·파일 3개·재설치, 제거·없는데 제거·**표식 없는 남의 폴더는 설치/제거 모두 거부(파일 보존)**, 번들 파일 목록, 테마 적용 값(그라디언트 상단 0.535/0.617/0.702, 키 빨강, 버튼 #5D5D5D)·백업 위치(샌드박스)·복원, 두 번 적용해도 첫 백업 유지, 템플릿 로드 후 화면 구성(영역 5개 종류, DAG Outliner, 컬렉션 Outliner, 사이드바/툴바/툴헤더, 렌즈 35)·씬(cm, 1–120, 24 fps, 오브젝트 0)·애드온 활성.
- GUI `gui_step5_layout.py` (11): 실제 창에서 Outliner 가 뷰포트 왼쪽(창 폭의 10–22%), Properties 오른쪽, Layer Editor 가 같은 열 위, 타임라인 바닥 전체 폭, 오브젝트 생성 시 Properties 가 Object 탭.
- 스크린샷 직접 확인 (`gui_step5_layout.png`, `gui_step5_object.png`): Maya 식 회청→검정 그라디언트 뷰포트, 밝은 회색 UI, 리드 선택 흰 윤곽, 위치 필드 "0 cm", 타임라인 현재 프레임 빨강, End 120.
- 사용자 실제 설정(`%APPDATA%/Blender Foundation/Blender/4.5/config/userpref.blend` 2026-03-05, `scripts/` 비어 있음) 변화 없음.

## 결정 (delegated)

- 오른쪽 열 = 위 Layer Editor / 아래 Properties (「계획」 참고, 헤드리스 제약).
- Channel Box 자리 = 3D 뷰 사이드바 (Step 6 에서 카테고리 추가).
- 다른 Blender 워크스페이스(Modeling, Shading …)는 유지, 첫 탭만 "General".
- 빈 씬 (카메라·라이트도 삭제, Maya 새 씬과 같음).
- 테마는 자동 적용하지 않고 버튼으로만; 테마 색 중 [K] 는 Maya UI 팔레트가 텍스트에 없어 근사.
- 템플릿 폴더 이름 "MayaKit" (File > New 메뉴에 표시).

## 남은 것

- 타임라인 뷰 범위가 0–250 으로 보임 (재생 범위 1–120 에 맞춘 뷰 아님) — 헤드리스에서 뷰 범위 설정 미구현.
- 사이드바 폭(약 300 px)은 조절 안 함 (Maya CB 260 px).
- Range Slider·Command Line·Status Line → Step 7. Channel Box 패널 → Step 6. Shelf → Step 13.
- Maya 그리드(간격 5, 분할 5)와 오브젝트 와이어 색의 실제 Maya 비교 → manual_checks.
