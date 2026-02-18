"""
Mouse Inverter + Click Hook.
- Инвертирует движение мыши (вверх↔вниз, влево↔вправо)
- Перехватывает ЛКМ/ПКМ и передаёт координаты в overlay
- Выход: нажать '=' и ввести пароль 12021
"""
import ctypes
import ctypes.wintypes
import sys
import threading

from PyQt6.QtWidgets import QApplication, QInputDialog, QLineEdit
from PyQt6.QtCore import pyqtSignal, QObject

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WH_MOUSE_LL       = 14
WM_MOUSEMOVE      = 0x0200
WM_LBUTTONDOWN    = 0x0201
WM_RBUTTONDOWN    = 0x0204
VK_OEM_PLUS       = 0xBB   # клавиша '=' (основная)
VK_OEM_MINUS      = 0xBD   # клавиша '-' (запасная)


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt",          POINT),
        ("mouseData",   ctypes.c_ulong),
        ("flags",       ctypes.c_ulong),
        ("time",        ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


HOOKPROC = ctypes.CFUNCTYPE(
    ctypes.c_long,
    ctypes.c_int,
    ctypes.wintypes.WPARAM,
    ctypes.POINTER(MSLLHOOKSTRUCT),
)


class Signals(QObject):
    request_password = pyqtSignal()
    mouse_clicked    = pyqtSignal(int, int)   # x, y клика


class MouseInverter:
    def __init__(self, signals: Signals):
        self._hook      = None
        self._hook_ref  = None
        self._last_x    = None
        self._last_y    = None
        self.active     = True
        self._signals   = signals
        self._thread_id = None

        self._sw = user32.GetSystemMetrics(0)
        self._sh = user32.GetSystemMetrics(1)
        self._eq_was_down = False

    def _hook_proc(self, nCode, wParam, lParam):
        if nCode >= 0:
            pt    = lParam.contents.pt
            cur_x = pt.x
            cur_y = pt.y

            # --- Перехват кликов ЛКМ / ПКМ ---
            if wParam in (WM_LBUTTONDOWN, WM_RBUTTONDOWN):
                print(f"[HOOK] Click at {cur_x}, {cur_y}")
                self._signals.mouse_clicked.emit(cur_x, cur_y)
                # НЕ блокируем клик — пропускаем дальше

            # --- Инверсия движения ---
            elif wParam == WM_MOUSEMOVE and self.active:
                if self._last_x is not None:
                    dx = cur_x - self._last_x
                    dy = cur_y - self._last_y
                    if dx != 0 or dy != 0:
                        new_x = max(0, min(self._sw - 1, cur_x - 2 * dx))
                        new_y = max(0, min(self._sh - 1, cur_y - 2 * dy))
                        self._last_x = new_x
                        self._last_y = new_y
                        user32.SetCursorPos(new_x, new_y)
                        return 1
                else:
                    self._last_x = cur_x
                    self._last_y = cur_y

            # --- Проверка клавиши '=' ---
            state = user32.GetAsyncKeyState(VK_OEM_PLUS)
            if not bool(state & 0x8000):
                state = user32.GetAsyncKeyState(0x3D)  # ASCII '='
            if bool(state & 0x8000) and not self._eq_was_down:
                self._eq_was_down = True
                print("[HOOK] '=' key detected, requesting password")
                self._signals.request_password.emit()
            elif not bool(user32.GetAsyncKeyState(VK_OEM_PLUS) & 0x8000) and \
                 not bool(user32.GetAsyncKeyState(0x3D) & 0x8000):
                self._eq_was_down = False

        return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

    def install(self):
        self._hook_ref = HOOKPROC(self._hook_proc)
        self._hook = user32.SetWindowsHookExW(WH_MOUSE_LL, self._hook_ref, None, 0)
        if self._hook:
            print(f"Mouse hook installed: {self._hook}")
        else:
            err = kernel32.GetLastError()
            print(f"Failed to install mouse hook! Error: {err}")

    def uninstall(self):
        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None

    def run_message_loop(self):
        """Windows message loop — обязателен для LL хука."""
        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
