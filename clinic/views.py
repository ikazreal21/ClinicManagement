from django.template.defaulttags import register
from calendar import c
from dataclasses import is_dataclass
# from lib2to3.pgen2 import driver
from multiprocessing import context
from operator import inv
import re
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout


from django.utils import timezone
from django.contrib.auth.decorators import login_required
from datetime import date, datetime, time, timedelta
from django.utils.dateparse import parse_date
# from pytz import timezone

from django.utils.timezone import now

from django.http import JsonResponse

import requests 
import ast
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncMonth

from .models import *
from .forms import *
from .utils import *

DOCTOR_SCHEDULES = {
    'OB': {
        0: [(14, 0), (18, 0)],  # Monday 2-6 PM
        1: [(10, 0), (18, 0)],  # Tuesday 10 AM-6 PM
        2: [(13, 0), (18, 0)],  # Wednesday 1-6 PM
        3: [(10, 0), (18, 0)],  # Thursday 10 AM-6 PM
        4: [(14, 30), (18, 0)],  # Friday 2:30-6 PM
        5: [],
        6: [],
    },
    'IM': {
        0: [(11, 0), (18, 0)],  # Monday 11 AM-6 PM
        1: [(11, 0), (18, 0)],  # Tuesday 11 AM-6 PM
        2: [(11, 0), (18, 0)],  # Wednesday 11 AM-6 PM
        3: [],
        4: [],
        5: [],
        6: [],
    },
    'GD': {
        0: [(14, 0), (18, 0)],  # Monday to Friday 2-6 PM
        1: [(14, 0), (18, 0)],
        2: [(14, 0), (18, 0)],
        3: [(14, 0), (18, 0)],
        4: [(14, 0), (18, 0)],
        5: [],
        6: [],
    },
}

def update_appointment_status():
    """
    Update the status of appointments:
    If the status is 'Pending' and the appointment date (datetime) has passed,
    update the status to 'No Appearance'.
    """
    # Get current datetime
    current_time = now()

    # Filter appointments with 'Pending' status and datetime in the past
    pending_appointments = Appointment.objects.filter(status='Pending', datetime__lt=current_time)

    # Update the status of the filtered appointments
    for appointment in pending_appointments:
        appointment.status = 'No Appearance'
        appointment.save()

    return f"Updated {pending_appointments.count()} appointments to 'No Appearance'."

@login_required(login_url='login')
def Home(request):
    print(update_appointment_status())
    if request.user.is_authenticated:
        if request.user.is_patient:
            return redirect('patientdashboard')
        elif request.user.is_doctor:
            return redirect('doctorhome')
        elif request.user.is_staff:
            if not request.user.is_superuser:
                return redirect('staffhome')
    patients = Patient.objects.all()

    return render(request, 'clinic/home.html', {'patients': patients})

@login_required(login_url='login')
def PatientDetails(request, pk):
    patient = Patient.objects.get(id=pk)
    medical_history = PatientMedicalHistory.objects.filter(patient=patient)
    records = PatientRecord.objects.filter(patient=patient)
    appointment = Appointment.objects.filter(patient=patient).filter(status="Completed").order_by('-datetime')
    context = {'patient': patient, 'medical_history': medical_history, 'records': records, 'appointment': appointment}
    return render(request, 'clinic/patientdetails.html', context)

@login_required(login_url='login')
def AppointmentPage(request):
    appointments = Appointment.objects.all()
    context = {'appointments': appointments}
    return render(request, 'clinic/appointments.html', context)

@login_required(login_url='login')
def ViewAppointment(request, pk):
    appointment = Appointment.objects.get(id=pk)

    current_date_str = datetime.now().strftime('%b %e %Y')
    print(appointment.onlydate == current_date_str)

    array = ast.literal_eval(appointment.procedures)
    array = [item.strip() for item in array]

    is_specialization = False
    if appointment.specialization == "None" and appointment.specialization == "None":
        is_specialization = True

    if appointment.patient:
        appointment_email = appointment.patient.email
        appointment_name = f"{appointment.patient.last_name}, {appointment.patient.first_name}"
        subject_name = f"Booking Confirmation - {appointment.patient.last_name}, {appointment.patient.first_name}"
    else:
        appointment_email = appointment.email
        appointment_name = f"{appointment.patient_name}"
        subject_name = f"Booking Confirmation - {appointment.patient_name}"
    if request.method == 'POST':
        staff_name = []
        specialization = []

        for i in array:
            staff_name.append(request.POST.get(f'staff_name_{i}'))
            specialization.append(request.POST.get(f'specialization_{i}'))

        print(staff_name)
        print(specialization)


        staff_email = ""
        staff_specialization = ""
        subject = subject_name
        for i in staff_name:
            staff_email += f'{i}, '
        for i in specialization:
            staff_specialization += f'{i}, '

        appointment.specialization = staff_email
        appointment.staff_name = staff_specialization
        appointment.save()
        
        PatientNotification.objects.create(
            patient=appointment.patient,
            appointment_id=appointment.id,
            title='Your Appointment has been Updated',
            message=f'Your appointment on {appointment.datetime.strftime("%b %e %Y %I:%M %p")} has Already have a result you can received the Physical Copy on Our Clinic.'
        )

        message = f'Hi {appointment_name},\n\nYour appointment has been confirmed. Please find the details below:\n\nDate: {appointment.datetime.strftime("%b %e %Y")}\nTime: {appointment.datetime.strftime("%I:%M %p")}\nStaff: {appointment.staff_name} and Specialization: {appointment.specialization}\n\nRegards,\nAsher Medical Clinic'

        print(message)
        
        recepients = [appointment_email, ]
                    
        send_email(subject, message, recepients)

        return redirect('appointments')

    # print(array)
    if appointment.patient:
        context = {'appointment': appointment, 'procedure': array, 
                    'profile': appointment.patient, 
                   'is_specialization': is_specialization, 
                   'current_date_str': appointment.onlydate == current_date_str }
    else: 
        context = {'appointment': appointment , 'procedure': array, 'is_specialization': is_specialization}
    return render(request, 'clinic/viewappointment.html', context)

@login_required(login_url='login')
def AddAppointment(request):
    staff_procedures = Procedures.objects.filter(category='staff')
    if request.method == 'POST':
        selects_data = request.POST.get('selects', '')
        print("Selects: ", selects_data)
        selects_list = selects_data.split(',') if selects_data else []
        procedures = str(selects_list)
        
        print("Procedures: ", procedures)

        form = AppointmentForm(request.POST)
        time = request.POST.get('time')
        date = request.POST.get('date')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        datetime_str = f"{date} {time}"
        appointment_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %I:%M %p')    

        patient_name = f"{first_name} {last_name}"
        print(form.errors)
        if form.is_valid():
            form.save(commit=False).datetime = appointment_datetime
            form.save(commit=False).status = "Confirm Appearance"
            form.save(commit=False).patient_name = patient_name
            form.save(commit=False).procedures = procedures
            form.save()
            return redirect('appointments')
    context = {'form': AppointmentForm(), 'staff_procedures': staff_procedures}
    return render(request, 'clinic/appoinmentform.html', context)

@login_required(login_url='login')
def ApproveAppointment(request, pk):
    appointment = Appointment.objects.get(id=pk)
    appointment.status = "Approved"
    appointment.save()
    if appointment.is_followup:
        PatientNotification.objects.create(
        patient=appointment.patient,
        appointment_id=appointment.id,
        title='Follow Up Appointment Approved',
        message=f'Your Follow Up appointment on {appointment.datetime.strftime("%b %e %Y %I:%M %p")} has been Approved.'
        )
        return redirect('appointments')
    PatientNotification.objects.create(
        patient=appointment.patient,
        appointment_id=appointment.id,
        title='Appointment Approved',
        message=f'Your appointment on {appointment.datetime.strftime("%b %e %Y %I:%M %p")} has been Approved.'
    )
    return redirect('appointments')

@login_required(login_url='login')
def ConfirmAppearance(request, pk):
    appointment = Appointment.objects.get(id=pk)
    appointment.status = "Confirm Appearance"
    appointment.save()
    PatientNotification.objects.create(
        patient=appointment.patient,
        appointment_id=appointment.id,
        title='Confirm Appearance',
        message=f'Your appointment on {appointment.datetime.strftime("%b %e %Y %I:%M %p")} has Confirmed Appearance.'
    )
    return redirect('appointments')

@login_required(login_url='login')
def NoAppearance(request, pk):
    appointment = Appointment.objects.get(id=pk)
    appointment.status = "No Appearance"
    appointment.save()
    PatientNotification.objects.create(
        patient=appointment.patient,
        appointment_id=appointment.id,
        title='No Appearance',
        message=f'Your appointment on {appointment.datetime.strftime("%b %e %Y %I:%M %p")} has No Appearance.'
    )
    return redirect('appointments')

@login_required(login_url='login')
def DeclineAppointment(request, pk):
    if request.method == 'POST':
        reason = request.POST.get('decline_reason')
        # Retrieve and update the appointment status and reason
        appointment = Appointment.objects.get(id=pk)
        appointment.status = 'Declined'
        appointment.decline_reason = reason  # Assuming there's a field to store this
        appointment.save()

        PatientNotification.objects.create(
        patient=appointment.patient,
        appointment_id=appointment.id,
        title='Appointment Declined',
        message=f'Your appointment on {appointment.datetime.strftime("%b %e %Y %I:%M %p")} has been Declined. for the reason of {reason}'
        )
        
        return redirect('appointments')
    # appointment = Appointment.objects.get(id=pk)
    # appointment.status = "Declined"
    # appointment.save()
    # PatientNotification.objects.create(
    #     patient=appointment.patient,
    #     appointment_id=appointment.id,
    #     title='Appointment Declined',
    #     message=f'Your appointment on {appointment.datetime.strftime("%b %e %Y %I:%M %p")} has been Declined.'
    # )
    # return redirect('appointments')

@login_required(login_url='login')
def CompleteAppointment(request, pk):
    appointment = Appointment.objects.get(id=pk)
    appointment.status = "Completed"
    appointment.save()
    PatientNotification.objects.create(
        patient=appointment.patient,
        appointment_id=appointment.id,
        title='Appointment Completed',
        message=f'Your appointment for your requested procedure on {appointment.datetime.strftime("%b %e %Y %I:%M %p")} has been Completed.'
    )
    return redirect('appointments')

@login_required(login_url='login')
def Calendar(request):
    appointments = Appointment.objects.filter(status="Approved").order_by('datetime')

    for appointment in appointments:
        procedures_list = [proc.strip().strip("'") for proc in appointment.procedures.strip('[]').split(',')]
        structured_procedures = []
        for procedure in procedures_list:
            parts = procedure.rsplit(' - ', 1)
            structured_procedures.append((parts[0], parts[1] if len(parts) > 1 else 'Unknown'))
        appointment.procedures = structured_procedures  # Update the procedures attribute

    context = {'appointments': appointments}
    return render(request, 'clinic/calendar.html', context)

def Login(request):
    if request.user.is_authenticated:
        if request.user.is_doctor:
            return redirect('patientdashboard')
        return redirect('home')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)

                return redirect('home')
            else:
                messages.info(request, 'Username OR password is incorrect')
    context = {}
    return render(request, 'clinic/login.html', context)

def Logout(request):
    logout(request)
    return redirect('landing')


###################
# Patient
###################
def is_within_clinic_hours(datetime_obj):
    """Check if the given datetime is within clinic operating hours."""
    if datetime_obj.weekday() < 5:  # Monday to Friday
        return datetime_obj.time() >= time(7, 30) and datetime_obj.time() <= time(18, 0)
    elif datetime_obj.weekday() == 5:  # Saturday
        return datetime_obj.time() >= time(8, 0) and datetime_obj.time() <= time(17, 0)
    else:
        return False  # Closed on Sundays

def find_next_available_appointment_time(patient, appointment_datetime):
    """Find the next available appointment time with 30-minute interval."""
    latest_appointment = Appointment.objects.filter(
        datetime=appointment_datetime
    ).filter(Q(status="Approved") | Q(status="Pending")).order_by('datetime').first()
    
    if latest_appointment:
        print(latest_appointment.datetime)
        next_appointment_time = latest_appointment.datetime + timedelta(minutes=30)

        PatientNotification.objects.create(
            patient=patient,
            appointment_id=latest_appointment.id,
            title='Appointment Rescheduled',
            message=f'Your appointment has been rescheduled to {next_appointment_time.strftime("%b %e %Y %I:%M %p")}.'
        )
    else:
        print(appointment_datetime)
        next_appointment_time = appointment_datetime
    
    # while next_appointment_time and not is_within_clinic_hours(next_appointment_time):
    #     next_appointment_time += timedelta(minutes=30)
    
    return next_appointment_time

@register.filter # register the template filter with django
def get_string_as_list(value): # Only one argument.
    """Evaluate a string if it contains []"""
    
    array = ast.literal_eval(value)
    array = [item.strip() for item in array]
    return array

def notif(patient):
    notif = PatientNotification.objects.filter(patient=patient).order_by('-id')[:3]
    return notif


@login_required(login_url='patient_login')
def PatientHome(request):
    patient = Patient.objects.get(user=request.user)
    appointments = Appointment.objects.filter(patient=patient, status="Approved").order_by('datetime')
    announcements = Announcement.objects.all()
    # for appoinment in appointments:
    #     if appoinment.procedures:
    #         print(appoinment.procedures)
    #         appoinment.procedures = ast.literal_eval(appoinment.procedures)
    if patient.is_verified:
        if patient.is_first_time:
            return redirect('patient_profile')
    else:
        return redirect('need_verification')

    context = {'announcements': announcements}
    return render(request, 'patient/announcements.html', context)
    # context = {'appointments': appointments, 'notif': notif(patient)}
    # return render(request, 'patient/dashboard.html', context)


@login_required(login_url='patient_login')
def PatientProfile(request):
    patient = Patient.objects.get(user=request.user)
    if patient.date_of_birth:
        birth_date = patient.date_of_birth.strftime('%d/%m/%Y')
    else:
        birth_date = None
    print(patient)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES, instance=patient)
        print(form)
        if form.is_valid():
            patient_profile = form.save()
            patient_profile.is_first_time = False
            patient_profile.save()
            return redirect('patientdashboard')
    context = {'patient': patient , 'birth_date': birth_date, 'notif': notif(patient) }
    return render(request, 'patient/profile_page.html', context)

@login_required(login_url='patient_login')
def PatientAppointment(request):
    if request.user.is_superuser:
        return redirect('appointments')
    patient = Patient.objects.get(user=request.user)
    if patient.is_first_time:
        return redirect('patient_profile')
    appointments = Appointment.objects.filter(patient=patient).filter(Q(status="Approved") | Q(status="Pending") | Q(status="Confirm Appearance")).order_by('datetime')
    context = {'appointments': appointments, 'notif': notif(patient)}
    return render(request, 'patient/appointment.html', context)

@login_required(login_url='patient_login')
def CancelAppointment(request, pk):
    if request.method == 'POST':
        reason = request.POST.get('cancel_reason')

        appointment = Appointment.objects.get(id=pk)
        patient = Patient.objects.get(user=appointment.patient.user)
        
        appointment.status = "Cancelled"
        appointment.reasons = reason
        appointment.save()
        PatientNotification.objects.create(
            patient=patient,
            appointment_id=appointment.id,
            title='Appointment Cancelled',
            message=f'Your appointment on {appointment.datetime.strftime("%b %e %Y %I:%M %p")} has been Cancelled. for the Reason of: {reason}'
        )
        return redirect('patient_appointments')

    appointment = Appointment.objects.get(id=pk)
    patient = Patient.objects.get(user=appointment.patient.user)

    appointment.status = "Cancelled"
    appointment.save()
    PatientNotification.objects.create(
        patient=patient,
        appointment_id=appointment.id,
        title='Appointment Cancelled',
        message=f'Your appointment on {appointment.datetime.strftime("%b %e %Y %I:%M %p")} has been Cancelled.'
    )
    return redirect('patient_appointments')

@login_required(login_url='patient_login')
def PatientAddAppointment(request):
    patient = Patient.objects.get(user=request.user)
    # doctor_procedures = Procedures.objects.filter(category='doctor')
    doctor_procedures = {
        'OB': list(Procedures.objects.filter(category='doctor', doctor_procedure='OB').values('name', 'doctor_procedure')),
        'IM': list(Procedures.objects.filter(category='doctor', doctor_procedure='IM').values('name', 'doctor_procedure')),
        'GD': list(Procedures.objects.filter(category='doctor', doctor_procedure='GD').values('name', 'doctor_procedure'))
    }
    
    if patient.is_first_time:
        return redirect('patient_profile')

    if request.method == 'POST':
        doctor = request.POST.get('doctor')
        selects_data = request.POST.get('selects', '')
        selects_list = selects_data.split(',') if selects_data else []
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        
        if not doctor or not date_str or not time_str:
            messages.error(request, "Please fill all fields.")
            return redirect('patient_appointment_form')
        
        datetime_str = f"{date_str} {time_str}"
        try:
            appointment_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %I:%M %p')
        except ValueError:
            messages.error(request, "Invalid date or time format.")
            return redirect('patient_appointment_form')
        
        # Validate the appointment time with the doctor's schedule
        schedule = DOCTOR_SCHEDULES.get(doctor)
        if not schedule:
            messages.error(request, "Selected doctor has no available schedule.")
            return redirect('patient_appointment_form')
        
        weekday = appointment_datetime.weekday()
        start_end_times = schedule.get(weekday)
        
        if not start_end_times:
            messages.error(request, "Doctor is not available on the selected date.")
            return redirect('patient_appointment_form')
        
        if not is_within_time_range(appointment_datetime, start_end_times):
            messages.error(request, "Selected time is outside the doctor's working hours.")
            return redirect('patient_appointment_form')
        
        # Create and save the appointment
        form = AppointmentFormPatient(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.datetime = appointment_datetime
            appointment.status = "Pending"
            appointment.patient = patient
            appointment.procedures = str(selects_list)
            appointment.save()
            return redirect('patientdashboard')

    context = {
        'doctor_procedures_json': doctor_procedures,
        'today_date': timezone.localtime(timezone.now()).strftime('%Y-%m-%d'),
    }
    return render(request, 'patient/addappointment.html', context)

def is_within_time_range(appointment_datetime, start_end_times):
    start, end = start_end_times
    start_time = appointment_datetime.replace(hour=start[0], minute=start[1])
    end_time = appointment_datetime.replace(hour=end[0], minute=end[1])
    return start_time <= appointment_datetime <= end_time

@login_required(login_url='patient_login')
def PatientNotif(request):
    patient = Patient.objects.get(user=request.user)
    if patient.is_first_time:
        return redirect('patient_profile')
    appointments = Appointment.objects.filter(patient=patient)
    PatientNotification.objects.filter(patient=patient).update(is_read=True)
    notifs = PatientNotification.objects.filter(patient=patient).order_by('-id')
    context = {'notifs': notifs, 'notif': notif(patient)}
    return render(request, 'patient/notification.html', context)

@login_required(login_url='patient_login')
def ViewNotif(request, pk):
    patient = Patient.objects.get(user=request.user)
    if patient.is_first_time:
        return redirect('patient_profile')
    notif = PatientNotification.objects.get(id=pk)
    notif.is_read = True
    notif.save()
    context = {'notifs': notif}
    return render(request, 'patient/viewnotification.html', context)


@login_required(login_url='patient_login')
def ViewPatientAppointment(request, pk):
    appointment = Appointment.objects.get(id=pk)
    notifs = PatientNotification.objects.filter(appointment_id=pk).order_by('-id')
    context = {'appointment': appointment , 'notifs': notifs, 'notif': notif(appointment.patient)}
    print(appointment.procedures)
    return render(request, 'patient/viewappointments.html', context)
        

@login_required(login_url='patient_login')
def PatientRecords(request):
    patient = Patient.objects.get(user=request.user)
    if patient.is_first_time:
        return redirect('patient_profile')
    records = Appointment.objects.filter(patient=patient).filter(Q(status="Completed") | Q(status="Cancelled") | Q(status='Declined') | Q(status='No Appearance')).order_by('datetime')
    context = {'appointments': records}
    return render(request, 'patient/appointment_history.html', context)

@login_required(login_url='patient_login')
def Services(request):
    services = Procedures.objects.all()
    context = {'services': services}
    return render(request, 'patient/services.html', context)


def PatientLogin(request):
    if request.user.is_authenticated:
        if request.user.is_patient:
            return redirect('patientdashboard')
        elif request.user.is_doctor:
            return redirect('doctorhome')
        elif request.user.is_staff:
            if not request.user.is_superuser:
                return redirect('staffhome')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_patient:
                    return redirect('patientdashboard')
                elif user.is_doctor:
                    return redirect('doctorhome')
                elif user.is_staff:
                    if not user.is_superuser:
                        return redirect('staffhome')
            else:
                messages.error(request, 'Username OR password is incorrect')
    return render(request, 'patient/login.html')
    


def PatientRegister(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        form = CreateUserForm(request.POST)
        
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
        elif len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
        elif CustomUser.objects.filter(username=username).exists():
            messages.error(request, "This email is already registered.")
        else:
            verification_code = create_rand_id()
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save(commit=False).is_patient = True
                user = form.save()
                email = form.cleaned_data.get("username")
                Patient.objects.create(
                    user=user,
                    email=email,
                    verification_code=verification_code
                )
                send_verification_email(email, user, verification_code)
                return redirect('patient_login')
            else:
                messages.error(request, 'An error occured')
    else:
        form = CreateUserForm()
    return render(request, 'patient/register.html', {'form': form})


def PatientLogout(request):
    logout(request)
    return redirect('patient_login')


def Terms(request):
    return render(request, 'patient/terms.html')

def AssetLink(request):
    assetlink = [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
            "namespace": "android_app",
            "package_name": "xyz.appmaker.doigcr",
            "sha256_cert_fingerprints": ["1D:A3:1A:C1:F0:D0:74:51:89:E3:49:62:69:BA:08:94:46:2A:A4:4B:89:2E:FC:AC:3B:AA:81:D5:0A:07:03:61"]
            }
        }
    ]
    return JsonResponse(assetlink, safe=False)


@login_required(login_url='patient_login')
def DoctorHome(request):
    if request.user.is_im:
        appointments = Appointment.objects.filter(Q(status="Approved") | Q(status="Confirm Appearance"), Q(procedures__icontains='(Doctor)') &  Q(procedures__icontains='IM')).order_by('datetime')
        doctor_speciality = 'IM'
    elif request.user.is_gd:
        appointments = Appointment.objects.filter(Q(status="Approved") | Q(status="Confirm Appearance"), Q(procedures__icontains='(Doctor)') |  Q(procedures__icontains='GD')).order_by('datetime')
        doctor_speciality = 'GD'
    elif request.user.is_ob:
        appointments = Appointment.objects.filter(Q(status="Approved") | Q(status="Confirm Appearance"), Q(procedures__icontains='(Doctor)') |  Q(procedures__icontains='OB')).order_by('datetime')
        doctor_speciality = 'OB'
    else:
        appointments = []
        doctor_speciality = 'Unknown'

    for appointment in appointments:
        procedures_list = [proc.strip().strip("'") for proc in appointment.procedures.strip('[]').split(',')]
        structured_procedures = []
        for procedure in procedures_list:
            print("procedure", procedure)
            parts = procedure.rsplit(' - ', 1)
            if doctor_speciality in parts[0]:
                structured_procedures.append((parts[0], parts[1] if len(parts) > 1 else 'Unknown'))
            print("structured_procedures", structured_procedures)
        appointment.procedures = structured_procedures  # Update the procedures attribute

    context = {'appointments': appointments}
    return render(request, 'doctor/calendar.html', context)

@login_required(login_url='patient_login')
def FollowUpAppointment(request, pk):
    patient = Patient.objects.get(id=pk)
    if request.user.is_im:
        doctor = 'IM'
    elif request.user.is_gd:
        doctor = 'GD'
    elif request.user.is_ob:
        doctor = 'OB'
    else:
        doctor_procedures = []

    doctor_procedures = {
        'OB': list(Procedures.objects.filter(category='doctor', doctor_procedure='OB').values('name', 'doctor_procedure')),
        'IM': list(Procedures.objects.filter(category='doctor', doctor_procedure='IM').values('name', 'doctor_procedure')),
        'GD': list(Procedures.objects.filter(category='doctor', doctor_procedure='GD').values('name', 'doctor_procedure'))
    }

    if request.method == 'POST':
        selects_data = request.POST.get('selects', '')
        selects_list = selects_data.split(',') if selects_data else []
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        
        if not doctor or not date_str or not time_str:
            messages.error(request, "Please fill all fields.")
            return redirect('patient_appointment_form')
        
        datetime_str = f"{date_str} {time_str}"
        try:
            appointment_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %I:%M %p')
        except ValueError:
            messages.error(request, "Invalid date or time format.")
            return redirect('patient_appointment_form')
        
        # Validate the appointment time with the doctor's schedule
        schedule = DOCTOR_SCHEDULES.get(doctor)
        if not schedule:
            messages.error(request, "Selected doctor has no available schedule.")
            return redirect('patient_appointment_form')
        
        weekday = appointment_datetime.weekday()
        start_end_times = schedule.get(weekday)
        
        if not start_end_times:
            messages.error(request, "Doctor is not available on the selected date.")
            return redirect('patient_appointment_form')
        
        if not is_within_time_range(appointment_datetime, start_end_times):
            messages.error(request, "Selected time is outside the doctor's working hours.")
            return redirect('patient_appointment_form')
        
        # Create and save the appointment
        form = AppointmentFormPatient(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.datetime = appointment_datetime
            appointment.status = "Pending"
            appointment.patient = patient
            appointment.is_followup = True
            appointment.procedures = str(selects_list)
            appointment.save()
            return redirect('doctorhome')

    context = {
        'doctor' : doctor,
        'doctor_procedures_json': doctor_procedures,
        'today_date': timezone.localtime(timezone.now()).strftime('%Y-%m-%d'),
    }
    return render(request, 'doctor/followup_appointment.html', context)

def is_within_time_range(appointment_datetime, start_end_times):
    start, end = start_end_times
    start_time = appointment_datetime.replace(hour=start[0], minute=start[1])
    end_time = appointment_datetime.replace(hour=end[0], minute=end[1])
    return start_time <= appointment_datetime <= end_time

@login_required(login_url='patient_login')
def DoctorAppointments(request):
    if request.user.is_im:
        appointments = Appointment.objects.filter(Q(status="Approved") | Q(status="Pending") | Q(status="Confirm Appearance"), Q(procedures__icontains='(Doctor)') &  Q(procedures__icontains='IM')).order_by('datetime')
    elif request.user.is_gd:
        appointments = Appointment.objects.filter(Q(status="Approved") | Q(status="Pending") | Q(status="Confirm Appearance"), Q(procedures__icontains='(Doctor)') &  Q(procedures__icontains='GD')).order_by('datetime')
    elif request.user.is_ob:
        appointments = Appointment.objects.filter(Q(status="Approved") | Q(status="Pending") | Q(status="Confirm Appearance"), Q(procedures__icontains='(Doctor)') &  Q(procedures__icontains='OB')).order_by('datetime')
    else:
        appointments = []
    context = {'appointments': appointments}
    return render(request, 'doctor/appointments.html', context)

def ViewDoctorAppointment(request, pk):
    appointment = get_object_or_404(Appointment, id=pk)

    if request.user.is_im:
        doctor_speciality = 'IM'
    elif request.user.is_gd:
        doctor_speciality = 'GD'
    elif request.user.is_ob:
        doctor_speciality = 'OB'
    else:
        doctor_speciality = 'Unknown'

    # Convert procedures field to a structured format
    procedures_list = [proc.strip() for proc in appointment.procedures.strip('[]').split(',')]
    
    structured_procedures = []
    for procedure in procedures_list:
        procedure = procedure.strip().strip("'")
        if ' - ' in procedure:
            proc_name, proc_status = procedure.rsplit(' - ', 1)
        else:
            proc_name, proc_status = procedure, 'Pending'  # Default status
        if  doctor_speciality in proc_name: # Default status
            structured_procedures.append((proc_name.strip(), proc_status.strip()))
        # structured_procedures.append((proc_name.strip(), proc_status.strip()))

    if request.method == 'POST':
        updated_procedures = []
        for idx, procedure in enumerate(structured_procedures):
            status_key = f'procedure_status_{idx + 1}'
            proc_name, _ = procedure  # Unpacking
            if status_key in request.POST:
                new_status = request.POST[status_key]
                updated_procedure = f'{proc_name} - {new_status}'
                updated_procedures.append(updated_procedure)

        # Save the updated procedures back to the appointment
        appointment.procedures = str(updated_procedures)
        appointment.save()
        
        messages.success(request, "Procedures updated successfully.")
        return redirect('view_doctor_appointment', pk=appointment.id)
    
    print(structured_procedures)

    return render(request, 'doctor/viewappointment.html', {
        'appointment': appointment,
        'procedures': structured_procedures,
        'profile': appointment.patient,
    })

@login_required(login_url='patient_login')
def DoctorAppointmentHistory(request):
    if request.user.is_im:
        appointments = Appointment.objects.filter(Q(status="Completed") | Q(status="Cancelled") | Q(status='Declined') | Q(status='No Appearance') | Q(status='Results Ready'), Q(procedures__icontains='(Doctor)') & Q(procedures__icontains='IM')).order_by('-datetime')
    elif request.user.is_gd: 
        appointments = Appointment.objects.filter(Q(status="Completed") | Q(status="Cancelled") | Q(status='Declined') | Q(status='No Appearance') | Q(status='Results Ready'), Q(procedures__icontains='(Doctor)') &  Q(procedures__icontains='GD')).order_by('-datetime')
    elif request.user.is_ob:
        appointments = Appointment.objects.filter(Q(status="Completed") | Q(status="Cancelled") | Q(status='Declined') | Q(status='No Appearance') | Q(status='Results Ready'), Q(procedures__icontains='(Doctor)') &  Q(procedures__icontains='OB')).order_by('-datetime')
    else:
        appointments = []
    context = {'appointments': appointments}
    return render(request, 'doctor/appointment_history.html', context)

@login_required(login_url='patient_login')
def CompleteDoctorAppointment(request, pk):
    appointment = get_object_or_404(Appointment, id=pk)
    appointment.status = 'Completed'
    appointment.save()
    messages.success(request, 'Appointment marked as completed.')
    PatientNotification.objects.create(
        patient=appointment.patient,
        appointment_id=appointment.id,
        title='Appointment Completed',
        message=f'Your appointment on {appointment.datetime.strftime("%b %e %Y %I:%M %p")} has been Completed.'
    )
    return redirect('doctor_appointments')

# Staff
def StaffHome(request):
    appointments = Appointment.objects.filter(Q(status="Approved") | Q(status="Confirm Appearance"), procedures__icontains='(Staff)').order_by('datetime')

    for appointment in appointments:
        procedures_list = [proc.strip().strip("'") for proc in appointment.procedures.strip('[]').split(',')]
        structured_procedures = []
        for procedure in procedures_list:
            parts = procedure.rsplit(' - ', 1)
            structured_procedures.append((parts[0], parts[1] if len(parts) > 1 else 'Unknown'))
        appointment.procedures = structured_procedures  # Update the procedures attribute

    context = {'appointments': appointments}
    return render(request, 'staff/calendar.html', context)

def StaffAppointments(request):
    appointments = Appointment.objects.filter(Q(status="Approved") | Q(status="Pending") | Q(status="Confirm Appearance"), procedures__icontains='(Staff)').order_by('-datetime')
    context = {'appointments': appointments}
    return render(request, 'staff/appointments.html', context)


def ViewStaffAppointment(request, pk):
    appointment = get_object_or_404(Appointment, id=pk)

    # Convert procedures field to a structured format
    procedures_list = [proc.strip() for proc in appointment.procedures.strip('[]').split(',')]
    print(procedures_list)
    structured_procedures = []
    for procedure in procedures_list:
        procedure = procedure.strip().strip("'")
        if ' - ' in procedure:
            proc_name, proc_status = procedure.rsplit(' - ', 1)
        else:
            proc_name, proc_status = procedure, 'Pending'  # Default status
        structured_procedures.append((proc_name.strip(), proc_status.strip()))

    if request.method == 'POST':
        updated_procedures = []
        for idx, procedure in enumerate(structured_procedures):
            status_key = f'procedure_status_{idx + 1}'
            proc_name, _ = procedure  # Unpacking
            if status_key in request.POST:
                new_status = request.POST[status_key]
                updated_procedure = f'{proc_name} - {new_status}'
                updated_procedures.append(updated_procedure)

        # Save the updated procedures back to the appointment
        appointment.procedures = str(updated_procedures)
        appointment.save()
        
        messages.success(request, "Procedures updated successfully.")
        return redirect('view_staff_appointment', pk=appointment.id)
    
    print(structured_procedures)

    return render(request, 'staff/viewappointment.html', {
        'appointment': appointment,
        'procedures': structured_procedures,
        'profile': appointment.patient,
    })

def StaffAppointmentHistory(request):
    appointments = Appointment.objects.filter(Q(status="Completed") | Q(status="Cancelled") | Q(status='Declined') | Q(status='No Appearance') | Q(status='Results Ready'), procedures__icontains='(Staff)').order_by('-datetime')
    context = {'appointments': appointments}
    return render(request, 'staff/appointment_history.html', context)

def CompleteStaffAppointment(request, pk):
    appointment = get_object_or_404(Appointment, id=pk)
    appointment.status = 'Completed'
    appointment.save()
    messages.success(request, 'Appointment marked as completed.')
    PatientNotification.objects.create(
        patient=appointment.patient,
        appointment_id=appointment.id,
        title='Appointment Completed',
        message=f'Your appointment on {appointment.datetime.strftime("%b %e %Y %I:%M %p")} has been Completed.'
    )
    return redirect('staff_appointments')



def SendEmail(request, pk):
    appointment = get_object_or_404(Appointment, id=pk)
    appointment.status = "Results Ready"
    appointment.save()
    full_name = appointment.first_name + ' ' + appointment.last_name
    send_results_ready_email(appointment.email, full_name, appointment.date())
    return redirect('viewappointment', pk=appointment.id)


def VerifyEmail(request, verification_code):
    patient = Patient.objects.get(verification_code=verification_code)
    patient.is_verified = True
    patient.save()
    return render(request, 'patient/verified.html')

def send_verification_email(email, user, verification_code):
    subject = 'Email Verification'
    message = f'Hi {user.username},\n\nPlease click the link below to verify your email address:\n\nhttps://ashermd.ellequin.com/verify_email/{verification_code}'
    send_email(subject, message, [email])

def Landing(request):
    services = Procedures.objects.filter(category='staff')[0:3]
    context = {'services': services}
    print(services)
    return render(request, 'clinic/landing.html', context)

def About(request):
    return render(request, 'clinic/about.html')

def ServicesLanding(request):
    services = Procedures.objects.filter(category='staff')
    context = {'services': services}
    print(services)
    return render(request, 'clinic/services.html', context)

def NeedVerification(request):
    logout(request)
    return render(request, 'patient/need_verification.html')

def Announcements(request):
    announcements = Announcement.objects.all()
    context = {'announcements': announcements}
    return render(request, 'patient/announcements.html', context)

def PatientCurrentAppointment(request):
    patient = Patient.objects.get(user=request.user)
    appointments = Appointment.objects.filter(patient=patient).filter(Q(status="Approved") |  Q(status="Confirm Appearance")).order_by('datetime')
    # for appoinment in appointments:
    #     if appoinment.procedures:
    #         print(appoinment.procedures)
    #         appoinment.procedures = ast.literal_eval(appoinment.procedures)
    if patient.is_verified:
        if patient.is_first_time:
            return redirect('patient_profile')
    else:
        return redirect('need_verification')

    context = {'appointments': appointments, 'notif': notif(patient)}
    return render(request, 'patient/dashboard.html', context)


def appointment_statistics(request):
    # Get current date and time
    now = timezone.now()
    start_of_month = now.replace(day=1)

    # Filter appointments for the current month
    current_month_appointments = Appointment.objects.filter(datetime__gte=start_of_month)

    # Total appointments
    total_appointments = Appointment.objects.count()

    # Appointments approved this month
    approved_this_month = current_month_appointments.filter(status="Approved").count()

    # Appointments completed this month
    completed_this_month = current_month_appointments.filter(status="Completed").count()

    # Appointments declined this month
    declined_this_month = current_month_appointments.filter(status="Declined").count()

    # Average appointments per month (across all months)
    avg_appointments_per_month = Appointment.objects.annotate(
        month=TruncMonth('datetime')
    ).values('month').annotate(total=Count('id')).aggregate(avg=Avg('total'))['avg']

    # Average declined appointments per month
    avg_declined_per_month = Appointment.objects.filter(status="Declined").annotate(
        month=TruncMonth('datetime')
    ).values('month').annotate(total=Count('id')).aggregate(avg=Avg('total'))['avg']

    context = {
        'total_appointments': total_appointments,
        'approved_this_month': approved_this_month,
        'completed_this_month': completed_this_month,
        'declined_this_month': declined_this_month,
        'avg_appointments_per_month': avg_appointments_per_month,
        'avg_declined_per_month': avg_declined_per_month,
    }

    return render(request, 'clinic/reports.html', context)


def get_available_times(request):
    doctor = request.GET.get('doctor')
    date_str = request.GET.get('date')
    
    # Validate input parameters
    if not doctor or not date_str:
        return JsonResponse({'error': 'Invalid doctor or date parameter'}, status=400)
    
    selected_date = parse_date(date_str)
    if not selected_date:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Retrieve the schedule for the selected doctor
    schedule = DOCTOR_SCHEDULES.get(doctor)
    if not schedule:
        return JsonResponse({'error': 'No schedule found for the selected doctor'}, status=400)
    
    # Determine the doctor's working hours for the selected day
    weekday = selected_date.weekday()  # Monday = 0, Sunday = 6
    print(weekday)
    start_end_times = schedule.get(weekday)
    if not start_end_times:
        return JsonResponse({'times': [], 'message': 'Doctor is unavailable on this day'})
    
    # Generate available time slots within the doctor's schedule
    available_times = []
    start_time, end_time = start_end_times
    current_time = datetime.combine(selected_date, datetime.min.time()).replace(hour=start_time[0], minute=start_time[1])
    end_time = datetime.combine(selected_date, datetime.min.time()).replace(hour=end_time[0], minute=end_time[1])
    
    # Retrieve booked appointments for the selected doctor on this date
    booked_times = Appointment.objects.filter(
        datetime__date=selected_date,
        doctor=doctor
    ).values_list('datetime', flat=True)
    
    # Convert booked_times to naive datetime objects
    booked_times_naive = [bt.replace(tzinfo=None) for bt in booked_times]
    
    # Generate 30-minute intervals, skipping already booked times
    while current_time < end_time:
        if current_time not in booked_times_naive:
            available_times.append(current_time.strftime('%I:%M %p'))
        current_time += timedelta(minutes=30)
    
    return JsonResponse({'times': available_times})