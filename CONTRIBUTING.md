# Contributing

Thank you for being here. Maya Workflow Kit gets better every time someone who knows Maya tries it and says what
they noticed, so any kind of help is welcome, in whatever shape suits you:

- a bug report, long or short
- a single line like "this feels different from Maya" — honestly the most valuable thing a Maya user can give me
- a screenshot or a short screen recording
- an idea, a wish, a question
- a pull request, written in your own style

You don't need to run the tests, follow a format or match the code style. Open an
[issue](https://github.com/5hyuns/maya-workflow-kit-for-blender/issues/new), start a
[discussion](https://github.com/5hyuns/maya-workflow-kit-for-blender/discussions) or send a pull request, and I'll
take care of fitting it in with the rest.

If something in Blender behaves differently from how your hands expect Maya to behave, please say so, even if you
aren't sure it's a bug. Those notes are exactly what this project is built from.

## One thing to keep in mind

Describe Maya the way a user sees it: what is on the screen and what happens when you do something. Please don't
include Autodesk's files, scripts, icons or text, or anything taken from inside Maya's program files. The kit
re-creates Maya's behaviour in its own code, and keeping it that way protects both you and the project.

## If you'd like to dig in (optional)

- Building and running the tests: see [Development](README.md#development) in the README. In short,
  `python tests/run.py` builds the extension and runs the headless tests in a sandbox, without touching your own
  Blender settings (set `BLENDER` to your Blender executable if it isn't in the default Windows location). A few
  tests that need maintainer-only data or tools are skipped.
- Looking for a place to start:
  [good first issue](https://github.com/5hyuns/maya-workflow-kit-for-blender/labels/good%20first%20issue) and
  [help wanted](https://github.com/5hyuns/maya-workflow-kit-for-blender/labels/help%20wanted).
- Just want to talk it through first:
  [Discussions](https://github.com/5hyuns/maya-workflow-kit-for-blender/discussions).

Everyone who contributes or tests is thanked by name in the release notes (unless you'd rather not be).
