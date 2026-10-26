# Joint selection workflow

Restart Blender after updating this installed extension, or disable and re-enable the extension. Maya mode must be enabled.

- Allset's POSE JOINTS / EDIT JOINTS dropdown at the start of the viewport header pulses softly in teal while the active armature is selected, including in the Maya layout. The pulse stops on deselection.
- Click a joint to select it and use W/E/R directly. Pose mode is entered automatically.
- Shift-click toggles a joint, Ctrl-click subtracts it, and Ctrl+Shift-click adds it.
- Click another rig, mesh, or curve to leave the current rig's selection context automatically.
- Click empty space to clear selection and release Pose mode.
- Alt+D clears joint and object selection, clears the active object, and leaves Pose/Edit mode.
- F8 switches between rest-skeleton editing and joint selection. Returning from skeleton editing selects joints in Pose mode.
- Object rows in Allset's Outliner can leave armature Edit mode directly.
- Q/W/E/R finish the Joint Tool and activate the corresponding selection/transform tool. A selected joint can be used to branch a new chain.

These changes follow Maya's [selection modifiers and F8 behavior](https://help.autodesk.com/cloudhelp/2024/ENU/Maya-Basics/files/GUID-5C5F2B9B-BE16-4C49-B72B-70EA7CB4C688.htm) and [Select None shortcut](https://help.autodesk.com/cloudhelp/2022/ENU/Maya-Basics/files/GUID-D1BBC051-0EE7-4A91-B4FF-2A369764EC8B.htm).

Blender still represents joints as bones inside armatures. Rest editing, connected-bone translation, mixed object/bone transforms, box selection across different rigs, and custom bone-shape picking retain Blender limitations. Existing parenting, connectivity, constraints, and animation data are not converted. This is closer Maya interaction, not complete Maya rigging equivalence.

Verification uses Blender 5.2.3 LTS. Run `tests/integration/blender_joint_workflow.py` in a background factory session for mode/selection/modifier/keymap checks. Run `tests/integration/blender_joint_viewport.py` in a separate factory GUI session for actual viewport joint/mesh/background picking with selection priority enabled and disabled; that test exits its Blender process after completion.

## Leaving Paint Skin Weights

Q returns to Select; W/E/R return to Move/Rotate/Scale. The same toolbox buttons, including Lasso and Paint Select, leave Weight Paint before activating the selected tool. The painted mesh remains selected, the helper skeleton is released from Pose mode, and vertex weights are preserved. Re-enter through Skin > Paint Skin Weights; a previously remembered transform tool is replaced by a brush.

These exits use Maya's [global tool shortcuts](https://help.autodesk.com/cloudhelp/2025/ENU/Maya-KeyboardShortcuts/files/GUID-8370FB55-6BE6-4571-872B-F8291A187EC0.htm). Blender integration checks in `tests/integration/blender_weight_paint_exit.py` cover tool switching, re-entry, mesh selection, skeleton release, and unchanged weights. `tests/integration/blender_weight_paint_keys.py` checks real Q/W/E/R key events in an isolated factory window.

## Channel Box scrolling

Use the mouse wheel over Channel Box labels, value fields, or expanded input attributes to scroll the channels directly. Each wheel step advances one row, and trackpad panning supports smaller accumulated movements. The Layer Editor stays fixed while scrolling the Channel Box. The triangle buttons remain available. Scroll positions clamp at the first and last rows; scrolling does not edit channel values.
