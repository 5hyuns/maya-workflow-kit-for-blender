# Step 198: weighted / non-weighted tangents, weight lock, default tangent weight, buffer curve swap (mayapy, Maya 2022).
# Writes tmp/maya198/weights.json (key tangents + densely evaluated values for the Bezier fit in step 198).
import json, os
import maya.standalone; maya.standalone.initialize()
import maya.cmds as cmds

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tmp", "maya198", "weights.json")
KEYS = ((1, 0.0), (5, 2.0), (10, 5.0), (15, 3.0), (25, 8.0))
D = {}


def mk(name, weighted_global=None):
    cmds.file(new=True, force=True)
    if weighted_global is not None:
        cmds.keyTangent(g=True, wt=weighted_global)
    c = cmds.polyCube(name=name)[0]
    for t, v in KEYS:
        cmds.setKeyframe(c, at="tx", t=t, v=v)
    return c


def info(c):
    q = lambda **k: cmds.keyTangent(c, at="tx", q=True, **k)
    ts = [x / 4.0 for x in range(4, 25 * 4 + 1)]
    return {"weighted": cmds.keyTangent(c, at="tx", q=True, wt=True),
            "itt": q(itt=True), "ott": q(ott=True), "ia": q(ia=True), "oa": q(oa=True),
            "iw": q(iw=True), "ow": q(ow=True), "ix": q(ix=True), "iy": q(iy=True), "ox": q(ox=True), "oy": q(oy=True),
            "lock": q(l=True), "wl": q(wl=True),
            "eval": [(t, cmds.keyframe(c, at="tx", q=True, eval=True, t=(t,))[0]) for t in ts]}


c = mk("nonw")
D["fps"] = cmds.currentUnit(q=True, time=True)
D["default_global_wt"] = cmds.keyTangent(q=True, g=True, wt=True)
D["nonweighted"] = info(c)
cmds.keyTangent(c, at="tx", e=True, wt=True)                     # Curves > Weighted Tangents
D["to_weighted"] = info(c)
cmds.keyTangent(c, at="tx", e=True, t=(5, 5), wl=False)          # Free Tangent Length on key 2
D["freed"] = info(c)
cmds.keyTangent(c, at="tx", e=True, t=(5, 5), ow=6.0, iw=0.5)    # long out / short in
D["edited_weights"] = info(c)
cmds.keyTangent(c, at="tx", e=True, t=(5, 5), wl=True)           # Lock Tangent Length
cmds.keyTangent(c, at="tx", e=True, t=(5, 5), oa=40.0)
D["locked_angle_change"] = info(c)
cmds.keyTangent(c, at="tx", e=True, wt=False)                    # back to non-weighted
D["back_nonweighted"] = info(c)
c = mk("defw", weighted_global=True)                               # Default Tangent Weight > Weighted
D["new_curve_default_weighted"] = info(c)
cmds.keyTangent(g=True, wt=False)
# buffer curve
c = mk("buf")
cmds.selectKey(c, at="tx")
cmds.bufferCurve(animation="keys", overwrite=True)
D["buffer_exists"] = cmds.bufferCurve(c, at="tx", q=True, exists=True)
cmds.keyframe(c, at="tx", e=True, t=(10, 10), vc=9.0)
cmds.selectKey(c, at="tx")
cmds.bufferCurve(animation="keys", swap=True)
D["after_swap"] = cmds.keyframe(c, at="tx", q=True, vc=True)
cmds.selectKey(c, at="tx")
cmds.bufferCurve(animation="keys", swap=True)
D["after_swap2"] = cmds.keyframe(c, at="tx", q=True, vc=True)
cmds.keyframe(c, at="tx", e=True, t=(5, 5), tc=6.0)
cmds.selectKey(c, at="tx")
cmds.bufferCurve(animation="keys", swap=True)
D["swap_after_time_move"] = (cmds.keyframe(c, at="tx", q=True, tc=True), cmds.keyframe(c, at="tx", q=True, vc=True))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(D, open(OUT, "w"), indent=1)
print("OK")
