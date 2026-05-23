#!/bin/bash

TCP_PORTS=(8000 8081 9000)
UDP_PORTS=(14550 14551)

GRACE_PERIOD=2

IS_WINDOWS=false
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || -n "$WINDIR" ]]; then
    IS_WINDOWS=true
fi

find_pids() {
    local proto=$1
    local port=$2

    if [ "$IS_WINDOWS" = true ]; then
        # netstat -ano returns Windows PIDs; lsof is unreliable on MSYS2
        netstat -ano 2>/dev/null \
            | awk -v proto="${proto}" -v port="${port}" '
                toupper($1) == toupper(proto) && $2 ~ ":"port"$" { print $NF }
            ' | sort -u
    elif command -v lsof &>/dev/null; then
        lsof -ti "${proto}:${port}" 2>/dev/null
    else
        netstat -ano 2>/dev/null \
            | awk -v proto="${proto}" -v port="${port}" '
                toupper($1) == toupper(proto) && $2 ~ ":"port"$" { print $NF }
            ' | sort -u
    fi
}

kill_pids() {
    local pids=("$@")
    if [ "$IS_WINDOWS" = true ]; then
        for pid in "${pids[@]}"; do
            # taskkill operates on Windows PIDs directly; MSYS_NO_PATHCONV prevents
            # MSYS2 from mangling the /PID and /F flags into paths
            MSYS_NO_PATHCONV=1 taskkill /PID "$pid" /F 2>/dev/null
        done
    else
        kill -TERM "${pids[@]}" 2>/dev/null
    fi
}

force_kill_pids() {
    local pids=("$@")
    if [ "$IS_WINDOWS" = true ]; then
        for pid in "${pids[@]}"; do
            MSYS_NO_PATHCONV=1 taskkill /PID "$pid" /F 2>/dev/null
        done
    else
        kill -KILL "${pids[@]}" 2>/dev/null
    fi
}

kill_port() {
    local proto=$1
    local port=$2

    local pids
    pids=$(find_pids "$proto" "$port")

    if [ -z "$pids" ]; then
        echo "  $port ($proto): nothing running"
        return
    fi

    echo "  $port ($proto): killing PID(s) $pids"
    # shellcheck disable=SC2086
    kill_pids $pids

    if [ "$IS_WINDOWS" = false ]; then
        sleep "$GRACE_PERIOD"

        local remaining
        remaining=$(find_pids "$proto" "$port")
        if [ -n "$remaining" ]; then
            echo "  $port ($proto): force killing PID(s) $remaining"
            # shellcheck disable=SC2086
            force_kill_pids $remaining
        fi
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
