"""QA 240 activity C (part 2): seeded random walk, seeds 1..5 x 200 actions (toggle / mode switch / undo / redo /
undo+redo / save+reopen / Maya mode off+on / auto key effect), every invariant checked after every action.

    ALLSET_SANDBOX=qa_c python tests/run.py --no-build -k __none__ --extra tools/qa/qa_toggles_walk.py

Seeds: env QA_C_SEEDS (default "1,2,3,4,5"), length QA_C_STEPS (default 200). A violation is shrunk and written as
tools/qa/repro_c_s<seed>_<n>.py.
"""

import json
import os
import time
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location("qa_c_walk", Path(__file__).resolve().parent / "qa_c_walk.py")
walk = module_from_spec(_spec)
_spec.loader.exec_module(walk)
core = walk.core

SEEDS = [int(s) for s in os.environ.get("QA_C_SEEDS", "1,2,3,4,5").split(",")]
STEPS = int(os.environ.get("QA_C_STEPS", "200"))
BUDGET = 250.0        # tests/run.py kills a file after 300 s
_seen = set()
_all = []


def test_walk():
    t0 = time.time()
    per_seed = []
    for seed in SEEDS:
        if time.time() - t0 > BUDGET * 0.6:
            per_seed.append({"seed": seed, "skipped": "time budget"})
            continue
        acts = walk.random_actions(seed, STEPS)
        ts = time.time()
        run = walk.Run(ignore_known=True)
        found = run.run(acts)
        recs = []
        for i, oracle, msg in found:
            sig = walk.signature(oracle, msg)
            cls = next((k for k in walk.CLASSES if __import__("re").search(k, msg)), sig)   # one finding per root cause
            if cls in _seen:
                continue
            _seen.add(cls)
            left = BUDGET - (time.time() - t0)
            small = walk.shrink(acts[:i + 1], sig, budget_s=min(30.0, max(0.0, left - 60))) if left > 70 else acts[:i + 1]
            name = f"repro_c_s{seed}_{len(_seen)}"
            path = walk.write_repro(name, [list(a) for a in small], sig, msg)
            rec = core.finding(f"C-{core.TAG}-s{seed}-{len(_seen)}", walk.SEVERITY.get(oracle, "S3"),
                               f"tools/qa/{path.name}", oracle, msg)
            rec["actions"] = len(small)
            rec["first_index"] = i
            recs.append(rec)
            core.log("FINDING", seed, i, oracle, msg, "->", path.name, len(small))
        per_seed.append({"seed": seed, "actions": len(acts), "violations": len(found), "known_class_hits": run.known, "unique": len(recs),
                         "findings": recs, "seconds": round(time.time() - ts, 1)})
        _all.extend(recs)
    path = core.OUT / "qa_c.json"
    try:
        allr = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        allr = {}
    allr.setdefault(f"{core.TAG} {core.VERSION}", {})["walk"] = per_seed
    path.write_text(json.dumps(allr, indent=1), encoding="utf-8")


def test_zero_violations():
    assert not _all, f"{len(_all)} unique violation(s): " + " | ".join(f["detail"][:120] for f in _all[:6])
