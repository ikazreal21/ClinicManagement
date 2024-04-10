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

@login_required(login_url='login')
def Home(request):
    patients = Patient.objects.all()
    return render(request, 'clinic/home.html', {'patients': patients})

@login_required(login_url='login')
def PatientDetails(request, pk):
    patient = Patient.objects.get(id=pk)
    medical_history = PatientMedicalHistory.objects.filter(patient=patient)
    records = PatientRecord.objects.filter(patient=patient)
    context = {'patient': patient, 'medical_history': medical_history, 'records': records}
    return render(request, 'clinic/patientdetails.html', context)

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