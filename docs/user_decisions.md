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
    1 cm 큐브가 1 m 물체처럼 떨어진다 (떨어지는 시간 √(L/g) 가 같음). kit 의 FX 생성 경로 (step 65) 는 Maya 사용자가 보는 움직임을 따른다:
    중력 = 9.8 × `maya_unit()` / Space Scale m/s² (kit "Space Scale" 기본 1 = Maya 와 같은 뜻, 0.01 이면 실제 크기), 충돌 거리·마진·
    파티클 크기·속도·Mantaflow 도메인 = Maya 값 × `maya_unit()`; 필드·이펙터 크기는 step 54. 장면 중력은 전역이라 Blender 의 Physics
    탭으로 직접 만든 시뮬레이션도 줄어든 중력을 받지만 길이 기본값은 미터 그대로다 (안내). 기하 크기 (결정 8) 와 조명 감쇠 계산은 그대로
    (조명 세기는 × `maya_unit()²`, 태양광 제외, step 54). Bullet 의 절대 임계값과 1 cm 안정성, Y-up → Z-up 중력 방향은 step 65 에서 잰다.
    결정 8 의 "물리·라이트 감쇠는 실제 크기 1 cm" 는 시뮬레이션에 한해 이 결정으로 바뀐다.
