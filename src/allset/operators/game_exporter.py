# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya File > Game Exporter (step 225, Issue #135; ATTACH_PLAN L24): the Model / Animation export window with
Maya's Animation Clips list, written with the kit's Maya FBX preset (operators/file_io.py, step 222 rig post-process).

Maya 2026 (mayapy, research/scripts/maya_anim225/game_exporter.py; ``$M/others/gameFbxExporter*.mel``):

- settings live on a ``gameFbxExporter`` node; factory values (createNode, ``FACTORY``): Export All, Model tab,
  one file, Bake Animation on, Skinning / Blend Shapes on, Smoothing Groups / Tangents and Binormals on, Triangulate /
  Move to Origin / Embed Media / Include Children / Input Connections off, Up Axis Y, Cameras / Lights on;
- a new clip (``gameExp_AddNewAnimationClip``) starts with the playback range, an empty name, export on; a typed name
  that exists gets the next number (``gameExp_ProvideUniqueName``: walk -> walk1, run09 -> run10);
- clips export as FBX takes (``FBXExportSplitAnimationIntoTakes`` name start end): **one file** = the file name
  (``.fbx`` added) with a take per exported clip; **a file per clip** = file name used as a prefix + clip name +
  ``.fbx`` (``gameExp_GenerateClipFilenameList``). Maya's files also carry the FBX plug-in's own ``Take 001`` and its
  per-clip loop never clears the take list, so a later clip file repeats the earlier clips' takes (measured) — the
  kit writes only the clip's own takes (delegated: engines would import those extra clips).

Blender (step 231, Issue #140): each clip is the scene's timeline take written by the kit's Maya FBX preset (the
step 222 rig rewrite included, so a clip file has Export Selection's joints), one write per clip with the scene's
range set to the clip; several clips of one file are merged into it as takes (``merge_takes``). Blender's NLA-strip
takes are not used: they evaluate one object at a time (``_ClipTimeline``).
"""

import os
import re

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, \
    StringProperty

from .. import results

FACTORY = {"export_type": 'MODEL', "export_set": 'ALL', "model_file_mode": 'SINGLE', "file_split": 'SINGLE',
           "bake_animation": True, "skinning": True, "blendshapes": True, "smoothing_groups": True,
           "tangents": True, "triangulate": False, "move_to_origin": False, "embed_media": False,
           "include_children": False, "input_connections": False, "up_axis": 'Y', "include_cameras": True,
           "include_lights": True}


class ALLSET_PG_game_clip(bpy.types.PropertyGroup):
    name: StringProperty(name="Clip Name")
    start: FloatProperty(name="Start", default=1.0)
    end: FloatProperty(name="End", default=24.0)
    export: BoolProperty(name="Export", default=True)


class ALLSET_PG_game_exporter(bpy.types.PropertyGroup):
    export_type: EnumProperty(name="Export", items=[('MODEL', "Model", "Export the models (no animation)"),
                                                  ('ANIMATION', "Animation Clips", "Export the animation clips")],
                              default='MODEL')
    export_set: EnumProperty(name="Export", items=[('ALL', "Export All", ""), ('SELECTION', "Export Selection", "")],
                             default='ALL')
    model_file_mode: EnumProperty(name="File Type", items=[('SINGLE', "Single File", ""),
                                                          ('PER_ROOT', "Multiple Files", "A file per root object")],
                                  default='SINGLE')
    file_split: EnumProperty(name="File Type", items=[('SINGLE', "Multiple Clips to Single File", ""),
                                                     ('PER_CLIP', "Clips to Multiple Files", "")], default='SINGLE')
    clips: CollectionProperty(type=ALLSET_PG_game_clip)
    clip_index: IntProperty(default=0)
    bake_animation: BoolProperty(name="Bake Animation", default=True)
    skinning: BoolProperty(name="Skinning", default=True)
    blendshapes: BoolProperty(name="Blend Shapes", default=True)
    smoothing_groups: BoolProperty(name="Smoothing Groups", default=True)
    tangents: BoolProperty(name="Tangents and Binormals", default=True)
    triangulate: BoolProperty(name="Triangulate", default=False)
    move_to_origin: BoolProperty(name="Move to Origin", default=False)
    embed_media: BoolProperty(name="Embed Media", default=False)
    include_children: BoolProperty(name="Include Children", default=False)
    input_connections: BoolProperty(name="Input Connections", default=False)
    up_axis: EnumProperty(name="Up Axis", items=[('Y', "Y", ""), ('Z', "Z", "")], default='Y')
    include_cameras: BoolProperty(name="Cameras", default=True)
    include_lights: BoolProperty(name="Lights", default=True)
    export_path: StringProperty(name="Path", subtype='DIR_PATH')
    export_filename: StringProperty(name="File Name")


def settings(context):
    return context.scene.allset_game_exporter


# --- clips -------------------------------------------------------------------------------------------------------

def playback_range(scene):
    """Maya's playback range = the kit's preview range when it is on, else the scene range (step 20)."""
    if scene.use_preview_range:
        return float(scene.frame_preview_start), float(scene.frame_preview_end)
    return float(scene.frame_start), float(scene.frame_end)


def add_clip(scene):
    s = scene.allset_game_exporter
    clip = s.clips.add()
    clip.name = ""
    clip.start, clip.end = playback_range(scene)
    clip.export = True
    s.clip_index = len(s.clips) - 1
    return clip


def unique_name(name, taken):
    """Maya gameExp_ProvideUniqueName: count up a trailing number (keeping its zeros), else append 1."""
    while name in taken:
        m = re.search(r"\d+$", name)
        if m:
            digits = m.group(0)
            number = int(digits) + 1
            width = len(digits) if len(str(number)) <= len(digits) else len(str(number))
            name = name[:m.start()] + str(number).zfill(width)
        else:
            name = name + "1"
    return name


def clip_files(s, folder):
    """[(path, [clips])] Maya writes for the exported clips (gameExp_GenerateClipFilenameList)."""
    clips = [c for c in s.clips if c.export]
    stem = s.export_filename
    if s.file_split == 'SINGLE':
        name = stem if os.path.splitext(stem)[1] else stem + ".fbx"
        return [(os.path.join(folder, name), clips)] if clips and stem else []
    base = stem[:-4] if stem.lower().endswith(".fbx") else stem
    out = []
    for c in clips:
        name = base + c.name
        out.append((os.path.join(folder, name if os.path.splitext(name)[1] else name + ".fbx"), [c]))
    return out


def model_files(s, folder, roots):
    stem = s.export_filename
    if s.model_file_mode == 'SINGLE':
        return [(os.path.join(folder, stem if os.path.splitext(stem)[1] else stem + ".fbx"), roots)] if stem else []
    base = stem[:-4] if stem.lower().endswith(".fbx") else stem
    return [(os.path.join(folder, base + r.name + ".fbx"), [r]) for r in roots]


# --- FBX ---------------------------------------------------------------------------------------------------------

def fbx_args(context, s, selection):
    from . import file_io, units
    _op, args = file_io.export_args('FBX', units.maya_unit(context.scene), selection)
    types = {'MESH', 'EMPTY', 'OTHER'}
    if s.skinning:
        types.add('ARMATURE')
    if s.include_cameras:
        types.add('CAMERA')
    if s.include_lights:
        types.add('LIGHT')
    args.update(object_types=types, mesh_smooth_type='FACE' if s.smoothing_groups else 'OFF',
                use_tspace=s.tangents, use_triangles=s.triangulate,
                axis_up=s.up_axis, axis_forward='-Z' if s.up_axis == 'Y' else 'Y')
    if s.embed_media:
        args.update(embed_textures=True, path_mode='COPY')
    return args


KTIME = 46186158000            # FBX ticks per second
ANIM_IDS = (b"AnimationStack", b"AnimationLayer", b"AnimationCurveNode", b"AnimationCurve")


class _ClipTimeline:
    """The scene's timeline = one clip while Blender's writer bakes it (its scene take, not NLA strips).

    Step 231 (Issue #140): the writer's NLA-strip takes evaluate one object's strip at a time (export_fbx_bin.py
    ``bake_anim_use_nla_strips``: every other strip muted, every active action removed), so a joint chain driven
    by another object (an IK handle's keys, a constraint target) was written without that object's animation —
    the audit's 21 cm IK arm. The timeline take evaluates the whole scene, like Maya's exporter, and leaves the
    kit's animation-layer NLA tracks out of the take list (they evaluate into the result instead). The scene gets
    a unique name while it writes: Blender derives a take's element ids from the scene name, so the takes of
    several clips can be merged into one file (``merge_takes``)."""

    def __init__(self, scene, clip, index):
        self.scene, self.clip, self.index = scene, clip, index

    def __enter__(self):
        sc = self.scene
        self.saved = (sc.name, sc.frame_start, sc.frame_end, sc.frame_current)
        start, end = int(round(self.clip.start)), int(round(self.clip.end))
        if end < start:
            raise ValueError(f"Clip {self.clip.name}: the end is before the start")
        name, n = f"{sc.name}.clip{self.index}", 0
        while name in bpy.data.scenes:
            n += 1
            name = f"{self.saved[0]}.clip{self.index}.{n}"
        sc.name = name
        _set_range(sc, start, end)
        return self

    def __exit__(self, *exc):
        sc = self.scene
        name, start, end, current = self.saved
        sc.name = name
        _set_range(sc, start, end)
        sc.frame_set(current)


def _set_range(sc, start, end):
    # Blender clamps frame_start to frame_end and back: widen first, then narrow
    sc.frame_end = max(end, sc.frame_end)
    sc.frame_start = start
    sc.frame_end = end


def _rename(elem, name):
    """An FBX object name is ``<name>\x00\x01<class>``."""
    old = elem.props[1]
    tail = old[old.index(b"\x00\x01"):] if b"\x00\x01" in old else b""
    elem.props[1] = name.encode("utf-8") + tail


def _text(v):
    return v.decode("utf-8", "replace") if isinstance(v, bytes) else v


def _same_kind(old, new):
    return new.encode("utf-8") if isinstance(old, bytes) else new


def merge_takes(path, parts, clips):
    """One file with a take per clip: ``path`` holds clip 0's take, ``parts[i]`` clip i+1's (the same objects
    written again, so the same object ids). Takes are renamed after their clips. Returns the take names."""
    from . import fbx_rig
    tree, version = fbx_rig.load(path)
    objects, conns = tree.first(b"Objects"), tree.first(b"Connections")
    takes = tree.first(b"Takes")
    have = {e.props[0] for e in objects.elems if e.props}
    added = {}
    for part in parts:
        other, _v = fbx_rig.load(part)
        anim = [e for e in other.first(b"Objects").elems if e.id in ANIM_IDS]
        ids = {e.props[0] for e in anim}
        if ids & have:
            raise RuntimeError("Game Exporter: two clips wrote the same take ids")
        objects.elems.extend(anim)
        have |= ids
        for e in anim:
            added[e.id] = added.get(e.id, 0) + 1
        conns.elems.extend(c for c in other.first(b"Connections").elems if c.props[1] in ids)
        o_takes = other.first(b"Takes")
        if takes is not None and o_takes is not None:
            takes.elems.extend(t for t in o_takes.elems if t.id == b"Take")
    defs = tree.first(b"Definitions")
    if defs is not None and added:
        for ot in defs.find(b"ObjectType"):
            n, cnt = added.get(ot.props[0]), ot.first(b"Count")
            if n and cnt is not None:
                cnt.props[0] += n
        total = defs.first(b"Count")
        if total is not None:
            total.props[0] += sum(added.values())
    stacks = objects.find(b"AnimationStack")
    children = {}
    for c in conns.elems:
        if c.props[0] == b"OO":
            children.setdefault(c.props[2], []).append(c.props[1])
    layers = {e.props[0]: e for e in objects.find(b"AnimationLayer")}
    names = []
    for st, clip in zip(stacks, clips):
        old = fbx_rig.name_of(st)
        _rename(st, clip.name)
        for lid in children.get(st.props[0], ()):
            if lid in layers:
                _rename(layers[lid], clip.name)
        for t in (takes.find(b"Take") if takes is not None else ()):
            if _text(t.props[0]) == old:
                t.props[0] = _same_kind(t.props[0], clip.name)
                for sub in t.elems:
                    if sub.id == b"FileName":
                        sub.props[0] = _same_kind(sub.props[0], clip.name + ".tak")
        names.append(clip.name)
    if takes is not None and names:
        cur = takes.first(b"Current")
        if cur is not None:
            cur.props[0] = _same_kind(cur.props[0], names[0])
    fbx_rig.save(path, tree, version)
    return names


class _Scope:
    """What a kit export leaves out (file_io ``_FileDialog``, steps 164 / 211 / 226): Export All = no startup
    cameras, never control shapes; Export Selection with Include Children = the selection with its hierarchy."""

    def __init__(self, context, selection, children):
        self.context, self.selection, self.children = context, selection, children
        self.stack = []

    def __enter__(self):
        from . import dag, startup_cameras
        from .control_shapes import excluded as shapes_excluded
        sc, vl = self.context.scene, self.context.view_layer
        cms = [shapes_excluded(sc, vl)]
        if not self.selection:
            cms.append(startup_cameras.excluded(sc, vl))
        elif self.children:
            cms.append(dag.selected_hierarchy(self.context))
        for cm in cms:
            cm.__enter__()
            self.stack.append(cm)
        return self

    def __exit__(self, *exc):
        while self.stack:
            self.stack.pop().__exit__(*exc)


def export(context, s):
    """Write the files; returns [(path, take names)]."""
    from . import file_io, units
    folder = bpy.path.abspath(s.export_path) or ""
    if not folder:
        raise ValueError("The file path is empty")            # Maya kGameExporterFilePathEmpty
    if not os.path.isdir(folder):
        raise ValueError(f"The directory doesn't exist: {folder}")
    selection = s.export_set == 'SELECTION'
    view_layer = context.view_layer
    obs = list(context.selected_objects) if selection else [o for o in context.scene.objects
                                                            if o.name in view_layer.objects]
    if selection and not obs:
        raise ValueError("Nothing selected to export.")
    k = units.maya_unit(context.scene)
    out = []
    if s.export_type == 'ANIMATION':
        files = clip_files(s, folder)
        if not files:
            raise ValueError("The file name is empty or no clip is checked for export")
        names = [c.name for c in s.clips if c.export]
        if any(not n for n in names) or len(set(names)) != len(names):
            raise ValueError("Every exported clip needs a unique name")
        for path, clips in files:
            args = dict(fbx_args(context, s, selection), bake_anim=True, bake_anim_use_nla_strips=False,
                        bake_anim_use_all_actions=False, bake_anim_force_startend_keying=True)
            parts = []
            try:
                with _Scope(context, selection, s.include_children):
                    for i, clip in enumerate(clips):
                        part = path if i == 0 else os.path.splitext(path)[0] + f".clip{i}.tmp.fbx"
                        if i:
                            parts.append(part)
                        with _ClipTimeline(context.scene, clip, i):
                            file_io.write(context, 'FBX', part, "export_scene.fbx", args, True, k)
                out.append((path, merge_takes(path, parts, clips)))
            finally:
                for part in parts:                 # written beside the user's file, deleted at once
                    if os.path.exists(part):
                        os.remove(part)
        return out
    roots = [o for o in obs if o.parent is None or o.parent not in obs]
    files = model_files(s, folder, roots)
    if not files:
        raise ValueError("The file name is empty")               # Maya kGameExporterFilenameEmpty
    for path, part in files:
        args = dict(fbx_args(context, s, True), bake_anim=False)
        keep = list(context.selected_objects)
        try:
            for o in context.selected_objects:
                o.select_set(False)
            for r in part:
                for o in [r, *r.children_recursive]:
                    if o in obs and o.name in view_layer.objects:
                        o.select_set(True)
            file_io.write(context, 'FBX', path, "export_scene.fbx", args, True, k)
        finally:
            for o in context.selected_objects:
                o.select_set(False)
            for o in keep:
                o.select_set(True)
        out.append((path, []))
    return out


# --- window ------------------------------------------------------------------------------------------------------

class ALLSET_UL_game_clips(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0):
        row = layout.row(align=True)
        row.prop(item, "export", text="")
        row.prop(item, "name", text="", emboss=True, placeholder="Clip Name")
        row.prop(item, "start", text="")
        row.prop(item, "end", text="")


class ALLSET_OT_game_clip(bpy.types.Operator):
    """Add a clip with the playback range, or delete the picked clip"""
    bl_idname = "allset.game_clip"
    bl_label = "Animation Clip"
    bl_options = {'INTERNAL', 'UNDO'}

    action: EnumProperty(items=[('ADD', "Add", ""), ('REMOVE', "Delete", "")], options={'SKIP_SAVE'})

    def execute(self, context):
        s = settings(context)
        if self.action == 'ADD':
            add_clip(context.scene)
        elif 0 <= s.clip_index < len(s.clips):
            s.clips.remove(s.clip_index)
            s.clip_index = max(0, min(s.clip_index, len(s.clips) - 1))
        return {'FINISHED'}


class ALLSET_OT_game_exporter(bpy.types.Operator):
    """Maya Game Exporter: export models or animation clips (one FBX take per clip) for a game engine"""
    bl_idname = "allset.game_exporter"
    bl_label = "Game Exporter"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        s = settings(context)
        if not s.export_path:
            from . import project
            s.export_path = project.current_root(context)
        return context.window_manager.invoke_props_dialog(self, width=560, title="Game Exporter",
                                                          confirm_text="Export")

    def draw(self, context):
        s = settings(context)
        layout = self.layout
        layout.row().prop(s, "export_type", expand=True)
        box = layout.box()
        box.row().prop(s, "export_set", expand=True)
        if s.export_type == 'MODEL':
            box.row().prop(s, "model_file_mode", expand=True)
        else:
            box.label(text="Animation Clips")
            row = box.row()
            row.template_list("ALLSET_UL_game_clips", "", s, "clips", s, "clip_index", rows=4)
            col = row.column(align=True)
            col.operator("allset.game_clip", text="", icon='ADD').action = 'ADD'
            col.operator("allset.game_clip", text="", icon='REMOVE').action = 'REMOVE'
            box.row().prop(s, "file_split", expand=True)
            box.prop(s, "bake_animation")
        col = layout.box().column(align=True)
        col.label(text="Export Settings")
        grid = col.grid_flow(columns=2, align=True)
        for name in ("skinning", "blendshapes", "smoothing_groups", "tangents", "triangulate", "move_to_origin",
                     "embed_media", "include_children", "include_cameras", "include_lights"):
            sub = grid.row()
            sub.enabled = name not in {"blendshapes", "move_to_origin"}
            sub.prop(s, name)
        col.row().prop(s, "up_axis", expand=True)
        box = layout.box()
        box.label(text="Path")
        box.prop(s, "export_path")
        box.prop(s, "export_filename")
        folder = bpy.path.abspath(s.export_path)
        files = clip_files(s, folder) if s.export_type == 'ANIMATION' else []
        for path, clips in files[:4]:
            box.label(text=os.path.basename(path) + ("   " + ", ".join(c.name for c in clips) if clips else ""),
                      icon='FILE')

    def execute(self, context):
        try:
            done = export(context, settings(context))
        except (ValueError, RuntimeError) as ex:
            self.report({'ERROR'}, str(ex).strip().splitlines()[-1])
            return {'CANCELLED'}
        results.result(self, "Exported " + ", ".join(os.path.basename(p) for p, _t in done))
        return {'FINISHED'}


classes = (ALLSET_PG_game_clip, ALLSET_PG_game_exporter, ALLSET_UL_game_clips, ALLSET_OT_game_clip,
           ALLSET_OT_game_exporter)


def register_props():
    bpy.types.Scene.allset_game_exporter = PointerProperty(type=ALLSET_PG_game_exporter)


def unregister_props():
    del bpy.types.Scene.allset_game_exporter
