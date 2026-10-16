# Step 13 — 통합·배포

PLAN 표 #14 (사용자 번호 13).

## 계획

- 검증 순서: 전체 헤드리스 테스트 → `tools/build.py` → `blender --command extension validate` (zip + 소스) → **깨끗한 샌드박스
  설정**(`tmp/release_env`, 빈 config/scripts/extensions)에 `extension install-file -r user_default --enable` → 그 설정으로 GUI Blender 를
  `--factory-startup` 없이 실행(실제 첫 시작과 같게) → 확장·Maya 키맵 활성 확인 → Maya 레이아웃 설치 → 템플릿 로드 → 데모 씬 →
  `docs/screenshots/` 세트. 자동화: `tools/release_check.py` (+ Blender 안 스크립트 `tools/release_shots.py`, `tests/gui/sim.py` 재사용).
- 문서: README.md (한국어 + 영어: 설치, 기능, Maya↔Blender 대응표, C++ 벽 = `research/blender/api_limits.md` "Things that are C-only"),
  CHANGELOG.md (Keep a Changelog), LICENSE (GPL-3.0 전문, Blender 설치본 `license/spdx/GPL-3.0-or-later.txt` = FSF 원문) — 저장소 루트와
  익스텐션 패키지(`src/maya_kit/LICENSE`) 양쪽 (delegated: 패키지에도 라이선스 원문 동봉).
- 버전 0.1.0 유지 (첫 릴리스, delegated).

## 한 것

- `tools/release_check.py`, `tools/release_shots.py`: 위 순서 자동화, 체크 10개, 스크린샷 7장.
- 매니페스트 `[permissions] files` 문구 갱신 (셸프 저장 추가). validate 가 64자 제한으로 처음에 실패 → 줄임.
- **릴리스 점검이 찾은 결함 2건 수정**:
  1. 명령줄 `install-file --enable` (백그라운드) 가 `keymap_auto_activated` 표시는 저장하고 활성 키컨피그는 저장하지 않아, 첫 GUI 시작이
     Blender 키맵으로 남았다 → 표시를 GUI 세션에서만 저장 (`keymap/__init__.py`).
  2. 새 설정에서는 `scripts/startup` 이 Blender 시작 뒤에 생겨 `sys.path` 에 없으므로, 처음 설치한 세션에서 템플릿 `__init__` 이
     import 되지 않았고(`ModuleNotFoundError: bl_app_templates_user`), 템플릿 전환이 저장된 환경설정을 다시 읽어 Maya 키맵이 풀렸다 →
     설치 직후 `bpy.utils.refresh_script_paths()`, 템플릿 `register()` 가 활성 키맵이 기본 "Blender" 일 때 Maya 키맵을 다시 켬.
- README.md, CHANGELOG.md, LICENSE (+ `src/maya_kit/LICENSE`), `docs/screenshots/01_layout … 07_outliner_rigging_shelf.png`.
- `tests/test_step13_release.py` (3): 두 LICENSE 동일·GPL-3, 매니페스트 SPDX, zip 내용(매니페스트·LICENSE·템플릿 포함, `__pycache__`/
  `.blend1`/Maya 리소스·research 없음), 백그라운드 활성화가 키맵 선택 표시를 남기지 않음.
- 레거시 zip: 샌드박스(`tmp/legacy_env`)에서 `preferences.addon_install` → 활성화 → Maya 키맵·연산자·셸프 저장 경로(사용자 config 아래)
  → 비활성화 확인 (Step 1 에서 미룬 항목).

## 검증

- 헤드리스 `python tests/run.py`: **188/188** (14 파일).
- GUI `python tests/gui/run.py`: **115/115** (수정 뒤 재실행).
- `blender --command extension validate`: zip·소스 모두 "Success parsing TOML", exit 0.
- `python tools/release_check.py`: validate PASS, install + enable PASS, 첫 시작 확장 활성·Maya 키맵 PASS, 레이아웃 설치 PASS, 템플릿 로드 뒤
  Maya 키맵 유지 PASS, Maya 띠 PASS, Maya 이름 PASS, 사이드바 탭 2개 PASS (exit 0).
- 스크린샷 7장 직접 확인: 레이아웃(메뉴바/Status Line/Shelf/Outliner/Channel Box), Create 메뉴, RMB 마킹메뉴, 핫박스, AE transform,
  AE history, Outliner + Rigging 셸프.

## 결정 (delegated)

- LICENSE 원문을 루트와 패키지 양쪽에 둠 (테스트가 같음을 확인). 버전 0.1.0.
- 템플릿 로드 시 Maya 키맵 재활성은 활성 키맵이 "Blender" 일 때만 (사용자가 다른 키맵을 골랐으면 존중).
- 스크린샷은 1600×900, 샌드박스 첫 시작 그대로 (Maya 테마는 적용하지 않음 — 테마는 사용자가 고르는 옵션).

## 남은 것

- Blender Extensions 플랫폼 등록(아이콘·태그·웹사이트 필드), 서명된 릴리스 — 원격 저장소 없음.
- 첫 실행 Quick Setup 창의 Continue 가 키맵을 "Blender" 로 바꿀 수 있음 (README 에 안내, manual_checks).
- 이전 단계 「남은 것」: 메뉴셋 F2–F6 키, Range Slider·타임라인 모양, Status Line 입력 라인, 마킹메뉴 편집기, 셸프 드래그 정렬 등.
