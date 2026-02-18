from PyQt6.QtWidgets import QGraphicsPixmapItem
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QTransform, QCursor
import random
import math


class Fly(QGraphicsPixmapItem):
    """
    Муха, которая убегает от курсора.
    Спрайт-лист: assets/fly.png — сетка 2x2 (4 кадра).
    Тело и крылья статичны, только ноги меняются между кадрами.
    """

    FLEE_RADIUS = 150   # px — начало побега
    PANIC_RADIUS = 70   # px — паника (быстрее)

    def __init__(self, screen_width, screen_height):
        super().__init__()

        self.screen_width = screen_width
        self.screen_height = screen_height

        # Загружаем спрайт-лист и нарезаем кадры
        self.frames = []
        self._load_frames()

        # Начальная позиция — случайная точка на экране
        self.setPos(
            random.randint(100, screen_width - 100),
            random.randint(100, screen_height - 100),
        )

        # Центрируем origin спрайта
        if self.frames:
            w = self.frames[0].width()
            h = self.frames[0].height()
            self.setOffset(-w / 2, -h / 2)
            self.setTransformOriginPoint(0, 0)  # вращаем вокруг центра

        # Анимация
        self.frame_idx = 0
        self.anim_timer = 0
        self.anim_speed_wander = 8   # тиков на кадр при блуждании
        self.anim_speed_flee = 3     # тиков на кадр при побеге

        # Скорости
        self.wander_speed = random.uniform(1.5, 3.0)
        self.flee_speed = random.uniform(8, 14)

        # Случайное блуждание
        self.wander_angle = random.uniform(0, 2 * math.pi)
        self.wander_timer = 0
        self.wander_change = random.randint(30, 80)

        # Дрожание
        self.jitter = 1.5

        # Режим
        self.mode = "WANDER"

        # Текущий угол поворота (градусы)
        self.current_angle = 0.0

        # Показываем первый кадр
        self._set_frame(0)

    # ------------------------------------------------------------------ #

    def _load_frames(self):
        """Нарезаем спрайт-лист 2x2 на 4 кадра."""
        sheet = QPixmap("assets/fly.png")
        if sheet.isNull():
            print("ERROR: не удалось загрузить assets/fly.png")
            # Создаём заглушку
            placeholder = QPixmap(80, 80)
            placeholder.fill(Qt.GlobalColor.transparent)
            self.frames = [placeholder] * 4
            return

        cols, rows = 2, 2
        fw = sheet.width() // cols
        fh = sheet.height() // rows

        # Целевой размер кадра (масштабируем до удобного)
        target_w = 40
        target_h = 40

        for row in range(rows):
            for col in range(cols):
                frame = sheet.copy(col * fw, row * fh, fw, fh)
                frame = frame.scaled(
                    target_w, target_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.frames.append(frame)

        print(f"Loaded {len(self.frames)} fly frames ({fw}x{fh} each, scaled to {target_w}x{target_h})")

    def _set_frame(self, idx):
        """Установить кадр анимации."""
        frame = self.frames[idx % len(self.frames)]
        self.setPixmap(frame)

    def _apply_rotation(self, move_x, move_y):
        """Повернуть спрайт в направлении движения."""
        if abs(move_x) < 0.1 and abs(move_y) < 0.1:
            return  # стоим — не меняем угол
        # atan2 даёт угол в радианах, переводим в градусы
        # Спрайт по умолчанию смотрит вверх (голова к верху экрана)
        # atan2(y, x) = 0 при движении вправо → нам нужно +90° поправка
        angle_deg = math.degrees(math.atan2(move_y, move_x)) + 90
        # Плавное сглаживание угла (lerp)
        diff = angle_deg - self.current_angle
        # Нормализуем разницу в диапазон [-180, 180]
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        self.current_angle += diff * 0.25  # скорость поворота
        self.setRotation(self.current_angle)

    # ------------------------------------------------------------------ #

    def update_logic(self):
        """Вызывается каждый тик (~30 FPS)."""

        # --- Позиция курсора ---
        cursor_pos = QCursor.pos()
        cx, cy = cursor_pos.x(), cursor_pos.y()
        fx, fy = self.x(), self.y()

        # Вектор ОТ курсора К мухе
        dx_cur = fx - cx
        dy_cur = fy - cy
        dist = math.sqrt(dx_cur * dx_cur + dy_cur * dy_cur)

        # --- Режим ---
        self.mode = "FLEE" if dist < self.FLEE_RADIUS else "WANDER"

        # --- Анимация ног ---
        anim_speed = self.anim_speed_flee if self.mode == "FLEE" else self.anim_speed_wander
        self.anim_timer += 1
        if self.anim_timer >= anim_speed:
            self.anim_timer = 0
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)
            self._set_frame(self.frame_idx)

        # --- Движение ---
        if self.mode == "FLEE":
            if dist > 0:
                nx, ny = dx_cur / dist, dy_cur / dist
            else:
                a = random.uniform(0, 2 * math.pi)
                nx, ny = math.cos(a), math.sin(a)

            speed = self.flee_speed * 1.8 if dist < self.PANIC_RADIUS else self.flee_speed
            move_x = nx * speed + random.uniform(-self.jitter, self.jitter)
            move_y = ny * speed + random.uniform(-self.jitter, self.jitter)

        else:
            # Случайное блуждание
            self.wander_timer += 1
            if self.wander_timer >= self.wander_change:
                self.wander_timer = 0
                self.wander_change = random.randint(30, 80)
                self.wander_angle += random.uniform(-math.pi / 2, math.pi / 2)

            move_x = math.cos(self.wander_angle) * self.wander_speed + random.uniform(-self.jitter, self.jitter)
            move_y = math.sin(self.wander_angle) * self.wander_speed + random.uniform(-self.jitter, self.jitter)

        # --- Поворачиваем корпус в направлении движения ---
        self._apply_rotation(move_x, move_y)

        # --- Применяем ---
        new_x = fx + move_x
        new_y = fy + move_y

        # --- Отскок от краёв ---
        margin = 60
        if new_x < margin:
            new_x = margin
            self.wander_angle = random.uniform(-math.pi / 4, math.pi / 4)
        elif new_x > self.screen_width - margin:
            new_x = self.screen_width - margin
            self.wander_angle = random.uniform(math.pi * 3 / 4, math.pi * 5 / 4)

        if new_y < margin:
            new_y = margin
            self.wander_angle = random.uniform(0, math.pi)
        elif new_y > self.screen_height - margin:
            new_y = self.screen_height - margin
            self.wander_angle = random.uniform(-math.pi, 0)

        self.setPos(new_x, new_y)
