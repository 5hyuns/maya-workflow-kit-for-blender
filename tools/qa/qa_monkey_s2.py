"""QA 240 activity D: seeded monkey, seed 2 (~700 actions, capped at ~200 s by tests/run.py's 300 s file limit).

    ALLSET_SANDBOX=qa_d python tests/run.py --no-build -k __none__ --extra tools/qa/qa_monkey.py,tools/qa/qa_monkey_s2.py,tools/qa/qa_monkey_s3.py

Engine and exclusion list: tools/qa/qa_d_core.py. Output: tmp/qa240/qa_d.json, tmp/qa240/findings.jsonl,
repros tools/qa/repro_d_<seed>_<index>.py.
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location("qa_d_core", Path(__file__).resolve().parent / "qa_d_core.py")
core = module_from_spec(_spec)
_spec.loader.exec_module(core)
RES = {}


def test_monkey():
    RES.update(core.run_seed(2))


def test_no_kit_exceptions():
    bad = [f for f in RES.get("findings", []) if f["severity"] != "S4"]
    assert not bad, " | ".join(f["detail"][:150] for f in bad[:5])
