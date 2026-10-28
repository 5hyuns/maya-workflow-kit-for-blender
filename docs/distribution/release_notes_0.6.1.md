# Release notes 0.6.1 (GitHub release)

Text for the GitHub release of v0.6.1. Full list: `CHANGELOG.md` 「0.6.1」. Before publishing, run the maintainer
checklist in `docs/release_checklist.md`.

---

**0.6.1 — Time Slider numbers, and a guide for contributors** (Blender 4.5 LTS – 5.2)

A small update to 0.6.0. Install it over 0.6.0 or 0.5.0 as usual; shelves, hotkeys and scenes are kept.

Fixed
- Time Slider frame numbers no longer grow when the timeline is made taller; they follow the UI scale instead
  (#179, fixed by @LSKianhao in #188).

Added
- CONTRIBUTING.md: how to help, from a one-line "this feels different from Maya" note to a pull request. A fresh
  clone can run the test suite: tests that need Maya reference data it doesn't have are skipped.

Everything else in 0.6.0 (rigging that behaves like Maya 2026, Four View panels, UV Shell selection and the fixes for
the reports after 0.5.0) is described in the 0.6.0 release and in `CHANGELOG.md`. The known differences listed there
still apply.

## Thank you

@LSKianhao reported the Time Slider number size (#179) and sent the fix (#188). Thanks also to everyone
whose reports and suggestions shaped 0.6: @Egminator (#170), @todd-mrcool
(#171), @Rickamykazy1 (#173), @esonstyle (#174), @Kevorama (#175), @CommonDirt (#176), @ryankentpaule (#177),
@GimpTOOTS (#178), @Weeliano (#183), @hacker9002 and @cnzim (#156). Please keep telling us what breaks or feels off
in real work.

Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc. This extension is not affiliated with or
endorsed by Autodesk, Inc.
