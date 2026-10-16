# HANDOFF

## 현재 작업

- Step 12 (M5 셸프) 완료 — `docs/steps/step_12.md`. 헤드리스 185/185, GUI 115/115.
- Maya 띠: 표식 있는 얇은 Image Editor (헤더 = Status Line, 툴 헤더 = Shelf), App Template 에 포함, 다른 레이아웃은 Windows > UI Elements > Shelf.
- `ui/shelf.py` (버튼·탭·사용자 셸프 `shelves.json`·띠), `ui/shelf_data.py` (생성: `tools/gen_shelf_data.py`), `ui/shelf_map.py` (동작·내장 아이콘).
- Step 11 = `4f2ac87` (Outliner/AE), Step 10 = `86f3c29`.

## 바로 다음 할 일

- **Step 13 — 통합·배포** (사용자 번호): 전체 헤드리스 테스트, 익스텐션 zip 빌드 + `blender --command extension validate`, 깨끗한 샌드박스 설정에
  설치 → 활성화 → App Template 설치 → GUI 스크린샷 세트(`docs/screenshots/`), README.md (한국어+영어: 설치, 기능, 한계).
  - 재료: 각 step 문서 「결정」「남은 것」, `docs/keymap_mapping.md`, `docs/manual_checks.md`, GUI 테스트 `--shots`.
- 미뤄진 것: 메뉴셋 F2–F6 키, Range Slider·타임라인·`.` `,` 키, Status Line 입력 라인, 마킹메뉴 편집기, Step 10–12 「남은 것」.
