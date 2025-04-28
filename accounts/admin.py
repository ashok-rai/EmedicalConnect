from django.contrib import admin
from .models import User, PatientProfile, DoctorProfile

# Register your models here.
admin.site.register(User)
admin.site.register(PatientProfile)
admin.site.register(DoctorProfile)