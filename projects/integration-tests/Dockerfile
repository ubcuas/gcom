FROM python:3.12-slim

WORKDIR /tests

COPY requirements.txt /tests/requirements.txt
RUN pip install --no-cache-dir -r /tests/requirements.txt

COPY . /tests

ENV PYTHONUNBUFFERED=1

# Default command can be overridden by compose / CI.
CMD ["pytest", "-v"]
