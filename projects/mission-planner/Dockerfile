# Multi-stage Dockerfile for Mission Planner with ArduCopter 4.5.5 SITL on ARM64
# For Linux devices running ARM architecture
# Note: Mavproxy runs as a separate service in docker-compose

# Stage 1: Base image with essential tools
FROM arm64v8/python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    curl \
    sudo \
    pkg-config \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Mission Planner application
FROM base AS mps

# Set working directory
WORKDIR /app

# Copy mission planner project files
COPY requirements.txt .
COPY pyproject.toml .
COPY src/ ./src/
COPY technical-documentation/ ./technical-documentation/

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir future

# Create entrypoint script
RUN mkdir -p /app/scripts && \
    cat > /app/scripts/entrypoint.sh << 'ENTRYPOINT_EOF' && \
    chmod +x /app/scripts/entrypoint.sh
#!/bin/bash

# Configuration from environment variables with defaults
MAVLINK_MASTER=${MAVLINK_MASTER:-"udp:mavproxy:14551"}
MPS_HOST=${MPS_HOST:-"0.0.0.0"}
MPS_PORT=${MPS_PORT:-"9000"}
MPS_DEV=${MPS_DEV:-""}
MPS_STATUS_HOST=${MPS_STATUS_HOST:-"0.0.0.0"}
MPS_STATUS_PORT=${MPS_STATUS_PORT:-"8000"}
DISABLE_STATUS=${DISABLE_STATUS:-"false"}

echo "Starting Mission Planner Server (MPS)..."
echo "  MAVLink Master: $MAVLINK_MASTER"
echo "  Host: $MPS_HOST"
echo "  Port: $MPS_PORT"
echo "  Status Host: $MPS_STATUS_HOST"
echo "  Status Port: $MPS_STATUS_PORT"

# Build MPS command line arguments
MPS_ARGS="--port=$MPS_PORT"
[ -n "$MPS_DEV" ] && MPS_ARGS="$MPS_ARGS --dev"
[ "$DISABLE_STATUS" = "true" ] && MPS_ARGS="$MPS_ARGS --disable-status"
[ -n "$MPS_STATUS_HOST" ] && MPS_ARGS="$MPS_ARGS --status-host=$MPS_STATUS_HOST"
[ -n "$MPS_STATUS_PORT" ] && MPS_ARGS="$MPS_ARGS --status-port=$MPS_STATUS_PORT"

# Start MPS in foreground
python src/main.py $MPS_ARGS
ENTRYPOINT_EOF

# Expose ports
# Mission Planner Server HTTP port
EXPOSE 9000

# Status WebSocket port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9000/status || exit 1


# Set the entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
