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
    if request.method == 'POST':
        form = ResultsForm(request.POST, request.FILES)
        print(form.errors)
        if form.is_valid():
            form.save(commit=False).patient = appointment
            form.save()

            subject = f"Booking Confirmation - {appointment.patient.last_name}, {appointment.patient.first_name}"
            message = f'Hi {appointment.patient.first_name},\n\nYour appointment has been confirmed. Please find the details below:\n\nDate: {appointment.datetime.strftime("%b %e %Y")}\nTime: {appointment.datetime.strftime("%I:%M %p")}\nDoctor: {appointment.doctor}\n\nRegards,\nAsher Medical Clinic'
            
            recepients = [appointment.patient.email, ]
                        
            send_email(subject, message, recepients)
            return redirect('appointments')
    if appointment.patient:
        context = {'appointment': appointment, 'profile': appointment.patient}
    else: 
        context = {'appointment': appointment}
    return render(request, 'clinic/viewappointment.html', context)

@login_required(login_url='login')
def AddAppointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        time = request.POST.get('time')
        date = request.POST.get('date')
        datetime_str = f"{date} {time}"
        if form.is_valid():
            form.save(commit=False).datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            form.save(commit=False).status = "Pending"
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