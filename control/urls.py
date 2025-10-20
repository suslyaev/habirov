from django.urls import path
from . import views

urlpatterns = [
    path('price-item-data/', views.get_price_item_data, name='price_item_data'),
]

