

import asyncio, sys
import socketio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


peer_ids = []

name = sys.argv[1] if len(sys.argv) > 1 else "sfu"
sio = socketio.AsyncClient()



@sio.on("peer_joined")
async def on_peer_joined(data):
    global peer_ids
    peer_ids.append(data["peer_id"])
    await sio.emit("signal", {"to": data["peer_id"], "type": "offer", "data": {"msg": "hello"}})



@sio.on("signal")
async def on_signal(data):
    print(f"[{name}] got signal: {data}")

@sio.event
async def connect():
    print(f"[{name}] connected, sid={sio.sid}")

@sio.event
async def disconnect():
    print(f"[{name}] disconnected")

@sio.on("*")                       # catch-all: prints every event the server sends
async def any_event(event, data):
    print(f"[{name}] got '{event}': {data}")

async def main():
    global peer_ids
    await sio.connect("http://localhost:8081", auth = {"role": "sfu"})   # use the port server.py listens on
    session = PromptSession()
    with patch_stdout():
        while True:
            text = await session.prompt_async(f"[{name}] > ")
            index = 0
            if not peer_ids:
                print("no peers to message to")
                continue
            for i in range(len(peer_ids)):
                await sio.emit("signal", {"to": peer_ids[i], "type": "offer", "data" : {"msg" : text}})


asyncio.run(main())