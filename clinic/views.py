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

import os
import ast
import firebase_admin
from firebase_admin import db, credentials
from firebase_admin import firestore

os.path.join(settings.BASE_DIR, "credentials.json")


creds = credentials.Certificate(os.path.join(settings.BASE_DIR, "credentials.json"))
firebase_admin.initialize_app(creds)

db = firestore.client()

# data = {
#     "name": "John Doe",
#     "age": 30,
#     "city": "New York"
# }
 
# doc_ref = db.collection("resultNotif").document()
# doc_ref.set(data)
# doc_ref.id

def get_document(collection_name, document_id):

    doc_ref = db.collection(collection_name).document(document_id)

    print(doc_ref)

    doc = doc_ref.get()

    print(doc)

    if doc.exists:
        return doc.to_dict()
    else:
        print(f"Document '{document_id}' not found in collection '{collection_name}'.")
        return None


def get_all_docs(collectionName):
    # Get the reference to the collection
    #collection_ref = db.collection(collectionName)
    docs = (
            db.collection(collectionName)
            .stream()
        )
    # Iterate over the documents and store their IDs and data in a list
    documents_list = []
    for doc in docs:
        doc_data = doc.to_dict()
        doc_data['id'] = doc.id
        doc_data['docData'] = doc._data
        documents_list.append(doc_data)
    # print(documents_list)


    # Print the list of documents
    # for doc_data in documents_list:
    #     print(f"Document ID: {doc_data['id']}")
    #     print(f"Document Data: {doc_data['docData']}")
    #     print()
    return documents_list

# get_all_docs("users")
# get_all_docs("pending_appointment")

@login_required(login_url='login')
def Home(request):
    patient = get_all_docs("users")
    pending_appointment = get_all_docs("pending_appointment")
    # print(pending_appointment)

    for i in patient:
        user_check = Patient.objects.filter(document_id=i['id'])
        print(i)
        if not user_check:
            user = CustomUser.objects.create(username=i['docData']['email'], password=i['docData']['password'], is_patient=True)

            Patient.objects.create(
                user=user,
                patient_code=i['docData']['userID'],
                first_name=i['docData']['firstName'],
                last_name=i['docData']['lastName'],
                email=i['docData']['email'],
                phone=i['docData']['contactNum'],
                address=i['docData']['address'],
                city=i['docData']['city'],
                state=i['docData']['state'],
                zip_code=i['docData']['zipCode'],
                date_of_birth=i['docData']['dateOfBirth'],
                age=i['docData']['age'],
                gender=i['docData']['gender'][0],
                emergency_contact_name=i['docData']['emergencyContactName'],
                emergency_contact_phone=i['docData']['emergencyContactPhone'],
                emergency_contact_relationship=i['docData']['emergencyContactRelationship'],
                document_id=i['id']
            )
        
    for i in pending_appointment:
        # print(i['email'])
        user_check = Patient.objects.filter(user__username=i['email'])
        # print("appointment", user_check)
        if user_check:
            appoinment = Appointment.objects.filter(document_id=i['id'])
            if not appoinment:
                Appointment.objects.create(
                    user=user_check[0],
                    patient_code=i['userId'],
                    patient_name=i['first_name'] + " " + i['last_name'],
                    first_name=i['first_name'],
                    last_name=i['last_name'],
                    email=i['email'],
                    phone=i['phone'],
                    datetime=datetime.strptime(i['datetime'].strip(), '%Y-%m-%d %H:%M'),
                    procedures=str(i['procedures']),
                    notes=i['notes'],
                    status=i['status'],
                    document_id=i['id'],
                )
            else:
                continue

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
        
        data = {
            "message": message,
            "userID": appointment.patient_code,
        }
        
        doc_ref = db.collection("resultNotif").document()
        doc_ref.set(data)
        doc_ref.id

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