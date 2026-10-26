# 요약 5 — 애니메이션 특화부터가 맞는가, 그리고 기능 사슬 (2026-10-26)

자세한 내용: `CHAINS.md` (사슬 5개 표, 끊긴 고리 L1–L24, 출처), `ANIM_FOCUS_VERDICT.md` (판정 근거, NURBS 범위, 설계 선택, 순서).

## 판정
**조건부로 맞다 (확신도 70 %).** 단, 새 Maya 기능을 더하는 게 아니라 **이미 있는 리깅·디폼·애니 기능 사이의 끊긴 고리를 이어, 사슬 하나를 엔진까지 Maya 손으로 통하게 하는 일**로 할 때 맞다. 모델링 손 버그는 지금처럼 늘 먼저 고친다.
- 찬성: 근거 수 상위가 리깅·스킨이다(Paint Skin Weights 14, Bind 13, Joints 11, Constraints 11). 강의계획서 9개 모두 스키닝을 다룬다. Blender 사용자도 돈을 내는 빈칸이 리깅 쪽이다(Auto-Rig Pro 70,400+ 판매, Voxel Heat Skinning 13,000+). 본인 경로(모델 → UV → 리그 → 웨이트 → 디폼)와 맞는다. 메뉴는 이미 86 %(리깅) / 78 %(애니)가 동작해서, 남은 비용은 고리 24개에 몰려 있다 [사실].
- 반대: 리거가 가장 회의적이다. Blender 본은 Y축이 고정이고 바인드 행렬이 없어 리그 FBX가 완전히 안 풀릴 수 있다. GN 디포머 성능은 측정한 적이 없다 [U]. Blender가 애니 레이어를 2026년에 만든다. 지금 외부 보고는 모델러에게서 온다.
- 틀렸다는 신호: 1단계 뒤 사슬 ③ dogfood에서 막힘 0·어색함 ≤ 2가 나옴, L11 계획이 2 step 안에 mayapy 왕복을 못 맞춤, 릴리스 4주 뒤 리깅 이슈 0, "직접 리그한다" < 20 %.
- **NURBS**: 커브는 리그 재료로만 깊게 한다(컨트롤 모양·Spline IK·CV 클러스터·Motion Path). 서피스 모델링(Trim·Stitch·Fillet)은 멈춘다. 리본은 낮은 순위이고 B-Bones로 안내한다.

## 사슬 5개 (✔ 동작 · △ 부분 · ✖ 끊김)
```
① 커브 → 컨트롤:   커브✔ → 컨트롤 모양✖L1 → 색△L2 → 오프셋 그룹△L3 → 컨스트레인트△L4 → SDK△L5 → 잠금✔ → S✔ → Graph Editor✔
② 커브 기반:       커브✔ → Spline IK(기존 커브)✖L6 → CV 클러스터✖L7 ┊ Motion Path△L8 → Flow Path✖L9 ┊ Wire✔ ┊ Loft→메시△L10 → 핀△
③ 조인트 → 엔진:   조인트✔ → Orient✔ → Mirror·Label✔ → IK✔ → IK/FK✖L14 → Bind✔ → Paint△L13 → 미러·복사·Prune✔ → Bake△L18 → FBX✖L11 → 다시 가져오기✖L12
④ 디포머 → 교정:   Blend Shape✔ → 인비트윈·조합✖L15 → 가중치 키✖L15b → SDK 구동✖L5 → 포즈 교정✖L16 ┊ Cluster·Lattice·Nonlinear·Wrap·Delta Mush✔ → 순서✖L17
⑤ 애니 → 엔진:     받은 리그△L19·L20 → S✔(Y-up△L23) → Time Slider✔ → Graph Editor✔ → 레이어✔(Blender와 겹칠 위험) → 트레일✖L21 → Playblast✔ → Bake△L18 → 클립△L24 → FBX✖L11
```
**교차점**: L11 리그 FBX(③④⑤가 모두 여기서 끝남), L5 SDK 대상(①④③), L18 Bake(③⑤), L19 쿼터니언 본(⑤).

## 사슬별 끊긴 고리 Top (새로 찾은 것 ★)
| 사슬 | Top 고리 | 크기 |
|---|---|---|
| ③ | L11 리그 FBX 막힘 · ★L18 Bake "Keep unbaked keys"를 끄면 컨스트레인트를 지움 · L13 Paint에서 Q가 안 나감 | L · S · S |
| ⑤ | ★L19 쿼터니언 본(Rigify)은 Rotate 행이 없어 S가 회전을 안 키함 · L23 Translate Y · ★L20 pick walk가 숨은 본으로 들어감 | M · M · S |
| ① | ★L1 커브를 컨트롤 모양으로 바꾸는 명령 없음(`parent -s` 거부) · ★L5 SDK가 셰이프 키·IK 가중치를 못 구동 · ★L4 포즈 모드에서 커브를 함께 못 고름 | M · M · M |
| ④ | ★L17 디포머 순서 바꾸기 없음 · L15 인비트윈·조합 회색 · ★L16 조인트 회전 → 교정 셰이프 경로 없음 | S · M · M |
| ② | ★L7 커브 CV 클러스터가 아무것도 안 움직임 · ★L6 Spline IK가 기존 커브를 못 씀 · ★L8 Motion Path 선택 순서·U 키 | S · S · M |

## 구현 순서
0. **늘 먼저**: 외부 보고된 모델링 손 버그.
1. **S 묶음 (한 step)**: L18, L13, L3, L6, L7, L20, L15b, L24 확인 테스트. 고리마다 "앞 단계 출력 → 다음 단계 입력" 테스트를 붙인다.
2. **사슬 ③의 끝 열기**: L11 리그 FBX(「계획」 + mayapy 왕복 먼저), L12, L14 IK/FK.
3. **사슬 ⑤ 받은 리그**: L19 쿼터니언, L23 Translate Y, L24 Game Exporter 클립.
4. **사슬 ① 컨트롤**: 먼저 설계를 정한다. 권장은 "Maya 손으로 만들고 결과는 본 + Custom Shape"[delegated]. 그다음 L1, L2, L4, L5.
5. **사슬 ④ 교정**: L17, L15, L16, GN 디포머 성능 측정.
6. **사슬 ② 나머지**: L8, L21, L10, L9 (수요 신호가 나오면).

DONE
