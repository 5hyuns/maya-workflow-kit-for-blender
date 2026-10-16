# HANDOFF

## 현재 작업

- Step 5 (M2-a 레이아웃 App Template + Maya 테마) 완료 — `docs/steps/step_5.md`. 헤드리스 61/61, GUI 47/47.
- 레이아웃: `tools/make_startup.py` → `src/maya_kit/app_template/MayaKit/startup.blend` (워크스페이스 "General"). 테마: `tools/make_theme.py` → `src/maya_kit/theme/maya.xml`. 둘 다 생성기로만 수정.
- Channel Box 자리는 General 화면 3D 뷰의 **사이드바**(N 패널, 이미 표시됨).

## 바로 다음 할 일

- **Step 6 — M2-b Channel Box** (`docs/PLAN.md` #6).
  - 근거: `research/maya/channel_box.md` (구성 §1, 표시 4개 섹션 §2.1, 채널 선택 §2.2, MMB 가상 슬라이더 §2.3, Channels 메뉴 §2.4, Edit 메뉴 §2.5, 필드 편집 §2.6, Layer Editor §3, Blender 대응 §4), `research/blender/api_limits.md` #1/1a/1b/1c.
  - 3D 뷰 사이드바 카테고리 "Channel Box": 선택 객체의 Translate/Rotate/Scale XYZ + Visibility (+ 커스텀 속성), SHAPES(데이터), INPUTS(모디파이어 = history) 섹션; 다중 선택 일괄 편집 (Maya 는 선택 전체에 적용); 채널 이름 클릭 선택 → 뷰포트 MMB 드래그 가상 슬라이더 (MMB 는 IC 툴 키맵의 MMB 이동과 충돌 — 우선순위 확인, `industry_compatible_vs_maya.md` §1 "MMB-drag anywhere").
  - 템플릿의 사이드바가 Channel Box 탭을 열도록 make_startup 갱신 고려 (영역의 활성 카테고리 설정 가능 여부 확인).
  - MMB 모달·다중 편집 설계 → 먼저 `docs/steps/step_6.md` 「계획」. GUI 검증은 `tests/gui/gui_step6_*.py`.
