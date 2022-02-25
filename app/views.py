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
def teste(request):
    print('teste')
    update_extra_time()
    return JsonResponse({"status": "OK"})
