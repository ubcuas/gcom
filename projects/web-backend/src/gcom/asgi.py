import os
import django
from django.core.asgi import get_asgi_application
import socketio
from websocket.sockets import sio  # your AsyncServer instance

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gcom.settings")
django.setup()

django_asgi_app = get_asgi_application()
application = socketio.ASGIApp(sio, django_asgi_app)
