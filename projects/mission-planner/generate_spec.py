import sys
import os
import yaml
from flasgger import Swagger
from openapi_spec_validator import validate_spec
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

# Add src to python path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from server.httpserver import HTTP_Server


# Mock dependencies since we only need the route definitions
class MockMavConnection:
    pass


class MockStatusCache:
    pass


class MockHandler:
    pass


def generate_spec():
    # Instantiate server with mocks
    server = HTTP_Server(MockMavConnection(), MockStatusCache(), MockHandler())
    app, _ = server.create_app()

    # Define the base template with Info, Servers, Tags, and Components
    # This replaces the need to read from api_spec.yaml as a template
    template = {
        "openapi": "3.0.2",
        "info": {
            "title": "mission-planner",
            "version": "2.0.0",
            "description": "This is the API that the mission-planner server exposes to web-backend.",
            "contact": {"name": "Amin Fahiminia, Hansen Dan"},
        },
        "servers": [{"url": "http://localhost:9000"}],
        "tags": [
            {"name": "queue", "description": "Access to the waypoint queue"},
            {"name": "status", "description": "Access to aircraft status"},
            {
                "name": "feature",
                "description": "Access to competition-specific behaviour",
            },
            {
                "name": "landing",
                "description": "Access to landing, RTL, and home waypoint",
            },
            {"name": "options", "description": "Access to flight options"},
            {"name": "delivery", "description": "Access to delivery operations"},
            {"name": "takeoff", "description": "Access to takeoff operations"},
        ],
        "components": {
            "schemas": {
                "Waypoint": {
                    "type": "object",
                    "required": ["id", "name", "latitude", "longitude"],
                    "properties": {
                        "id": {
                            "type": "number",
                            "format": "integer",
                            "description": "Waypoint identifier",
                        },
                        "name": {
                            "type": "string",
                            "description": "Waypoint name (note: not preserved through MAVLink protocol, will be regenerated as 'Mission Waypoint N')",
                        },
                        "latitude": {
                            "type": "number",
                            "format": "float64",
                            "description": "Latitude in decimal degrees",
                        },
                        "longitude": {
                            "type": "number",
                            "format": "float64",
                            "description": "Longitude in decimal degrees",
                        },
                        "altitude": {
                            "type": "number",
                            "format": "float64",
                            "description": "Altitude in meters MSL. If omitted, uses previous waypoint's altitude (or 50m for first waypoint)",
                        },
                        "command": {
                            "type": "string",
                            "description": "MAVLink command type (e.g., 'WAYPOINT', 'LOITER_UNLIM', 'DO_CHANGE_SPEED'). Default: 'WAYPOINT'",
                            "default": "WAYPOINT",
                        },
                        "param1": {
                            "type": "number",
                            "format": "float",
                            "description": "Command parameter 1. For WAYPOINT: hold time in seconds (multicopter only). Default: 0",
                            "default": 0,
                        },
                        "param2": {
                            "type": "number",
                            "format": "float",
                            "description": "Command parameter 2. For WAYPOINT: acceptance radius in meters (NOTE: ignored by ArduPilot, use WPNAV_RADIUS parameter instead). Default: 0",
                            "default": 0,
                        },
                        "param3": {
                            "type": "number",
                            "format": "float",
                            "description": "Command parameter 3. For WAYPOINT: pass-through radius (NOTE: ignored by ArduPilot). Default: 0",
                            "default": 0,
                        },
                        "param4": {
                            "type": "number",
                            "format": "float",
                            "description": "Command parameter 4. For WAYPOINT: desired yaw angle (NOTE: ignored by ArduPilot in most cases). Default: 0",
                            "default": 0,
                        },
                    },
                },
                "Status": {
                    "type": "object",
                    "properties": {
                        "timestamp": {"type": "number", "format": "double"},
                        "current_wpn": {"type": "integer"},
                        "latitude": {"type": "number", "format": "double"},
                        "longitude": {"type": "number", "format": "double"},
                        "altitude": {"type": "number", "format": "double"},
                        "roll": {"type": "number", "format": "double"},
                        "pitch": {"type": "number", "format": "double"},
                        "airspeed": {"type": "number", "format": "double"},
                        "groundspeed": {"type": "number", "format": "double"},
                        "heading": {"type": "number", "format": "double"},
                        "batteryvoltage": {"type": "number", "format": "double"},
                        "winddirection": {"type": "number", "format": "double"},
                        "windvelocity": {"type": "number", "format": "double"},
                    },
                },
            }
        },
    }

    # Configure Flasgger to use OpenAPI 3.0.2
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
        "openapi": "3.0.2",
    }

    # Initialize Swagger using the in-code template and config
    swagger = Swagger(app, config=swagger_config, template=template)

    with app.app_context():
        # Get the spec (this returns the full OpenAPI object)
        spec = swagger.get_apispecs()

        # Validate the spec
        try:
            validate_spec(spec)
            print("Spec validation successful.")
        except OpenAPIValidationError as e:
            print(f"Spec validation failed: {e}")
            sys.exit(1)

        # Write to api_spec.yaml
        with open("api_spec.yaml", "w") as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

    print("API spec generated successfully at projects/mission-planner/api_spec.yaml")


if __name__ == "__main__":
    generate_spec()
