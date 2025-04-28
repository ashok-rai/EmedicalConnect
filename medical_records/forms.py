from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import MedicalRecord, Prescription, Medication


class MedicalRecordForm(forms.ModelForm):
    """Form for adding and editing medical records"""
    
    class Meta:
        model = MedicalRecord
        fields = ['record_type', 'title', 'description', 'record_date', 'file', 'is_private']
        widgets = {
            'record_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.patient = kwargs.pop('patient', None)
        self.doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
    
    def clean_record_date(self):
        """Validate record date is not in the future"""
        date = self.cleaned_data.get('record_date')
        if date and date > timezone.now().date():
            raise ValidationError("Record date cannot be in the future.")
        return date
    
    def clean_file(self):
        """Validate file size and type"""
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError("File size must be under 10MB.")
            
            # Check file extension
            valid_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            import os
            ext = os.path.splitext(file.name)[1][1:].lower()
            if ext not in valid_extensions:
                raise ValidationError(f"Unsupported file extension. Use: {', '.join(valid_extensions)}")
        
        return file
    
    def save(self, commit=True):
        """Save with patient and doctor information"""
        record = super().save(commit=False)
        
        if self.patient and not record.patient:
            record.patient = self.patient
        
        if self.doctor and not record.created_by:
            record.created_by = self.doctor
        
        if commit:
            record.save()
        
        return record


class PrescriptionForm(forms.ModelForm):
    """Form for adding prescription details"""
    
    class Meta:
        model = Prescription
        fields = ['dosage_instructions', 'expiry_date', 'refills_allowed']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'dosage_instructions': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Add general dosage instructions and notes for all medications...'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
    
    def clean_expiry_date(self):
        """Validate expiry date is not in the past"""
        date = self.cleaned_data.get('expiry_date')
        if date and date < timezone.now().date():
            raise ValidationError("Expiry date cannot be in the past.")
        return date
    
    def save(self, commit=True):
        """Save with doctor information"""
        prescription = super().save(commit=False)
        
        if self.doctor and not prescription.prescribed_by:
            prescription.prescribed_by = self.doctor
        
        if commit:
            prescription.save()
        
        return prescription


class MedicationForm(forms.ModelForm):
    """Form for adding medications to a prescription"""
    
    class Meta:
        model = Medication
        fields = ['name', 'dosage', 'frequency', 'duration', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Medication name'}),
            'dosage': forms.TextInput(attrs={'placeholder': 'e.g., 500mg, 5ml'}),
            'frequency': forms.TextInput(attrs={'placeholder': 'e.g., Twice daily, Every 8 hours'}),
            'duration': forms.TextInput(attrs={'placeholder': 'e.g., 7 days, 2 weeks'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Special instructions or warnings...'}),
        }


# Formset for multiple medications
MedicationFormSet = forms.inlineformset_factory(
    Prescription,
    Medication,
    form=MedicationForm,
    extra=1,
    can_delete=True
)