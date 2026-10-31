"""
Mock SFU

Connects to the signaling server as the "sfu". Sends an offer to every
frontend that joins, sends anything typed in the terminal to all connected frontends,
and can drop frontends that leave.

Usage: python test-sfu.py [name]
See the Testing section of README.md in this folder.

Author: Nitish Joson Terance Joe Heston
"""


import asyncio, sys
import socketio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


peer_ids = []

name = sys.argv[1] if len(sys.argv) > 1 else "sfu"
sio = socketio.AsyncClient()



@sio.on("peer_joined")
async def on_peer_joined(data):
    # SFU will always start with an offer. This is how the frontend learns the SFU's sid.
    peer_ids.append(data["peer_id"])
    await sio.emit("signal", {"to": data["peer_id"], "type": "offer", "data": {"msg": "hello"}})

@sio.on("peer_left")
async def on_peer_left(data):
    if data["peer_id"] in peer_ids:
        peer_ids.remove(data["peer_id"])
    print(f"[{name}] peer left: {data['peer_id']}")


@sio.on("signal")
async def on_signal(data):
    print(f"[{name}] got signal: {data}")

@sio.event
async def connect():
    print(f"[{name}] connected, sid={sio.sid}")

@sio.event
async def disconnect():
    print(f"[{name}] disconnected")

@sio.on("*")                      
async def any_event(event, data):
    #catch-all: prints every event the server sends, 
    #only fires if the event does not have its own handler
    print(f"[{name}] got '{event}': {data}")

async def main():
    await sio.connect("http://localhost:8081", auth = {"role": "sfu"})   # use the port server.py listens on
    session = PromptSession()
    with patch_stdout(): # keeps incoming messages printing above prompt instead of on top of prompt
        while True:
            text = await session.prompt_async(f"[{name}] > ")
            if not peer_ids:
                print("no peers to message to")
                continue
            for i in range(len(peer_ids)):
                await sio.emit("signal", {"to": peer_ids[i], "type": "offer", "data" : {"msg" : text}})


asyncio.run(main())