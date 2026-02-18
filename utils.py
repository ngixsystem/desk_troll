import win32gui
import win32con
import mss
from PIL import Image
import time
import ctypes
from ctypes import wintypes

# Keyboard hook for blocking Windows key
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
VK_LWIN = 0x5B
VK_RWIN = 0x5C

hook_handle = None
hook_proc_ref = None  # Keep reference to prevent garbage collection

def low_level_keyboard_handler(nCode, wParam, lParam):
    """Low-level keyboard hook to block Windows key."""
    if nCode >= 0 and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
        vk_code = ctypes.cast(lParam, ctypes.POINTER(ctypes.c_ulong)).contents.value
        if vk_code in (VK_LWIN, VK_RWIN):
            print(f"Blocked Windows key: {vk_code}")
            return 1  # Block the key
    return ctypes.windll.user32.CallNextHookEx(hook_handle, nCode, wParam, lParam)

def block_windows_key():
    """Install keyboard hook to block Windows key."""
    global hook_handle, hook_proc_ref
    
    # Define callback type
    HOOKPROC = ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_void_p)
    )
    
    # Create and store callback reference
    hook_proc_ref = HOOKPROC(low_level_keyboard_handler)
    
    # Install hook
    hook_handle = ctypes.windll.user32.SetWindowsHookExA(
        WH_KEYBOARD_LL,
        hook_proc_ref,
        ctypes.windll.kernel32.GetModuleHandleW(None),
        0
    )
    
    if hook_handle:
        print(f"Windows key hook installed: {hook_handle}")
    else:
        print("Failed to install Windows key hook")
    
    return hook_handle

def unblock_windows_key():
    """Remove keyboard hook to unblock Windows key."""
    global hook_handle
    if hook_handle:
        ctypes.windll.user32.UnhookWindowsHookEx(hook_handle)
        hook_handle = None

def get_desktop_icon_positions():
    """Get positions of all desktop icons by selecting them with Ctrl+A."""
    import pyperclip
    import time
    
    icon_positions = []
    
    try:
        # Find desktop window
        progman = win32gui.FindWindow("Progman", None)
        def_view = win32gui.FindWindowEx(progman, 0, "SHELLDLL_DefView", None)
        
        if def_view == 0:
            # Try WorkerW windows
            def enum_windows_callback(hwnd, _):
                nonlocal def_view
                if win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None):
                    def_view = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
                    return False
                return True
            win32gui.EnumWindows(enum_windows_callback, None)
        
        if def_view:
            list_view = win32gui.FindWindowEx(def_view, 0, "SysListView32", None)
            
            if list_view:
                # Focus the desktop
                win32gui.SetForegroundWindow(list_view)
                time.sleep(0.2)
                
                # Simulate Ctrl+A to select all icons
                VK_CONTROL = 0x11
                VK_A = 0x41
                KEYEVENTF_KEYUP = 0x0002
                
                # Press Ctrl
                ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
                time.sleep(0.05)
                # Press A
                ctypes.windll.user32.keybd_event(VK_A, 0, 0, 0)
                time.sleep(0.05)
                # Release A
                ctypes.windll.user32.keybd_event(VK_A, 0, KEYEVENTF_KEYUP, 0)
                time.sleep(0.05)
                # Release Ctrl
                ctypes.windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
                
                time.sleep(0.3)  # Wait for selection
                
                # Get selected item count
                LVM_GETSELECTEDCOUNT = 0x1032
                selected_count = ctypes.windll.user32.SendMessageW(list_view, LVM_GETSELECTEDCOUNT, 0, 0)
                
                print(f"Selected {selected_count} icons")
                
                # Get positions using simpler method - grid layout
                # Desktop icons are typically arranged in a grid
                # Standard spacing: ~100px horizontally, ~100px vertically
                # Starting from top-left
                
                icon_spacing_x = 100
                icon_spacing_y = 100
                start_x = 20
                start_y = 20
                
                # Create grid of positions based on selected count
                icons_per_column = 10  # Typical desktop layout
                for i in range(selected_count):
                    col = i // icons_per_column
                    row = i % icons_per_column
                    x = start_x + col * icon_spacing_x
                    y = start_y + row * icon_spacing_y
                    icon_positions.append((x, y))
                
                # Deselect all icons programmatically
                LVM_SETITEMSTATE = 0x102B
                LVIS_SELECTED = 0x0002
                
                # Deselect all items (-1 means all items)
                class LVITEM(ctypes.Structure):
                    _fields_ = [
                        ("mask", ctypes.c_uint),
                        ("iItem", ctypes.c_int),
                        ("iSubItem", ctypes.c_int),
                        ("state", ctypes.c_uint),
                        ("stateMask", ctypes.c_uint),
                    ]
                
                lvi = LVITEM()
                lvi.stateMask = LVIS_SELECTED
                lvi.state = 0  # Clear selection
                
                ctypes.windll.user32.SendMessageW(list_view, LVM_SETITEMSTATE, -1, ctypes.byref(lvi))
                time.sleep(0.2)
    
    except Exception as e:
        print(f"Error getting icon positions: {e}")
        import traceback
        traceback.print_exc()
    
    return icon_positions

def toggle_desktop_icons(show=True):
    """Show or hide desktop icons."""
    try:
        # Find the desktop ListView (SysListView32) which contains the icons
        progman = win32gui.FindWindow("Progman", None)
        def_view = win32gui.FindWindowEx(progman, 0, "SHELLDLL_DefView", None)
        
        if def_view == 0:
            # Sometimes the desktop is under WorkerW
            worker_w = None
            def enum_windows_callback(hwnd, _):
                nonlocal worker_w
                if win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None):
                    worker_w = hwnd
                    return False
                return True
            
            win32gui.EnumWindows(enum_windows_callback, None)
            if worker_w:
                def_view = win32gui.FindWindowEx(worker_w, 0, "SHELLDLL_DefView", None)
        
        if def_view:
            list_view = win32gui.FindWindowEx(def_view, 0, "SysListView32", None)
            if list_view:
                if show:
                    win32gui.ShowWindow(list_view, win32con.SW_SHOW)
                else:
                    win32gui.ShowWindow(list_view, win32con.SW_HIDE)
        
        time.sleep(0.3)
    except Exception as e:
        print(f"Error toggling desktop icons: {e}")

def minimize_all_windows():
    """Minimize all windows using Win+D keyboard shortcut."""
    try:
        # Simulate Win+D using SendInput
        VK_LWIN = 0x5B
        KEYEVENTF_KEYUP = 0x0002
        
        # Press Win
        ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0, 0)
        time.sleep(0.05)
        # Press D
        ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)
        time.sleep(0.05)
        # Release D
        ctypes.windll.user32.keybd_event(0x44, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)
        # Release Win
        ctypes.windll.user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
        
        time.sleep(0.5)
    except Exception as e:
        print(f"Error minimizing windows: {e}")

def capture_desktop() -> Image.Image:
    """Captures a screenshot of the entire desktop (all monitors)."""
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        sct_img = sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

def capture_dual_screenshots():
    """
    Captures two screenshots:
    1. Wallpaper only (icons hidden)
    2. Full desktop (icons visible)
    
    Returns: (wallpaper_image, desktop_image)
    """
    # Minimize all windows first
    minimize_all_windows()
    
    # Hide desktop icons
    toggle_desktop_icons(show=False)
    time.sleep(0.5)  # Wait for icons to hide
    
    # Capture wallpaper
    wallpaper_img = capture_desktop()
    
    # Show desktop icons back
    toggle_desktop_icons(show=True)
    time.sleep(0.5)  # Wait for icons to appear
    
    # Capture full desktop with icons
    desktop_img = capture_desktop()
    
    return wallpaper_img, desktop_img

def get_screen_geometry():
    """Get screen width and height."""
    import ctypes
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
