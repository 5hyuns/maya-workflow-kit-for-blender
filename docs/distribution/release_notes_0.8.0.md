# Release notes 0.8.0 (GitHub release)

Text for the GitHub release of v0.8.0. Full list: the 0.8.0 section of `CHANGELOG.md`.

---

**0.8.0 — Maya 2026 menus, your own marking menus, Channel Box dragging, Quad Draw and the fixes from your reports** (Blender 5.2 LTS)

Install it over 0.7.0 (or 0.6.x / 0.5.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
For Blender 4.5 LTS keep using 0.6.2.

Added
- Marking Menu Editor (Windows > Settings/Preferences): change the kit's marking menus in Maya's grid, and make your
  own marking menus that open with a hotkey the Maya way (#239).
- Channel Box value dragging: left-drag a value sideways, Ctrl / Shift / Alt for whole steps or finer moves; one drag
  is one undo step (#224). INPUTS attributes (polyCube1 Subdivisions, Bevel Width ...) can be selected, dragged with
  the middle mouse in the viewport and keyed like channels (#230, #222).
- Japanese and Simplified Chinese for the kit's own labels and tooltips, following Blender's language setting (#197).
- Render Sequence with All Render-Enabled Cameras and Skip existing frames (#252); project AutoSave (#254).
- Skin Tools weight layers (#127), Hypergraph: Hierarchy (#232), Sweep Mesh that stays editable (#238), Interactive
  Creation for polygon primitives (#225), Hotkey Editor > Import of a Maya hotkey set (#219), flipped UVs coloured in
  the UV Editor (#246), Time Slider middle-mouse drag (#255).
- 75 more FX and Rendering menu items run Blender's own systems (#123).
- RMB marking menu over a lattice (#227); Shift+W / E / R key Translate / Rotate / Scale from any editor (#212).
- Alt+B adds Maya's blue gradient; a ViewCube with hover controls; selected wires no longer show their back edges
  (#216, #224, #243).

Changed
- Marking menus, the hotbox, Hypershade > Create, the Graph Editor toolbar and the Animation shelf follow Maya 2026.
- Reset Pivot Position puts an object's pivot on its centre, like Maya; Zero Position on Reset in the pivot-edit menu
  keeps the old behaviour.
- Double-click a vertex or face selects its whole shell; Shift+double-click a neighbouring face selects the face
  loop (#222).
- Joint Tool: drag after a click to place the joint, with joints, bones and a ghost of the next joint drawn while the
  tool runs (#230).
- Quad Draw: Maya's options marking menu, Tab + middle-drag strip width, and a large connections / symmetry / preview
  update (#89, #231).
- Display > Polygons is Maya's submenu (#240).
- A Space tap maximizes any panel of the four view (#214); Ctrl first, then drag a Move handle snaps (#215); Graph
  Editor Spline / Clamped / Plateau / Flat tangents have Maya's slopes (#210); joints draw like Maya's.

Fixed
- Undo while the Joint Tool runs takes back one joint (#256); Bind Skin keeps a posed mesh in place, and grouping a
  skeleton keeps the skin following it (#230).
- Hypershade Delete Unused Nodes no longer crashes Blender (#251).
- Other add-ons' keys no longer run before the kit's Maya keys (#218, #250); UV Shell picks show in the UV Editor
  (#245); the Tool Box column fits on Retina displays (#248); translated menu bar labels fit (#249).
- Alt+LMB tumble with Emulate 3 Button Mouse (#242), Panels > Tear Off (#255), Graph Editor Shift+drag and middle
  drag (#211), Target Weld through the mesh (#233), F framing kept ahead of other add-ons' F menus (#237), hiding a
  group from the Outliner (#223), View > Select Camera (#229).
- More Bevel cases like Maya (#213), NURBS surfaces (Extrude Tube, Boundary / Square, Birail 1) and Loft > Polygons
  UVs like Maya, UV > Normalize on picked UVs.

The known differences listed in `CHANGELOG.md` still apply.

## Thank you

@TMouraille made the Marking Menu Editor (#239), the Display > Polygons submenu (#240), left-aligned torn-off menus
(#241) and group pivot editing (#253). @youngmin2k improved Quad Draw (#231) and fixed F framing next to other add-ons
(#237). Tom Pilott sent Channel Box value dragging and the viewport extras (#224). @A2wkiller made the Outliner hide
keys (#235), the lattice marking menu (#236) and the Polygon Primitives notice (#234).

Thanks for the reports and ideas: @DAI3rd (#249, #251, #252, #254), @natalietrn (#243, #244, #245, #246),
@zzador (#256, #257), @coolmuzzy (#255), @gsvetlin-beep (#238), @Troyzerk (#233), @LASooner (#232),
@bhowiebkr (#230), @Fizkefaaz (#212, #214, #229), @ankushinvedus-cell (#227), @Weeliano (#217, #222),
@Kevorama (#223), @XeonG (#215, #216), @TheAtomicSoul (#218), @sipinglinfeng-prog (#219), @RIPTIDE-z (#197), @MarfyValarios (#250),
@videopilot (#248) and @samansabz (#242). Please keep telling us what breaks or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc. This extension is not affiliated with or
endorsed by Autodesk, Inc.
