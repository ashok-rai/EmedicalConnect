from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Appointment, Feedback
from accounts.models import DoctorProfile


class AppointmentForm(forms.ModelForm):
    """Form for booking appointments"""
    
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'reason']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.patient = kwargs.pop('patient', None)
        super().__init__(*args, **kwargs)
        
        # Only show active doctors
        self.fields['doctor'].queryset = DoctorProfile.objects.filter(
            user__is_active=True
        )
    
    def clean_appointment_date(self):
        """Validate appointment date is not in the past"""
        date = self.cleaned_data.get('appointment_date')
        if date < timezone.now().date():
            raise ValidationError("Appointment date cannot be in the past.")
        return date
    
    def clean(self):
        """Additional validation for doctor availability"""
        cleaned_data = super().clean()
        
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('appointment_date')
        time = cleaned_data.get('time')
        
        if doctor and date and time:
            # Check if doctor is available on that day
            if doctor.available_days:
                available_days = [day.strip().lower() for day in doctor.available_days.split(',')]
                appointment_day = date.strftime('%A').lower()
                if appointment_day not in available_days:
                    self.add_error('appointment_date', f"Dr. {doctor.user.get_full_name()} is not available on {date.strftime('%A')}s.")
            
            # Check if doctor is available at that time
            if doctor.available_time_start and doctor.available_time_end:
                if time < doctor.available_time_start or time > doctor.available_time_end:
                    self.add_error('appointment_time', f"Dr. {doctor.user.get_full_name()} is only available between "
                                                  f"{doctor.available_time_start.strftime('%I:%M %p')} and "
                                                  f"{doctor.available_time_end.strftime('%I:%M %p')}.")
            
            # Check for overlapping appointments
            if not self.instance.pk:  # Only check for new appointments
                existing_appointments = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=date,
                    appointment_time=time,
                    status='scheduled'
                )
                
                if existing_appointments.exists():
                    self.add_error('appointment_time', "This time slot is already booked. Please choose another time.")
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save with patient information"""
        appointment = super().save(commit=False)
        
        try:
            if self.patient and not appointment.patient:
                appointment.patient = self.patient
        except Exception as e:
            print(f"Error: {e}")
            # Log the error or handle it as needed
            # Optionally, you can raise a ValidationError or handle it differently
        
        # if self.patient and not appointment.patient:
        #     appointment.patient = self.patient
        
        if commit:
            appointment.save()
        
        return appointment


class AppointmentRescheduleForm(forms.ModelForm):
    """Form for rescheduling appointments"""
    
    class Meta:
        model = Appointment
        fields = ['appointment_date', 'appointment_time']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def clean_appointment_date(self):
        """Validate appointment date is not in the past"""
        date = self.cleaned_data.get('appointment_date')
        if date < timezone.now().date():
            raise ValidationError("Appointment date cannot be in the past.")
        return date
    
    def clean(self):
        """Check for overlapping appointments"""
        cleaned_data = super().clean()
        
        date = cleaned_data.get('appointment_date')
        time = cleaned_data.get('appointment_time')
        
        if date and time and self.instance and self.instance.doctor:
            doctor = self.instance.doctor
            
            # Check if doctor is available on that day
            if doctor.available_days:
                available_days = [day.strip().lower() for day in doctor.available_days.split(',')]
                appointment_day = date.strftime('%A').lower()
                if appointment_day not in available_days:
                    self.add_error('appointment_date', f"Dr. {doctor.user.get_full_name()} is not available on {date.strftime('%A')}s.")
            
            # Check if doctor is available at that time
            if doctor.available_time_start and doctor.available_time_end:
                if time < doctor.available_time_start or time > doctor.available_time_end:
                    self.add_error('appointment_time', f"Dr. {doctor.user.get_full_name()} is only available between "
                                                  f"{doctor.available_time_start.strftime('%I:%M %p')} and "
                                                  f"{doctor.available_time_end.strftime('%I:%M %p')}.")
            
            # Check for overlapping appointments (excluding current appointment)
            existing_appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=date,
                appointment_time=time,
                status='scheduled'
            ).exclude(pk=self.instance.pk)
            
            if existing_appointments.exists():
                self.add_error('appointment_time', "This time slot is already booked. Please choose another time.")
        
        return cleaned_data


class AppointmentNotesForm(forms.ModelForm):
    """Form for doctor to add notes to appointments"""
    
    class Meta:
        model = Appointment
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 5}),
        }


class FeedbackForm(forms.ModelForm):
    """Form for patients to provide feedback for appointments"""
    
    class Meta:
        model = Feedback
        fields = ['rating', 'comments']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience with the doctor...'}),
        }
        labels = {
            'rating': 'How would you rate your experience? (1-5)',
            'comments': 'Additional Comments',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].help_text = '1 = Poor, 5 = Excellent'