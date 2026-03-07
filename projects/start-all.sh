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
    # 1. Search for Hardware (Telemetry Radio) - Prioritizes this over SITL
    local USB_RADIO=$(ls /dev/tty.usbserial* /dev/ttyUSB* 2>/dev/null | head -n 1)

    # 2. Configure Master and Baudrate based on what we found
    if [ -n "$USB_RADIO" ]; then
        echo "--- HARDWARE DETECTED: $USB_RADIO ---"
        MASTER_STR="$USB_RADIO"
        BAUD_STR="--baudrate=115200"
        IS_HARDWARE=true  # Flag to disable SITL later
    else
        echo "--- NO HARDWARE: Falling back to SITL ---"
        MASTER_STR="tcp:127.0.0.1:5760"
        BAUD_STR=""
        IS_HARDWARE=false
    fi

    # 3. Set OS-Specific Command and Arguments
    if [[ "$OSTYPE" == "darwin"* ]]; then
        MAV_CMD="mavproxy.py"
        MAV_ARGS="--master=$MASTER_STR $BAUD_STR --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        MAV_CMD="mavproxy.py"
        MAV_ARGS="--master=$MASTER_STR $BAUD_STR --out=udp:172.25.32.1:14550 --out=udp:127.0.0.1:14551"
    else
        MAV_CMD="mavproxy"
        MAV_ARGS="--master=$MASTER_STR $BAUD_STR --out=udp:127.0.0.1:14550 --out=udp:127.0.0.1:14551"
    fi
}

prepare_env() {
    local folder=$1
    local venv_dir="$folder/$VENV_PATH"
    local req_file="$folder/requirements.txt"

    if ! $PY_CMD -m venv --help &>/dev/null; then
        echo "ERROR: Python 'venv' module is missing."
        exit 1
    fi

    if [ ! -d "$venv_dir" ]; then
        echo "Creating new venv in $folder..."
        $PY_CMD -m venv "$venv_dir"
        "$venv_dir/bin/pip" install --upgrade pip
        "$venv_dir/bin/pip" install -r "$req_file"
        touch "$venv_dir/pyvenv.cfg"
        return
    fi

    if [ -f "$req_file" ]; then
        if [[ "$req_file" -nt "$venv_dir/pyvenv.cfg" ]]; then
            echo "Updating requirements in $folder..."
            "$venv_dir/bin/pip" install -r "$req_file"
            touch "$venv_dir/pyvenv.cfg"
        fi
    fi
}

setup_tmux() {
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        echo "Session '$SESSION_NAME' already exists. Attaching..."
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
    # Only run SITL if no hardware was detected
    if [ "$IS_HARDWARE" = false ]; then
        select_sitl_image
        setup_network
        tmux send-keys -t "$SESSION_NAME:0.0" "echo 'Starting SITL'; docker rm -f uasitl 2>/dev/null; docker run --rm -p 5760-5780:5760-5780 -it --network=gcom-x_uasnet --name=uasitl $UASITL_IMAGE" C-m
        echo "Waiting for SITL to initialize..."
        sleep 3
    else
        tmux send-keys -t "$SESSION_NAME:0.0" "echo 'Hardware detected at $MASTER_STR. SITL bypassed.'" C-m
    fi
}

setup_mavproxy() {
    # Mavproxy
    tmux send-keys -t "$SESSION_NAME:0.1" "echo 'Starting mavproxy'; cd $SCRIPT_DIR/mission-planner && source $VENV_PATH/bin/activate && $MAV_CMD $MAV_ARGS" C-m
    echo "Giving MAVProxy time to start..."
    sleep 3
}

setup_mission_planner() {
    tmux send-keys -t "$SESSION_NAME:0.2" "echo 'Starting mission planner'; cd $SCRIPT_DIR/mission-planner && source $VENV_PATH/bin/activate && $PY_CMD src/main.py" C-m
}

setup_web_backend() {
    tmux send-keys -t "$SESSION_NAME:0.3" "echo 'Starting web backend'; cd $SCRIPT_DIR/web-backend && source $VENV_PATH/bin/activate && $PY_CMD src/server.py" C-m
}

setup_web_frontend() {
    tmux send-keys -t "$SESSION_NAME:0.4" "echo 'Starting web frontend'; cd $SCRIPT_DIR/web-frontend && npm run dev" C-m
}

start_all() {
    select_python
    select_mavproxy_command # Must run before setup_sitl to set IS_HARDWARE flag
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
