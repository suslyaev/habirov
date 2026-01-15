from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'objects', views.ObjectViewSet, basename='object')
router.register(r'stages', views.StageViewSet, basename='stage')
router.register(r'estimates', views.EstimateViewSet, basename='estimate')
router.register(r'estimate-items', views.EstimateItemViewSet, basename='estimateitem')
router.register(r'contractors', views.ContractorViewSet, basename='contractor')

urlpatterns = [
    # Авторизация
    path('auth/login/', views.login_view, name='api_login'),
    path('auth/logout/', views.logout_view, name='api_logout'),
    path('auth/me/', views.me_view, name='api_me'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # REST API
    path('', include(router.urls)),
]


