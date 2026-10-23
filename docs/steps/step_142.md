# Step 142 — UI 모습 · 맞춤 (#78 #77 #76 #54 #41)

## 계획

| 순서 | 레인 | 이슈 | 파일 |
|---|---|---|---|
| 1 | UI (worktree, 포그라운드) | #78 dock 폭 (Maya 처럼 Channel Box 탭일 때 좁게), #77 UI 1.5 배율 1600 px 창의 메뉴 막대 넘침 · Set Driven Key 버튼, #76 매니퓰레이터 축 색 · 선택 안 된 와이어 색 | `ui/maya_dock.py`, `ui/toolbox.py`, `ui/status_line.py`, `ui/set_driven_key.py`, `ui/manipulator.py`, `ui/selection_wire.py`, 관련 테스트 |
| 1 | ICONS (worktree, 포그라운드) | #54 남은 메뉴 아이콘 (Deform, Mesh Display, Effects / Fields, Edit Mesh / Mesh Tools) | `ui/menu_icons.py`, `ui/menu_icon_data.py`, `tools/gen_menu_icons.py`, 아이콘 그림 모듈, `tests/test_step131_icons.py` 계열 |
| 2 | MEDIA (포그라운드, 1 뒤) | #41 테마 없이 스토어 미디어 · 홍보 샷 · docs/screenshots 다시 찍기 (생성기에서 테마 적용 제거) | `tools/marketing/*`, `tools/release_shots.py`, `docs/distribution/media/`, `docs/distribution/marketing/`, `docs/screenshots/`, `site/media/` |

순서가 필요한 것: MEDIA 는 UI 레인의 새 모습 (dock 폭, 매니퓰레이터 색) 을 찍어야 해서 1 뒤. 부하 제한: 동시에 레인 2 개, Blender 2 개.
테스트 규칙: 기능 테스트 먼저 (사용자 지시 "Tests first") + 헤드리스 전체 + 바뀐 모듈 GUI 만. 새로 찾은 문제는 즉시 GitHub 이슈.
