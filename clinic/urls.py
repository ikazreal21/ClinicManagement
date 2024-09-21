from django.contrib.auth import views as auth_views
from django.urls import re_path as url

from django.urls import path
from . import views

from pwa.views import manifest, service_worker, offline


urlpatterns = [
    path("home/", views.Home, name="home"),
    path("patientdetails/<str:pk>/", views.PatientDetails, name="patientdetails"),
    path("appointments/", views.AppointmentPage, name="appointments"),
    path("addappointment/", views.AddAppointment, name="addappointment"),
    path("viewappointment/<str:pk>/", views.ViewAppointment, name="viewappointment"),
    path("approveappointment/<str:pk>/", views.ApproveAppointment, name="approveappointment"),
    path("completeappointment/<str:pk>/", views.CompleteAppointment, name="completeappointment"),
    path("calendar/", views.Calendar, name="calendar"),
    path("declineappointment/<str:pk>/", views.DeclineAppointment, name="declineappointment"),

    # Auth
    path("login/", views.Login, name="login"),
    path("logout/", views.Logout, name="logout"),

    ######################
    # Patient
    ######################
    path("patient_register/", views.PatientRegister, name="patient_register"),
    path("patient_login/", views.PatientLogin, name="patient_login"),
    path("patient_logout/", views.PatientLogout, name="patient_logout"),
    
    path("", views.Services, name="services"),
    path("dashboard", views.PatientHome, name="patientdashboard"),
    path("patient_profile/", views.PatientProfile, name="patient_profile"),
    path("patient_notifications/", views.PatientNotif, name="patient_notifications"),
    path("view_notification/<str:pk>/", views.ViewNotif, name="view_notification"),
    path("view_appointment/<str:pk>/", views.ViewPatientAppointment, name="view_appointment"),
    path("patient_appointments/", views.PatientAppointment, name="patient_appointments"),
    path("patient_appointmenthistory/", views.PatientRecords, name="patient_appointmenthistory"),    
    path("patient_appointment_form/", views.PatientAddAppointment, name="patient_appointment_form"),
    path("cancel_appointment/<str:pk>/", views.CancelAppointment, name="cancel_appointment"),

    # terms and conditions
    path("terms/", views.Terms, name="terms"),

    path(".well-known/assetlinks.json", views.AssetLink),

    url(r'^serviceworker\.js$', service_worker, name='serviceworker'),
    url(r'^manifest\.json$', manifest, name='manifest'),
    url('^offline/$', offline, name='offline')
]