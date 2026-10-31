"""
Mock GCOM Frontend

Connects to the signaling server as a "frontend". Learns the SFU's sid from
the "from" field of the first offer it receives, then sends anything typed in the terminal
to the SFU. Clears the SFU when it receives "sfu_left".

Usage: python test-client.py <name>
See the Testing section of README.md in this folder.

Author: Nitish Joson Terance Joe Heston
"""

import asyncio, sys
import socketio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

sfu_sid = ""

name = sys.argv[1] if len(sys.argv) > 1 else "client"
sio = socketio.AsyncClient()


@sio.on("signal")
async def on_signal(data):
    global sfu_sid
    print(f"[{name}] got signal: {data}")

    #server will not tell the frontend who the sfu is,
    #so the frontend will learn the sfu_sid from the SFU's first message. 
    sfu_sid = data["from"]
    print(f"[{name}] learned sfu: {sfu_sid}")


@sio.on("sfu_left")
async def on_sfu_left(data):
    global sfu_sid
    sfu_sid = ""
    print(f"[{name}] sfu left: {data['peer_id']}") 


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
    await sio.connect("http://localhost:8081", auth = {"role": "frontend"})   # use the port server.py listens on
    session = PromptSession() 
    with patch_stdout(): # keeps incoming messages printing above prompt instead of on top of prompt
        while True:
            text = await session.prompt_async(f"[{name}] > ")
            if sfu_sid == "":
                print("No SFU Yet")
            else:
                await sio.emit("signal", {"to": sfu_sid, "type": "offer", "data" : {"msg" : text}})


asyncio.run(main())