#!/usr/bin/env sh
set -eu

# Install dependencies first.
# We keep this here (instead of baking an image) so the repo works without
# publishing images, but we still provide a deterministic readiness signal.
python -m pip install --no-cache-dir -U pip
python -m pip install --no-cache-dir future MAVProxy

# Mark container as ready for dependent services.
# This is what the docker healthcheck will wait for.
touch /tmp/mavproxy.ready

exec mavproxy.py --master=tcp:sitl:5760 --out=udp:mission-planner:14551
