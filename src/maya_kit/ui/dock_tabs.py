# SPDX-License-Identifier: GPL-3.0-or-later
"""Sidebar = the Maya dock only: hide Blender's Item / Tool / View sidebar tabs (docs/steps/step_49.md).

Maya's right dock is one tab stack: Channel Box / Layer Editor, Attribute Editor, Modeling Toolkit
(research/maya/ui_layout.md:122-127). The kit's dock is the 3D View sidebar's "Channel Box" tab
(``WindowManager.maya_kit_dock`` switches CB/LE and AE, step 11). With the preference
``maya_dock_only`` the other sidebar panels that were registered when the kit was enabled are hidden
by wrapping their ``poll``: only in a 3D View sidebar (``wm.call_panel`` popups such as the Status
Line's Tool Settings still work). Blender stores a panel's poll callback when the class is registered
and only calls Python if the class had a ``poll`` then, so each panel is unregistered, given the
wrapper and registered again (children first out, parents first in; all of them, so their order
stays); ``unregister`` does the same with the original poll.
Child panels (``bl_parent_id``) hide with their parent.
"""

import bpy

_wrapped = []    # (cls, cls.__dict__ poll before or None, child panels re-registered or None)


def _hidden(context):
    region = context.region
    if region is None or region.type != 'UI':
        return False
    space = context.space_data
    if space is None or space.type != 'VIEW_3D':
        return False
    from .. import preferences
    try:
        return preferences.get(context).maya_dock_only
    except KeyError:
        return False


def _subclasses(cls):
    for sub in cls.__subclasses__():
        yield sub
        yield from _subclasses(sub)


def _idname(cls):
    return getattr(cls, "bl_idname", "") or cls.__name__


def sidebar_panels():
    """Registered top-level 3D View sidebar panels that are not the kit's, in registration order."""
    seen = set()
    out = []
    for cls in _subclasses(bpy.types.Panel):
        if cls in seen or cls.__name__.startswith("MAYAKIT_"):
            continue
        seen.add(cls)
        if (getattr(cls, "bl_space_type", None) == 'VIEW_3D' and getattr(cls, "bl_region_type", None) == 'UI'
                and not getattr(cls, "bl_parent_id", "") and cls.is_registered):
            out.append(cls)
    return out


def _children(parent, panels):
    """Registered descendants of ``parent`` (depth first, parents before children)."""
    pid = _idname(parent)
    for cls in panels:
        if getattr(cls, "bl_parent_id", "") == pid and cls.is_registered:
            yield cls
            yield from _children(cls, panels)


def _make_poll(original):
    def poll(cls, context):
        if _hidden(context):
            return False
        return original(context) if original is not None else True
    return classmethod(poll)


def register():
    everything = [c for c in _subclasses(bpy.types.Panel) if getattr(c, "bl_space_type", None) == 'VIEW_3D']
    # Every panel is re-registered (not only those without a poll) so the panels keep their order.
    for cls in sidebar_panels():
        raw = cls.__dict__.get("poll")
        kids = list(_children(cls, everything))
        _reregister(cls, kids, _make_poll(getattr(cls, "poll", None)))
        _wrapped.append((cls, raw, kids))


def _reregister(cls, kids, poll):
    for kid in reversed(kids):
        if kid.is_registered:
            bpy.utils.unregister_class(kid)
    if cls.is_registered:
        bpy.utils.unregister_class(cls)
    if poll is not None:
        cls.poll = poll
    elif "poll" in cls.__dict__:
        del cls.poll
    bpy.utils.register_class(cls)
    for kid in kids:
        bpy.utils.register_class(kid)


def unregister():
    for cls, raw, kids in _wrapped:   # forward: the original order again
        _reregister(cls, kids, raw)
    _wrapped.clear()
