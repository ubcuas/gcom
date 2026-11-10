"""
Prototype Video Streaming SFU

Connects to the signaling server as the "sfu" and streams tests/test-video.mp4
(on a loop) to every frontend that joins, over WebRTC. Each frontend gets its own
peer connection; all of them share the same video source. A frontend's connection
is closed when it leaves.

Usage: python video-streaming-sfu.py [name]
See the Testing section of README.md in this folder.

Author: Nitish Joson Terance Joe Heston
"""

import asyncio, sys
from pathlib import Path
import socketio

# RTCPeerConnection -> one WebRTC connection to ONE frontend
# RTCSessionDescription -> wraps an offer or answer, meaning the SDP text + its type
# MediaPlayer -> reads the video file and turns it into a video track
# MediaRelay -> lets several connections share one track
# VideoStreamTrack -> base class for a video source, handles frame timestamps
# MediaStreamError -> raised by a track when it has ended
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc.mediastreams import MediaStreamError

# found relative to this script, so it runs from any folder
VIDEO_FILE = Path(__file__).parent / "tests" / "test-video.mp4"

# FOR MOCK STREAM: loop video so that it doesn't freeze after 30s
class LoopingVideoTrack(VideoStreamTrack):
    # MediaPlayer(loop=True) ends the track at the end of the file, so reopen the file instead

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.player = MediaPlayer(path)

    async def recv(self):
        try:
            frame = await self.player.video.recv()
        except MediaStreamError:
            self.player = MediaPlayer(self.path)
            frame = await self.player.video.recv()
        # timestamps must keep increasing across restarts of the file
        frame.pts, frame.time_base = await self.next_timestamp()
        return frame


peer_connections = {}  # frontend sid -> RTCPeerConnection
video_source = LoopingVideoTrack(str(VIDEO_FILE))
relay = MediaRelay()

name = sys.argv[1] if len(sys.argv) > 1 else "sfu"
sio = socketio.AsyncClient()


@sio.on("peer_joined")
async def on_peer_joined(data):
    # SFU will always start with an offer. This is how the frontend learns the SFU's sid.
    peer_id = data["peer_id"]
    pc = RTCPeerConnection()
    peer_connections[peer_id] = pc
    pc.addTrack(relay.subscribe(video_source))
    offer = await pc.createOffer()
    # setLocalDescription gathers the ICE candidates, so send localDescription (not offer) to include them
    await pc.setLocalDescription(offer)
    await sio.emit("signal", {"to": peer_id, "type": "offer", "data": {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}})


@sio.on("peer_left")
async def on_peer_left(data):
    # close the connection so we stop sending video to a frontend that's gone
    pc = peer_connections.pop(data["peer_id"], None)
    if pc is not None:
        await pc.close()

    print(f"[{name}] peer left: {data['peer_id']}")


@sio.on("signal")
async def on_signal(data):
    print(f"[{name}] got signal: {data}")

    pc = peer_connections.get(data["from"])
    if pc is None:
        return

    # only answers matter; ice-candidate messages can be ignored since aiortc puts its candidates in the SDP
    if data["type"] != "answer":
        return

    await pc.setRemoteDescription(RTCSessionDescription(sdp=data["data"]["sdp"], type=data["data"]["type"]))


@sio.event
async def connect():
    print(f"[{name}] connected, sid={sio.sid}")


@sio.event
async def disconnect():
    print(f"[{name}] disconnected")


@sio.on("*")
async def any_event(event, data):
    # catch-all: prints every event the server sends,
    # only fires if the event does not have its own handler
    print(f"[{name}] got '{event}': {data}")


async def main():
    await sio.connect("http://localhost:8081", auth={"role": "sfu"})  # use the port server.py listens on
    await sio.wait()  # keep running until stopped with Ctrl+C


asyncio.run(main())
