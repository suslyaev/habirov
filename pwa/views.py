from django.shortcuts import render
from django.views.decorators.cache import never_cache


@never_cache
def app_view(request):
    """Главная страница PWA приложения"""
    return render(request, 'pwa/app.html')


@never_cache
def manifest_view(request):
    """Манифест PWA"""
    from django.http import JsonResponse
    return JsonResponse({
        "name": "Хабиров Учет",
        "short_name": "Учет",
        "description": "Приложение для учета транзакций",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#007bff",
        "icons": [
            {
                "src": "/static/pwa/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/pwa/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/pwa/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/static/pwa/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any"
            }
        ]
    })


@never_cache
def service_worker_view(request):
    """Service Worker"""
    from django.http import HttpResponse
    from django.template import loader
    
    template = loader.get_template('pwa/sw.js')
    js_content = template.render({}, request)
    return HttpResponse(js_content, content_type='application/javascript')
