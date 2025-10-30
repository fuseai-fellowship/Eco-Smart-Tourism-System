from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .model_loader import model_manager

@csrf_exempt
def travel_predict(request):
    if request.method == 'POST':
        if not model_manager.travel_model:
            return JsonResponse({'status': 'error', 'message': 'Travel model not loaded'}, status=500)
        
        try:
            data = json.loads(request.body)
            user_input = data.get('user_input', '')
            
            # Generate itinerary using the .pkl model
            itinerary = model_manager.travel_model.generate_itinerary(user_input)
            
            return JsonResponse({
                'status': 'success',
                'itinerary': itinerary,
                'message': 'Travel itinerary generated successfully'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'POST request required'}, status=405)
