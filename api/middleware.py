"""
Middleware для отключения CSRF проверки для API endpoints
"""


class DisableCSRFForAPI:
    """
    Middleware для отключения CSRF проверки для всех запросов к /api/
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Отключаем CSRF проверку для всех запросов к API
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return self.get_response(request)
