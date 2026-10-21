# Step 130 lane D — docs, manifest, package scan (#40)

## 한 것

- `src/allset/blender_manifest.toml`: `tags = ["User Interface"]` (심사자 요구 5), 권한 `files` = "Your shelves and Maya project
  folders" (앱 템플릿·설정 백업이 없어짐 — 셸프 (`extension_path_user`) 와 사용자의 Maya 프로젝트 폴더 (Documents) 만 씀), 라이선스
  주석에서 테마 XML·스플래시 삭제. `blender --command extension validate src/allset` (4.5, 샌드박스 설정) →
  `Success parsing TOML`.
- `tests/test_step130_package_scan.py` (새): 소스 패키지와 빌드 zip 의 `.py` 를 토큰화해 (주석·문자열 제외) 검사 —
  `exec` / `eval` / `execfile` / `__import__` 호출, `compile(..., 'exec'|'eval'|'single')`, `sys.path` / `sys.modules` /
  `sys.meta_path` / `sys.path_hooks` 접근, `import builtins` / `__builtins__`, `importlib.util` / `machinery`, `rna_xml`,
  `user_disabling`, `remove_on_disable`, `keyconfig_activate`, `save_userpref` (Maya File > Save Preferences 의 연산자 id 문자열
  `ui/menu_map.py` 만 허용), `preferences.<섹션>.<값> =` (별칭 `prefs = context.preferences` 포함, 애드온 prefs 제외) /
  `setattr(preferences.<섹션>...)`, `...themes... =`, `keyconfigs.active =`; `.xml` 파일·`theme` 패키지·`prefs_preset.py` 없음;
  `bl_app_templates` 문자열·`save_homefile`·`user_resource` 없음; manifest tags. 스캐너 자체 시험 (`test_scanner_catches_known_violations`)
  포함. 병합 전 소스 (d2fc205) 에서 40 건 지적 (runner exec/eval/훅, shelf exec, render_settings sys.modules, ic_data execfile, 테마
  rna_xml, switch 의 테마·keyconfig 쓰기, user_disabling, remove_on_disable, panel_menus 의 use_rotate_around_active) — 레인 병합 뒤 0 이어야 한다.
  주의: `ui/shelf.py:60` 의 `user_resource('CONFIG', ...)` (extension_path_user 가 없을 때의 레거시 대체 경로) 도 확장 밖 쓰기로 잡는다 (GitHub #42).
- 문서: `README.md`, `docs/distribution/listing.md`, `docs/distribution/extensions_audit.md` (「첫 심사 결과와 대응」),
  `docs/DISTRIBUTION.md` (머리 요약), `site/index.html` · `site/app.js` · `site/PRODUCT.md` — 테마·앱 템플릿·환경설정 변경·복원
  문구 삭제, 「Recommended setup」 (어두운 회색 테마는 사용자가 Get Extensions 에서 고름, Navigation / Undo Steps 256 / Region Overlap 끔 /
  Only Insert Available) 추가.
- `docs/distribution/review_reply.md` (새): 심사자 답글 초안 (항목별 인용 + 바뀐 것, `<commit>` / `<version>` / `<round-trip test>` 자리).
- `docs/user_decisions.md` 13 (delegated): 사라지는 기능 기록.

## 다시 찍을 것 (찍지 않음, GitHub #41)

킷 Maya 테마 (Studio Grey 회색 UI, 리드 초록 선택, Alt+B 그라디언트) 로 찍힌 미디어. Maya 모드 화면은 모두 테마가 들어 있다.

| 경로 | 내용 |
|---|---|
| `docs/distribution/media/01–09_*.png`, `featured.png` | 스토어 스틸·대표 이미지 (Maya 테마) |
| `docs/distribution/media/10_switch_before.png`, `docs/distribution/marketing/screens/10_switch_before.png` | 일반 Blender 화면이지만 환영 창 문구가 바뀌면 다시 |
| `docs/distribution/marketing/screens/01–09_*.png` | 위 스틸의 원본 |
| `docs/distribution/marketing/clips/00_trailer.mp4`, `01–07_*.mp4` | 스토어 갤러리 영상 (07_switch 는 「keys and colours back」 장면) |
| `docs/distribution/marketing/gif/01–07_*.gif` | README·소셜용 GIF |
| `docs/distribution/marketing/kit/*.png`, `docs/distribution/marketing/key_visual*.png` | README 히어로·소셜 카드·키 비주얼 (Maya 테마 화면 포함; 아이콘은 제외) |
| `site/media/*.jpg/.webp/.mp4/.webm`, `og.png` (아이콘·파비콘 제외) | 사이트 클립·스틸 (`shot-hero`, `shot-menus_shelves`, 클립 5 개, `trailer`) |
| `docs/screenshots/01–07_*.png` | release_check 스크린샷 |

생성기도 테마를 켠다 — 다시 찍기 전에 고칠 것: `tools/marketing/shots.py`, `clips.py`, `scene.py`, `bg_check.py`
(`allset.make_maya` / 테마 적용 호출), `tools/release_shots.py` 확인. 「Maya 회색」 화면을 원하면 촬영 샌드박스에 테마를 따로 깔아야 한다
(어떤 테마를 쓸지 = 사용자 결정; 리스팅에 쓰려면 그 테마의 출처·라이선스 표기).

## 남은 것 (메인 세션)

- 레인 병합 뒤 `python tests/run.py -k step130_package_scan` (zip 빌드 필요) 와 `release_check.py` 의 validate.
- `review_reply.md` / `listing.md` 의 `<commit>`, `<version>`, `<round-trip test>`, 레인 K 주석 (`execfile` 대체 방법) 채우기.
- 레인 C 가 남긴 동작에 맞춰 문구 확인: 환영 창 유지 여부, 레이아웃 append 방식, Save Preferences 메뉴 항목 유지 여부.
