from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Max, Avg
from django.utils import timezone

from .models import PatientProfile, DoctorProfile
from .forms import PatientProfileForm, DoctorProfileForm
from appointments.models import Appointment
from medical_records.models import MedicalRecord
from messaging.models import Message, Conversation

User = get_user_model()


def home(request):
    """Home page view"""
    return render(request, 'accounts/home.html')


@login_required
def dashboard(request):
    """Dashboard view based on user role"""
    
    user = request.user
    context = {}
    
    if user.is_patient():
        # Get patient profile
        patient_profile = PatientProfile.objects.get(user=user)
        
        # Get upcoming appointments
        upcoming_appointments = Appointment.objects.filter(
            patient=patient_profile,
            appointment_date__gte=timezone.now().date(),
            status='scheduled'
        ).order_by('appointment_date', 'appointment_time')
        
        # Get next appointment
        next_appointment = upcoming_appointments.first()
        
        # Get recent medical records
        recent_records = MedicalRecord.objects.filter(
            patient=patient_profile
        ).order_by('-created_at')[:5]
        
        # Get recent prescriptions with related records
        recent_prescriptions = MedicalRecord.objects.filter(
            patient=patient_profile,
            record_type='prescription',
            prescription__isnull=False
        ).order_by('-created_at')[:5]
        
        # Get unread messages count
        unread_messages_count = Message.objects.filter(
            conversation__participants=user,
            is_read=False
        ).exclude(sender=user).count()
        
        context = {
            'active_tab': 'dashboard',
            'upcoming_appointments_count': upcoming_appointments.count(),
            'medical_records_count': MedicalRecord.objects.filter(patient=patient_profile).count(),
            'unread_messages_count': unread_messages_count,
            'next_appointment': next_appointment,
            'recent_records': recent_records,
            'recent_prescriptions': recent_prescriptions,
        }
        
        return render(request, 'dashboard/patient.html', context)
    
    elif user.is_doctor():
        # Get doctor profile
        doctor_profile = DoctorProfile.objects.get(user=user)
        
        # Get today's appointments
        today = timezone.now().date()
        todays_appointments = Appointment.objects.filter(
            doctor=doctor_profile,
            appointment_date=today
        ).order_by('appointment_time')
        
        # Get upcoming appointments
        upcoming_appointments = Appointment.objects.filter(
            doctor=doctor_profile,
            appointment_date__gt=today,
            status='scheduled'
        ).order_by('appointment_date', 'appointment_time')
        
        # Get unique patients count
        total_patients = Appointment.objects.filter(
            doctor=doctor_profile
        ).values('patient').distinct().count()
        
        # Get recent patients
        recent_patients = PatientProfile.objects.filter(
            appointments__doctor=doctor_profile
        ).distinct().annotate(
            last_appointment=Max('appointments__appointment_date')
        ).order_by('-last_appointment')[:5]
        
        # Get unread messages
        unread_messages = Message.objects.filter(
            conversation__participants=user,
            is_read=False
        ).exclude(sender=user).count()
        
        # Get recent messages
        recent_messages = Message.objects.filter(
            conversation__participants=user
        ).exclude(sender=user).order_by('-timestamp')[:5]
        
        context = {
            'active_tab': 'dashboard',
            'todays_appointments': todays_appointments,
            'todays_appointments_count': todays_appointments.count(),
            'upcoming_appointments_count': upcoming_appointments.count(),
            'total_patients_count': total_patients,
            'unread_messages_count': unread_messages,
            'recent_patients': recent_patients,
            'recent_messages': recent_messages,
        }
        
        return render(request, 'dashboard/doctor.html', context)
    
    elif user.is_admin():
        # Get counts for admin dashboard
        total_doctors = DoctorProfile.objects.count()
        total_patients = PatientProfile.objects.count()
        
        # Get today's appointments
        today = timezone.now().date()
        todays_appointments = Appointment.objects.filter(
            appointment_date=today
        ).count()
        
        # Get total appointments
        total_appointments = Appointment.objects.count()
        completed_appointments = Appointment.objects.filter(status='completed').count()
        cancelled_appointments = Appointment.objects.filter(status='cancelled').count()
        
        # Get total medical records
        total_records = MedicalRecord.objects.count()
        
        # Get recent users
        recent_users = User.objects.all().order_by('-date_joined')[:10]
        
        # Get recent appointments
        recent_appointments = Appointment.objects.all().order_by('-created_at')[:5]
        
        # Get average rating if any feedback exists
        average_rating = 0
        if Appointment.objects.filter(feedback__isnull=False).exists():
            from appointments.models import Feedback
            average_rating = Feedback.objects.aggregate(Avg('rating'))['rating__avg'] or 0
        
        context = {
            'active_tab': 'dashboard',
            'total_doctors_count': total_doctors,
            'total_patients_count': total_patients,
            'todays_appointments_count': todays_appointments,
            'total_records_count': total_records,
            'recent_users': recent_users,
            'recent_appointments': recent_appointments,
            'total_users_count': User.objects.count(),
            'total_appointments_count': total_appointments,
            'completed_appointments_count': completed_appointments,
            'cancelled_appointments_count': cancelled_appointments,
            'average_rating': average_rating,
        }
        
        return render(request, 'dashboard/admin.html', context)
    
    # Fallback for unknown roles
    return render(request, 'accounts/home.html', context)


@login_required
def profile(request):
    """User profile view"""
    
    user = request.user
    context = {'active_tab': 'profile'}
    
    if user.is_patient():
        patient_profile = get_object_or_404(PatientProfile, user=user)
        context['profile'] = patient_profile
        return render(request, 'accounts/patient_profile.html', context)
    
    elif user.is_doctor():
        doctor_profile = get_object_or_404(DoctorProfile, user=user)
        context['profile'] = doctor_profile
        return render(request, 'accounts/doctor_profile.html', context)
    
    elif user.is_admin():
        context['user'] = user
        return render(request, 'accounts/admin_profile.html', context)
    
    return redirect('accounts:dashboard')


@login_required
def edit_profile(request):
    """Edit user profile view"""
    
    user = request.user
    context = {'active_tab': 'profile'}
    
    if user.is_patient():
        patient_profile = get_object_or_404(PatientProfile, user=user)
        
        if request.method == 'POST':
            form = PatientProfileForm(request.POST, instance=patient_profile, user=user)
            if form.is_valid():
                form.save(user=user)
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('accounts:profile')
        else:
            form = PatientProfileForm(instance=patient_profile, user=user)
        
        context['form'] = form
        return render(request, 'accounts/edit_patient_profile.html', context)
    
    elif user.is_doctor():
        doctor_profile = get_object_or_404(DoctorProfile, user=user)
        
        if request.method == 'POST':
            form = DoctorProfileForm(request.POST, instance=doctor_profile, user=user)
            if form.is_valid():
                form.save(user=user)
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('accounts:profile')
        else:
            form = DoctorProfileForm(instance=doctor_profile, user=user)
        
        context['form'] = form
        return render(request, 'accounts/edit_doctor_profile.html', context)
    
    elif user.is_admin():
        if request.method == 'POST':
            # Simple form for admin
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            
            if first_name and last_name:
                user.first_name = first_name
                user.last_name = last_name
                user.save()
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('accounts:profile')
        
        context['user'] = user
        return render(request, 'accounts/edit_admin_profile.html', context)
    
    return redirect('accounts:dashboard')


@login_required
def doctor_list(request):
    """View list of doctors for patients"""
    
    specialization = request.GET.get('specialization', '')
    name = request.GET.get('name', '')
    
    doctors = DoctorProfile.objects.all()
    
    if specialization:
        doctors = doctors.filter(specialization__icontains=specialization)
    
    if name:
        doctors = doctors.filter(
            Q(user__first_name__icontains=name) | 
            Q(user__last_name__icontains=name)
        )
    
    # Get distinct specializations for filter dropdown
    specializations = DoctorProfile.objects.values_list(
        'specialization', flat=True
    ).distinct()
    
    context = {
        'doctors': doctors,
        'specializations': specializations,
        'current_specialization': specialization,
        'current_name': name,
    }
    
    return render(request, 'accounts/doctor_list.html', context)


@login_required
def doctor_detail(request, pk):
    """View doctor details"""
    
    doctor = get_object_or_404(DoctorProfile, pk=pk)
    
    # Get doctor's availability
    available_days = [day.strip() for day in doctor.available_days.split(',')] if doctor.available_days else []
    
    # Get doctor's rating and feedback
    from appointments.models import Feedback
    feedback = Feedback.objects.filter(appointment__doctor=doctor)
    avg_rating = feedback.aggregate(Avg('rating'))['rating__avg'] or 0
    recent_feedback = feedback.order_by('-created_at')[:5]
    
    context = {
        'doctor': doctor,
        'available_days': available_days,
        'avg_rating': avg_rating,
        'feedback_count': feedback.count(),
        'recent_feedback': recent_feedback,
    }
    
    return render(request, 'accounts/doctor_detail.html', context)


@login_required
def admin_doctor_list(request):
    """Admin view for managing doctors"""
    
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('accounts:dashboard')
    
    doctors = DoctorProfile.objects.all().order_by('-created_at')
    
    # Handle status change (activate/deactivate)
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        action = request.POST.get('action')
        
        if doctor_id and action in ['activate', 'deactivate']:
            doctor = get_object_or_404(DoctorProfile, id=doctor_id)
            
            if action == 'activate':
                doctor.user.is_active = True
                doctor.user.save()
                messages.success(request, f'Dr. {doctor.user.get_full_name()} has been activated.')
            else:
                doctor.user.is_active = False
                doctor.user.save()
                messages.success(request, f'Dr. {doctor.user.get_full_name()} has been deactivated.')
    
    context = {
        'active_tab': 'doctors',
        'doctors': doctors
    }
    
    return render(request, 'accounts/admin_doctor_list.html', context)


@login_required
def admin_patient_list(request):
    """Admin view for managing patients"""
    
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('accounts:dashboard')
    
    patients = PatientProfile.objects.all().order_by('-created_at')
    
    # Handle status change (activate/deactivate)
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        action = request.POST.get('action')
        
        if patient_id and action in ['activate', 'deactivate']:
            patient = get_object_or_404(PatientProfile, id=patient_id)
            
            if action == 'activate':
                patient.user.is_active = True
                patient.user.save()
                messages.success(request, f'{patient.user.get_full_name()} has been activated.')
            else:
                patient.user.is_active = False
                patient.user.save()
                messages.success(request, f'{patient.user.get_full_name()} has been deactivated.')
    
    context = {
        'active_tab': 'patients',
        'patients': patients
    }
    
    return render(request, 'accounts/admin_patient_list.html', context)
