# WebRTC Signaling Server

A lightweight Socket.IO-based signaling server that coordinates WebRTC connection establishment between the Streaming Node and GCOM system.

## Overview

This server facilitates the exchange of WebRTC session descriptions (SDP) and ICE candidates between peers. It does not handle media or data transmission itself - only the signaling handshake required to establish a direct peer-to-peer connection.

For the overall streaming design, current tasks and WebRTC reading material, see the [Video Streaming Prototype Setup](https://docs.google.com/document/d/1ylTDTS70TpU-JMkbgAyR9Vlb4LoIdt7-BBO7r3wqGHU/edit?usp=sharing) doc.

## Requirements

- Python 3.8+

## Installation

1. Navigate to the signaling server directory:
```bash
cd projects/webrtc_signaling_server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or using a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Start the server:
```bash
python server.py
```

The server will start on port 8081 and accept WebSocket connections.

## Testing

The `tests/` folder has helper scripts that let you test the server without a real SFU, frontend, or video streaming:

| File | Role | What it does |
|---|---|---|
| `test-sfu.py` | `sfu` | This is the Mock SFU. It will Automatically send an `offer` to every frontend that joins, and sends anything typed in the terminal to all connected frontends. Tracks peers through `peer_joined` / `peer_left`. |
| `test-client.py` | `frontend` | This is the Mock frontend. It will learn the SFU's sid from the `from` field of the first offer it receives, then sends anything typed in the terminal to the SFU. It will clear the SFU sid on `sfu_left`. |
| `run-test.sh` | n/a | Opens a tmux session with the server, with one SFU and two frontends in a 2x2 grid.|
| `test-video.mp4` | n/a | Test video (with a running timer) streamed by `video-streaming-sfu.py`. |
| `test-website.html` | `frontend` | Browser test page for the video stream. Work in progress, still an empty template. |

### Setup (once)

```bash
cd projects/webrtc_signaling_server
python3 -m venv venv
source venv/bin/activate
pip install python-socketio aiohttp prompt_toolkit aiortc
chmod +x tests/run-test.sh
```

### Run

```bash
./tests/run-test.sh
```

Requires tmux (Linux, macOS or WSL). To run it without tmux, start each one in its own terminal from `projects/webrtc_signaling_server`, in this order:

```bash
python server.py
python tests/test-sfu.py sfu
python tests/test-client.py peer1
python tests/test-client.py peer2
```

### What you should see

1. Each frontend prints `got signal ... 'type': 'offer'` and then `learned sfu: <sid>`.
2. Typing in a frontend pane: the SFU pane prints the message with `from` set to that frontend.
3. Typing in the SFU pane: every frontend receives it.
4. Close a frontend: the SFU prints `peer left`.
5. Close the SFU: the frontends print `sfu left` and show `No SFU Yet` until a new SFU connects.

### Video streaming SFU

`video-streaming-sfu.py` (in this folder, not `tests/`) is a prototype SFU that sends video over WebRTC. For now it streams a local test video instead of the live stream. It connects with role `sfu`, and for every frontend that joins it creates a peer connection, adds the video from `tests/test-video.mp4` (looped), and sends the offer. It applies each frontend's answer, and closes the connection when that frontend leaves.

For now, until the test-website is completed, run it instead of `test-sfu.py` in order to test its functionality (not both, since only one SFU can connect at a time):

```bash
python server.py
python video-streaming-sfu.py
```

> NOTE:
> Testing is incomplete. The next step is to test the video in a browser using `tests/test-website.html`, which is still being written.

Until then, `test-client.py` can connect as a frontend, but it can't answer a WebRTC offer, so it only shows that the offer arrives.

### tmux basics

- `Ctrl+b` then an arrow key: switch pane (typing goes to the pane you're in)
- `Ctrl+b` then `[`: scroll (press `q` to stop)
- `Ctrl+b` then `d`: detach (everything keeps running); `tmux attach -t signaling` brings it back
- `tmux kill-session -t signaling`: stop everything

### Stopping a server that's already running

If starting the server fails because port 8081 is already in use, an older server is still running:

- Started by `run-test.sh`: `tmux kill-session -t signaling` (or `Ctrl+b`, then `:kill-session`, then Enter, from inside tmux)
- Started in a normal terminal: press `Ctrl+C` in that terminal
- Not sure where it's running: `ss -ltnp | grep 8081` shows the process using the port and its `pid`; stop it with `kill <pid>`

## Events

There are two client roles:
- **`sfu`**: the video source (the SFU, or a mock/streaming node). Only one at a time.
- **`frontend`**: a GCOM web frontend instance. Any number can connect.

A client declares its role in the Socket.IO `auth` payload when it connects. There is no separate register event:

```javascript
const socket = io("http://localhost:8081", { auth: { role: "frontend" } });
```

```python
await sio.connect("http://localhost:8081", auth={"role": "sfu"})
```

The server refuses the connection (the client receives `connect_error`) if the role is missing or invalid, or if an `sfu` is already connected.

| Direction | Event | Payload | Meaning |
|---|---|---|---|
| client → server | `connect` (Socket.IO built-in) | `auth: {"role": "frontend" \| "sfu"}` | Opening the connection. The role is sent in the `auth` payload; see above. |
| server → sfu | `peer_joined` | `{"peer_id": "<sid>"}` | A frontend has connected. The SFU should create a peer connection and send it an offer. When the SFU connects, it receives one `peer_joined` for every frontend already connected. |
| server → sfu | `peer_left` | `{"peer_id": "<sid>"}` | A frontend disconnected. The SFU should close that peer connection. |
| server → frontend | `sfu_left` | `{"peer_id": "<sid>"}` | The SFU disconnected. The frontend should close its peer connection and wait for a new offer. |
| client → server → client | `signal` | `{"to": "<sid>", "type": ..., "data": {...}}` | An offer, answer or ICE candidate (see [Message Format](#message-format)). `to` is required. The server adds `"from": "<sender sid>"` and forwards it to that one peer only. |
| server → client | `error` | `{"message": "..."}` | The client's last message was rejected. |

Routing rules:
- `signal` is only forwarded between a frontend and the SFU. Frontends never receive anything about each other.
- `signal` with a missing/unknown `to`, or sent from a client without a valid role, is rejected with `error` by the server.
- The SFU always sends the offer; frontends only answer.

## Message Format

Clients should send signaling messages in the following format:

```json
{
  "to": "<sid>",
  "type": "offer" | "answer" | "ice-candidate",
  "data": { ... }
}
```

### Valid Message Types

- `offer`: WebRTC SDP offer
- `answer`: WebRTC SDP answer
- `ice-candidate`: ICE candidate for network path negotiation

### Example Messages

**Offer:**
```json
{
  "to": "<sid>",
  "type": "offer",
  "data": {
    "sdp": "...",
    "type": "offer"
  }
}
```

**Answer:**
```json
{
  "to": "<sid>",
  "type": "answer",
  "data": {
    "sdp": "...",
    "type": "answer"
  }
}
```

**ICE Candidate:**
```json
{
  "to": "<sid>",
  "type": "ice-candidate",
  "data": {
    "candidate": "...",
    "sdpMid": "...",
    "sdpMLineIndex": 0
  }
}
```

## Client Connection

Clients connect using Socket.IO protocol and must declare a role. Example of a frontend using JavaScript:

```javascript
const socket = io('http://localhost:8081', { auth: { role: 'frontend' } });

socket.on('connect', () => {
  console.log('Connected to signaling server');
});

socket.on('signal', (data) => {
  console.log('Received signal:', data);
  // data.from is the sender's sid (the SFU); reply to it with an answer
});

// Send signaling message (after receiving the SFU's offer)
socket.emit('signal', {
  to: sfuSid,  // the "from" of the offer
  type: 'answer',
  data: { /* answer data */ }
});
```

For a full browser implementation, see `projects/web-frontend/src/hooks/useWebRTCConnection.ts`.

## Behavior

- **Clients**: one `sfu` at a time and any number of `frontend`s. Connections with a missing or invalid role, or a second `sfu`, are refused.
- **Message Routing**: `signal` messages go only to the client named in `to`, and only between a frontend and the SFU.
- **Validation**: Validates message format, message types and the `to` field, and replies with `error` when a message is rejected
- **Logging**: Logs all connections, disconnections, and messages

## Health Check

A simple HTTP endpoint is available at `http://localhost:8081/` for health checks.

## Architecture

This signaling server is a critical component in the Hawkeye-OS streaming architecture:

```
Streaming Node <---> Signaling Server <---> GCOM frontend(s)
                           |
                    (Coordinates WebRTC
                     connection setup)
```

After the WebRTC connection is established, the signaling server is no longer needed for data transmission.
