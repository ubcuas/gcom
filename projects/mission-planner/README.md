# MissionPlanner Scripts

## Overview

This project provides a HTTP server that interfaces with drone autopilot systems using the MAVLink protocol. It acts as a bridge between drones/SITL (Software In The Loop) simulation and the GCOM web-backend, enabling automated mission planning and execution for UAS (Unmanned Aerial Systems). The web-backend uses this API to control drones and receive telemetry data.

**Key Components:**

- **SITL (Software In The Loop)**: A simulation environment that runs autopilot firmware virtually, allowing you to test drone behavior without physical hardware
- **Updated System**: The current cross-platform implementation using pymavlink for direct MAVLink communication - operates independently without requiring Mission Planner desktop application

## Table of Contents

1. [Instructions](#instructions)
2. [Endpoints](#endpoints)
3. [Sockets](#sockets)

## Instructions

The current system uses pymavlink to communicate directly with autopilot systems via the MAVLink protocol. This approach works cross-platform and operates completely independently - Mission Planner desktop application is only needed for optional visualization and monitoring.

### SITL

1. In order to run SITL on your local machine, you will need to have Docker installed. For installation instructions, refer to the following:

    - [Windows Installation](https://docs.docker.com/desktop/install/windows-install/)
    - [MacOS Installation](https://docs.docker.com/desktop/install/mac-install/)

2. Optionally, you can install Mission Planner for flight visualization and monitoring. Refer to [installation steps](https://ardupilot.org/planner/docs/mission-planner-installation.html). Note: This is not required for the system to function.

3. Once you have Docker, you will need to pull the [SITL image from DockerHub](https://hub.docker.com/r/ubcuas/uasitl/tags). To do this, run the Docker application then run the following command (where `X.X.X` is the desired ArduPilot version - this should match what is/will be running on the drone):

    - ArduPlane (VTOL):
        - x86: `docker pull ubcuas/uasitl:plane-X.X.X`
        - ARM64: `docker pull ubcuas/uasitl:plane-arm-X.X.X`
    - ArduCopter (Quadcopter):
        - x86: `docker pull ubcuas/uasitl:copter-X.X.X`
        - ARM64: `docker pull ubcuas/uasitl:copter-arm-X.X.X`

    If everything goes correctly, running `docker image ls` should contain an entry for `ubcuas/uasitl`.

4. Run one of the following commands to get SITL running. Refer to [the documentation](https://github.com/ubcuas/UASITL) for more customization:

    - x86: `docker run --rm -d -p 5760:5760 --name acom-sitl ubcuas/uasitl:[plane/copter]-X.X.X`
    - ARM64: `docker run --rm -d -p 5760:5760 --name acom-sitl ubcuas/uasitl:[plane/copter]-arm-X.X.X`

### Mavproxy

Mavproxy is a command-line ground station software that acts as a communication proxy between SITL and other applications. It forwards MAVLink messages from the simulated drone to multiple outputs, allowing both Mission Planner (for visualization) and this project (for programmatic control) to connect simultaneously.

Refer to [Mavproxy documentation](https://ardupilot.org/mavproxy/docs/getting_started/download_and_installation.html#updating) for installation instructions (Installing via pip is recommended for Linux systems. Windows installations must use the installer.).

#### Running Mavproxy

Linux:

```bash
mavproxy.py --master=tcp:127.0.0.1:5760 --out=udp:172.25.32.1:14550 --out=udp:127.0.0.1:14551
```

Windows:

```pwsh
mavproxy --master=tcp:127.0.0.1:5760 --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551
```

> [!NOTE]
> Change the IP address according to your networking setup.
> In the example command, we're running Docker, Mission Planner Script, and mavproxy inside WSL2 with Mission Planner on the host Windows machine. Therefore, I set master to connect to the SITL container and output to another localhost port for Mission Planner Script (pymavlink) to connect to and another output to the IP of Windows host machine.
> If using WSL2, get the IP of host machine using `ip route show default`
> If using Windows, make sure to run mavproxy as an Administrator.

When running mavproxy, point master to the SITL instance connection and specify 2 outputs, one to interface with pymavlink and one for connecting with Mission Planner for visualization. Optionally, omit the second output if Mission Planner visualization is not needed.

### Using MPS

1. Create and activate a virtual environment

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

2. Install required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Launch the application:

    ```bash
    python src/main.py
    ```

    The server will listen on the specified port (default 9000) for HTTP requests.

### Command Line Arguments

| Argument                  | Description                                                               |
| ------------------------- | ------------------------------------------------------------------------- |
| `--dev`                   | If present, server is started in development mode rather than production. |
| `--port=9000`             | Port on which to listen for HTTP requests.                                |
| `--status-host=localhost` | Hostname for the status socket to connect to.                             |
| `--status-port=1323`      | Port for the status socket to connect to.                                 |
| `--disable-status`        | If present, disables the status socket.                                   |

> [!TIP]
> `main.py` usually cannot be stopped via CTRL+C. CTRL+BREAK sometimes works, depending on the system.
> If those two methods do not work then the program can be terminated by closing the terminal instance
> that it was originally invoked from.

### Visualization (Optional)

Connect Mission Planner to one of the outputs of mavproxy for flight visualization and monitoring. This is not required for the system to function but provides helpful visual feedback during development and testing.

## Endpoints

See `api_spec.yml` or `postman_collection.json` for up-to-date information on endpoints.

## Sockets

The status WebSocket client connects to `localhost:1323` by default. The hostname and port can be changed via command-line arguments.

Every 100ms, it will emit the `drone_update` event with the following information:

```json
{
  "timestamp": 0,
  "latitude": 0.0,
  "longitude": 0.0,
  "altitude": 0.0,
  "vertical_velocity": 0.0,
  "velocity": 0.0,
  "heading": 0.0,
  "battery_voltage": 0.0
}
```

The timestamp is the number of milliseconds since the epoch.
