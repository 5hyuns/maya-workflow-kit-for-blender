# Release notes 0.19.0 (GitHub release)

Text for the GitHub release of v0.19.0. Full list: the 0.19.0 section of `CHANGELOG.md`.

---

**0.19.0 — Maya's IK/FK switching, the rest of the Time Slider Bookmarks, new Graph Editor and Dope Sheet tools, a Shelf Editor drag from contributor @AlexBarbulescu, and smoother window drags in Maya mode** (Blender 5.2 LTS and 5.3)

Hello everyone, and thank you for the reports and the help. This release is mostly about animation and rigging:
Maya's IK/FK switching, the rest of the Time Slider Bookmarks and new Graph Editor and Dope Sheet tools. It also
makes window drags smoother in Maya mode (#334) and joint drawing lighter while playing (#344), and finishes #320.
@AlexBarbulescu sent the Shelf Editor drag in #382; we brought it into the kit with him credited as co-author, as a
preference that is off by default because Maya's Shelf Editor uses Move Up / Move Down. Thank you, Alex!

Install it over 0.18.0 (or 0.8.0 – 0.17.0) as usual; shelves, hotkeys, scenes and the kit's settings are kept.
(Removing the kit before installing deletes them: use Export Settings first.)
Supported: Blender 5.2 LTS and 5.3. Other versions are not tested: the extension still installs on Blender 5.0 and
5.1, but they may have problems. For Blender 4.5 LTS keep using 0.6.2. Versions after 5.3 are not offered the
extension until they are tested.

## New

- **IK/FK switching:** Skeleton > Enable IK/FK Control and Enable IK Handle Snap work like Maya. With Snap on,
  turning a joint of an IK chain takes the IK handle along to the end joint; with IK/FK control off, a keyed handle
  keeps its joints from turning. IK chain joints hold the IK solution in their rotate channels, so the Channel Box
  shows the solved rotation and Ik Blend 1 → 0 keeps the IK pose. A turned joint stays turned until the chain is
  solved again (the handle moves, its Ik Blend, Pole Vector, Twist or Solver Enable changes, or the time changes
  while the handle has keys), and with Snap on an RP chain's Pole Vector turns with the start joint.
- **Connect to IK/FK** (Key > IK/FK Keys): the selected objects get an Ik Blend that follows the IK handle, and
  selecting such an object works for Set IK/FK Key, Enable IK Solver and Move IK to FK.
- **Time Slider Bookmarks:** Edit, Show Bookmarks and the Bookmark Manager work like Maya. Each bookmark has its own
  colour; the mouse over a bookmark shows its name and range and draws its end lines down through the Time Slider;
  a right-click opens the bookmark menu for the bookmark under the mouse; Ctrl + drag moves a bookmark or one of its
  ends; Ctrl + double-click highlights its range. Next / Previous Bookmark wrap round like Maya.
- **Graph Editor:** the Region Keys Tool (drag a side or corner of its box to scale the keys inside, drag inside to
  move them), Pre-Select Highlight (the curve under the mouse drawn brighter; it stays when the mouse leaves the
  curve view and goes when a drag starts) and Prefer Selected Curves, like Maya. The two Select options are off by
  default, like Maya.
- **Dope Sheet:** Channels > Offset Keys moves the selected keys by a number of frames, with its option box.
- **Shelf Editor drag (#382, from @AlexBarbulescu):** with the preference Shelf Editor Drag on, each Shelf Contents
  row has a grip to move the button to a new place.

## Fixed and changed from your reports

- **Joint size (#320):** joints keep their Radius size when the armature object is scaled, so a rig scaled up to
  fit a scene's units no longer draws giant joints.
- **Window drags (#334):** dragging or resizing a window in Maya mode is smoother: the kit's panels draw what they
  drew before instead of working it out again at every step, and with windows on displays of different scaling
  each window is fitted at its own scaling.
- **Playback (#344):** joints with controls draw faster while playing.
- RP handles with Twist and IK chains of three or more bones write the solved rotation into the joints right after
  the handle moves.
- Moving UVs in the UV Editor while the 3D View shows the UV selection can no longer crash Blender.

## Known differences

- The bookmark name box under the mouse keeps the kit's look; if the mouse leaves the Blender window straight from a
  bookmark, its name stays until the mouse comes back into the window.
- The Graph Editor's Pre-Select Highlight lights curves; keys and tangent handles are not highlighted yet.
- The known differences listed in `CHANGELOG.md` still apply.

## Thank you

Thanks to @AlEuf01 (#320), @GIBBETGAMES (#334) and @pixelkeyblade18 (#344) for reports that showed what to fix, and
again to @AlexBarbulescu for #382. Please keep telling us what breaks or feels off in real work.

Maya Workflow Kit is a free, personal open-source project: no paid version, no donations requested, and no commercial
goal behind it.
