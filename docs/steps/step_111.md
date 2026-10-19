# Step 111 — Distribution prep 1: rename to "Allset for Maya Users" + trademark hygiene

User decision 2026-10-19 (`docs/user_decisions.md` 12): publish free on extensions.blender.org as **Allset for Maya
Users** (id `allset`, tagline "The whole Maya workflow in Blender, in one install"). Sources:
`docs/distribution/extensions_audit.md` (copy of the platform / Autodesk trademark audit), `docs/distribution/naming.md`
(copy-masters run summary).

## 계획

1. Docs: audit copy, naming summary, decision 12.
2. Package: `git mv src/maya_kit src/allset`, app template `MayaKit` → `Allset`, installer files `maya_kit*` → `allset*`.
3. Mechanical rename in tracked code / tests / tools / CLAUDE.md / README / manual_checks (ordered):
   `MAYAKIT_` → `ALLSET_`, `MAYA_KIT` → `ALLSET` (env vars), `maya_kit` → `allset` (operator ids, RNA props, ID props,
   module path `bl_ext.user_default.allset`, zip names), `MayaKit` → `Allset` (template, strip masks), `Maya Kit` → `Allset`.
   History docs (`docs/steps/*`, HANDOFF history, PLAN, CHANGELOG entries) keep their wording. Nothing is published, so
   no migration for old ID / RNA property names in user files (delegated); the old template install `MayaKit` is removed
   when the new one is installed or the layout is removed (only if it carries the kit marker).
4. Brand-like user-visible names → neutral: keyconfig "Maya" → "Maya-style", workspace "Maya" → "Maya-style",
   theme preset → "Studio Grey (Maya-inspired)" (`theme/studio_grey.xml`), hotbox centre title "Maya" → "Allset",
   Help > "Autodesk App Store" → "Blender Extensions" (generator rename), splash / welcome text → Allset message.
   Labels that describe Maya behaviour ("Maya-style", Maya menu names) stay.
5. Positioning text (README first paragraph, preferences description / About, splash): other tools give one piece at a
   time (pivot, keymap, shelf, theme), Allset brings the whole Maya workflow in one install. Trademark notice (English,
   audit 「필수 고지문」) in README, preferences About and the manifest-adjacent docs.
6. Check: no Autodesk logo / icon / Maya screen capture in the package or `docs/screenshots/`; `git grep` for the old
   prefixes = 0 outside history docs; regenerate generated files (`startup.blend`, theme XML, menu data, keymap mapping,
   splash); full headless + GUI tests.

## 한 것

- 문서: `docs/distribution/extensions_audit.md` (감사 파일 사본), `docs/distribution/naming.md` (copy-masters 결과 요약: 최종
  Allset for Maya Users, 스토어 카피 후보 2), `docs/user_decisions.md` 12 (사용자 지시의 「결정 8」 — 8 번이 이미 단위 규칙이라 12 번,
  delegated), `docs/DISTRIBUTION.md` 머리에 결정 안내, CHANGELOG `[Unreleased]`.
- 이름: manifest `id = "allset"`, `name = "Allset for Maya Users"`, tagline "The whole Maya workflow in Blender, in one install".
  패키지 `src/maya_kit` → `src/allset`, 앱 템플릿 `MayaKit` → `Allset`, 설치기 `tools/installer/allset*`, zip `allset-<ver>.zip`.
- 기계적 변경 (`tmp/s111/rename.py`, 추적 파일 323 개): `MAYAKIT_` → `ALLSET_` (클래스 850 곳), `maya_kit.` → `allset.`
  (연산자 id), `maya_kit_*` → `allset_*` (RNA / ID 속성, strip 마스크 `.AllsetStrip`), `MAYA_KIT_*` → `ALLSET_*` (환경 변수),
  `bl_ext.user_default.allset`. 역사 문서 (docs/steps, PLAN, HANDOFF 기록, CHANGELOG 기존 항목) 는 그대로.
- 브랜드처럼 보이던 이름 → 중립: 키컨피그 "Maya" → "Maya-style", 작업 공간 "Maya" → "Maya-style", 테마 이름
  "Studio Grey (Maya-inspired)" (`theme/studio_grey.xml`), 핫박스 가운데 제목 "Maya" → "Allset", Help >
  "Autodesk App Store" → "Blender Extensions" (`tools/gen_menu_data.py` `LABEL_RENAMES`, 재생성), 스플래시 / 환영 창 문구.
  Maya 동작을 설명하는 라벨 (Maya-style, Maya 메뉴 이름, Maya / Blender 전환) 은 그대로.
- 포지셔닝 + 상표 고지문: README 첫머리 (영문·한국어: 다른 도구는 한 조각씩 — 피벗·키맵·셸프·테마, Allset 은 워크플로우 전체를
  한 번에), 환경설정 맨 위 About 상자 (`preferences.draw_about`: 같은 설명 + 영문 고지문), 스플래시 ("for Maya users" / tagline).
- 예전 설치 정리: `app_template.remove_legacy()` — 레이아웃 설치·제거 때 `bl_app_templates_user/MayaKit` 을 표시 파일
  `.maya_kit` 이 있을 때만 지움.
- 재생성: `startup.blend` (make_startup, GUI), 스플래시·환영 그림 (make_splash), `menu_data.py`, `docs/keymap_mapping.md`,
  `docs/screenshots/` (release_check). 테마 XML 은 다시 만들어도 같음.

delegated:
- 아직 공개 전이라 예전 RNA / ID 속성 이름 (`maya_kit_*`) 을 쓰는 사용자 파일은 옮기지 않음.
- 키컨피그 이름은 "Maya-style" (Blender 의 "Industry Compatible" 처럼 동작을 설명하는 이름).
- 「Autodesk Account」 같은 Maya 메뉴 재현 라벨은 회색 + 안내로 그대로 (감사가 지적한 것은 App Store 하나).

## 검증

- 남은 옛 이름: `git grep -E "maya_kit|MAYAKIT|MayaKit|Maya Kit|MAYA_KIT|maya\.|MAYA_(OT|PT|MT)_"` (역사 문서 제외) =
  **0** (예전 템플릿 정리 코드의 `LEGACY` 한 줄과 그 주석만, 의도).
- 헤드리스 전체 **846/846** (99 파일), GUI 전체 **1074/1074** (86 파일), 뒤에 바꾼 환영 창·환경설정 뒤 enable / step42 / step13 / step61 다시 통과.
- `tools/release_check.py`: `extension validate` PASS (`dist/allset-0.1.0.zip`), 깨끗한 설치·키맵 "Maya-style"·되돌리기 모두
  PASS, 한 항목 FAIL 「sidebar shows the Channel Box / Layer Editor tab (got 'Item')」 — **이름 변경 전 커밋 a97abb3 에서도 같은
  FAIL** (worktree 로 재현), step 99 의 도크 탭 이후 생긴 release_shots 스크립트 문제. 스크린샷 자체는 Channel Box 탭.
- 패키지 그림 = 킷이 만든 것뿐 (splash / splash_2x / welcome.png, startup.blend, 셸프 아이콘은 코드로 그림). `docs/screenshots/`
  7 장 = 킷 화면 (Autodesk 로고·아이콘·Maya 화면 캡처 없음, 직접 봄).

## 남은 것

- release_shots 의 사이드바 탭 확인 (Ctrl+휠 대신 `allset_dock` 설정) — 이름 변경과 무관, 다음 배포 단계에서.
- step 112 (가이드라인 위반 2 건: `sys.modules["maya"]` 삽입, 자산 CC0 표기), 113 (opt-in, 정리, monkeypatch), 114 (등록 자료).
