# Step 117 — Distribution prep 4: listing package and final validation

사용자 지시 (10-19): extensions.blender.org 제출물 준비 (업로드는 사용자가 직접 — 하지 않음). 등록 설명은 첫 문장부터
「키맵이 아니라 Maya 워크플로우 전체」, 기능을 워크플로우 묶음 (Navigate & Select / Hotbox & Marking Menus / Channel Box &
Attribute Editor / Menu Sets & Shelves / Maya concepts / Option windows) 으로, 스크린샷도 묶음별로. 검증: validate, moderation
ruff, 깨끗한 설정에서 설치 → 활성화 → opt-in → 비활성화 → 제거 후 남는 파일 0, `extensions_audit.md` 요건마다 최종 상태.
version 0.2.0, CHANGELOG, 최종 zip, 커밋.

## 한 것

- **`docs/distribution/listing.md`** 재구성: A 폼 필드 (이름, tagline, 짧은 설명, 태그, 라이선스, 지원 버전, 권한, 아이콘·대표
  이미지·미리보기 파일), B 긴 설명 (영어, 그대로 붙여 넣는 Markdown: 첫 문장 "Not just a Maya keymap: …", 6 묶음, 켤 때 바뀌는
  것 = opt-in 전에는 없음, 되돌리는 법, 확장 밖에 쓰는 경로, `exec` / `bpy.utils.execfile` / `ctypes` 이유, 한계, 상표 고지문),
  C 미디어 표 (캡션·업로드 순서), D 심사자용 기술 고지 (step 115 문단 + 버전 실측).
- **미디어** `docs/distribution/media/` (`python tools/make_listing_media.py`):
  - `icon.png` 256 × 256, `featured.png` 1920 × 1080 — `tools/make_splash.py --media` (킷 자체 그림, Workbench 렌더: 회색 패널,
    Maya 선택 색의 와이어 큐브 3개, 이름·tagline·"not just a keymap" 줄, 하단 상표 고지). `--media` 는 배포되는 스플래시 PNG 를
    다시 쓰지 않는다 (다시 렌더하면 바이트가 바뀜).
  - 스크린샷 6장 1600 × 900 — `tools/listing_shots.py` (GUI, 깨끗한 샌드박스 `tmp/listing_env` 에 빌드한 zip 설치, Maya 테마는
    Make Blender feel like Maya 처럼 적용, 툴팁·인뷰 메시지 끔): 1 컴포넌트 선택 + Move 매니퓰레이터, 2 핫박스, 3 탭 스택을
    나눠 Attribute Editor 위 / Channel Box 아래 (키 채널 빨강, SHAPES), 4 Rigging 메뉴셋 + Skeleton 메뉴 + Rigging 셸프,
    5 Outliner group1 / 셰이프 + Freeze 된 pSphere1 + Modify 메뉴 (Freeze Transformations 행), 6 Duplicate Special Options.
  - ToS 2.2 (미리보기에 Blender 로고 금지): 상단 막대 왼쪽 Blender 메뉴 아이콘을 찍은 뒤 막대 색으로 덮는다 (`hide_logo`,
    Blender 동봉 numpy 로 픽셀 수정). Maya 화면·로고 없음, GIF 없음.
- **manifest**: version 0.2.0, tags + Rigging, `files` 권한 사유 "Layout template, settings backup, shelves, Maya project
  folders" (63 자 — 프로젝트 폴더 쓰기가 사유에 없었음), **지원 범위 4.2.0–5.2.x → 4.5.0–4.5.x** (`blender_version_min` 4.5.0,
  `blender_version_max` 5.0.0; 아래 검증: 4.2.23 25 실패, 5.0.1 / 5.1.2 / 5.2.2 19 / 20 / 23 실패; delegated — 반쯤 되는 킷보다
  「호환 안 됨」 표시가 낫다). README / DISTRIBUTION / CLAUDE.md / test_step53 맞춤, `.ruff_cache/` 빌드 제외. 설치기 예시 zip 이름 0.2.0.
- **ruff** (moderation guidelines 의 명령 그대로, `src/allset` 에서): 지적 10 건 수정 — 안 쓰는 import 6 (`cmds_shim` 은
  runner 가 필요할 때 import, `hypershade` 의 `NODES`, `attribute_editor` 의 `CATEGORY`, `modeling_toolkit` 의 `chrome`,
  `view_furniture` 의 `Quaternion`, `menu_items.world_bounds` 의 중복 `Vector`), 안 쓰는 변수 1, placeholder 없는 f-string 1,
  `maya_patches.apply` 의 루프 변수가 `patch` 모듈을 가리던 것 1.
- **`tools/release_check.py leftover_check`** (새 샌드박스 `tmp/release_env_clean`): 빈 설정에서 Blender 한 번 → 파일 목록 →
  install-file --enable → `welcome.opt_in` (Make Blender Maya, 템플릿·확장 사용자 폴더 생김 확인) → disable → 실행 중
  Remove (`extensions.package_uninstall`) → 새로 생긴 파일 중 Blender 자신의 것 (`config/userpref.blend`, `extensions/.cache`,
  관리 저장소 index) 을 뺀 것이 0 개여야 PASS.
- `docs/distribution/extensions_audit.md` 「최종 상태」 표: 요건 26 개마다 OK / 설명함 + 근거 (테스트·파일).
- CHANGELOG `[0.2.0]` (steps 14–117 을 워크플로우 묶음으로), `docs/manual_checks.md` step 117 (업로드 폼 확인).

## 판단 (delegated)

- 지원 범위 4.5.x: 지시는 「지원 버전」 표기. 실측 없이 4.2–5.2 를 적어 두는 것은 No surprises (ToS 3.1) 위반 위험 →
  Blender 4.2.23 LTS 를 받아 (`tmp/blender42/`, sha256 확인) 헤드리스 전체: 25 실패 → min 4.5.0. 5.x 는 step 53 (414 테스트) 뒤로
  다시 잰 적이 없었다: 5.0.1 19, 5.1.2 20, 5.2.2 23 실패 (step53 의 범위 테스트는 실행 중에 고쳐서 셈에서 뺌) — 원인은 Blender 5.0 의
  layered action (`Action.fcurves` 없음: Graph Editor 탄젠트 / 키 / SDK / Time Slider 틱), 템플릿 도크 역할 (Allset 레이아웃의 탭
  스택), 5.x 키맵 / UV / Target Weld 차이 → max 5.0.0. 5.x 호환은 다음 단계 후보 (측정하려면 max 를 잠시 올려 설치).
- ruff 버전: 지금 최신 ruff 0.17 은 기본 규칙이 넓어져 (RUF012, BLE001 등 스타일) 수정 뒤 647 건. 지침의 명령은 규칙을 지정하지 않으므로
  오랜 기본 규칙 (E4/E7/E9/F) 의 ruff 0.8.6 으로 0 건을 맞췄다 (실제 오류인 F 계열은 둘 다 같음: 0.17 에서도 F 는 0).
  저장소의 tests/ · tools/ 는 제출 zip 에 없어 손대지 않음 (지적 40 건, 남은 것).
- 미리보기 크기: 플랫폼 업로드 폼의 정확한 픽셀 요구는 공개 문서에서 확인하지 못함 [U] — 아이콘 256 정사각, 대표 16:9 1920 ×
  1080, 스크린샷 16:9 1600 × 900 으로 만들고 manual_checks 에 업로드 때 확인 항목.
- 3 번 스크린샷은 Maya 기본 (한 탭 스택) 이 아니라 스택을 위아래로 나눈 배치 — CB 와 AE 를 한 장에 보이려고. Maya 도 패널을
  나란히 도킹할 수 있다.

## 검증

- ruff 0.8.6 (지침 명령, `src/allset`): 10 → "All checks passed!".
- leftover_check 단독 실행: PASS 3/3 (opt-in 이 템플릿·사용자 폴더를 만듦, 실행 중 Remove, 남는 킷 파일 0 — 남은 것은
  `config/userpref.blend`, `extensions/.cache/compat.dat` 뿐).
- make_listing_media: listing_shots 체크 6/6 PASS, 8 장 생성, 스크린샷 직접 확인 (로고 덮임, 툴팁 없음, 메뉴 위치).
- Blender 4.2.23: 헤드리스 844 / 869 (25 실패: 4.5 로 저장된 템플릿을 읽는 dock / layout, 4.3+ 브러시 에셋, FBX / OBJ 옵션,
  키맵 데이터 차이 등) → 최소 버전 4.5.0.
- Blender 4.5.4 헤드리스 전체: 868 / 869 → 실패 1 = `test_step114` 가 `src/allset/.ruff_cache/` (ruff 가 만든 캐시, zip 에도
  들어감) 를 잡음 → 캐시 삭제 + manifest `paths_exclude_pattern` 에 `.ruff_cache/` → step114 4/4, step53 7/7 재실행 통과
  (= 869 / 869), zip 에 캐시 없음 확인.
- Blender 5.0.1 850 / 869, 5.1.2 848 / 869, 5.2.2 845 / 869 (위 판단).
- `tools/release_check.py`: 24 / 24 PASS — `extension validate dist/allset-0.2.0.zip` "Success", 깨끗한 설치, 사용자 셋업 유지 / 복원,
  Remove 후 복원, leftover 0, 첫 시작·레이아웃 스크린샷 (`docs/screenshots/` 다시 찍힘).
- GUI 전체 (`tests/gui/run.py`, 커밋 직전 1 회): 1121 / 1121 (89 파일).

## 남은 것

- 업로드와 플랫폼 폼 확인 (사용자, `docs/manual_checks.md` step 117), 지원 URL (공개 저장소가 생기면).
- tests/ · tools/ 의 ruff 지적 40 건 (제출물 밖).
- **Blender 5.x 호환** (위 실패 목록: layered actions, 템플릿 도크 역할, 키맵 / UV / Target Weld) → 고친 뒤 max 를 올리고 0.2.x.
- 이전 단계의 열린 것: 툴바 떼기, `ui/outliner.py` 의 안 쓰는 행 목록, manual_checks 115 / 116.
