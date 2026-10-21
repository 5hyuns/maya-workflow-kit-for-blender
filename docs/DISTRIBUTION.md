# 배포 방식 — 조사·비교·추천 (step 61)

> **2026-10-20 사용자 결정 (`docs/user_decisions.md` 12 개정, step 125)**: 표시 이름 **Maya Workflow Kit** (스토어 이름에 Blender 없음),
> 저장소 **Maya Workflow Kit for Blender** (`https://github.com/5hyuns/maya-workflow-kit-for-blender`), id `allset` 그대로, 릴리스 zip
> `maya-workflow-kit-<version>.zip`. 이 이름은 Autodesk 지침의 「for」 형태가 아니다 — 위험과 대체 이름 후보 「Workflow Kit for Maya
> Users」 는 결정 12 개정에.
> 2026-10-19 사용자 결정 (`docs/user_decisions.md` 12): extensions.blender.org 에 무료로, 이름 Allset for Maya Users (id `allset`) —
> 이름 부분은 위 개정으로 바뀜. 아래의 `maya_kit` / "Maya Kit" 는 step 111 전, "Allset" 은 step 125 전 이름이다. 등록 감사:
> `docs/distribution/extensions_audit.md`.

> **2026-10-21 첫 심사 결과 (step 130, GitHub #40)**: extensions.blender.org 심사자가 다섯 가지를 요구했다 — `exec` / `eval` 금지,
> `sys.path` / `sys.modules` 수정 금지, 테마 관련 전부 삭제 (테마는 설명·웹사이트에서 추천만), `user_disabling` 삭제 + 등록한 것은
> 전부 해제 + 되돌리는 데 추가 조치가 필요한 변경 금지, tags 는 User Interface 만. 그래서 아래 (a) 의 「예외 하나」 (앱 템플릿 복사),
> 환경설정 프리셋·백업·복원, 테마, 활성 키컨피그 전환은 **모두 없어졌다** (결정 13, `docs/user_decisions.md`): 레이아웃은 현재 파일에
> 워크스페이스로 append, Maya 키는 애드온 keyconfig 항목, 스크립트는 Text 데이터블록 + `text.run_script`, manifest `tags =
> ["User Interface"]`, 권한 `files` = "Your shelves and Maya project folders". 「되돌리기」 는 이제 평범한 끄기·Remove 뿐이다 (복원할 것이
> 없음). 정적 검사 `tests/test_step130_package_scan.py`, 심사자 답글 초안 `docs/distribution/review_reply.md`. 아래 본문은 step 61 의
> 조사 기록으로 남긴다.

사용자 요청 (2026-10-18): 「나중에 addon이나 exe 설치, 배포가 어떤 방식이 좋을지 고민해 봐라.」
조사·비교·준비만 했다. **업로드·공개·결제 설정·서명은 하지 않았다** — 결정 항목은 `docs/user_decisions.md` 11.
조사 날짜 2026-10-18. 출처는 각 줄의 URL (블렌더 매뉴얼 "latest" = 5.2 LTS, 확장 플랫폼 ToS = 2026-08-10 판).
[O] 원문 확인, [I] 추론, [U] 확인 못 함 (맨 끝 목록).

## 한눈에

| | (a) extensions.blender.org | (b) 자체 저장소 URL | (c) Superhive / Gumroad 유료 | (d) Windows .exe 설치기 | (e) 포터블 Blender + 킷 묶음 |
|---|---|---|---|---|---|
| **설치 (Maya 사용자, Blender 있음)** | 웹 「Get」 버튼을 Blender 창에 끌어 놓기 + 첫 「Allow Online Access」 ≈ 2–3 동작. 앱 안: Edit > Preferences > Get Extensions > 검색 > Install ≈ 5 클릭 + 입력 [O] | 웹 페이지의 끌어 놓기 링크 (`….zip?repository=./index.json`) 하나 = 설치 + 저장소 등록 ≈ 2–3 동작. 직접 등록: Preferences > Get Extensions > Repositories ▾ > + > Add Remote Repository > URL 붙여넣기 > 검색 > Install ≈ 9 [O] | 구매 → zip 다운로드 → Blender 에 끌어 놓기 (Install from Disk) ≈ 결제 뒤 3–4. Superhive 는 첫 끌어 놓기에 API 토큰 입력 → 이후 앱 안 [O] | 다운로드 → (서명 없으면 SmartScreen 「추가 정보 → 실행」 +2) → 라이선스 / Blender 버전 선택 / Maya 모드 / 설치 / 마침 ≈ 6–8. **Blender 를 먼저 닫아야 함** [O 초안 실측] | 400 MB zip 받기 → 풀기 → blender.exe ≈ 3, 대신 사용자의 원래 Blender 와 다른 프로그램 [O] |
| **업데이트** | 앱 안 「Check for Updates」 또는 저장소의 「Check for Updates on Startup」 → 상태 표시줄 알림 → Update. 자동 설치는 없음 [O] | (a) 와 같음 (같은 Blender 장치) — `tools/repo_check.py` 로 0.1.0 → 0.1.1 실측 [O] | Superhive: 토큰 저장소로 앱 안 업데이트, **구매 후 12개월** (2026 정책, 연장 +25%). Gumroad: 손으로 다시 받기 [O] | 새 exe 다시 실행. 설치기가 (b) 저장소를 `repo-add` 로 등록하면 이후 앱 안 업데이트 [I] | 묶음 전체를 다시 받기 (또는 System 저장소 수동 교체) [O] |
| **되돌리기** | 상단 바 「Maya \| Blender」, 환경설정 「Restore Blender Settings」, Preferences > Extensions > Remove — 모두 사용자 설정 복원 (step 60) [O 실측] | 같음 + `repo-remove` 로 저장소 제거 — 실측 10/10 | 같음 | 제어판 「제거」 = Blender 안에서 Remove (복원 후 삭제) — 실측 9/9 | 폴더 삭제. 원래 Blender 설정은 처음부터 안 건드림 |
| **비용** | 0 | 0 (GitHub Pages 같은 정적 호스팅) | Superhive 무료 플랜: 판매가의 70 % 수령, 결제 수수료 5.5 % + 품목당 $0.49 (Pro $49/월 80 %, Ultimate $199/월 90 %). Gumroad: 10 % + $0.50 (Discover 경유 30 %), 카드 수수료 별도 [U] | Inno Setup 무료 (상용은 라이선스 구매 「요청」), NSIS zlib. 서명: OV 인증서 약 $215–400/년 (Certum €209~), 하드웨어 키 필수, 유효 최대 459일. Azure Artifact Signing $9.99/월은 **한국 개인 불가 (조직만)**. 서명해도 평판이 쌓일 때까지 SmartScreen 경고 | 호스팅 400 MB × 버전 |
| **법적 조건** | GPL-3.0-or-later 코드 전부 ✓, **바이너리 자산은 CC0** (startup.blend, splash/welcome PNG, maya.xml), 이름에 "Blender" 금지, 숨은 동작 금지 (설명에 모든 변경), 내부 모듈 변조 금지 (아래 위험) | 심사 없음. GPL 만 지키면 됨 | GPL 코드 판매 가능 — 구매자도 GPL 로 받아 재배포 가능 (Blender 라이선스 페이지). 확장 플랫폼에 같은 제품의 무료판을 두면 앱 안 광고·업셀 금지 | 설치기 스크립트도 우리 것 (GPL), 서명 계약은 사용자 명의 | Blender GPL: 공식 릴리스 그대로면 blender.org 소스 안내로 충분. 제품 이름에 "Blender" 금지 (상표 정책) |
| **경쟁 제품** | Maya 테마 (무료), Maya Pivot (무료), Gesture Helper, BagaPie (무료 애드온 + 유료 자산은 Superhive) | 작은 Maya 키맵들은 GitHub (zip/py) | Maya Config Pro $50 (Superhive, 확장 호환, 12개월 지원), Maya Shelf & Navigation $8, Friendly Pivot $10/$20, HardOps/BoxCutter $19 [U 가격] | 이 분야에서 exe 로 파는 제품은 못 찾음 [U] | 못 찾음 |

**추천 (delegated)** — 아래 「추천」 절: 이름부터 정하고 → **무료 GPL 핵심판을 자체 저장소 (b) 로 먼저** → 플랫폼 위험 항목을 정리한 뒤
**extensions.blender.org (a) 에 제출** → exe (d) 는 선택 (지금은 만들지 않음, 초안만) → 유료 (c) 는 하더라도 「무료 킷 + 별도 유료 상품」 → 묶음 (e) 은 하지 않음.

**지원 Blender** (모든 경로 공통, manifest `blender_version_min` 4.5.0 / `blender_version_max` 5.3.0): 4.5.x – 5.2.x —
4.5.4, 5.0.1, 5.1.2, 5.2.2 에서 헤드리스·GUI·설치 왕복 통과 (`docs/compat_5x.md`, step 118). 5.3 이 나오면 같은 측정 뒤 올림.

## (a) Blender Extensions 플랫폼

- 누구나 Blender ID 로 /submit/ 에 zip 업로드 → 사람이 심사 → 공개. https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html
  심사 기간 공식 수치 없음 [U] ("Extensions are manually reviewed", https://devtalk.blender.org/t/extensions-platform/34663).
- **무료·GPL 만**: "free and Open Source extensions ... only offers GNU GPL compliant software" https://extensions.blender.org/about/ ;
  ToS 1.1 GPL-3.0-or-later, 3.10 결제·키·외부 가입으로 기능을 막지 말 것, 6.1–6.3 Blender UI 안 광고·유료판 홍보 금지 (설명 페이지의 후원 링크는 허용).
  https://extensions.blender.org/terms-of-service/
- **ToS 1.2 바이너리 자산 CC0**: 킷의 바이너리 4개는 모두 킷 스크립트가 만든 것 — `startup.blend` (`tools/make_startup.py`),
  `splash.png` / `splash_2x.png` / `welcome.png` (`tools/make_splash.py`, Blender 번들 글꼴로 렌더한 글자 포함), `maya.xml` 은 텍스트
  (`tools/make_theme.py`). Maya 자료는 들어 있지 않음 (결정 6). 저작권자가 CC0 로 내놓기로 하면 조건 충족 → 결정 11-d.
- **ToS 2.1** 이름에 "Blender" 금지 — 표시 이름 "Maya Workflow Kit" 에는 없음 (저장소 이름 "… for Blender" 는 스토어 밖). **2.4** 다른 회사 로고는 그 회사 지침이 허용할 때만 — Autodesk 지침상 Maya
  로고·아이콘 불가 (킷은 쓰지 않음).
- **ToS 3.1 "No surprises"**: 설명에 하는 일을 전부 — 킷은 키맵 (Maya 키컨피그 활성), 탐색·언두 환경설정 (백업·복원), 테마 (선택),
  레이아웃 템플릿 설치 (선택), 상단 바·메뉴·헤더 그리기 교체를 바꾼다 → 설명 초안에 그대로 적을 것 (「공개 전 체크리스트」).
- **ToS 3.9 "must not temper with ... Blender's internal modules"** — 위험 [U]: 킷은 `TOPBAR_HT_upper_bar.draw_left/right`,
  `IMAGE_HT_header.draw`, `TIME_HT_editor_buttons.draw_header`, `VIEW3D_MT_editor_menus.draw_collapsible` 을 바꾸고, 사이드바 패널을
  감싼 poll 로 다시 등록한다 (`ui/dock_tabs.py`). 끄면 전부 원래대로 (`tests/kit.py` 스냅숏, `test_enable_disable`) 지만, 심사자가 이것을
  「변조」로 볼지는 규정·선례를 못 찾았다. 제출 전에 설명에 「끄면 원래대로」 와 근거를 적고, 거절되면 (b) 로 계속.
- **심사 체크리스트** https://developer.blender.org/docs/features/extensions/moderation/guidelines/ : 자동 업데이터 금지, 파일 쓰기 위치
  (`bpy.utils.extension_path_user`), `sys` 읽기 전용, background 에서 `keyconfigs.addon` None 처리, `bl_ext`/`user_default`/`blender_org`
  하드코딩 금지. 킷 상태: 네트워크·업데이터 코드 없음, 저장소 이름 하드코딩 없음, 쓰기 데이터 (`switch_snapshot.json`, 테마 백업,
  `shelves.json`) 는 `extension_path_user` (CONFIG 는 레거시 애드온 빌드의 대체 경로일 뿐) — `tests/test_step61_distribution.py` 가 지킨다.
  **예외 하나**: Maya 레이아웃 = 앱 템플릿을 `scripts/startup/bl_app_templates_user/Maya_Workflow_Kit` (step 125 전 `Allset`) 로 복사 (사용자가 Make Blender Maya /
  Install Maya Layout 을 누를 때만, 끄기·Restore·Remove 때 삭제). 앱 템플릿은 확장 종류가 아니라 (`type` = add-on / theme) 다른 방법이
  없다 — 설명에 명시.
- manifest 규칙 (getting_started.html): `tagline` ≤ 64자·끝 문장부호 없음, 권한 설명 ≤ 64자·끝 문장부호 없음, 선택 필드는 비우지 말고 빼기,
  태그는 플랫폼 목록 (`$S\modules\_bpy_internal\extensions\tags.py:11-43`). 이번에 `tags`, `copyright` 추가 (아래 준비물).
- 사용자 쪽: 첫 사용 때 「Allow Online Access」, 업데이트는 자동 설치 없음 — "Extensions don't update automatically" https://extensions.blender.org/about/ ;
  저장소별 「Check for Updates on Startup」 → 상태 표시줄 알림 https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html

## (b) 자체 저장소 (Blender 4.2+ remote repository)

- 정적 파일 하나면 됨: "host a static JSON file that is generated by Blender"
  https://docs.blender.org/manual/en/latest/advanced/extensions/creating_repository/static_repository.html —
  `blender --command extension server-generate --repo-dir DIR --html` → `index.json` + `index.html` (끌어 놓기 링크 포함).
  **`python tools/build_repo.py`** 가 이것을 `dist/repo/` 에 만든다 (zip + index.json + index.html; 실측).
- 사용자: Repositories > + > Add Remote Repository 에 `<호스트>/index.json`, 또는 웹 페이지의 `maya-workflow-kit-x.y.z.zip?repository=./index.json&blender_version_min=4.5.0`
  링크를 Blender 창에 끌어 놓기 (설치 + 저장소 등록), 또는 명령줄 `blender --command extension repo-add --url …` (설치기가 쓸 수 있음).
- 비공개 배포가 필요하면 Access Token 지원 (Superhive·Poly Hammer 가 같은 방식) https://docs.polyhammer.com/poly-hammer-portal/blender-extension-repo
- **실측 (`python tools/repo_check.py`, 깨끗한 샌드박스 + 「사용자 설정」 시드, `file:///…/index.json`)**: repo-add + sync + install --enable
  → Maya 키맵·사용자 애드온·테마 유지 → Make Blender Maya → 끄기 = 원래대로 → 다시 켜기 → 저장소에 0.1.1 게시 → sync + update = 0.1.1,
  켜진 채 Maya 키맵 → Maya 모드에서 Remove = 원래대로, 패키지 폴더 없음 → repo-remove = 저장소 목록 원래대로. 10/10.
  - 실측으로 안 것: 저장소 sync 는 `file://` 이어도 online access 가 필요하다 (`--online-mode`, 아니면 sync poll 실패); sync 는 켜진 모든
    원격 저장소를 받으므로 테스트 샌드박스에서는 blender_org 저장소를 꺼서 네트워크를 안 쓴다; `extensions.package_uninstall(repo_index)`
    의 번호는 **켜진** 저장소만 센다 (`$S\addons_core\bl_pkg\bl_extension_ops.py:811-830`) — blender_org 를 끈 설정에서 예전 probe 가 엉뚱한 번호를 썼다.
- 호스팅: GitHub Pages / 릴리스 자산 등 아무 정적 HTTPS (공식 문서에 GitHub 이름은 없음 [U], 정적 파일 외 요구 없음).

## (c) 유료 판매 (Superhive / Gumroad)

- Superhive https://superhivemarket.com/pricing : 플랜 Free $0 → 70 %, Pro $49/월 → 80 %, Ultimate $199/월 → 90 %; 결제 수수료 5.5 / 5 / 4 %
  + 품목당 $0.49; Merchant of Record, 매월 첫 영업일 정산 (최대 31일 보류) https://support.superhivemarket.com/article/44-terms-of-use-creator .
  확장 호환 제품은 구매자가 API 토큰으로 Superhive 저장소를 붙여 앱 안 설치·업데이트
  https://superhivemarket.com/posts/blender-extension-support-launched-on-superhive . **2026 정책: 구매 후 12개월 지원·새 버전, 연장 25 %, 판매자 예외 없음**
  https://www.blendernation.com/2026/04/01/incoming-policy-changes-on-superhive
- Gumroad https://gumroad.com/pricing : 10 % + $0.50 (Discover 경유 30 %), 2025-01-01 부터 세금 대행 (MoR). Blender 저장소 연동 없음 → 수동 다운로드.
- GPL 판매 관례: "You are free to sell such scripts, but the sales then is restricted to the download service itself. Your customers will receive the script
  under the same license (GPL)" https://www.blender.org/about/license/ — 실제로 파는 것은 편의·지원·업데이트. Superhive 도 같은 안내
  https://support.superhivemarket.com/article/294-how-to-make-your-blender-addon-gpl-compliant
- 플랫폼과 같이 쓰려면 BagaPie 방식: 플랫폼에는 완전한 무료 애드온, 유료는 별도 상품 (자산·튜토리얼·지원) — 앱 안 홍보 금지 (ToS 6.1–6.3).

## (d) Windows .exe 설치기

- 설치기가 하는 일은 결국 Blender 에 시키는 것: Blender 찾기 → `blender --command extension install-file -r user_default --enable zip`
  → (선택) Make Blender Maya → 제거 때 **Blender 안에서** Remove (킷의 unregister 가 사용자 설정을 되돌린 뒤 파일 삭제; `blender --command
  extension remove` 는 애드온 코드를 안 불러 복원 불가 — step 60).
- 초안 (`tools/installer/`, **컴파일·서명 안 함**):
  - `allset_setup.ps1` — Windows PowerShell 5.1. Blender 찾기: MSI 의 Uninstall 키 (`DisplayName=Blender`, `InstallLocation`; 이
    PC 실측: `HKLM\SOFTWARE\BlenderFoundation` 은 없음), `Program Files\Blender Foundation\*`, Steam (`HKCU\Software\Valve\Steam`
    SteamPath 의 기본 라이브러리), Microsoft Store (목록에만, WindowsApps 는 직접 실행 불가 → Blender 안에서 설치 안내). zip 의 manifest
    `blender_version_min/max` 로 호환 판단. 여러 버전 선택 (`-Blender "a;b"`), 실행 중인 Blender 감지 (종료할 때 옛 환경설정을 덮어쓰므로
    거부, 코드 3), 설치한 버전 기록 (`-Record`) → 제거 때 그 목록 (`-TargetsFile`).
  - `blender_helper.py` — Blender 안에서 make / remove / status.
  - `allset.iss` — Inno Setup 6 스크립트: 사용자 단위 (관리자 권한 없음), GPL 라이선스 페이지, Blender 버전 체크 목록 (최신만 기본 체크),
    「Make Blender Maya now」 옵션, 제거기 = helper remove. Autodesk 상표 각주 포함.
  - **실측 (`python tools/installer_check.py`, 깨끗한 샌드박스 + 사용자 설정 시드)**: -Install -MakeMaya → user_default 에 설치·켜짐, Maya 키맵,
    테마·스플래시 바뀜, 사용자 애드온 유지, 기록 1줄 → -Uninstall -TargetsFile → 원래대로 → 두 번째 제거도 무해. 9/9.
- 서명·SmartScreen https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation : 서명 없는 exe 는 「Windows의
  PC 보호」 → 「실행」 을 눌러야 함; Windows 11 Smart App Control 은 서명 없는 파일을 막음; OV/EV 서명도 평판이 쌓일 때까지 경고 ("several weeks
  and hundreds of clean installs"), "EV certificates no longer bypass SmartScreen". 인증서: 2023-06 부터 하드웨어 키, 2026-02-27 부터 최대 459일
  https://shop.certum.eu/code-signing.html ; Azure Artifact Signing 개인은 미국·캐나다만 https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart
- 판단 [I]: Maya 사용자에게 exe 의 이점 (Blender 찾기, 여러 버전 한 번에, 제어판 제거) 은 실제지만, 1인 개발자에게 서명비·경고·유지비가 크다.
  zip 끌어 놓기 + Blender 안 스위치/Remove 가 같은 일을 서명 없이 한다 → **선택 사항, 지금은 초안만**.

## (e) 포터블 「Blender + 킷」 묶음

- Blender 재배포: 공식 릴리스 그대로면 blender.org 소스 안내로 GPL 충족, 수정본은 소스 동봉 https://www.blender.org/support/faq/ ;
  GPL-3 §6 https://www.gnu.org/licenses/gpl-3.0.html#section6
- 상표: "Don't use the Blender trademark ... in the name of your ... product" (보조 문구는 가능) https://www.blender.org/about/trademark-policy/ —
  "Blender Maya Edition" 같은 이름 불가.
- 크기: 4.5.13 windows-x64.zip 398,648,740 B https://download.blender.org/release/Blender4.5/
- 방식: 포터블 폴더 안 「System」 확장 저장소 ("intended to bundle extensions with Blender, to make it portable")
  https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html
- 판단 [I]: 사용자는 이미 Blender 가 있고, 킷의 목표는 그 Blender 를 Maya 처럼 바꾸고 되돌리는 것. 400 MB × Blender 업데이트마다 다시 배포 →
  **하지 않음** (오프라인 교실 같은 특수 경우에만 System 저장소로).

## (f) 이름·상표 (Maya)

- Autodesk "Guidelines for Use" https://www.autodesk.com/company/legal-notices-trademarks/trademarks/guidelines-for-use :
  "Use your own product name", "Use a referential phrase like "for," "for use with," "compatible with"", **"Don't incorporate the Autodesk trademarks
  into your product name"**, "Don't use a name that is similar to or a variation on an Autodesk trademark", 각주 "Autodesk, Maya are trademarks
  of the Autodesk group of companies. <name> is not affiliated with Autodesk.", 로고·제품 아이콘은 별도 계약 필요.
- Maya 화면 캡처는 교육·리뷰만 사전 허용, 제품 홍보 이미지는 아님 https://www.autodesk.com/company/legal-notices-trademarks/intellectual-property/copyright
  → `research/maya/screens` 는 홍보에 쓰지 않음 (결정 6 과 같은 방향).
- 현실: 플랫폼에 "Maya" 테마·"Maya Pivot", Superhive 에 "Maya Config Pro" 가 있다 — 묵인이지 허락이 아니다. 무료 애드온에 대한 Autodesk 의 집행
  사례는 못 찾음 [U].
- 결론 [I] (step 61 당시 이름 "Maya Kit" / `maya_kit` 에 대한 것; step 125 의 "Maya Workflow Kit" 도 같은 "Don't" 에 해당 — 사용자가 위험을 알고 선택, 결정 12 개정): 지금 이름은 지침의 "Don't" 에 해당. 공개 전에 **자기 이름 + "for Maya users" 류 설명**으로 바꾸는 것이
  안전하다. **`id` 는 업데이트의 정체성**이라 공개 뒤에 바꾸면 기존 사용자에게 업데이트가 끊긴다 → 첫 공개 전에 정할 것 (결정 11-a).
  킷 안 화면 문구 (상단 바 「Maya | Blender」, 메뉴 이름 등) 는 Maya 를 가리키는 서술적 사용이라 유지 [I].

## 추천 (delegated)

1. **이름·id 먼저** (11-a): 공개 전에 한 번. Autodesk 지침에 맞게 자기 이름 + tagline "Maya-style keymap, UI and workflow for Maya users"
   + 설명 끝 상표 각주. 바꾸면 manifest `id`/`name`, 스플래시 글자 (`tools/make_splash.py`), 앱 템플릿 이름을 함께.
2. **무료 GPL 핵심판 = (b) 자체 저장소로 시작**: 심사 없이 바로, 앱 안 설치·업데이트 그대로 (실측 10/10), 비용 0. 첫 사용자들로 거친 곳을 고친다.
3. **그다음 (a) 플랫폼 제출**: 도달 범위가 가장 넓다. 준비: 바이너리 CC0 선언 (11-d), ToS 3.1 설명 (모든 변경 + 되돌리기), 3.9 대비 설명
   (그리기 교체와 끄면 복원). 거절돼도 (b) 가 그대로 남는다. 두 곳에 같은 `id` 로 두면 사용자는 한 곳에서만 받는다 (저장소마다 따로 설치됨) [I].
4. **(d) exe 는 선택, 지금은 안 만듦** — 초안·테스트만 (`tools/installer/`, `tools/installer_check.py`). 만든다면 서명 (11-e) 과 함께,
   그리고 설치기가 (b) 저장소를 등록해 업데이트는 Blender 가 하게 [I].
5. **(c) 유료는 하더라도 「무료 킷 + 별도 유료 상품」** (BagaPie 방식). 킷 자체를 유료로 하면 플랫폼에 못 올리고, GPL 이라 재배포를 막을 수 없다.
6. **(e) 묶음은 하지 않음.**

## 준비물 (이번 단계에서 만든 것)

- `src/allset/blender_manifest.toml`: `tags = ["User Interface", "3D View", "Modeling", "Animation"]`, `copyright = ["2026 ohnsk"]`
  (`website` 는 공개 페이지가 생기면, `platforms` 는 순수 Python 이라 생략). `extension validate` 통과.
  주의: `maintainer` 의 이메일은 공개 목록에 그대로 보인다 (11-c).
- `tools/build_repo.py` — zip + `index.json` + `index.html` (`dist/repo/`, Blender 의 `server-generate`).
- `tools/repo_check.py` — (b) 경로 왕복 (설치·켜기·Make Maya·끄기·업데이트·Remove·저장소 제거).
- `tools/installer/` (`allset_setup.ps1`, `blender_helper.py`, `allset.iss`) + `tools/installer_check.py` — (d) 초안과 그 왕복.
- `tests/test_step61_distribution.py` — manifest 규칙, 네트워크·자동 업데이트 코드 없음, 저장소 이름 하드코딩 없음, 쓰기 위치.
- 기존 `tools/release_check.py` — zip 설치 (Install from Disk 와 같은 `install-file`) 왕복.

## 공개 전 체크리스트 (사용자가 결정한 뒤)

- [ ] 이름·id·tagline 확정 (11-a) → manifest, 스플래시, 템플릿 이름, 문서
- [ ] 바이너리 CC0 선언 (11-d) — 패키지에 `ASSETS_LICENSE` 한 줄 또는 설명에
- [ ] 설명 초안: 하는 일 전부 (키맵 활성, 탐색·언두 환경설정, 테마·레이아웃은 선택, 상단 바·메뉴 교체), 되돌리는 법 (상단 바 Blender / Restore
      Blender Settings / Remove), **명령줄 `blender --command extension remove` 는 설정을 되돌리지 못하니 Blender 안에서 Remove**, 상표 각주
- [ ] 스크린샷은 킷 화면만 (Maya 화면 캡처·아이콘 금지)
- [ ] (b): 호스팅 계정 (11-c) → `python tools/build_repo.py` → `dist/repo/` 업로드 → 끌어 놓기 링크가 든 페이지
- [ ] (a): Blender ID → /submit/ → 심사 대응
- [ ] 매 릴리스: version 올림 → `python tests/run.py`, `python tools/release_check.py`, `python tools/repo_check.py` → 저장소 갱신

## 확인 못 한 것 [U]

- 플랫폼 심사 기간; 그리기 함수 교체·패널 재등록 (ToS 3.9) 을 심사자가 받아들이는지 (첫 심사 (step 130) 에서는 지적되지 않음).
  앱 템플릿 복사·환경설정 변경·테마는 첫 심사에서 거절됨 → 제거 (결정 13).
- Autodesk 가 무료 애드온 이름의 "Maya" 를 문제 삼은 사례.
- Steam 의 Blender 폴더 이름·추가 라이브러리 위치, Store 패키지 이름 (이 PC 에 없음); NSIS 유니코드 세부; Certum 오픈소스 서명 가격.
- 경쟁 제품 일부 가격 (HardOps/BoxCutter, MACHIN3tools DeusEx: 집계 사이트 값), Gumroad 카드 수수료.
- 끌어 놓기 링크 설치 (웹 → Blender 창) 는 GUI 동작이라 자동 테스트하지 않음 → `docs/manual_checks.md`.
