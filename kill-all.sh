#!/bin/bash

TCP_PORTS=(8000 8081 9000)
UDP_PORTS=(14550 14551)

GRACE_PERIOD=2

kill_port() {
    local proto=$1
    local port=$2

    local pids
    pids=$(lsof -ti "${proto}:${port}" 2>/dev/null)

    if [ -z "$pids" ]; then
        echo "  $port ($proto): nothing running"
        return
    fi

    echo "  $port ($proto): killing PID(s) $pids"
    kill -TERM $pids 2>/dev/null

    sleep "$GRACE_PERIOD"

    local remaining
    remaining=$(lsof -ti "${proto}:${port}" 2>/dev/null)
    if [ -n "$remaining" ]; then
        echo "  $port ($proto): force killing PID(s) $remaining"
        kill -KILL $remaining 2>/dev/null
    fi
}

echo "Killing TCP ports..."
for port in "${TCP_PORTS[@]}"; do
    kill_port tcp "$port"
done

echo "Killing UDP ports..."
for port in "${UDP_PORTS[@]}"; do
    kill_port udp "$port"
done

echo "Done."
