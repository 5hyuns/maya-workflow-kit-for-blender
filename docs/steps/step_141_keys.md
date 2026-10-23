# Step 141 레인 KEYS — Ctrl+A 모든 모드, UV dolly, 언두 안내, joint 이름, 필드 기본값

계획: `docs/steps/step_141.md` 1. 이슈 #65 #72 #73, 블라인드스팟 B4 B6 (`docs/steps/step_133_remaining.md:194-198`).

## 한 일

1. **#65 Ctrl+A = AE / Channel Box 전환 (모든 모드)** — `keymap/maya_patches.py` `patch_attribute_editor` + `CTRL_A_MODES`.
   Maya Ctrl+a 는 global 핫키이고 어떤 에디터 컨텍스트도 Ctrl+a 를 따로 묶지 않는다 (`research/maya/hotkeys_default.json`
   hotkeySetup.mel:230; 에디터 컨텍스트의 a 키는 Ctrl 없음). IC 가 Ctrl+A 를 select-all 로 쓰는 3D 모드 키맵 (Mesh, Pose,
   Curve, Armature, Metaball, Lattice, Particle, Curves, Sculpt Curves, Point Cloud, Paint Face Mask, Paint Vertex
   Selection) 과 UV Editor 에서 IC 항목을 빼고 `allset.ae_toggle`. 오브젝트 모드처럼 Ctrl+Shift+A = Select All
   (`<mode>.select_all(SELECT)`, IC 의 해제 대신), Alt+D = Select None: 포즈 = `pose.select_all(DESELECT)` (Maya 에서 joint 는
   오브젝트라 모드가 그대로), 컴포넌트 모드 (Curve / Armature / Metaball / Lattice / Curves / Point Cloud) = `allset.select_none`
   (해제 + 오브젝트 모드, research/maya/interaction.md:75, Mesh 와 같음). IC 4.5 / 5.0 / 5.1 / 5.2 데이터의 Ctrl+A 항목은 같다
   (테스트가 확인). `mapping.py` 행 메모 갱신, `docs/keymap_mapping.md` 재생성 (Ctrl+a 행: Object Mode / Mesh 둘 다 ae_toggle).
2. **B4 UV / Image Editor Alt+RMB dolly** — `operators/view.py` `ALLSET_OT_dolly_2d` (`allset.dolly_2d`): 드래그를 직접 읽어
   (오른쪽 / 위 = 확대, `dolly_zoom_factor` = 3D `dolly_distance` 의 역수, 150 px × UI 배율 = 두 배) 매 이동마다
   `image.view_zoom(factor)` 를 부른다. Blender Zoom Axis 설정 (팩토리 Vertical) 을 읽지 않음. ESC = 시작 배율로. "Image" 키맵의
   IC `image.view_zoom` Alt+RMB 제거 (View2D 의 같은 이벤트는 Image 가 먼저라 shadows 로 선언).
3. **B6 언두 깊이** — 스토어 규칙상 설정을 못 쓰므로 안내만: README Recommended setup 항목 (경로 Edit > Preferences > System >
   Memory & Limits > Undo Steps, 왜 256 인지), 킷 환경설정 패널에 "Recommended setup" 줄 (`preferences.undo_hint`: Undo Steps <
   256 일 때만, 현재 값 표시, 읽기만), 환영 대화상자 마지막 문단 (Tip). `docs/manual_checks.md` step 30 항목을 새 동작으로.
4. **#73 joint 이름** — `operators/joints.taken_joint_names`: 오브젝트가 쓰는 아마추어의 bone 만 센다. 지운 skeleton 의
   armature 데이터는 퍼지 전까지 `bpy.data` 에 사용자 0 으로 남아 joint1 을 막고 있었다. skeletonN 은 원래 오브젝트 이름 기준.
5. **#72 Gravity / Newton** — `operators/create.FIELD_MAGNITUDES`: Gravity 9.8 (Maya -Y = 아래로 부는 Wind, Flow 0), Newton
   -5 (Blender Force 는 음수 = 끌어당김), × step 68 `fx.sim_scale` (maya_unit / Space Scale). Maya 값은 메뉴 option var
   (Maya 설치 `scripts/others/dynSetOptionVars.mel:225,237,268,272,276`) + mayapy 측정 → `research/maya/re/fields_141.md`
   (이 워크트리의 research 복사본에 씀 — 메인 checkout 으로 옮길 것).

## delegated 결정

- Ctrl+A 범위: 3D 모드 + UV Editor. Text / Console / Font / File Browser 는 텍스트식 전체 선택 유지 (Maya Script Editor 도 텍스트
  필드). Graph Editor / Dope Sheet / Outliner / Node Editor / NLA / Sequencer / Clip / Markers 의 Ctrl+A 전체 선택은 이번에 그대로
  (Maya 는 거기서도 AE 지만 Markers 키맵 순서 · 키 선택 습관을 재 봐야 함 → 남은 일). Sculpt Ctrl+A (마스크 파이) 그대로.
- Alt+D: Paint / Particle 모드에는 넣지 않음 (오브젝트 모드로 빠지면 어색).
- 2D dolly 는 가운데 기준 확대 (Blender 팩토리 "Zoom to Mouse Position" 꺼짐과 같음); Maya UV Editor 가 커서 기준인지는 미측정 [U].
- Graph Editor / Dope Sheet Alt+RMB 는 View2D `view2d.zoom` 그대로: keepaspect 가 없는 뷰라 각 축이 자기 드래그로 확대되고
  (가로 = 시간축, 오른쪽 = 확대) Zoom Axis 설정을 읽지 않는다 [I, $S 밖 C 코드 기억]. Node Editor 는 IC Alt+RMB = 링크 떼기
  (`node.move_detach_links_release`) 라 dolly 가 없다 → 남은 일.
- Newton: Maya Newton 가속은 거리에 따라 다르다 (측정 1 유닛 ≈ 1.67, 4 유닛 ≈ 0.67 units/s², attenuation 1). Blender Force 감쇠는
  미터 기준 (1 + d)^-p 라 Maya 의 1/d 를 못 따라가므로 감쇠 없이 세기 5 (Maya magnitude) 만 맞춤.
- 언두 안내 위치: 킷 환경설정 + 환영 대화상자 (Help 메뉴 / 알림은 안 씀). Blender 설정 화면을 여는 버튼은 넣지 않음
  (`screen.userpref_show(section=...)` 가 설정 값을 바꾼다).

## 검증

- `python tests/run.py -k step141_keys` 15/15 (Ctrl+A 각 모드 = ae_toggle 하나 + Ctrl+Shift+A select_all(SELECT) 하나,
  Alt+D, 텍스트 에디터 유지, IC 4 버전 동일, 매핑 행, Image Alt+RMB = dolly_2d, 배율 수학, 언두 안내 README / 앱, joint1 재시작 /
  빈 번호, 필드 세기 · 방향 · Space Scale, 중력 필드 낙하 = nucleus 중력 낙하 (cm -4.5158 / m -4.5158 유닛, 정확히 같음),
  Newton 끌림 2.5 유닛 ± ).
- `python tests/run.py -k step141_keys,keymap,step107,step108,step16,step57,step68,enable_disable,step130,step11_,step18_,step54`
  → 첫 실행 118/120 (test_keymap_maya `_STACKS` 에 새 모드 키맵 없음, step130_no_exec 가 주석의 "exec (" 를 잡음) → 고친 뒤 통과.
- GUI `python tests/gui/run.py -k step141_keys` 6/6: UV Editor 에서 Alt+RMB 오른쪽 120 px → 배율 1.000 → 1.558
  (= 2^(120/(150·1.25))), 왼쪽 240 px → 0.642, 클릭만 = 그대로; Zoom Axis 설정은 Vertical 그대로.
- 전체 헤드리스 `python tests/run.py --no-build`: **1206 passed, 0 failed, 147 files**.

## 남은 일

- Graph Editor / Dope Sheet / Outliner / Node Editor 의 Ctrl+A (Maya 는 global AE) — Markers 키맵 순서 측정 후.
- Node Editor (Hypershade) Alt+RMB dolly, Maya UV Editor dolly 중심 측정.
- 나머지 필드 (Air 4 / Radial 5 / Uniform 5 / Turbulence / Vortex) 의 Maya 세기 (`research/maya/re/fields_141.md` 에 값 있음).
