from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin
from django.forms import TextInput, Textarea, CharField
from django import forms
from django.db import models
from django.contrib.auth.models import Group
from admin_interface.models import Theme

class UserAdminConfig(UserAdmin):
    model = CustomUser
    search_fields = ('username', 'email')
    list_filter = ('first_name', 'is_active', 'is_staff', 'is_patient')
    list_display = ('username', 'id', 'email','is_active', 'is_staff', 'is_patient', 'is_doctor', 'is_im', 'is_ob', 'is_gd')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_patient', 'is_doctor', 'is_im', 'is_ob', 'is_gd')}),
    )
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 20, 'cols': 60})}
    }
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'email',
                    'password1',
                    'password2',
                    'is_active',
                    'is_staff',
                    'is_patient',
                    'is_doctor',
                    'is_im',
                    'is_ob',
                    'is_gd',
                ),
            },
        ),
    )


admin.site.unregister(Group)
admin.site.unregister(Theme)  
admin.site.register(CustomUser, UserAdminConfig)
admin.site.register(Patient)
admin.site.register(PatientMedicalHistory)
admin.site.register(PatientRecord)
admin.site.register(Appointment)
admin.site.register(Results)
admin.site.register(Procedures)
admin.site.register(PatientNotification)  
admin.site.register(Announcement)


admin.site.site_header = "Asher MD Admin"
admin.site.site_title = "Asher MD Admin Portal"
admin.site.index_title = "Welcome to Asher MD Admin Portal"

# @admin.register(Billing)
# class BillingAdmin(admin.ModelAdmin):
#     readonly_fields = ["reference_number","transac_id"]


# @admin.register(ReservationFacilities)
# class ReservationFacilitiesAdmin(admin.ModelAdmin):
#     readonly_fields = ["reference_number"]