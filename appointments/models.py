from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import PatientProfile, DoctorProfile


class Appointment(models.Model):
    """Model for appointment bookings"""
    
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    )
    
    patient = models.ForeignKey(
        PatientProfile, 
        on_delete=models.CASCADE, 
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        DoctorProfile, 
        on_delete=models.CASCADE, 
        related_name='appointments'
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='scheduled'
    )
    notes = models.TextField(blank=True, help_text=_("Doctor's notes about the appointment"))
    meeting_link = models.URLField(blank=True, help_text=_("Zoom or other video conference link for telemedicine"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
        unique_together = ['doctor', 'appointment_date', 'appointment_time']
    
    def __str__(self):
        return f"{self.patient.user.get_full_name()} - Dr. {self.doctor.user.get_full_name()} ({self.appointment_date})"


class Feedback(models.Model):
    """Patient feedback for appointments"""
    
    appointment = models.OneToOneField(
        Appointment, 
        on_delete=models.CASCADE, 
        related_name='feedback'
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text=_("Rating from 1 to 5, where 5 is the best")
    )
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback for {self.appointment}"
