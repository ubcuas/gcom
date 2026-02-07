from django.urls import path
from .views import send_command

urlpatterns = [
    path("send", send_command, name="send mqtt message"),
]
