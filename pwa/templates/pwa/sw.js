/**
 * Service Worker для PWA
 * Кэширование ресурсов для работы оффлайн
 */

const CACHE_NAME = 'habirov-v2'; // Обновлена версия для принудительного обновления кеша
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
                // Используем addAll, но обрабатываем ошибки для каждого ресурса отдельно
                return Promise.allSettled(
                    urlsToCache.map(url => 
                        cache.add(url).catch(err => {
                            console.warn(`⚠️ Не удалось закешировать ${url}:`, err);
                            return null;
                        })
                    )
                );
            })
            .then(() => {
                console.log('✅ Все ресурсы закешированы');
                return self.skipWaiting(); // Активируем сразу
            })
            .catch(err => {
                console.error('❌ Ошибка при установке Service Worker:', err);
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
    
    // Для главной страницы и других HTML используем Network First с fallback на Cache
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
                    
                    // Если в кэше нет главной страницы, пытаемся вернуть кешированную версию
                    if (request.url.endsWith('/') || request.url.includes('/')) {
                        return caches.match('/').then((indexResponse) => {
                            if (indexResponse) {
                                return indexResponse;
                            }
                            // Последний fallback
                            return new Response('Офлайн режим. Приложение будет доступно после восстановления соединения.', {
                                headers: { 'Content-Type': 'text/html; charset=utf-8' }
                            });
                        });
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


