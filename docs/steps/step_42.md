# Step 42 — 켜자마자 Maya: 첫 시작 경로

backlog 2 (`docs/PLAN.md` 「Maya 동일화 계획」). 근거: `research/maya/screens/compare/00_first_start.png` (지금: 키맵만 켜지고 레이아웃
설치·열기·테마가 각각 버튼, Blender 스플래시), step_40.md blindspot 1·2·12·16, `research/competitors.md` 6절 (경쟁 제품 불만: 설치가
기존 애드온을 지움).

## 실측: 앱 템플릿 `userpref.blend` (a)

`tmp/exp42/probe.py` (샌드박스, 헤드리스, 4 프로세스). 사용자 설정 = node_wrangler 켬·빨강 그라디언트·ui_scale 1.1·TRACKBALL,
템플릿 `userpref.blend` = rigify 켬 (node_wrangler 끔)·파랑·Segoe UI·ui_scale 0.8·ui_styles 9 pt·TURNTABLE.

| 템플릿 진입 시 | 결과 [O] |
|---|---|
| 테마 | 템플릿 것 (파랑) |
| **add-on 목록** | **템플릿 것** — 사용자 node_wrangler 꺼짐, rigify 켜짐 |
| `font_path_ui`, `ui_scale`, ui_styles | 템플릿 것 |
| 입력 (회전 방식) | 사용자 것 그대로 |
| 템플릿 안에서 바꾼 설정 | `config/T42/userpref.blend` 에 따로 저장, 기본 Blender 로 돌아가면 사용자 값 그대로 |
| 다음 시작 | 기본 템플릿으로 시작 (템플릿은 기억되지 않음) |

→ **기각 (delegated)**: 사용자 add-on 이 Maya 레이아웃 안에서 꺼진다 (경쟁 제품이 욕먹는 바로 그 문제), 그리고 템플릿 안 설정이
따로 갈라져 나중에 바꾼 사용자 설정이 Maya 레이아웃에 안 따라온다.

사고 기록: 첫 실험은 `BLENDER_USER_*` 폴더를 만들지 않고 띄워, Blender 가 환경 변수를 무시하고 **사용자 실제 `userpref.blend` 를
읽고 저장했다** (14:19). 바뀐 값 4개 (3D 뷰 그라디언트 위쪽 색, ui_scale 1.3, 회전 방식 TRACKBALL, node_wrangler 켬) 중
테마 (나머지 테마 값이 모두 팩토리와 같음 → 팩토리 값)·ui_scale (1.0)·회전 방식 (TURNTABLE) 을 팩토리 값으로 되돌림.
node_wrangler 는 원래 상태를 몰라 켠 채로 둠. 되돌리기 전 파일은 `tmp/exp42/userpref_real_after_experiment.blend`.
재발 방지: CLAUDE.md 규칙 (폴더 먼저 만들기, 스크립트는 config 경로가 tmp/ 안인지 단언).

## 계획 (delegated)

1. **「Make Blender Maya」 한 번에** (`maya_kit.make_maya`): 레이아웃 템플릿 설치 → Maya 테마 켬 → Blender 스플래시 끔 →
   「Maya 레이아웃으로 시작」 켬 → 새 파일을 MayaKit 템플릿으로 연다 (저장 안 된 변경이 있으면 확인). 각각 환경설정 옵션이고,
   **「Revert Maya Look」** (`maya_kit.revert_maya`) 은 모두 끄고 (테마·스플래시 복원) 템플릿을 지운다. 현재 파일은 그대로.
2. **환영 대화상자** (`maya_kit.welcome`): 확장을 켠 뒤 첫 GUI 시작 (또는 GUI 에서 켠 직후) 한 번, kit 시작 화면 이미지 +
   "Make Blender Maya" 확인 버튼 = **1 동작**. 닫으면 다시 묻지 않음 (환경설정에 버튼은 남음). 백그라운드 `install-file --enable`
   에서는 표시 플래그를 저장하지 않는다 (step 13 규칙). GUI 테스트·dogfood 는 `MAYA_KIT_NO_WELCOME=1`.
3. **시작 시 Maya 레이아웃** (옵션 `start_in_maya_layout`): Blender 가 파일 없이 시작해 시작 파일을 읽은 직후 (load_post) MayaKit
   템플릿으로 바꾼다. 확장을 켤 때 load_post 를 무장하고 첫 타이머 틱에 해제 → 시작 때만 동작, 세션 중 File > New > General 은
   건드리지 않는다. 파일을 열고 시작했거나 이미 다른 템플릿이면 안 바꾼다.
4. **테마 = 옵션** (`maya_theme`): 켜면 백업 후 적용, 끄면 복원; **확장을 끄면 복원** (CLAUDE.md prefs_preset 규칙과 같은 모양),
   다시 켜면 옵션이 켜져 있으면 재적용. 스플래시는 `prefs_preset.GROUPS["splash"]` (`view.show_splash` False, 기본 꺼짐).
5. **시작 화면 이미지** (c): `tools/make_splash.py` 가 Blender 워크벤치로 kit 자체 그림 (Maya 회색 바탕, 와이어 큐브 + 리드 연두,
   "Maya Kit" 글자, "Autodesk 와 무관" 표기) 을 렌더 → 템플릿 `splash.png` / `splash_2x.png` (Blender 가 템플릿 활성 시 스플래시로
   씀) + 환영 대화상자 그림. Maya 이미지·로고는 쓰지 않음 (결정 6).
6. 뷰 배경 단색 #5c5c5c + 그리드 #404040 (blindspot 3, 같은 커밋) 을 지금 넣는다: 이 단계 검증 기준 (뷰 배경 ΔE00 < 2) 에 필요.
   나머지 테마 색은 step 43.
7. `tests/kit.py` 스냅숏에 `themes[0]` (값 해시) · `ui_styles` 추가.
8. 결정 3 개정 (delegated): 템플릿 설치는 여전히 사용자 동작 (환영 대화상자 / Make Blender Maya / 설치 버튼) 으로만, 제거는 Revert /
   Remove 버튼. 추가: 옵션을 켜면 시작 시 Maya 레이아웃.

검증: 헤드리스 — node_wrangler 를 미리 켜 두고 make_maya → 그대로 켜져 있음, 테마·스플래시·템플릿·현재 템플릿, revert / disable 후
테마 해시·show_splash 복원. GUI — 깨끗한 설정 `install-file --enable` → GUI 시작 → 환영 대화상자 → Return 1 번 → Maya 레이아웃 + 테마
(look_compare `pixels.md`: 메뉴바·패널·뷰 배경 지점 ΔE00 < 2), 두 번째 GUI 시작이 MayaKit 으로 열림.

## 한 것

- `src/maya_kit/first_start.py` (새): `maya_kit.make_maya` (Make Blender Maya), `maya_kit.revert_maya` (Revert Maya Look),
  `maya_kit.welcome` (확인 버튼 = Make Blender Maya, 한 번만), 시작 시 Maya 레이아웃 (load_post 무장 → 첫 타이머 틱에 해제).
- 환경설정: 맨 위에 두 버튼 + 옵션 `maya_theme` / `maya_hide_splash` (`prefs_preset.GROUPS["splash"]`) / `start_in_maya_layout`,
  숨은 `welcome_done`. 테마 상자 (Apply/Restore 버튼) 는 옵션으로 대체 (오퍼레이터는 남김: 옵션을 켜고 끔).
- `theme/__init__.py`: 적용·복원을 `rna_xml` 로 **Preferences 구조체 기준** 경로 (`themes[0]`, `ui_styles[0]`) 로 바꿈 —
  템플릿 전환이 prefs 를 다시 읽으며 add-on 을 unregister/register 하는데, 그때는 context 가 제한돼 프리셋 오퍼레이터와 context
  경로가 실패한다. 테마 `filepath` 도 백업·복원 (안 하면 해시가 달라짐). 확장을 끄면 복원, 옵션이 켜져 있으면 다시 켤 때 재적용.
- **버그 수정** (`app_template.layout_open` 에도 있던 것): 오퍼레이터 안에서 `read_homefile(app_template=...)` 을 부르면 그 사이 add-on
  이 재등록되어, 오퍼레이터 보고 단계에서 Blender 가 죽었다 (`WM_operator_pystring`, 헤드리스 재현). 템플릿 열기는 이제 오퍼레이터가
  끝난 뒤 타이머로 (`first_start.open_layout_later`).
- 테마: 뷰 배경 단색 0.36 + 그리드 0.25 (`tools/make_theme.py`, blindspot 3).
- `tools/make_splash.py` (새, 워크벤치 렌더): 템플릿 `splash.png` / `splash_2x.png`, 대화상자용 정사각 `welcome.png`.
- `tests/kit.py` 스냅숏: `theme` (값 해시), `ui_styles`. GUI 테스트·dogfood·release_check 는 `MAYA_KIT_NO_WELCOME=1`.
- `tools/look_shots.py` 첫 장면 = 깨끗한 설정의 실제 첫 시작 (환영 대화상자 → Return 1 번), `tools/look_second_start.py` = 같은
  설정으로 두 번째 GUI 시작. look_compare 가 둘의 체크를 출력.
- 결정 3 개정 → `docs/user_decisions.md` 9.

## 검증

- 헤드리스 `python tests/run.py`: **348/348** (39 파일; 새 `test_step42_first_start.py` 4: 샌드박스 확인, 테마 옵션 → 끄면 해시 그대로,
  node_wrangler 를 켜 둔 채 make → 템플릿 MayaKit·테마·스플래시 끔·**add-on 목록 그대로**·템플릿에 userpref.blend 없음 → revert →
  테마 해시·show_splash·템플릿 제거 복원, open_layout=False 는 파일 유지). `test_enable_disable` 누수 0 (테마·ui_styles 포함).
- GUI `python tests/gui/run.py`: **281/281**. `python tools/dogfood.py`: **47/47**, 콘솔 오류 0. `python tools/release_check.py`: PASS
  (docs/screenshots 재생성).
- `python tools/look_compare.py` (깨끗한 설정 `install-file --enable` → GUI): 체크 9/9 — Return 1 번에 MayaKit 템플릿, 테마 켬·스플래시 끔,
  Maya 키맵; 두 번째 시작 = MayaKit 템플릿·테마·스플래시 없음·대화상자 다시 안 뜸. `pixels.md`: 메뉴바 0.0, 패널 (Status Line·
  Outliner 메뉴·CB·타임라인 헤더·상태바) 0.0, **뷰 배경 0.0** (전 20.1). 전체 픽셀 ΔE>5 9 → 7, 테마 쌍 11 → 9.
- `00_first_start.png` (환영 대화상자 + Blender 스플래시), `01_layout_empty` 나란히 이미지를 직접 확인.

## 남은 것

- 실제 OS 입력으로 설치·환영 대화상자·재시작 확인: `docs/manual_checks.md` 「Step 42」 5 항목.
- 첫 시작에는 Blender 스플래시가 환영 대화상자와 함께 뜬다 (스플래시 끔은 Make 이후부터). 스플래시를 닫는 API 가 없어 그대로 둠.
- 템플릿 `splash.png` 는 MayaKit 템플릿이 활성일 때만 보인다 (Help > Splash Screen); 시작 화면은 스플래시를 끄므로 주로 환영
  대화상자에서 보인다.
- 사용자 실제 설정 사고 (위 「실측」): node_wrangler 가 켜진 채 남음 — 사용자 확인 필요.
