# Step 38 — Channel Box 다중 선택·상대값 입력, AE 재질 라벨

## 계획 (delegated)

Maya 근거:
- 리드 오브젝트 = 마지막에 고른 것. Channel Box 는 리드의 채널·SHAPES·INPUTS 를 보여 주고, 값을 바꾸면 그 속성이 있는 **선택한
  모든 오브젝트**에 적용한다 (research/maya/channel_box.md:53-57, `channelBoxCommand.mel:16-64` 의 `#P`).
- 필드는 상대 계산을 받는다: `+=5`, `-=2`, `*=2`, `/=2`. 여러 행을 고르고 입력하면 고른 모든 행에 적용 (channel_box.md:134-137).
- Channel Box 숫자는 단위 없이 보인다 (Maya 의 현재 단위 = cm, 각도 = 도).
- AE 재질 탭 이름은 노드 종류다 (`lambert: lambert1`). lambert 는 AElambertTemplate 섹션 (research/maya/attribute_editor.md:137-140,
  research/maya/ae_templates.json `lambert`): Common Material Attributes (열림) / Special Effects / Matte Opacity /
  Raytrace Options / … . blinn·phong 은 lambert 공통 + Specular Shading (열림), surfaceShader 는 Surface Shader Attributes
  (Maya 2022 `AEblinnTemplate.mel:30-39`, `AEphongTemplate.mel:30-33`, `AEsurfaceShaderTemplate.mel:30-34`; research 에는 없음).

지금 상태 (ui/channel_box.py):
- 메인 채널 (Translate/Rotate/Scale/Visibility) 은 이미 Scene 프록시가 모든 선택에 쓴다.
- 사용자 속성·SHAPES·INPUTS 는 리드의 실제 속성을 그려서 리드에만 적용된다 (:649-677).
- 상대값: Blender 숫자 필드는 식을 계산하지만 `+=5` 는 문법 오류다. 필드가 지금 값을 모른다. 입력 문자열을 가로챌 수 없다.

설계:
1. **값 필드 = 문자열 프록시** (delegated). Maya 필드처럼 클릭하면 글자를 고친다.
   - 보이는 값: 표시 단위 숫자 (cm 템플릿 = cm), 단위 글자 없음, 소수 3 자리까지 (뒤 0 은 지움). 각도는 도, 불리언은 on/off.
   - 입력 처리 (`parse_entry`):
     - `+=` / `-=`: 오브젝트마다 자기 값에 더함.
     - `*=` / `/=`: 오브젝트마다 곱함.
     - 그 밖: 절대값. 숫자는 `bpy.utils.units.to_value` 로 읽는다. 단위 없는 숫자는 표시 단위, `5 m`·`5mm`·식 (`2*3`) 도 됨.
       회전은 도 (tmp/probe38 실측).
   - 잘못된 입력은 무시 (값 그대로).
   - 편집한 행이 고른 채널 중 하나면 고른 채널 모두에 적용한다. 아니면 그 행만.
   - 끌기로 값 바꾸기는 Maya 처럼 뷰포트 MMB 가상 슬라이더 (step 6) 로 한다. 필드 Ctrl+휠·드래그는 없어진다.
   - 숫자 float 프록시 (`cb.tx` 등) 는 API·테스트용으로 남긴다.
2. **메인 채널**: `MAYAKIT_PG_channel_box` 에 `<key>_text` 문자열 프록시 10개 (get = 리드, set = 모든 선택). 잠금·autokey 규칙은 지금과 같다.
3. **사용자 속성 / SHAPES / INPUTS**: 행이 오브젝트마다 달라서 `Scene.maya_kit_cb.rows` 컬렉션에 둔다.
   - 행 하나 = (kind, name, mod type, 같은 종류 중 몇 번째) + `text` 프록시.
   - Scene 에 두는 이유: WM 속성을 UI 에서 고치면 언두가 쌓이지 않는다 (WM 은 언두 대상 ID 가 아님).
   - 다시 만드는 때: depsgraph / load_post 핸들러가 리드 시그니처 (리드 이름, 데이터 종류, 사용자 속성, 모디파이어 이름·종류·펼침) 를
     비교해서. 시그니처도 같은 PG 에 둬서 언두 뒤에도 행과 시그니처가 함께 돌아간다. 그리기 때 행이 낡았으면 지금처럼 리드 속성을
     그린다 (안전한 폴백).
   - 적용 대상 (delegated, "같은 이름의 채널"):
     - 사용자 속성: 같은 이름이 있는 선택 오브젝트.
     - SHAPES: 같은 오브젝트 종류의 데이터에 같은 속성이 있으면.
     - INPUTS: 같은 종류 모디파이어 중 같은 순번 (Maya 히스토리 노드 이름은 오브젝트마다 polyCube1/polyCube2 처럼 다르다).
   - 문자열로 그리는 것은 스칼라 INT/FLOAT/BOOLEAN 만. 색 같은 배열은 리드 속성 그대로.
4. **AE 재질**:
   - `operators/material.new_material` 이 `mat["maya_kit_type"]` (lambert / blinn / phong / standardSurface / surfaceShader) 를 남긴다.
   - `attribute_editor.material_type(mat)`: ID 프로퍼티가 있으면 그것. 없으면 Principled → standardSurface, 노드 없음 → material.
     탭 라벨·헤더·섹션이 모두 이 함수를 쓴다.
   - `ae_layout`: LAMBERT (research 템플릿 `lambert` 와 섹션 비교 테스트), BLINN / PHONG (lambert + Specular Shading),
     SURFACE_SHADER. 모두 Principled 소켓에 매핑한다.

검증:
- 헤드리스 `tests/test_step38_channel_box_multi.py`:
  - 표시 형식 (cm·도·on/off), 절대·상대 입력 (`+=`, `-=`, `*=`, `/=`, 단위, 잘못된 입력).
  - 여러 오브젝트에 오브젝트마다 상대 적용, 고른 채널 모두에 적용.
  - 사용자 속성·SHAPES (카메라 lens)·INPUTS (Bevel width) 를 다른 선택에도 적용, 행 다시 만들기·언두.
  - AE 라벨·섹션 (lambert1 → lambert, Common Material Attributes 열림), 템플릿 섹션 비교.
- GUI: Channel Box 다중 선택 상태에서 Translate X 필드에 `+=5` 입력 → 두 오브젝트 모두 +5 cm, 스크린샷.
  AE lambert1 탭 스크린샷.
- 전체 헤드리스·GUI·dogfood.

## 한 것

- `ui/cb_entry.py` (새): 표시·입력 규칙.
  - 표시는 Maya 처럼 단위 없는 숫자다. 길이는 표시 단위, 각도는 도, on/off.
  - 입력: 절대값, `+=`/`-=`/`*=`/`/=`. 단위 있는 값 (`5 m`) 과 식 (`2*3`) 도 받는다.
- `ui/channel_box.py`:
  - 메인 채널 값 필드는 `<key>_text` 문자열 프록시다. `apply_entry` 가 오브젝트마다 자기 값 기준으로 적용한다.
    잠긴 채널은 건너뛰고 autokey 를 지킨다. 고른 채널 중 하나에 입력하면 고른 채널 모두에 적용한다.
  - 사용자 속성·SHAPES·INPUTS 는 `Scene.maya_kit_cb.rows` 행이다. depsgraph/load_post 핸들러가 `rows_sig` 가 다르면
    다시 만들고, 행이 낡았으면 지금처럼 리드 속성을 그린다. 같은 이름 채널에 적용한다:
    - 사용자 속성은 이름이 같은 것.
    - SHAPES 는 같은 오브젝트 종류.
    - INPUTS 는 같은 종류 모디파이어 중 같은 순번.
  - 숫자 float 프록시 (`cb.tx`) 는 API 용으로 남겼다.
- `operators/material.new_material` 이 `mat["maya_kit_type"]` 를 남긴다.
- `ui/attribute_editor.material_type` 이 탭 라벨·헤더·섹션에 쓰인다.
- `ui/ae_layout`: LAMBERT (research `lambert` 템플릿과 섹션 비교), BLINN / PHONG (+ Specular Shading), SURFACE_SHADER.
- delegated 결정:
  - 값 필드를 텍스트로 바꿨다. 필드 드래그 대신 뷰포트 MMB 가상 슬라이더를 쓴다.
  - 행 데이터를 Scene 에 둔다 (WM 은 언두 안 됨).
  - INPUTS 는 종류 + 순번으로 대응한다.
  - Principled 소켓에 대응시켰다: transparency → Alpha (Opacity), incandescence → Emission Color, eccentricity → Roughness.

## 검증

- 헤드리스 `tests/test_step38_channel_box_multi.py` 11/11. 다음을 확인한다:
  - 표시 형식, 절대·상대·잘못된 입력.
  - 두 오브젝트에 오브젝트마다 상대 적용, 고른 채널 모두에 적용, 잠금.
  - 사용자 속성, 카메라 lens (SHAPES), Bevel segments (INPUTS, 이름이 달라도), 행이 리드를 따름.
  - AE 라벨·섹션 5 종, disable 시 핸들러 제거.
  - `test_step11` 의 AE 템플릿 섹션 비교에 lambert 가 추가됐다.
- 전체 헤드리스 **333/333** (36 파일), GUI **277/277** (30 파일), dogfood **47/47**, 콘솔 오류 0.
- GUI `tests/gui/gui_step38_channel_box_multi.py` 5/5:
  - 두 큐브 선택, Translate X 필드에 실제 클릭·입력 `+=5` + Enter 하면 Cube 1 → 6, Cube2 4 → 9.
  - AE 재질 탭 `lambert: lambert1`.
  - 스크린샷 `gui_step38_cb_before/typing/after.png`, `gui_step38_ae_lambert.png` 를 직접 확인했다.
  - dogfood 10 (cm 템플릿): Translate Y "100" = 100 cm.
- `docs/manual_checks.md` Step 38 항목 5개.

## 남은 것

- 언두: 행 편집은 Scene 속성이라 언두 단계가 생겨야 한다. 실제 Ctrl+Z 로 여러 오브젝트가 한 번에 돌아가는지는 수동 확인 항목으로 남겼다.
  헤드리스 `ed.undo` 는 창이 없어 시험하지 않았다.
- Maya 의 필드 색 (키·잠금·연결) 은 지금처럼 오른쪽 아이콘으로 보인다. 텍스트 필드라 Blender 의 키 색칠은 없다.
- 잘못된 입력은 조용히 무시된다. Maya 는 오류를 낸다. Blender 단위 파서가 콘솔에 오류를 찍을 수 있다.
- AE lambert 의 Diffuse (Principled `Weight`) 는 4.5 에서 숨은 소켓이라 그려지지 않는다.
  Incandescence 기본값은 Blender Emission Color 의 흰색이다 (세기 0 이라 보이는 효과는 없음).
- Channel Box 색 배열 (조명 color) 과 열거형은 리드에만 적용된다.
