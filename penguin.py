from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QPixmap, QPainter, QColor, QImage, QTransform
from PIL import Image
import random
import math

class Penguin(QGraphicsPixmapItem):
    def __init__(self, screen_width, screen_height, screenshot_pixmap=None, icon_positions=[]):
        super().__init__()
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screenshot_pixmap = screenshot_pixmap
        self.icon_positions = icon_positions
        
        # State Machine
        self.state = "IDLE"  # IDLE, WALK, STEAL, EXIT, EXITED
        self.state_timer = 0
        
        # Position (start from random edge)
        edge = random.choice(["left", "right", "top", "bottom"])
        if edge == "left":
            self.setPos(-64, random.randint(0, screen_height))
        elif edge == "right":
            self.setPos(screen_width + 64, random.randint(0, screen_height))
        elif edge == "top":
            self.setPos(random.randint(0, screen_width), -64)
        else:  # bottom
            self.setPos(random.randint(0, screen_width), screen_height + 64)
        
        # Target: choose real icon position if available, otherwise random
        if self.icon_positions and len(self.icon_positions) > 0:
            target_icon = random.choice(self.icon_positions)
            self.target_x = target_icon[0] + 32  # Center of icon
            self.target_y = target_icon[1] + 32
        else:
            self.target_x = random.randint(100, screen_width - 100)
            self.target_y = random.randint(100, screen_height - 100)
        
        # Movement - 5x faster
        self.speed = random.uniform(10, 20)
        
        # Stolen item (QGraphicsPixmapItem)
        self.stolen_item = None
        self.steal_pos = None
        
        # Animation
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_speed = 5  # Change frame every 5 updates
        
        # Load sprite sheet
        self.load_sprite_sheet()
        
    def load_sprite_sheet(self):
        """Load and split the kid sprite sheet into individual frames."""
        try:
            # Load the sprite sheet
            sprite_path = "assets/kid_sprite.png"
            full_sprite = QPixmap(sprite_path)
            
            if full_sprite.isNull():
                print(f"Failed to load sprite: {sprite_path}")
                self.create_fallback_sprite()
                return
            
            # Sprite sheet is 3x3 grid
            # Each sprite is approximately 1/3 of width and 1/3 of height
            sprite_width = full_sprite.width() // 3
            sprite_height = full_sprite.height() // 3
            
            # Extract all 9 frames
            self.sprite_frames = {
                'run': [],      # Row 1: frames 0-2 (running)
                'celebrate': [], # Row 2: frames 3-5 (jumping/celebrating)
                'walk': [],      # Row 3: frames 6-8 (walking/idle)
                'steal': []      # Separate: stealing animation
            }
            
            # Row 1 - Running (for WALK state)
            for col in range(3):
                frame = full_sprite.copy(col * sprite_width, 0, sprite_width, sprite_height)
                # Scale to 200% size (160x200)
                scaled = frame.scaled(160, 200, Qt.AspectRatioMode.KeepAspectRatio, 
                                     Qt.TransformationMode.SmoothTransformation)
                self.sprite_frames['run'].append(scaled)
            
            # Row 2 - Celebrating (for STEAL state)
            for col in range(3):
                frame = full_sprite.copy(col * sprite_width, sprite_height, sprite_width, sprite_height)
                scaled = frame.scaled(160, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
                self.sprite_frames['celebrate'].append(scaled)
            
            # Row 3 - Walking (for IDLE and EXIT states)
            for col in range(3):
                frame = full_sprite.copy(col * sprite_width, sprite_height * 2, sprite_width, sprite_height)
                scaled = frame.scaled(160, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
                self.sprite_frames['walk'].append(scaled)
            
            # Load separate stealing sprite (reaching up animation)
            try:
                stealing_sprite = QPixmap("assets/stealing.png")
                if not stealing_sprite.isNull():
                    scaled_stealing = stealing_sprite.scaled(160, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                                             Qt.TransformationMode.SmoothTransformation)
                    self.sprite_frames['steal'].append(scaled_stealing)
                else:
                    # Fallback to celebrate animation
                    self.sprite_frames['steal'] = self.sprite_frames['celebrate'].copy()
            except:
                # Fallback to celebrate animation
                self.sprite_frames['steal'] = self.sprite_frames['celebrate'].copy()
            
            # Set initial sprite
            self.setPixmap(self.sprite_frames['walk'][0])
            
        except Exception as e:
            print(f"Error loading sprite sheet: {e}")
            self.create_fallback_sprite()
    
    def make_transparent(self, pixmap):
        """Remove white/light background from pixmap and make it transparent."""
        # Convert QPixmap to QImage
        image = pixmap.toImage()
        
        # Convert to ARGB32 format for transparency support
        image = image.convertToFormat(QImage.Format.Format_ARGB32)
        
        # Process each pixel
        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixel(x, y)
                r = (pixel >> 16) & 0xFF
                g = (pixel >> 8) & 0xFF
                b = pixel & 0xFF
                
                # If pixel is close to white (light background), make it transparent
                if r > 240 and g > 240 and b > 240:
                    image.setPixel(x, y, 0)  # Fully transparent
        
        return QPixmap.fromImage(image)
    
    def create_fallback_sprite(self):
        """Create a simple fallback sprite if image loading fails."""
        pixmap = QPixmap(80, 100)
        pixmap.fill(QColor(0, 0, 0, 0))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Simple stick figure
        painter.setPen(QColor(0, 0, 0))
        painter.setBrush(QColor(100, 200, 255))
        
        # Head
        painter.drawEllipse(25, 10, 30, 30)
        # Body
        painter.drawLine(40, 40, 40, 70)
        # Arms
        painter.drawLine(40, 50, 20, 60)
        painter.drawLine(40, 50, 60, 60)
        # Legs
        painter.drawLine(40, 70, 25, 95)
        painter.drawLine(40, 70, 55, 95)
        
        painter.end()
        
        self.sprite_frames = {
            'run': [pixmap],
            'celebrate': [pixmap],
            'walk': [pixmap]
        }
        self.setPixmap(pixmap)
    
    def update_animation(self):
        """Update the animation frame based on current state."""
        self.animation_timer += 1
        
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            
            # Choose animation based on state
            if self.state == "WALK":
                frames = self.sprite_frames['run']
            elif self.state == "STEAL":
                frames = self.sprite_frames['steal']  # Use stealing animation
            elif self.state == "EXIT":
                frames = self.sprite_frames['celebrate']
            else:  # IDLE
                frames = self.sprite_frames['walk']
            
            # Cycle through frames
            self.animation_frame = (self.animation_frame + 1) % len(frames)
            current_pixmap = frames[self.animation_frame]
            
            # Flip sprite based on movement direction
            if hasattr(self, 'target_x') and hasattr(self, 'x'):
                # If moving left, flip the sprite horizontally
                if self.target_x < self.x():
                    current_pixmap = current_pixmap.transformed(
                        QTransform().scale(-1, 1)
                    )
            
            self.setPixmap(current_pixmap)
        
    def update_logic(self):
        """Update penguin state and position."""
        self.state_timer += 1
        
        # Update animation
        self.update_animation()
        
        if self.state == "IDLE":
            if self.state_timer > 30:  # Wait ~1 second
                self.state = "WALK"
                self.state_timer = 0
                
        elif self.state == "WALK":
            # Move towards target
            dx = self.target_x - self.x()
            dy = self.target_y - self.y()
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < 10:
                # Reached target
                self.state = "STEAL"
                self.state_timer = 0
            else:
                # Move
                move_x = (dx / distance) * self.speed
                move_y = (dy / distance) * self.speed
                self.setPos(self.x() + move_x, self.y() + move_y)
                    
        elif self.state == "STEAL":
            if self.state_timer == 1:
                # Steal the icon from screenshot
                self.steal_icon()
            
            if self.state_timer > 60:  # Steal animation ~2 seconds
                self.state = "EXIT"
                self.state_timer = 0
                # Set exit target (off screen)
                if self.x() < self.screen_width / 2:
                    self.target_x = -100
                else:
                    self.target_x = self.screen_width + 100
                self.target_y = random.randint(0, self.screen_height)
                
        elif self.state == "EXIT":
            # Move towards exit
            dx = self.target_x - self.x()
            dy = self.target_y - self.y()
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < 10 or self.x() < -100 or self.x() > self.screen_width + 100:
                self.state = "EXITED"
            else:
                move_x = (dx / distance) * self.speed
                move_y = (dy / distance) * self.speed
                self.setPos(self.x() + move_x, self.y() + move_y)
    
    def steal_icon(self):
        """Steal an icon from the screenshot at current position."""
        if self.screenshot_pixmap is None or self.stolen_item is not None:
            return
        
        # Crop a piece of the screenshot at penguin's position
        # Increased size to 140x140 to fully cover desktop icons with labels and selection highlights
        icon_size = 140
        crop_x = int(self.x()) - 20  # Offset to better center on icon
        crop_y = int(self.y()) - 20
        
        # Make sure we don't go out of bounds
        crop_x = max(0, min(crop_x, self.screenshot_pixmap.width() - icon_size))
        crop_y = max(0, min(crop_y, self.screenshot_pixmap.height() - icon_size))
        
        # Crop the icon from screenshot
        stolen_pixmap = self.screenshot_pixmap.copy(crop_x, crop_y, icon_size, icon_size)
        
        # Create a graphics item for the stolen icon
        self.stolen_item = QGraphicsPixmapItem(stolen_pixmap)
        self.stolen_item.setParentItem(self)
        self.stolen_item.setPos(0, -30)  # Position above penguin
        self.stolen_item.setZValue(10)  # Make sure it's on top
        
        # Store position for hole creation
        self.steal_pos = (crop_x, crop_y, icon_size)
