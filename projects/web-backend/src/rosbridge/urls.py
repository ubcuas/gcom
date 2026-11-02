from django.urls import path

from . import views

urlpatterns = [
    path("prepare_takeoff", views.prepare_takeoff, name="rosbridge_prepare_takeoff"),
    path("set_mode", views.set_mode, name="rosbridge_set_mode"),
    path("arm", views.arm, name="rosbridge_arm"),
    path("start_mission", views.start_mission, name="rosbridge_start_mission"),
    path("rtl", views.rtl, name="rosbridge_rtl"),
]
