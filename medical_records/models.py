from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import PatientProfile, DoctorProfile


class MedicalRecord(models.Model):
    """Model for patient medical records"""
    
    RECORD_TYPE_CHOICES = (
        ('lab_report', 'Laboratory Report'),
        ('prescription', 'Prescription'),
        ('medical_image', 'Medical Image'),
        ('diagnosis', 'Diagnosis'),
        ('treatment_plan', 'Treatment Plan'),
        ('surgery_record', 'Surgery Record'),
        ('allergy_record', 'Allergy Record'),
        ('vaccination', 'Vaccination Record'),
        ('other', 'Other'),
    )
    
    patient = models.ForeignKey(
        PatientProfile, 
        on_delete=models.CASCADE, 
        related_name='medical_records'
    )
    created_by = models.ForeignKey(
        DoctorProfile, 
        on_delete=models.SET_NULL, 
        related_name='records_created',
        null=True, 
        blank=True
    )
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    record_date = models.DateField()
    file = models.FileField(upload_to='medical_records/', blank=True, null=True)
    is_private = models.BooleanField(default=False, help_text=_("If marked private, only the patient and their doctors can view"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-record_date', '-created_at']
    
    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.title} ({self.record_type})"


class Prescription(models.Model):
    """Model for prescriptions"""
    
    medical_record = models.OneToOneField(
        MedicalRecord, 
        on_delete=models.CASCADE, 
        related_name='prescription',
        limit_choices_to={'record_type': 'prescription'}
    )
    prescribed_by = models.ForeignKey(
        DoctorProfile, 
        on_delete=models.SET_NULL, 
        related_name='prescriptions',
        null=True
    )
    expiry_date = models.DateField(null=True, blank=True)
    dosage_instructions = models.TextField()
    refills_allowed = models.PositiveSmallIntegerField(default=0)
    
    def __str__(self):
        return f"Prescription for {self.medical_record.patient.user.get_full_name()}"


class Medication(models.Model):
    """Model for medications in a prescription"""
    
    prescription = models.ForeignKey(
        Prescription, 
        on_delete=models.CASCADE, 
        related_name='medications'
    )
    name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.dosage}"
