# extensions.blender.org 등록 감사 + Maya 상표 조사 (Hermes 서브에이전트, 2026-10-19)

## 근거 URL
- [M] https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html (manifest)
- [T] https://docs.blender.org/manual/en/latest/advanced/extensions/tags.html
- [L] https://docs.blender.org/manual/en/latest/advanced/extensions/licenses.html
- [A] https://docs.blender.org/manual/en/latest/advanced/extensions/addons.html
- [ToS] https://extensions.blender.org/terms-of-service/
- [G] https://developer.blender.org/docs/handbook/extensions/addon_guidelines/
- [MG] https://developer.blender.org/docs/features/extensions/moderation/guidelines/
- Autodesk: https://www.autodesk.com/company/legal-notices-trademarks/trademarks/guidelines-for-use

## 요건 요약
- tagline은 64자 이하, 끝에 문장부호 없음. 빈 값 금지. type은 add-on. tags는 공식 목록에서만 [M][T].
- 애드온은 GPL-3.0-or-later. **바이너리·자산(png, blend, svg, 폰트)은 CC0** [ToS 1.2][L]. copyright 필드 [ToS 1.3].
- 이름에 "Blender" 금지. 보증받은 것처럼 보이면 안 됨. 타사 로고는 그 회사가 허락할 때만 [ToS 2.x].
- No surprises: 하는 일을 설명에 전부 적는다 [ToS 3.1]. 순수 Python, 난독화 금지 [3.5-3.6]. OS·타 소프트웨어·다른 확장·**Blender 내부 모듈**·민감한 사용자 데이터를 건드리지 않는다 [3.9].
- 네트워크를 쓰면 `network` 권한과 `bpy.app.online_access`가 필요하다 [ToS 4]. 자기완결, 원격 코드 금지 [5]. 다른 애드온 간섭 금지 [G].
- **sys.path 변경과 전역 모듈 딕셔너리(sys.modules) 삽입 금지** [G][MG]. 자기 폴더에 쓰지 말고 `bpy.utils.extension_path_user`를 쓴다 [G][A].
- 자동 업데이터 금지 [MG]. `__package__` 사용 [A]. `keyconfigs.addon`이 None일 때 처리 [MG]. 리뷰 이미지 품질 [MG]. 확장 빌드에 legacy `bl_info`를 남기지 않는 것을 권고 [A].
- 제출 전 실행: `blender --command extension validate <zip>`, 그리고 [MG]의 ruff 명령.

## 현재 코드 감사 (src/maya_kit, 0.1.0 시점 줄 번호 — 지금은 다를 수 있음)
- **위반** `command_line/__init__.py` ~207-211: `sys.modules["maya"]`, `sys.modules["maya.cmds"]` 삽입. → 커맨드 라인·셸프·스크립트 에디터의 exec 네임스페이스 안에서만 `cmds`를 제공한다. `import maya.cmds`는 그 네임스페이스 전용 `__import__` 훅으로 처리한다.
- **위반** splash*.png, welcome.png, startup.blend 등 자산에 CC0 표기 없음. → 자산 라이선스 표기를 넣는다(manifest license에 `SPDX:CC0-1.0` 추가 가능 여부 확인, 안 되면 README와 ASSETS_LICENSE). Maya 아이콘이나 Maya 화면 캡처는 넣지 않는다.
- **위험** app_template/MayaKit/__init__.py: 확장 밖에 설치된 템플릿 코드가 `addon_utils.enable`을 호출하고 활성 키맵을 바꾼다. 확장을 지워도 남는다. → 템플릿은 레이아웃만 담고 코드는 최소로 한다. 비활성화·제거 때 마커가 있는 템플릿을 삭제한다(또는 템플릿 없이 workspace append 방식만 쓴다).
- **위험** 활성화하자마자 키맵 활성화(keymap/__init__ ~96-104), 환경설정 프리셋 적용(prefs_preset ~188-197), 자동 `save_userpref`(switch.py ~409-424). → 첫 실행 환영 창에서 "Make Blender feel like Maya" 확인을 받은 뒤에만 적용한다(opt-in). 자동 저장은 사용자가 동작했을 때만 한다.
- **위험** Blender UI 클래스의 `draw` 교체: STATUSBAR_HT_header(command_line), outliner, shelf, toolbox, TOPBAR, TIME. → 가능한 곳은 append/prepend로 바꾼다. 남는 것은 설명에 이유와 복원 보장을 적는다.
- 경미: `operators/keystate.py` ctypes user32 GetAsyncKeyState(읽기 전용) → 설명에 적거나 fallback을 둔다. "Help/Autodesk App Store" 메뉴 라벨 → 오해 소지가 있어 바꾼다. 확장 빌드에서 `bl_info` 제거. `rig_tools`의 Rigify enable은 확인 창이 있어 괜찮음.
- 통과: manifest 필드, GPL, tags, 네트워크 없음, 업데이터 없음, `__package__`, keyconfigs.addon None 처리, exec는 사용자 입력만 실행.

## Maya 상표 결론
- 플랫폼 ToS는 다른 회사 제품 이름 자체를 금지하지 않는다. Autodesk 지침은 **제품 이름(id 포함)에 Autodesk 상표를 넣지 말 것, 비슷한 변형도 금지**, 대신 "for / for use with / compatible with Maya"는 허용, 내 제품명을 더 눈에 띄게, 상표 각주, 제휴를 암시하지 않을 것, 로고·아이콘 금지.
- 따라서: 이름·id·URL에는 Maya를 쓰지 않는다. tagline과 설명에서는 "Maya-style …", "for Maya users"처럼 참조로 쓰는 것은 괜찮다. UI 라벨 중 Maya의 동작을 설명하는 것("Maya-style", "as in Maya")은 괜찮지만, 브랜드처럼 쓰는 라벨(테마 이름 "Maya Grey" 등)은 "Studio Grey (Maya-inspired)"처럼 중립적으로 바꾼다. 연산자 id 접두사(`maya.` / `MAYA_OT_`)는 중립 접두사로 바꾼다.
- 선례: Maya Pivot, Origin_move_like_maya, Maya 테마 2종, Houdini 테마, Unreal Viewport Navigation 등이 승인돼 있다(심사에서 용인된 것일 뿐 Autodesk가 허락한 것은 아님).
- 필수 고지문 (설명, README, 환경설정 About에 넣는다):
  > Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc., and/or its subsidiaries and/or affiliates in the USA and/or other countries. This project is an independent, free and open-source (GPL) extension for Blender. It is not affiliated with, endorsed by, sponsored by, or otherwise approved by Autodesk, Inc. or the Blender Foundation. It contains no Autodesk code, icons, MEL scripts or other Autodesk assets; references to Maya are solely to describe compatibility and the intended audience.

## 이름 결정 (Hermes delegated, 사용자 지시: 인기 제품 패턴)
- 인기 패턴(다운로드 상위·유명 애드온): 짧은 기능명 1~2단어(LoopTools, Bool Tool, F2, BoxCutter, HardOps, Zen UV, Right Mouse Navigation)이고, tagline이 무엇을 하는지 설명한다. 다른 회사 제품명은 tagline에서 "…-style"로만 쓴다(Unreal-style navigation 등).
- **이름: Switchover** (id `switchover`). extensions.blender.org에서 검색해 보니 같은 이름이 없다.
- **tagline: "Maya-style keymap, hotbox and workflow for Maya users"** (53자, 마침표 없음). 이름에는 "Blender"도 "Maya"도 없다.

## 이름 수정 (사용자 10-19: 워크플로우 강조, 이름에 Maya를 넣고 싶다)
- **이름: Switchover for Maya Users**, id `switchover`. Autodesk가 허용하는 'for' 참조 형태다. 우리 이름이 먼저 나오고 Maya는 대상만 가리킨다. URL·id에는 maya를 넣지 않는다.
- **tagline: "The complete Maya workflow, not just a keymap"**

## 최종 이름 (copy-masters 실행 결과, 사용자 요청 '전부 합친 것' 반영)
- **Allset for Maya Users** (id `allset`). tagline: **The whole Maya workflow in Blender, in one install** (50자). 위 Switchover 안은 폐기.
- extensions.blender.org에 같은 이름 없음. 다른 업종에 Allset(음식 픽업 앱)이 있지만 3D 도구와는 분야가 다르다.
