/**
 * Service Worker для PWA
 * Кэширование ресурсов для работы оффлайн
 */

const CACHE_NAME = 'habirov-v1';
const urlsToCache = [
    '/',
    '/static/pwa/css/app.css',
    '/static/pwa/js/db.js',
    '/static/pwa/js/api.js',
    '/static/pwa/js/sync.js',
    '/static/pwa/js/app.js',
    '/manifest.json',
];

// Установка Service Worker
self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker: Установка');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('📦 Кэширование ресурсов');
                return cache.addAll(urlsToCache);
            })
            .then(() => self.skipWaiting())
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
        }).then(() => self.clients.claim())
    );
});

// Перехват запросов
self.addEventListener('fetch', (event) => {
    const { request } = event;
    
    // Не кэшируем API запросы - они идут через fetch с проверкой соединения
    if (request.url.includes('/api/')) {
        return; // Пропускаем, пусть обрабатывается обычным fetch
    }
    
    // Стратегия: Network First, Fallback to Cache
    event.respondWith(
        fetch(request)
            .then((response) => {
                // Клонируем ответ для сохранения в кэш
                const responseToCache = response.clone();
                
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(request, responseToCache);
                });
                
                return response;
            })
            .catch(() => {
                // Если сеть недоступна, берем из кэша
                return caches.match(request).then((response) => {
                    if (response) {
                        return response;
                    }
                    
                    // Если в кэше нет, возвращаем офлайн страницу (опционально)
                    return new Response('Офлайн режим', {
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


