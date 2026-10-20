# Step 125 — 홍보 장면 모델 교체 · 이름 Maya Workflow Kit · README (사용자 지시 2026-10-20)

사용자 지시 요지: (A) 무료 모델 품질이 낮다 → Blender 커뮤니티가 공유한 고품질 자산 (공식 데모 파일, Blender Studio, Blend Swap
CC0/CC-BY, Poly Haven HDRI) 로 장면 교체, 라이선스를 파일마다 확인해 근거 기록, 모든 홍보 이미지·영상을 새 장면 + **Maya 그라디언트 뷰포트
배경** (자동 검사) 으로 다시 생성. (B) 제품 이름 = **Maya Workflow Kit** (스토어 표시 이름, Blender 없음), 저장소 = **Maya Workflow Kit for
Blender** (`https://github.com/5hyuns/maya-workflow-kit-for-blender`), 내부 id `allset` / 패키지 / 접두사 그대로; 상표 위험 메모; 마케팅
로고타입 재생성; GitHub README (Hermes 초안 반영); zip 이름 `maya-workflow-kit-<ver>.zip`.

## 계획 (병렬 레인, delegated)

| 레인 | 맡는 파일 | 내용 | 의존 |
|---|---|---|---|
| A1 자산 | `tools/marketing/assets.json`, `fetch_assets.py`, `docs/distribution/marketing/CREDITS.md`, `research/marketing_assets/` | 후보 조사 → 라이선스 직접 확인 (URL + 문구) → 받기 → 기능별 배정표 | 없음 |
| A0 촬영 규칙 | `tools/marketing/shots.py`, `clips.py`, `scene.py` (+ 새 `bg_check.py`) | 모든 3D View = Maya 그라디언트 (Alt+B 상태, Maya 테마) 고정, 찍은 뒤 뷰포트 위·아래 ΔE 검사 (단색 = FAIL), 템플릿 이름 변경 반영 | 없음 (최종 촬영은 A1 + B-code 뒤) |
| B-code 이름 | `src/**`, `tests/**`, `tools/*.py` (marketing 제외, `make_clips.py` / `make_marketing.py` 의 zip 줄 포함), `CLAUDE.md` | 보이는 「Allset」 → Maya Workflow Kit (manifest name, 환영 창, 환경설정, 스위치, 메뉴, 핫박스 가운데, notices, 템플릿 표시 이름), zip 이름, validate + 설치 왕복 | 없음 |
| B2 문서 | `docs/**` (step / HANDOFF / CREDITS 제외), `README.md`, 마케팅 md | 결정 12 갱신 + 상표 위험·대체 이름, 배포 문서, README (Hermes 초안) | 없음 |
| C 로고타입 | `tools/marketing/compose.py`, `kit.py`, `clip_compose.py`, `content.json`, `style.json` | 잠금업 = 「Maya Workflow Kit」 (Bold N, text-strong) + 「for Maya users, in Blender」 (SemiBold 0.66 N, teal) — 두 줄 / 한 줄 규칙은 step 124 그대로 | 없음 (최종 렌더는 새 원본 뒤) |
| 메인 | step 문서, HANDOFF, 병합, 최종 촬영 지시, 전체 테스트, 시각 확인, 커밋 | | |

순서가 필요한 것: 최종 촬영 (스크린샷·클립) 은 새 자산 (A1) 과 이름이 바뀐 빌드 (B-code: 화면 안 「Allset」 글자가 사라져야 함) 뒤 —
그 전 촬영은 버려진다. 최종 합성 (C) 은 새 원본 뒤.

결정 (delegated): 앱 템플릿 표시 이름도 제품 이름 (폴더 `Maya_Workflow_Kit` → Blender 가 「Maya Workflow Kit」 로 표시); 잠금업 문구
「for Maya users, in Blender」 = 지시의 「이름 바로 뒤 첫 문장 맥락」; 「Maya」 를 따로 강조색으로 칠하지 않음 (상표: 제품 이름 일부로 강조하지
않기).

순서가 필요했던 것 (한 줄): 최종 촬영은 자산 (A1) 과 이름이 바뀐 빌드 (B-code) 뒤 — 화면 안 글자 (환영 창, 핫박스 가운데) 가 새 이름이어야 함.

## 한 것

- **레인 A1 자산** (`tools/marketing/assets.json`, `fetch_assets.py --active`, `CREDITS.md`, `research/marketing_assets/INVENTORY_125.md`):
  Blender Studio Rain v3 리그 · Pack Bot 리그 · Security Bot 리그 (+ 배터리), Blender 4.5 스플래시 DOGWALK (CC BY 4.0, 페이지·.blend
  ReadMe 문구 기록), Cube Diorama · Poly Haven Studio Small 09 HDRI (CC0). 제외: Classroom (STAEDTLER 등 실제 상표), Barcelona
  Pavilion (실존 건축·가구 디자인), BY-SA 전부 (홍보물이 BY-SA 가 될 위험, 보수적), 라이선스 표기 없는 데모, 로그인/구독 자료, Blend Swap
  (직접 다운로드 아님). 옛 Kenney / Quaternius / Poly Haven 소품은 `superseded`. fetch 가 이미 풀린 파일은 다시 풀지 않음 (Windows 폰트
  잠금 충돌 해결).
- **레인 A0 그라디언트 규칙** (`scene.py` `maya_look` + `GRADIENT_KEEPER` 타이머, `bg_check.py`): Maya 모드의 모든 3D View = Alt+B
  그라디언트 상태 (Maya 테마), 촬영마다 뷰포트 위·아래 색을 Lab 으로 재서 위 색이 Maya #889db3 와 ΔE00 ≤ 8, 위-아래 ΔE00 ≥ 20, 아래가
  더 어두움 — 아니면 FAIL (step 124 단색 원본 10 장 모두 FAIL 확인). 순수 Blender 화면 (switch_before, 스위치 클립의 Blender 구간) 은
  Blender 테마 그대로 두고 검사에서 제외 (delegated: 설치 직후 Blender 를 보여 주는 화면이라 Maya 그라디언트를 칠하면 사실과 다름).
  장면 레시피 전부 새 자산으로 (DOGWALK = 첫 화면·핫박스·스위치, Rain = 마킹 메뉴·메뉴·리깅·애니, Pack Bot = 컴포넌트·Modeling
  Toolkit·내비게이션, Security Bot + 배터리 = Channel Box·피벗·스냅·키).
- **레인 B-code 이름** (`src/allset/names.py` `PRODUCT`, `app_template.TEMPLATE_ID = "Maya_Workflow_Kit"` + 옛 「Allset」 템플릿 정리,
  `tools/build.py` `ext_zip()` → `dist/maya-workflow-kit-<ver>.zip`, 스플래시, 설치기, `tests/test_step125_name.py`): 보이는 글자 전부
  Maya Workflow Kit, 내부 id 그대로. 결정 (delegated): 핫박스 가운데 = 「Maya Workflow Kit」, manifest `website` 는 저장소가 공개될 때까지
  넣지 않음 (비공개 → 404), 기본 프로젝트 `Documents/Maya Workflow Kit/projects/default`.
- **레인 B2 문서**: 결정 12 개정 (사용자 결정, 상표 위험, 대체 이름 「Workflow Kit for Maya Users」), DISTRIBUTION / listing / audit /
  naming / compat_5x / marketing md / CHANGELOG, README.md 를 Hermes 초안으로 새로 씀 (링크 32 개 0 깨짐).
- **레인 C 로고타입** (`compose.lockup` 문자열을 `style.json` 으로, 레이아웃마다 N 재조정, 크레딧 필드, 상표 고지 작은 글씨를 키 비주얼 ·
  키트 카드 · 트레일러 끝 카드에 — delegated: 이름이 Maya 로 시작하므로 이미지 자체에도 고지).
- **메인 병합·검토**: 안 쓰이던 `tools/listing_shots.py` 삭제 (step 122 부터 아무도 부르지 않음, 단색 배경으로 찍던 옛 스크립트),
  keymap_mapping 재생성. 검토로 고친 것: Pack Bot 컷이 다리 하나만 확대 (편집 모드 경계 상자) → 로봇 전체 구도, 내비게이션 클립이
  DOGWALK 안에서 나무 속으로 들어가고 눈사람 리그가 클릭을 가져감 → Pack Bot (리그 숨김) + 작은 드래그, 피벗 스냅 검사가 Bevel 전
  메시 꼭짓점과 비교 → 평가된 메시, 리깅 클립 끝 Paint Skin Weights 가 무게 없는 끝 관절 (전부 파랑) → 무게가 가장 많은 영향.

## 검증

- 헤드리스 전체 894/894 (이름 변경 후, `tests/run.py --no-build`), `test_step125_name` 4/4. release_check exit 0 (`extension validate`
  Success on `dist/maya-workflow-kit-0.2.0.zip`, 깨끗한 설정 설치 → 켜기 → Maya → 끄기 → 제거 = 남는 파일 0), repo_check 11/11,
  installer_check 9/9, GUI `-k` hotbox / welcome / switch / layout / first-screen 47/47 (B-code 레인). 마무리 재확인: 아래 「마무리」.
- 촬영: make_marketing 모든 PASS (뷰포트 그라디언트 검사 포함, 순수 Blender 화면 1 장 제외), make_clips 7 개 녹화 + 합성: 클립 5.6–7.6 s
  2.6–4.5 MB, GIF ≤ 3.99 MB, 트레일러 33.5 s 12.7 MB, 가장 긴 정적 구간 ≤ 0.8 s (클립) / 0.3 s (트레일러). 클립 그라디언트 검사 = Maya 모드
  프레임 전부.
- 직접 본 것: 원본 스크린샷 시트, 정지 이미지 10 + 키 비주얼 2 + 키트 6 시트, 클립 7 개 + 트레일러 2 fps 타일, 피벗 클립 끝 프레임,
  키 비주얼 원본 크기.

## 남은 것

- **pivot_snap 클립 재녹화가 불안정** (Hermes 지시로 중단): 배포본 `clips/05_pivot_snap.mp4` 와 트레일러는 회전까지 된 15:53 녹화본
  (끝 프레임 확인: 배터리가 새 피벗 둘레로 돎). 그 뒤 다시 녹화하면 E 회전 드래그가 링을 못 잡아 상자 선택이 됨 (카메라 70° 에서 Z 링이
  거의 납작한 타원, 링 반지름 상수 RING_PX 가 이 세션에서 실제의 약 절반) — 코드는 그 녹화 때 상태로 되돌렸고, 검사는 평가된 메시 ·
  인스턴스 꼭짓점 · 월드 회전으로 고쳐 둠. V 스냅은 덮개 기계 부품 꼭짓점에서 2.7 mm (원인 미확정, 허용 5 mm). 다음에 클립을 다시 찍을 땐
  회전 드래그를 링 픽셀 측정으로 잡거나 카메라를 낮출 것.
- 키 비주얼의 기울인 화면이 가로로 늘어남 = step 126.
- 내비게이션 클립 크레딧은 Pack Bot 으로 바꿈 (재녹화 후); 03 Channel Box 캡션 「keyed channels in red」 vs AE 초록 (step 124 남은 것).
- 5.x 버전에서는 이름 변경 후 다시 돌리지 않음 (compat_5x.md 에 날짜와 함께 표시).
- manual_checks 「Step 125」 (B2): 설치 뒤 보이는 이름, 옛 Allset 템플릿과 두 개 안 생기는지, GitHub README 렌더링, 스토어 이름 재검색.
