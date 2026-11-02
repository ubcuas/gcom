"""HTTP endpoints that forward flight commands to ACMS's flight_commander services via rosbridge.

Every endpoint answers {"success": bool, "message": str}:
  200 the service succeeded, 502 the service ran but reported failure,
  503 rosbridge unreachable or the call errored, 504 no response in time.
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .client import RosbridgeError, RosbridgeTimeout, get_client

SERVICE_PREFIX = "/flight_commander"


async def _call(service: str, args: dict | None = None) -> JsonResponse:
    try:
        values = await get_client().call_service(f"{SERVICE_PREFIX}/{service}", args)
    except RosbridgeTimeout as e:
        return JsonResponse({"success": False, "message": str(e)}, status=504)
    except RosbridgeError as e:
        return JsonResponse({"success": False, "message": str(e)}, status=503)
    success = bool(values.get("success", False))
    return JsonResponse(
        {"success": success, "message": values.get("message", "")},
        status=200 if success else 502,
    )


def _body(request) -> dict:
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _bad_request(message: str) -> JsonResponse:
    return JsonResponse({"success": False, "message": message}, status=400)


@csrf_exempt
@require_POST
async def prepare_takeoff(request):
    """Upload a mission that climbs straight up from home to `altitude` metres. Does not arm or fly."""
    altitude = _body(request).get("altitude")
    if not isinstance(altitude, (int, float)) or isinstance(altitude, bool) or altitude <= 0:
        return _bad_request("altitude must be a number > 0")
    return await _call("takeoff", {"takeoff_altitude": float(altitude), "waypoints": []})


@csrf_exempt
@require_POST
async def set_mode(request):
    """Switch flight mode by name, e.g. GUIDED, AUTO, LOITER."""
    mode = _body(request).get("mode")
    if not isinstance(mode, str) or not mode.strip():
        return _bad_request("mode must be a non-empty string")
    return await _call("set_mode", {"mode": mode.strip().upper()})


@csrf_exempt
@require_POST
async def arm(request):
    """`arm: true` arms, `arm: false` disarms."""
    value = _body(request).get("arm")
    if not isinstance(value, bool):
        return _bad_request("arm must be true or false")
    return await _call("arm", {"data": value})


@csrf_exempt
@require_POST
async def start_mission(request):
    """Start the uploaded mission. Needs the aircraft armed and in AUTO."""
    return await _call("start_mission")


@csrf_exempt
@require_POST
async def rtl(request):
    """Return to launch: fly home and land."""
    return await _call("land")
