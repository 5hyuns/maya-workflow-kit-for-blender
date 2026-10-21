# Step 135 fix lane (fix135b): GUI tests after the dock widening and collapsed INPUTS

Root causes and fixes, one per failing GUI test. Decisions made here without asking are marked delegated.

- **gui_step129_prims** — kit bug: `channel_box.cb_share` sized the adaptive Channel Box part without
  `pane_room`'s 0.3-unit margin, and `int(11.2 / 0.8)` = 13, so a primitive's collapsed Channel Box (CB_LINES = 14)
  lost its last line (the INPUTS node name `polyCylinder1`) to the scroll window. Fixed both terms; the test now
  scrolls the expanded node into the pane with `sim.scroll_channel_box()` (sets the pane's first line, clamped by the
  draw; the wheel itself stays tested in gui_step135_dock — delegated).
