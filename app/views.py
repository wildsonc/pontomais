from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.http import JsonResponse

from .tasks import *


@api_view(['POST', 'GET'])
@csrf_exempt
def update(request):
    update_shift()
    update_departments()
    update_employees()
    return JsonResponse({"status": "OK"})


@api_view(['POST', 'GET'])
@csrf_exempt
def journey(request, date=None):
    days = request.query_params.get('days')
    if date:
        update_journey(date)
    elif days:
        bulk_update_journey(int(days))
    else:
        update_journey()
    return JsonResponse({"status": "OK"})
