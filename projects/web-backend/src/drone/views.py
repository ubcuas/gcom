import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from drf_spectacular.utils import OpenApiResponse, extend_schema

from .mps_api import DroneApiClient


@extend_schema(
    summary="Get current drone status",
    description="Retrieves the current status of the drone including position, altitude, battery level, flight mode, and other telemetry data. This endpoint returns cached data from the mission planner's status cache, updated continuously via MAVLink.",
    responses={
        200: OpenApiResponse(description="Current drone status data"),
        400: OpenApiResponse(
            description="Failed to retrieve status from mission planner"
        ),
    },
    tags=["Drone Status"],
)
@require_http_methods(["GET"])
def get_current_status(request):
    response = DroneApiClient.get_current_status()
    return JsonResponse(response.json(), safe=False, status=response.status_code)


@extend_schema(
    summary="Get drone status history",
    description="Retrieves historical status data for the drone. Returns a time-series of drone telemetry including position, altitude, and other status information over time.",
    responses={
        200: OpenApiResponse(description="Array of historical status data points"),
        400: OpenApiResponse(
            description="Failed to retrieve status history from mission planner"
        ),
    },
    tags=["Drone Status"],
)
@require_http_methods(["GET"])
def get_status_history(request):
    response = DroneApiClient.get_status_history()
    return JsonResponse(response.json(), safe=False, status=response.status_code)


@extend_schema(
    summary="Prepare drone for takeoff",
    description=(
        "Prepares the drone for autonomous takeoff by creating a single TAKEOFF waypoint at the drone's current position. "
        "The waypoint is uploaded to the drone and becomes active when the drone is armed and switched to AUTO flight mode.\n\n"
        "**Altitude Units:** Meters (relative to home position)\n\n"
        "**Side Effects:**\n"
        "- Clears any existing mission on the drone\n"
        "- Uploads a new mission with a single TAKEOFF waypoint\n"
        "- Sets the AUTO_OPTIONS parameter to value 3\n"
        "- Uses the drone's current GPS position as the takeoff location\n\n"
        "**Returns:** The takeoff waypoint that was created"
    ),
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "altitude": {
                    "type": "number",
                    "description": "Target takeoff altitude in meters (relative to home position)",
                    "example": 25.0,
                }
            },
            "required": ["altitude"],
        }
    },
    responses={
        200: OpenApiResponse(
            description="Takeoff waypoint created successfully. Returns the takeoff waypoint object."
        ),
        400: OpenApiResponse(
            description="Invalid input (missing altitude) or mission planner error"
        ),
        500: OpenApiResponse(
            description="Internal server error during takeoff preparation"
        ),
    },
    tags=["Mission Planning"],
)
@csrf_exempt
@require_http_methods(["POST"])
def prepare_takeoff(request):
    try:
        data = json.loads(request.body)
        altitude = data.get("altitude")
        response = DroneApiClient.prepare_takeoff(altitude)

        # get current position from the drone status queue
        status = DroneApiClient.get_queue()

        if response.status_code >= 400:
            print(f"[ERROR] Mission-planner response: {response.text}")
            return JsonResponse(
                {"error": "Mission-planner error", "details": response.text},
                status=response.status_code,
            )
        # return first element of the queue as the takeoff waypoint
        takeoff_wp = status.json()[0]
        return JsonResponse(takeoff_wp, status=200)

        # return HttpResponse(status=response.status_code)
    except (KeyError, ValueError, TypeError) as e:
        print(
            f"[ERROR] Invalid input for prepare_takeoff: {type(e).__name__}: {str(e)}"
        )
        return JsonResponse({"error": "Invalid input"}, status=400)
    except Exception as e:
        print(
            f"[ERROR] Unexpected error in prepare_takeoff: {type(e).__name__}: {str(e)}"
        )
        return JsonResponse(
            {"error": "Internal server error", "details": str(e)},
            status=500,
        )


@extend_schema(
    summary="Configure Return-to-Launch (RTL) altitude parameter",
    description=(
        "Sets the RTL_ALT parameter on the drone, which controls the altitude the drone will fly at when executing a Return-to-Launch command. "
        "This parameter must be configured before executing RTL via the /rtl endpoint.\n\n"
        "**Altitude Units:** Meters (will be converted to centimeters internally for MAVLink protocol)\n\n"
        "**What is RTL?** Return-to-Launch is a flight mode that commands the drone to fly back to its home position at the specified altitude and land automatically.\n\n"
        "**Side Effects:**\n"
        "- Modifies the drone's RTL_ALT parameter (persists until changed)\n"
        "- Does NOT trigger RTL mode or any movement\n"
        "- Parameter change is confirmed by the drone before returning success"
    ),
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "altitude": {
                    "type": "number",
                    "description": "RTL return altitude in meters (relative to home position)",
                    "example": 50.0,
                }
            },
            "required": ["altitude"],
        }
    },
    responses={
        200: OpenApiResponse(description="RTL altitude parameter set successfully"),
        400: OpenApiResponse(
            description="Invalid input (missing altitude) or drone failed to confirm parameter change"
        ),
        500: OpenApiResponse(
            description="Internal server error during parameter configuration"
        ),
    },
    tags=["Mission Planning"],
)
@csrf_exempt
@require_http_methods(["POST"])
def prepare_rtl_params(request):
    try:
        data = json.loads(request.body)
        altitude = data.get("altitude")
        response = DroneApiClient.prepare_rtl_params(altitude)

        if response.status_code >= 400:
            print(f"[ERROR] Mission-planner response: {response.text}")
            return JsonResponse(
                {"error": "Mission-planner error", "details": response.text},
                status=response.status_code,
            )

        return HttpResponse(status=response.status_code)
    except (KeyError, ValueError, TypeError) as e:
        print(
            f"[ERROR] Invalid input for prepare_rtl_params: {type(e).__name__}: {str(e)}"
        )
        return JsonResponse({"error": "Invalid input"}, status=400)
    except Exception as e:
        print(
            f"[ERROR] Unexpected error in prepare_rtl_params: {type(e).__name__}: {str(e)}"
        )
        return JsonResponse(
            {"error": "Internal server error", "details": str(e)},
            status=500,
        )


@extend_schema(
    summary="Arm or disarm the drone",
    description=(
        "Arms or disarms the drone's motors. When armed, the drone is ready to take off (motors spinning). "
        "When disarmed, the motors are stopped and the drone cannot fly.\n\n"
        "**Safety Note:** Only arm the drone when ready for flight and in a safe environment."
    ),
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "arm": {
                    "type": "boolean",
                    "description": "true to arm the drone, false to disarm",
                    "example": True,
                }
            },
            "required": ["arm"],
        }
    },
    responses={
        200: OpenApiResponse(description="Arm/disarm command sent successfully"),
        400: OpenApiResponse(description="Invalid input or mission planner error"),
    },
    tags=["Drone Control"],
)
@csrf_exempt
@require_http_methods(["PUT"])
def arm(request):
    try:
        data = json.loads(request.body)
        arm_value = data.get("arm")
        response = DroneApiClient.arm(arm_value)
        return HttpResponse(status=response.status_code)
    except (KeyError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid input"}, status=400)


@extend_schema(
    summary="Initiate drone landing",
    description=(
        "Commands the drone to begin landing at its current position. "
        "The drone will descend vertically and land immediately."
    ),
    responses={
        200: OpenApiResponse(description="Land command sent successfully"),
        400: OpenApiResponse(description="Mission planner error"),
    },
    tags=["Drone Control"],
)
@require_http_methods(["GET"])
def land(request):
    response = DroneApiClient.land()
    return HttpResponse(status=response.status_code)


@extend_schema(
    summary="Execute Return-to-Launch (RTL)",
    description=(
        "Initiates Return-to-Launch mode, commanding the drone to fly back to its home position and land. "
        "The drone will climb/descend to the altitude specified by the RTL_ALT parameter (configured via /prepare_rtl_params), "
        "fly to the home position, and then land automatically.\n\n"
        "**Prerequisites:** RTL altitude should be configured via /prepare_rtl_params endpoint first.\n\n"
        "**Note:** This is an immediate command that executes right away."
    ),
    responses={
        200: OpenApiResponse(description="RTL mode activated successfully"),
        400: OpenApiResponse(description="Invalid input or mission planner error"),
    },
    tags=["Drone Control"],
)
@csrf_exempt
@require_http_methods(["POST"])
def post_rtl(request):
    try:
        response = DroneApiClient.post_rtl()
        return HttpResponse(status=response.status_code)
    except (KeyError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid input"}, status=400)


@extend_schema(
    summary="Lock mission queue",
    description=(
        "Locks the mission queue to prevent modifications during critical operations. "
        "**Note:** This endpoint is currently not implemented in the mission planner and may return an error."
    ),
    responses={
        200: OpenApiResponse(description="Lock command sent successfully"),
        400: OpenApiResponse(description="Mission planner error"),
        404: OpenApiResponse(description="Endpoint not implemented in mission planner"),
    },
    tags=["Mission Planning"],
)
@require_http_methods(["GET"])
def lock(request):
    response = DroneApiClient.lock()
    return HttpResponse(status=response.status_code)


@extend_schema(
    summary="Unlock mission queue",
    description=(
        "Unlocks the mission queue to allow modifications after being locked. "
        "**Note:** This endpoint is currently not implemented in the mission planner and may return an error."
    ),
    responses={
        200: OpenApiResponse(description="Unlock command sent successfully"),
        400: OpenApiResponse(description="Mission planner error"),
        404: OpenApiResponse(description="Endpoint not implemented in mission planner"),
    },
    tags=["Mission Planning"],
)
@require_http_methods(["GET"])
def unlock(request):
    response = DroneApiClient.unlock()
    return HttpResponse(status=response.status_code)


@extend_schema(
    summary="Get or replace mission waypoint queue",
    description=(
        "**GET:** Retrieves the remaining mission waypoints starting from the drone's current waypoint index. "
        "Returns an array of waypoint objects with position data and command parameters.\n\n"
        "**POST:** Completely replaces the drone's entire mission with a new waypoint queue. "
        "Clears the existing mission and uploads all provided waypoints to the drone.\n\n"
        "**Altitude Units:** Meters (relative to home position)\n\n"
        "**POST Side Effects:**\n"
        "- Clears all existing waypoints on the drone\n"
        "- Uploads new waypoints to drone's onboard memory\n"
        "- Resets waypoint index (typically to 0/home)\n"
        "- Mission becomes active immediately\n\n"
        "**Waypoint Format:** Each waypoint includes id, name, latitude (degrees), longitude (degrees), "
        "altitude (meters), command type, and command parameters (param1-4)."
    ),
    request={
        "application/json": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 0},
                    "name": {"type": "string", "example": "Waypoint 1"},
                    "latitude": {
                        "type": "number",
                        "description": "Latitude in decimal degrees",
                        "example": 49.2606,
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude in decimal degrees",
                        "example": -123.2460,
                    },
                    "altitude": {
                        "type": "number",
                        "description": "Altitude in meters (relative to home)",
                        "example": 50.0,
                    },
                    "command": {
                        "type": "string",
                        "description": "MAVLink command type (defaults to WAYPOINT)",
                        "example": "WAYPOINT",
                    },
                    "param1": {
                        "type": "number",
                        "description": "Command parameter 1 (defaults to 0)",
                        "example": 0,
                    },
                    "param2": {
                        "type": "number",
                        "description": "Command parameter 2 (defaults to 0)",
                        "example": 0,
                    },
                    "param3": {
                        "type": "number",
                        "description": "Command parameter 3 (defaults to 0)",
                        "example": 0,
                    },
                    "param4": {
                        "type": "number",
                        "description": "Command parameter 4 (defaults to 0)",
                        "example": 0,
                    },
                },
                "required": ["id", "name", "latitude", "longitude"],
            },
        }
    },
    responses={
        200: OpenApiResponse(
            description="GET: Array of remaining waypoints. POST: Mission uploaded successfully."
        ),
        400: OpenApiResponse(description="Invalid input or mission planner error"),
        500: OpenApiResponse(
            description="Internal server error during queue operation"
        ),
    },
    tags=["Mission Planning"],
)
@csrf_exempt
@require_http_methods(["GET", "POST"])
def queue(request):
    if request.method == "GET":
        response = DroneApiClient.get_queue()
        return JsonResponse(response.json(), safe=False, status=response.status_code)
    elif request.method == "POST":
        try:
            waypoints = json.loads(request.body)
            response = DroneApiClient.post_queue(waypoints)

            if response.status_code >= 400:
                print(f"[ERROR] Queue POST failed with status {response.status_code}")
                print(f"[ERROR] Mission-planner response: {response.text}")
                return JsonResponse(
                    {"error": "Mission-planner error", "details": response.text},
                    status=response.status_code,
                )

            return HttpResponse(status=response.status_code)
        except (KeyError, ValueError, TypeError) as e:
            print(f"[ERROR] Invalid input for queue POST: {type(e).__name__}: {str(e)}")
            return JsonResponse({"error": "Invalid input"}, status=400)
        except Exception as e:
            print(
                f"[ERROR] Unexpected error in queue POST: {type(e).__name__}: {str(e)}"
            )
            return JsonResponse(
                {"error": "Internal server error", "details": str(e)}, status=500
            )


@extend_schema(
    summary="Set drone home position",
    description=(
        "Sets the home position for the drone. The home position is the reference point for Return-to-Launch (RTL) operations "
        "and serves as the altitude zero reference. The drone will return to this location when RTL is executed.\n\n"
        "**Altitude Units:** Meters (absolute altitude or relative to ground level depending on drone configuration)"
    ),
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "number",
                    "description": "Home latitude in decimal degrees",
                    "example": 49.2606,
                },
                "longitude": {
                    "type": "number",
                    "description": "Home longitude in decimal degrees",
                    "example": -123.2460,
                },
                "altitude": {
                    "type": "number",
                    "description": "Home altitude in meters",
                    "example": 100.0,
                },
            },
            "required": ["latitude", "longitude", "altitude"],
        }
    },
    responses={
        200: OpenApiResponse(description="Home position set successfully"),
        400: OpenApiResponse(description="Invalid input or mission planner error"),
    },
    tags=["Mission Planning"],
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


@extend_schema(
    summary="Insert waypoints into current mission",
    description=(
        "Inserts new waypoints into the mission queue immediately before the drone's current waypoint position. "
        "This allows for mid-flight mission adjustments without replacing the entire queue.\n\n"
        "**Difference from POST /queue:** This endpoint preserves the remaining waypoints after the insertion point, "
        "while POST /queue completely replaces the entire mission.\n\n"
        "**Altitude Units:** Meters (relative to home position). If not specified, uses the drone's current altitude as default.\n\n"
        "**Side Effects:**\n"
        "- New waypoints are inserted before the current waypoint index (minimum index 1)\n"
        "- All remaining waypoints after current position are preserved\n"
        "- Entire mission (new + remaining) is re-uploaded to the drone\n"
        "- Drone continues with updated mission if in AUTO mode\n\n"
        "**Use Case:** Mid-flight course corrections and mission modifications without aborting the current flight."
    ),
    request={
        "application/json": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 0},
                    "name": {"type": "string", "example": "New Waypoint"},
                    "latitude": {
                        "type": "number",
                        "description": "Latitude in decimal degrees",
                        "example": 49.2606,
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude in decimal degrees",
                        "example": -123.2460,
                    },
                    "altitude": {
                        "type": "number",
                        "description": "Altitude in meters (defaults to current altitude)",
                        "example": 50.0,
                    },
                    "command": {
                        "type": "string",
                        "description": "MAVLink command type (defaults to WAYPOINT)",
                        "example": "WAYPOINT",
                    },
                    "param1": {
                        "type": "number",
                        "description": "Command parameter 1 (defaults to 0)",
                        "example": 0,
                    },
                    "param2": {
                        "type": "number",
                        "description": "Command parameter 2 (defaults to 0)",
                        "example": 0,
                    },
                    "param3": {
                        "type": "number",
                        "description": "Command parameter 3 (defaults to 0)",
                        "example": 0,
                    },
                    "param4": {
                        "type": "number",
                        "description": "Command parameter 4 (defaults to 0)",
                        "example": 0,
                    },
                },
                "required": ["id", "name", "latitude", "longitude"],
            },
        }
    },
    responses={
        200: OpenApiResponse(description="Waypoints inserted successfully"),
        400: OpenApiResponse(description="Invalid input or mission planner error"),
    },
    tags=["Mission Planning"],
)
@csrf_exempt
@require_http_methods(["POST"])
def insert(request):
    try:
        queue = json.loads(request.body)
        response = DroneApiClient.insert(queue)
        return HttpResponse(status=response.status_code)
    except (KeyError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid input"}, status=400)


@extend_schema(
    summary="Clear mission waypoint queue",
    description=(
        "Clears all waypoints from the drone's mission queue. The drone will have no active mission after this operation.\n\n"
        "**Warning:** This removes all waypoints including the home position. Use with caution."
    ),
    responses={
        200: OpenApiResponse(description="Mission queue cleared successfully"),
        400: OpenApiResponse(description="Mission planner error"),
    },
    tags=["Mission Planning"],
)
@require_http_methods(["GET"])
def clear(request):
    response = DroneApiClient.clear()
    return HttpResponse(status=response.status_code)


@extend_schema(
    summary="Create diversion around exclusion zone",
    description=(
        "Dynamically reroutes the aircraft around an exclusion zone (no-fly zone, restricted airspace, or obstacle) "
        "while maintaining the overall mission path. The drone will navigate around the defined polygonal exclusion area "
        "and rejoin the normal flight path at the specified waypoint.\n\n"
        "**Note:** This endpoint is currently not fully implemented in the mission planner. "
        "It may return success but not execute the diversion logic.\n\n"
        "**Use Cases:**\n"
        "- Emergency airspace closures\n"
        "- Dynamic no-fly zones during mission execution\n"
        "- Obstacle avoidance without aborting the entire mission\n\n"
        "**Altitude Units:** Meters (relative to home position)"
    ),
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "exclude": {
                    "type": "array",
                    "description": "Array of waypoints defining the vertices of the exclusion polygon (in order)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "latitude": {
                                "type": "number",
                                "description": "Latitude in decimal degrees",
                            },
                            "longitude": {
                                "type": "number",
                                "description": "Longitude in decimal degrees",
                            },
                            "altitude": {
                                "type": "number",
                                "description": "Altitude in meters",
                            },
                        },
                    },
                    "example": [
                        {"latitude": 49.2606, "longitude": -123.2460, "altitude": 50},
                        {"latitude": 49.2610, "longitude": -123.2465, "altitude": 50},
                        {"latitude": 49.2615, "longitude": -123.2470, "altitude": 50},
                    ],
                },
                "rejoin_at": {
                    "type": "object",
                    "description": "Waypoint where the drone should rejoin the original mission after bypassing the exclusion zone",
                    "properties": {
                        "id": {"type": "integer"},
                        "latitude": {
                            "type": "number",
                            "description": "Latitude in decimal degrees",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Longitude in decimal degrees",
                        },
                        "altitude": {
                            "type": "number",
                            "description": "Altitude in meters",
                        },
                    },
                    "example": {
                        "id": 5,
                        "latitude": 49.2620,
                        "longitude": -123.2475,
                        "altitude": 50,
                    },
                },
            },
            "required": ["exclude", "rejoin_at"],
        }
    },
    responses={
        200: OpenApiResponse(
            description="Diversion request processed (implementation incomplete)"
        ),
        400: OpenApiResponse(description="Invalid input or mission planner error"),
    },
    tags=["Mission Planning"],
)
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


@extend_schema(
    summary="Change drone flight mode",
    description=(
        "Changes the drone's flight mode. Flight modes control how the drone behaves and responds to pilot input.\n\n"
        "**Common Flight Modes:**\n"
        "- **STABILIZE:** Manual control with attitude stabilization\n"
        "- **LOITER:** Holds position using GPS\n"
        "- **AUTO:** Autonomous flight following waypoint mission\n"
        "- **GUIDED:** Flies to commanded positions via GCS\n"
        "- **RTL:** Return to Launch and land\n"
        "- **LAND:** Descend and land at current position\n"
        "- **ALT_HOLD:** Maintains current altitude with manual horizontal control\n\n"
        "**Note:** Available modes depend on the drone's autopilot configuration."
    ),
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "description": "Flight mode name (e.g., AUTO, LOITER, RTL, STABILIZE)",
                    "example": "AUTO",
                }
            },
            "required": ["mode"],
        }
    },
    responses={
        200: OpenApiResponse(description="Flight mode changed successfully"),
        400: OpenApiResponse(description="Invalid input or mission planner error"),
    },
    tags=["Drone Control"],
)
@csrf_exempt
@require_http_methods(["PUT"])
def flightmode(request):
    try:
        data = json.loads(request.body)
        mode = data.get("mode")
        response = DroneApiClient.put_flightmode(mode)
        return HttpResponse(status=response.status_code)
    except (KeyError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid input"}, status=400)


@extend_schema(
    summary="Get or set drone parameter",
    description=(
        "**GET:** Retrieves the current value of a drone parameter by its parameter ID.\n\n"
        "**PUT:** Sets a new value for a drone parameter. The parameter is sent to the drone via MAVLink protocol, "
        "and the change is confirmed by the drone before returning success.\n\n"
        "**Parameters** are configuration values that control drone behavior, such as:\n"
        "- **RTL_ALT:** Return-to-Launch altitude in centimeters\n"
        "- **AUTO_OPTIONS:** Bitmask for AUTO mode behavior\n"
        "- **WPNAV_SPEED:** Waypoint navigation speed\n"
        "- And many more autopilot-specific parameters\n\n"
        "**Note:** Parameter names and units vary by autopilot (ArduPilot, PX4, etc.). "
        "Refer to your autopilot's parameter documentation for details."
    ),
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "number",
                    "description": "New parameter value (units depend on the specific parameter)",
                    "example": 5000,
                }
            },
            "required": ["value"],
        }
    },
    responses={
        200: OpenApiResponse(
            description="GET: Parameter value retrieved. PUT: Parameter set successfully."
        ),
        400: OpenApiResponse(
            description="Invalid input, parameter not found, or failed to set parameter"
        ),
        500: OpenApiResponse(description="Internal server error"),
    },
    tags=["Drone Configuration"],
)
@csrf_exempt
@require_http_methods(["GET", "PUT"])
def parameter(request, param_id):
    if request.method == "GET":
        try:
            response = DroneApiClient.get_parameter(param_id)

            if response.status_code >= 400:
                print(f"[ERROR] Mission-planner response: {response.text}")
                return JsonResponse(
                    {"error": "Mission-planner error", "details": response.text},
                    status=response.status_code,
                )

            return JsonResponse(
                response.json(), safe=False, status=response.status_code
            )
        except Exception as e:
            print(
                f"[ERROR] Unexpected error in get_parameter: {type(e).__name__}: {str(e)}"
            )
            return JsonResponse(
                {"error": "Internal server error", "details": str(e)}, status=500
            )
    else:  # PUT
        try:
            data = json.loads(request.body)
            value = data.get("value")

            if value is None:
                return JsonResponse(
                    {"error": "Parameter value is required"}, status=400
                )

            response = DroneApiClient.set_parameter(param_id, value)

            if response.status_code >= 400:
                print(f"[ERROR] Mission-planner response: {response.text}")
                return JsonResponse(
                    {"error": "Mission-planner error", "details": response.text},
                    status=response.status_code,
                )

            return HttpResponse(status=response.status_code)
        except (KeyError, ValueError, TypeError) as e:
            print(
                f"[ERROR] Invalid input for set_parameter: {type(e).__name__}: {str(e)}"
            )
            return JsonResponse({"error": "Invalid input"}, status=400)
        except Exception as e:
            print(
                f"[ERROR] Unexpected error in set_parameter: {type(e).__name__}: {str(e)}"
            )
            return JsonResponse(
                {"error": "Internal server error", "details": str(e)}, status=500
            )
