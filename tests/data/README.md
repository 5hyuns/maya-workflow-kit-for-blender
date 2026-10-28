A place for measured Maya numbers that tests compare against, kept in git so a fresh clone can run those comparisons.

Tests look a file up with `kit.maya_data("maya", "re", "<name>.json")`: here first (`tests/data/maya/re/<name>.json`),
then in the maintainer's local `research/` folder. In a clone that has neither, those tests report SKIP, not FAIL.

Only numeric results belong here (positions, weights, values) — no Maya scripts, icons or documentation text.
