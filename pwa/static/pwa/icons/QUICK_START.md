# Быстрая генерация иконок

## Самый простой способ (рекомендуется):

1. **Откройте файл `create_icons_browser.html` в браузере**
   - Просто дважды кликните на файл или откройте через браузер
   - Или перейдите по адресу: `http://ваш-сервер/static/pwa/icons/create_icons_browser.html`

2. **Нажмите кнопку "Сгенерировать все иконки"** (или они сгенерируются автоматически)

3. **Скачайте каждую иконку** (кнопка "📥 Скачать" под каждой иконкой)

4. **Сохраните файлы** в папку `pwa/static/pwa/icons/`:
   - `icon-16.png`
   - `icon-32.png`
   - `icon-192.png`
   - `icon-512.png`

Готово! 🎉

---

## Альтернативные способы:

### Способ 2: Установить системные зависимости для Python скрипта

На сервере (Linux):
```bash
sudo apt-get update
sudo apt-get install libcairo2-dev libgdk-pixbuf2.0-dev libpango1.0-dev
cd pwa/static/pwa/icons
python3 create_favicon.py
```

На macOS:
```bash
brew install cairo
cd pwa/static/pwa/icons
python3 create_favicon.py
```

### Способ 3: Онлайн конвертер

1. Откройте `icon.svg` в браузере
2. Используйте онлайн конвертер: https://convertio.co/svg-png/
3. Загрузите SVG и сгенерируйте PNG размеров: 16, 32, 192, 512
4. Сохраните как `icon-16.png`, `icon-32.png`, `icon-192.png`, `icon-512.png`
