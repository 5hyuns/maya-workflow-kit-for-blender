# Step 132 — Release prep 0.2.1

## 계획

사용자 지시: 0.2.1 출시 준비 — manifest 0.2.1, CHANGELOG (고친 이슈 번호 · 한 줄 설명, 사용자 보고 감사), README / site 버전,
`tools/build.py` → `dist/maya-workflow-kit-0.2.1.zip`, `extension validate`, release_check 전체 (깨끗한 설치 → 활성화 → opt-in →
비활성화 → 제거 잔여 0), 헤드리스 · GUI 전체 숫자, 4.5 와 5.x 하나 이상에서 설치 왕복, 커밋 · push 후 `gh release create v0.2.1 --draft`
(zip 2 개, 노트 = CHANGELOG 0.2.1 + 설치법 + 상표 고지), 고친 이슈 닫힘 확인, 남은 이슈 → 마일스톤 0.3.0, 스토어용 릴리스 노트
`docs/distribution/release_notes_0.2.1.md`. 스토어 업로드와 초안 publish 는 사용자가 한다.

### 0.2.1 에 넣을 이슈 (delegated)

HANDOFF 는 출시 전에 #53 #52 #44 #41 을 고치기로 했다.

- **#44** (Ctrl+N 이 Blender 기본 파일을 엶) · **#52** (1.25 배율에서 패널 툴바가 잘림) · **#53** (1.25 배율에서 첫 영역 분할 때 레이아웃이
  다시 맞춰짐): Windows 125 % 사용자가 바로 보는 회귀 (step 130 의 밀도 프리셋 · 앱 템플릿 제거 뒤) → 0.2.1 에서 고침. 레인 3 개 (worktree).
- **#41** (스토어 미디어 · 마케팅 생성기가 없어진 테마를 씀): 스크린샷 · 클립 전부 다시 찍는 큰 일이고 zip 과 무관 (미디어는 따로 올림) →
  **0.3.0 으로 미룸**. 그때까지 스토어 미디어는 0.2.0 것을 쓰지 않도록 사용자 할 일에 적는다.

### 레인

| 레인 | 할 일 | 순서 |
|---|---|---|
| FIX44 / FIX52 / FIX53 | 각 이슈 수정 + 테스트 (worktree) | 바로, 병렬 |
| 메인 | 버전 · CHANGELOG · README · 릴리스 노트 · 이슈 정리 | 바로 |
| 메인 | 병합 → 빌드 · validate · 헤드리스 전체 · GUI 전체 (한 번) · release_check 4.5 + 5.2.2 · 초안 릴리스 | 병합 뒤 (같은 zip 을 검증해야 해서 순차) |

release_check 의 스크린샷은 `tmp/` 로 (docs/screenshots 는 #41 에서 테마 없이 다시 찍는다, delegated).

## 한 것

- **0.2.1 에 고친 이슈 (레인 3 개, worktree → 병합)**:
  - #44 (`step_132_fix44.md`): Maya 모드 Ctrl+N = `allset.new_maya_scene` (IC Window Ctrl+N `wm.read_homefile` 제거, Text 의 Ctrl+N 은
    그대로 = shadows), mapping 행 IC → KIT, `docs/keymap_mapping.md` 재생성.
  - #53 (`step_132_fix53.md`): 원인은 Blender 가 아니라 킷의 `toolbox.fit_columns` 가 늦게 (첫 영역 분할 뒤) 움직인 것 — 화면을 불러온
    그대로일 때만 맞추고 영역 집합이 바뀌면 멈춤.
  - #52 (`step_132_fix52.md`): 패널 툴바가 헤더 폭에 맞춰 그룹 단위로 접히고 나머지는 Maya 식 » 팝오버 (`ui/toolbar_fit.py`, 폭 규칙은
    1.0 / 1.25 / 1.5 에서 측정).
- **버전 · 문서**: manifest 0.2.1, `CHANGELOG.md` 0.2.1 (스토어 심사 변경 #40 #42 #43 #46 #51, 사용자 보고 #1–#14 #22 #23 #25 #27 #28
  #36 #37 #38 + 감사, 자체 점검 #15 #17–#21 #24 #26 #29 #39 #45 #47–#50, 출시 전 #44 #52 #53), README 설치 절에 0.2.1 + GitHub Releases
  링크, `docs/distribution/listing.md` zip 이름, 스토어 릴리스 노트 `docs/distribution/release_notes_0.2.1.md`. site 는 버전을 쓰지 않고
  Releases 로 연결하므로 그대로.
- **출시 도구**: release_check 의 오래된 기대 2 개 (opt-in 이 앱 템플릿을 쓴다, `allset.layout_install`) 를 step 130 동작으로 고침 —
  템플릿을 쓰지 않음을 확인하고, 촬영은 번들 `startup.blend` (`first_start.new_maya_scene`) 로 연다. release_check 스크린샷은 `tmp/`
  로 (docs/screenshots 는 #41 에서, delegated). `test_step34_menus` 의 가짜 layout 이 step 131 의 메뉴 `icon_value` 인자를 받게 함.
- **이슈 정리**: #41 → 0.3.0 (코멘트), #54 (step 131 후속) 0.3.0. 0.2.1 마일스톤의 나머지 (#44 #52 #53) 는 이 커밋의 `Fixes` 로 닫힘.

## 검증

- `python tools/build.py` → `dist/maya-workflow-kit-0.2.1.zip` (2 275 687 B) + `-legacy.zip`.
- `python tools/release_check.py` (Blender 4.5.4): validate PASS, install + enable PASS, 검사 22/22 PASS — 사용자 설정 보존, 끄기 · 제거 후
  복원, 깨끗한 설정에서 설치 → 활성화 → opt-in → 비활성화 → 제거 후 킷 파일 0 개, GUI 첫 시작 8 개, 스크린샷 7 장 (`tmp/release132_shots/`,
  01_layout 직접 봄).
- `python tools/release_check.py --blender <5.2.2> --no-shots`: validate PASS, 14/14 PASS (같은 왕복, 잔여 0).
- 헤드리스 전체 `python tests/run.py --no-build`: **1025 passed, 0 failed** (127 파일).
- GUI 전체 `python tests/gui/run.py --no-build` (실효 배율 1.25): **1302 passed, 0 failed** (111 파일) — step 130 · 131 의 남은 1 건 (#53) 도 통과.
- 레인별: #44 헤드리스 39 + GUI 2, #53 GUI 65 (1.25) + 65 (1.0) + 헤드리스 29, #52 헤드리스 40 + GUI 51 (1.25) + 51 (1.0) + 36 (1.5).

## 남은 것 (사용자 할 일 포함)

- **사용자**: extensions.blender.org 에 `dist/maya-workflow-kit-0.2.1.zip` 업로드 (릴리스 노트 = `docs/distribution/release_notes_0.2.1.md`),
  GitHub 의 v0.2.1 초안 릴리스 확인 후 publish. 스토어 미디어는 0.2.0 의 테마 화면 그대로 — #41 (0.3.0) 에서 다시 찍는다.
- 0.3.0: #16 #30–#35 (Maya 옵션 창 · 도구), #41 (미디어), #54 (남은 메뉴 · Outliner 아이콘).
- #52 의 폭 규칙은 4.5 에서만 측정 (5.x 재측정 안 함).
