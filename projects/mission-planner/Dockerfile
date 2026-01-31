FROM python:3.12-slim

# Minimal OS deps; pymavlink can require build tooling in some environments.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

EXPOSE 9000

CMD ["python", "-u", "/app/src/main.py"]
