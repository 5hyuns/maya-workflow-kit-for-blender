# Step 1 — Project skeleton

## 한 것

- `git init`, `.gitignore` (.serena/, .claude/, CLAUDE.local.md, __pycache__, build/, dist/, tmp/ — 테스트 BLENDER_USER_* 샌드박스 포함, *.blend1).
- `CLAUDE.md`, `docs/PLAN.md`, `docs/HANDOFF.md`, `docs/manual_checks.md`.
- Extension 골격 `src/maya_kit/`: `blender_manifest.toml` (id `maya_kit`, 0.1.0, min 4.2.0), `__init__.py` (서브패키지 순서대로 register, 역순 unregister; 레거시용 `bl_info`), `preferences.py` (AddonPreferences), `keymap/` (`add_item` + 정리), `operators/`, `ui/`, `theme/`, `app_template/`.
- `tools/build.py`: `blender --command extension build` 로 `dist/maya_kit-0.1.0.zip`, 레거시 `dist/maya_kit-0.1.0-legacy.zip`. Blender 없으면 zip 폴백.
- `tests/run.py` 하네스: 빌드 → `tmp/test_env/{config,scripts,extensions}` 새로 만들기 → `extension install-file -r user_default` → 테스트 파일마다 `blender -b --factory-startup --python tests/_bootstrap.py` → PASS/FAIL 집계, 실패 시 exit 1.
- `tests/test_enable_disable.py`: 활성화·비활성화 후 상태 스냅샷 비교 (bpy.types, 주요 타입 RNA 프로퍼티·속성, bpy.ops, add-on 키맵, app.handlers, `.append()`된 draw 함수, addons).

## 검증

```
python tests/run.py
PASS  test_enable_disable::test_enable_registers_preferences
PASS  test_enable_disable::test_disable_restores_baseline
PASS  test_enable_disable::test_enable_disable_cycles
PASS  test_enable_disable::test_snapshot_detects_leaks
4 passed, 0 failed, 1 file(s)
```

- `test_snapshot_detects_leaks`는 일부러 Scene 프로퍼티·키맵 항목·핸들러를 새게 해서 스냅샷이 잡는지 확인한다 (헛통과 방지).
- `%APPDATA%/Blender Foundation/Blender/4.5/config/userpref.blend` 수정 시각 2026-03-05 그대로 (테스트가 사용자 설정을 건드리지 않음).

## 결정 (delegated)

- 테스트 프로세스는 파일 단위 분리 (상태 오염 방지, 1초 내외).
- 확장 설치는 실제 사용자 경로와 같은 `extension install-file` 로 빌드된 zip을 검증. 활성화는 `addon_utils.enable(handle_error=raise)` 로 오류를 숨기지 않음.
- `blender --command` 는 stdin 을 물려받으면 멈춘다 → 하네스·빌드 모두 `stdin=DEVNULL`.
- `research/` 는 git에 넣지 않았다: `maya/*.json` 에 Maya MEL 추출 텍스트가 있어 decision 6 (Maya 자료를 저장소에 복사하지 않음)과 충돌. 로컬 참고 자료로 유지.
- 환경설정 옵션(Maya 단위, 부모 지정 모드, 레이아웃 설치)은 해당 기능 단계에서 추가 (지금 넣으면 동작 없는 옵션).

## 남은 것

- 레거시 zip 실제 설치 테스트는 Step 15.
- GUI 확인 없음 (UI 없음).
