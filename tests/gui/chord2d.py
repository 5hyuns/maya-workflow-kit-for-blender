"""Case runner shared by the 2D editor Alt+LMB+MMB GUI tests (#325): each case frames the editor, holds Alt, presses /
lets go of mouse buttons and drags, then keeps the view rectangle the editor shows for the checks."""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check, ev, screenshot, step, win  # noqa: E402

SHOTS = os.environ.get("ALLSET_GUI_SHOTS", "")
STEP_PX = 8        # one mouse move
D = 40             # one drag leg
NAV = {"VIEW2D_OT_pan", "VIEW2D_OT_zoom", "IMAGE_OT_view_pan", "IMAGE_OT_view_zoom", "ALLSET_OT_nav_2d",
       "ALLSET_OT_dolly_2d"}
# area: the editor under test; frame: puts its view back to the same start
C = {"refs": {}, "area": None, "frame": None, "tag": "2d"}


def region():
    return next(r for r in C["area"].regions if r.type == 'WINDOW')


def rect():
    """View rectangle shown by the region (view coordinates of its corners)."""
    r = region()
    x0, y0 = r.view2d.region_to_view(0, 0)
    x1, y1 = r.view2d.region_to_view(r.width, r.height)
    return (x0, y0, x1, y1)


def modal_names():
    return [op.bl_idname for op in win().modal_operators]


def same_rect(a, b, tol=0.01):
    """Equal within ``tol`` of the view size on each axis."""
    w, h = abs(b[2] - b[0]) or 1.0, abs(b[3] - b[1]) or 1.0
    return (abs(a[0] - b[0]) < tol * w and abs(a[2] - b[2]) < tol * w
            and abs(a[1] - b[1]) < tol * h and abs(a[3] - b[3]) < tol * h)


def same_view(a, b, px=2):
    """Equal within ``px`` region pixels on each axis (a 2D view may settle by a pixel after any change)."""
    r = region()
    w, h = abs(b[2] - b[0]) or 1.0, abs(b[3] - b[1]) or 1.0
    tx, ty = px * w / max(r.width, 1), px * h / max(r.height, 1)
    return (abs(a[0] - b[0]) <= tx and abs(a[2] - b[2]) <= tx
            and abs(a[1] - b[1]) <= ty and abs(a[3] - b[3]) <= ty)


def fmt(rc):
    return "(%.3f, %.3f, %.3f, %.3f)" % rc


def override():
    return bpy.context.temp_override(window=win(), area=C["area"], region=region())


def point(fx=0.5, fy=0.5):
    r = region()
    return r.x + int(r.width * fx), r.y + int(r.height * fy)


def add_case(name, script, at=(0.5, 0.5), verify=None):
    """``script``: ('press' | 'release', button) and ('move', dx, dy) per leg (split into STEP_PX moves), all with
    Alt held; ('snap', key) keeps the view rectangle at that point. The view is framed first; whatever is still held
    at the end is let go."""
    st = {"held": [], "snaps": {}}

    def start():
        C["frame"]()
        x, y = point(*at)
        st["xy"] = [x, y]
        ev('MOUSEMOVE', 'NOTHING', x=x, y=y)

    def alt_down():
        st["rect0"] = rect()
        ev('LEFT_ALT', 'PRESS', alt=True, x=st["xy"][0], y=st["xy"][1])

    step(start)
    step(alt_down)
    for item in script:
        if item[0] in ('press', 'release'):
            def button(item=item):
                kind, btn = item
                if kind == 'press':
                    st["held"].append(btn)
                    ev(btn, 'PRESS', alt=True, x=st["xy"][0], y=st["xy"][1])
                else:
                    st["held"].remove(btn)
                    ev(btn, 'RELEASE', alt=True, x=st["xy"][0], y=st["xy"][1])
            step(button)
        elif item[0] == 'move':
            moves = max(abs(item[1]), abs(item[2])) // STEP_PX
            for _ in range(moves):
                def move(item=item, moves=moves):
                    st["xy"][0] += item[1] // moves
                    st["xy"][1] += item[2] // moves
                    ev('MOUSEMOVE', 'NOTHING', alt=True, x=st["xy"][0], y=st["xy"][1])
                    st["modals"] = modal_names()
                step(move)
        elif item[0] == 'snap':
            step(lambda item=item: st["snaps"].__setitem__(item[1], rect()))

    def finish():
        st["rect1"] = rect()
        st["during"] = st.get("modals", [])
        for btn in list(reversed(st["held"])):
            ev(btn, 'RELEASE', alt=True, x=st["xy"][0], y=st["xy"][1])
        st["held"].clear()
        ev('LEFT_ALT', 'RELEASE', x=st["xy"][0], y=st["xy"][1])
    step(finish)
    step(lambda: None)

    def done():
        C["refs"][name] = st
        left = [n for n in modal_names() if n in NAV]
        check(f"{name}: nothing left running after letting go ({left})", not left)
        if verify:
            for v in (verify if isinstance(verify, (list, tuple)) else (verify,)):
                v(st)
        if SHOTS:
            screenshot(os.path.join(SHOTS, f"issue325_{C['tag']}_{name}.png"))
    step(done)


# --- checks -------------------------------------------------------------------------------------------------------

def like(ref, label):
    """The view ends where the ``ref`` case's view ended, and it moved."""
    def verify(st):
        want = C["refs"][ref]["rect1"]
        check(f"{label}: the view {fmt(st['rect1'])} is the {ref} view {fmt(want)} "
              f"(start {fmt(st['rect0'])}, modals {st['during']})",
              same_rect(st["rect1"], want) and not same_rect(st["rect1"], st["rect0"]))
    return verify


def unchanged(label):
    def verify(st):
        check(f"{label}: the view does not change ({fmt(st['rect0'])} -> {fmt(st['rect1'])}, "
              f"modals {st['during']})", same_view(st["rect1"], st["rect0"]))
    return verify


def still(label, key):
    def verify(st):
        check(f"{label}: the view holds still after the button is let go "
              f"({fmt(st['snaps'][key])} -> {fmt(st['rect1'])})", same_view(st["rect1"], st["snaps"][key]))
    return verify


def zoomed(label, inward=True, y_too=True):
    """Zoomed in (``inward``) or out: the width shrinks / grows; the height with it (``y_too``) or kept."""
    def verify(st):
        a, b = st["rect0"], st["rect1"]
        w0, w1, h0, h1 = a[2] - a[0], b[2] - b[0], a[3] - a[1], b[3] - b[1]
        wide = w1 < w0 * 0.95 if inward else w1 > w0 * 1.05
        if y_too:
            high = abs(h1 / h0 - w1 / w0) < 0.02 * (w1 / w0)
        else:
            high = abs(h1 - h0) <= 2 * h0 / max(region().height, 1)     # a pixel of settling
        check(f"{label}: zooms {'in' if inward else 'out'} (width {w0:.3f} -> {w1:.3f}, height {h0:.3f} -> "
              f"{h1:.3f}{'' if y_too else ' kept'}, modals {st['during']})", wide and high)
    return verify


def panned(label, ref_key=None, px=D):
    """Moved right by ``px`` px worth of the view (content follows the mouse), size kept."""
    def verify(st):
        a = st["snaps"][ref_key] if ref_key else st["rect0"]
        b = st["rect1"]
        per_px = (a[2] - a[0]) / region().width
        shift = a[0] - b[0]
        check(f"{label}: pans {shift:.3f} (~{px * per_px:.3f} for {px} px), size kept "
              f"({a[2] - a[0]:.3f} -> {b[2] - b[0]:.3f})",
              abs(shift - px * per_px) < 0.1 * px * per_px and abs((b[2] - b[0]) - (a[2] - a[0])) < 1e-3 * (a[2] - a[0]))
    return verify
