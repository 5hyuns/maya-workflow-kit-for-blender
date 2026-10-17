# Step 68 — FX: Maya 시뮬레이션 스케일 · nucleus · nParticles 이미터 · nCloth · nCache

근거: `research/maya/workflows/fx.md` (§3 갭 표: 스케일 20, Create Emitter 15, nucleus 12, Emit from Object 12, nCloth 9, nCache 9, 강체 9;
§4 개념 결정 1–3, 6; §5 후보 1–2), 결정 10 (`docs/user_decisions.md:29-36`), PLAN W4, mayapy 측정 (step 48: nucleus `spaceScale` 1.0,
gravity 9.8, 방향 (0, −1, 0), substeps 3), shots fx_01–02.

## 계획

### 측정 (`tmp/exp68/*.py`, `blender -b --factory-startup`, 1 m 장면 (k = 1, 중력 9.81) vs 1 cm 장면 (k = 0.01))

| 시뮬 | 1 cm 장면에서 바꾼 것 | 결과 (길이 / k) |
|---|---|---|
| 레거시 파티클 (점 이미터, 30 프레임) | 중력 × k, 속도·크기 × k | 최저 z −7.750 vs −7.750, 평균 −6.634 vs −6.634 — **완전히 같음** |
| 천 (한쪽 고정, 30 프레임) | 중력 × k, 충돌 거리 × k | 늘어짐 −0.944 vs 기준 −0.705 (덜 뻣뻣) |
| 〃 | + 강성 × k | **−0.703** (기준 −0.705) |
| 〃 | + 강성 × k² / 감쇠 × k / 질량 ÷ k | −0.899 / −0.708 / −0.313 |
| 천 + 상자 콜라이더 (40 프레임) | 중력·거리·두께·강성 × k | 기준과 다름 (혼돈적 접촉: 기준은 미끄러져 떨어짐) — [U] 접촉 모양은 근사 |
| 〃 | 충돌 거리 그대로 (0.015 m) | 천이 15 유닛 위에 뜸 (1 cm 평면이 "뜸") |
| 강체 (상자 → 바닥, 100 프레임) | 중력 × k, 마진·비활성 속도 × k | z 1.967 / 0.5 / 0.5 / 0.5 — **같음** (마진 그대로여도 같음) |

→ 규칙 (delegated, 결정 10 구체화): 시뮬레이션 배율 `g = maya_unit() / Space Scale`.
- 중력 = 9.8 × g m/s² (nucleus 값), 방향 = Maya 축 (0, −1, 0) → Blender (X→X, Y→Z, Z→−Y, step 57 규칙).
- 길이 (천 충돌 거리 / 자기 충돌 거리, 콜라이더 두께, 파티클 크기·속도, 강체 마진·비활성 속도) × `maya_unit()`.
- 천 강성 (tension / compression / shear / bending) × g — 중력이 g 배면 Blender 천 스프링은 크기와 무관한 힘이라 강성도 g 배여야 같은 늘어짐
  (측정). Space Scale 이 바뀌면 이미 만든 천도 다시 맞춘다 (오브젝트 ID 속성 `maya_kit_cloth_g` = 적용된 g).
- substeps: Maya 3 = Blender 기본 (천 quality 5, 강체 substeps 10) → quality = round(5·s/3), 강체 = round(10·s/3).

### 설계 (모두 delegated)

1. **`Scene.maya_kit_nucleus`** (`operators/fx.py`): gravity 9.8, gravity_direction (Maya 축) (0, −1, 0), space_scale 1.0, substeps 3, `exists`.
   값이 바뀌면 `apply(scene)` → `scene.gravity`, 강체 월드 substeps, 모든 천 quality·강성. kit FX 생성 연산자가 처음 쓰면 `exists` = True + apply
   (Maya 가 첫 nObject 에서 nucleus1 을 만드는 것과 같음, fx_01 로그). 그 전엔 장면 중력을 건드리지 않음.
2. **AE 「nucleus1」 탭**: nucleus 가 있고 오브젝트에 천 / 파티클 / 콜라이더 / 강체가 있으면 탭 하나 더 (키 `NUC`). 섹션 = Maya nucleus 템플릿 이름
   (Gravity and Wind / Solver Attributes / Scale Attributes) [K], 안내 행 「Blender 에는 nucleus 노드가 없어 장면 중력·강체 월드·각 천에 나눠 씁니다」.
3. **nParticles > Create Emitter** = `maya_kit.fx_emitter`: 원점에 정점 하나 메시 `emitter1` (렌더 숨김) + 파티클 시스템 `nParticle1`
   (VERT 방출, Maya omni: 방향 무작위 속도 1 유닛/s = `factor_random` × maya_unit, rate 100/s = 재생 범위 동안 count, 수명 = 범위 끝까지,
   표시 점, 크기 0.05 × maya_unit, 캐시 범위 = 재생 범위). Emit from Object = `maya_kit.fx_emit_from_object`: 선택 메시 전부에 같은 설정.
4. **nCloth > Create nCloth** = `maya_kit.fx_ncloth` (선택 메시 전부, 모디파이어 `nCloth1`…), Create Passive Collider = `maya_kit.fx_passive`
   (COLLISION, 두께 × maya_unit), Remove nCloth = `maya_kit.fx_remove_ncloth`. 강체 Active / Passive = `maya_kit.fx_rigid` (선택 전부, 마진 · 비활성 속도).
5. **nCache** = `maya_kit.ncache(action, kind)`: Create New Cache > nObject = 선택 (없으면 장면 전부) 의 포인트 캐시 굽기 (천 · 파티클 · 소프트바디 ·
   선택에 강체가 있으면 강체 월드) + 지오메트리 노드 시뮬레이션 존 굽기, > Maya Fluid = Mantaflow 도메인 `fluid.bake_all`; Delete Cache = 각각 지우기.
   셸프 FX Caching 의 같은 버튼도 이 연산자.
6. 안내 (`notices`): Create Emitter (점 메시), nCloth (Maya 단위 스케일), Enable/Disable All Caches (Blender 는 구운 캐시를 늘 씀).

범위 밖 (PLAN 「남긴 것」): 3D 유체 컨테이너 (선택 없이), MASH (menus.json 에 없음), Bifrost, nConstraint, "frame change too large" 경고.

검증: 헤드리스 `tests/test_step68_fx.py` (스케일 수식, 만든 노드 · 이름 · 값, 파티클 낙하가 1 m 장면 / 0.01 과 같음, nucleus 적용 · 강성 재조정,
캐시 굽기 / 지우기, 메뉴 · 셸프 매핑), GUI `tests/gui/gui_step68_fx.py` (MayaKit 템플릿: F5 → Create Emitter → 1 초 → 파티클이 Maya 처럼 ≈4.9 유닛 낙하
→ 바닥 평면 Passive + 1 유닛 평면 nCloth → 2 초 → 바닥에 닿음 (1.5 유닛 위에 뜨지 않음)), dogfood.

## 한 것

- `operators/fx.py`: `Scene.maya_kit_nucleus` (Gravity 9.8, Gravity Direction Maya 축 (0, −1, 0), Space Scale 1, Substeps 3; 값을 바꾸면 `apply`)
  → `scene.gravity` = 9.8 × g (g = maya_unit / Space Scale), 강체 월드 substeps, 모든 천 quality·강성 (Space Scale 이 바뀌면 `maya_kit_cloth_g` 로 재조정).
  kit FX 연산자가 처음 쓰면 nucleus 생성 (그 전엔 장면 중력 그대로).
- Create Emitter = `maya_kit.fx_emitter` (`emitter1` 점 메시 렌더 숨김 + `nParticle1`: VERT, omni 속도 1 유닛/s, rate 100/s × 재생 범위,
  끝까지 생존, 점 표시, 크기·표시 크기 × maya_unit), Emit from Object = `fx_emit_from_object` (선택 메시 전부),
  Create nCloth / Passive / Remove = `fx_ncloth` / `fx_passive` / `fx_remove_ncloth` (선택 전부, 이름 `nCloth1` / `nRigid1`),
  강체 Active / Passive = `fx_rigid` (선택 전부, 마진·비활성 속도 × maya_unit), nCache = `maya_kit.ncache` (선택 없으면 장면 전체;
  포인트 캐시 + 강체 월드 + GN 시뮬레이션 존 / Mantaflow 도메인; 굽기·지우기).
- 메뉴 (`menu_map`): nParticles Create Emitter / Emit from Object (Legacy 절 `#2` 도), nCloth 3 개, nCache Create New Cache > nObject / Maya Fluid,
  Delete Cache, Fields/Solvers Interactive Playback · 강체. 셸프: Emitter / Add Emitter / Create Passive / Create nCloth / Remove nCloth /
  FX Caching 캐시 버튼 (예전 `particle_system_add`, `ptcache.bake_all` 매핑 교체 — fx.md:54-57 의 "잘못 붙은 Emitter").
- 안내 (`notices`): Create Emitter (점 메시), Create nCloth (Maya 단위 스케일 + nucleus), Enable / Disable All Caches (구운 캐시는 늘 재생).
- AE 「nucleus1」 탭 (`ae_layout.NUCLEUS`: Gravity and Wind / Ground Plane / Solver Attributes / Scale Attributes, 없는 속성은 회색 행 + 안내 글).
- `chrome.paragraph`: 백그라운드에서 `ui_scale` 이 0 → 1 로 처리.

측정으로 추가로 안 것 (계획 표 외):
- Blender RNA 하한 0.001 m: 천 충돌 거리 · 자기 충돌 거리, 콜라이더 두께, 파티클 크기 → cm 템플릿에서 0.1 유닛으로 잘림 (Maya nCloth thickness 기본 0.1 [K] 과 같은 값).
  GUI: 1 유닛 천이 바닥 위 0.17–0.19 유닛에 멈춤 (예전 0.015 m 면 1.5 유닛 위).
- 파티클 `display_size` 기본 0.1 m 도 스케일해야 함 — 안 하면 뷰포트 점이 10 유닛 공으로 그려짐 (GUI 스크린샷에서 발견).

## 검증

- 헤드리스 `tests/test_step68_fx.py` 10/10 (수식, 이미터 노드·이름·값, cm 장면과 m 장면 파티클 낙하가 Maya 단위로 같음 (≈4.9 유닛), Emit from Object 2 개,
  nCloth 2 개 + Space Scale / Substeps / 방향 → 중력·강성·품질, Remove, 천이 Passive 바닥에 닿음, 강체 2 개, 캐시 굽기 (선택만 / 전체) · 지우기 · 유체 없음 CANCELLED,
  AE nucleus1 탭, 메뉴·셸프 매핑). `test_step11` AE 행 검사에 nucleus 소유자 추가. 전체 헤드리스 560/560.
- GUI `tests/gui/gui_step68_fx.py` 8/8 (MayaKit 템플릿: F5 → Create Emitter → Alt+V 재생 → 1 초에 가장 오래된 파티클 −4.96 유닛 → Passive 바닥 + nCloth →
  2 초 → 바닥 위 0.17–0.19 → AE nucleus1), 스크린샷 `gui_step68_particles.png`, `gui_step68_ncloth.png` 직접 확인. GUI 전체 ui 0.8: 470/470.
- dogfood 47/47, 콘솔 오류 0. `docs/manual_checks.md` 「Step 68」 6 항목.

## 남은 것

- 천 접촉 모양은 1 m 장면과 근사 (혼돈적; 매달린 천 늘어짐만 측정으로 일치). Maya 에서 같은 장면 낙하 시간 실측은 아직 [U].
- 파티클이 Passive 콜라이더에 부딪히는지 (Maya nParticle 은 부딪힘) 확인·조정 안 함; nucleus Use Plane (바닥) 은 안내만.
- 필드를 선택 오브젝트에 연결 (Maya Assign to Selected), Gravity 필드 = 장면 중력 안내, "frame change too large" 경고: 안 함.
- 범위 밖 (PLAN 「남긴 것」): 선택 없이 3D 유체 컨테이너, MASH (menus.json 에 없음), Bifrost, nConstraint, nHair.
