# SPDX-License-Identifier: GPL-3.0-or-later
"""Step 140 Maya option windows: modeling, parenting and key commands (issues #33, #35).

Same spec as operators/option_windows.py (``F`` fields, ``Window`` = one ``allset.opt_<key>`` operator); labels and
factory defaults read from Maya 2022 (research/maya/re/option_boxes_140.md). option_windows.py appends ``WINDOWS``
to its own list, so this module only imports ``F`` / ``Window`` / helpers from it.
"""

from .option_windows import F, Window  # noqa: F401  (option_windows imports this module at its end)

WINDOWS = []
