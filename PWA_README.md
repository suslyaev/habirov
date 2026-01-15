# 📱 PWA Приложение "Хабиров Учет"

## 🎉 Готово к использованию!

### Что реализовано:

✅ **Авторизация** - телефон + пароль  
✅ **Работа оффлайн** - приложение работает без интернета  
✅ **Создание транзакций** - даже без связи  
✅ **Автоматическая синхронизация** - каждые 30 секунд  
✅ **Индикация статуса** - видно какие транзакции синхронизированы  
✅ **PWA** - можно установить на iPhone/Android как приложение  

---

## 🚀 Как запустить:

### Локально:

```bash
cd /Users/alex/Documents/distr/habirov
source env/bin/activate
python manage.py runserver 4000
```

Откройте в браузере: **http://localhost:4000/**

### На сервере:

После деплоя откройте: **https://iphabirov.ru/**

---

## 📲 Установка на iPhone:

1. Откройте https://iphabirov.ru/ в Safari
2. Нажмите кнопку "Поделиться" (квадрат со стрелкой)
3. Выберите "На экран «Домой»"
4. Готово! Иконка появится на рабочем столе

## 📲 Установка на Android:

1. Откройте https://iphabirov.ru/ в Chrome
2. Нажмите меню (три точки)
3. Выберите "Установить приложение"
4. Готово!

---

## 🔐 Тестовый аккаунт:

- **Телефон:** +70000000000
- **Пароль:** admin

---

## 💡 Как это работает:

### Онлайн режим:
1. Авторизуетесь по телефону/паролю
2. Получаете JWT токен (хранится 7 дней)
3. Создаете транзакции → сразу отправляются на сервер
4. Видите все транзакции из базы

### Оффлайн режим:
1. Теряете связь → появляется желтый баннер "⚠️ Оффлайн"
2. Создаете транзакции → сохраняются локально в IndexedDB
3. Помечаются как 🟡 "Не синхронизировано"
4. При восстановлении связи → автоматически отправляются на сервер
5. Меняют статус на 🟢 "Синхронизировано"

---

## 📁 Структура проекта:

```
habirov/
├── api/                          # REST API
│   ├── serializers.py           # Сериализаторы данных
│   ├── views.py                 # API endpoints
│   └── urls.py                  # API роуты
│
├── pwa/                          # PWA приложение
│   ├── static/pwa/
│   │   ├── css/
│   │   │   └── app.css         # Стили приложения
│   │   ├── js/
│   │   │   ├── app.js          # Главный модуль
│   │   │   ├── api.js          # API клиент
│   │   │   ├── db.js           # IndexedDB
│   │   │   └── sync.js         # Синхронизация
│   │   └── icons/
│   │       ├── icon-192.png    # Иконка 192x192
│   │       └── icon-512.png    # Иконка 512x512
│   ├── templates/pwa/
│   │   ├── app.html            # HTML приложения
│   │   └── sw.js               # Service Worker
│   ├── views.py
│   └── urls.py
```

---

## 🔧 API Endpoints:

### Авторизация:
- `POST /api/auth/login/` - вход (phone, password)
- `POST /api/auth/logout/` - выход
- `GET /api/auth/me/` - текущий пользователь
- `POST /api/auth/refresh/` - обновить токен

### Транзакции:
- `GET /api/transactions/` - список транзакций
- `POST /api/transactions/` - создать транзакцию
- `GET /api/transactions/{id}/` - получить транзакцию
- `PUT/PATCH /api/transactions/{id}/` - обновить транзакцию

### Справочники (только чтение):
- `GET /api/categories/` - категории
- `GET /api/projects/` - проекты
- `GET /api/stages/` - этапы
- `GET /api/estimates/` - сметы
- `GET /api/contractors/` - контрагенты

---

## 🎨 Настройка иконок:

Текущие иконки - временные заглушки (синий квадрат).

### Как заменить на свои:

**Вариант 1:** Откройте в браузере:
```
file:///Users/alex/Documents/distr/habirov/pwa/static/pwa/icons/create_icons.html
```

**Вариант 2:** Используйте готовые PNG (192x192 и 512x512):
```bash
cp your-icon-192.png pwa/static/pwa/icons/icon-192.png
cp your-icon-512.png pwa/static/pwa/icons/icon-512.png
```

**Вариант 3:** Конвертируйте SVG:
```bash
cd pwa/static/pwa/icons/
convert icon.svg -resize 192x192 icon-192.png
convert icon.svg -resize 512x512 icon-512.png
```

---

## 🔄 Синхронизация:

- **Автоматически** каждые 30 секунд
- **Вручную** - кнопка 🔄 в шапке приложения
- **При восстановлении связи** - автоматически

---

## 🐛 Отладка:

### Просмотр локальных данных:
В браузере откройте DevTools → Application → IndexedDB → HabirovDB

### Просмотр Service Worker:
DevTools → Application → Service Workers

### Проверка кэша:
DevTools → Application → Cache Storage → habirov-v1

### Логи:
- API: DevTools → Console
- Service Worker: DevTools → Console (с фильтром Service Worker)

---

## 📦 Деплой на сервер:

1. Загрузите код на сервер
2. Установите зависимости: `pip install -r requirements.txt`
3. Примените миграции: `python manage.py migrate`
4. Соберите статику: `python manage.py collectstatic`
5. Перезапустите Gunicorn: `sudo systemctl restart habirov`

---

## 🎯 Готово!

Приложение полностью функционально и готово к использованию!

**Откройте:** http://localhost:4000/  
**Логин:** +70000000000  
**Пароль:** admin


