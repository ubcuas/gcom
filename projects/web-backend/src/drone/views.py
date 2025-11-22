from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from .mps_api import DroneApiClient


@require_http_methods(["GET"])
def get_current_status(request):
    response = DroneApiClient.get_current_status()
    return JsonResponse(response.json(), safe=False, status=response.status_code)


@require_http_methods(["GET"])
def get_status_history(request):
    response = DroneApiClient.get_status_history()
    return JsonResponse(response.json(), safe=False, status=response.status_code)


@csrf_exempt
@require_http_methods(["POST"])
def takeoff(request):
    try:
        data = json.loads(request.body)
        altitude = data.get("altitude")
        response = DroneApiClient.takeoff(altitude)
        return HttpResponse(status=response.status_code)
    except (KeyError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid input"}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def arm(request):
    try:
        data = json.loads(request.body)
        arm_value = data.get("arm")
        response = DroneApiClient.arm(arm_value)
        return HttpResponse(status=response.status_code)
    except (KeyError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid input"}, status=400)


@require_http_methods(["GET"])
def land(request):
    response = DroneApiClient.land()
    return HttpResponse(status=response.status_code)


@require_http_methods(["GET"])
def get_rtl(request):
    response = DroneApiClient.get_rtl()
    return JsonResponse(response.json(), status=response.status_code)


@csrf_exempt
@require_http_methods(["POST"])
def post_rtl(request):
    try:
        data = json.loads(request.body)
        altitude = data.get("altitude")
        response = DroneApiClient.post_rtl(altitude)
        return HttpResponse(status=response.status_code)
    except (KeyError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid input"}, status=400)


@require_http_methods(["GET"])
def lock(request):
    response = DroneApiClient.lock()
    return HttpResponse(status=response.status_code)


@require_http_methods(["GET"])
def unlock(request):
    response = DroneApiClient.unlock()
    return HttpResponse(status=response.status_code)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def queue(request):
    if request.method == "GET":
        response = DroneApiClient.get_queue()
        return JsonResponse(response.json(), safe=False, status=response.status_code)
    elif request.method == "POST":
        try:
            waypoints = json.loads(request.body)

            # Transform waypoints to mission-planner format
            transformed_waypoints = []
            for wp in waypoints:
                transformed_wp = wp.copy()
                # Map ardupilot_param2/3 to param2/3 for mission-planner
                # We ignore param1 and param4 as they are not used
                transformed_wp['param1'] = 0
                param2 = wp.get('ardupilot_param2', 0) 
                param3 = wp.get('ardupilot_param3', 0)
                transformed_wp['param2'] = param2 if param2 != None else 0
                transformed_wp['param3'] = param3 if param3 != None else 0
                transformed_wp['param4'] = 0
                # Remove the ardupilot_param fields
                transformed_wp.pop('ardupilot_param2', None)
                transformed_wp.pop('ardupilot_param3', None)
                transformed_waypoints.append(transformed_wp)

            response = DroneApiClient.post_queue(transformed_waypoints)

            if response.status_code >= 400:
                print(f"[ERROR] Queue POST failed with status {response.status_code}")
                print(f"[ERROR] Mission-planner response: {response.text}")
                return JsonResponse(
                    {"error": "Mission-planner error", "details": response.text},
                    status=response.status_code
                )

            return HttpResponse(status=response.status_code)
        except (KeyError, ValueError, TypeError) as e:
            print(f"[ERROR] Invalid input for queue POST: {type(e).__name__}: {str(e)}")
            return JsonResponse({"error": "Invalid input"}, status=400)
        except Exception as e:
            print(f"[ERROR] Unexpected error in queue POST: {type(e).__name__}: {str(e)}")
            return JsonResponse(
                {"error": "Internal server error", "details": str(e)},
                status=500
            )


@csrf_exempt
@require_http_methods(["POST"])
def post_home(request):
    try:
        wp = json.loads(request.body)
        response = DroneApiClient.post_home(wp)
        return HttpResponse(status=response.status_code)
    except (KeyError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid input"}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def insert(request):
    try:
        queue = json.loads(request.body)

        # Transform waypoints to mission-planner format
        transformed_queue = []
        for wp in queue:
            transformed_wp = wp.copy()
            # Map ardupilot_param2/3 to param2/3 for mission-planner
            transformed_wp['param1'] = 0
            transformed_wp['param2'] = wp.get('ardupilot_param2', 0)
            transformed_wp['param3'] = wp.get('ardupilot_param3', 0)
            transformed_wp['param4'] = 0
            # Remove the ardupilot_param fields
            transformed_wp.pop('ardupilot_param2', None)
            transformed_wp.pop('ardupilot_param3', None)
            transformed_queue.append(transformed_wp)

        response = DroneApiClient.insert(transformed_queue)
        return HttpResponse(status=response.status_code)
    except (KeyError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid input"}, status=400)


@require_http_methods(["GET"])
def clear(request):
    response = DroneApiClient.clear()
    return HttpResponse(status=response.status_code)


@require_http_methods(["POST"])
def diversion(request):
    try:
        data = json.loads(request.body)
        exclude_wps = data.get("exclude")
        rejoin_wp = data.get("rejoin_at")
        response = DroneApiClient.diversion(exclude_wps, rejoin_wp)
        return HttpResponse(status=response.status_code)
    except (KeyError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid input"}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def flightmode(request):
    try:
        data = json.loads(request.body)
        mode = data.get("mode")
        response = DroneApiClient.flightmode(mode)
        return HttpResponse(status=response.status_code)
    except (KeyError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid input"}, status=400)
