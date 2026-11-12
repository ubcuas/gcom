from django.urls import path

from . import views

urlpatterns = [
    path("prepare_takeoff", views.prepare_takeoff, name="acms_prepare_takeoff"),
    path("set_mode", views.set_mode, name="acms_set_mode"),
    path("arm", views.arm, name="acms_arm"),
    path("start_mission", views.start_mission, name="acms_start_mission"),
    path("rtl", views.rtl, name="acms_rtl"),
]
