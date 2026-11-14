# MediaMTX (Video Streaming)

[MediaMTX](https://github.com/bluenviron/mediamtx) takes in the camera streams over RTSP and serves them to browsers over WebRTC. Each browser sets up its connection directly with MediaMTX using WHEP (one HTTP request containing the WebRTC offer), so no separate signaling server is needed.

```
Jetson cameras / FFmpeg --RTSP--> MediaMTX --WebRTC--> browsers (GCOM frontend)
```

Its configuration is [`mediamtx.yml`](mediamtx.yml) in this folder, and it runs as the `mediamtx` service in the root `docker-compose.yml`.

## Starting MediaMTX

From the repo root:

```bash
docker compose up -d mediamtx
```

or start the whole of GCOM, which includes it:

```bash
docker compose up -d
```

Stop it with `docker compose stop mediamtx`.

## Streams

Each stream is a path in `mediamtx.yml`:

| Path | Source |
|---|---|
| `test` | Anything published to `rtsp://localhost:8556/test`, e.g. the FFmpeg commands below |
| `cam_front`, `cam_back`, `cam_probe`, `realsense` | Pulled from the Jetson at `rtsp://host.docker.internal:8554/<name>` when the first viewer connects. The names should match `camera_names` in `camera_streaming/config/cameras.yaml`. |

Any stream can be viewed directly at `http://localhost:8889/<stream-name>` (MediaMTX's own viewer page), which is useful for checking the video side before involving GCOM.

## Viewing in GCOM

Open the `/webrtc-test` page of the web frontend and click **Connect**. The frontend connects to `VITE_MEDIAMTX_URL` (default `http://localhost:8889`) and shows the stream named by `VITE_MEDIAMTX_STREAM` (default `test`). See the [web-frontend README](../projects/web-frontend/README.md).

## Test streams (no camera needed)

Install [FFmpeg](https://ffmpeg.org/) on the machine running the publisher, start MediaMTX, then publish to the `test` path with one of these. Leave FFmpeg running while viewing, and press `Ctrl+C` to stop publishing.

A generated test pattern with a tone:

```bash
ffmpeg -re -f lavfi -i testsrc=size=1280x720:rate=30 \
  -f lavfi -i sine=frequency=1000:sample_rate=44100 \
  -c:v libx264 -preset ultrafast -tune zerolatency -pix_fmt yuv420p -g 30 \
  -c:a aac -rtsp_transport tcp -f rtsp rtsp://localhost:8556/test
```

The looping test video, which has a running timer that makes delays easy to spot (run from the repo root):

```bash
ffmpeg -re -stream_loop -1 -i docker/test-video.mp4 \
  -c:v libx264 -preset ultrafast -tune zerolatency -pix_fmt yuv420p -g 30 \
  -rtsp_transport tcp -f rtsp rtsp://localhost:8556/test
```

Why these options matter:

- `-rtsp_transport tcp`: FFmpeg otherwise sends over UDP, which the compose setup doesn't expose, and MediaMTX drops the stream after 10 seconds.
- `-tune zerolatency`: produces video without B-frames (frames that depend on later frames). WebRTC can't play H264 with B-frames, so MediaMTX refuses to send it to browsers. This is also why the test video can't be published with `-c copy`.
- `-g 30`: a keyframe (full picture) every 30 frames, i.e. every second. A new viewer can't show anything until the next keyframe arrives, so with FFmpeg's default (one every 250 frames, about 8 seconds) connecting takes up to 8 seconds.

## Requirements for the camera streams

The Jetson's camera encoders need the same settings as the test streams:

- **No B-frames**, or MediaMTX can't send the stream to browsers.
- **A keyframe about every second** (keyframe interval / GOP), or new viewers wait several seconds for video.

## Viewing from another machine

WebRTC media uses UDP port `8189`. When viewing from another machine, set `MEDIAMTX_WEBRTC_HOST` in `.env` to an IP address or hostname reachable by viewers, then restart MediaMTX. The frontend's `VITE_MEDIAMTX_URL` must also point at that address instead of `localhost`.
