from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import string
import random
from django.utils import timezone
from .publisher import client, MQTT_TOPIC_CMD, ack_event, ack_data


@require_http_methods(["POST"])
@csrf_exempt
def send_command(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    data.setdefault(
        "id",
        "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16)),
    )
    data.setdefault("timestamp", timezone.now().timestamp())

    message_str = json.dumps(data)

    # Clear previous ACK state
    ack_event.clear()
    ack_data.clear()

    # Publish message
    client.publish(MQTT_TOPIC_CMD, message_str)
    try:
        # Wait for ACK (timeout 5 seconds)
        client.loop_start()
        if ack_event.wait(timeout=5):
            client.loop_stop()
            return JsonResponse(
                {"message": message_str, "ack": ack_data.get("ack")}, status=200
            )
        else:
            client.loop_stop()
            return JsonResponse({"message": message_str, "ack": None}, status=400)
    except Exception as e:
        return e
