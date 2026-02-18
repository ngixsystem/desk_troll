"""
Overlay Window:
- Делает скриншот рабочего стола при запуске
- Показывает скриншот поверх рабочего стола (фейковый рабочий стол)
- Под скриншотом — kong.jpg на весь экран
- По клику ЛКМ/ПКМ — убирает блок 512x512 вокруг курсора, показывая kong
- Клавиша = + пароль 12021 — выход
"""
import ctypes
import ctypes.wintypes
import sys
import time

from PyQt6.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene, QApplication, QInputDialog, QLineEdit
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor

import mss
from PIL import Image


def minimize_all_windows():
    """Сворачивает все окна через Win+D (keybd_event)."""
    VK_LWIN    = 0x5B
    VK_D       = 0x44
    KEYEVENTF_KEYUP = 0x0002
    u32 = ctypes.windll.user32
    u32.keybd_event(VK_LWIN, 0, 0, 0)           # Win вниз
    u32.keybd_event(VK_D,    0, 0, 0)           # D вниз
    u32.keybd_event(VK_D,    0, KEYEVENTF_KEYUP, 0)  # D вверх
    u32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)  # Win вверх
    time.sleep(1.2)  # ждём анимацию


def capture_screenshot() -> QPixmap:
    """Делает скриншот всего экрана и возвращает QPixmap с альфа-каналом."""
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        img = sct.grab(monitor)
        pil = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX").convert("RGBA")
        data = pil.tobytes("raw", "RGBA")
        qimg = QImage(data, pil.width, pil.height, QImage.Format.Format_RGBA8888)
        # Конвертируем в ARGB32 — этот формат поддерживает прозрачность при рисовании
        qimg = qimg.convertToFormat(QImage.Format.Format_ARGB32)
        return QPixmap.fromImage(qimg)


class ClickSignals(QObject):
    clicked = pyqtSignal(int, int)  # x, y позиция клика


class OverlayWindow(QMainWindow):
    def __init__(self, on_exit):
        super().__init__()
        self.on_exit = on_exit

        user32 = ctypes.windll.user32
        self.sw = user32.GetSystemMetrics(0)
        self.sh = user32.GetSystemMetrics(1)

        # Окно поверх всего, без рамки — НЕ прозрачное для кликов
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(0, 0, self.sw, self.sh)

        # Сцена
        self.scene = QGraphicsScene(0, 0, self.sw, self.sh)
        self.view = QGraphicsView(self.scene, self)
        self.view.setGeometry(0, 0, self.sw, self.sh)
        self.view.setStyleSheet("background: transparent; border: 0px;")
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 1. Фон — kong.jpg на весь экран
        kong_pixmap = QPixmap("assets/kong.jpg")
        if not kong_pixmap.isNull():
            kong_pixmap = kong_pixmap.scaled(
                self.sw, self.sh,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
        else:
            kong_pixmap = QPixmap(self.sw, self.sh)
            kong_pixmap.fill(QColor(0, 0, 0))
        self.kong_item = self.scene.addPixmap(kong_pixmap)
        self.kong_item.setZValue(0)

        # 2. Скриншот поверх kong (сначала сворачиваем все окна)
        print("Minimizing all windows...")
        minimize_all_windows()
        print("Capturing screenshot...")
        self.screenshot_pixmap = capture_screenshot()
        self.screenshot_item = self.scene.addPixmap(self.screenshot_pixmap)
        self.screenshot_item.setZValue(1)
        print("Screenshot captured.")

        # Разрешение закрытия
        self.allow_close = False

        # Фокус
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.activateWindow()
        self.raise_()

    def _on_click(self, x, y):
        """Вызывается при клике мыши (из хука) — стираем блок 512x512."""
        print(f"[OVERLAY] _on_click called at {x}, {y}")
        self._erase_block(x, y, 512)

    def _erase_block(self, cx, cy, size):
        """Стираем блок size×size вокруг точки (cx, cy) из скриншота."""
        half = size // 2
        x = max(0, cx - half)
        y = max(0, cy - half)
        w = min(size, self.sw - x)
        h = min(size, self.sh - y)

        # Конвертируем pixmap → QImage с альфа-каналом
        img = self.screenshot_item.pixmap().toImage().convertToFormat(
            QImage.Format.Format_ARGB32_Premultiplied
        )
        # Стираем блок (делаем прозрачным)
        painter = QPainter(img)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(x, y, w, h, QColor(0, 0, 0, 0))
        painter.end()
        # Обновляем pixmap на сцене
        self.screenshot_item.setPixmap(QPixmap.fromImage(img))
        print(f"[OVERLAY] Erased block at ({x},{y}) size {w}x{h}")


    def show_password_dialog(self):
        """Показать диалог пароля."""
        password, ok = QInputDialog.getText(
            self,
            'Выход',
            'Введите пароль:',
            QLineEdit.EchoMode.Password,
        )
        if ok and password == "12021":
            self.allow_close = True
            QApplication.quit()


    def closeEvent(self, event):
        if self.allow_close:
            event.accept()
        else:
            event.ignore()
