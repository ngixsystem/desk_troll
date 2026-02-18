# -*- coding: utf-8 -*-
"""
cmd_troll.py  --  Fake ransomware prank.
Phases: header -> deleting -> encrypt -> ransom (Bitcoin screen)
Exit: press '=' -> password 12021
Supports multiple monitors.
"""

import sys
import random
import ctypes
import ctypes.wintypes
import threading

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QInputDialog, QLineEdit, QPlainTextEdit, QStackedWidget,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QRect, QObject, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QKeyEvent, QPainter, QClipboard, QPixmap, QIcon

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WH_KEYBOARD_LL = 13
WM_KEYDOWN     = 0x0100
WM_SYSKEYDOWN  = 0x0104
VK_LWIN     = 0x5B
VK_RWIN     = 0x5C
VK_F4       = 0x73
VK_ESCAPE   = 0x1B
VK_OEM_PLUS = 0xBB

# ── Fake data ─────────────────────────────────────────────────────────────────
FAKE_DRIVES = ["C:\\", "D:\\", "C:\\Windows\\", "C:\\Users\\"]
FAKE_DIRS = [
    "Documents", "Desktop", "Downloads", "Pictures", "Videos",
    "AppData\\Roaming", "AppData\\Local", "Program Files",
    "Program Files (x86)", "Windows\\System32", "Windows\\SysWOW64",
    "Users\\Public", "ProgramData",
]
FAKE_EXTS = [
    ".exe", ".dll", ".sys", ".dat", ".db", ".log", ".ini",
    ".docx", ".xlsx", ".pdf", ".jpg", ".png", ".mp4", ".zip",
    ".py", ".json", ".xml", ".bat", ".ps1", ".reg",
]
FAKE_NAMES = [
    "explorer", "svchost", "winlogon", "lsass", "csrss",
    "ntoskrnl", "hal", "kernel32", "user32", "advapi32",
    "document_final", "photo_2024", "backup", "passwords",
    "important", "project", "report_2025", "secret",
    "config", "registry_backup", "system_restore",
]
VIRUS_HEADERS = [
    "VIRUS.EXE v3.1 -- SYSTEM DESTROYER",
    "RANSOMWARE ACTIVATED -- ALL FILES WILL BE ENCRYPTED",
    "CRITICAL SYSTEM INFECTION DETECTED",
    "[!] W32/Trojan.Destroyer -- PAYLOAD EXECUTING [!]",
]
RU_WARNING = (
    "\u26a0  \u0412\u0421\u0415 \u0412\u0410\u0428\u0418 \u0424\u0410\u0419\u041b\u042b "
    "\u0411\u0423\u0414\u0423\u0422 \u0417\u0410\u0428\u0418\u0424\u0420\u041e\u0412\u0410\u041d\u042b "
    "\u0418 \u0423\u0414\u0410\u041b\u0415\u041d\u042b  \u26a0"
)
FAKE_ERRORS = [
    "ERROR: Access denied -- forcing deletion...",
    "WARNING: File in use -- terminating process...",
    "OVERRIDE: System protection bypassed",
    "KERNEL: Memory protection disabled",
    "BYPASS: Windows Defender neutralized",
    "ALERT: Shadow copies being destroyed...",
    "CRITICAL: MBR overwrite in progress...",
]

FAKE_BTC_ADDRESS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf" + "Na"

# ── Marquee ticker ───────────────────────────────────────────────────────────
MARQUEE_TEXT = (
    "  \u26a0  "
    "\u0412\u041d\u0418\u041c\u0410\u041d\u0418\u0415: "
    "\u0412\u0430\u0448\u0438 \u0444\u0430\u0439\u043b\u044b "
    "\u0437\u0430\u0448\u0438\u0444\u0440\u043e\u0432\u0430\u043d\u044b!  "
    "\u041f\u0435\u0440\u0435\u0432\u0435\u0434\u0438\u0442\u0435 5 000 USD \u0432 Bitcoin  "
    "\u0438\u043b\u0438 \u0432\u0441\u0435 \u0434\u0430\u043d\u043d\u044b\u0435 "
    "\u0431\u0443\u0434\u0443\u0442 \u0443\u0434\u0430\u043b\u0435\u043d\u044b!  "
    "\u0427\u0435\u0440\u0435\u0437 30 \u043c\u0438\u043d\u0443\u0442 "
    "\u0432\u0438\u0440\u0443\u0441 \u0440\u0430\u0441\u043f\u0440\u043e\u0441\u0442\u0440\u0430\u043d\u0438\u0442\u0441\u044f "
    "\u043d\u0430 \u0432\u0441\u0435 \u043a\u043e\u043c\u043f\u044c\u044e\u0442\u0435\u0440\u044b "
    "\u0432 \u043e\u0444\u0438\u0441\u0435!  "
    "\u26a0  BTC: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa  "
    "\u26a0  DO NOT TURN OFF YOUR COMPUTER  "
    "\u26a0  "
)


class MarqueeTicker(QLabel):
    """Horizontally scrolling text ticker."""

    def __init__(self, text=MARQUEE_TEXT, bg="#AA0000", fg="#FFFFFF",
                 font_size=12, speed=2, parent=None):
        super().__init__(parent)
        self._full_text = text * 3
        self._offset = 0
        self._speed = speed
        self._fg = fg
        self._bg = bg

        f = QFont("Consolas", font_size, QFont.Weight.Bold)
        self.setFont(f)
        self.setStyleSheet(f"background-color: {bg}; color: {fg};")
        self.setFixedHeight(self.fontMetrics().height() + 10)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._scroll)
        self._timer.start(30)

    def _scroll(self):
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(self._full_text)
        self._offset = (self._offset + self._speed) % (text_w // 3)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self._bg))
        painter.setPen(QColor(self._fg))
        painter.setFont(self.font())
        fm = self.fontMetrics()
        y = (self.height() + fm.ascent() - fm.descent()) // 2
        painter.drawText(-self._offset, y, self._full_text)
        painter.end()


def random_path():
    drive = random.choice(FAKE_DRIVES)
    parts = [random.choice(FAKE_DIRS)]
    if random.random() < 0.4:
        parts.append(random.choice(FAKE_DIRS).split("\\")[0])
    name = random.choice(FAKE_NAMES) + random.choice(FAKE_EXTS)
    return drive + "\\".join(parts) + "\\" + name


# ── Keyboard hook ─────────────────────────────────────────────────────────────
_kb_hook_handle = None
_kb_hook_ref    = None


def _make_kb_hook():
    global _kb_hook_handle, _kb_hook_ref

    HOOKPROC = ctypes.CFUNCTYPE(
        ctypes.c_long,
        ctypes.c_int,
        ctypes.wintypes.WPARAM,
        ctypes.c_void_p,
    )

    def handler(nCode, wParam, lParam):
        if nCode >= 0 and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            vk = ctypes.cast(lParam, ctypes.POINTER(ctypes.c_ulong)).contents.value
            if vk != VK_OEM_PLUS:
                return 1
        return user32.CallNextHookEx(_kb_hook_handle, nCode, wParam, lParam)

    _kb_hook_ref = HOOKPROC(handler)
    _kb_hook_handle = user32.SetWindowsHookExW(
        WH_KEYBOARD_LL, _kb_hook_ref,
        kernel32.GetModuleHandleW(None), 0
    )

    msg = ctypes.wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


def uninstall_kb_hook():
    global _kb_hook_handle
    if _kb_hook_handle:
        user32.UnhookWindowsHookEx(_kb_hook_handle)
        _kb_hook_handle = None


# ── Logic & Controller ────────────────────────────────────────────────────────
class TrollLogic(QObject):
    phase_changed = pyqtSignal(str)     # new_phase
    tick_event = pyqtSignal()           # clock tick
    request_password = pyqtSignal()     # '=' key pressed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.phase = "header"
        self.phase_timer = 0
        self.deleted_count = 0
        self.total_fake = random.randint(18000, 32000)

        # Global '=' key poller
        self._eq_was_down = False
        self._key_timer = QTimer(self)
        self._key_timer.timeout.connect(self._check_eq_key)
        self._key_timer.start(100)

        # Main tick loop
        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._on_tick)
        self._tick_timer.start(60)

    def _check_eq_key(self):
        is_down = bool(user32.GetAsyncKeyState(VK_OEM_PLUS) & 0x8000)
        if is_down and not self._eq_was_down:
            self.request_password.emit()
        self._eq_was_down = is_down

    def _on_tick(self):
        self.phase_timer += 1

        if self.phase == "header":
            if self.phase_timer > 15:
                self.phase = "deleting"
                self.phase_timer = 0
                self.phase_changed.emit("deleting")
            return

        if self.phase == "deleting":
            self.deleted_count += random.randint(1, 3)
            self.tick_event.emit()

            if self.deleted_count >= self.total_fake:
                self.phase = "encrypt"
                self.phase_timer = 0
                self.phase_changed.emit("encrypt")

        elif self.phase == "encrypt":
            self.tick_event.emit()
            if self.phase_timer > 120:
                self.phase = "ransom"
                self.phase_timer = 0
                self._tick_timer.stop()
                self.phase_changed.emit("ransom")


# ── UI Components ─────────────────────────────────────────────────────────────
class RansomScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0a0a0a;")

        root = QVBoxLayout(self)
        root.setContentsMargins(60, 40, 60, 40)
        root.setSpacing(16)

        def lbl(text, size=12, color="#FF0000", bold=False, center=True):
            w = QLabel(text)
            f = QFont("Consolas", size)
            if bold: f.setWeight(QFont.Weight.Bold)
            w.setFont(f)
            w.setStyleSheet(f"color: {color}; background: transparent;")
            w.setWordWrap(True)
            if center: w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return w

        skull = (
            "  ██████╗  █████╗ ███╗   ██╗ ██████╗ ███████╗██████╗ \n"
            " ██╔══██╗██╔══██╗████╗  ██║██╔════╝ ██╔════╝██╔══██╗\n"
            " ██║  ██║███████║██╔██╗ ██║██║  ███╗█████╗  ██████╔╝\n"
            " ██║  ██║██╔══██║██║╚██╗██║██║   ██║██╔══╝  ██╔══██╗\n"
            " ██████╔╝██║  ██║██║ ╚████║╚██████╔╝███████╗██║  ██║\n"
            " ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝"
        )
        skull_lbl = QLabel(skull)
        skull_lbl.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        skull_lbl.setStyleSheet("color: #FF0000; background: transparent;")
        skull_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(skull_lbl)

        root.addWidget(lbl(
            "\u0412\u0410\u0428\u0418 \u0424\u0410\u0419\u041b\u042b "
            "\u0417\u0410\u0428\u0418\u0424\u0420\u041e\u0412\u0410\u041d\u042b!",
            size=22, color="#FF0000", bold=True
        ))

        sep = QLabel("=" * 90)
        sep.setFont(QFont("Consolas", 10))
        sep.setStyleSheet("color: #FF3300; background: transparent;")
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(sep)

        root.addWidget(lbl(
            "\u0427\u0442\u043e\u0431\u044b \u0432\u043e\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c "
            "\u0434\u043e\u0441\u0442\u0443\u043f \u043a \u0432\u0430\u0448\u0438\u043c "
            "\u0444\u0430\u0439\u043b\u0430\u043c, \u043f\u0435\u0440\u0435\u0432\u0435\u0434\u0438\u0442\u0435 "
            "5 000 USD \u0432 Bitcoin \u043d\u0430 \u0443\u043a\u0430\u0437\u0430\u043d\u043d\u044b\u0439 "
            "\u043a\u043e\u0448\u0435\u043b\u0451\u043a. \u0423 \u0432\u0430\u0441 \u0435\u0441\u0442\u044c "
            "30 \u043c\u0438\u043d\u0443\u0442. \u041f\u043e\u0441\u043b\u0435 \u044d\u0442\u043e\u0433\u043e "
            "\u043a\u043b\u044e\u0447 \u0431\u0443\u0434\u0435\u0442 \u0443\u043d\u0438\u0447\u0442\u043e\u0436\u0435\u043d.",
            size=13, color="#FFAA00", bold=False
        ))

        self._timer_label = lbl("", size=20, color="#FF4444", bold=True)
        root.addWidget(self._timer_label)
        self._seconds_left = 30 * 60
        self._update_timer()
        self._countdown = QTimer()
        self._countdown.timeout.connect(self._tick_countdown)
        self._countdown.start(1000)

        root.addWidget(lbl(
            "\u0410\u0434\u0440\u0435\u0441 Bitcoin \u043a\u043e\u0448\u0435\u043b\u044c\u043a\u0430:",
            size=11, color="#AAAAAA"
        ))

        addr_frame = QFrame()
        addr_frame.setStyleSheet(
            "background: #1a1a1a; border: 2px solid #FF6600; border-radius: 6px;"
        )
        addr_layout = QHBoxLayout(addr_frame)
        addr_layout.setContentsMargins(16, 10, 16, 10)

        self._addr_label = QLabel(FAKE_BTC_ADDRESS)
        self._addr_label.setFont(QFont("Consolas", 13, QFont.Weight.Bold))
        self._addr_label.setStyleSheet("color: #FF9900; background: transparent; border: none;")
        self._addr_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        addr_layout.addWidget(self._addr_label, stretch=1)

        copy_btn = QLabel("[ COPY ]")
        copy_btn.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        copy_btn.setStyleSheet("color: #00FF00; background: transparent; border: none;")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.mousePressEvent = self._copy_address
        addr_layout.addWidget(copy_btn)
        root.addWidget(addr_frame)

        root.addWidget(lbl("5 000 USD = 0.0847 BTC", size=14, color="#FFFF00", bold=True))
        root.addWidget(lbl(
            "After payment send transaction ID to: pay@darkweb-recovery.onion\n"
            "DO NOT restart your computer. DO NOT contact police.",
            size=10, color="#888888"
        ))
        root.addWidget(sep)
        root.addWidget(lbl(
            "\u041d\u0435 \u043f\u043b\u0430\u0442\u0438\u0442\u0435? "
            "\u041a\u0430\u0436\u0434\u044b\u0435 6 \u0447\u0430\u0441\u043e\u0432 "
            "\u0446\u0435\u043d\u0430 \u0443\u0432\u0435\u043b\u0438\u0447\u0438\u0432\u0430\u0435\u0442\u0441\u044f "
            "\u043d\u0430 1 000 USD.",
            size=11, color="#FF4444"
        ))

        office_warn = QLabel(
            "\u26a0  \u0412\u041d\u0418\u041c\u0410\u041d\u0418\u0415!  "
            "\u0415\u0441\u043b\u0438 \u0432 \u0442\u0435\u0447\u0435\u043d\u0438\u0435 30 "
            "\u043c\u0438\u043d\u0443\u0442 \u043e\u043f\u043b\u0430\u0442\u0430 \u043d\u0435 "
            "\u043f\u043e\u0441\u0442\u0443\u043f\u0438\u0442, \u0432\u0438\u0440\u0443\u0441 "
            "\u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438 "
            "\u0440\u0430\u0441\u043f\u0440\u043e\u0441\u0442\u0440\u0430\u043d\u0438\u0442\u0441\u044f "
            "\u043d\u0430 \u0412\u0421\u0415 \u043a\u043e\u043c\u043f\u044c\u044e\u0442\u0435\u0440\u044b "
            "\u0432 \u0432\u0430\u0448\u0435\u043c \u043e\u0444\u0438\u0441\u0435.  \u26a0"
        )
        office_warn.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        office_warn.setStyleSheet(
            "color: #FFFFFF; background: #AA0000; padding: 10px; border-radius: 4px;"
        )
        office_warn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        office_warn.setWordWrap(True)
        root.addWidget(office_warn)
        root.addStretch()
        root.addWidget(MarqueeTicker())
        hint = QLabel("Press = to authenticate")
        hint.setFont(QFont("Consolas", 7))
        hint.setStyleSheet("color: #111111; background: transparent;")
        hint.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(hint)

    def _copy_address(self, _event):
        QApplication.clipboard().setText(FAKE_BTC_ADDRESS)

    def _tick_countdown(self):
        self._seconds_left = max(0, self._seconds_left - 1)
        self._update_timer()

    def _update_timer(self):
        h = self._seconds_left // 3600
        m = (self._seconds_left % 3600) // 60
        s = self._seconds_left % 60
        self._timer_label.setText(
            f"\u0412\u0440\u0435\u043c\u044f \u0434\u043e "
            f"\u0443\u043d\u0438\u0447\u0442\u043e\u0436\u0435\u043d\u0438\u044f "
            f"\u043a\u043b\u044e\u0447\u0430: {h:02d}:{m:02d}:{s:02d}"
        )


class CmdScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #000000;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        mono = QFont("Consolas", 11)
        mono.setStyleHint(QFont.StyleHint.Monospace)

        self.header = QLabel(random.choice(VIRUS_HEADERS))
        self.header.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self.header.setStyleSheet("color: #FF0000; background: #000000;")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header)

        sep = QLabel("=" * 80)
        sep.setFont(mono)
        sep.setStyleSheet("color: #FF3300; background: #000000;")
        layout.addWidget(sep)

        ru_warn = QLabel(RU_WARNING)
        ru_warn.setFont(QFont("Consolas", 13, QFont.Weight.Bold))
        ru_warn.setStyleSheet("color: #FF0000; background: #000000;")
        ru_warn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ru_warn)

        sep2 = QLabel("=" * 80)
        sep2.setFont(mono)
        sep2.setStyleSheet("color: #FF3300; background: #000000;")
        layout.addWidget(sep2)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(mono)
        self.log.setStyleSheet(
            "QPlainTextEdit { background-color: #000000; color: #00FF00; border: none; }"
        )
        self.log.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.log.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.log, stretch=1)

        self.progress_label = QLabel()
        self.progress_label.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self.progress_label.setStyleSheet("color: #FFFF00; background: #000000;")
        layout.addWidget(self.progress_label)

        self.status_label = QLabel("Initializing payload...")
        self.status_label.setFont(mono)
        self.status_label.setStyleSheet("color: #FF4444; background: #000000;")
        layout.addWidget(self.status_label)

        layout.addWidget(MarqueeTicker())

        hint = QLabel("Press = to authenticate")
        hint.setFont(QFont("Consolas", 7))
        hint.setStyleSheet("color: #111111; background: #000000;")
        hint.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(hint)


class CmdTrollWindow(QMainWindow):
    def __init__(self, logic, is_primary=False):
        super().__init__()
        self.logic = logic
        self.is_primary = is_primary
        self._allow_close = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        # Prevent icon flickering
        blank = QPixmap(1, 1)
        blank.fill(QColor(0,0,0,0))
        self.setWindowIcon(QIcon(blank))

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        self.setPalette(pal)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._cmd = CmdScreen()
        self._ransom = RansomScreen()
        self._stack.addWidget(self._cmd)
        self._stack.addWidget(self._ransom)
        self._stack.setCurrentIndex(0)

        # Connect to logic signals
        self.logic.phase_changed.connect(self._on_phase_changed)
        self.logic.tick_event.connect(self._on_tick)
        self.logic.request_password.connect(self._on_request_password)

        # Blinking header independent
        self._blink_state = True
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink_header)
        self._blink_timer.start(500)

        self._update_progress()

    def _on_phase_changed(self, phase):
        if phase == "deleting":
            self._append("Starting deletion sequence...\n", "#FF0000")
        elif phase == "encrypt":
            self._append("\n[!] DELETION COMPLETE. Starting encryption...\n", "#FF0000")
        elif phase == "ransom":
            self._stack.setCurrentIndex(1)
            self._blink_timer.stop()

    def _on_tick(self):
        phase = self.logic.phase
        if phase == "deleting":
            if random.random() < 0.05:
                self._append(random.choice(FAKE_ERRORS), "#FF4444")
            else:
                path = random_path()
                size = random.randint(1, 999999)
                self._append(f"DEL  {path}  [{size:,} bytes]", "#00FF00")
            self._update_progress()
        
        elif phase == "encrypt":
            sector = random.randint(0, 0xFFFFFF)
            key = ''.join(random.choices('0123456789ABCDEF', k=32))
            self._append(f"ENCRYPT  sector 0x{sector:06X}  key={key}", "#FF8800")

    def _on_request_password(self):
        if self.is_primary:
            self.show_password_dialog()

    def _append(self, text, color="#00FF00"):
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(" ", "&nbsp;")
        self._cmd.log.appendHtml(
            f'<span style="color:{color};font-family:Consolas,monospace;">{safe}</span>'
        )
        sb = self._cmd.log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _update_progress(self):
        pct = min(100, int(self.logic.deleted_count / self.logic.total_fake * 100))
        filled = int(50 * pct / 100)
        bar = "#" * filled + "-" * (50 - filled)
        self._cmd.progress_label.setText(
            f"[{bar}] {pct}%   "
            f"{self.logic.deleted_count:,} / {self.logic.total_fake:,} files deleted"
        )

    def _blink_header(self):
        self._blink_state = not self._blink_state
        color = "#FF0000" if self._blink_state else "#880000"
        self._cmd.header.setStyleSheet(f"color: {color}; background: #000000;")

    def show_password_dialog(self):
        password, ok = QInputDialog.getText(
            self, "Authentication Required",
            "Enter password to abort:",
            QLineEdit.EchoMode.Password,
        )
        if ok and password == "12021":
            print("Password correct. Exiting...")
            uninstall_kb_hook()
            QApplication.closeAllWindows()
            sys.exit(0)

    def closeEvent(self, event):
        event.ignore()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Equal and self.is_primary:
            self.show_password_dialog()
        event.accept()


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    
    # Global icon blank
    blank_pixmap = QPixmap(1, 1)
    blank_pixmap.fill(QColor(0, 0, 0, 0))
    app.setWindowIcon(QIcon(blank_pixmap))

    kb_thread = threading.Thread(target=_make_kb_hook, daemon=True)
    kb_thread.start()

    logic = TrollLogic()
    windows = []
    
    screens = app.screens()
    for i, screen in enumerate(screens):
        win = CmdTrollWindow(logic, is_primary=(i == 0))
        # Set geometry to cover this specific screen
        win.setGeometry(screen.geometry())
        win.showFullScreen() 
        windows.append(win)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
