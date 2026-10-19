# Step 121 — 인기 애드온 등록 페이지 레퍼런스 → 미디어 기준 (사용자 요청 2026-10-19)

사용자 요청: 「Blender 상위 애드온(인기 많은 것)을 레퍼런스 삼아서 가자. Blender 보면 움직이는 이미지도 들어가던데?」
결과 문서: `docs/distribution/marketing/references.md` (표·공식 규칙·우리 미디어 기준·다음 단계 지시). 원자료 (페이지 HTML,
파싱 JSON, ffprobe, 썸네일, 콜라주): `research/marketing_refs/` (추적 안 함 — 남의 이미지).

## 계획

1. 공식 규칙: extensions.blender.org 의 미디어 허용 형식·크기·개수 — 공개 문서, 없으면 사이트 소스.
2. 레퍼런스: extensions.blender.org 다운로드 상위 20 + 평점 상위 (상위 20 에 없는 것), Superhive 「Most Sales」 10, Maya 전환·
   마킹 메뉴·키맵 경쟁 제품. 각 페이지의 미디어 구성을 HTML 에서 직접 셈 (영상은 ffprobe / YouTube 길이), 이미지 글자·첫 장은 눈으로.
3. 공통 패턴 → 우리 미디어 기준, 다음 두 단계 지시.
4. `listing.md` 의 「no GIF」 표현을 사실대로.

일반 서브에이전트 2 개가 병렬로 (extensions + 공식 규칙 / Superhive + 경쟁), 각 행에 URL. 숫자는 저장된 HTML·소스에서 다시 확인 (공식 규칙
인용문을 저장한 폼 소스에서 grep).

## 한 것

- **공식 규칙** (공개 문서에는 없음 → 사이트 소스 `infrastructure/extensions-website` main @ 8415711 의 업로드 폼): 미리보기 칸마다
  「A JPEG, PNG or WebP image, or an MP4 video」 (GIF·WebM 불가), 16:9, 최소 1 개, 개수·크기 제한 코드에 없음, 캡션 255 자, 영상의
  포스터 = 0.01 초 프레임; 대표 이미지 ≥ 1920 × 1080 16:9 (= og:image); 아이콘 256 PNG; 태그라인 64 자. 모더레이션 가이드: 설명 본문에
  무거운 GIF 금지.
- **사실 정정**: 「no GIF」 → 미리보기에 MP4 가능, GIF 는 설명 본문의 외부 링크로만 (3/27 사례). 사전 단서 확인: ucupaint 영상 6 (+ 이미지 4),
  simple-deform-helper 영상 11 (단서의 10 이 아님), references-overlays 설명에 GIF 5.
- **표** (references.md §2–§4): extensions 27 개 (다운로드 상위 20 + 평점 상위 6 + references-overlays), Superhive 베스트셀러 10, 경쟁 11
  (Maya Config Pro / Lite / Addon (Gumroad) / Pro (Gumroad), Maya Shelf & Navigation, Pie Menu Editor, MARKING MENUS, Keymapper, EMC Tools,
  Origin Move like Maya, Maya Pivot).
- **패턴**: 다운로드 상위는 대부분 예전 기본 애드온 (20 중 9 는 미디어 없음) → 기준은 평점 상위 제3자 목록. 평점 상위 6 중 5 가 영상, 영상 길이
  중앙값 26.6 초, 미리보기 최대 11; Superhive 9/10 이 2 번째 칸에 영상, 대표 이미지는 이름 + 한 줄 (문단 0/10), 갤러리 중앙값 10; 이미지 속
  글자는 제목 또는 한 문장, 설명은 캡션에. 경쟁 5/10 이 Maya 비슷한 「M」 로고.
- **우리 미디어 기준 (delegated, §5)**: 대표 이미지 = 실제 Allset 화면 + 이름 + 한 줄 (M 로고·Maya 화면 없음); 갤러리 10 = 트레일러 MP4
  30–45 초 (첫 프레임 = 제목 카드) + 기능 클립 6 개 6–15 초 + 제목 붙은 정지 이미지 3 장, 모두 1920 × 1080, 모든 항목 캡션; 이미지 속 영어 =
  제목 ≤ 6 단어 + 한 줄 ≤ 12 단어; extensions 설명에는 GIF 안 넣음 (GIF 는 README·SNS 용, 123 단계); 장면은 모두 킷이 만든 것 (출처 표기
  불필요), 배경은 Maya 팩토리 #5c5c5c.
- **다음 단계 지시** (§6): 122 = copy.md / style.md, 대표 이미지·정지 이미지 3 장, listing C 갱신; 123 = 클립 6 + 트레일러 (이벤트 시뮬레이션
  녹화, ffmpeg H.264), 크기·첫 프레임 확인, README 용 GIF, kit 폴더. 중단된 stash 코드는 참고만.
- `listing.md`: 파트 C 제목의 「no GIF」 삭제 + 상점 규칙 단락 (출처 references.md §1) + 0.2.0 세트 / 목표 세트 구분. 덤 (delegated): 파일
  중간에 남아 있던 **옛 사본** (B 뒷부분 + C + D, `blender_version_max = "5.0.0"` 의 step 117 문구) 삭제 — 지금 판과 모순.

## 검증

- 공식 규칙 인용문을 저장된 폼 소스·가이드 HTML 에서 grep 으로 확인 (`or an MP4 video`, `at least 1920 x 1080`, `heavy image`).
- 콜라주 3 장 (`research/marketing_refs/collage_*.png`) 을 직접 보고 표의 대표 이미지 분류와 맞는지 확인.
- 문서를 읽는 헤드리스 테스트: step114 4 / 4, step117 · step61 등 14 / 14. 코드 변경 없음 → GUI 전체는 돌리지 않음.

## 남은 것

- 웹 서버 자체의 업로드 크기 제한은 소스에 없음 (unknown) — 첫 업로드 때 확인 (기준은 클립 ≤ 8 MB, 트레일러 ≤ 20 MB 로 넉넉히 작게).
- Superhive 판매 수는 「N+」 반올림, Gumroad 는 판매 수 비공개.
- 실제 카피·이미지·영상은 122 / 123 단계.
