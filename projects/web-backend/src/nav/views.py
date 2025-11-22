from rest_framework import viewsets
from .models import Route, OrderedWaypoint
from .serializers import RouteSerializer, OrderedWaypointSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


# Create your views here.
class OrderedWaypointViewset(viewsets.ModelViewSet):
    """Viewset for CRUD operations on Waypoints"""

    queryset = OrderedWaypoint.objects.all()
    serializer_class = OrderedWaypointSerializer

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True

        return super(OrderedWaypointViewset, self).get_serializer(*args, **kwargs)


class RoutesViewset(viewsets.ModelViewSet):
    """Viewset for CRUD operations on Routes"""

    queryset = Route.objects.all().prefetch_related("waypoints")
    serializer_class = RouteSerializer

    @action(detail=True, methods=["post"], url_path="reorder-waypoints")
    def reorder_waypoints(self, request, pk=None):
        """
        Action to reorder waypoints in a route
        Args:
            request: The request object - contains the reordered waypoint ids
            pk: The primary key of the route whose waypoints we're reordering
        """
        route = self.get_object()

        waypoints = OrderedWaypoint.objects.filter(route=route)

        if (
            not request.data
            or not isinstance(request.data, list)
            or len(request.data) != len(waypoints)
        ):
            return Response(
                {"error": "Please provide a list of all waypoint IDs"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reordered_waypoint_ids = request.data
        for idx, waypoint_id in enumerate(reordered_waypoint_ids):
            try:
                waypoint = waypoints.get(id=waypoint_id)
                waypoint.order = idx
                waypoint.save()
            except OrderedWaypoint.DoesNotExist:
                return Response(
                    {"error": f"Waypoint with  not found with id: {waypoint_id}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {"success": "Waypoints reordered successfully"}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"], url_path="sync-waypoints")
    def sync_waypoints(self, request, pk=None):
        """
        Synchronize waypoints for a route in a single atomic operation.
        Handles creating new waypoints, updating existing ones, and deleting removed ones.
        Args:
            request: Contains list of waypoints with their data
            pk: The primary key of the route to sync
        Returns:
            The updated route with all waypoints
        """
        from django.db import transaction

        route = self.get_object()
        waypoints_data = request.data

        if not isinstance(waypoints_data, list):
            return Response(
                {"error": "Expected a list of waypoints"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Get current waypoints as a dict keyed by ID
            existing_waypoints = {str(wp.id): wp for wp in route.waypoints.all()}
            updated_waypoint_ids = set()

            # Process each waypoint in the new list
            for idx, waypoint_data in enumerate(waypoints_data):
                waypoint_id = str(waypoint_data.get("id", ""))

                # Check if this is a new waypoint (temporary ID like "-1" or negative number)
                is_new = waypoint_id == "-1" or (
                    waypoint_id.lstrip("-").isdigit() and int(waypoint_id) < 0
                )

                # Set order based on position in array and ensure route is set
                waypoint_data["order"] = idx
                waypoint_data["route"] = route.id

                if is_new:
                    # Create new waypoint - remove temporary ID
                    waypoint_data.pop("id", None)
                    serializer = OrderedWaypointSerializer(data=waypoint_data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                else:
                    # Update existing waypoint
                    if waypoint_id not in existing_waypoints:
                        return Response(
                            {"error": f"Waypoint {waypoint_id} not found in route"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    waypoint = existing_waypoints[waypoint_id]
                    serializer = OrderedWaypointSerializer(
                        waypoint, data=waypoint_data, partial=False
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    updated_waypoint_ids.add(waypoint_id)

            # Delete waypoints that are no longer in the list
            for waypoint_id, waypoint in existing_waypoints.items():
                if waypoint_id not in updated_waypoint_ids:
                    waypoint.delete()

        # Refresh and return the updated route
        route.refresh_from_db()
        serializer = RouteSerializer(route)
        return Response(serializer.data, status=status.HTTP_200_OK)
