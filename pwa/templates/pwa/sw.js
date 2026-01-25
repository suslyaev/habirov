/**
 * Service Worker для PWA
 * Кэширование ресурсов для работы оффлайн
 */

const CACHE_NAME = 'habirov-v3'; // Обновлена версия для принудительного обновления кеша
const urlsToCache = [
    '/',
    '/static/pwa/css/app.css',
    '/static/pwa/js/db.js',
    '/static/pwa/js/api.js',
    '/static/pwa/js/sync.js',
    '/static/pwa/js/app.js',
    '/manifest.json',
    '/sw.js',
    '/static/pwa/icons/icon-192.png',
    '/static/pwa/icons/icon-512.png',
];

// Установка Service Worker
self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker: Установка');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('📦 Кэширование ресурсов');
                // Сначала кешируем статические ресурсы (они точно должны закешироваться)
                const staticResources = urlsToCache.filter(url => url.startsWith('/static/') || url === '/manifest.json' || url === '/sw.js');
                const mainPage = urlsToCache.filter(url => url === '/');
                
                return Promise.allSettled([
                    // Кешируем статические ресурсы
                    ...staticResources.map(url => 
                        cache.add(url).catch(err => {
                            console.warn(`⚠️ Не удалось закешировать ${url}:`, err);
                            return null;
                        })
                    ),
                    // Главную страницу кешируем отдельно, с обработкой ошибок
                    ...mainPage.map(url => 
                        fetch(url).then(response => {
                            if (response.ok) {
                                return cache.put(url, response);
                            }
                            throw new Error(`Failed to fetch ${url}: ${response.status}`);
                        }).catch(err => {
                            console.warn(`⚠️ Не удалось закешировать главную страницу ${url}:`, err);
                            // Не критично, она закешируется при первом запросе
                            return null;
                        })
                    )
                ]);
            })
            .then(() => {
                console.log('✅ Ресурсы закешированы');
                return self.skipWaiting(); // Активируем сразу
            })
            .catch(err => {
                console.error('❌ Ошибка при установке Service Worker:', err);
                // Все равно активируем Service Worker
                return self.skipWaiting();
            })
    );
});

// Активация Service Worker
self.addEventListener('activate', (event) => {
    console.log('✅ Service Worker: Активация');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('🗑️ Удаление старого кэша:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            // Немедленно берем контроль над всеми клиентами
            return self.clients.claim();
        })
    );
});

// Перехват запросов
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Не кэшируем API запросы - они идут через fetch с проверкой соединения
    if (url.pathname.startsWith('/api/')) {
        return; // Пропускаем, пусть обрабатывается обычным fetch
    }
    
    // Для статических ресурсов (CSS, JS) используем Cache First
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                
                // Если нет в кеше, пытаемся загрузить из сети
                return fetch(request).then((response) => {
                    // Клонируем для сохранения в кеш
                    const responseToCache = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseToCache);
                    });
                    return response;
                }).catch(() => {
                    // Если и сети нет, возвращаем пустой ответ
                    return new Response('Resource not available offline', {
                        status: 503,
                        headers: { 'Content-Type': 'text/plain' }
                    });
                });
            })
        );
        return;
    }
    
    // Для главной страницы используем Cache First (для работы офлайн)
    // Но также обновляем кеш в фоне при наличии сети
    if (url.pathname === '/' || url.pathname === '') {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                // Пытаемся загрузить из сети для обновления кеша (в фоне)
                const fetchPromise = fetch(request).then((response) => {
                    // Проверяем, что ответ валидный
                    if (response && response.status === 200 && response.type !== 'error') {
                        // Клонируем ответ для сохранения в кэш
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseToCache);
                            console.log('✅ Главная страница обновлена в кеше');
                        });
                    }
                    return response;
                }).catch(() => {
                    // Игнорируем ошибки сети
                    return null;
                });
                
                // Если есть закешированная версия, возвращаем её сразу (работает офлайн)
                if (cachedResponse) {
                    // Обновляем кеш в фоне, но не ждем
                    fetchPromise.catch(() => {});
                    return cachedResponse;
                }
                
                // Нет в кеше - ждем ответа из сети
                return fetchPromise.then((response) => {
                    if (response && response.status === 200) {
                        return response;
                    }
                    // Если не удалось загрузить, возвращаем базовую HTML страницу
                    throw new Error('Failed to fetch');
                }).catch(() => {
                    return new Response('<!DOCTYPE html><html><head><meta charset="utf-8"><title>Офлайн</title></head><body><h1>Приложение загружается...</h1><p>Пожалуйста, проверьте подключение к интернету.</p></body></html>', {
                        headers: { 'Content-Type': 'text/html; charset=utf-8' }
                    });
                });
            })
        );
        return;
    }
    
    // Для других HTML страниц используем Network First с fallback на Cache
    event.respondWith(
        fetch(request)
            .then((response) => {
                // Проверяем, что ответ валидный
                if (!response || response.status !== 200 || response.type === 'error') {
                    throw new Error('Invalid response');
                }
                
                // Клонируем ответ для сохранения в кэш
                const responseToCache = response.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(request, responseToCache);
                });
                
                return response;
            })
            .catch(() => {
                // Если сеть недоступна, берем из кэша
                return caches.match(request).then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    
                    return new Response('Resource not available offline', {
                        status: 503,
                        headers: { 'Content-Type': 'text/plain' }
                    });
                });
            })
    );
});

// Background Sync API (для синхронизации в фоне)
self.addEventListener('sync', (event) => {
    console.log('🔄 Background Sync:', event.tag);
    
    if (event.tag === 'sync-transactions') {
        event.waitUntil(
            // Здесь можно добавить логику синхронизации в фоне
            // Но мы используем периодическую синхронизацию в app.js
            Promise.resolve()
        );
    }
});


