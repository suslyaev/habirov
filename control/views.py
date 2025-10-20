from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import PriceItem
import json

# Create your views here.

@csrf_exempt
@require_http_methods(["GET"])
def get_price_item_data(request):
    """API для получения данных прайсовой позиции по ID"""
    price_item_id = request.GET.get('id')
    
    if not price_item_id:
        return JsonResponse({'error': 'ID не указан'}, status=400)
    
    try:
        price_item = PriceItem.objects.get(id=price_item_id)
        return JsonResponse({
            'id': price_item.id,
            'name': price_item.name,
            'unit': price_item.unit,
            'price_per_unit': float(price_item.price_per_unit),
            'material': price_item.material.name if price_item.material else None,
            'work_type': price_item.work_type.name if price_item.work_type else None,
        })
    except PriceItem.DoesNotExist:
        return JsonResponse({'error': 'Позиция не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
