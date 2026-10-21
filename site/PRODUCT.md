# PRODUCT — Maya Workflow Kit (product site)

> Written for the impeccable workflow (step 127). The user delegated every decision, so this was inferred from the
> repository, not from an interview; assumptions are marked **[assumed]**. Sources: `docs/distribution/listing.md`
> (feature truth), `docs/distribution/naming.md` + `docs/user_decisions.md` decision 12 (name, trademark rules),
> `docs/distribution/marketing/style.md` + `copy.md` (visual system, copy).

## What it is

A free, open-source (GPL-3.0-or-later) Blender extension, Blender 4.5.x – 5.2.x. It makes Blender work the way Maya
2022 works for someone who learned 3D in Maya: hotbox and marking menus, Channel Box and Attribute Editor, menu sets,
shelves and option windows, Maya navigation and selection, and Maya scene concepts (Freeze, History, Center Pivot,
groups, centimetres, `pCube1`). Tagline: **The whole Maya workflow in Blender, in one install.**

Unique mechanism: it is not a keymap. Other tools cover one piece each (a pivot tool, a keymap, a shelf);
this rebuilds the whole set together, one Maya workflow at a time, on top of Blender's own tools — and it changes
nothing until the user chooses Maya, with one click (or Ctrl+Alt+Shift+M) back to plain Blender.

## Audience

- Maya artists (modelers, riggers, animators) who must or want to use Blender: freelancers, students whose school
  switched, studios trialling Blender. **[assumed]** They know Maya's UI by muscle memory and judge in seconds whether a
  "Maya mode" is real or a keymap skin.
- They arrive from a README link, a Reddit / X post or the store listing, on desktop mostly, phone sometimes.

## Job of the site (Persuade)

Within one viewport: what this is (Maya's workflow inside Blender), that it is real (the actual UI, moving), and what to
do (install). Then proof per workflow, how install / revert works (nothing changes until you choose), the
recommended setup (a dark grey theme of the user's choice and the Blender preferences the kit no longer sets — step
130, store review), honest limits, FAQ, credits and the trademark notice.

Since step 130 the kit ships no theme and writes no preferences: never claim Maya colours, a Maya theme, a layout
template or restored settings.

## Truth rules

- Facts only; no comparisons with other products, no superlatives, no invented numbers. Numbers only when current
  (e.g. supported versions), never test counts.
- Name: "Maya Workflow Kit"; the first sentence after the name gives the "for Maya users, in Blender" context;
  "Maya" never styled apart from the rest of the name. Repository: maya-workflow-kit-for-blender.
- Footer carries the Autodesk non-affiliation notice; media credits (Blender Studio rigs and the DOGWALK splash scene,
  CC BY 4.0; Cube Diorama and Poly Haven HDRI, CC0) appear with the media.
- Not yet on extensions.blender.org: the store link is a placeholder; install = the zip from GitHub Releases.

## Brand commitments (from step 124 / 125)

Maya greys (#1e1e1e – #5c5c5c, Maya's factory viewport), Maya logo teal #00bcbb as the one accent, Autodesk Hello
Yellow #ffff00 only for action moments, black ink on accents; Inter; the lockup "Maya Workflow Kit" + "for Maya users,
in Blender" at 0.66 ×.
