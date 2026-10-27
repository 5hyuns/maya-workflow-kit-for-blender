# Step 229 — Release prep 0.5.0

Steps 192–228 + PR #125 (@cnzim). 사용자 10-26 밤: 단계마다 미룬 검사를 여기서 한 번에 — 헤드리스 전체 (4.5 / 5.x), GUI 전체
(`ALLSET_GUI_FULL=1`), release_check 4.5.4 / 5.2.2, dogfood, look_compare; 실패는 그 파일만 `-k` 로 다시, 원인은 git bisect.

## 한 것

- origin/master 에 사용자가 올린 e09bbb0 (docs/strategy 를 공개 저장소에서 뺌) 와 로컬이 갈라져 있어 **merge** (911bc44, rebase 안 함:
  step 문서가 인용하는 커밋 해시 유지). 로컬 커밋 중 docs/strategy 를 바꾼 것 없음 → 새로 공개되는 전략 문서 없음.
- CHANGELOG `[0.5.0] — 2026-10-27` (Added 25 / Changed 10 / Fixed 9, PR #125 @cnzim), `docs/distribution/release_notes_0.5.0.md`.

### 전체 실행에서 나온 것 (고침)

- **Blender 5.2.3 크래시** (`test_step214_lights`, 3 번 중 2 번): step 214 의 Ambient Light / World 동기화가
  depsgraph_update_post 안에서 World·노드 트리·`scene.world` 를 만들고 지움 → 다음 relations build 에서 `std::bad_alloc`
  (DepsgraphNodeBuilder). 동기화는 0 s 타이머로 (`maya_lights._queue` / `flush`), 프레임 변경은 값 (라이트 energy, 있는 ambient 색)
  만 바로 씀 (렌더 작업은 프레임 사이에 타이머를 안 돌림). 이후 3 / 3 크래시 없음.
- **Blender 5.0.1 크래시** (`test_step213_component` / `step218_paint` / `step224_paint`): 5.0.1 은 메시 에지를 스스로 계산할 때
  (`from_pydata` 에지 없이, `update(calc_edges=True)`) `.select_edge` 를 BOOLEAN 이 아닌 INT32_2D 로 만듦 (킷 없이 재현) → Python 의
  `MeshEdge.select` 쓰기 / weight paint 나가기 (`mesh_select_vert_flush`) 가 크래시. `compat.repair_selection_attributes` /
  `compat.mesh_from_pydata` (기능 검사, 버전 검사 아님) 로 고치고 `weight_paint.set_vertex_selection` 과 loft 메시 (`surfaces_maya`)
  가 씀. 사용자 기능 손실 없음.
- **Modify > Reorder Rotation…** (`allset.reorder_rotation`, 방향 유지: Python 의 `rotation_mode` 쓰기는 값을 다시 해석만 함 —
  측정) 와 **Paint Attributes Tool** (= weight paint) 연결 → Modify 58 / 97 → 60 / 97.
- step 219 (Maya 2026 메뉴) 이후 안 돌린 테스트들: Paint Membership 경로 (옵션 창 `paint_weights_membership` 도 고침), Light Linking
  하위 메뉴, ViewCube 라벨, Deform 비율은 Maya Muscle 70 항목을 빼고 셈 (62 / 74, 안내는 계속 검사, delegated), Display 메뉴 Grid
  행 위치 (34 → 9 px, 샷으로 잼), Animation Editors 에서 Trax Editor 행 (3 → 6), Booleans "Difference (A - B)".
- 다른 단계 이후 낡은 검사: 5.x 의 `Bone.select` 없음 → 킷 shim, 5.x 새 셰이프 키 값 1.0, float32 허용치, step 211 숨은 시작
  카메라 (step138 / step81), PR #125 의 상시 창 모달 두 개 (step18 / 129 / 139 — transform 모달만 "움직임"), step 214 Maya Color
  소켓 (step129 material), step 226 SDK 탄젠트 (M62-3), step 209 Reference Editor 창 (M69-5), step 208 이름 규칙 blinn6 (step29).
- `test_step125_name` 허용 목록에 장면 밖 헬퍼 컬렉션 3 개. 테스트 러너가 `TEST <name>` 을 찍어 크래시 위치를 보여 줌.
- M59-4 (pivot ring 이 오브젝트를 돌림): git bisect v0.4.1..HEAD — 모든 커밋에서 그 단계만 돌리면 PASS (전체 sweep 순서에서만 실패) →
  커밋 원인 없음.
- `gui_step134_selection` 101k 정점 캐시 다시 만들기 36 → 73 ms: git bisect = 2e8dcde (PR #125, 살아 있는 edit BMesh 에서 읽어
  하이라이트가 선택보다 늦지 않게 — 유지자가 받아들인 동작). 프레임 그리기는 그대로 (~2.7 ms) → 테스트 한도 60 → 90 ms (delegated).

## 검증

- 헤드리스 전체: 4.5.4 2302 / 2308 → 실패 6 개 고친 뒤 그 파일 -k 통과; 5.2.3 2286 / 2301 → 15 개 고친 뒤 -k 통과 (step214_lights
  크래시 3 / 3 없음); 5.0.1 2271 / 2274 → 크래시 3 개 고친 뒤 39 / 39; 5.1.2 2308 / 2310 — 남은 2 = step 214 Cycles 렌더
  (`test_step214_lights` ambient / volume, bf4aa49 에서도 같음 = 5.1 만, release notes 알려진 한계).
- GUI 전체 (`ALLSET_GUI_FULL=1`, 4.5): 2132 / 2159 (206 파일, GUI_SKIP 2) → 실패 14 파일 고친 뒤 -k: 419 / 420 + 44 / 44, step134 13 / 13.
- release_check 4.5.4 (validate PASS, 설치·해제·Remove 모두 PASS, docs/screenshots 7 장 다시 찍음 — 01 확인) / 5.2.2 (--no-shots,
  모두 PASS). dogfood 48 / 48, 콘솔 오류 0. look_compare 검사 9 / 9, 킷 그림 색 12 / 12, 뷰포트 20 / 20 (ΔE00 5), rects 5 / 12 (기록).

## 남은 것

- Blender 5.1 Cycles 의 Maya Ambient / Volume light (Light Path 출력이 world / light 셰이더에서 다름) — 5.2 에서는 맞음.
- M59-4 는 전체 sweep 순서에서만 한 번 실패 (단독·재실행 PASS) — 순서 의존 여부는 다음 GUI 전체 때 다시 봄.
- 열린 채로 둔 이슈: #89 Quad Draw 나머지, #123 FX / Render, #124 첫 1 시간, #127 Maya 2027 Skin Tools, #108 (고정).
