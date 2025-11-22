from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import OrderedWaypoint, Route


class OrderedWaypointSerializer(serializers.ModelSerializer):
    """Serializer to convert Waypoint objects to JSON"""

    class Meta:
        model = OrderedWaypoint
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=OrderedWaypoint.objects.all(),
                fields=["route", "order"],
                message="A waypoint with this order already exists in this route. Each waypoint must have a unique order within its route.",
            )
        ]


class RouteSerializer(serializers.ModelSerializer):
    """Serializer to convert Route objects to JSON"""

    waypoints = OrderedWaypointSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = ["id", "name", "waypoints"]
