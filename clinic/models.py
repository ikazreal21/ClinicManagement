from email.policy import default
from math import e
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
import locale
import uuid

from django.core.files.storage import FileSystemStorage
from django.db import models


class CustomUser(AbstractUser):
    is_patient = models.BooleanField(default=False)

class Patient(models.Model):
    GENDER = (
        ("M", "Male"),
        ("F", "Female"),
    )


    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    patient_code = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    zip_code = models.CharField(max_length=255, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER, null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=255, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=255, null=True, blank=True)
    emergency_contact_relationship = models.CharField(max_length=255, null=True, blank=True)
    patientimage = models.ImageField(upload_to='patientimages/', null=True, blank=True)
    document_id = models.CharField(max_length=255, null=True, blank=True)

    is_first_time = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'

    def __str__(self):
        return self.first_name + " " + self.last_name
    
    def date(self):
        return self.date_of_birth.strftime('%b %e %Y')
    
    
class PatientMedicalHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    patient_code = models.CharField(max_length=255, null=True, blank=True)
    medical_condition = models.CharField(max_length=255, null=True, blank=True)
    medication = models.CharField(max_length=255, null=True, blank=True)
    allergies = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Patient Medical History'
        verbose_name_plural = 'Patients Medical History'

    def __str__(self):
        return self.patient.first_name + " " + self.patient.last_name + " - " + self.medical_condition
    
class PatientRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    patient_code = models.CharField(max_length=255, null=True, blank=True)
    datetime = models.DateTimeField(null=True, blank=True)
    specialization = models.CharField(max_length=255, null=True, blank=True)
    staff_name = models.CharField(max_length=255, null=True, blank=True)
    procedures = models.CharField(max_length=255, null=True, blank=True)
    notes = models.CharField(max_length=255, null=True, blank=True)
    report = models.FileField(upload_to='reports/')

    class Meta:
        verbose_name = 'Patient Record'
        verbose_name_plural = 'Patients Record'
    
    # def __str__(self):
    #     return self.patient.first_name + " " + self.patient.last_name + " - " + self.procedures
    
    def date(self):
        return self.datetime.strftime('%b %e %Y %I:%M %p')

class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    patient_code = models.CharField(max_length=255, null=True, blank=True)
    patient_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    datetime = models.DateTimeField(null=True, blank=True)
    specialization = models.CharField(max_length=255, null=True, default="None")
    staff_name = models.CharField(max_length=255, null=True, default="None")
    procedures = models.CharField(max_length=255, null=True, blank=True)
    notes = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, default="Pending", null=True, blank=True)
    report = models.FileField(upload_to='reports/', null=True, blank=True)
    document_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        ordering = ['-datetime']
    
    # def __str__(self):
    #     if self.patient:
    #         patient_name = self.patient.first_name + " " + self.patient.last_name
    #     else:
    #         patient_name = self.patient_name
    #     return patient_name + " - " + self.procedures
    
    def date(self):
        return self.datetime.strftime('%b %e %Y %I:%M %p')

class Results(models.Model):
    patient = models.OneToOneField(Appointment, on_delete=models.CASCADE, null=True, blank=True)
    report = models.FileField(upload_to='reports/', null=True, blank=True)

    class Meta:
        verbose_name = 'Result'
        verbose_name_plural = 'Results'

    # def __str__(self):
    #     if self.patient.patient:
    #         patient_name = self.patient.patient.first_name + " " + self.patient.patient.last_name
    #     else:
    #         patient_name = self.patient.patient_name
    #     return patient_name + " - " + self.patient.procedures