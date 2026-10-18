# Step 100 — 기본 재질 lambert1 (initialShadingGroup)

backlog 2 (step 98 #6). 근거: `research/maya/screens/audit7/pairs/h01_hypershade_win1.png`, `c03_attribute_editor.png`.

## 계획 (delegated)

mayapy 측정 (`tmp/m100.py`, Maya 2022 factory):

- 새 장면 재질 = lambert1, standardSurface1, particleCloud1; shading group = initialShadingGroup, initialParticleSE.
  `initialShadingGroup.surfaceShader` = lambert1. 새 polyCube 의 shape → initialShadingGroup.
- lambert1: color (0.5, 0.5, 0.5), transparency 0, ambientColor 0, incandescence 0, diffuse 0.8, translucence 0, refractions
  off, refractiveIndex 1.0, refractionLimit 6.
- `MLdeleteUnused` (Delete Unused Nodes) 후에도 lambert1 · standardSurface1 · particleCloud1 남음. 새 lambert = lambert2.
- AE 에 연결된 노드: pCubeShape1 → initialShadingGroup, polyCube1.

결정:

1. **lambert1 = 표시 ID 속성 `maya_kit_default` 가 붙은 Principled 재질 하나** (`operators/material.default_material`), fake user
   (File > Optimize Scene Size / orphan purge 가 지우지 않음 = Delete Unused 가 남기는 것). 이름이 바뀌어도 표시로 찾는다. step 100
   이전 kit 가 만든 「lambert1」 (Assign New Material > Lambert, `maya_kit_type` lambert) 이 있으면 그것을 기본으로 채택; 다른 재질이
   이름을 가졌으면 Blender 접미사를 받고 사용자 이름은 건드리지 않음. standardSurface1 / particleCloud1 / shaderGlow1 은 만들지 않음
   (쓰임 없음).
2. **새 shape 는 lambert1** (MESH, NURBS SURFACE; 커브는 Maya 도 shading group 이 없음): `create.create` 가 직접 넣고, 다른 길
   (Blender Add 메뉴, 복제, 분리, 가져오기) 은 depsgraph 핸들러가 장면 오브젝트 집합을 비교해 새로 생긴 재질 없는 오브젝트에 넣는다.
   load / undo / redo 는 기준만 다시 잡음 (원래 있던 오브젝트는 그대로 — 사용자 파일을 바꾸지 않음). 새 장면 (파일 경로 없음) 을 열면
   lambert1 을 미리 만든다 (Maya 새 장면에 있으므로 Hypershade 에 보임). 모두 `maya_naming` 환경설정을 따름 (Maya 장면 규칙).
3. **새 Lambert = lambert2**: `new_material` 이 먼저 lambert1 을 보장. lambert 기본값 = Base Color 0.5 (Maya color), Emission Color 검정
   (incandescence 0; Principled 기본 흰색이 AE 에 흰색으로 보였음).
4. **Diffuse 0.8 은 표현하지 않음**: Principled 의 「Weight」 소켓은 비활성 (값 0, `inputs.get` 이 None — kit AE 의 Diffuse 행은 원래
   그려지지 않았다). color × diffuse 를 Base Color 에 넣으면 AE 숫자가 Maya 와 달라지므로 Maya 속성값 0.5 를 쓰고, 렌더 알베도가 Maya
   (0.4) 보다 밝은 것은 남은 것으로.
5. **AE**: 재질마다 Maya 처럼 shading group 탭을 재질 앞에 (`SG:i`, 이름 initialShadingGroup / `<재질>SG`, 「Shading Group
   Attributes」: Surface Material = 재질 탭으로 가는 버튼, Volume / Displacement 는 흐린 빈 행). 뷰포트 Solid 색은 재질의 viewport
   색 (기본 0.8) 이라 그대로 — 바꾸지 않음.
6. 면 할당: 재질 슬롯이 없는 메시에 면 재질을 줄 때 나머지 면은 빈 슬롯 대신 lambert1 (Maya: 나머지 면은 initialShadingGroup).

## 한 것

- `operators/material.py`: `default_material`, `is_default`, `shading_group_name`, `give_default`, 새 오브젝트 핸들러
  (`register_handlers` / `unregister_handlers`, `operators/__init__.py` 에서 호출), `new_material` 의 lambert1 보장, lambert 기본값,
  `assign_faces` 의 lambert1 슬롯.
- `operators/create.py`: 생성 직후 `give_default`.
- `ui/attribute_editor.py`: `SG:` 탭 (`tabs`, `tab_target`, `draw_shading_group`).
- 테스트: `tests/test_step100_default_material.py` 6 개. 기존 테스트를 Maya 기준으로 갱신 — step 29 (새 Lambert = lambert2, 면 할당
  슬롯 [lambert1, blinn1], Assign Existing 에 lambert1), step 11 (AE 탭 순서에 standardSurface1SG), step 12 (셸프 Lambert = lambert2),
  step 67 (Hypershade Browser 에 lambert1).

## 검증

- 헤드리스 `python tests/run.py`: **725/725** (step 100 6 개 포함; 측정값: color 0.5, incandescence 0, lambert2, purge 뒤 lambert1 남음,
  AE `SG:0 initialShadingGroup` → `MAT:0 lambert1`, Blender Add 로 만든 큐브도 lambert1, 기존 오브젝트는 그대로).
- GUI 세션 `tmp/s100_session.py` (effective 1.0, Make Blender Maya): 새 장면에 lambert1, pCube1 → lambert1, Hypershade 창 — 콘솔 0.
  나란히 비교 `research/maya/screens/step100/pair_hypershade.png`, `pair_ae_lambert1.png`, `pair_ae_initial_sg.png` 직접 확인:
  Browser 에 lambert1 견본, Property Editor lambert / Color 회색 / Incandescence 검정, AE 탭 pCube1 | pCubeShape1 | initialSh… | lambert1.
- look_compare: pixels 25/34 · viewport 11/12 · scene 3/3 · density 6/6 — step 99 와 같음 (뷰포트 색 변화 없음).
- GUI 전체 **1015/1015** (`gui_step67_render` 의 "구가 아직 재질 없음" 검사를 "lambert1 이고 새 재질은 아님" 으로 갱신), dogfood **47/47** 콘솔 0.

## 남은 것

- Diffuse 0.8 / Ambient Color 행 없음 (Principled 에 대응 입력 없음) — 렌더 알베도 0.5 (Maya 실효 0.4).
- Hypershade 창 모양 (Maya Browser 탭·Material Viewer·Create 목록) 은 backlog 7.
- standardSurface1 / particleCloud1 / shaderGlow1 기본 노드는 만들지 않음.
