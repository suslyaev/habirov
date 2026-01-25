#!/usr/bin/env python3
"""
Простой скрипт для генерации PNG иконок
Использует только Pillow (PIL), не требует Cairo
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

# Размеры иконок
SIZES = [16, 32, 192, 512]

def create_icon(size):
    """Создает иконку заданного размера"""
    # Создаем изображение с синим фоном
    img = Image.new('RGB', (size, size), color='#007bff')
    draw = ImageDraw.Draw(img)
    
    # Радиус скругления (примерно 20% от размера)
    radius = int(size * 0.2)
    
    # Рисуем скругленный прямоугольник (фон)
    if radius > 0:
        # Создаем маску для скругления
        mask = Image.new('L', (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (size, size)], radius=radius, fill=255)
        # Применяем маску (для простоты просто рисуем прямоугольник)
        draw.rounded_rectangle([(0, 0), (size, size)], radius=radius, fill='#007bff')
    else:
        draw.rectangle([(0, 0), (size, size)], fill='#007bff')
    
    # Рисуем символ рубля
    # Размер символа зависит от размера иконки
    symbol_size = int(size * 0.4)
    center_x = size // 2
    center_y = size // 2
    
    # Толщина линий
    line_width = max(2, size // 32)
    
    # Рисуем символ рубля (упрощенная версия)
    # Вертикальная линия
    x = center_x - symbol_size // 3
    draw.rectangle(
        [x - line_width//2, center_y - symbol_size//2, 
         x + line_width//2, center_y + symbol_size//2],
        fill='white'
    )
    
    # Горизонтальные линии
    y1 = center_y - symbol_size // 3
    y2 = center_y
    y3 = center_y + symbol_size // 3
    
    for y in [y1, y2, y3]:
        draw.rectangle(
            [x - line_width, y - line_width//2,
             x + symbol_size // 2, y + line_width//2],
            fill='white'
        )
    
    # Дополнительные декоративные элементы
    dot_size = max(2, size // 64)
    for offset_x, offset_y in [(-symbol_size//1.5, -symbol_size//2), 
                               (-symbol_size//1.5, symbol_size//2),
                               (symbol_size//1.5, -symbol_size//2),
                               (symbol_size//1.5, symbol_size//2)]:
        draw.ellipse(
            [center_x + offset_x - dot_size, center_y + offset_y - dot_size,
             center_x + offset_x + dot_size, center_y + offset_y + dot_size],
            fill='white'
        )
    
    return img

def generate_icons():
    """Генерирует все иконки"""
    script_dir = Path(__file__).parent
    
    print("🎨 Генерация иконок...")
    
    for size in SIZES:
        try:
            icon = create_icon(size)
            png_path = script_dir / f'icon-{size}.png'
            icon.save(png_path, 'PNG')
            print(f"✅ Создан {png_path} ({size}x{size})")
        except Exception as e:
            print(f"❌ Ошибка при создании icon-{size}.png: {e}")

if __name__ == '__main__':
    try:
        generate_icons()
        print("\n🎉 Готово! Все иконки созданы.")
        print("💡 Совет: Используйте create_icons_browser.html для более детального дизайна")
    except ImportError:
        print("❌ Ошибка: Установите Pillow: pip install pillow")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
