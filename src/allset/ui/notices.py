# SPDX-License-Identifier: GPL-3.0-or-later
""" notices: the near substitute + one line, for Maya menu items ( 「Maya 워크플로우
계획」 W3,  「계획」 (b)).

One table for every place a Maya item has no Blender equivalent, or a different one: the item's tooltip
(greyed items: ``allset.menu_unavailable``; items with a substitute: ``allset.menu_item``) and the Help
Line, which shows the notice while the tooltip is up — Maya's Help Line shows a menu item's annotation the same
way (). Keys are Maya menu label paths (``ui/menu_sets.iter_items``).
"""

import time

import bpy

from .. import live_refs

# path: (substitute in Blender, one line). Paths with an action in menu_map.MAP run that substitute.
NOTICES = {
    # Windows > Settings/Preferences (step 120)
    "Windows/Settings/Preferences/Marking Menu Editor": (
        "Marking menus", "The marking menus are the kit's Maya layouts; Blender has no editor for them "
        "(Preferences > Keymap edits which key opens which menu)."),
    "Windows/Settings/Preferences/Shelf Editor": (
        "Shelves", "The shelves are Maya's factory shelves; there is no shelf editor (right-click a Blender "
        "button > Add to Quick Favorites keeps your own commands)."),
    "Windows/Settings/Preferences/Panel Editor": (
        "Workspaces", "Blender saves panel layouts as workspaces: drag area edges and save the file or "
        "use Windows > Workspaces."),
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
        "ns: name prefix", "Blender has no namespaces: Maya Workflow Kit keeps them as a \"ns:\" prefix in names."),
    # Rendering (W3: Light Editor -> kit light list, step 67)
    "Windows/Rendering Editors/Light Editor": (
        "kit Light Editor", "Blender has no Light Editor: Maya Workflow Kit lists the scene lights in a 3D View sidebar tab "
        "(Exposure is part of Power)."),
    "Windows/Rendering Editors/Hypershade": (
        "Shader Editor + kit list", "Blender has no Hypershade: the Shader Editor is the graph, its Hypershade sidebar "
        "tab the browser (add nodes with Shift+A)."),
    **{f"Render/{item}": (
        "Command line", "Blender has no batch render queue: render frames with blender -b file.blend -a "
        "(or Render Sequence here).") for item in ("Batch Render", "Cancel Batch Render", "Show Batch Render")},
    # step 109: mapped items whose Blender result differs
    "Create/NURBS Primitives/Square": (
        "Four NURBS curves", "Blender has no NURBS square: four straight NURBS curves under an empty, like Maya's group."),
    "Create/NURBS Primitives/Cube": (
        "Six NURBS patches", "Blender has no NURBS cube: six NURBS surface patches under an empty, like Maya's group."),
    "Create/NURBS Primitives/Cone": (
        "NURBS cylinder", "Blender has no NURBS cone: a NURBS cylinder with its top row of points closed."),
    "Create/Curve Tools/Pencil Curve Tool": (
        "Curve Draw tool", "Blender's Draw tool on a new curve in Edit Mode: drag to draw (on the 3D cursor's plane)."),
    "Create/Sweep Mesh": (
        "Curve bevel, converted", "Blender makes the mesh from a copy of the curve with a round bevel (8 sides); no live "
        "profile options."),
    "Curves/Add Points Tool": (
        "Extrude (E)", "Blender extrudes the curve's end points: move the mouse, click to place the new point."),
    "Curves/Offset/Offset Curve": (
        "Poly curve", "Blender's offset copy is a poly curve through the moved points, not a fitted NURBS curve."),
    "Surfaces/Loft": (
        "Mesh", "Blender can't loft NURBS surfaces: the loft is a quad mesh through the curves (active curve last)."),
    "Surfaces/Planar": (
        "Filled 2D curve", "Blender fills closed 2D curves: a copy of the curve, flattened onto its own XY plane."),
    "Surfaces/Extrude": (
        "Curve bevel object", "Blender bevels a copy of the path curve with the profile curve (select the profile "
        "first, the path last)."),
    "Surfaces/Bevel Plus": (
        "Curve extrude + bevel, converted", "Blender builds a mesh from the filled curve, extruded and bevelled both ways around "
        "the curve's plane."),
    "Mesh Tools/Sculpting Tools/Spray Tool": (
        "Draw Sharp brush", "Blender has no stamp spray brush: Draw Sharp is the closest (also sculpt Ctrl+8)."),
    "Mesh Tools/Sculpting Tools/Repeat Tool": (
        "Layer brush", "Blender has no repeating stamp brush: Layer is the closest (also sculpt Ctrl+9)."),
    "Fluids/Add/Edit Contents/Emit from Object": (
        "Quick Smoke", "Blender makes the selected meshes smoke flows inside a new Mantaflow domain."),
    "Fluids/Make Collide": (
        "Fluid effector", "Blender gives the selected meshes a Fluid modifier of type Effector."),
    "nCloth/Display Input Mesh": (
        "Cloth modifier off", "Blender shows the input mesh by turning the Cloth modifier off in the viewport."),
    "nCloth/Display Current Mesh": (
        "Cloth modifier on", "Blender shows the simulated mesh with the Cloth modifier on in the viewport."),
    "nHair/Paint Hair Follicles": (
        "Hair Sculpt mode", "Blender hair is a Curves object groomed in Sculpt mode: select one (Add > Curves > Empty "
        "Hair) and use the Add brush."),
    # step 110: mapped items whose Blender result differs
    "Mesh Tools/Make Hole": (
        "Bridged loops", "Blender faces can't have holes: the stamp outline is bridged to the face's border with "
        "quads (select the face to cut, then the stamp face)."),
    "Skeleton/Set Preferred Angle": (
        "Stored rotation", "Blender's IK bends from the rest pose: the angle is stored for Assume Preferred Angle, "
        "the solver doesn't read it."),
    "Skeleton/Create IK Spline Handle": (
        "Spline IK constraint", "Blender makes a Spline IK constraint on the end bone and the curve curve1; there is no "
        "ikHandle / effector node."),
    "Deform/Cluster": (
        "Hook modifier", "Blender's cluster is a Hook modifier driven by the clusterNHandle empty."),
    "Deform/Soft Modification Tool": (
        "Hook with falloff", "Blender's soft modification is a Hook modifier on the whole mesh with Maya's falloff "
        "(radius 5, smooth), driven by softModNHandle."),
    "Render/IPR Render Current Frame": (
        "Viewport Rendered", "Blender's IPR is the viewport in Rendered shading (Render Region: Ctrl+B)."),
    # FX (step 68, , )
    **{path: ("one-point mesh emitter", "Blender particles come from a mesh: Maya Workflow Kit makes a one-point mesh emitter1 "
              "with the particles, sized in Maya units.")
       for path in ("nParticles/Create Emitter", "nParticles/Create Emitter#2")},
    "nCloth/Create nCloth": (
        "Cloth modifier", "Blender cloth simulates real sizes: Maya Workflow Kit scales collision distances, stiffness and gravity "
        "so one unit moves like Maya's (nucleus Space Scale in the Attribute Editor)."),
    **{f"nCache/{item}": (
        "Baked caches", "Blender always plays a baked cache: Delete Cache to simulate again.")
       for item in ("Enable All Caches on Selected", "Disable All Caches on Selected")},
    # Lights (PLAN W5, ; step 137 operators/lights.py)
    **{f"Create/Lights/{kind} Light": (
        f"{kind} light", "Maya Decay Rate No Decay renders in Cycles; Blender EEVEE and the viewport get darker with the "
        "square of the distance, the power matching Maya intensity 1 at 10 units.") for kind in ("Point", "Spot")},
    "Create/Lights/Area Light": (
        "Area light", "Blender's area light falls off like Maya's; its power matches Maya intensity 1 (2 x 2 units)."),
    # Rigging (W3: HumanIK / Quick Rig -> Rigify)
    **{path: ("Rigify", "Blender has no HumanIK / Quick Rig: the bundled Rigify add-on builds a rig from a "
                        "meta-rig fitted to the mesh (Generate Rig).")
       for path in ("Skeleton/HumanIK", "Skeleton/Quick Rig", "Windows/Animation Editors/HumanIK",
                    "Windows/Animation Editors/Quick Rig")},
    # Scene / files (W3: Reference -> link + library override, Set Project -> relative paths)
    # Scene management (step 69, operators/project.py, )
    "File/Create Reference...": (
        "Link + Library Override", "Blender references are linked .blend files: Maya Workflow Kit makes them editable "
        "(library override) and prefixes the names with the namespace (ns:name)."),
    "File/Reference Editor": (
        "Outliner: Blender File", "Linked files are listed in the Outliner's Blender File view (right-click: "
        "Reload / Relocate)."),
    "File/Set Project...": (
        "Maya Workflow Kit project", "Blender has no projects: Maya Workflow Kit keeps this folder, opens file dialogs in its scenes "
        "folder and renders to its images folder."),
    "File/Project Window": (
        "Maya Workflow Kit project", "Blender has no projects: Maya Workflow Kit makes Maya's project folders and keeps the folder "
        "as your project."),
    # UV (step 66): Blender cuts / sews UVs in the UV Editor only
    "UV/Auto Seams": (
        "UV > Automatic", "Blender has no automatic seams: UV > Automatic cuts the mesh into shells by 6 projection "
        "planes, Smart UV Project (UV Editor) by angle."),
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
    "Help/About Maya": ("About Blender", "Blender's About shows its version (Maya Workflow Kit is an extension)."),
})

# Greyed items (no Blender action in Maya Workflow Kit) by Maya menu path prefix: (closest Blender feature, one line).
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
                 "Screw modifier) but have no Trim, Fillet or Stitch (Loft, Planar, Extrude and Bevel Plus are "
                 "built by Maya Workflow Kit): model with polygons."),
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
    "Key/Set Blend Shape Target Weight Keys": ("Shape key Value", "Blender keys a shape key's Value in the Shape "
                                               "Keys panel (I over the field)."),
    "Skeleton": ("Armature edit / pose mode", "Blender: IK handles are IK constraints (switch with Influence), "
                 "joints are bone heads edited in armature edit mode."),
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
    "Mesh Tools": ("Edit mode tools", "Blender: paint reduce / transfer weights = vertex groups on Decimate / "
                   "Data Transfer modifiers."),
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


def _anim_editor_categories(ed):
    """Greyed items of the Graph Editor / Dope Sheet menu bars (step 104, menus captured in Maya 2022)."""
    return {
        f"{ed}/Edit/Transformation Tools": (
            "G / S on keys", "Blender moves and scales keys with G and S (or by dragging): it has no lattice, region "
            "or retime key tool."),
        f"{ed}/Edit/Select Unsnapped": (
            "Snap", "Blender can't select the keys off whole frames: Edit > Snap puts the selected keys on frames."),
        f"{ed}/Edit/Select Curve Nodes": (
            "F-curves", "Blender's curves are F-curves inside an Action, not scene nodes you can select."),
        f"{ed}/Edit/Set Curve Colors...": (
            "Change Curve Color", "Blender colours curves one selection at a time: Edit > Change Curve Color."),
        f"{ed}/Edit/Scene Time Warp": (
            "Time Stretching", "Blender has no time warp curve: Output Properties > Frame Range > Time Stretching "
            "remaps the whole scene."),
        f"{ed}/Curves": (
            "Graph Editor Key / Channel menus", "Blender has no such curve command: its curve tools are in the Graph "
            "Editor's Key and Channel menus (Smooth, Decimate, Clean, Bake, Euler Filter)."),
        f"{ed}/Curves/Change Rotation Interp": (
            "Rotation Mode", "Blender interpolates each rotation channel on its own; Euler / Quaternion is the "
            "object's Rotation Mode (sidebar Item tab)."),
        f"{ed}/Curves/Spreadsheet...": (
            "Sidebar F-Curve tab", "Blender edits key values in the sidebar (F-Curve > Active Keyframe), not in a "
            "spreadsheet."),
        f"{ed}/Curves/Default Tangent Weight": (
            "Bézier handles", "Blender's Bézier handles always have a length (weighted tangents): there is no "
            "non-weighted mode."),
        **{f"{ed}/Curves/{item}": (
            "Bézier handles", "Blender's Bézier handles always have a length (weighted tangents): there is nothing to "
            "convert.") for item in ("Non-weighted Tangents", "Weighted Tangents")},
        f"{ed}/Keys": (
            "Channel mute / I key", "Blender mutes whole channels, not single keys, and inserts keys with I or "
            "Ctrl+right-click."),
        **{f"{ed}/Tangents/{sub}": (
            "Preferences > Animation", "Blender has no flat default: new keys get Auto Clamped, Auto, Vector, Aligned "
            "or Free handles.") for sub in ("Default In Tangent", "Default Out Tangent")},
        **{f"{ed}/Tangents/{item}": (
            "Handle types", "Blender's handles keep their own length: lengths are never locked or freed.")
           for item in ("Lock Tangent Length", "Free Tangent Length")},
        f"{ed}/List": (
            "Only Show Selected", "Blender lists the selected objects' channels (List > Auto Load Selected Objects); "
            "it has no bookmarks or manual loading."),
        f"{ed}/Show": (
            "Channel filters", "Blender filters channels by data type and by name (header filter popover); Maya's "
            "other node and attribute filters aren't there."),
        f"{ed}/Help/What's New/Highlight What's New": (
            "Release notes", "Blender doesn't highlight new menu items: Help > What's New lists them."),
    }


CATEGORIES.update({
    **_anim_editor_categories("Graph Editor"),
    **_anim_editor_categories("Dope Sheet"),
    "Graph Editor/View": (
        "View menu", "Blender's Graph Editor has no such display option: see its View menu and the sidebar View tab "
        "(Blender ▸ menu)."),
    "Graph Editor/View/Theme": (
        "Themes", "Blender's colours come from the theme: Preferences > Themes (install a Maya-like theme there if you want "
        "Maya's colours)."),
    "Graph Editor/View/Curve Name": (
        "Channel list", "Blender doesn't write curve names in the graph: they are in the channel list."),
    "Graph Editor/Select": (
        "Select menu", "Blender has no selection mask: it selects keys with their handles (click a handle to pick "
        "it alone)."),
    "Dope Sheet/View": (
        "View menu", "Blender's Dope Sheet always draws its ticks and has no scene summary or auto frame."),
    "Dope Sheet/Curves": (
        "Graph Editor", "This curve filter is in Blender's Graph Editor only (Windows > Animation Editors > Graph "
        "Editor)."),
    "UV Editor/Edit": (
        "Select All + Unpin", "Blender's UVs can't be deleted (every face has them); Unpin All = Select > All, then "
        "Unpin Selection."),
    "UV Editor/Edit/Reset UV Editor UI": (
        "Load Factory Settings", "Blender resets editors with File > Defaults > Load Factory Settings."),
    "UV Editor/Select": (
        "Select menu", "Blender's UV Select menu has no such filter: Select Linked, Split, Overlap, Pinned and "
        "Shortest Path are there."),
    "UV Editor/Select/Convert Selection": (
        "Select mode", "Blender converts only between vertex, edge, face, UV and shell (the UV Toolkit icons)."),
    "UV Editor/Cut/Sew": (
        "Seams / Rip", "Blender makes shells from seams (Cut, Unwrap) and splits UVs with the Rip tool; it has no "
        "auto seams or grid shells."),
    "UV Editor/Modify": (
        "UV menu", "Blender has no such UV layout command: Pack Islands, Align, Snap and Average Islands Scale are "
        "its tools."),
    "UV Editor/Tools": (
        "UV tools", "Blender's UV tools are Select, Move / Rotate / Scale, Rip and the Grab / Relax / Pinch sculpt "
        "brushes."),
    "UV Editor/View": (
        "Overlays", "Blender's UV Editor has no such display option: see its Overlays popover and View menu."),
    "UV Editor/View/Isolate Select": (
        "Hide", "Blender isolates UVs by hiding the rest: UV > Show/Hide Faces (H / Shift+H)."),
    "UV Editor/Image": (
        "Image field", "Blender shows one image (header image field): no dimming, PSD networks, bake preview or pixel "
        "ruler."),
    "UV Editor/Textures": (
        "Image field", "Blender lists the images in the header image field."),
    "UV Editor/UV Sets": (
        "UV Maps", "Blender's UV sets are UV Maps (Object Data Properties > UV Maps: rename there; no per-instance "
        "sharing)."),
    "UV Editor/Help/What's New/Highlight What's New": (
        "Release notes", "Blender doesn't highlight new menu items: Help > What's New lists them."),
    "UV Toolkit/Options": (
        "Panel sections", "Blender's panels have no settings reset: fold the sections by hand."),
})


SHOW_SECONDS = 5.0
_current = {"text": "", "until": 0.0}
# [(window pointer, status bar area)] seen while drawing it. Global areas aren't in screen.areas, so the area can't be
# found again by pointer; it lives as long as its window, so it is only touched while that window is open (#36).
_status_area = []


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


def remember_status_area(area, window=None):
    window = window or bpy.context.window
    if area is not None and window is not None and (not _status_area or _status_area[0][1] != area):
        _status_area[:] = [(window.as_pointer(), area)]


def _redraw_status():
    for win_ptr, area in list(_status_area):
        if live_refs.window(win_ptr) is None:
            _status_area.clear()
            continue
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


class ALLSET_OT_tip(bpy.types.Operator):
    """A note about the Blender side of a Maya window, shown as a tooltip instead of a sentence in the window
; clicking puts it in the Help Line"""
    bl_idname = "allset.tip"
    bl_label = "Note"
    bl_options = {'INTERNAL'}

    text: bpy.props.StringProperty(options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, props):
        return props.text

    def execute(self, context):
        if self.text:
            show(self.text)
        return {'FINISHED'}


def tip(layout, text, label="", icon='INFO'):
    """A flat button whose tooltip is ``text`` (Maya windows carry no Blender explanation sentences)."""
    op = layout.operator(ALLSET_OT_tip.bl_idname, text=label, icon=icon, emboss=False)
    op.text = text
    return op


def register():
    bpy.utils.register_class(ALLSET_OT_tip)


def unregister():
    bpy.utils.unregister_class(ALLSET_OT_tip)
    for fn in (_expire, _redraw_status):
        if bpy.app.timers.is_registered(fn):
            bpy.app.timers.unregister(fn)
    _current.update(text="", until=0.0)
    _status_area.clear()

# Mapped editor items that run a near substitute (step 104): Maya 2022's newer auto tangents are one Blender handle.
NOTICES.update({
    f"{ed}/Tangents/{sub}Auto/{kind}": (
        "Auto Clamped handles", "Blender has one auto tangent (Auto Clamped): Maya's Ease / Mix / Custom weights "
        "aren't there.")
    for ed in ("Graph Editor", "Dope Sheet") for sub in ("", "In Tangent/", "Out Tangent/")
    for kind in ("Auto Ease", "Auto Mix", "Auto Custom")})


# Greyed items of the Hypershade / Render Settings / Script Editor menu bars (step 105, captured in Maya 2022)
CATEGORIES.update({
    "Hypershade/File": (
        "File > Append", "Blender shares shading networks by appending or linking materials from another .blend "
        "(File > Append), not by exporting a network file."),
    "Hypershade/Edit": (
        "Shader Editor", "Blender has no such Hypershade command: PSD networks, texture conversion and swatch "
        "rendering aren't there; edit the network in the Shader Editor."),
    "Hypershade/Edit/Delete All by Type": (
        "Outliner / Purge", "Blender has no node of this type to delete: use the Outliner (Blender File view) or "
        "File > Clean Up > Purge."),
    "Hypershade/Edit/Select All by Type": (
        "Outliner", "Blender selects materials and textures in the Outliner's Blender File view, not in the scene."),
    "Hypershade/Edit/Duplicate": (
        "Duplicate", "Blender copies a material with its whole node tree (Duplicate / Shading Network)."),
    "Hypershade/Create": (
        "Shift+A in the Shader Editor", "Blender has no node of this Maya type: add the closest node with Shift+A "
        "in the Shader Editor."),
    "Hypershade/Create/Materials": (
        "Principled BSDF", "Blender has no game, hair-tube, ocean or USD Preview shader of this kind: start from a "
        "Standard Surface (Principled BSDF)."),
    "Hypershade/Create/Volumetric Materials": (
        "Volume shaders", "Blender's volumes are shaders on the material's Volume output (Principled Volume) or the "
        "World's: add them with Shift+A > Volume."),
    "Hypershade/Create/Lights": (
        "World light", "Blender has no ambient or volume light: light the scene with the World colour."),
    "Hypershade/Create/Image Plane": (
        "Image Plane", "Blender's image planes are made in the 3D View (Create > Free Image Plane)."),
    "Hypershade/Create/Rendering": (
        "View Layers / AOVs", "Blender's render passes are View Layer passes (View Layer Properties > Passes)."),
    "Hypershade/Create/Glow": (
        "Bloom / Glare", "Blender makes glow in the compositor (Glare node)."),
    "Hypershade/Create/Particle Utilities": (
        "Attribute node", "Blender's particles feed shaders through the Particle Info / Attribute nodes."),
    "Hypershade/Create/Switch Utilities": (
        "Mix nodes", "Blender switches between inputs with Mix nodes (or Geometry Nodes Switch)."),
    "Hypershade/Create/Create Options": (
        "Shader Editor", "Blender materials always have their output node; textures get their own Mapping node."),
    "Hypershade/Tabs": (
        "Node groups / workspaces", "Blender's Shader Editor has one graph per material: no Hypershade tabs (use "
        "node groups or another workspace)."),
    "Hypershade/Graph": (
        "Shader Editor", "Blender shows the whole node tree of the material: there is no partial graph to build."),
    "Hypershade/Window": (
        "Blender editors", "Blender has no such Hypershade panel: the material preview is in the Properties "
        "Material tab."),
    "Hypershade/Options": (
        "Preferences", "Blender's Shader Editor has no such option (see Preferences > Editing / Interface)."),
    "Hypershade/Help/What's New/Highlight What's New": (
        "Release notes", "Blender doesn't highlight new menu items: Help > What's New lists them."),
    "Render Settings/Edit": (
        "Path field", "Blender has no project image directory: type the folder in the Common tab's Path field."),
    "Render Settings/Presets": (
        "Format presets", "Blender's render presets are the Format panel preset menu (Output Properties); Maya's "
        "AOV / user presets aren't there."),
    "Render Settings/Help/What's New/Highlight What's New": (
        "Release notes", "Blender doesn't highlight new menu items: Help > What's New lists them."),
    "Script Editor/File": (
        "Text Editor", "Blender sources a script by opening it and running it (Text > Run Script) and saves one text "
        "at a time; shelf buttons from scripts aren't there."),
    "Script Editor/History": (
        "Info editor filters", "Blender's history pane is the Info editor: it echoes every operator; its filters are "
        "in the Info editor's View menu."),
    "Script Editor/Command": (
        "Text Editor View menu", "Blender's Text Editor has no such option (see its View menu and Preferences > "
        "Editing > Text Editor)."),
    "Script Editor/Tabs": (
        "Text data-blocks", "Blender's script tabs are texts: rename one in the Text Editor header's name field."),
    "Script Editor/Help": (
        "Python API", "Blender has no help on a selected command: see the Python API reference (Help > Python "
        "Command Reference)."),
    "Script Editor/Help/What's New/Highlight What's New": (
        "Release notes", "Blender doesn't highlight new menu items: Help > What's New lists them."),
})


# Greyed marking-menu entries (step 136, ): key = "<menu proc>/<label path>" (the kit menu
# name in marking/menus.MENUS, then the labels down to the item), same (substitute, one line) form. While a marking
# menu hovers a greyed entry, marking/modal.py puts its line in the Help Line. tests/test_step136_items.py checks that
# every greyed entry has one and every key is a greyed entry.
_RMB_LIST = {
    "DG Traversal": ("Modifier stack", "Blender has no dependency graph to walk: an object's history is its modifier "
                     "stack (Channel Box INPUTS, Properties > Modifiers)."),
    "Inputs": ("Channel Box INPUTS", "Blender has no input nodes to list here: the object's modifiers and constraints "
               "are its INPUTS in the Channel Box."),
    "Outputs": ("Outliner", "Blender has no output connections to list: what uses this object shows in the Outliner "
                "(Blender File view)."),
    "Metadata": ("Custom properties", "Blender has no component metadata: store values as custom properties (Attribute "
                 "Editor Extra Attributes) or mesh attributes."),
    "Time Editor": ("NLA Editor", "Blender's clip-based animation editor is the NLA Editor (Windows > Animation "
                    "Editors)."),
}
MARKING = {
    **{f"{menu}/{label}": n for menu in ("dagMenuProc", "dagMenuProc_curve") for label, n in _RMB_LIST.items()},
    "dagMenuProc/Vertex Face": (
        "Face corners", "Blender has no vertex-face component: per-corner values (normals, colours, UVs) are edited "
        "on the face corners through their tools."),
    "dagMenuProc_curve/Curve Point": (
        "Control points", "Blender curves are edited by their control points only: there are no points on the curve "
        "to pick (Subdivide adds one)."),
    "dagMenuProc_curve/Hull": (
        "Control points", "Blender draws the control polygon but has no hull component: select its control points."),
    "dagMenuProc_curve/Edit Point": (
        "Control points", "Blender curves have no edit points: Bezier curves are edited by their knots and handles."),
    "buildObjectMenuItemsNow/Complete Tool": (
        "Enter", "Blender tools finish with Enter or a right-click: there is no tool to complete from this menu."),
    "buildObjectMenuItemsNow_pivot/Show Orientation Handle": (
        "Transform orientation", "Blender's pivot has no orientation handle: turn the pivot with a custom "
        "orientation (Orientation menu > Create)."),
    "contextPolyToolsVertexMM/Reorder Vertices": (
        "Sort Mesh Elements", "Blender can't set the vertex order from three picked vertices: Mesh > Sort Elements "
        "reorders them by a rule."),
    "contextPolyToolsEdgeMM/Merge/Collapse Edges/Merge Edge Tool": (
        "Merge / Bridge", "Blender has no tool that merges two clicked border edges: select both edges and use Merge "
        "(At Center) or Bridge."),
    "contextPolyToolsFaceMM/Assign Invisible Faces": (
        "Delete faces / Hide", "Blender's Subdivision Surface has no invisible faces: delete the faces or hide them "
        "(Display > Hide)."),
    **{f"contextPolyToolsDefaultMM/{label}": (
        "Extra Objects add-on", f"Blender has no {label.lower()} primitive by default: the free Extra Objects "
        "extension adds one (Preferences > Get Extensions).") for label in ("Pipe", "Helix", "Gear")},
    "polyConvertMM/Grow Selection/Grow Along Loop": (
        "Select Loops", "Blender grows a selection in every direction only: select the edge loop (Select > Select "
        "Loops) or use Grow."),
    "polyConvertMM/Shrink Selection/Shrink Selection Along Loop": (
        "Shrink", "Blender shrinks a selection in every direction only (Select > Shrink)."),
    "polyConvertMM/To UVs/To UV Perimeter": (
        "UV Editor", "Blender selects UV island borders in the UV Editor (Select > Select Split / island select), "
        "not from the 3D View."),
    "polyConvertMM/To Face Path": (
        "Shortest Path", "Blender picks a face path with Ctrl+click on the second face (Select > Shortest Edge Path)."),
    "translateMarkingMenuImpl/Snap/Face Center": (
        "Snap to Face", "Blender snaps to faces (Face Project / Face Nearest), not to their centres."),
    "translateMarkingMenuImpl/Keep Spacing": (
        "Snap With", "Blender moves the selected components together while snapping (Snap With in the snapping "
        "popover); there is no separate keep-spacing switch."),
    "translateMarkingMenuImpl/Axis/Live Object Axis": (
        "Custom orientation", "Blender has no live object axis: create an orientation from the object (Orientation "
        "menu > Create) and pick it."),
    "translateMarkingMenuImpl/Axis/Custom": (
        "Custom orientation", "Blender's custom axis is a saved orientation: Orientation menu > Create, from the "
        "selection."),
    "rotateMarkingMenuImpl/Custom/Custom": (
        "Custom orientation", "Blender's custom axis is a saved orientation: Orientation menu > Create, from the "
        "selection."),
    "rotateMarkingMenuImpl/Custom/Reset": (
        "Orientation: Object", "Blender keeps saved orientations until you delete them: pick Object to go back to "
        "the default rotate axis."),
    "scaleMarkingMenuImpl/Axis/Live Object Axis": (
        "Custom orientation", "Blender has no live object axis: create an orientation from the object (Orientation "
        "menu > Create) and pick it."),
    **{f"buildSelectAllMM/{label}": (
        "Modifier stack", "Blender's history is the modifier stack, which has no upstream / downstream nodes to "
        "select or switch off: show / hide modifiers in Properties > Modifiers.")
       for label in ("Select All Inputs", "Select All Outputs", "Enable All Outputs", "Disable All Outputs")},
    "HotboxNorthMenu/Persp/Relationship Editor": (
        "Workspaces", "Blender has no relationship editor layout: the Outliner and Properties sit beside the view "
        "in every workspace."),
    "HotboxEastMenu/Time Slider": (
        "Timeline area", "Blender's Time Slider is the Timeline area: drag its edge to hide it, or maximize the view "
        "(Ctrl+Space) for more room."),
    "HotboxEastMenu/Range Slider": (
        "Timeline header", "The Range Slider is part of the Timeline header in Blender: it hides with the Timeline."),
    "HotboxWestMenu/Hierarchy": (
        "Select > Hierarchy", "Blender has no hierarchy select mode: click the object and use Select > Hierarchy "
        "(or the Outliner) to take its children."),
    "HotboxWestMenu/Dynamics Mask": (
        "Object types filter", "Blender's dynamics are modifiers and physics settings on ordinary objects, so they "
        "have no selection mask of their own."),
    "contextPolyToolsUVMM/Create UV Shell": (
        "Unwrap", "Blender makes a UV island by unwrapping the selected faces (UV > Unwrap) or by cutting along "
        "seams."),
    "contextPolyToolsUVMM/Delete UVs": (
        "Unwrap / Reset", "Blender meshes keep UVs for every face: re-unwrap or Reset them (UV > Reset) instead of "
        "deleting."),
    **{f"{menu}/Auto Seams": (
        "Smart UV Project", "Blender has no automatic seam placement: Smart UV Project cuts by angle, or mark seams "
        "and Unwrap.") for menu in ("contextPolyToolsUVMM", "contextPolyToolsUVShellMM")},
    **{f"{menu}/Texture Borders": (
        "Seams overlay", "Blender's UV Editor draws island borders itself; the 3D View shows seams (Overlays > "
        "Seams).") for menu in ("contextPolyToolsUVMM", "contextPolyToolsUVShellMM")},
    "doSelectComponentMM/All Components off": (
        "Mesh select mode", "Blender always keeps vertex, edge or face picking on: switch with F9 / F10 / F11."),
    "doSelectComponentMM/Save to shelf": (
        "Quick Favorites", "Blender has no shelf button from a pick mask: right-click a select mode button > Add to "
        "Quick Favorites."),
}
_PICK_MASK = ("Pick mask", "Blender picks this kind of component in the object's own edit mode (Tab), not through a "
              "pick mask: the mask only switches mesh vertex / edge / face picking.")
MARKING.update({f"doSelectComponentMM/{p}": _PICK_MASK for p in (
    "Points/All Points", "Points/CVs", "Points/Lattice Points", "Points/Subdiv Mesh Points", "Points/Particles",
    "Parm Points/All Parm Points", "Parm Points/Edit Points", "Parm Points/Curve Points",
    "Parm Points/Subdiv Mesh UVs", "Parm Points/Surface Points", "Lines/Trim Edges", "Lines/All Lines",
    "Lines/Springs", "Lines/Isoparms", "Hulls", "Pivots/Scale Pivots", "Pivots/Joint Pivots", "Pivots/All Pivots",
    "Pivots/Rotate Pivots", "Handles", "Misc./Local Rotation Axes", "Misc./Image Planes", "Misc./All Misc")})
