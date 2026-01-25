#!/usr/bin/env python3
"""
Скрипт для генерации PNG иконок из SVG
Требует: pip install cairosvg pillow
"""

import os
import sys
from pathlib import Path

try:
    import cairosvg
    from PIL import Image
    import io
except ImportError:
    print("Установите зависимости: pip install cairosvg pillow")
    sys.exit(1)

# Размеры иконок
SIZES = [16, 32, 192, 512]

def generate_icons():
    """Генерирует PNG иконки из SVG"""
    script_dir = Path(__file__).parent
    svg_path = script_dir / 'icon.svg'
    
    if not svg_path.exists():
        print(f"❌ Файл {svg_path} не найден")
        return
    
    print(f"📦 Генерация иконок из {svg_path}")
    
    for size in SIZES:
        png_path = script_dir / f'icon-{size}.png'
        
        try:
            # Конвертируем SVG в PNG
            png_data = cairosvg.svg2png(
                url=str(svg_path),
                output_width=size,
                output_height=size
            )
            
            # Сохраняем PNG
            with open(png_path, 'wb') as f:
                f.write(png_data)
            
            print(f"✅ Создан {png_path} ({size}x{size})")
            
        except Exception as e:
            print(f"❌ Ошибка при создании {png_path}: {e}")

if __name__ == '__main__':
    generate_icons()
    print("\n🎉 Готово! Все иконки созданы.")
