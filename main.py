#!/usr/bin/env python3
"""
Запускает overlay (скриншот + kong.jpg) и инверсию мыши одновременно.
Выход: нажать '=' и ввести пароль 12021.
"""
import sys
import threading
import ctypes

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer

from overlay import OverlayWindow
from mouse_inverter import MouseInverter, Signals

user32 = ctypes.windll.user32
VK_OEM_PLUS = 0xBB  # клавиша '='


def main():
    app = QApplication(sys.argv)

    signals = Signals()

    # Overlay
    window = OverlayWindow(on_exit=lambda: None)

    # Подключаем сигналы
    signals.request_password.connect(
        window.show_password_dialog,
        Qt.ConnectionType.QueuedConnection
    )
    signals.mouse_clicked.connect(
        window._on_click,
        Qt.ConnectionType.QueuedConnection
    )

    window.show()

    # Инверсия мыши в отдельном потоке
    inverter = MouseInverter(signals)

    def hook_thread():
        inverter._thread_id = threading.get_ident()
        inverter.install()
        inverter.run_message_loop()

    t = threading.Thread(target=hook_thread, daemon=True)
    t.start()

    # Отдельный таймер для опроса клавиши '=' (каждые 100мс)
    _eq_was_down = [False]

    def check_equal_key():
        state = user32.GetAsyncKeyState(VK_OEM_PLUS)
        is_down = bool(state & 0x8000)
        if is_down and not _eq_was_down[0]:
            print("[TIMER] '=' key detected, requesting password")
            window.show_password_dialog()
        _eq_was_down[0] = is_down

    key_timer = QTimer()
    key_timer.timeout.connect(check_equal_key)
    key_timer.start(100)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
