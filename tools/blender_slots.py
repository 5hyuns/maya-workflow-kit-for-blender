"""Machine-wide Blender slots: at most ``SLOTS`` Blender processes from this repository's harnesses at once.

The PC crashed three times on 2026-10-23 with several Blenders (+ Maya) running together (user decision 10-25:
lanes may go up to 4, Blender processes stay at 2). Every harness that starts a Blender (tests/run.py,
tests/gui/run.py, tools/release_check.py, tools/build.py) holds one slot while that process runs:

    with blender_slots.slot("tests/run.py install"):
        subprocess.run([blender, ...])

A slot is a file lock (msvcrt byte lock on Windows, fcntl elsewhere) on ``slot<i>.lock`` in a folder outside the
repository (``%LOCALAPPDATA%/allset_blender_slots``), so worktrees and several repository copies share it. The OS
drops the lock when the holding process dies, so a killed run never leaves a slot taken.

Environment: ``ALLSET_BLENDER_SLOTS`` = slot count (default 2); ``ALLSET_NO_SLOTS=1`` skips the lock (a Blender that
a test starts from inside an already slotted Blender, or a run that must not wait).
"""

import contextlib
import os
import sys
import time
from pathlib import Path

SLOTS = max(1, int(os.environ.get("ALLSET_BLENDER_SLOTS", "2")))
POLL = 0.5          # seconds between tries while every slot is taken
NOTE_AFTER = 5.0    # print one "waiting" line after this long


def folder():
    base = os.environ.get("LOCALAPPDATA") or os.path.join(Path.home(), ".cache")
    d = Path(base) / "allset_blender_slots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _try_lock(fh):
    """Lock the first byte of ``fh`` without waiting; True when this process now holds it."""
    try:
        if sys.platform == "win32":
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _unlock(fh):
    try:
        if sys.platform == "win32":
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


def acquire(label="", timeout=None):
    """Wait for a free slot; returns (index, open file) — pass it to ``release``. ``timeout`` (s): raise TimeoutError."""
    d = folder()
    start = time.monotonic()
    noted = False
    while True:
        for i in range(SLOTS):
            fh = open(d / f"slot{i}.lock", "a+b")
            if _try_lock(fh):
                fh.seek(0)
                fh.truncate()
                fh.write(f"{os.getpid()} {label}\n".encode("utf-8", "replace"))
                fh.flush()
                return i, fh
            fh.close()
        waited = time.monotonic() - start
        if timeout is not None and waited > timeout:
            raise TimeoutError(f"no free Blender slot after {waited:.0f} s ({d})")
        if not noted and waited > NOTE_AFTER:
            print(f"blender_slots: all {SLOTS} Blender slots are taken, waiting ({label})", flush=True)
            noted = True
        time.sleep(POLL)


def release(held):
    if held is None:
        return
    _i, fh = held
    _unlock(fh)
    fh.close()


@contextlib.contextmanager
def slot(label="", timeout=None):
    """Hold one Blender slot for the ``with`` block (nothing when ``ALLSET_NO_SLOTS=1``)."""
    if os.environ.get("ALLSET_NO_SLOTS") == "1":
        yield None
        return
    held = acquire(label, timeout)
    try:
        yield held[0]
    finally:
        release(held)


def holders():
    """{slot index: "pid label"} of the slots taken right now (diagnostics)."""
    out = {}
    for i in range(SLOTS):
        p = folder() / f"slot{i}.lock"
        if not p.exists():
            continue
        with open(p, "a+b") as fh:
            if _try_lock(fh):
                _unlock(fh)
                continue
        try:
            out[i] = p.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            out[i] = "?"
    return out


def _selftest():
    """Three processes that each hold a slot 1.5 s: never more than SLOTS at once, the third waits."""
    import subprocess
    import tempfile
    log = Path(tempfile.mkdtemp()) / "spans.txt"
    code = "\n".join([
        f"import sys, time; sys.path.insert(0, {str(Path(__file__).parent)!r}); import blender_slots as b",
        "with b.slot('selftest'):",
        "    t0 = time.time(); time.sleep(1.5)",
        f"    open({str(log)!r}, 'a').write(f'{{t0}} {{time.time()}}' + chr(10))",
    ])
    env = dict(os.environ, ALLSET_NO_SLOTS="0")
    procs = [subprocess.Popen([sys.executable, "-c", code], env=env) for _ in range(SLOTS + 1)]
    for pr in procs:
        pr.wait()
    spans = [tuple(map(float, ln.split())) for ln in log.read_text().splitlines()]
    peak = max(sum(1 for a, b in spans if a <= t < b) for t, _ in spans)
    assert len(spans) == SLOTS + 1, spans
    assert peak <= SLOTS, f"{peak} at once"
    print(f"blender_slots selftest ok: {len(spans)} holders, at most {peak} at once (slots {SLOTS})")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        print({"folder": str(folder()), "slots": SLOTS, "taken": holders()})
