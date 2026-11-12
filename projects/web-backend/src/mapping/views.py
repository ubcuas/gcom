import json
import math

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import AreaOfInterest
from .serializers import AreaOfInterestSerializer

# pylint: disable=no-member


@require_http_methods(["GET"])
def get_no_fly_zones(request):
    """Return temporary no-fly-zone data for the map UI.

    The query parameters mirror the future backend contract while keeping the
    mock zones close to the currently displayed drone.
    """
    try:
        latitude = float(request.GET.get("latitude", 49.2606))
        longitude = float(request.GET.get("longitude", -123.246))
    except (TypeError, ValueError):
        return JsonResponse({"error": "latitude and longitude must be numbers"}, status=400)

    return JsonResponse(
        [
            {
                "id": "mock-no-fly-zone-1",
                "latitude": latitude + 0.0012,
                "longitude": longitude + 0.0015,
                "radius_m": 75,
            },
            {
                "id": "mock-no-fly-zone-2",
                "latitude": latitude - 0.0014,
                "longitude": longitude - 0.0011,
                "radius_m": 110,
            },
        ],
        safe=False,
    )


@csrf_exempt
def process_area_of_interest(request):
    try:
        if request.method == "POST":
            valid_ser = AreaOfInterestSerializer(data=json.loads(request.body))

            if not valid_ser.is_valid():
                return HttpResponse("Invalid Input", status=400)

            a = str(valid_ser.validated_data["area_of_interest"])
            area_modelled = AreaOfInterest(
                area_of_interest=json.dumps(
                    valid_ser.validated_data["area_of_interest"]
                )
            )
            area_modelled.save()

            return HttpResponse(
                "Area of Interest Successfully Saved" + "\n" + a, status=200
            )
        elif request.method == "GET":
            area_modelled = AreaOfInterest.objects.last()
            if area_modelled is None:
                return HttpResponse("No Area Of Interest Saved", status=204)

            area = {"area_of_interest": json.loads(area_modelled.area_of_interest)}

            return JsonResponse(area, status=200)
        else:
            return HttpResponse("Correct Address, Incorrect Method", status=405)
    except (KeyError, ValueError, TypeError) as e:
        return HttpResponse("Server Error\n" + str(e), status=500)
