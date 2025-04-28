from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.db.models import Q

from .models import Appointment, Feedback
from .forms import AppointmentForm, AppointmentRescheduleForm, AppointmentNotesForm, FeedbackForm
from accounts.models import PatientProfile, DoctorProfile
from messaging.models import Notification


@login_required
def book_appointment(request):
    """View for booking new appointments"""
    
    # Check if user is a patient
    if not request.user.is_patient():
        messages.error(request, "Only patients can book appointments.")
        return redirect('accounts:dashboard')
    
    # Get patient profile
    patient = get_object_or_404(PatientProfile, user=request.user)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, patient=patient)
        if form.is_valid():
            appointment = form.save()
            
            # Send notification to doctor
            Notification.objects.create(
                user=appointment.doctor.user,
                notification_type='appointment',
                title='New Appointment',
                message=f'You have a new appointment with {patient.user.get_full_name()} on {appointment.appointment_date} at {appointment.appointment_time}.',
                related_url=reverse('appointments:appointment_detail', args=[appointment.id])
            )
            
            # Send email to doctor if email is available
            if appointment.doctor.user.email:
                send_mail(
                    'New Appointment Booking',
                    f'You have a new appointment with {patient.user.get_full_name()} on {appointment.appointment_date} at {appointment.appointment_time}.',
                    settings.DEFAULT_FROM_EMAIL,
                    [appointment.doctor.user.email],
                    fail_silently=True,
                )
            
            messages.success(request, "Appointment booked successfully!")
            return redirect('appointments:appointment_detail', pk=appointment.id)
    else:
        # Pre-select doctor if provided in URL
        doctor_id = request.GET.get('doctor')
        initial_data = {}
        if doctor_id:
            try:
                doctor = DoctorProfile.objects.get(id=doctor_id)
                initial_data['doctor'] = doctor
            except DoctorProfile.DoesNotExist:
                pass
            
        form = AppointmentForm(initial=initial_data, patient=patient)
    
    # Get list of specializations for filtering
    specializations = DoctorProfile.objects.values_list(
        'specialization', flat=True
    ).distinct()
    
    context = {
        'form': form,
        'specializations': specializations,
        'active_tab': 'book'
    }
    
    return render(request, 'appointments/book.html', context)


@login_required
def my_appointments(request):
    """View for listing patient's appointments"""
    
    # Check if user is a patient
    if not request.user.is_patient():
        messages.error(request, "Only patients can view their appointments.")
        return redirect('accounts:dashboard')
    
    # Get patient profile
    patient = get_object_or_404(PatientProfile, user=request.user)
    
    # Get different appointment status types
    upcoming_appointments = Appointment.objects.filter(
        patient=patient,
        appointment_date__gte=timezone.now().date(),
        status='scheduled'
    ).order_by('appointment_date', 'appointment_time')
    
    past_appointments = Appointment.objects.filter(
        patient=patient,
        appointment_date__lt=timezone.now().date()
    ).order_by('-appointment_date', '-appointment_time')
    
    cancelled_appointments = Appointment.objects.filter(
        patient=patient,
        status='cancelled'
    ).order_by('-appointment_date', '-appointment_time')
    
    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'cancelled_appointments': cancelled_appointments,
        'active_tab': 'appointments'
    }
    
    return render(request, 'appointments/my_appointments.html', context)


@login_required
def appointment_detail(request, pk):
    """View appointment details"""
    
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check if user is authorized to view this appointment
    user = request.user
    if (user.is_patient() and appointment.patient.user != user) and \
       (user.is_doctor() and appointment.doctor.user != user) and \
       not user.is_admin():
        messages.error(request, "You don't have permission to view this appointment.")
        return redirect('accounts:dashboard')
    
    # Check if feedback exists for completed appointments
    feedback = None
    show_feedback_form = False
    
    if appointment.status == 'completed':
        try:
            feedback = Feedback.objects.get(appointment=appointment)
        except Feedback.DoesNotExist:
            # Show feedback form for patients if appointment is completed and no feedback yet
            if user.is_patient() and appointment.patient.user == user:
                show_feedback_form = True
    
    # Prepare feedback form
    feedback_form = None
    if show_feedback_form:
        if request.method == 'POST' and 'submit_feedback' in request.POST:
            feedback_form = FeedbackForm(request.POST)
            if feedback_form.is_valid():
                new_feedback = feedback_form.save(commit=False)
                new_feedback.appointment = appointment
                new_feedback.save()
                
                # Send notification to doctor
                Notification.objects.create(
                    user=appointment.doctor.user,
                    notification_type='feedback',
                    title='New Feedback Received',
                    message=f'{appointment.patient.user.get_full_name()} has left feedback for your appointment on {appointment.appointment_date}.',
                    related_url=reverse('appointments:appointment_detail', args=[appointment.id])
                )
                
                messages.success(request, "Thank you for your feedback!")
                return redirect('appointments:appointment_detail', pk=appointment.id)
        else:
            feedback_form = FeedbackForm()
    
    context = {
        'appointment': appointment,
        'feedback': feedback,
        'feedback_form': feedback_form,
        'show_feedback_form': show_feedback_form
    }
    
    return render(request, 'appointments/detail.html', context)


@login_required
def cancel_appointment(request, pk):
    """Cancel an appointment"""
    
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check if user is authorized to cancel this appointment
    user = request.user
    if (user.is_patient() and appointment.patient.user != user) and \
       (user.is_doctor() and appointment.doctor.user != user) and \
       not user.is_admin():
        messages.error(request, "You don't have permission to cancel this appointment.")
        return redirect('accounts:dashboard')
    
    # Check if appointment can be cancelled
    if appointment.status != 'scheduled':
        messages.error(request, "Only scheduled appointments can be cancelled.")
        return redirect('appointments:appointment_detail', pk=appointment.id)
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        
        # Send notification to other party
        recipient = appointment.doctor.user if user.is_patient() else appointment.patient.user
        canceller = 'patient' if user.is_patient() else 'doctor'
        
        Notification.objects.create(
            user=recipient,
            notification_type='appointment',
            title='Appointment Cancelled',
            message=f'The appointment on {appointment.appointment_date} at {appointment.appointment_time} has been cancelled by the {canceller}.',
            related_url=reverse('appointments:appointment_detail', args=[appointment.id])
        )
        
        # Send email notification
        if recipient.email:
            send_mail(
                'Appointment Cancelled',
                f'The appointment on {appointment.appointment_date} at {appointment.appointment_time} has been cancelled by the {canceller}.',
                settings.DEFAULT_FROM_EMAIL,
                [recipient.email],
                fail_silently=True,
            )
        
        messages.success(request, "Appointment has been cancelled successfully.")
        
        # Redirect based on user role
        if user.is_patient():
            return redirect('appointments:my_appointments')
        elif user.is_doctor():
            return redirect('appointments:doctor_appointments')
        else:
            return redirect('appointments:admin_all_appointments')
    
    context = {
        'appointment': appointment
    }
    
    return render(request, 'appointments/cancel.html', context)


@login_required
def reschedule_appointment(request, pk):
    """Reschedule an appointment"""
    
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check if user is authorized to reschedule this appointment
    user = request.user
    if (user.is_patient() and appointment.patient.user != user) and \
       (user.is_doctor() and appointment.doctor.user != user) and \
       not user.is_admin():
        messages.error(request, "You don't have permission to reschedule this appointment.")
        return redirect('accounts:dashboard')
    
    # Check if appointment can be rescheduled
    if appointment.status != 'scheduled':
        messages.error(request, "Only scheduled appointments can be rescheduled.")
        return redirect('appointments:appointment_detail', pk=appointment.id)
    
    if request.method == 'POST':
        form = AppointmentRescheduleForm(request.POST, instance=appointment)
        if form.is_valid():
            # Update status to rescheduled if it's not a new appointment
            old_date = appointment.appointment_date
            old_time = appointment.appointment_time
            
            # Save the form with new date/time
            rescheduled_appointment = form.save(commit=False)
            rescheduled_appointment.status = 'rescheduled'
            rescheduled_appointment.save()
            
            # Create a new scheduled appointment with the new date/time
            new_appointment = Appointment.objects.create(
                patient=appointment.patient,
                doctor=appointment.doctor,
                appointment_date=form.cleaned_data['appointment_date'],
                appointment_time=form.cleaned_data['appointment_time'],
                reason=appointment.reason,
                status='scheduled'
            )
            
            # Send notification to other party
            recipient = appointment.doctor.user if user.is_patient() else appointment.patient.user
            rescheduler = 'patient' if user.is_patient() else 'doctor'
            
            Notification.objects.create(
                user=recipient,
                notification_type='appointment',
                title='Appointment Rescheduled',
                message=f'The appointment originally scheduled for {old_date} at {old_time} has been rescheduled to {new_appointment.appointment_date} at {new_appointment.appointment_time} by the {rescheduler}.',
                related_url=reverse('appointments:appointment_detail', args=[new_appointment.id])
            )
            
            # Send email notification
            if recipient.email:
                send_mail(
                    'Appointment Rescheduled',
                    f'The appointment originally scheduled for {old_date} at {old_time} has been rescheduled to {new_appointment.appointment_date} at {new_appointment.appointment_time} by the {rescheduler}.',
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient.email],
                    fail_silently=True,
                )
            
            messages.success(request, "Appointment has been rescheduled successfully.")
            return redirect('appointments:appointment_detail', pk=new_appointment.id)
    else:
        form = AppointmentRescheduleForm(instance=appointment)
    
    context = {
        'form': form,
        'appointment': appointment
    }
    
    return render(request, 'appointments/reschedule.html', context)


@login_required
def doctor_appointments(request):
    """View for doctor to see their appointments"""
    
    # Check if user is a doctor
    if not request.user.is_doctor():
        messages.error(request, "Only doctors can access this page.")
        return redirect('accounts:dashboard')
    
    # Get doctor profile
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    
    # Filter parameters
    status = request.GET.get('status', 'all')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    appointments = Appointment.objects.filter(doctor=doctor)
    
    # Apply filters
    if status != 'all':
        appointments = appointments.filter(status=status)
    
    if search:
        appointments = appointments.filter(
            Q(patient__user__first_name__icontains=search) |
            Q(patient__user__last_name__icontains=search) |
            Q(patient__user__email__icontains=search) |
            Q(reason__icontains=search)
        )
    
    if date_from:
        appointments = appointments.filter(appointment_date__gte=date_from)
    
    if date_to:
        appointments = appointments.filter(appointment_date__lte=date_to)
    
    # Default sorting
    appointments = appointments.order_by('appointment_date', 'appointment_time')
    
    # Get today's appointments separately
    today = timezone.now().date()
    todays_appointments = appointments.filter(appointment_date=today)
    
    # Get upcoming appointments (future dates, excluding today)
    upcoming_appointments = appointments.filter(
        appointment_date__gt=today,
        status='scheduled'
    )
    
    # Get past appointments
    past_appointments = appointments.filter(
        appointment_date__lt=today
    ).order_by('-appointment_date', '-appointment_time')
    
    context = {
        'todays_appointments': todays_appointments,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'status_filter': status,
        'search_query': search,
        'date_from': date_from,
        'date_to': date_to,
        'active_tab': 'appointments'
    }
    
    return render(request, 'appointments/doctor_appointments.html', context)


@login_required
def complete_appointment(request, pk):
    """Mark an appointment as completed"""
    
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check if user is the doctor for this appointment
    if not request.user.is_doctor() or appointment.doctor.user != request.user:
        messages.error(request, "Only the assigned doctor can complete this appointment.")
        return redirect('accounts:dashboard')
    
    # Check if appointment can be marked as completed
    if appointment.status != 'scheduled':
        messages.error(request, "Only scheduled appointments can be marked as completed.")
        return redirect('appointments:appointment_detail', pk=appointment.id)
    
    if request.method == 'POST':
        notes_form = AppointmentNotesForm(request.POST, instance=appointment)
        if notes_form.is_valid():
            completed_appointment = notes_form.save(commit=False)
            completed_appointment.status = 'completed'
            completed_appointment.save()
            
            # Send notification to patient
            Notification.objects.create(
                user=appointment.patient.user,
                notification_type='appointment',
                title='Appointment Completed',
                message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} on {appointment.appointment_date} has been marked as completed.',
                related_url=reverse('appointments:appointment_detail', args=[appointment.id])
            )
            
            # Send email notification
            if appointment.patient.user.email:
                send_mail(
                    'Appointment Completed',
                    f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} on {appointment.appointment_date} has been marked as completed. You can now leave feedback for this appointment.',
                    settings.DEFAULT_FROM_EMAIL,
                    [appointment.patient.user.email],
                    fail_silently=True,
                )
            
            messages.success(request, "Appointment has been marked as completed.")
            return redirect('appointments:appointment_detail', pk=appointment.id)
    else:
        notes_form = AppointmentNotesForm(instance=appointment)
    
    context = {
        'appointment': appointment,
        'notes_form': notes_form
    }
    
    return render(request, 'appointments/complete.html', context)


@login_required
def add_appointment_notes(request, pk):
    """Add or update notes for an appointment"""
    
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check if user is the doctor for this appointment
    if not request.user.is_doctor() or appointment.doctor.user != request.user:
        messages.error(request, "Only the assigned doctor can add notes to this appointment.")
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = AppointmentNotesForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, "Appointment notes have been updated.")
            return redirect('appointments:appointment_detail', pk=appointment.id)
    else:
        form = AppointmentNotesForm(instance=appointment)
    
    context = {
        'appointment': appointment,
        'form': form
    }
    
    return render(request, 'appointments/add_notes.html', context)


@login_required
def add_feedback(request, pk):
    """Add feedback for a completed appointment"""
    
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check if user is the patient for this appointment
    if not request.user.is_patient() or appointment.patient.user != request.user:
        messages.error(request, "Only the patient can add feedback for this appointment.")
        return redirect('accounts:dashboard')
    
    # Check if appointment is completed
    if appointment.status != 'completed':
        messages.error(request, "Feedback can only be added for completed appointments.")
        return redirect('appointments:appointment_detail', pk=appointment.id)
    
    # Check if feedback already exists
    try:
        existing_feedback = Feedback.objects.get(appointment=appointment)
        messages.info(request, "You have already provided feedback for this appointment.")
        return redirect('appointments:appointment_detail', pk=appointment.id)
    except Feedback.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.appointment = appointment
            feedback.save()
            
            # Send notification to doctor
            Notification.objects.create(
                user=appointment.doctor.user,
                notification_type='feedback',
                title='New Feedback Received',
                message=f'{appointment.patient.user.get_full_name()} has left feedback for your appointment on {appointment.appointment_date}.',
                related_url=reverse('appointments:appointment_detail', args=[appointment.id])
            )
            
            messages.success(request, "Thank you for your feedback!")
            return redirect('appointments:appointment_detail', pk=appointment.id)
    else:
        form = FeedbackForm()
    
    context = {
        'appointment': appointment,
        'form': form
    }
    
    return render(request, 'appointments/add_feedback.html', context)


@login_required
def view_feedback(request):
    """View all feedback for a doctor"""
    
    # Check if user is a doctor
    if not request.user.is_doctor():
        messages.error(request, "Only doctors can view their feedback.")
        return redirect('accounts:dashboard')
    
    # Get doctor profile
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    
    # Get all feedback for appointments with this doctor
    feedback = Feedback.objects.filter(
        appointment__doctor=doctor
    ).order_by('-appointment__appointment_date')
    
    # Calculate average rating
    total_ratings = feedback.count()
    if total_ratings > 0:
        avg_rating = sum(f.rating for f in feedback) / total_ratings
    else:
        avg_rating = 0
    
    # Count by rating
    rating_counts = {i: feedback.filter(rating=i).count() for i in range(1, 6)}
    
    context = {
        'feedback_list': feedback,
        'avg_rating': avg_rating,
        'total_ratings': total_ratings,
        'rating_counts': rating_counts,
        'active_tab': 'feedback'
    }
    
    return render(request, 'appointments/view_feedback.html', context)


@login_required
def admin_all_appointments(request):
    """Admin view for all appointments"""
    
    # Check if user is an admin
    if not request.user.is_admin():
        messages.error(request, "Only administrators can view this page.")
        return redirect('accounts:dashboard')
    
    # Filter parameters
    status = request.GET.get('status', 'all')
    doctor_id = request.GET.get('doctor', 'all')
    patient_id = request.GET.get('patient', 'all')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    appointments = Appointment.objects.all()
    
    # Apply filters
    if status != 'all':
        appointments = appointments.filter(status=status)
    
    if doctor_id != 'all':
        appointments = appointments.filter(doctor__id=doctor_id)
    
    if patient_id != 'all':
        appointments = appointments.filter(patient__id=patient_id)
    
    if search:
        appointments = appointments.filter(
            Q(patient__user__first_name__icontains=search) |
            Q(patient__user__last_name__icontains=search) |
            Q(doctor__user__first_name__icontains=search) |
            Q(doctor__user__last_name__icontains=search) |
            Q(reason__icontains=search)
        )
    
    if date_from:
        appointments = appointments.filter(appointment_date__gte=date_from)
    
    if date_to:
        appointments = appointments.filter(appointment_date__lte=date_to)
    
    # Default sorting
    appointments = appointments.order_by('-appointment_date', '-appointment_time')
    
    # Get doctors and patients for filter dropdowns
    doctors = DoctorProfile.objects.all()
    patients = PatientProfile.objects.all()
    
    context = {
        'appointments': appointments,
        'doctors': doctors,
        'patients': patients,
        'status_filter': status,
        'doctor_filter': doctor_id,
        'patient_filter': patient_id,
        'search_query': search,
        'date_from': date_from,
        'date_to': date_to,
        'active_tab': 'appointments'
    }
    
    return render(request, 'appointments/admin_appointments.html', context)
