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
# from pytz import timezone

from django.http import JsonResponse

import requests 
import ast
from django.db.models import Q

from .models import *
from .forms import *
from .utils import *


@login_required(login_url='login')
def Home(request):
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
        context = {'appointment': appointment, 'procedure': array, 'profile': appointment.patient, 'is_specialization': is_specialization}
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
        patient_name = f"{first_name} {last_name}"
        print(form.errors)
        if form.is_valid():
            form.save(commit=False).datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            form.save(commit=False).status = "Pending"
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
        message=f'Your appointment on {appointment.datetime.strftime("%b %e %Y %I:%M %p")} has been Completed.'
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
    return redirect('login')


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
    # for appoinment in appointments:
    #     if appoinment.procedures:
    #         print(appoinment.procedures)
    #         appoinment.procedures = ast.literal_eval(appoinment.procedures)
    if patient.is_first_time:
        return redirect('patient_profile')
    
    context = {'appointments': appointments, 'notif': notif(patient)}
    return render(request, 'patient/dashboard.html', context)


@login_required(login_url='patient_login')
def PatientProfile(request):
    patient = Patient.objects.get(user=request.user)
    if patient.date_of_birth:
        birth_date = patient.date_of_birth.strftime('%d/%m/%Y')
    else:
        birth_date = None
    print(birth_date)
    
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
    patient = Patient.objects.get(user=request.user)
    if patient.is_first_time:
        return redirect('patient_profile')
    appointments = Appointment.objects.filter(patient=patient).filter(Q(status="Approved") | Q(status="Pending")).order_by('datetime')
    context = {'appointments': appointments, 'notif': notif(patient)}
    return render(request, 'patient/appointment.html', context)

@login_required(login_url='patient_login')
def CancelAppointment(request, pk):
    patient = Patient.objects.get(user=request.user)
    appointment = Appointment.objects.get(id=pk)
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
    
    # Separate procedures for doctors and staff
    doctor_procedures = Procedures.objects.filter(category='doctor')
    staff_procedures = Procedures.objects.filter(category='staff')
    
    philippines_now = timezone.localtime(timezone.now())
    date_today = date.today()
    date_today_edited = philippines_now.strftime('%Y-%m-%d')

    if patient.is_first_time:
        return redirect('patient_profile')
    
    if request.method == 'POST':
        selects_data = request.POST.get('selects', '')
        selects_list = selects_data.split(',') if selects_data else []
        form = AppointmentFormPatient(request.POST)
        time = request.POST.get('time')
        dates = request.POST.get('date')
        procedures = str(selects_list)
        datetime_str = f"{dates} {time}"
        print(datetime_str)

        if form.is_valid():
            # Create datetime object from date and time
            appointment_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            
            # Check if appointment falls within clinic hours
            if not is_within_clinic_hours(appointment_datetime):
                messages.error(request, 'Appointment time is outside of clinic operating hours.')
                return redirect('patient_appointment_form')
            
            next_appointment_time = find_next_available_appointment_time(patient, appointment_datetime)
            
            # Check if the next available appointment time falls within clinic hours
            if not is_within_clinic_hours(next_appointment_time):
                messages.error(request, 'Next available appointment time is outside of clinic operating hours.')
                return redirect('patient_appointment_form')
            
            # Save the appointment
            appointment = form.save(commit=False)
            appointment.datetime = next_appointment_time
            appointment.status = "Pending"
            appointment.patient = patient
            appointment.procedures = procedures
            appointment.save()
            
            return redirect('patientdashboard')

    context = {
        'doctor_procedures': doctor_procedures,
        'staff_procedures': staff_procedures,
        'today_date': date_today_edited,
        'notif': notif(patient)
    }
    return render(request, 'patient/addappointment.html', context)

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
    records = Appointment.objects.filter(patient=patient).filter(Q(status="Completed") | Q(status="Cancelled") | Q(status='Declined')).order_by('datetime')
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
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save(commit=False).is_patient = True
            user = form.save()
            email = form.cleaned_data.get("username")
            Patient.objects.create(
                user=user,
                email=email,
            )
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
    assetlink = [ { "relation": ["delegate_permission/common.handle_all_urls"], "target": { "namespace": "android_app", "package_name": "xyz.appmaker.tnzpgl", "sha256_cert_fingerprints": ["6F:B0:09:F5:63:5C:3A:37:AA:E0:1B:BD:F1:A6:39:1C:61:2D:7B:F4:99:70:C3:79:BC:FB:C9:B6:2E:C9:3A:46"] } } ]
    return JsonResponse(assetlink, safe=False)


def DoctorHome(request):
    appointments = Appointment.objects.filter(status="Approved", procedures__icontains='(Doctor)').order_by('datetime')

    for appointment in appointments:
        procedures_list = [proc.strip().strip("'") for proc in appointment.procedures.strip('[]').split(',')]
        structured_procedures = []
        for procedure in procedures_list:
            parts = procedure.rsplit(' - ', 1)
            structured_procedures.append((parts[0], parts[1] if len(parts) > 1 else 'Unknown'))
        appointment.procedures = structured_procedures  # Update the procedures attribute

    context = {'appointments': appointments}
    return render(request, 'doctor/calendar.html', context)

def DoctorAppointments(request):
    appointments = Appointment.objects.filter(status='Approved', procedures__icontains='(Doctor)').order_by('datetime')
    context = {'appointments': appointments}
    return render(request, 'doctor/appointments.html', context)

def ViewDoctorAppointment(request, pk):
    appointment = get_object_or_404(Appointment, id=pk)

    # Convert procedures field to a structured format
    procedures_list = [proc.strip() for proc in appointment.procedures.strip('[]').split(',')]
    
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
        return redirect('view_doctor_appointment', pk=appointment.id)
    
    print(structured_procedures)

    return render(request, 'doctor/viewappointment.html', {
        'appointment': appointment,
        'procedures': structured_procedures,
        'profile': appointment.patient,
    })

def DoctorAppointmentHistory(request):
    appointments = Appointment.objects.filter(status='Completed', procedures__icontains='(Doctor)').order_by('datetime')
    context = {'appointments': appointments}
    return render(request, 'doctor/appointment_history.html', context)

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
    appointments = Appointment.objects.filter(status="Approved", procedures__icontains='(Staff)').order_by('datetime')

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
    appointments = Appointment.objects.filter(status='Approved', procedures__icontains='(Staff)').order_by('datetime')
    context = {'appointments': appointments}
    return render(request, 'staff/appointments.html', context)


def ViewStaffAppointment(request, pk):
    appointment = get_object_or_404(Appointment, id=pk)

    # Convert procedures field to a structured format
    procedures_list = [proc.strip() for proc in appointment.procedures.strip('[]').split(',')]
    
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
        return redirect('view_doctor_appointment', pk=appointment.id)
    
    print(structured_procedures)

    return render(request, 'staff/viewappointment.html', {
        'appointment': appointment,
        'procedures': structured_procedures,
        'profile': appointment.patient,
    })

def StaffAppointmentHistory(request):
    appointments = Appointment.objects.filter(status='Completed', procedures__icontains='(Staff)').order_by('datetime')
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