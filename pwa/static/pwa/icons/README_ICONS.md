# Генерация иконок для PWA

## Автоматическая генерация (Python)

1. Установите зависимости:
```bash
pip install cairosvg pillow
```

2. Запустите скрипт:
```bash
cd pwa/static/pwa/icons
python create_favicon.py
```

## Ручная генерация

### Вариант 1: Онлайн конвертер
1. Откройте файл `icon.svg` в браузере
2. Используйте онлайн конвертер: https://convertio.co/svg-png/
3. Сгенерируйте PNG файлы размеров: 16x16, 32x32, 192x192, 512x512
4. Сохраните как `icon-16.png`, `icon-32.png`, `icon-192.png`, `icon-512.png`

### Вариант 2: Inkscape (командная строка)
```bash
# Установите Inkscape
# macOS: brew install inkscape
# Linux: sudo apt-get install inkscape

inkscape icon.svg --export-filename=icon-16.png -w 16 -h 16
inkscape icon.svg --export-filename=icon-32.png -w 32 -h 32
inkscape icon.svg --export-filename=icon-192.png -w 192 -h 192
inkscape icon.svg --export-filename=icon-512.png -w 512 -h 512
```

### Вариант 3: ImageMagick
```bash
# Установите ImageMagick
# macOS: brew install imagemagick
# Linux: sudo apt-get install imagemagick

convert -background none icon.svg -resize 16x16 icon-16.png
convert -background none icon.svg -resize 32x32 icon-32.png
convert -background none icon.svg -resize 192x192 icon-192.png
convert -background none icon.svg -resize 512x512 icon-512.png
```

## Проверка

После генерации проверьте, что все файлы созданы:
- icon-16.png
- icon-32.png
- icon-192.png
- icon-512.png
