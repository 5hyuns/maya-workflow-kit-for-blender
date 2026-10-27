# Step 229 — Release prep 0.5.0

Steps 192–228 + PR #125 (@cnzim). 사용자 10-26 밤: 단계마다 미룬 검사를 여기서 한 번에 — 헤드리스 전체 (4.5 / 5.x), GUI 전체
(`ALLSET_GUI_FULL=1`), release_check 4.5.4 / 5.2.2, dogfood, look_compare; 실패는 그 파일만 `-k` 로 다시, 원인은 git bisect.

## 한 것

- origin/master 에 사용자가 올린 e09bbb0 (docs/strategy 를 공개 저장소에서 뺌) 와 로컬이 갈라져 있어 **merge** (911bc44, rebase 안 함:
  step 문서가 인용하는 커밋 해시 유지). 로컬 커밋 중 docs/strategy 를 바꾼 것 없음 → 새로 공개되는 전략 문서 없음.
- CHANGELOG `[0.5.0] — 2026-10-27` (Added 25 / Changed 10 / Fixed 9, PR #125 @cnzim), `docs/distribution/release_notes_0.5.0.md`.
