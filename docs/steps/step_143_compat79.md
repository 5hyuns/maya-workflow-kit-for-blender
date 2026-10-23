# Step 143 (compat): issue #79 — Blender 5.2.3에서 Maya 모드 전환 실패

## 증상

GitHub #79 "Cant get it to work in Blender 5.2.3 LTS": Maya 모드로 전환하면

```
switch._apply_pending → set_mode → register_mode → ui/__init__.register
→ ui/render_settings.register → wrap_panels → render_panels
→ sorted(out, key=registration_key)
→ seq = list(_module_names(cls).get("classes", ()) or ())
TypeError: 'module' object is not iterable
```

모드 모듈 등록이 중간에 멈춰 이후 `allset.new_maya_scene` 같은 연산자가 없다는 오류가 반복된다.

## 원인

`registration_key` (step 105)는 Render 패널을 등록 순서대로 다시 등록하려고, 패널 클래스를 정의한 모듈의
전역 `classes`를 순서 목록으로 읽는다. 이 값이 tuple/list라고 가정했다.

- 공식 Blender 5.2.3 포터블 (`blender-5.2.3-windows-x64.zip`, sha256 723f08a4…dc2fb = download.blender.org
  공식값)을 `--factory-startup`으로 띄워 Properties > Render 패널 전체를 검사: `classes`가 tuple/list가
  아닌 모듈은 **없음** (5.2.2도 동일). 즉 Blender 자체 변경이 아니다.
- 따라서 신고자 환경의 **서드파티 애드온**이 Render 탭에 패널을 두고, 그 모듈의 전역 `classes`가 서브모듈
  (`from . import classes` 같은 패키지 구조)인 경우다. `list(module)` → "'module' object is not iterable".
  버전 5.2.3은 우연이고, 같은 애드온이면 4.5에서도 똑같이 실패한다.

## 수정

`src/allset/ui/render_settings.py`: `_class_order(cls)` 추가 — `classes`가 tuple/list일 때만 그 순서를 쓰고,
그 밖의 값(모듈, dict, 제너레이터, 문자열, None, 숫자 ...)은 빈 목록으로 취급(= 그 모듈 안에서 순서 0, 애드온
패널은 Blender 패널 뒤 `(1, 0, module, index)`). tuple/list인 경우의 키는 step 105와 완전히 같다
(4.5 동작 불변). compat.py 대상 아님: 버전 차이가 아니라 서드파티 데이터 방어이므로.

## 검증

`tests/test_step143_compat79.py`
- `classes`가 모듈 / 42 / None / dict / 제너레이터 / 문자열 / object인 가짜 패널: 예외 없음, 키
  `(1, 0, module, 0)`; 정상 tuple은 그 순서 유지; bl_ui `properties_output` 패널의 키 = step 105 공식 그대로;
  혼합 정렬에서 bl_ui 패널이 먼저.
- 끝단 경로: `classes`가 모듈인 가짜 서드파티 Render 패널을 등록한 뒤 `kit.enable()`
  (`switch.set_mode(True)`) → Maya 모드 켜짐, 패널이 wrap되고 RENDER_PT_context 뒤, disable 후 원래 poll 복귀.
- 수정 전 코드로 돌리면 두 테스트 모두 `TypeError: 'module' object is not iterable` (이슈와 같은 오류)로 실패.

`python tests/run.py -k step143,step105,step118,enable_disable`

| Blender | 결과 |
|---|---|
| 4.5.4 LTS | 22 passed, 0 failed |
| 5.2.2 (`ALLSET_SANDBOX=s522`) | 22 passed, 0 failed |
| 5.2.3 LTS (`ALLSET_SANDBOX=s523`, 새로 받은 공식 포터블) | 22 passed, 0 failed |

5.2.3 포터블: `C:/Users/ohnsk/AppData/Local/allset_blenders/blender-5.2.3-windows-x64/`.

## 남은 일

- 신고자에게 어떤 애드온이었는지는 확인 못 함 (애드온 목록을 물어보면 재현 데이터로 남길 수 있다).
