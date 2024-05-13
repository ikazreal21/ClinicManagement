from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from django.forms import ModelForm, ValidationError
from .models import *

class AppointmentForm(ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'

class ResultsForm(ModelForm):
    class Meta:
        model = Results
        fields = '__all__'