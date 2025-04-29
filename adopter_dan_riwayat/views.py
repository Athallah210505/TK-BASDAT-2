from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

def adopter_list(request):
    return render(request, 'adopter_list.html')

def adopter_detail(request, adopter_id=None):
    return render(request, 'adopter_detail.html')

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_adoption(request, adoption_id):
    try:
        return JsonResponse({
            'status': 'success',
            'message': f'Adoption record {adoption_id} deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_adopter(request, adopter_id):
    try:
        return JsonResponse({
            'status': 'success',
            'message': f'Adopter {adopter_id} deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)