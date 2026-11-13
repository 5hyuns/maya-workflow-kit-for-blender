"""The checks of gui_selection_wire_instanced.py on the Vulkan GPU backend: the instanced selection wire draws the same
pixels as drawing each object by itself there too."""

import os
import runpy
import sys

import gpu

GUI_ARGS = "--gpu-backend vulkan"
GUI_TIMEOUT = 600

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import check  # noqa: E402

check(f"Blender runs on the Vulkan backend ({gpu.platform.backend_type_get()})",
      gpu.platform.backend_type_get() == 'VULKAN')
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_selection_wire_instanced.py"),
               run_name="__main__")
