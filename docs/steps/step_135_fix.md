# Step 135 fix lane (fix135b): GUI tests after the dock widening and collapsed INPUTS

Root causes and fixes, one per failing GUI test. Decisions made here without asking are marked delegated.

- **gui_step129_prims** — kit bug: `channel_box.cb_share` sized the adaptive Channel Box part without
  `pane_room`'s 0.3-unit margin, and `int(11.2 / 0.8)` = 13, so a primitive's collapsed Channel Box (CB_LINES = 14)
  lost its last line (the INPUTS node name `polyCylinder1`) to the scroll window. Fixed both terms; the test now
  scrolls the expanded node into the pane with `sim.scroll_channel_box()` (sets the pane's first line, clamped by the
  draw; the wheel itself stays tested in gui_step135_dock — delegated).
- **gui_step65_extrude** — test: the Divisions field was clicked at a fixed measured y (`DIVISIONS_FIELD`, step 65),
  but with collapsed nodes and a scrolling Channel Box part the expanded polyExtrudeFace1 rows sit elsewhere. Now
  `scroll_channel_box()` + `find_button` on the `divisions_text` data path.
- **gui_step55_pose** — test: the constraint weight field was `field(12.6)` (a fixed row offset under Translate X);
  the expanded constraint node moves it and the part scrolls. Now looked up by data path (the `allset_cb.rows[i].text`
  of the CONSTRAINT row) after `scroll_channel_box()`.
- **gui_step124_persp_label** — test probe: it subtracted the window's desktop position (`win().y` = 60 here) from
  `area.y`, which is already in window coordinates like the screenshot, so it scanned 60 px below the view's bottom
  (it passed only while the OS put the window near the top of the desktop). The kit draws "persp" once; the probe now scans
  `area.y .. area.y + 70`.
- **gui_step134_selection** — test: in the narrower viewport pCube1 (lead, green) covers part of pCube3, so two of
  pCube3's sampled edge midpoints landed on pCube1's green silhouette. The kit colours were right. The probe now skips
  pCube3 points inside (or within 4 px of) the selected cubes' screen hulls and needs at least 4 uncovered edges
  (10 of 12 at 1.25) — delegated: kept the scene, filtered the samples.
- **gui_manual_sweep [M76-1] / [M76-3]** — test geometry: the template persp lens is fixed (step 81), so in the
  narrower viewport the 0.8 cm control circle is ~13 px across; its centre (the "off the curve" click) lay within
  `select_priority.RADIUS_PX` x UI scale (6.25 px) of the circle's drawn chords, so Maya priority rightly picked the
  curve and the later toggle checks cascaded. Not a kit bug. The M76 section now zooms in 2x (view distance restored
  at `m76_2_ik`; the first click moved one tick later because the view matrices update when the view draws) —
  delegated.
