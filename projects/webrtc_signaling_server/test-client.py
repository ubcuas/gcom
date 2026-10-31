"""
Author: Nitish Joson Terance Joe Heston

Description: This script is used to run a test of the server for debugging purposes.

Instruction:
in your terminal, make a virtual enviromemnt and download dependencies from requirement.txt
Have one terminal running the server and other terminals running clients. 
--------

cd path/to/webrtc_signaling_server    # the folder containing server.py

python3 -m venv venv                  # create the virtual environment
source venv/bin/activate              # activate it; your prompt should now start with (venv)

pip install python-socketio aiohttp prompt_toolkit   # install only what server.py needs

# terminal 1
python server.py

# terminal 2
python test-client.py client1

# terminal 3
python test-client.py client2
"""


import asyncio, sys
import socketio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

my_sfu = ""

name = sys.argv[1] if len(sys.argv) > 1 else "client"
sio = socketio.AsyncClient()




@sio.on("signal")
async def on_signal(data):
    print(f"[{name}] got signal: {data}")
    global my_sfu
    my_sfu = data["from"]
    print(f"[{name}] learned sfu: {my_sfu}")



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
    global my_sfu
    await sio.connect("http://localhost:8081", auth = {"role": "frontend"})   # use the port server.py listens on
    session = PromptSession()
    with patch_stdout():
        while True:
            text = await session.prompt_async(f"[{name}] > ")
            if my_sfu == "":
                print("No SFU Yet")
            else:
                await sio.emit("signal", {"to": my_sfu, "type": "offer", "data" : {"msg" : text}})

asyncio.run(main())