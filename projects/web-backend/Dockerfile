FROM python:3.12

RUN apt-get update && apt-get install -y \
    supervisor \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /src /var/log/supervisor

WORKDIR /src

COPY ./src /src
COPY pyproject.toml /src

RUN pip3 install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main

RUN cat <<EOF > /etc/supervisor/supervisord.conf
[supervisord]
nodaemon=true

[program:server]
command=poetry run python server.py
directory=/src
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/server_stdout.log
stderr_logfile=/var/log/supervisor/server_stderr.log
EOF

EXPOSE 8000

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
