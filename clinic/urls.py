from django.contrib.auth import views as auth_views

from django.urls import path
from . import views




urlpatterns = [
    path("", views.Home, name="home"),
    path("patientdetails/<str:pk>/", views.PatientDetails, name="patientdetails"),

    # Auth
    path("login/", views.Login, name="login"),
    path("logout/", views.Logout, name="logout"),
]