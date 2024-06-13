from django.contrib.auth import views as auth_views

from django.urls import path
from . import views




urlpatterns = [
    path("", views.Home, name="home"),
    path("patientdetails/<str:pk>/", views.PatientDetails, name="patientdetails"),
    path("appointments/", views.AppointmentPage, name="appointments"),
    path("addappointment/", views.AddAppointment, name="addappointment"),
    path("viewappointment/<str:pk>/", views.ViewAppointment, name="viewappointment"),
    path("approveappointment/<str:pk>/", views.ApproveAppointment, name="approveappointment"),
    path("completeappointment/<str:pk>/", views.CompleteAppointment, name="completeappointment"),
    path("calendar/", views.Calendar, name="calendar"),

    # Auth
    path("login/", views.Login, name="login"),
    path("logout/", views.Logout, name="logout"),

    ######################
    # Patient
    ######################
    path("patient_register/", views.PatientRegister, name="patient_register"),
    path("patient_login/", views.PatientLogin, name="patient_login"),
    path("patient_logout/", views.PatientLogout, name="patient_logout"),
    
    path("patients/", views.PatientHome, name="patientdashboard"),
    path("patient_profile/", views.PatientProfile, name="patient_profile"),
]