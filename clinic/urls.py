from django.contrib.auth import views as auth_views
from django.urls import re_path as url

from django.urls import path
from . import views

from pwa.views import manifest, service_worker, offline


urlpatterns = [
    path("", views.Landing, name="landing"),
    path("about/", views.About, name="about"),
    path("services", views.ServicesLanding, name="serviceslanding"),
    path("home/", views.Home, name="home"),
    path("patientdetails/<str:pk>/", views.PatientDetails, name="patientdetails"),
    path("appointments/", views.AppointmentPage, name="appointments"),
    path("addappointment/", views.AddAppointment, name="addappointment"),
    path("viewappointment/<str:pk>/", views.ViewAppointment, name="viewappointment"),
    path("approveappointment/<str:pk>/", views.ApproveAppointment, name="approveappointment"),
    path("completeappointment/<str:pk>/", views.CompleteAppointment, name="completeappointment"),
    path("calendar/", views.Calendar, name="calendar"),
    path("declineappointment/<str:pk>/", views.DeclineAppointment, name="declineappointment"),

    ######################
    path("confirmappearance/<str:pk>/", views.ConfirmAppearance, name="confirmappearance"),
    path("noappearance/<str:pk>/", views.NoAppearance, name="noappearance"),

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
    path("dashboard", views.PatientCurrentAppointment, name="patientdashboard"),
    path("patient_profile/", views.PatientProfile, name="patient_profile"),
    path("patient_notifications/", views.PatientNotif, name="patient_notifications"),
    path("view_notification/<str:pk>/", views.ViewNotif, name="view_notification"),
    path("view_appointment/<str:pk>/", views.ViewPatientAppointment, name="view_appointment"),
    path("patient_appointments/", views.PatientAppointment, name="patient_appointments"),
    path("patient_appointmenthistory/", views.PatientRecords, name="patient_appointmenthistory"),    
    path("patient_appointment_form/", views.PatientAddAppointment, name="patient_appointment_form"),
    path("cancel_appointment/<str:pk>/", views.CancelAppointment, name="cancel_appointment"),

    ######################
    # Doctor 
    ######################
    path("doctorhome/", views.DoctorHome, name="doctorhome"),
    path("doctors_appointments/", views.DoctorAppointments, name="doctors_appointments"),
    path("view_doctor_appointment/<str:pk>/", views.ViewDoctorAppointment, 
    name="view_doctor_appointment"),
    path("appoinment_history/", views.DoctorAppointmentHistory, name="appoinment_history"),
    path("complete_doctor_appointment/<str:pk>/", views.CompleteDoctorAppointment, name="complete_doctor_appointment"),
    path("follow_up/<str:pk>/", views.FollowUpAppointment, name="follow_up"),

    ######################
    # Staff
    ######################
    path("staffhome/", views.StaffHome, name="staffhome"),
    path("staff_appointments/", views.StaffAppointments, name="staff_appointments"),
    path("view_staff_appointment/<str:pk>/", views.ViewStaffAppointment, 
    name="view_staff_appointment"),
    path("staff_appointment_history/", views.StaffAppointmentHistory, name="staff_appointment_history"),
    path("complete_staff_appointment/<str:pk>/", views.CompleteStaffAppointment, name="complete_doctor_appointment"),

    path("send_email/<str:pk>/", views.SendEmail, name="send_email"),

    path("need_verification/", views.NeedVerification, name="need_verification"),

    path("verify_email/<str:verification_code>/", views.VerifyEmail, name="verify_email"),

    path("announcements/", views.Announcements, name="announcements"),

    path("reports/", views.appointment_statistics, name="reports"),

    # terms and conditions
    path("terms/", views.Terms, name="terms"),

    path('get-available-times/', views.get_available_times, name='get_available_times'),

    path(".well-known/assetlinks.json", views.AssetLink),

    url(r'^serviceworker\.js$', service_worker, name='serviceworker'),
    url(r'^manifest\.json$', manifest, name='manifest'),
    url('^offline/$', offline, name='offline')
]