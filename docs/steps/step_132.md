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
