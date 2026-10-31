"""
run chmod +x run-test.sh once 
start it with ./run-test.sh

Using tmux:

Move between panes: Ctrl+b, then an arrow key. 
Typing goes to the pane you're in, so move to a pane before sending a message from it.

Scroll up in a pane: Ctrl+b then [. Press q to stop scrolling.

Stop everything: tmux kill-session -t signaling.
 Or Ctrl+b then d detaches and leaves everything running in the background.
"""

#!/usr/bin/env bash
cd "$(dirname "$0")"          # run from this folder no matter where it's called from
PY=venv/bin/python            # use the venv's python directly, no need to activate
S=signaling

tmux kill-session -t $S 2>/dev/null   # clean up a previous run

tmux new-session -d -s $S "$PY server.py; exec bash"
tmux split-window -t $S "sleep 2; $PY test-sfu.py sfu; exec bash"
tmux split-window -t $S "sleep 3; $PY test-client.py peer1; exec bash"
tmux split-window -t $S "sleep 3; $PY test-client.py peer2; exec bash"
tmux select-layout -t $S tiled        # arrange as a 2x2 grid
tmux attach -t $S