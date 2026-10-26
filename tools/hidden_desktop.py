"""Keep test Blenders off the maintainer's screen (Windows).

GUI tests need a real Blender window (events, timers, drawing), so they cannot run with ``-b``.
Instead they run on a separate, invisible Windows desktop in the same session: windows, GPU
drawing and crash dialogs all live there, nothing appears on the monitors. Child processes
inherit the desktop, so wrapping the runner is enough.

    python tools/hidden_desktop.py <cmd ...>   # run any command there, exit with its code
    ensure_hidden()                           # at the top of a GUI runner: re-run itself there

``ALLSET_GUI_VISIBLE=1`` opts out (manual debugging). No-op on other platforms.
"""
import os
import subprocess
import sys

NAME = "allset_hidden_tests"


def _api():
    import ctypes
    import ctypes.wintypes as wt
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    u32 = ctypes.WinDLL("user32", use_last_error=True)
    u32.CreateDesktopW.restype = wt.HANDLE
    u32.CreateDesktopW.argtypes = [wt.LPCWSTR, wt.LPCWSTR, ctypes.c_void_p, wt.DWORD, wt.DWORD,
                                   ctypes.c_void_p]
    u32.GetThreadDesktop.restype = wt.HANDLE
    u32.GetUserObjectInformationW.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD,
                                              ctypes.POINTER(wt.DWORD)]
    return ctypes, wt, k32, u32


def current_desktop():
    if os.name != "nt":
        return ""
    ctypes, wt, k32, u32 = _api()
    h = u32.GetThreadDesktop(k32.GetCurrentThreadId())
    buf = ctypes.create_unicode_buffer(256)
    n = wt.DWORD()
    u32.GetUserObjectInformationW(h, 2, buf, ctypes.sizeof(buf), ctypes.byref(n))  # UOI_NAME
    return buf.value


def run(cmd):
    """Run ``cmd`` (list) on the hidden desktop, wait, return its exit code."""
    ctypes, wt, k32, u32 = _api()

    class SI(ctypes.Structure):
        _fields_ = [("cb", wt.DWORD), ("lpReserved", wt.LPWSTR), ("lpDesktop", wt.LPWSTR),
                    ("lpTitle", wt.LPWSTR), ("dwX", wt.DWORD), ("dwY", wt.DWORD),
                    ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD), ("dwXCountChars", wt.DWORD),
                    ("dwYCountChars", wt.DWORD), ("dwFillAttribute", wt.DWORD), ("dwFlags", wt.DWORD),
                    ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD), ("lpReserved2", ctypes.c_void_p),
                    ("hStdInput", wt.HANDLE), ("hStdOutput", wt.HANDLE), ("hStdError", wt.HANDLE)]

    class PI(ctypes.Structure):
        _fields_ = [("hProcess", wt.HANDLE), ("hThread", wt.HANDLE), ("dwProcessId", wt.DWORD),
                    ("dwThreadId", wt.DWORD)]

    if not u32.CreateDesktopW(NAME, None, None, 0, 0x10000000, None):  # GENERIC_ALL; opens if it exists
        raise OSError(f"CreateDesktop failed: {ctypes.get_last_error()}")
    si = SI()
    si.cb = ctypes.sizeof(SI)
    si.lpDesktop = NAME
    pi = PI()
    line = ctypes.create_unicode_buffer(subprocess.list2cmdline(cmd))
    if not k32.CreateProcessW(None, line, None, None, False, 0, None, None,
                              ctypes.byref(si), ctypes.byref(pi)):
        raise OSError(f"CreateProcess failed: {ctypes.get_last_error()}")
    try:
        k32.WaitForSingleObject(pi.hProcess, 0xFFFFFFFF)
    except KeyboardInterrupt:
        k32.TerminateProcess(pi.hProcess, 1)
        raise
    code = wt.DWORD()
    k32.GetExitCodeProcess(pi.hProcess, ctypes.byref(code))
    k32.CloseHandle(pi.hThread)
    k32.CloseHandle(pi.hProcess)
    return code.value


def ensure_hidden():
    """Re-run the calling script on the hidden desktop unless it is already there (or opted out)."""
    if os.name != "nt" or os.environ.get("ALLSET_GUI_VISIBLE") == "1":
        return
    if current_desktop() == NAME:
        return
    sys.stdout.flush()
    sys.exit(run([sys.executable, *sys.argv]))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(run(sys.argv[1:]))
