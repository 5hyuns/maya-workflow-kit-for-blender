# Step 61 — 배포 방식 조사·결정 (공개 안 함)

Request (user, verbatim, 2026-10-18): 「나중에 addon이나 exe 설치, 배포가 어떤 방식이 좋을지 고민해 봐라.」
범위: 조사·비교·준비만. 업로드·공개·결제 설정·실행 파일 서명은 하지 않는다.

## 한 것

- **조사** (웹, 일반 서브에이전트, 출처 URL 포함 → `docs/DISTRIBUTION.md`): extensions.blender.org ToS (2026-08-10 판)·심사 체크리스트·manifest
  규칙, 자체 저장소 (`server-generate`, 끌어 놓기 링크, `repo-add`), Superhive 수수료·12개월 지원 정책·토큰 저장소, Gumroad, Blender 의 GPL
  판매 입장, Inno Setup / NSIS, 코드 서명 2026 (하드웨어 키, 459일, Artifact Signing 개인 = 미국·캐나다), SmartScreen, Blender 재배포·상표,
  Autodesk 상표 지침, 경쟁 제품 배포 방식. 서브에이전트가 「CONFIG 폴더에 쓴다」 고 한 세 곳 (`switch.py:54`, `theme/__init__.py:31`,
  `ui/shelf.py:57`) 은 코드를 다시 보니 레거시 애드온 빌드의 대체 경로였다 (확장은 `extension_path_user`) — 문서에는 확인한 사실만.
- **`docs/DISTRIBUTION.md`**: (a)–(e) 비교 표 (설치 동작 수·업데이트·되돌리기·비용·법적 조건·경쟁 제품), 후보별 근거, 이름·상표, 추천 (delegated),
  준비물, 공개 전 체크리스트, 확인 못 한 것.
- **결정** (`docs/user_decisions.md` 11, delegated): 무료 GPL 핵심판 = 자체 저장소 먼저 → extensions.blender.org 제출, exe 선택 (초안만),
  유료는 별도 상품, 묶음 안 함. 사용자가 정할 것: 이름·id (Maya 상표), 무료/유료, 계정·공개 이메일, 바이너리 CC0, exe 서명.
- **manifest**: `tags` (플랫폼 목록에서), `copyright`. `extension validate` 통과.
- **`tools/build_repo.py`**: Blender 의 `server-generate --html` 로 `dist/repo/` (zip + index.json + index.html).
- **`tools/repo_check.py`**: 깨끗한 샌드박스 + 사용자 설정 시드에서 `file://` 저장소로 등록 → 설치·켜기 → Make Blender Maya → 끄기 → 켜기 →
  다음 버전 게시·업데이트 → Maya 모드에서 Remove → 저장소 제거, 각 지점에서 사용자 설정 비교.
- **`tools/installer/`** (초안, 컴파일·서명 안 함): `maya_kit_setup.ps1` (PowerShell 5.1: Blender 찾기 — Uninstall 키·Program Files·Steam·Store,
  zip manifest 로 버전 범위, 여러 버전, 실행 중이면 거부, 설치 기록 → 제거), `blender_helper.py` (Blender 안 make / remove / status),
  `maya_kit.iss` (Inno Setup 6: 사용자 단위, 버전 체크 목록, Maya 모드 옵션, 제거기). **`tools/installer_check.py`** 가 ps1 을 샌드박스에서 왕복.
- `tools/release_probe.py`: `enable`, `offline_org` 모드, `MAYA_KIT_REPO`, 스냅숏에 `kit_version`·`repos`; Remove 의 `repo_index` 를 Blender 목록
  (`extension_repos_read`, 켜진 저장소만) 에서 찾음.
- `tests/test_step61_distribution.py`: manifest 규칙 (이름·라이선스·tagline·권한 설명·태그·빈 선택 필드), 네트워크·자동 업데이트 코드 없음,
  저장소 이름 하드코딩 없음, 쓰기 위치 (`user_resource` 는 앱 템플릿과 레거시 대체 경로뿐).

### 실측으로 안 것

- 저장소 sync 는 `file://` 이어도 online access 필요 (`blender --online-mode --command extension sync`; 아니면 `repo_sync_all.poll` 실패).
  sync 는 켜진 원격 저장소를 모두 받는다 → 테스트는 blender_org 를 꺼서 네트워크 0.
- `extensions.package_uninstall(repo_index=…)` 의 번호는 켜진 저장소만 센다 (`$S\addons_core\bl_pkg\bl_extension_ops.py:811-830`).
- 이 PC 의 Blender 4.5.4 MSI 는 `HKLM\SOFTWARE\BlenderFoundation` 이 없고 Uninstall 키 (`DisplayName=Blender`, `InstallLocation`) 로만 찾힌다.
- `bl_app_templates_user` 로의 템플릿 복사가 확장 폴더 밖 쓰기의 유일한 예외 (앱 템플릿은 확장 종류가 아님).

## 검증

- `python tools/release_check.py --no-shots`: validate + install + 11 PASS (설치가 사용자 설정을 지킴, 끄기 복원, Make Blender Maya 뒤 Remove 복원).
- `python tools/repo_check.py`: **10/10** (위 「한 것」 의 순서; 0.1.0 → 0.1.1 업데이트 포함).
- `python tools/installer_check.py`: **9/9** (-Install -MakeMaya → 설치·켜짐·Maya 키맵·테마·스플래시, 사용자 애드온 유지, 기록 → -Uninstall -TargetsFile
  → 원래대로, 두 번째 제거 무해).
- `maya_kit_setup.ps1 -List` 가 이 PC 의 Blender 4.5 를 찾음 (Uninstall 키).
- 헤드리스 `python tests/run.py`: **486/486** (57 파일; 새 `test_step61_distribution.py` 4 개).

## 남은 것

- 사용자 결정 (`docs/user_decisions.md` 11 a–e) 뒤 공개 작업 — `docs/DISTRIBUTION.md` 「공개 전 체크리스트」.
- 이름을 바꾸면 manifest `id`/`name`, 스플래시 글자, 템플릿 이름 `MayaKit`, 문서·테스트의 `bl_ext.user_default.maya_kit` 을 함께.
- `maya_kit.iss` 는 컴파일해 보지 않음 (Inno Setup 미설치) — exe 를 만들기로 하면 컴파일·GUI 확인 (`docs/manual_checks.md` step 61).
- 끌어 놓기 링크 설치와 「Check for Updates on Startup」 알림은 GUI 확인 항목 (manual_checks).
- 플랫폼 심사의 판단 항목 (ToS 3.9 그리기 교체, 앱 템플릿 복사) 은 제출해 봐야 안다.
