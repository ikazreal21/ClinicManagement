
from calendar import c
from dataclasses import is_dataclass
from lib2to3.pgen2 import driver
from multiprocessing import context
from operator import inv
import re
from django.shortcuts import render, redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from pytz import timezone

from django.http import JsonResponse

import requests 
import ast
from django.db.models import Q

from .models import *
from .forms import *
from .utils import *


@login_required(login_url='login')
def Home(request):
    
    patients = Patient.objects.all()

    return render(request, 'clinic/home.html', {'patients': patients})

@login_required(login_url='login')
def PatientDetails(request, pk):
    patient = Patient.objects.get(id=pk)
    medical_history = PatientMedicalHistory.objects.filter(patient=patient)
    records = PatientRecord.objects.filter(patient=patient)
    appointment = Appointment.objects.filter(patient=patient)
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
    if request.method == 'POST':
        procedures_appointment = [f'{request.POST.get("procedures")}']
        form = AppointmentForm(request.POST)
        time = request.POST.get('time')
        date = request.POST.get('date')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        procedures = str(procedures_appointment)
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
    context = {'form': AppointmentForm()}
    return render(request, 'clinic/appoinmentform.html', context)

@login_required(login_url='login')
def ApproveAppointment(request, pk):
    appointment = Appointment.objects.get(id=pk)
    appointment.status = "Approved"
    appointment.save()
    return redirect('appointments')

@login_required(login_url='login')
def CompleteAppointment(request, pk):
    appointment = Appointment.objects.get(id=pk)
    appointment.status = "Completed"
    appointment.save()
    return redirect('appointments')

@login_required(login_url='login')
def Calendar(request):
    appointments = Appointment.objects.filter(status="Approved").order_by('datetime')
    context = {'appointments': appointments}
    return render(request, 'clinic/calendar.html', context)

def Login(request):
    if request.user.is_authenticated:
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

@login_required(login_url='patient_login')
def PatientHome(request):
    patient = Patient.objects.get(user=request.user)
    appoint = Appointment.objects.filter(patient=patient)
    if patient.is_first_time:
        return redirect('patient_profile')
    context = {'appointments': appoint}
    return render(request, 'patient/dashboard.html', context)


@login_required(login_url='patient_login')
def PatientProfile(request):
    patient = Patient.objects.get(user=request.user)
    context = {'patient': patient}
    return render(request, 'patient/profile_page.html', context)

@login_required(login_url='patient_login')
def PatientAddAppointment(request):
    patient = Patient.objects.get(user=request.user)
    if request.method == 'POST':
        procedures_appointment = [f'{request.POST.get("procedures")}']
        form = AppointmentForm(request.POST)
        time = request.POST.get('time')
        date = request.POST.get('date')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        procedures = str(procedures_appointment)
        datetime_str = f"{date} {time}"
        patient_name = f"{first_name} {last_name}"
        print(form.errors)
        if form.is_valid():
            form.save(commit=False).datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            form.save(commit=False).status = "Pending"
            form.save(commit=False).patient_name = patient_name
            form.save(commit=False).patient = patient
            form.save(commit=False).patient_code = patient.patient_code
            form.save(commit=False).email = patient.email
            form.save()
            return redirect('patientdashboard')


def PatientLogin(request):
    if request.user.is_authenticated:
        return redirect('patienthome')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('patienthome')
            else:
                messages.info(request, 'Username OR password is incorrect')
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
            return redirect('login')
    else:
        form = CreateUserForm()
    return render(request, 'patient/register.html', {'form': form})


def PatientLogout(request):
    logout(request)
    return redirect('patient_login')