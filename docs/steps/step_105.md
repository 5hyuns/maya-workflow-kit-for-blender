# Step 105 — Hypershade, Render Settings, Script Editor look

Backlog 7 of audit 7 (step_98.md #31–#33; PLAN 「재점검 7차」 7).

## 계획

Evidence: the three windows captured in a Maya 2022 GUI with step 104's method (`research/scripts/maya_editors105/`,
`research/maya/screens/editors105/_editors105.json`): Hypershade menu bar File / Edit / View / Create / Tabs / Graph /
Window / Options / Help (255 items, Create = 160 node types), Browser tabs Materials / Textures / Utilities / Rendering /
Lights / Cameras / Shading Groups / Bake Sets / Projects / Asset Nodes; Render Settings Edit / Presets / Help (21) with
the factory values HD 540 = 960 × 540, PNG, frames 1–10 step 1, padding 4, single frame, and its image size preset
list; Script Editor File / Edit / History / Command / Tabs / Help (52). The menu data joins `ui/editor_menu_data.py`
(`tools/gen_editor_menu_data.py` reads both captures), so step 101 / 104 rules (mapped or noticed) apply.

1. **Hypershade** (`ui/hypershade.py`): Maya menu bar in every Shader Editor header through
   `NODE_MT_editor_menus.draw_collapsible` (the step 37 pattern; Blender's menus in a 「Blender」 menu, the slot / New
   buttons stay). Browser = swatch tabs (WindowManager enum) as a preview grid: Materials (previews), Textures (image
   / texture nodes in materials), Utilities (other non-shader nodes), Rendering (worlds), Lights, Cameras, Shading
   Groups (`<mat>SG` / initialShadingGroup); View menu swatch size / sort order are WM properties the grid reads.
   Create = Maya's surface shaders Blender can build, Maya order: Anisotropic, Blinn, Lambert, Layered Shader, Phong,
   Phong E, Ramp Shader, Standard Surface, Surface Shader, Use Background (new kinds in `operators/material.py`:
   Principled stand-ins plus Layer Weight → Color Ramp, Mix Shader, Holdout; AE sections in `ae_layout`). Create menu
   textures / utilities add the matching Blender node to the current material's graph (`maya_kit.hs_node`).
   Property Editor = AE sections of the picked material (step 67), kept.
2. **Render Settings** (`ui/render_settings.py`): `maya_kit.render_settings` opens a Properties window marked as the
   kit's (window / space pointers, like the Light Editor) with only the Render tab, Maya menu bar in its header,
   panel 1 = Render Layer (view layer) + Render Using (engine) + tabs Common | <engine>. Common = Maya's sections
   over `scene.render`: Path / File name / Image size lines, File Output (file name prefix, image format,
   Frame/Animation ext, frame padding — all written into `render.filepath` / `image_settings`), Frame Range,
   Renderable Cameras, Image Size (Maya presets incl. HD 540 960 × 540, width / height / pixel aspect). The fields
   are Scene properties with get / set on `scene.render` (UI edits push undo). The renderer tab = Blender's own Render
   panels; in the Common tab they are hidden by wrapping their poll (the `ui/dock_tabs.py` technique, only in the
   marked window). Presets > Import Render Settings > Default Settings = Maya's factory values.
3. **Script Editor** (`ui/script_editor.py`, replaces `command_line.MAYAKIT_OT_script_editor`): a new window split
   into history (Info editor: Blender's report log = Maya's echo of commands and results) over input (Text Editor)
   with tabs MEL / Python (texts `MEL` / `Python`; the header draws them as tabs). Maya menu bar + icon row in the
   Info header (`INFO_MT_editor_menus.draw_collapsible`), Ctrl+Enter / numpad Enter = Execute
   (`maya_kit.script_run`: the Python tab runs through the command line runner with `cmds`, the command and result
   are echoed as reports; MEL tab = Maya-style warning, decision 5). Keymap items first in "Text", pass through
   outside the kit window.

Verification: headless `tests/test_step105_maya_windows.py` (Common fields write `scene.render`, presets, menus vs
capture, new material kinds, script run / echo), GUI `tests/gui/gui_step105_windows.py` with shots beside audit-7
pairs h01 / h03 / h05.

## 한 것

- **Maya 측정** (`research/scripts/maya_editors105/`, Maya 2022 GUI): Hypershade 메뉴 9 (잎 249, Create 160 노드 종류),
  Browser 탭 10, Render Settings 메뉴 3 (21) + 공장값 (960 × 540, PNG = imageFormat 32, 1–10, padding 4, 단일 프레임) 과
  이미지 크기 프리셋 목록, Script Editor 메뉴 6 (59). `tools/gen_editor_menu_data.py` 가 두 캡처를 읽어
  `ui/editor_menu_data.py` (7 편집기, 48 메뉴, 914 잎).
- **Hypershade** (`ui/hypershade.py` 다시 씀): Shader Editor 헤더에 Maya 메뉴 막대 (`NODE_MT_editor_menus.draw_collapsible`,
  슬롯 / New 는 그대로, Blender 메뉴는 「Blender」), Browser = 탭 7 (Materials / Textures / Utilities / Rendering / Lights /
  Cameras / Shading Groups) 의 견본 격자 (View 메뉴의 견본 크기·정렬·역순 = WM 속성), 클릭 = 재질 선택 / 라이트·카메라 선택 /
  노드 표시 / 월드. Create = Maya 순서 10 종 (Anisotropic, Blinn, Lambert, Layered Shader, Phong, Phong E, Ramp Shader,
  Standard Surface, Surface Shader, Use Background; 새 종류 = `operators/material.py` Principled + Layer Weight→Color Ramp /
  Mix Shader / Holdout, AE 절은 `ae_layout`). Create 메뉴 텍스처·유틸리티 50 종 = 현재 재질 그래프에 대응 노드
  (`maya_kit.hs_node`), Edit 명령 (`maya_kit.hs_edit`: Delete, Delete Unused Nodes — lambert1 유지, Select Objects with
  Materials, Select Materials from Objects, Duplicate). 매핑 111/249, 회색 138 모두 안내.
- **Render Settings** (`ui/render_settings.py`): 표시한 Properties 창 (Render 탭만), 헤더 = Maya 메뉴, Render Layer / Render
  Using 줄, 탭 Common | <엔진 이름>. Common = Path / File name / Image size 줄 + Color Management, File Output (경로, 파일
  이름 접두사, 이미지 형식, Frame/Animation ext 4 종, 자릿수 → 모두 `render.filepath` / `image_settings`), Frame Range,
  Renderable Cameras, Image Size (Maya 프리셋 19 종, HD 540, 픽셀 비율). 필드 = Scene get/set 속성 (UI 편집 = 언두).
  엔진 탭 = Blender 렌더 패널; Common 탭에서는 그 창에서만 poll 래핑으로 숨김 (RENDER_PT_context 는 늘 숨김 — Render
  Using 줄이 대신). Presets > Import Render Settings > Default Settings = Maya 공장값 (`maya_kit.rs_defaults`).
- **Script Editor** (`ui/script_editor.py`): 새 창을 가로로 나눠 위 = Info (기록), 아래 = Text Editor (입력), 탭 MEL /
  Python / + (텍스트에 `maya_kit_script_lang`). Info 헤더 = Maya 메뉴 + 아이콘 줄 (열기·저장, 기록 / 입력 / 모두 지우기,
  실행), Text 헤더 = 탭 + Execute. `maya_kit.script_run` = 선택 또는 탭 전체를 command line runner 로 (cmds, bpy, C, D;
  마지막 식 = `# Result:`), 명령과 결과를 보고로 남겨 기록 창에 보임; MEL 탭 = Maya 식 오류 (결정 5). Ctrl+Enter (입력 유지)
  / 숫자패드 Enter (지움) 를 "Text" 맨 앞에. 매핑 32/59.
- **키맵**: IC 의 Ctrl+Enter = `render.render` 가 "Screen Editing" (편집기 키맵보다 먼저 보는 창 키맵) 에 있어 Script Editor 의
  Ctrl+Enter 가 렌더가 됨 (--debug-handlers 로 측정) → 제거 (Maya 에 Ctrl+Enter 렌더 없음, delegated).
- **고친 함정 2**: (1) 렌더 패널을 다시 등록하면 Properties 의 패널 순서가 바뀜 (EEVEE Motion Blur 가 Sampling 위로) →
  등록 순서 (`bl_ui._modules` + 모듈 `classes` 튜플) 로 다시 등록; (2) 템플릿 로드로 애드온이 다시 켜질 때 Cycles 가 먼저
  내린 패널을 kit 가 되올려 Cycles register 가 "already registered" 로 실패 → 주인 없이 내려간 클래스는 poll 만 되돌림.
- Blender 픽셀 비율 칸은 1 부터: Maya 0.9 (CCIR 601) = 1 : 1/0.9.

## 검증

- 헤드리스 `tests/test_step105_maya_windows.py` 8/8 (메뉴 막대 = 캡처, 잎 329 안내 없는 회색 0, Common 필드 → `render.filepath`
  / 해상도 / 픽셀 비율, Default Settings = 960 × 540 PNG 단일, 경로 왕복, 패널 숨김이 kit 창에서만, Create 10 종 노드 구성,
  Browser 탭·정렬, Delete Unused 가 lambert1 유지, Script 실행 / MEL 거절 / 선택 텍스트, 헤더 교체). 헤드리스 전체 777/777.
- GUI `tests/gui/gui_step105_windows.py` 7/7 (Hypershade 창 + 탭, Render Settings 표시 창, Script Editor 위 기록 / 아래 입력,
  Ctrl+Enter 로 `cmds.polySphere()` 실행 → pSphere1, 입력 유지). 나란히 그림 `research/maya/screens/step105/`
  (h01 / h03 / h03 renderer / h05 `_pair.png`). EEVEE 패널 순서가 Blender 기본과 같음을 그림으로 확인. GUI 전체 1048/1048 (step 7 의 「Script Editor = Python Console」 확인을 새 창 구성으로 바꿈).

## 남은 것

- Hypershade 는 여전히 Shader Editor + 사이드바: Maya 의 Browser 위 / Create 왼쪽 / Property Editor 오른쪽 배치와 Material
  Viewer (큰 미리보기) 는 없음 (사이드바 한 줄), 좁은 사이드바에서 탭 이름이 잘림. Tabs / Bins / Asset Nodes / Bake Sets 없음.
- 새 장면의 렌더 크기는 여전히 Blender 기본 1920 × 1080 (Maya 는 HD 540): 템플릿 기본값을 바꿀지 아직 안 정함 — Presets >
  Default Settings 로 맞춤. Maya 의 렌더 Frame Range (1–10) 는 Time Slider 범위와 따로지만 Blender 는 하나.
- Script Editor: History 메뉴 (Echo All Commands 등) 는 회색 안내, 문법 강조는 Python 기준 (MEL 탭은 실행 안 함), Source Script
  없음.
- 다음: step 106 Tool Settings 와 Attribute Editor (step_98.md #20–#22).
