Measured Maya numbers that tests compare against, kept in git so a fresh clone can run them.

Tests look a file up with `kit.maya_data("maya", "re", "<name>.json")`: here first (`tests/data/maya/re/<name>.json`),
then in the maintainer's local `research/` folder. When neither has it, the test is reported as SKIP, not FAIL.

Only numeric results go here (positions, weights, values) — no Maya scripts, icons or documentation text.
