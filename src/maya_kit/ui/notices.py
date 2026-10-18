# SPDX-License-Identifier: GPL-3.0-or-later
""" notices: the near substitute + one line, for Maya menu items ( 「Maya 워크플로우
계획」 W3,  「계획」 (b)).

One table for every place a Maya item has no Blender equivalent, or a different one: the item's tooltip
(greyed items: ``maya_kit.menu_unavailable``; items with a substitute: ``maya_kit.menu_item``) and the Help
Line, which shows the notice while the tooltip is up — Maya's Help Line shows a menu item's annotation the same
way (). Keys are Maya menu label paths (``ui/menu_sets.iter_items``).
"""

import time

import bpy

# path: (substitute in Blender, one line). Paths with an action in menu_map.MAP run that substitute.
NOTICES = {
    # Pivot / snapping (step 59, )
    "Modify/Make Live": (
        "Face snapping", "Blender snaps onto every surface, not only the live one: Make Live turns face "
        "snapping on and names the surface in the Status Line."),
    "Modify/Bake Pivot": (
        "Pivot orientation", "Blender has one pivot (the origin), so only the pivot orientation is baked into "
        "Rotate; the position already is the object's pivot."),
    # Animation (W3: Animation Layers -> NLA, Character Sets -> Keying Sets, Time Editor / Trax -> NLA)
    "Windows/Relationship Editors/Animation Layers": (
        "NLA Editor", "Blender has no animation layers: stack actions as NLA tracks (blend mode per strip)."),
    "Windows/Animation Editors/Trax Editor": (
        "NLA Editor", "Blender has no Trax: clips are actions laid out as NLA strips."),
    "Windows/Animation Editors/Time Editor": (
        "NLA Editor", "Blender has no Time Editor: clips are actions laid out as NLA strips."),
    "Windows/Relationship Editors/Character Sets": (
        "Keying Sets", "Blender has no character sets: a Keying Set (Scene properties) keys a chosen set of channels."),
    "Control/Create Character Set": (
        "Keying Set", "Blender has no character sets: a Keying Set (Scene properties) keys a chosen set of channels."),
    "Key/Create Character Set": (
        "Keying Set", "Blender has no character sets: a Keying Set (Scene properties) keys a chosen set of channels."),
    # Playback (step 56): Blender playback always loops
    **{f"Playback/Playback Looping/{kind}": (
        "Continuous", "Blender playback always loops (no Once / Oscillate).") for kind in ("Once", "Oscillate")},
    # Sets (step 96): kit sets are collections outside the scene; Blender has no exclusive sets
    "Create/Sets/Partition": (
        "Set", "Blender has no partitions (sets whose members can't be in another set of the partition): use Create > Sets > Set."),
    # Dependency graph editors (W3: Node Editor -> none, Hypergraph -> Outliner)
    "Windows/Node Editor": (
        "Shader Editor", "Blender has no node graph of attribute connections: attribute links are drivers "
        "(Expression Editor), material nodes are in the Shader Editor (Hypershade)."),
    "Windows/General Editors/Hypergraph: Hierarchy": (
        "Outliner", "Blender has no Hypergraph: the Outliner shows the hierarchy."),
    "Windows/General Editors/Hypergraph: Connections": (
        "Drivers", "Blender has no connection graph: attribute links are drivers (Expression Editor)."),
    "Windows/General Editors/Namespace Editor": (
        "ns: name prefix", "Blender has no namespaces: Maya Kit keeps them as a \"ns:\" prefix in names."),
    # Rendering (W3: Light Editor -> kit light list, step 67)
    "Windows/Rendering Editors/Light Editor": (
        "kit Light Editor", "Blender has no Light Editor: Maya Kit lists the scene lights in a 3D View sidebar tab "
        "(Exposure is part of Power)."),
    "Windows/Rendering Editors/Hypershade": (
        "Shader Editor + kit list", "Blender has no Hypershade: the Shader Editor is the graph, its Hypershade sidebar "
        "tab the browser (add nodes with Shift+A)."),
    **{f"Render/{item}": (
        "Command line", "Blender has no batch render queue: render frames with blender -b file.blend -a "
        "(or Render Sequence here).") for item in ("Batch Render", "Cancel Batch Render", "Show Batch Render")},
    "Render/IPR Render Current Frame": (
        "Viewport Rendered", "Blender's IPR is the viewport in Rendered shading (Render Region: Ctrl+B)."),
    # FX (step 68, , )
    **{path: ("one-point mesh emitter", "Blender particles come from a mesh: Maya Kit makes a one-point mesh emitter1 "
              "with the particles, sized in Maya units.")
       for path in ("nParticles/Create Emitter", "nParticles/Create Emitter#2")},
    "nCloth/Create nCloth": (
        "Cloth modifier", "Blender cloth simulates real sizes: Maya Kit scales collision distances, stiffness and gravity "
        "so one unit moves like Maya's (nucleus Space Scale in the Attribute Editor)."),
    **{f"nCache/{item}": (
        "Baked caches", "Blender always plays a baked cache: Delete Cache to simulate again.")
       for item in ("Enable All Caches on Selected", "Disable All Caches on Selected")},
    # Lights (PLAN W5, )
    **{f"Create/Lights/{kind} Light": (
        f"{kind} light", "Blender lights always get darker with the square of the distance (no No Decay); "
        "Maya Kit scales the power to the Maya unit.") for kind in ("Point", "Spot", "Area")},
    # Rigging (W3: HumanIK / Quick Rig -> Rigify)
    **{path: ("Rigify", "Blender has no HumanIK / Quick Rig: the bundled Rigify add-on builds a rig from a "
                        "meta-rig fitted to the mesh (Generate Rig).")
       for path in ("Skeleton/HumanIK", "Skeleton/Quick Rig", "Windows/Animation Editors/HumanIK",
                    "Windows/Animation Editors/Quick Rig")},
    # Scene / files (W3: Reference -> link + library override, Set Project -> relative paths)
    # Scene management (step 69, operators/project.py, )
    "File/Create Reference...": (
        "Link + Library Override", "Blender references are linked .blend files: Maya Kit makes them editable "
        "(library override) and prefixes the names with the namespace (ns:name)."),
    "File/Reference Editor": (
        "Outliner: Blender File", "Linked files are listed in the Outliner's Blender File view (right-click: "
        "Reload / Relocate)."),
    "File/Set Project...": (
        "Maya Kit project", "Blender has no projects: Maya Kit keeps this folder, opens file dialogs in its scenes "
        "folder and renders to its images folder."),
    "File/Project Window": (
        "Maya Kit project", "Blender has no projects: Maya Kit makes Maya's project folders and keeps the folder "
        "as your project."),
    # UV (step 66): Blender cuts / sews UVs in the UV Editor only
    "UV/Auto Seams": (
        "Smart UV Project", "Blender has no automatic seams: UV > Automatic (Smart UV Project) cuts by angle."),
    # Modeling (step 64): the Crease Tool works, with Blender's 0-1 crease underneath
    "Mesh Tools/Crease Tool": (
        "Edge crease", "Blender stores creases as 0-1 (1 = fully sharp). The kit shows Maya's value (sharp for that "
        "many smooth levels) and stores sqrt(value / 10); see it with 3 (smooth mesh preview)."),
    # FX (W3: nucleus -> scene gravity + per-object settings; Gravity field)
    "Modify/Evaluate Nodes/nucleuses": (
        "Scene gravity", "Blender has no nucleus node: gravity is in Scene properties, solver settings are per object."),
    "Fields/Solvers/Gravity": (
        "Wind field", "Blender has no gravity field: a wind field blowing down; the scene's gravity is global "
        "(Scene properties)."),
}


# Step 101: mapped items whose Blender result differs from Maya's.
NOTICES.update({
    "File/Archive Scene": (
        "Pack Resources", "Blender packs textures and sounds into the .blend instead of zipping the scene folder."),
    **{f"File/{item}": ("FBX export", "Blender has no game-engine live links: export FBX (Unity / Unreal read it).")
       for item in ("Game Exporter", "Send To Unity", "Send To Unreal")},
    "File/View Sequence...": (
        "Play Rendered Animation", "Blender plays the render output frames (Render > View Animation)."),
    "Edit/Delete All by Type/Shading Groups and Materials": (
        "Purge Unused Data", "Blender removes unused materials (and other unused data) with File > Clean Up > Purge."),
    "Modify/Replace Objects": (
        "Link Object Data", "Blender gives the selected objects the active object's mesh (Object > Link/Transfer Data)."),
    "Modify/Evaluate Nodes/Evaluate All": (
        "Always evaluated", "Blender always evaluates every modifier and constraint: nothing to switch on."),
    "Playback/Playback Looping/Continuous": (
        "Continuous", "Blender playback always loops: Continuous is already on."),
    **{f"Display/Heads Up Display/{item} Details": (
        "Statistics overlay", "Blender's Statistics overlay shows the object and selection counts.")
       for item in ("Object", "Selection")},
    "Display/Toggle Show/Hide": (
        "Maya visibility toggle", "Blender: same as h (selected objects shown / hidden)."),
    **{f"Mesh Tools/Sculpting Tools/{maya} Tool": (brush, f"Blender has no {maya} brush: the {brush} sculpt brush "
                                                          "is the closest.")
       for maya, brush in (("Foamy", "Clay"), ("Wax", "Clay Strips"), ("Knife", "Crease Sharp"),
                           ("Amplify", "Sharpen"), ("Freeze", "Mask"))},
    "Deform/Cluster": ("Hook", "Blender clusters are Hook modifiers on the selected vertices (edit mode)."),
    "Deform/Nonlinear/Sine": ("Wave modifier", "Blender has no sine deformer: the Wave modifier ripples the surface."),
    **{f"Deform/Paint Weights/{kind}": (
        "Weight Paint", "Blender deformer weights are vertex groups: pick the modifier's group and paint it.")
       for kind in ("Blend Shape", "Cluster", "Delta Mush", "Tension", "Proximity Wrap", "Lattice", "ShrinkWrap",
                    "Wire", "Nonlinear", "Jiggle", "Texture Deformer")},
    **{f"Constrain/{item}": ("Shrinkwrap constraint", "Blender sticks an object to a surface with a Shrinkwrap "
                                                     "constraint (Nearest Surface Point).")
       for item in ("Closest Point", "Point On Poly")},
    "Constrain/Rivet": ("Vertex parent", "Blender: select the object, then vertices of the mesh, Vertex Parent (Ctrl+P)."),
    "Toon/Assign Outline": ("Line Art", "Blender draws toon outlines with a Line Art Grease Pencil object."),
    "Stereo/Create/Stereo Camera": (
        "Stereoscopy", "Blender stereo = a camera with Render > Stereoscopy (Views) on, no stereo rig."),
    "Audio/Import Audio Clip to Time Editor...": (
        "Sound strip", "Blender has no Time Editor: the sound becomes a Video Sequencer strip."),
    **{f"Cache/Geometry Cache/{item}": ("Alembic", "Blender writes / reads geometry caches as Alembic (.abc) "
                                                   "files, played by a Mesh Sequence Cache modifier.")
       for item in ("Create New Cache", "Import Cache...", "Export Cache")},
    **{f"Cache/GPU Cache/{item}": ("Alembic", "Blender has no GPU cache node: GPU caches are Alembic files.")
       for item in ("Import...", "Export All...", "Export Selection...")},
    "Help/Maya Help": ("Blender Manual", "Blender's manual opens in the web browser."),
    "Help/About Maya": ("About Blender", "Blender's About shows its version (Maya Kit is an extension)."),
})

# Greyed items (no Blender action in Maya Kit) by Maya menu path prefix: (closest Blender feature, one line).
# notices.category picks the longest matching prefix; tests/test_step101_menu_honesty.py checks that every
# greyed menu item has a notice and that every rule here matches at least one greyed item.
# (Create Description... / Create Interactive Groom Splines are mapped to a new hair Curves object.)
_XGEN_ITEMS = ("XGen Editor", "XGen Library", "Import Collections or Descriptions...",
               "Export Collections or Descriptions...", "Export Selection as Archive(s)...",
               "Batch Convert Scenes to Archives...", "Convert XGen Primitives to Polygons...",
               "Convert to Interactive Groom...", "Import Preset...", "Export as Preset...",
               "Interactive Groom Editor", "Interactive Grooming Tools", "Cache",
               "Convert Interactive Groom to Polygons...", "Display HUD")
CATEGORIES = {
    # whole Maya-only systems
    "Surfaces": ("NURBS surface edit mode", "Blender's NURBS surfaces can be edited (CVs, Open/Close, Revolve = "
                 "Screw modifier) but have no Loft, Trim, Fillet or Stitch: model with polygons."),
    "Generate": ("Grease Pencil / Geometry Nodes", "Blender has no Paint Effects: draw strokes with Grease Pencil, "
                 "scatter geometry with Geometry Nodes."),
    **{f"Generate/{item}": ("Hair curves", "Blender has no XGen: hair is a Curves object groomed in Sculpt mode "
                            "with Geometry Nodes hair modifiers.") for item in _XGEN_ITEMS},
    "Generate/Character Generator": ("none", "Blender has no character web service: model or import the character."),
    "Generate/ReCap": ("Import", "Blender has no ReCap link: import point clouds / meshes from files (PLY, OBJ)."),
    "nHair": ("Hair curves", "Blender hair = Curves objects groomed in Sculpt mode; there are no follicles or "
              "nHair dynamics (use the Hair Dynamics node group)."),
    "nConstraint": ("Cloth pin group / Rigid Body Constraint", "Blender has no nConstraints: pin cloth with a "
                    "vertex group (Cloth > Shape > Pin Group), connect rigid bodies with Rigid Body Constraints."),
    "nCloth": ("Cloth modifier", "Blender cloth is a Cloth modifier (Physics properties): rest shape, output space "
               "and texture maps are not separate nodes."),
    "nCache": ("Physics cache (Bake)", "Blender caches each simulation in its Physics properties (Bake / Free "
               "Bake): merging, replacing or editing cache frames isn't available."),
    "nParticles": ("Particle system", "Blender particles are a particle system on a mesh: instancing = Render As "
                   "Object / Collection; there are no goals, sprite wizard or collision events."),
    "Fluids": ("Mantaflow fluid", "Blender fluids are Mantaflow domains (Physics > Fluid): no 2D containers, "
               "contents painting, ponds or boats; Ocean is a modifier."),
    "Fields/Solvers": ("Force fields / Rigid Body World", "Blender fields are Force Field objects; rigid body "
                       "solvers, keys and initial states are in Scene > Rigid Body World and each Physics tab."),
    "Effects": ("Quick Effects", "Blender's Object > Quick Effects has Smoke, Fire, Liquid and Explode; Fireworks, "
                "Lightning, Shatter and Flow aren't built in (Cell Fracture extension for Shatter)."),
    "Toon": ("Line Art / Freestyle", "Blender toon lines are Line Art (Grease Pencil) or Freestyle; line attributes "
             "are Line Art modifiers, not painted maps."),
    "Toon/Assign Fill Shader": ("Shader to RGB material", "Blender toon fills are materials with Shader to RGB + a "
                                "Color Ramp (EEVEE)."),
    "Stereo": ("Stereoscopy (Views)", "Blender stereo = Render > Stereoscopy with the camera's Stereoscopy "
               "settings: there are no stereo rigs or camera links."),
    "Audio": ("Sound strips", "Blender sounds are Video Sequencer strips (waveforms show in the Sequencer); "
              "No sounds available is greyed in Maya too."),
    "Cache/Geometry Cache": ("Alembic / Mesh Sequence Cache", "Blender plays geometry caches as Alembic files in a "
                             "Mesh Sequence Cache modifier: replacing, merging or editing cache frames isn't available."),
    "Cache/Alembic Cache": ("Alembic import", "Blender's Alembic import already keeps the file linked (Mesh Sequence "
                            "Cache); replace = import again, About = the Blender manual."),
    "Cache/GPU Cache": ("Cache File properties", "Blender has no GPU cache node: reload an imported Alembic from its "
                        "Cache File properties."),
    "Help": ("Blender Help menu", "Blender has no Autodesk account, product research or analytics services; "
             "Blender's Help menu has the manual and bug reports."),
    "Control": ("Keying Sets / bone collections", "Blender has no character sets or controller tags: Keying Sets key "
                "a chosen set of channels, bone collections group the controls."),
    # rigging / animation
    "Key": ("Keying Sets", "Blender has no character sets: a Keying Set (Scene properties) keys a chosen set of "
            "channels; the Attribute Editor is the Properties editor."),
    "Key/IK": ("IK constraint Influence", "Blender switches IK / FK by keying the IK constraint's Influence."),
    "Key/Scene Time Warp": ("NLA strip time", "Blender has no scene time warp: remap time per action with an NLA "
                            "strip's Scale / Repeat or a Time Offset modifier."),
    "Key/Scale Keys": ("Scale in the Graph Editor", "Blender scales keys in the Graph Editor / Dope Sheet: select "
                       "the keys and press S."),
    "Key/Set Blend Shape Target Weight Keys": ("Shape key Value", "Blender keys a shape key's Value in the Shape "
                                               "Keys panel (I over the field)."),
    "Skeleton": ("Armature edit / pose mode", "Blender: preferred angles = the rest pose, IK handles are IK "
                 "constraints (switch with Influence), reroot = re-parent bones in edit mode."),
    "Skeleton/Joint Labelling": ("Bone names (.L / .R)", "Blender has no joint labels: side and role come from bone "
                                 "names (.L / .R suffixes drive mirroring and Symmetrize)."),
    "Skin": ("Vertex groups / Weight Paint", "Blender skin weights are vertex groups edited in Weight Paint mode "
             "(Weights menu: Normalize, Mirror, Clean, Limit Total); no influence objects or interactive bind."),
    "Deform": ("Modifiers", "Blender deformers are modifiers (Properties > Modifiers) with vertex-group weights: no "
               "deformer sets, intermediate objects or tweak nodes."),
    "Constrain": ("Object / bone constraints", "Blender: Normal / Tangent = Shrinkwrap or Track To, UV Pin / "
                  "Proximity Pin = vertex parenting; targets are edited in the Constraints tab."),
    "Constrain/Motion Paths": ("Follow Path constraint", "Blender follows a curve with a Follow Path constraint "
                               "(animate its Offset); there are no flow path lattices or motion path keys."),
    "Visualize": ("Motion Paths", "Blender shows motion with Motion Paths (Object properties); object ghosting, "
                  "snapshots and turntables aren't built in (Grease Pencil has onion skinning)."),
    "Playback": ("Timeline Playback popover", "Blender's playback options are in the Timeline's Playback popover; "
                 "there is no cached-playback toggle or stepped preview."),
    # rendering
    "Render": ("Render properties", "Blender's render settings are in Properties > Render / Output: render "
               "diagnostics, Backburner and NURBS tessellation have no counterpart."),
    "Texturing": ("Shader Editor / Texture Paint", "Blender has no PSD networks or texture reference objects: "
                  "textures are image nodes in the Shader Editor, painted in Texture Paint mode."),
    "Lighting/Shading": ("Light Linking", "Blender light / shadow linking is a collection per light (Object "
                         "properties > Shading > Light Linking); Transfer Maps = Cycles Bake."),
    # modeling
    "UV": ("UV Editor", "Blender: grab UVs with G in the UV Editor, delete UVs by removing the UV map (Data "
           "properties > UV Maps)."),
    "Mesh Display": ("Normals / Color Attributes", "Blender's normals are under Mesh > Normals (custom normals), "
                     "vertex colors are Color Attributes (Data properties)."),
    **{f"Mesh Display/{sub}": ("Color Attribute node", "Blender mixes vertex colors into materials with a Color "
                               "Attribute node in the Shader Editor, not a per-object setting.")
       for sub in ("Color Material Channel", "Material Blend Setting")},
    "Mesh Display/Per Instance Sharing": ("Linked data", "Blender instances share mesh data (Alt+D, Object > "
                                          "Link/Transfer Data); per-instance attributes aren't available."),
    "Mesh Tools": ("Edit mode tools", "Blender: Make Hole = Boolean modifier, paint reduce / transfer weights = "
                   "vertex groups on Decimate / Data Transfer modifiers."),
    "Mesh Tools/Sculpting Tools": ("Sculpt mode", "Blender has no Spray / Repeat / Imprint stamps or Maya sculpt "
                                   "targets: use a textured Draw brush, or sculpt on a shape key."),
    "Mesh": ("Object > Link/Transfer Data", "Blender has no attribute clipboard or vertex-order transfer: Object > "
             "Link/Transfer Data copies data between objects."),
    "Mesh/Smooth Proxy": ("Subdivision Surface modifier", "Blender's smooth proxy is the Subdivision Surface "
                          "modifier: there is no mirror proxy."),
    "Edit Mesh": ("Edit mode", "Blender: invisible faces = delete or hide faces, reorder vertices = Mesh > Sort "
                  "Elements, project a curve = Knife Project."),
    "Curves": ("Curve edit mode", "Blender curves don't have this command: use curve edit tools or Geometry Nodes "
               "(Resample = Rebuild, Fillet Curve, Offset, Trim)."),
    # common menus
    "Create": ("Add menu (Shift+A)", "Blender doesn't have this built in; Add (Shift+A) and the Extra Objects "
               "extension have the closest shapes."),
    "Create/Polygon Primitives": ("Extra Objects extension", "Blender has no pipe, helix, gear, soccer ball or "
                                  "super ellipse built in (the Extra Objects extension has them); creation is "
                                  "never interactive."),
    "Create/NURBS Primitives": ("Add > Surface", "Blender's NURBS primitives are in Add > Surface (no cube, cone or "
                                "square); objects are created at once, never interactively."),
    "Create/Subdiv Primitives": ("Subdivision Surface modifier", "Blender has no subdiv surface type: a polygon "
                                 "primitive with a Subdivision Surface modifier (3 = smooth preview)."),
    "Create/Volume Primitives": ("Volume / Mesh to Volume", "Blender has no volume primitives: a Volume object or a "
                                 "Mesh to Volume modifier."),
    "Create/Lights": ("World / volume shader", "Blender has no ambient or volume light: World lighting (ambient) or "
                      "a light with a volume shader."),
    "Create/Curve Tools": ("Curve Draw tool", "Blender draws curves with the Draw tool in curve edit mode; EP and "
                           "arc tools aren't built in."),
    "Create/Measure Tools": ("Measure tool", "Blender's Measure tool measures distances and angles; parameter and "
                             "arc length tools aren't built in."),
    "Create/Asset": ("Asset Browser", "Blender assets are data-blocks marked as assets (Asset Browser), not "
                     "containers."),
    "Create/Scene Assembly": ("Collection instance", "Blender's scene assemblies are collection instances (Add > "
                              "Collection Instance)."),
    "Create/Sweep Mesh": ("Curve Bevel", "Blender sweeps a profile along a curve with the curve's Bevel (Object / "
                          "Profile) or Geometry Nodes Curve to Mesh."),
    "Select": ("Select menu", "Blender has no selection by this type or constraint: Select All by Type, Select "
               "Linked and Select Similar are the closest."),
    **{f"Select/{sub}": ("Curve edit mode", "Blender selects curve and surface control points in edit mode (Tab); "
                         "hulls, isoparms and edit points aren't separate components.")
       for sub in ("Components#2", "Components#3", "CV Selection Boundary", "Surface Border", "Cluster Curve")},
    "Select/Convert Selection": ("UV Editor / Select menu", "Blender has no vertex-face or UV components in the 3D "
                                 "View: UVs are selected in the UV Editor (UV Sync Selection)."),
    "Modify": ("Object menu", "Blender has no command by this name: see Object > Transform / Apply / Snap."),
    "Modify/Asset": ("Asset Browser / library overrides", "Blender has no assets with published attributes: mark "
                     "data-blocks as assets, expose values with library overrides or custom properties."),
    "Modify/Evaluate Nodes": ("Always evaluated", "Blender always evaluates every modifier and constraint; switch "
                              "one off with its Show in Viewport toggle."),
    "Modify/Convert": ("Object > Convert", "Blender converts curves, text, meshes and Grease Pencil; subdiv surfaces, "
                       "Paint Effects, displacement and fluids aren't separate types."),
    "Modify/Transformation Tools": ("Toolbar transform tools", "Blender's default manipulator is the active tool's "
                                    "gizmo: there is no Show Manipulator, Type or Default Object Manipulator."),
    "Edit": ("Edit menu", "Blender has no LOD groups, fur or attribute-value transfer: Object > Link/Transfer Data "
             "copies data between objects."),
    **{f"Edit/{sub}": ("Outliner / Purge", "Blender has no node of this type: delete it in the Outliner, or File > "
                       "Clean Up > Purge for unused data.") for sub in ("Delete All by Type", "Delete by Type")},
    "Edit/Keys": ("Scale in the Graph Editor", "Blender scales keys in the Graph Editor / Dope Sheet: select the keys "
                  "and press S."),
    "File": ("File menu", "Blender has no offline files, ATOM or After Effects Live Link: move animation with "
             "Append / Link or FBX / Alembic export."),
    "Display": ("Viewport Overlays", "Blender draws this through the Viewport Overlays popover or Object properties > "
                "Viewport Display; there is no per-camera visibility."),
    "Windows": ("Blender editors", "Blender has no editor by this name: any area's editor-type menu gives the "
                "closest editor."),
    **{f"Windows/{item}": ("Window menu", "Blender windows are managed by the OS (Window > Toggle Window Fullscreen); "
                           "there is no Home screen.")
       for item in ("Home", "Minimize Application", "Raise Main Window", "Raise Application Windows")},
}


SHOW_SECONDS = 5.0
_current = {"text": "", "until": 0.0}
_status_area = []   # the status bar area, seen while drawing it (global areas aren't in screen.areas)


def notice(path):
    """(substitute, line) written for this Maya menu path, or None."""
    return NOTICES.get(path)


def category(path):
    """(substitute, line) of the most specific CATEGORIES rule for ``path`` (longest prefix), or None."""
    best = None
    for prefix in CATEGORIES:
        if (path == prefix or path.startswith(prefix + "/")) and (best is None or len(prefix) > len(best)):
            best = prefix
    return CATEGORIES[best] if best is not None else None


def greyed_notice(path):
    """The notice a greyed (unmapped) item shows: its own, else its category's (step 101: none without one)."""
    return NOTICES.get(path) or category(path)


# Notices of kit panel rows that are not Maya menu items (e.g. Modeling Toolkit options, step 63),
# filled by the panels' register(); same (substitute, line) form.
PANEL_NOTICES = {}


def tooltip(path, mapped):
    """Tooltip text for a Maya menu item with a notice (also shows it in the Help Line)."""
    n = NOTICES.get(path) or PANEL_NOTICES.get(path) or (None if mapped else category(path))
    if n is None:
        return None
    substitute, line = n
    head = f"Maya: {path}  →  Blender: {substitute}" if mapped else f"Maya: {path} (greyed)  →  {substitute}"
    show(f"{path.rsplit('/', 1)[-1]}: {line}")
    return f"{head}\n{line}"


def show(text):
    """Put ``text`` in the Help Line for a few seconds."""
    _current["text"] = text
    _current["until"] = time.monotonic() + SHOW_SECONDS
    _redraw_status_later()
    if not bpy.app.timers.is_registered(_expire):
        bpy.app.timers.register(_expire, first_interval=SHOW_SECONDS + 0.1)


def current():
    return _current["text"] if time.monotonic() < _current["until"] else ""


def remember_status_area(area):
    if area is not None and (not _status_area or _status_area[0] != area):
        _status_area[:] = [area]


def _redraw_status():
    for area in _status_area:
        try:
            area.tag_redraw()
        except ReferenceError:
            _status_area.clear()
    return None


def _redraw_status_later():
    # Not from inside a tooltip / draw callback: one tick later.
    if not bpy.app.timers.is_registered(_redraw_status):
        bpy.app.timers.register(_redraw_status, first_interval=0.0)


def _expire():
    if not current():
        _current["text"] = ""
        _redraw_status()
        return None
    return 0.5


def register():
    pass


def unregister():
    for fn in (_expire, _redraw_status):
        if bpy.app.timers.is_registered(fn):
            bpy.app.timers.unregister(fn)
    _current.update(text="", until=0.0)
    _status_area.clear()
