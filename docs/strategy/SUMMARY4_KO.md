# 요약 4 — Maya에서 많이 쓰는 기능과 키트 상태 (2026-10-26)

자세한 표: `FEATURES.md` (125행, 영역별, 근거 id 포함) · 구현 목록: `TOP40.md` · 원자료: `data/web/features4_sources_a.md` (A0–A21), `data/web/features4_sources_b.md` (B1–B56), `data/menu_status_4.tsv` (메뉴 항목별 키트 상태), `data/menu_count_4.txt`.

## 근거 출처 종류 (78개)
- **Autodesk 공식 12개**: 기본 셸프(Maya 2022), Certified User 시험 목표(2020)와 Certified Professional 로드맵(2015), Maya Learning Channel, Quick Start, Realtime rigging 시리즈, Game Exporter 도움말, 공식 단축키 페이지.
- **교육 과정 12개**: LinkedIn Learning, Udemy, CGMA, AnimSchool, Gnomon, Animation Mentor, Pluralsight, World of Level Design 등.
- **게임 파이프라인 13개**와 **채용·직무 5개**: Unreal·Unity 문서, 내보내기 가이드, Bungie·Keywords 등의 공고.
- **커뮤니티 27개**와 **치트시트 3개**: Reddit, Polycount, BlenderArtists, YouTube.
- **한계** [사실]: Autodesk는 "가장 많이 쓰는 툴" 순위를 공개하지 않았다. 사용 데이터를 수집한다는 도움말만 있다. 그래서 빈도는 "그 기능을 다룬 독립 출처 수"로 대신했다(A ≥ 6, B 3–5, C 1–2, 1개면 추정). Reddit은 본문이 차단되어 스니펫만 썼다. 대학 강의계획서는 확인하지 못했다.

## 영역별 상위 5개 (근거 수)
| 영역 | 상위 5 |
|---|---|
| 0 손 | Outliner 9 · 피벗 D/Insert·Center Pivot 9 · Q/W/E/R + 매니퓰레이터 8 · Attribute Editor 8 · Group/Parent 8 |
| 1 모델링+UV | Freeze Transformations 9 · Delete History 8 · Extrude 7 · Multi-Cut 7 · Quad Draw 7 (UV는 UV Editor 7, 나머지 4) |
| 2 리깅+스킨 | **Paint Skin Weights 14** · Bind Skin 13 · Create Joints 11 · Constraints 11 · IK Handle 10 |
| 3 엔진 내보내기 | FBX Export All/Selection 7 · LOD 5 · 단위·루트·이름 4 · Bake Animation 3 · Game Exporter 3 |
| 4 애니 | Graph Editor 11 · Time Editor/클립 7 · Set Key 6 · Motion Path/Trail 6 · Time Slider 5 |

근거가 가장 많은 기능은 리깅·스킨 쪽에 몰려 있다. DIRECTION의 "영역 2 깊게"와 맞는다 [해석].

## 핵심 발견
- **많이 쓰는 기능의 메뉴는 이미 거의 다 동작한다** [사실: 표 집계]. A·B 등급 90행은 동작 64, 부분 24, 회색 2, 없음 0이다. 메뉴 동작률을 더 올리는 일은 이 우선순위와 거의 상관이 없다.
- **공백은 단계 사이의 연결에 몰려 있다** [사실: `docs/first_hour.md`]:
  - 모델 → UV: UV Editor가 새 창으로 열리면서 편집 모드로 바뀌고, 그 상태에서는 투영이 아무 일도 하지 않는다.
  - 리그 → 웨이트: Q를 눌러도 Paint Skin Weights가 끝나지 않는다.
  - 리그 → 엔진: 스킨 리그 FBX가 BLOCKED다. Maya에서 열면 rotate −90 / scale 100이 붙어 있다.
  - Game Exporter: Blender 기본 FBX 창이 그대로 열린다.
  - 개념: Translate Y가 위가 아니다.

## Top 40 중 상위 15
1. Rotate 매니퓰레이터를 Maya 것으로 (0, A, L)
2. 자주 쓰는 명령의 옵션 박스를 Maya 창으로 (0, B, M)
3. Translate Y = 위 표시: Maya 축 이름 표시와 안내 (0, B 추정, M)
4. Undo 깊이 256 안내 버튼 (0, B, S)
5. UV Editor를 패널로 열고 오브젝트 모드 유지 (1, A, M)
6. Quad Draw 남은 3가지, 이슈 #89 (1, A, M)
7. LOD Group / Generate LOD Meshes (1, B, 회색, M)
8. 면 선택이 없으면 UV 투영을 오브젝트 전체에 (1, B, S)
9. Unfold 결과를 mayapy와 비교 측정 (1, B, M)
10. Paint Skin Weights: Q/W/E/R로 페인트 끝내기 (2, A, S)
11. Paint Skin Weights: B+드래그로 브러시 크기 (2, A, S)
12. Paint Skin Weights: 뷰에서 조인트로 영향 고르기, 먼저 확인 (2, A, S)
13. Set Blend Shape Target Weight Keys (2, A, 회색, S)
14. Shape Editor 메뉴 중 게임에 쓰는 것 (2, A, M)
15. IK/FK 전환 키 (2, B, 회색, M)

그다음 순서는 #19 스킨 리그 FBX 내보내기(L), #20 게임 내보내기 전 검사, #23 스킨 메시 FBX 가져오기, #24 Game Exporter 창이다. 영역 순서상 15위 밖이지만, "에셋이 끝났다"의 정의라 웨이트 손(#10–12) 바로 뒤에 붙이기를 권한다 [해석]. 40개 중 31개는 구현 작업이다. 나머지 9개(V)는 "동작하지만 사람 손으로 확인한 적 없는 A 등급 기능"의 녹화·측정 작업이다.

## 키트가 이미 잘하는 것 [사실: 저장소]
- **모델링 핵심**: Extrude, Bevel, Multi-Cut, Merge, Delete History. first_hour 모델 단계는 10/10 OK이고, 결과가 mayapy와 일치한다.
- **리깅·스킨 메뉴**: Rigging 메뉴 86 %. Bind Skin은 Maya closest distance 가중치를 mayapy와 일치하게 낸다. Component Editor, Mirror / Copy Skin Weights, 가중치 Export / Import, Set Driven Key, 컨스트레인트, IK도 동작한다.
- **손의 바닥**: Channel Box(`+=`, 채널 드래그, RMB Channels), Hotbox, 마킹 메뉴(Maya 측정 반경), 셸프, 홀드 키(X/C/V, D, B), Maya 기본 핫키 210개 구현.
- **UV**: UV 메뉴 95 %, UV Editor 85 %. Cut/Sew, Layout, Texel Density, UV Sets, Checker를 지원한다.
- **애니메이션 메뉴**: Graph Editor 82 %, Dope Sheet 87 %, Set Key, Playblast, Motion Trail, Ghosting.
- **메시 FBX**: cm, Y-up, 크기, 위치가 Maya와 같다. 단 스킨 리그는 아니다.

DONE
