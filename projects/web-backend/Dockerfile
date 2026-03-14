FROM python:3.12

# RUN apt-get update && apt-get install -y \
#     supervisor \
#     && apt-get clean && rm -rf /var/lib/apt/lists/*

# RUN mkdir -p /src /var/log/supervisor

WORKDIR /web-backend

COPY requirements.txt ./

RUN python3 -m venv .venv
ENV PATH=".venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# RUN chmod +x /src/server.py
CMD ["python3", "/src/server.py"]
EXPOSE 8000

# build is successful (at least it seems to be)
# issue with running the application, unable to run server.py (unable to find it? or the cmd)
# docker: Error response from daemon: failed to create task for container: 
    # failed to create shim task: OCI runtime create failed: 
        # runc create failed: unable to start container process:
            #  error during container init: 
# exec: "python3": cannot run executable found relative to current directory
