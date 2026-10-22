# Step 137 레인 DEFAULTS — Maya 재질 / 조명 / Render Settings 기본값 (#71)

계획: `step_137.md` 「계획」 결정 (#71). Maya 값: `research/maya/re/render_defaults_137.md` (mayapy + Maya Software 렌더 측정,
step 133 `m07_mat.json` · `m04_scene.json` 포함).

## 한 것

- **재질** (`operators/material.py` MATERIALS): lambert 계열 전부 (lambert, blinn, phong, phongE, anisotropic) Color 0.5 ·
  Incandescence 검정 (Principled 기본 Emission Color 흰색이 AE 에 흰색으로 보이던 것) · specularColor 0.5 (Specular Tint).
  Blinn Specular Roll Off 0.7 (= Specular IOR Level, AE 행 그대로). rampShader / layeredShader 도 Incandescence 검정.
  standardSurface specularRoughness 0.4 (측정; aiStandardSurface 는 측정 못 해 그대로). diffuse 0.8 은 step 100 규칙대로 색에 안 곱함.
- **Eccentricity / Cosine Power** (delegated): `Material.allset_eccentricity` / `allset_cosine_power` = Principled Roughness 를
  읽고 쓰는 get/set 속성 (저장 값 없음). Blinn 하이라이트 = Trowbridge-Reitz, c3 = eccentricity = GGX alpha → Roughness = √e
  (0.3 → 0.548); Phong n ↔ alpha = √(2/(n+2)) → Roughness = (2/(n+2))^¼ (20 → 0.549). AE / Hypershade Property Editor 는 새 행
  종류 `("maya", 속성, 라벨, 소켓)` (`ui/ae_layout.py`, `ui/attribute_editor.draw_row`) 로 0.3 / 20 을 보인다 (맵 버튼은 소켓에).
- **조명** (새 `operators/lights.py`, `create._scale_data`): `Light.allset_intensity` (Maya intensity, 파워에서 읽고 씀) ·
  `Light.allset_decay` (No Decay / Linear / Quadratic / Cubic, ID 속성 `allset_decay_rate`). 새 point / spot / area 조명 = intensity 1,
  No Decay. 측정 (Maya Software: 값 = color × diffuse × I / d^n; Blender: 점 조명 a·P/(4π²r²), 해 a·S/π, 면 a·P/(π²r²) 원거리;
  Light Falloff 노드는 Cycles 만, EEVEE 는 무시) 에서 정한 규칙 (k = maya_unit, 10 단위에서 맞춤, delegated):
  - point / spot: 파워 = 4π² k² I 10^(2−n). Cycles: No Decay = Light Falloff Constant × (10k)⁻², Linear = Linear × (10k)⁻¹
    (모든 거리에서 정확), Quadratic = Blender 그대로 (정확), Cubic = Blender 법칙 + 10 단위 맞춤 (알림).
  - area: 파워 = π² · 9.87 · k² I / 10^n (Maya 면 조명도 원거리 1/d², No Decay 는 모든 엔진에서 모양 일치; 나머지는 10 단위 맞춤).
  - directional: 세기 = π · I (전에는 1 = Maya 0.32).
  - step 54 의 × maya_unit² 는 그대로 (식 안에 k²). EEVEE / 뷰포트는 늘 거리 제곱 = 10 단위에서 Maya 와 같다.
  - Maya 기본: spot cone 40° · penumbra 0, area 2 × 2 단위 (delegated [K]).
  - AE: Intensity 행 = `allset_intensity`, Decay Rate 행 = 드롭다운 + 툴팁 알림 (`lights.decay_notice`); Light Editor Intensity
    열도 Maya intensity. 5.1+ 는 조명마다 노드 트리가 있고 `use_nodes` 가 deprecated → `compat.ensure_light_nodes` /
    `release_light_nodes` (`LIGHT_ALWAYS_NODES`).
- **Render Settings 960 × 540** (100 %, pixel aspect 1): `tools/make_startup.py` `MAYA_RESOLUTION` → `startup.blend` 재생성.
  새 Maya 장면 (`first_start.new_maya_scene`, Ctrl+N) 은 이 파일을 읽으므로 따로 고칠 곳 없음; `render_settings.DEFAULTS` 는 이미 HD 540.
- 테스트: 새 `tests/test_step137_defaults.py` (10), `tests/gui/gui_step137_defaults.py`. 옛 값을 박은 테스트만 고침: step 54 (조명
  파워 10 W·k² → 새 규칙, 해 π), step 67 (Decay Rate 가 missing 행 → 실제 행, Light Editor energy → allset_intensity),
  step 21 (area 크기 1 → 2 단위). `tests/kit.py` 스냅샷에 Material / Light 속성 추가 (enable/disable 누수 검사).

## 검증

- `python tests/run.py -k step137,step100,step105,step54,step67,step29,step49,enable_disable,step130,step21,step38,step129_material,step131_hyper`:
  110 passed, 0 failed (16 파일). `test_step137_defaults` 10/10 — Cycles 렌더에서 새 점 조명이 10 · 40 단위 모두 0.5 ± 0.02
  (색 0.5 = Maya color × diffuse × I), EEVEE 10 단위 0.5 ± 0.02.
- 5.x: `ALLSET_SANDBOX=... tests/run.py --blender <5.2.2 / 5.0.1> -k step137,enable_disable` 각 14 passed, 0 failed.
- 전체 헤드리스 `python tests/run.py`: 1067 passed, 3 failed (133 파일) — 실패 3 개 (test_keymap_maya, step107_keys,
  step108_menu_hotkeys) 는 worktree 에 `research/` 가 없어서; 임시 junction 으로 다시 돌려 30 passed, 0 failed (junction 제거함).
- GUI `python tests/gui/run.py -k step131_hypershade,step105,step67,step137`: 29 passed, 0 failed (4 파일). 그림
  `gui_step137_blinn_ae.png` (blinn1 AE: Color 회색, Incandescence 검정, Eccentricity 0.300, Specular Roll Off 0.700, Specular Color 회색),
  `gui_step137_light_ae.png` (pointLightShape1: Intensity 1.000, Decay Rate No Decay + 알림 아이콘) — 눈으로 확인.

## 남은 것

- Channel Box SHAPES 의 조명 행은 여전히 Blender `energy` ("Power") — Maya 는 intensity. 애니메이션 키 (get/set 속성) 검증이 필요해 손대지 않음.
- Volume Light 는 Blender 에 없음 (기존 알림 그대로). ambientLight 도.
- anisotropic spreadX / spreadY (13 / 3) 는 Blender Anisotropic 0.5 그대로 (변환 규칙 없음). reflectivity 0.5 (레이트레이스 반사) 행 없음.
- diffuse 0.8 은 Principled 에 입력이 없어 렌더가 Maya 보다 1.25 배 밝다 (step 100 결정 그대로).
- maya_unit 이 바뀌면 (Maya Units 설정) 기존 조명의 파워 · falloff 세기는 다시 계산하지 않음 (intensity 값이 바뀌어 보임).
- 렌더 엔진이 EEVEE 면 No Decay / Linear 는 10 단위에서만 맞는다 (EEVEE 는 조명 노드를 무시, 측정).
