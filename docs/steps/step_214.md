# Step 214 — Render parity 2 (Issue #120)

Source: `docs/steps/step_210_remaining.md` §3 F2 / §8 #1 (carried over five audits): the kit lambert1 rendered 1.25 x
brighter than Maya (Principled has no diffuse 0.8 input, step 152), Create > Lights > Ambient / Volume Light were
greyed, and Blender's own F12 render had no Maya default light. Maya spec: `research/maya/re/render_parity_214.md`
(mayapy, Maya Software, colour management off; scripts and raw JSON in `tmp/m214/`), earlier
`research/maya/re/render_defaults_137.md`, `research/maya/re/default_light_152.md`.

## 계획 (delegated)

- Lanes (two foreground agents at a time, Blender ≤ 2): (1) Maya measurement (mayapy only) ∥ (2) diffuse node; then
  (3) Ambient / Volume Light ∥ (4) F12. Sequential only: (3) needed (1)'s formulas.
- Diffuse: a "Maya Diffuse" Mix node in front of Principled Base Color (Base Color = diffuse x colour). Rejected: a Mix
  Shader after the BSDF — it also scales specular / emission / alpha and breaks Blender's
  `PrincipledBSDFWrapper`, which needs Principled linked straight to the output
  (`$S\modules\bpy_extras\node_shader_utils.py:192-229`), so FBX / OBJ / glTF exports would lose the material.
- Ambient Light = World colour (flat part) + a positional light (shaded part); Volume Light = a point light at the
  centre with the volume's falloff. F12 = a kit operator in front of Blender's render keys (render handlers are off the
  main thread, measured).

## 한 것

- **Maya measurement** (`research/maya/re/render_parity_214.md`): Maya Software dithers 8-bit output, so a patch mean is
  read as (mean + 0.5) / 255, accurate to 0.02 / 255. lambert renders color x diffuse x I x max(0, n·L), and a texture
  on Color is multiplied by Diffuse too (checker / ramp / file). ambientLight: v = I x colour x max(0, (1 − s) + s cos θ),
  θ toward the light's **position**, no falloff, **not** multiplied by diffuse, no specular, unshadowed at factory
  settings. volumeLight (sphere): v = I x colour x diffuse x (1 − r/R) x max(0, n·L to the centre), 0 outside; R = the
  scale; the falloff scales with the volume. A volume light also turns the default light off.
- **Diffuse** (`operators/material.py`): LAMBERT / BLINN / PHONG / PHONG_E / ANISOTROPIC / RAMP and lambert1 get the
  "Maya Diffuse" node (Mix RGBA, factor = diffuse 0.8, A black, B = the Maya colour / ramp / texture). Helpers
  `diffuse_node`, `color_socket` (= Maya Color), `maya_input`, `ensure_diffuse`, `Material.allset_diffuse` (AE Diffuse
  row, before it drew nothing), `diffuse_bypass()` around kit File > Export (texture linked straight to Base Color for
  the writers, restored afterwards). The Principled Base Color default is kept equal to the Maya colour, so readers that
  skip links see it. The AE map button, checker materials, Modify bounding-box materials and the viewport display colour
  go through `color_socket`.
- **Ambient / Volume Light** (`operators/maya_lights.py`, `lights.KIND_PROP`): Create > Lights, the Rendering shelf,
  Hypershade Create > Lights and the Light Editor create `ambientLight1` / `ambientLightShape1`, `volumeLight1` /
  `volumeLightShape1`. Ambient = a point light at the object (part s x I, No Decay, specular 0, no shadow) + the flat
  part (1 − s) x I x colour added to the World by kit nodes "Maya Ambient" (Background x (1 − Is Camera Ray), so the
  camera background stays as it was) — both divided by 0.8 because Maya's ambient light ignores diffuse; several
  ambient lights add up; the nodes go when the last ambient light is deleted / hidden and on unregister. Volume = a point
  light at the centre, R = max world scale x `maya_unit()`; Cycles exact through light nodes (Light Falloff Constant x
  max(0, 1 − Ray Length / R)); EEVEE inverse square with `cutoff_distance` = R, matched to Maya at R/2.
  `Light.allset_ambient_shade`, Maya intensity in an ID property (keyable, re-applied on frame change). AE sections
  "Ambient Light Attributes" / "Volume Light Attributes" (Light Shape, Color Range, Penumbra, Emit Ambient = greyed
  rows with notes). Create menu working 310 → 312, Hypershade 115 → 117, unique menu paths 804 → 806.
- **F12** (`operators/default_light.ALLSET_OT_render_blender`, `keymap/maya_patches.patch_blender_render`):
  measured [O] in Blender 4.5.4 GUI (`tmp/f214m/m1_threads.py`): render_init / render_pre / render_post /
  render_complete of an INVOKE render all run on a non-main thread, so no handler can add the light safely. A kit
  operator adds `defaultLight` (when the scene needs it), starts `render.render` INVOKE (Render window as usual) and
  `default_light.after_render()` removes it when the job ends (at once when cancelled). Maya mode: Screen F12 = Render
  Image, Ctrl+F12 = Render Animation, IC's Ctrl+Alt+Enter render wrapped too. Maya's F12 is a UV selection mask key
  (`hotkeySetup.mel:256`, kit `allset.uv_component` in Object Mode / Mesh, step 107), so over the 3D View F12 keeps that
  meaning; the UV Editor gets the F12 UV key too so it doesn't render there (delegated).

## 검증

- Brightness, default cube under the default light, 0–255 (`tests/test_step152_render.py`, Maya 76.84 / 65.12 / 10.0):

  | engine / world | top | front | side | ΔE00 max |
  |---|---|---|---|---|
  | EEVEE, no world | 77.20 | 65.68 | 10.43 | 0.19 |
  | Cycles, no world | 77.34 | 65.68 | 10.43 | 0.19 |
  | EEVEE, template world | 82.43 | 70.85 | 15.60 | 1.93 |
  | Cycles, template world | 82.53 | 70.87 | 15.62 | 1.97 |

  Before: 96.5 / 82.1 / 13.0 (1.25 x).
- Ambient light, lambert1, light 10 units away (`tests/test_step214_lights.py`), values 0..1:

  | s / θ | Maya | Cycles | EEVEE |
  |---|---|---|---|
  | 0 / any | 0.500 | 0.500 | 0.493 |
  | 0.45 / 0 | 0.500 | 0.500 | 0.496 |
  | 0.45 / 90 | 0.275 | 0.275 | 0.273 |
  | 0.45 / 180 | 0.050 | 0.275 | 0.272 |
  | 1 / 0 | 0.500 | 0.500 | 0.4995 |
  | 1 / 90, 180 | 0 | 0 | 0.004 / 0 |

  The stand-in's only error: surfaces turned away (θ > 90°) keep the flat part — min(s, 1 − s) x I x colour at most
  (0.225 at s 0.45, θ 180°), because Maya clamps the whole sum.
- Volume light, R 2 units, plane facing the centre:

  | r/R | Maya | Cycles | EEVEE |
  |---|---|---|---|
  | 0.3 | 0.278 | 0.278 | 0.611 |
  | 0.5 | 0.115 | 0.115 | 0.112 |
  | 0.7 | 0.050 | 0.050 | 0.028 |
  | 0.9 | 0.015 | 0.015 | 0.0035 |
  | 1.2 | 0 | 0 | 0 |

  Cycles within 0.0005; EEVEE's inverse square (with its cutoff fade (1 − (d/R)⁴)², measured) is matched at R/2,
  mean error over the volume 0.084 x I x colour x diffuse.
- F12: headless Cycles centre 0.42 lit vs 0.0002 with Enable Default Light off; GUI `gui_step214_f12` 7 / 7 — F12 over
  the Outliner opens the Render window, the cube is lit like Maya (top brightest), `defaultLight` was in the render and
  is gone afterwards (shot `tmp/f214m/shots/gui_step214_f12_render.png`, checked by eye).
- Tests: `test_step214_diffuse` 9, `test_step214_lights` 8, `test_step214_f12` 8 — all pass; lane runs of related
  files 357 + 207 + 106 + 55 pass. Full headless **2086 / 2086** (4.5.4). GUI related + smoke (`-k step214,step137_defaults,step137_render,step29_materials,step67_render,step148_cb,step158_cb,step105_windows,step60_switch,step49_layout,step129_switch`) **90 / 92**: the 2 failures are `gui_step29_materials` (Favorite > Blinn names the material `blinn6`, then Escape check) and fail the same at 2896386 (step 213, before this step) — pre-existing, not touched here.

## 남은 것

- Template world grey (0.051) still adds ~5.6 / 255 ambient Maya doesn't have (and a grey render background where Maya's
  is black): changing it means regenerating `startup.blend` (`tools/make_startup.py`, GUI) — next render step.
- Blender's own top bar "Blender Render" submenu (`TOPBAR_MT_render`) still calls `render.render` (no default light);
  Maya's Render menu items are the kit's and have it.
- Ambient: Cycles shadows the World part (ambient occlusion) where Maya's factory ambient is unshadowed; θ > 90° error
  above. Volume: shapes other than Sphere, Inward / Down Axis, Emit Ambient, the Color Range / Penumbra ramps, the
  radius isn't drawn in the viewport. A World shared by several scenes / light data shared by several objects syncs
  only the handler's scene.
- Blender's own File > Export menu isn't wrapped by `diffuse_bypass` (a texture behind the diffuse node isn't
  exported; the flat colour is). Old files keep diffuse 1 (no migration).
- Pre-existing GUI failure `gui_step29_materials` (Favorite > Blinn gives `blinn6`: 5 extra blinn materials exist by then) — to look at in a later step.
- Render Setup (Status Line / Windows) stays greyed. 5.x not run for this step (`compat.WORLD_ALWAYS_NODES` assumed).
