from django.contrib.auth import views as auth_views

from django.urls import path
from . import views




urlpatterns = [
    path("", views.Home, name="home"),
    path("patientdetails/<str:pk>/", views.PatientDetails, name="patientdetails"),
    path("appointments/", views.AppointmentPage, name="appointments"),
    path("viewappointment/<str:pk>/", views.ViewAppointment, name="viewappointment"),
    path("approveappointment/<str:pk>/", views.ApproveAppointment, name="approveappointment"),
    path("completeappointment/<str:pk>/", views.CompleteAppointment, name="completeappointment"),

    # Auth
    path("login/", views.Login, name="login"),
    path("logout/", views.Logout, name="logout"),
]