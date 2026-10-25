# Step 198: Retime Tool in a GUI Maya 2022 (keys move only on a manipulator drag inside retimeKeyCtx; retimeHelper
# -moveFrame moves bars only, measured). QTest mouse events into the Graph Editor canvas (like research/scripts/maya_graph).
# Calibrate frame <-> canvas x by double-clicks (each makes a marker, read back with retimeHelper -q -frame), then drag
# markers. Factory prefs (MAYA_APP_DIR in tmp/). Writes MK_SHOTS_OUT/_ge198.json and _log.txt, then quits.
import json, os, traceback
import maya.cmds as cmds
import maya.mel as mel
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtTest import QTest

OUT = os.environ["MK_SHOTS_OUT"]
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "_log.txt"), "w")
DATA = {"cases": {}}
KEYS = ((1, 0), (5, 2), (10, 5), (15, 3), (20, 8), (30, 1))
TPF = [24.0]          # retimeHelper frame units per frame (measured: frame 5 -> 120)
CAL = {}


def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n"); LOG.flush()


def later(ms, f):
    QtCore.QTimer.singleShot(ms, f)


def ge_window():
    for t in QtWidgets.QApplication.topLevelWidgets():
        if t.isVisible() and "graph" in t.windowTitle().lower():
            return t


def canvas():
    t = ge_window()
    r = QtCore.QRect(t.mapToGlobal(QtCore.QPoint(0, 0)), t.size())
    g0 = QtCore.QPoint(r.x() + int(r.width() * 0.36), r.y() + int(r.height() * 0.22))
    g1 = QtCore.QPoint(r.x() + int(r.width() * 0.98), r.y() + int(r.height() * 0.95))
    mid = QtCore.QPoint((g0.x() + g1.x()) // 2, (g0.y() + g1.y()) // 2)
    w = QtWidgets.QApplication.widgetAt(mid)
    return w, w.mapFromGlobal(g0), w.mapFromGlobal(g1)


def markers():
    return [f / TPF[0] for f in (cmds.retimeHelper(q=True, frame=True) or [])]


def clear_markers():
    for _ in range(20):
        if not (cmds.retimeHelper(q=True, frame=True) or []):
            return
        cmds.retimeHelper(e=True, deleteFrame=0)


def times():
    return cmds.keyframe("pCube1", at="tx", q=True, tc=True)


def values():
    return cmds.keyframe("pCube1", at="tx", q=True, vc=True)


def reset_keys():
    cmds.cutKey("pCube1", at="tx", clear=True)
    for t, v in KEYS:
        cmds.setKeyframe("pCube1", at="tx", t=t, v=v)
    cmds.selectKey("pCube1", at="tx")


def ypix():
    c, l0, l1 = canvas()
    return (l0.y() + l1.y()) // 2


def xpix(frame):
    a, b = CAL["a"], CAL["b"]           # frame = a * x + b
    return int(round((frame - b) / a))


def drag(x0, x1, y=None, mods=QtCore.Qt.NoModifier):
    c, _l0, _l1 = canvas()
    y = int(canvas()[0].height() * 0.85) if y is None else y
    p0 = QtCore.QPoint(x0, y)
    QTest.mouseMove(c, p0)
    QTest.mousePress(c, QtCore.Qt.LeftButton, mods, p0)
    for k in range(1, 11):
        QTest.mouseMove(c, QtCore.QPoint(x0 + (x1 - x0) * k // 10, y))
    QTest.mouseRelease(c, QtCore.Qt.LeftButton, mods, QtCore.QPoint(x1, y))


STEPS = []


def step(f):
    STEPS.append(f); return f


@step
def s_setup():
    for t in QtWidgets.QApplication.topLevelWidgets():
        if t.isVisible() and t.objectName() != "MayaWindow" and isinstance(t, QtWidgets.QDialog):
            t.close()
    cmds.polyCube()
    reset_keys()
    cmds.select("pCube1")
    mel.eval("GraphEditor")
    cmds.playbackOptions(min=1, max=30)


@step
def s_tool():
    mel.eval("GraphEditorFrameAll")
    mel.eval("setToolTo retimeKeySuperContext")
    log("ctx", cmds.currentCtx(), "snapOnFrame", cmds.retimeKeyCtx("retimeKeyContext", q=True, snapOnFrame=True))
    DATA["snapOnFrame_default"] = cmds.retimeKeyCtx("retimeKeyContext", q=True, snapOnFrame=True)
    clear_markers()


@step
def s_calibrate():
    """Grab the canvas without markers, then with markers at 5 and 25 (retimeHelper): the changed pixel columns are
    the marker bars -> frame <-> x."""
    cmds.animView("graphEditor1GraphEd", e=True, startTime=0, endTime=32, minValue=-2, maxValue=10)
    clear_markers()
    cmds.refresh(force=True)
    later(400, _cal_a)


def _img():
    """Screen pixels of the canvas widget (a GL widget: QWidget.grab() is blank)."""
    c, _l0, _l1 = canvas()
    g = c.mapToGlobal(QtCore.QPoint(0, 0))
    return QtGui.QGuiApplication.primaryScreen().grabWindow(0, g.x(), g.y(), c.width(), c.height()).toImage()


def calibrate():
    cmds.animView("graphEditor1GraphEd", e=True, startTime=0, endTime=32, minValue=-2, maxValue=10)
    cmds.refresh(force=True)
    QtWidgets.QApplication.processEvents()
    _cal_a()


def _cal_a():
    img = _img()
    img.save(os.path.join(OUT, "cal.png"))
    cols = []
    for x in range(img.width()):
        for y in range(img.height()):
            c = QtGui.QColor(img.pixel(x, y))
            if c.red() > 200 and 120 < c.green() < 200 and c.blue() < 80:      # key diamonds (orange)
                cols.append(x)
                break
    groups = []
    for x in cols:
        if groups and x - groups[-1][-1] <= 2:
            groups[-1].append(x)
        else:
            groups.append([x])
    centres = [(g[0] + g[-1]) / 2.0 for g in groups]
    log("diamond columns", centres)
    DATA["diamonds"] = centres
    centres = [c for c in centres if c > 30]        # frame 1 sits under the yellow current-time line
    ks = KEYS[1:]
    if len(centres) == len(ks):
        k = (ks[-1][0] - ks[0][0]) / (centres[-1] - centres[0])
        CAL.update(a=k, b=ks[0][0] - k * centres[0])
        DATA["diamond_fit_err"] = [ks[i][0] - (CAL["a"] * centres[i] + CAL["b"]) for i in range(len(ks))]
    log("CAL", CAL, DATA.get("diamond_fit_err"))
    clear_markers()
    reset_keys()


def dclick(frame):
    c, _l0, _l1 = canvas()
    p = QtCore.QPoint(xpix(frame), int(c.height() * 0.85))
    QTest.mouseMove(c, p)
    QTest.mouseClick(c, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, p)
    QTest.mouseDClick(c, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, p)


def case(name, make, moves, snap=True, select_all=True, yfrac=0.85):
    """``make`` = marker frames; ``moves`` = [(marker frame, new frame)] dragged one after another."""
    def run():
        try:
            clear_markers()
            reset_keys()
            calibrate()
            if not select_all:
                cmds.selectKey(clear=True)
            cmds.retimeKeyCtx("retimeKeyContext", e=True, snapOnFrame=snap)
            clear_markers()
            for f in make:
                dclick(f)
                QtWidgets.QApplication.processEvents()
            cmds.refresh(force=True)
            later(1, lambda: _img().save(os.path.join(OUT, name + "_before.png")))
            rec = {"markers": list(make), "moves": [list(m) for m in moves], "snap": snap, "log": [],
                   "made": markers(), "times_after_dclick": times()}
            DATA["cases"][name] = rec
            seq = list(moves)

            def nxt():
                if not seq:
                    _img().save(os.path.join(OUT, name + "_after.png"))
                    rec["final_times"], rec["final_values"], rec["final_markers"] = times(), values(), markers()
                    log(name, json.dumps(rec))
                    return
                f0, f1 = seq.pop(0)
                x0, x1 = xpix(f0), xpix(f1)
                cmds.refresh(force=True)
                c, _a, _b = canvas()
                QTest.mouseMove(c, QtCore.QPoint(x0, int(c.height() * yfrac)))
                over = cmds.retimeHelper(q=True, mouseOver=True)
                drag(x0, x1, int(c.height() * yfrac))
                later(300, lambda: (rec["log"].append({"from": f0, "to": f1, "x": [x0, x1], "over": over,
                                                       "times": times(), "markers": markers()}), nxt()))
            nxt()
        except Exception:
            log(name, traceback.format_exc())
    return run


for _name, _make, _moves, _kw in (
        ("two_drag_second_right", (5, 15), ((15, 20),), {}),
        ("two_drag_second_left", (5, 15), ((15, 12),), {}),
        ("two_drag_first_left", (5, 15), ((5, 3),), {}),
        ("three_drag_middle", (5, 15, 25), ((15, 18),), {}),
        ("one_drag", (10,), ((10, 14),), {}),
        ("two_drag_frac_nosnap", (5, 15), ((15, 17.5),), {"snap": False}),
        ("two_drag_frac_snap", (5, 15), ((15, 17.5),), {"snap": True}),
        ("two_drag_noselect", (5, 15), ((15, 20),), {"select_all": False}),
        ("two_drag_line_low", (5, 15), ((15, 20),), {"yfrac": 0.85}),
        ("two_drag_twice", (5, 15), ((15, 20), (5, 7)), {}),
):
    _kw.setdefault("yfrac", 0.5)
    STEPS.append(case(_name, _make, _moves, **_kw))


@step
def s_quit():
    json.dump(DATA, open(os.path.join(OUT, "_ge198.json"), "w"), indent=1)
    log("done")
    LOG.close()
    cmds.quit(force=True)


IDX = [0]


def tick():
    if IDX[0] >= len(STEPS):
        return
    f = STEPS[IDX[0]]; IDX[0] += 1
    try:
        log("step", getattr(f, "__name__", "?")); f()
    except Exception:
        log(traceback.format_exc())
    later(3500, tick)


cmds.evalDeferred(lambda: later(9000, tick), lowestPriority=True)
