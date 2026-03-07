#!/bin/bash

SESSION_NAME="gcom"
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

VENV_PATH="venv"
ARCH=$(uname -m)
NETWORK_NAME="gcom-x_uasnet"

select_python() {
    if command -v python3 &>/dev/null; then
        PY_CMD="python3"
    elif command -v python &>/dev/null; then
        PY_CMD="python"
    else
        echo "Error: Python is not installed on this system."
        exit 1
    fi
}

select_sitl_image() {
    if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
        UASITL_IMAGE="ubcuas/uasitl:copter-arm-4.5.5"
        echo "ARM architecture detected. Using ARM image."
    else
        UASITL_IMAGE="ubcuas/uasitl:copter-4.5.5"
        echo "non-ARM architecture detected. Using standard image."
    fi
}

setup_network() {
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        echo "Creating docker network: $NETWORK_NAME"
        docker network create "$NETWORK_NAME"
    else
        echo "Network $NETWORK_NAME already exists, skipping creation."
    fi
}

select_mavproxy_command() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        MAV_CMD="mavproxy.py"
        MAV_ARGS="--master=tcp:127.0.0.1:5760 --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        MAV_CMD="mavproxy.py"
        MAV_ARGS="--master=tcp:127.0.0.1:5760 --out=udp:172.25.32.1:14550 --out=udp:127.0.0.1:14551"
    else
        MAV_CMD="mavproxy"
        MAV_ARGS="--master=tcp:127.0.0.1:5760 --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551"
    fi
}

prepare_env() {
    local folder=$1
    local venv_dir="$folder/$VENV_PATH"
    local req_file="$folder/requirements.txt"

    # Check if python3-venv is actually working
    if ! $PY_CMD -m venv --help &>/dev/null; then
        echo "-------------------------------------------------------"
        echo "ERROR: Python 'venv' module is missing."
        echo "If you are on Ubuntu/Debian, run:"
        echo "    sudo apt update && sudo apt install python3-venv"
        echo "-------------------------------------------------------"
        exit 1
    fi

    # 1. Create if missing
    if [ ! -d "$venv_dir" ]; then
        echo "Creating new venv in $folder..."
        $PY_CMD -m venv "$venv_dir"
        "$venv_dir/bin/pip" install --upgrade pip
        "$venv_dir/bin/pip" install -r "$req_file"
        touch "$venv_dir/pyvenv.cfg" # Mark as updated
        return
    fi

    # 2. Update if requirements.txt changed since last run
    if [ -f "$req_file" ]; then
        if [[ "$req_file" -nt "$venv_dir/pyvenv.cfg" ]]; then
            echo "Changes detected in requirements.txt. Updating..."
            "$venv_dir/bin/pip" install -r "$req_file"
            touch "$venv_dir/pyvenv.cfg"
        fi
    fi
}

setup_tmux() {
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
}

setup_sitl() {
    select_sitl_image
    setup_network
    # SITL
    tmux send-keys -t "$SESSION_NAME:0.0" "echo 'Starting SITL'; docker rm -f uasitl 2>/dev/null && docker run --rm -p 5760-5780:5760-5780 -it --network=gcom-x_uasnet --name=uasitl $UASITL_IMAGE" C-m
    echo "Waiting for SITL to initialize..."
    sleep 3
}

setup_mavproxy() {
    select_mavproxy_command
    # Mavproxy
    tmux send-keys -t "$SESSION_NAME:0.1" "echo 'Starting mavproxy'; cd $SCRIPT_DIR/mission-planner && source $VENV_PATH/bin/activate && $MAV_CMD $MAV_ARGS" C-m
    echo "Giving MAVProxy time to start the network streams..."
    sleep 3
}

setup_mission_planner() {
    # Mission Planner
    tmux send-keys -t "$SESSION_NAME:0.2" "echo 'Starting mission planner'; cd $SCRIPT_DIR/mission-planner && source $VENV_PATH/bin/activate && $PY_CMD src/main.py" C-m
}

setup_web_backend() {
    # Web Backend
    tmux send-keys -t "$SESSION_NAME:0.3" "echo 'Starting web backend'; cd $SCRIPT_DIR/web-backend && source $VENV_PATH/bin/activate && $PY_CMD src/server.py" C-m
}

setup_web_frontend() {
    # Web Frontend
    tmux send-keys -t "$SESSION_NAME:0.4" "echo 'Starting web frontend'; cd $SCRIPT_DIR/web-frontend && npm run dev" C-m
}

start_all() {
    select_python
    prepare_env "$SCRIPT_DIR/mission-planner"
    prepare_env "$SCRIPT_DIR/web-backend"
    setup_tmux
    setup_sitl
    setup_mavproxy
    setup_mission_planner
    setup_web_backend
    setup_web_frontend
    tmux attach-session -t "$SESSION_NAME"
}

start_all
