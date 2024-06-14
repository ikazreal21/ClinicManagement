from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from django.forms import ModelForm, ValidationError
from .models import *

class AppointmentForm(ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'

class AppointmentFormPatient(ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'
        exclude = ['staff_name', 'specialization']

class ResultsForm(ModelForm):
    class Meta:
        model = Results
        fields = '__all__'

class CreateUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "password1", "password2"]


class PatientForm(ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'
        exclude = ['user', 'patient_code', 'is_first_time']