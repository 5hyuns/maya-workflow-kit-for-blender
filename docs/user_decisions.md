# 사용자 결정 (위임 — Hermes가 사용자 대신 결정, 2026-10-16)

사용자는 모든 결정을 위임했다. 아래는 research/README.md 「팀이 결정해야 할 것」에 대한 결정이다.

1. **cm 단위**: 기본값은 **m 유지 + 표시 단위 cm** (`unit_settings.length_unit='CENTIMETERS'`, `scale_length=1.0`). 물리·클립·임포트 부작용을 피한다.
   추가로 애드온 환경설정에 **「Maya 단위 (1 BU = 1 cm, scale_length=0.01)」 옵션**을 두고 기본은 꺼둔다. 켜면 클립 거리·그리드 스케일도 함께 맞춘다. 부작용은 docs에 적는다.
2. **부모 지정**: **Maya 방식이 기본.** P(부모 지정)는 월드 변환을 유지하면서 로컬 값을 다시 계산하고 parent inverse는 identity로 둔다. 그래서 Channel Box 수치가 Maya와 같다. Blender 방식(parent inverse 유지)은 환경설정 옵션으로 남긴다.
3. **배포 형태**: **Blender 4.2+ Extension 하나**(키컨피그, 오퍼레이터, UI, 테마)로 배포한다. App Template(레이아웃 `startup.blend`)은 익스텐션 안에 넣어두고, 환경설정의 「Maya 레이아웃 설치」 버튼으로 사용자 `scripts/startup/bl_app_templates_user/`에 복사한다. 제거 버튼도 둔다. 레거시 애드온 zip도 같은 소스에서 빌드한다.
4. **대상 버전**: Blender 4.5 LTS (설치본 `C:/Program Files/Blender Foundation/Blender 4.5/blender.exe`). Maya 기준은 2022 팩토리 기본값.
5. **불가능한 것**(Y-up, rotate/scale 피벗 분리, 필드 위 MMB 드래그, MEL 실행)은 C++ 수정 없이 우회하고, 안 되는 것은 문서에 적는다. Blender 소스는 포크하지 않는다.
6. **Maya 자료 사용**: Maya의 MEL·아이콘·리소스 파일을 저장소에 복사해 배포하지 않는다. 동작과 배치만 참고해 다시 구현한다. `research/`의 추출 JSON은 내부 참고용이다.
7. **사용자 설정 보호**: 테스트할 때 사용자의 실제 Blender 설정(`%APPDATA%/Blender Foundation`)을 건드리지 않는다. `--factory-startup`이나 저장소 안의 임시 `BLENDER_USER_CONFIG`/`BLENDER_USER_SCRIPTS`를 쓴다.
8. **Maya 길이 규칙 (delegated, step 21, 2026-10-17)**: **Maya 길이 1 = 씬 표시 길이 단위 1** (Maya 의 current linear unit 과 같은 뜻,
   research/maya/defaults.json:10). Create 메뉴·셸프·마킹 메뉴·핫박스(`maya_kit.create`), Ctrl+G 그룹, `cmds.polyCube()` 등 모든
   생성 경로가 `operators/units.maya_unit()` 을 곱한다. 그래서 Channel Box 의 1 은 Maya 처럼 1 cm 이고, Maya FBX(cm)를 가져온 크기와
   같다 (Blender FBX 임포터 `global_scale = UnitScaleFactor / (100·scale_length)`, `$S\addons_core\io_scene_fbx\import_fbx.py:3133-3135`).
   - MayaKit 템플릿(결정 1: m + cm 표시): pCube1 = 0.01 BU = "1 cm". 템플릿의 3D 뷰는 Maya 새 씬 persp(28, 21, 28 cm)와 클립
     0.1 / 10000 cm 로 맞춘다.
   - Maya Units 옵션(scale_length 0.01): pCube1 = 1 BU = "1 cm". 새 파일에서는 뷰도 같은 cm 장면을 보도록 함께 스케일된다.
   - 팩토리 씬(m 표시): pCube1 = 1 BU = "1 m" (Maya 의 working unit 을 m 로 둔 것과 같음).
   - 결정 1 은 그대로다 (m 유지 → 물리·라이트 감쇠는 실제 크기 1 cm 물체로 계산된다. Maya 에서 가져온 장면과 같은 조건). 시뮬레이션은 결정 10 으로 개정 (step 48).
     step 10 「계획」 7 의 "1 Maya 단위 = 1 BU" 를 대체한다.
9. **결정 3 개정 — 첫 시작 경로 (delegated, step 42, 2026-10-17)**: 레이아웃 템플릿은 여전히 사용자 동작으로만 설치된다 —
   확장을 켠 뒤 첫 GUI 시작에 한 번 뜨는 환영 대화상자의 「Make Blender Maya」, 환경설정의 같은 버튼, 또는 기존 「Install Maya
   Layout」. Make Blender Maya 는 템플릿 설치 + Maya 테마 + 스플래시 끔 + 「Start in Maya Layout」 (파일 없이 시작하면 MayaKit
   템플릿으로 연다) 를 한 번에 켜고 환경설정을 저장한다. 「Revert Maya Look」 은 모두 끄고 (테마·스플래시 복원) 템플릿을 지운다.
   테마는 이제 옵션이며 확장을 끄면 원래 테마로 돌아온다. 템플릿에 `userpref.blend` 는 넣지 않는다: 템플릿 안에서 사용자의
   애드온 목록·테마·ui_scale 을 통째로 바꾼다는 것을 실측했다 (docs/steps/step_42.md).
10. **결정 8 개정 — 시뮬레이션 스케일 (delegated, step 48, 2026-10-17)**: Maya 2022 의 nucleus 기본값은 `spaceScale` 1.0, 중력 9.8,
    장면 단위 cm (mayapy 로 측정, docs/steps/step_48.md). Maya 문서대로라면 [K] Space Scale 1 은 장면 한 단위를 1 m 로 시뮬레이션해서
    1 cm 큐브가 1 m 물체처럼 떨어진다 (떨어지는 시간 √(L/g) 가 같음). kit 의 FX 생성 경로 (step 68, 처음 계획 번호 65) 는 Maya 사용자가 보는 움직임을 따른다:
    중력 = 9.8 × `maya_unit()` / Space Scale m/s² (kit "Space Scale" 기본 1 = Maya 와 같은 뜻, 0.01 이면 실제 크기), 충돌 거리·마진·
    파티클 크기·속도·Mantaflow 도메인 = Maya 값 × `maya_unit()`; 필드·이펙터 크기는 step 54. 장면 중력은 전역이라 Blender 의 Physics
    탭으로 직접 만든 시뮬레이션도 줄어든 중력을 받지만 길이 기본값은 미터 그대로다 (안내). 기하 크기 (결정 8) 와 조명 감쇠 계산은 그대로
    (조명 세기는 × `maya_unit()²`, 태양광 제외, step 54). Bullet 의 절대 임계값과 1 cm 안정성, Y-up → Z-up 중력 방향은 step 68 에서 잰다.
    결정 8 의 "물리·라이트 감쇠는 실제 크기 1 cm" 는 시뮬레이션에 한해 이 결정으로 바뀐다.
11. **배포 방식 (delegated, step 61, 2026-10-18 — 공개는 아직 안 함)**: 조사·비교는 `docs/DISTRIBUTION.md`. 기본 방침:
    무료 GPL 핵심판을 **자체 저장소 (정적 `index.json`, `tools/build_repo.py`) 로 먼저**, 정리 후 **extensions.blender.org** 에 제출;
    Windows .exe 설치기는 선택 (초안 `tools/installer/` 만, 컴파일·서명 안 함); 유료는 하더라도 「무료 킷 + 별도 유료 상품」; 포터블
    Blender 묶음은 하지 않음. 공개 전에 **사용자가 정할 것** (아래 「기본값」 은 정하지 않으면 따르는 delegated 값):
    - a. **제품 이름과 `id`** — Autodesk 상표 지침은 "Maya" 를 제품 이름에 넣지 말라고 한다 (자기 이름 + "for Maya users").
      `id` 는 업데이트의 정체성이라 첫 공개 전에 한 번만. 기본값: 공개 전까지 "Maya Kit" / `maya_kit` 유지, 공개 직전에 새 이름으로.
    - b. **무료 / 유료** — 기본값: 무료 (GPL, 플랫폼 조건). 유료라면 Superhive (구매 후 12개월 업데이트 정책) 에 별도 상품.
    - c. **계정·공개 정보** — Blender ID (플랫폼), 정적 호스팅 계정 (예: GitHub Pages), 판매 시 Superhive/Gumroad. manifest
      `maintainer` 의 이메일은 공개 목록에 보인다 — 공개용 주소로 바꿀지.
    - d. **킷 바이너리의 CC0 선언** (`startup.blend`, `splash*.png`, `welcome.png`: 모두 킷 스크립트가 만든 것) — 플랫폼 ToS 1.2 조건.
    - e. **exe 를 만든다면 코드 서명** (OV 인증서 약 $215–400/년, 한국 개인은 Azure Artifact Signing 불가) — 기본값: exe 안 만듦.
12. **배포처와 이름 (사용자 결정, 2026-10-19 — 사용자 지시의 「결정 8」; 8 번이 이미 단위 규칙이라 12 번으로 적음, delegated)**:
    - 배포처 = **extensions.blender.org (무료, GPL)**. 결정 11 의 a / b 를 이것으로 정한다 (업로드는 사용자가 직접).
    - 이름 = **Allset for Maya Users**, manifest `id = "allset"`, tagline **"The whole Maya workflow in Blender, in one install"**
      (50 자, 마침표 없음). Autodesk 상표 지침의 「for」 참조 형태: 우리 브랜드 Allset 이 앞, Maya 는 대상 표시로만.
      id · URL · 패키지 · 연산자 / 클래스 접두사에는 maya 를 쓰지 않는다 (`allset.` / `ALLSET_`).
    - 사용자에게 보이는 글: Maya 동작을 설명하는 표현 (Maya-style, as in Maya, Maya 메뉴 이름 재현) 은 유지, 브랜드처럼 쓰인 이름
      (테마, 앱 템플릿, 스플래시, 「Autodesk App Store」 메뉴) 은 중립 이름. README · 환경설정 About · 등록 설명에 영문 상표 고지문
      (`docs/distribution/extensions_audit.md` 「필수 고지문」). 근거: `docs/distribution/extensions_audit.md`, 이름 선택 과정
      `docs/distribution/naming.md`.
    - **2026-10-20 — 이 결정의 이름 부분은 아래 개정으로 바뀌었다** (위 글은 이전 결정과 그 이유로 남긴다).

    **결정 12 개정 — 이름 (사용자 결정, 2026-10-20, step 125 — delegated 아님)**. 사용자 지시 (원문):
    「Allset은 브랜드 힘이 없다. 제품 이름은 'Maya Workflow Kit'으로 하고, 저장소 이름에는 Blender를 붙이고
    (maya-workflow-kit-for-blender), Blender 애드온(스토어) 이름에서는 Blender를 뺀다. 제품 이름과 저장소 이름은 같은 계열이어야 한다.」
    - 제품 / 스토어 표시 이름 = **Maya Workflow Kit** (manifest `name`; 「Blender」 는 넣지 않는다 — 플랫폼 ToS 2.1).
    - 저장소 이름 = **Maya Workflow Kit for Blender**, GitHub 슬러그 `maya-workflow-kit-for-blender`
      (`https://github.com/5hyuns/maya-workflow-kit-for-blender`, 비공개로 만들 예정). README 제목도 「Maya Workflow Kit for Blender」.
      문서 · README · manifest `website` / 링크의 저장소 표기는 이 슬러그. 로컬 폴더 `C:/Repos/blender-maya-kit` 는 그대로.
    - 그대로 두는 것: manifest `id = "allset"`, 패키지 `src/allset`, 연산자 / 클래스 접두사 `allset.` / `ALLSET_`, 환경 변수
      `ALLSET_*`, tagline **"The whole Maya workflow in Blender, in one install"**, 테마 "Studio Grey (Maya-inspired)", 키컨피그
      "Maya-style". 바뀌는 것: 앱 템플릿 표시 이름 (폴더 `Maya_Workflow_Kit` → File > New > Maya Workflow Kit), 릴리스 zip
      `maya-workflow-kit-<version>.zip`, 화면의 「Allset」 글자 (환영 창, 환경설정, 스위치, 메뉴, 핫박스, 알림, 마케팅 잠금업).
    - 바꾼 이유 (사용자): 「Allset」 은 브랜드 힘이 없다 — 이름만으로 누구를 위한 무엇인지 알 수 없다.
    - **상표 위험 (사용자가 알고 선택함)**: Autodesk 상표 지침은 Autodesk 상표 (Maya) 를 **제품 이름의 일부로 쓰지 말고**, 자기 이름 뒤에
      「for Maya」 같은 참조 형태로 쓰라고 권한다 (`docs/distribution/extensions_audit.md` 「Maya 상표 결론」; 이전 이름 Allset for
      Maya Users 가 그 형태였다). 「Maya Workflow Kit」 은 Maya 로 시작하므로 이 권고에서 벗어난다. 대비:
      - **id 는 중립 유지** (`allset`, URL · 패키지 · 접두사에 maya 없음): Autodesk 가 이름을 바꾸라고 하면 manifest `name`, 템플릿
        표시 이름, 화면 글자, 문서만 바꾸면 된다 — 업데이트 정체성 (`id`) 과 사용자의 설치는 이어진다.
      - **스토어 심사에서 이름이 지적되면 대체 이름 후보 = 「Workflow Kit for Maya Users」** (지침의 「for」 형태; 같은 계열 저장소 이름은
        그때 다시 정한다).
      - 모든 자료 (README, 스토어 설명, 환경설정 About, 마케팅 이미지 · 글) 에 **비제휴 상표 고지문을 유지**한다
        (`docs/distribution/extensions_audit.md` 「필수 고지문」).
      - 이름 바로 뒤 첫 문장에 **「for Maya users, in Blender」 맥락**이 오게 한다 (마케팅 잠금업의 둘째 줄, README · 스토어 설명의 첫
        문장). 「Maya」 를 이름 안에서 따로 강조색으로 칠하지 않는다.
13. **스토어 심사 대응 — 사라지는 기능 (delegated, step 130, 2026-10-21, GitHub #40)**. extensions.blender.org 심사자 요구
    (exec/eval 금지, sys.path·sys.modules 금지, 테마 관련 전부 삭제, `user_disabling` 삭제, 끄면 모든 것이 되돌아가야 하고 되돌리는 데
    추가 조치가 필요한 변경 금지, tags = User Interface 만) 를 따르기 위해 아래 기능을 없애거나 바꾼다. 결정 3·9 의 테마·앱 템플릿·
    환경설정 저장 부분과 결정 12 개정의 테마 이름 "Studio Grey (Maya-inspired)" 를 대체한다. 근거와 레인 분담: `docs/steps/step_130.md`.
    - **테마 삭제**: 킷 테마 (`theme/studio_grey*.xml`), 테마 적용·백업·복원 코드, 「Revert Maya Look」 을 모두 뺀다. 킷이 그리는 색은
      사용자 테마 값이나 킷 고정 색을 쓴다. 그래서 Maya 선택 색 (리드 초록 #43ffa3, 나머지 흰색), Maya 회색 UI, Alt+B 그라디언트
      배경은 더 이상 자동으로 오지 않는다 — Alt+B 는 뷰마다 단색 배경 (`View3DShading.background_type = 'VIEWPORT'`) 만 돌린다.
      대신 README · 리스팅 · 사이트의 「Recommended setup」 에 사용자가 직접 고르는 어두운 회색 테마 (Blender 의 Get Extensions 에서
      설치) 를 권한다. Maya 회색 테마는 나중에 **별도 테마 확장** 으로 낼 수 있다 (미정).
    - **앱 템플릿 삭제**: 사용자 `scripts/startup/bl_app_templates_user/` 로 복사하던 「Maya Workflow Kit」 템플릿 (File > New 항목,
      스플래시) 을 없앤다 — 확장 폴더 밖 쓰기 금지. Maya 레이아웃은 확장 안의 `startup.blend` 에서 워크스페이스를 **현재 파일에
      append** 한다 (파일 데이터일 뿐, 저장하지 않으면 남지 않음). 「Start in Maya Layout」, 템플릿 설치·제거 버튼, 스플래시 숨김도 없어진다.
    - **환경설정 프리셋 삭제** (`prefs_preset.py`): 내비게이션 (Turntable, 활성 주변 회전 끔, 마우스 위치 줌 끔, Dolly 줌, 자동 원근),
      Undo Steps 256, Region Overlap 끔 (단단한 사이드 패널), 오토키 「Only Insert Available」, UI 밀도 (`ui_scale`), Segoe UI 글꼴,
      매끈하지 않은 와이어, 스플래시 숨김 — 킷은 더 이상 `bpy.context.preferences` 에 쓰지 않는다. 필요한 값은 「Recommended setup」 에
      사용자가 직접 바꿀 항목으로 적는다. Maya 의 오토키 「있는 채널만」 은 킷이 직접 키를 넣는 방식으로 대신한다 (레인 C 판단).
      3D View 패널 메뉴의 「Tumble around selection」 은 환경설정 대신 뷰 단위로 바꾸거나 뺀다 (레인 C).
    - **활성 keyconfig 를 바꾸지 않는다**: Maya 키는 모두 **애드온 keyconfig** (`wm.keyconfigs.addon`) 항목이고, 확장을 끄거나 Maya 모드를
      끄면 사라진다. 사용자의 활성 keyconfig 이름이 userpref 에 "Maya-style" 로 저장되는 일이 없다.
    - **`switch.user_disabling` / `app_template.remove_on_disable` / 환경설정 스냅숏 삭제**: 되돌릴 영구 변경이 없으므로 끄기 = 평범한
      `unregister()`. 「Restore Blender Settings」 도 필요 없어진다.
    - **스크립트 실행 = Blender 자신의 경로**: Command Line · Script Editor · Python 셸프 버튼의 코드는 Text 데이터블록에 쓰고
      `bpy.ops.text.run_script` 로 실행한다 (`exec` / `eval` / `compile` 없음). `import maya.cmds` 는 import 훅 대신 실행 전에 그 줄을 킷
      cmds 모듈 import 로 바꿔 쓴다 (사용자에게 보이는 Text 에 그대로 남음).
    - **manifest `tags = ["User Interface"]`** 만, 권한 `files` = "Your shelves and Maya project folders".
    - 검증: `tests/test_step130_package_scan.py` (패키지 정적 스캔), 레인 C 의 설치→등록→Maya 모드→해제→제거 왕복 비교 테스트,
      `blender --command extension validate`. 심사자 답글 초안: `docs/distribution/review_reply.md`.

14. **결정 3 · 9 개정 — 영구 변경 없음 (사용자 요청 + 심사자 요구, step 130, 2026-10-21, #40; 세부 선택은 delegated)**.
    사용자 지시 (원문): 「user_disabling·remove_on_disable 삭제, unregister가 register한 모든 것을 되돌리게; 확장 폴더 밖에 파일을 쓰는 것(app
    template 복사 등)·사용자 환경설정 영구 변경(save_userpref, 입력/키맵 prefs)·남는 handler/timer/msgbus 전부 제거 또는 런타임·애드온 키맵으로
    전환 ... 기능이 사라지는 부분(테마, app template, prefs 프리셋 등)은 docs/user_decisions.md에 기록.」 심사자 (extensions.blender.org):
    "Remove user_disabling. Add-on should uninstall normally without additional functions. Everything that is registered should be
    unregistered. No modifications should be made with add-on that requires additional steps to be unmade."
    - **킷은 Blender 환경설정을 쓰지 않는다** (`bpy.context.preferences.*` 값). 킷 자신의 애드온 환경설정 (Maya 모드, Start in Maya Layout 등)
      만 바꾸고, 그 변경을 Blender 의 Auto-Save Preferences 가 저장하도록 `is_dirty` 만 표시한다. `save_userpref` 는 Maya 의 File > Save
      Preferences 메뉴 (사용자 명령) 뿐.
    - **확장 폴더 밖에 쓰지 않는다**: 앱 템플릿 복사 (`scripts/startup/bl_app_templates_user/Maya_Workflow_Kit`) 를 없앴다. Maya 레이아웃
      `startup.blend` 는 확장 안에만 있고 읽기만 한다 — 「Maya Layout in This File」 / 스위치 = 그 파일의 워크스페이스를 현재 파일로 append
      (`switch.enter_layout`), 「New Scene in Maya Layout」 (`allset.new_maya_scene`, Maya File > New Scene, Status Line 새 장면 버튼) =
      `wm.read_homefile(filepath=<번들 startup.blend>, load_ui=True)` — 이름 없는 새 파일이고 환경설정을 다시 읽지 않는다 (측정).
    - **스냅샷 · 복원 장치 삭제**: `switch_snapshot.json`, `FOOTPRINT`, 테마 백업, `restore_snapshot` / `finish_interrupted`,
      「Restore Blender Settings」 / 「Revert Maya Look」 버튼, `switch.user_disabling`, `app_template.remove_on_disable` /
      `reinstall_if_wanted`. 되돌릴 영구 변경이 없으므로 끄기 · 비활성화 · 제거 = 등록한 것의 등록 해제뿐 (handler, timer, 키맵 항목, 클래스,
      속성, draw 함수). 검증: `tests/test_step130_lifecycle.py`.
    - **사라진 기능 (사용자에게 보이는 손실)** — 필요하면 사용자가 Blender 환경설정에서 직접 고른다 (리스팅의 「추천 환경설정」 글, 코드 없음):
      - Maya 내비게이션 프리셋 (Turntable, Dolly, 가로 줌 축, Zoom to Mouse 끔, Auto Perspective ...; step 4).
      - Undo 256 단계 (Blender 기본 32; step 30).
      - Solid Side Panels = Region Overlap 끔 (step 112): 겹침이 켜진 사용자 설정에서는 사이드바 / 툴바가 뷰 위에 그려질 수 있다 (Maya
        패널은 step 116 부터 별도 영역이라 영향이 작다).
      - Maya 테마 · 스플래시 끔 · Maya 밀도 (UI 크기) · Segoe UI 글꼴 · 앨리어스 와이어 (steps 42–44; 테마 제거는 레인 H).
      - 앱 템플릿: File > New > Maya Workflow Kit 항목과 「Blender 기본 File > New = Maya 레이아웃」. 대신 Maya 메뉴의 New Scene /
        「New Scene in Maya Layout」. Ctrl+N 키 항목은 레인 K (#44).
      - = / − 매니퓰레이터 크기: Blender `gizmo_size` 대신 킷 Move / Scale 매니퓰레이터만 세션 동안 커지고 작아진다 (Blender 의 Rotate
        기즈모는 그대로).
      - View > Tumble Behaviour 두 항목: Orbit Around Selection 환경설정을 바꾸지 않고 상태만 보여 주며, 누르면 Preferences > Navigation 을
        연다.
    - **Maya Auto Key 는 유지 — 방식만 바뀜**: Blender 의 "Only Insert Available" 환경설정 대신 킷 자체 토글 `Scene.allset_auto_key`
      (Time Slider 의 키 버튼) + depsgraph handler 가 이미 키가 있는 채널만 현재 프레임에 키한다 (`operators/auto_key.py`; 트랜스폼이
      끝난 뒤, 재생 중 / NLA 매핑 객체 제외). Blender 의 자체 Auto Keying 은 사용자 몫으로 남는다.
    - Maya 레이아웃의 3D 뷰 배경 = 뷰 자체의 단색 Maya #5c5c5c (`View3DShading.background_type='VIEWPORT'`, 테마가 아님; #45).
    - 결정 3 의 「Maya 레이아웃 설치」 버튼 · 사용자 scripts 폴더 복사, 결정 9 의 템플릿 설치 · Maya 테마 · 스플래시 끔 · 환경설정 저장은
      이 결정으로 대체된다.

15. **Selection Priority 끔의 뜻 (delegated, PR #125 후속, 2026-10-26)**: PR #125 가 조인트 클릭 선택을 `allset.select_priority`
    (Object 모드 클릭 맨 앞) 에 넣으면서, 애드온 환경설정 「Selection Priority」 를 꺼도 Object 모드의 모든 클릭을 가로채
    (`view3d.select` 를 직접 부름) 설정의 뜻이 바뀌었다. 정한 규칙: **꺼져 있으면 조인트를 맞힌 클릭만 킷이 받고 (Maya 의 조인트는 각자
    노드라 아마추어 전체가 아니라 그 조인트를 고름), 그 밖의 클릭은 PASS_THROUGH = Blender 자체 선택 (깊이 순, 반복 클릭 순환).**
    켜져 있으면 전과 같이 Maya 우선순위 (IK 핸들 > 조인트 > 커브 > 메시). Pose / 아마추어 Edit 모드에서 리그 밖을 클릭하면 리그에서 빠져나가는
    동작은 설정과 무관 (아마추어 모드에서만 일어나는 일이라 「아마추어 히트에만 개입」 범위 안). 근거: `C:/Repos/bmk-strategy/PR125_MAYA_CHECK.md`
    #3. 검증: `tests/test_pr125_followup.py::test_priority_off_leaves_non_joint_clicks_to_blender`.

16. **스켈레톤 선택 = 자동 Pose 모드 (PR #125 수용, 2026-10-26, 유지보수자 결정: 「Maya 손맛이 맞으면 PR 동작을 따른다」)**.
    `research/maya/workflows/rigging.md:136` 의 이전 결정 (delegated, 「오브젝트 모드에서 아마추어 클릭 → 포즈 모드 자동 진입은 하지 않음 —
    다른 오브젝트 선택이 끊김」) 을 뒤집는다. 이유: PR #125 가 그 끊김을 풀었다 — Pose / 아마추어 Edit 에서 다른 오브젝트나 빈 곳을 클릭하면
    (뷰포트, Outliner 모두) 리그에서 빠져나가 그 오브젝트를 고른다 (`joint_selection.select_object_at`, `toolbox.pose_empty_click`,
    `toolbox.joint_outliner_select`). 그래서 「클릭 = 그 조인트 선택」 이라는 Maya 의 손맛 (Maya 의 조인트는 오브젝트 노드, 모드 없음;
    2022 실측 + 2023–2027 문서 변화 없음, `C:/Repos/bmk-strategy/PR125_MAYA_CHECK.md` #3 #4 #7, `PR125_MAYA_LATER.md` 5) 을 얻고
    잃는 것이 없다. 규칙: 활성 + 선택된 아마추어가 바뀌면 Object → Pose, 선택이 풀리면 Pose → Object (`toolbox._auto_armature_tick`,
    0.18 s); Edit 은 사용자가 고른 경우 (F8 / 선택기) 만. 남은 확인: Outliner / 전체 선택으로 아마추어를 고르면 선택된 본이 없어 Channel
    Box 가 빈다 (Maya 는 루트 조인트 채널) — docs/manual_checks.md 「PR #125」. 연구 노트 `rigging.md:136` 은 메인 작업 트리의 추적되지 않는
    파일이라 이 브랜치 작업에서 고치지 않았다 — 이 결정이 그 줄을 대신한다.
