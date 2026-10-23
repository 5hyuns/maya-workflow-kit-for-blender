# Step 138 — 레인 FILEIO: FBX / OBJ / Alembic / USD 왕복 (#69)

계획: `docs/steps/step_138.md` 「계획」 파일 왕복. 근거: `step_133_work.md` I1–I4, 측정 방법 `research/maya/re/file_io.md` §2, 이번 측정 §4.

## 한 것

`src/allset/operators/file_io.py` — 변환 (Y up · cm) 을 채널에 감싸 두지 않고 **켤레로** 넣는다: 변환 M → C M C⁻¹, 점 p → C p
(카메라 · 라이트는 시선 축 때문에 C M S⁻¹). 그래서 Maya 와 킷이 같은 채널 숫자를 읽는다.

| 형식 | 내보내기 (kit → Maya) | 가져오기 (Maya → kit) |
|---|---|---|
| FBX | `bake_space_transform`, NLA strip / all actions 끔 (strip 없으면 애니메이션이 안 써졌음) | `bake_space_transform`, `anim_offset` 0 (Maya 1 프레임 = Blender 1 프레임) |
| OBJ | 쓴 뒤 `o 이름` 밑에 `g 이름` 추가 (Maya 는 g 로 이름) | `use_split_groups`, 오브젝트 행렬 (= 변환 전체) 을 메시로 |
| Alembic | 내보내는 동안만 모든 오브젝트 delta scale 1/s, 부모 역행렬 S·PI, 메시 끝에 Geometry Nodes ×s (`_AbcMayaScale`, 끝나면 원래대로) → 루트 S W S⁻¹ | 루트의 scale k 를 메시로, Transform Cache 컨스트레인트 → 장면 범위 매 프레임 키 |
| USD | `root_prim_path=""`, `merge_parent_xform`, `convert_world_material` 끔 → pxr 로 다시 씀 (`usd_maya_axes`: Y up, metersPerUnit 0.01, 모든 xform 켤레 + translate/rotateXYZ/scale, 점 · 노멀 · extent 변환, Blender 4.5 가 Xform 으로 쓴 병합 메시 prim → Mesh) | 스테이지 up / metersPerUnit 으로 C 를 구해 메시로, Transform Cache → 키, 재질 Scope 빈 오브젝트 (`Looks`, `_materials`) 삭제 |

공통 가져오기 뒤처리 `maya_names`: 이름 충돌 `.001` → Maya 식 번호 증가 (pCube1.001 → pCube2, lambert1.001 → lambert2), 메시 이름이
`Mesh` / 오브젝트 이름 / 파일 이름이면 Maya 셰이프 이름 (pCubeShape1). 피벗 (`delta_location`) 은 건드리지 않음.

delegated:
- 킷은 Z up 이고 Channel Box 는 Blender 축을 보여 주므로 Maya translate (1, 2, 3) / rotate Y 28.6 = 킷 (1, −3, 2) / rotate Z 28.6 을 "같은 값" 으로 본다.
- Alembic / USD 가져오기의 Transform Cache 는 키로 굽는다 (Maya 는 AlembicNode 연결, 킷 Channel Box 는 키 색) — 채널에 변환이 안 남게.
- USD 파일 단위는 항상 Maya cm (metersPerUnit 0.01) + Maya 단위 숫자 (결정 8: Maya 1 = 표시 단위 1, OBJ / Alembic 과 같음).
- FBX 는 step 102 대로 단위를 파일에 실음: factory m 장면의 1 m 는 Maya 100 cm (다른 형식은 1 Maya 단위). 바꾸지 않음.
- pxr 이 없거나 Skel prim / usdz 면 Blender 자체 변환으로 다시 씀 (top prim 에 rotate X −90 / scale 100 이 남음). Alembic 은 아마추어 · 컨스트레인트 · 커브 등이 있으면 Blender 의 루트 스케일 그대로.

## 검증

mayapy: `research/scripts/file_io_138_mayapy.py` (MAYA_APP_DIR = worktree `tmp/fio138/mayaapp`). Maya pCube1 = polyCube 1×1×1, t (1,2,3), r (0,28.6,0), tx 키 1@1 / 5@10.
표의 t / r / s 는 각 프로그램 채널 (킷 = 표시 단위 cm, Blender 축), "10" = 10 프레임 tx.

### kit → Maya (cm 장면, Maya 에서 읽은 값)

| 형식 | 전 | 후 | Maya → Maya 기준 |
|---|---|---|---|
| FBX | t (1,2,3) r (**−90**,28.6,0) s **100**, 애니 0 (10: 1) | t (1,2,3) r (0,28.6,0) s 1, 애니 1 (10: 5), pCube1Shape, lambert2 / pCube1SG | 같음 |
| OBJ | 이름 **Mesh** / MeshShape | **pCube1** / pCube1Shape, t 0 (점 world), SG kit_cube138_lambert1 | pCube1 / pCube1Shape, t 0 |
| Alembic | t (1,2,3) r (0,28.6,0) s **100** | s 1, pCubeShape1, 10: 5 | 같음 |
| USD | **root** (rx −90, s 100) > pCube1 (0.01,−0.03,0.02) > pCubeShape1 > pCubeShape1Shape (+ env_light 노드는 Maya 가 읽지 않음) | pCube1 하나, t (1,2,3) r (0,28.6,0) s 1, pCube1Shape, SG lambert2 / shader Principled_BSDF, 10: 1 | pCube1, 10: 1 (Maya 도 USD 애니 안 읽음) |

계층 (`kit_cube138_h`, group1 t (0,4,0) r Y 30 밑 pCube1 local (1,2,3) r Y 28.6): FBX / Alembic / USD 모두 Maya 에서 group1 (0,4,0) ry 30, pCube1 (1,2,3) ry 28.6, s 1.
factory m 장면 (`kit_cube138_m`): OBJ / Alembic / USD = 위와 같은 숫자, FBX = t (100,200,300) s 1 (단위를 실음).

### Maya → kit (cm 장면, 킷 Channel Box)

| 형식 | 전 | 후 |
|---|---|---|
| FBX | t (1,−3,2) r (**90**,0,28.6) s **0.01**, 메시 **Mesh**, 10: **4.556** (한 프레임 늦음), lambert1.001 | t (1,−3,2) r (0,0,28.6) s 1, pCube1 / pCubeShape1, 10: 5, lambert2 |
| OBJ | 이름 **maya_cube138** (파일 이름), r (90,0,0) s 0.01 | pCube1 / pCubeShape1, t 0 r 0 s 1, 재질 initialShadingGroup |
| Alembic | s **0.01**, Transform Cache | t (1,−3,2) r (0,0,28.6) s 1, 키 10: 5 |
| USD | r (**90**,0,28.6) s **0.01**, 메시 이름 pCube1, **Looks** 빈 오브젝트 | t (1,−3,2) r (0,0,28.6) s 1, pCubeShape1, 키 10: 5, Looks 없음 |

kit → kit (cm / m 장면 둘 다): 네 형식 모두 오브젝트 1 개, 위 값 그대로 (전: OBJ r 90 s 0.01, USD `_materials` + 오브젝트 이름 pCubeShape1, FBX 애니 없음).

### 테스트

- `tests/test_step138_file_io.py` 9 개: 측정 (kit_*.json + mayapy 용 파일), kit 왕복 cm / m × 4 형식, OBJ `g` 줄, USD 스테이지 (Y up, mpu 0.01, `/pCube1` Mesh, ops, 키), Alembic 내보내기 뒤 장면 그대로, 계층 왕복 FBX / ABC / USD, 이름 규칙, 프리셋, Maya 가 쓴 파일 4 개.
- `tests/test_step102_file_io.py`: USD 프리셋 기대값만 바꿈 (변환은 이제 쓴 뒤).
- `python tests/run.py -k step138,step102,step21,enable_disable,step130` → 45 passed, 0 failed (8 files). 전체 헤드리스: 아래 남은 것 위 줄 참고.

## 남은 것

- USD → Maya 재질: SG 이름은 재질 (lambert1 → 충돌로 lambert2), 셰이더 노드는 Blender 셰이더 prim 이름 `Principled_BSDF`. prim 이름 바꾸기 (Sdf namespace edit) 는 안 함.
- FBX 빈 오브젝트 (group1) 는 Maya 에서 locator 셰이프가 붙음 (Blender FBX Null). Maya 그룹은 셰이프 없는 transform.
- USD / Alembic 카메라 · 라이트 · 커브 · 스켈레톤 · 변형 메시 (Mesh Sequence Cache / 아마추어) 는 측정 안 함: 아마추어 · 시퀀스 캐시는 리더의 world 행렬을 그대로 둠 (채널에 변환이 남을 수 있음), USD 카메라 조리개 단위는 안 바꿈.
- 셰이프 이름 규칙: Maya 의 FBX / OBJ / USD 리더는 `pCube1Shape`, 킷은 Maya 생성 규칙 `pCubeShape1` (요청대로).
