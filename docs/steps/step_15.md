# Step 15 — Smooth Mesh Preview 를 history 에서 분리 + 매끈한 셰이딩

재점검 1차 B1 (`docs/steps/step_14.md`) 과 dogfood 의 각진 스무스 프리뷰 (shots/04).

## 계획

근거: Maya 1/2/3 은 shape 의 표시 속성일 뿐 지오메트리를 바꾸지 않는다 (research/maya/interaction.md:170-174
"per-shape display attribute and does not change geometry"). History(construction history = 업스트림 노드,
research/maya/concepts.md:64-74)에 들어가지 않는다.

1. **프리뷰 모디파이어만 다룸** (task 지시): `preview_modifier` 가 "첫 Subsurf" 대신 이름이
   `PREVIEW_MOD_NAME` 인 모디파이어만 찾는다. 사용자 Subsurf(예: polySmooth1)는 1/2/3 이 건드리지 않는다.
   사용자 Subsurf 가 있는 객체에서 3 → 그 위에 프리뷰가 한 번 더 (Maya 에서도 polySmooth 노드 + 스무스 프리뷰는 겹침).
   Step 4 의 "사용자 Subsurf 재사용" 동작과 테스트는 이번에 뒤집는다.
2. **Delete History / Non-Deformer History 가 프리뷰를 굽지 않음**: `history._bake` 의 `keep` 에 프리뷰 모디파이어를
   넣는다 (평가 때 꺼 두고 굽고 난 뒤 그대로 남김). 프리뷰만 있는 객체는 "history 없음" 으로 건너뜀.
3. **매끈한 셰이딩 (delegated)**: 조사한 선택지
   - (a) 메시 `shade_smooth` — 메시 데이터(sharp_face)를 바꾼다. 1 로 되돌릴 때 원래 값을 기억해야 하고 Delete History 후에도 남아
     "표시 전용" 원칙에 어긋남 → 탈락.
   - (b) Subsurf 의 `use_custom_normals` — 메시에 커스텀 노멀이 있을 때 보간만 함, 평평한 면은 그대로 → 효과 없음.
   - (c) 프리뷰 Subsurf 뒤에 "Set Shade Smooth" 지오메트리 노드 모디파이어 — Subsurf 가 마지막이 아니게 되어
     Blender 의 GPU 서브디비전이 꺼진다 (Subsurf 가 스택 마지막일 때만 GPU 평가) → 느려짐.
   - (d) **프리뷰 Subsurf 바로 앞에** "Set Shade Smooth" 지오메트리 노드 모디파이어 (`PREVIEW_SHADE_NAME`, 노드 그룹
     `.MayaKit Smooth Preview Shading` — `.` 으로 시작해 메뉴에서 숨김). Subsurf 는 입력의 sharp_face 를 이어받으므로 결과가
     매끈하고, Subsurf 가 마지막이라 GPU 서브디비전 유지. 메시 데이터 그대로. **선택.**
   두 모디파이어는 함께 켜고 끄고(show_viewport), 렌더에는 영향 없음(show_render False), Delete History 도 둘 다 남긴다.
   사용자가 프리뷰 뒤에 모디파이어를 추가하면 GPU 서브디비전만 꺼질 뿐 결과는 같음.
4. **INPUTS 에서 숨김**: Maya 스무스 프리뷰는 Channel Box INPUTS·AE history 탭에 노드로 나오지 않는다 (shape 의 표시 속성,
   AE shape 탭 "Smooth Mesh" 섹션). 셰이딩 모디파이어가 하나 더 생기므로 둘 다 CB INPUTS 와 AE 탭 목록에서 빼고,
   AE "Smooth Mesh" 섹션이 프리뷰 모디파이어의 레벨을 보여 준다 (delegated).

검증: 헤드리스 (3 → Delete History → 정점 수·모디파이어 그대로; Non-Deformer 도; 사용자 Subsurf + 1 → 사용자 것 show_viewport 유지;
3 의 평가 메시 면이 모두 smooth; 원본 메시 sharp_face 그대로), `python tests/run.py` 전체, `python tests/gui/run.py`,
`python tools/dogfood.py` 의 04_smooth_preview.png 를 직접 확인.

## 한 것

- `operators/display.py`: `is_preview()`, `PREVIEW_SHADE_NAME`, 노드 그룹 `.MayaKit Smooth Preview Shading`
  (Group Input → Set Shade Smooth → Group Output). `preview_modifier` 는 이름이 `Maya Smooth Preview` 인 Subsurf 만 찾고,
  만들거나 다시 켤 때 셰이딩 모디파이어를 바로 앞에 둔다 (4.5 에 `ObjectModifiers.move` 가 없어
  `object.modifier_move_to_index` 를 object override 로 — 0.1.0 파일의 셰이딩 없는 프리뷰도 고쳐짐).
  1/2/3 은 두 프리뷰 모디파이어의 `show_viewport` 만 바꾼다. 사용자 Subsurf 는 건드리지 않음 (Step 4 동작 뒤집음, delegated).
- `operators/history.py`: Delete History / Non-Deformer History 가 프리뷰 모디파이어를 `keep` 에 넣어 굽지 않고 남김;
  프리뷰만 있으면 history 없음으로 건너뜀; Non-Deformer 의 "deformer 뒤 모디파이어" 알림에서 프리뷰 제외.
- `ui/channel_box.py` INPUTS, `ui/attribute_editor.py` 탭 목록에서 프리뷰 모디파이어 제외; AE shape 탭 "Smooth Mesh" 섹션이
  프리뷰 Subsurf 의 레벨을 보여 줌.
- 테스트: `tests/test_step15_smooth_preview.py` 8개 (매끈한 평가 메시 + 원본 메시 그대로, Subsurf 마지막 유지·구 파일 보정,
  편집 모드, Delete History 두 종류, 사용자 Subsurf 는 구워짐, 프리뷰만 = history 없음, AE 탭 제외).
  `tests/test_step4_view.py` 의 재사용 테스트를 "사용자 Subsurf 는 1 에도 켜진 채" 로 바꿈.
- `tools/dogfood_session.py`: 3 후 평가 메시 smooth 체크, Alt+Shift+D 후 정점 8개·프리뷰 유지 체크 추가.

## 검증

- `python tests/run.py` → `196 passed, 0 failed, 15 file(s)` (step 14 의 188 + 새 8).
- `python tests/gui/run.py` → `115 passed, 0 failed, 10 file(s)`.
- `python tools/dogfood.py` → 새 체크 2개 포함 45개 중 37 통과; 실패 8개는 step 14 와 같은 아직 없는 키·복제 이름 (backlog 2, 5);
  콘솔 오류 0줄. `tmp/dogfood/shots/04_smooth_preview.png` 직접 확인: 각진 면 없이 매끈함. 09: Channel Box 에 INPUTS 섹션 없음
  (프리뷰만 있는 객체).
- GPU 서브디비전이 실제로 켜지는지는 헤드리스로 확인 불가 (Subsurf 가 스택 마지막인지만 테스트) → manual_checks.

## 남은 것

- Maya 스무스 프리뷰는 하드 엣지를 유지하는 옵션(Keep Hard Edges 등)이 있으나 여기서는 전부 매끈하게 (delegated, [K]).
- PgUp/PgDn 레벨 ±, `0` 기본 품질 → backlog 2 (키 묶음).
- 사용자가 프리뷰 뒤에 모디파이어를 추가하면 GPU 서브디비전이 꺼짐 (결과는 같음).
