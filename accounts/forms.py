from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import PatientProfile, DoctorProfile

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """Custom form for user registration with role selection"""
    
    ROLE_CHOICES = (
        ('patient', 'Register as Patient'),
        ('doctor', 'Register as Doctor'),
    )
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        initial='patient',
        required=True
    )
    
    class Meta:
        model = User
        fields = ['email', 'password1', 'password2', 'role']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        
        if commit:
            user.save()
            
            # Create corresponding profile
            if user.role == 'patient':
                PatientProfile.objects.create(user=user)
            elif user.role == 'doctor':
                DoctorProfile.objects.create(user=user)
                
        return user


class PatientProfileForm(forms.ModelForm):
    """Form for patient profile information"""
    
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = PatientProfile
        fields = [
            'date_of_birth', 'gender', 'address', 'phone_number',
            'blood_group', 'allergies', 'chronic_diseases',
            'emergency_contact_name', 'emergency_contact_number'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'allergies': forms.Textarea(attrs={'rows': 3}),
            'chronic_diseases': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize form with user data"""
        
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
    
    def save(self, user=None, commit=True):
        """Save user first and last name along with profile"""
        
        profile = super().save(commit=False)
        
        if user:
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            if commit:
                user.save()
        
        if commit:
            profile.save()
        
        return profile


class DoctorProfileForm(forms.ModelForm):
    """Form for doctor profile information"""
    
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = DoctorProfile
        fields = [
            'specialization', 'license_number', 'experience_years',
            'qualification', 'bio', 'consultation_fee', 'phone_number',
            'office_address', 'available_days', 'available_time_start',
            'available_time_end'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'office_address': forms.Textarea(attrs={'rows': 3}),
            'available_time_start': forms.TimeInput(attrs={'type': 'time'}),
            'available_time_end': forms.TimeInput(attrs={'type': 'time'}),
        }
        help_texts = {
            'available_days': 'Comma separated days e.g. Monday,Tuesday,Friday',
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize form with user data"""
        
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
    
    def save(self, user=None, commit=True):
        """Save user first and last name along with profile"""
        
        profile = super().save(commit=False)
        
        if user:
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            if commit:
                user.save()
        
        if commit:
            profile.save()
        
        return profile