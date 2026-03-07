#!/bin/bash

SESSION_NAME="gcom_projects"
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "Error: Python is not installed on this system."
    exit 1
fi

ARCH=$(uname -m)
if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    UASITL_IMAGE="ubcuas/uasitl:copter-arm-4.5.5"
    echo "ARM architecture detected. Using ARM image."
else
    UASITL_IMAGE="ubcuas/uasitl:copter-4.5.5"
    echo "non-ARM architecture detected. Using standard image."
fi

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    MAV_CMD="mavproxy.py"
    MAV_ARGS="--master=tcp:127.0.0.1:5760 --out=udp:172.25.32.1:14550 --out=udp:127.0.0.1:14551"
else
    MAV_CMD="mavproxy"
    MAV_ARGS="--master=tcp:127.0.0.1:5760 --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551"
fi

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Session '$SESSION_NAME' already exists. Ataching to the existing session..."
    tmux attach-session -t "$SESSION_NAME"
    exit 0
fi

tmux new-session -d -s "$SESSION_NAME"
tmux split-window -t "$SESSION_NAME:0" -v
tmux split-window -t "$SESSION_NAME:0" -h
tmux select-pane -t "$SESSION_NAME:0.0"
tmux split-window -t "$SESSION_NAME:0" -v
tmux split-window -t "$SESSION_NAME:0" -h
tmux select-layout -t "$SESSION_NAME:0" tiled

# SITL
tmux send-keys -t "$SESSION_NAME:0.0" "echo 'Starting SITL'; docker rm -f uasitl 2>/dev/null && docker run --rm -p 5760-5780:5760-5780 -it --network=gcom-x_uasnet --name=uasitl $UASITL_IMAGE" C-m
echo "Waiting for SITL to initialize..."
sleep 3

# Mavproxy
tmux send-keys -t "$SESSION_NAME:0.1" "echo 'Starting mavproxy'; cd $SCRIPT_DIR/mission-planner && source venv/bin/activate && $MAV_CMD $MAV_ARGS" C-m
echo "Giving MAVProxy time to start the network streams..."
sleep 3

# Mission Planner
tmux send-keys -t "$SESSION_NAME:0.2" "echo 'Starting mission planner'; cd $SCRIPT_DIR/mission-planner && source venv/bin/activate && $PY_CMD src/main.py" C-m

# Web Backend
tmux send-keys -t "$SESSION_NAME:0.3" "echo 'Starting web backend'; cd $SCRIPT_DIR/web-backend && source venv/bin/activate && $PY_CMD src/server.py" C-m

# Web Frontend
# tmux send-keys -t "$SESSION_NAME:0.4" "echo 'Starting web frontend'; cd $SCRIPT_DIR/web-frontend && npm run dev" C-m
# Modified line to prevent the pane from closing on error
tmux send-keys -t "$SESSION_NAME:0.4" "cd $SCRIPT_DIR/web-frontend && npm run dev || read" C-m

tmux attach-session -t "$SESSION_NAME"
