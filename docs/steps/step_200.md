# Step 200 — Blender 5.x test pass 2 (backlog #8, Issue #107)

## 계획

Blindspot NB4: the last full 5.x headless run was step 153 (docs/compat_5x.md:62). Steps 154–199 added
version-sensitive code. Run the full headless suite per version (`ALLSET_SANDBOX=<ver> python tests/run.py --no-build
--blender <exe>`, zip built once by 4.5 — the extension zip is version-independent), at most two Blenders at a time:
5.0.1 + 5.1.2 together, then 5.2.3; then GUI `-k step183,step186,step187` on 5.2.3. Fixes only through
`src/allset/compat.py` (feature checks), tests through `kit` helpers. Results go to a new section in
`docs/compat_5x.md`.
