# GCOM

## Overview

Welcome to the monorepo for the UAS Ground Communications project.
It houses the channel of communication between the drone and the web-app for waypoints, drone-actions and status updates.

It contains 3 main sub-projects:

1. **web-frontend** provides the user interface for operators
2. **web-backend** acts as the central server coordinating data flow and business logic
3. **mission-planner** handles low-level drone communication and flight operations
4. **integration-testing** provides integration testing for the connection between `mission-planner` and `web-backend`

Data flows from the drone through mission-planner → web-backend → web-frontend, with real-time updates pushed via WebSockets for live telemetry and status information.

The connection works like this:

- `mission-planner` interacts directly with the drone, and exposes a mavlink connection for interactions with the `web-backend`.
- The `web-backend` exposes a REST API for the `web-frontend` to communicate with.

## Projects Overview

Learn more about each project from their individual readmes:

- **[web-frontend](projects/web-frontend/README.md)** - User interface for operators
- **[web-backend](projects/web-backend/README.md)** - Central server coordinating data flow and business logic
- **[mission-planner](projects/mission-planner/README.md)** - Low-level drone communication and flight operations

## WebRTC Video Streaming in browser

The `mediamtx` service in `docker-compose.yml` serves WebRTC streams. Start it with:

```bash
docker compose up -d mediamtx
```
or start the entirety of gcom (and mediamtx service is included):
```bash
docker compose up -d
```

Open a stream in a browser at `http://localhost:8889/<stream-name>`. For example, the
test stream below is available at `http://localhost:8889/test`. WebRTC media uses UDP
port `8189`; when viewing from another machine, set `MEDIAMTX_WEBRTC_HOST` in `.env`
to an IP address or hostname reachable by viewers, then restart MediaMTX.

### Starting a stream

Make sure that there is an active camera connection to the Jetson, or use a mock stream. To get a successful video stream on the browser, the stream names should match the RTSP stream path as specified in `/docker/mediamtx.yml`. 

### Start a test stream (without any camera connection)

Install [FFmpeg](https://ffmpeg.org/) on the machine running the publisher, then publish
a generated video pattern to the configured `test` path:

```bash
ffmpeg -re -f lavfi -i testsrc=size=1280x720:rate=30 \
  -f lavfi -i sine=frequency=1000:sample_rate=44100 \
  -c:v libx264 -preset ultrafast -tune zerolatency -pix_fmt yuv420p \
  -c:a aac -f rtsp rtsp://localhost:8556/test
```

Leave FFmpeg running while viewing the stream. Press `Ctrl+C` to stop publishing, and
stop MediaMTX when finished with `docker compose stop mediamtx`.