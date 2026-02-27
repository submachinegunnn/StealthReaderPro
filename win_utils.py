import platform

SYSTEM = platform.system()

if SYSTEM == "Windows":
    import ctypes
    import ctypes.wintypes as wintypes
    WDA_EXCLUDEFROMCAPTURE = 0x00000011
else:
    ctypes = None
    wintypes = None
    WDA_EXCLUDEFROMCAPTURE = None

def protect_window(root):
    """Returns True if protection applied, False otherwise."""
    if SYSTEM != "Windows":
        return False

    try:
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
        success = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        return bool(success)
    except Exception as e:
        print(f"Stealth Error: {e}")
        return False