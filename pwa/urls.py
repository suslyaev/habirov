from django.urls import path
from . import views

app_name = 'pwa'

urlpatterns = [
    path('', views.app_view, name='app'),
    path('manifest.json', views.manifest_view, name='manifest'),
    path('sw.js', views.service_worker_view, name='service_worker'),
]


