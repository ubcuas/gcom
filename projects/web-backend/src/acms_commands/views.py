"""Flight commands forwarded to the aircraft's GCSCommandsServer (ACMS) over HTTP.

ACMS validates each request and calls its flight_commander ROS services. Its answer is relayed
unchanged: {"success": bool, "message": str} with
  200 succeeded, 400 bad request body, 502 the service ran but reported failure,
  503 ACMS or its flight_commander unreachable, 504 no response in time.
"""

import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

CONNECT_TIMEOUT_S = 5.0
# Longer than ACMS's own 15 s service timeout, so its more specific 504 message wins.
READ_TIMEOUT_S = 20.0


def _result(success: bool, message: str, status: int) -> JsonResponse:
    return JsonResponse({"success": success, "message": message}, status=status)


def _forward(request, endpoint: str) -> JsonResponse:
    url = f"{settings.ACMS_COMMANDS_URL.rstrip('/')}/{endpoint}"
    try:
        response = requests.post(
            url,
            data=request.body or None,
            headers={"Content-Type": "application/json"},
            timeout=(CONNECT_TIMEOUT_S, READ_TIMEOUT_S),
        )
    except requests.Timeout:
        return _result(False, f"ACMS at {url} did not answer within {READ_TIMEOUT_S:.0f} s", 504)
    except requests.RequestException as e:
        return _result(False, f"cannot reach ACMS at {url}: {e}", 503)

    try:
        body = response.json()
        success, message = bool(body["success"]), str(body["message"])
    except (ValueError, KeyError, TypeError):
        return _result(False, f"unexpected reply from ACMS ({response.status_code}): {response.text[:200]}", 502)
    return _result(success, message, response.status_code)


@csrf_exempt
@require_POST
def prepare_takeoff(request):
    """{"altitude": metres}: upload a climb straight up from home. Does not arm or fly."""
    return _forward(request, "prepare_takeoff")


@csrf_exempt
@require_POST
def add_route(request):
    """{"waypoints": [{"latitude", "longitude", "altitude"?}, ...], "append": bool}: upload a route.

    append=false replaces the mission; append=true adds it after the current one (e.g. a takeoff).
    A missing altitude repeats the previous one. Other waypoint fields are ignored by ACMS.
    """
    return _forward(request, "add_route")


@csrf_exempt
@require_POST
def set_mode(request):
    """{"mode": "GUIDED" | "AUTO" | ...}: switch flight mode."""
    return _forward(request, "set_mode")


@csrf_exempt
@require_POST
def arm(request):
    """{"arm": true | false}: arm or disarm."""
    return _forward(request, "arm")


@csrf_exempt
@require_POST
def start_mission(request):
    """Start the uploaded mission. Needs the aircraft armed and in AUTO."""
    return _forward(request, "start_mission")


@csrf_exempt
@require_POST
def rtl(request):
    """Return to launch: fly home and land."""
    return _forward(request, "rtl")
