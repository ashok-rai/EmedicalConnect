from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from django.core.paginator import Paginator

import os
import mimetypes

from .models import MedicalRecord, Prescription, Medication
from .forms import MedicalRecordForm, PrescriptionForm, MedicationFormSet
from accounts.models import PatientProfile, DoctorProfile
from messaging.models import Notification


@login_required
def record_list(request):
    """View list of medical records for a patient"""
    
    # If user is a patient, show their records
    if request.user.is_patient():
        patient = get_object_or_404(PatientProfile, user=request.user)
        records = MedicalRecord.objects.filter(patient=patient).order_by('-record_date', '-created_at')
    
    # If user is a doctor, redirect to patient selection
    elif request.user.is_doctor():
        return redirect('medical_records:patient_records')
    
    # If user is admin, show all records
    elif request.user.is_admin():
        records = MedicalRecord.objects.all().order_by('-record_date', '-created_at')
    
    else:
        messages.error(request, "You don't have permission to view medical records.")
        return redirect('accounts:dashboard')
    
    # Filter parameters
    record_type = request.GET.get('type', '')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Apply filters
    if record_type:
        records = records.filter(record_type=record_type)
    
    if search:
        records = records.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if date_from:
        records = records.filter(record_date__gte=date_from)
    
    if date_to:
        records = records.filter(record_date__lte=date_to)
    
    # Count by record type for sidebar
    record_counts = {
        'all': records.count(),
        'lab_report': records.filter(record_type='lab_report').count(),
        'prescription': records.filter(record_type='prescription').count(),
        'medical_image': records.filter(record_type='medical_image').count(),
        'diagnosis': records.filter(record_type='diagnosis').count(),
    }
    
    # Pagination
    paginator = Paginator(records, 10)  # 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'records': page_obj,
        'record_counts': record_counts,
        'current_type': record_type,
        'search_query': search,
        'date_from': date_from,
        'date_to': date_to,
        'active_tab': 'records'
    }
    
    return render(request, 'medical_records/record_list.html', context)


@login_required
def record_detail(request, pk):
    """View details of a specific medical record"""
    
    record = get_object_or_404(MedicalRecord, pk=pk)
    
    # Check if user has permission to view this record
    user = request.user
    if (user.is_patient() and record.patient.user != user) and \
       (user.is_doctor() and (not hasattr(record, 'prescription') or record.prescription.prescribed_by.user != user)) and \
       not user.is_admin():
        messages.error(request, "You don't have permission to view this record.")
        return redirect('accounts:dashboard')
    
    # If this record is a prescription, get its medications
    prescription = None
    medications = []
    if record.record_type == 'prescription' and hasattr(record, 'prescription'):
        prescription = record.prescription
        medications = prescription.medications.all()
    
    context = {
        'record': record,
        'prescription': prescription,
        'medications': medications,
        'active_tab': 'records'
    }
    
    return render(request, 'medical_records/record_detail.html', context)


@login_required
def add_record(request):
    """Add a new medical record"""
    
    # For patients: can only add certain types of records for themselves
    # For doctors: can add any type of record for their patients
    user = request.user
    
    if user.is_patient():
        patient = get_object_or_404(PatientProfile, user=user)
        doctor = None
        # Patients can only upload certain types of records
        allowed_types = ['medical_image', 'lab_report', 'vaccination']
    elif user.is_doctor():
        doctor = get_object_or_404(DoctorProfile, user=user)
        # Get the patient for whom the record is being added
        patient_id = request.GET.get('patient')
        if not patient_id:
            messages.info(request, "Please select a patient to add a record for.")
            return redirect('medical_records:patient_records')
        
        patient = get_object_or_404(PatientProfile, id=patient_id)
        # Doctors can add any type of record
        allowed_types = None
    else:
        messages.error(request, "You don't have permission to add medical records.")
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES, patient=patient, doctor=doctor)
        
        # Filter record types for patients
        if user.is_patient() and form.is_valid() and form.cleaned_data['record_type'] not in allowed_types:
            form.add_error('record_type', "You don't have permission to add this type of record.")
        
        if form.is_valid():
            record = form.save()
            
            # If the record is a prescription and it's added by a doctor, redirect to add prescription details
            if user.is_doctor() and record.record_type == 'prescription':
                return redirect('medical_records:add_prescription', record_id=record.id)
            
            # Send notification if doctor adds a record for patient
            if user.is_doctor():
                Notification.objects.create(
                    user=patient.user,
                    notification_type='medical_record',
                    title='New Medical Record Added',
                    message=f'Dr. {user.get_full_name()} has added a new {record.get_record_type_display()} to your records.',
                    related_url=f'/records/{record.id}/'
                )
            
            messages.success(request, "Medical record has been added successfully.")
            return redirect('medical_records:record_detail', pk=record.id)
    else:
        # Pre-fill with today's date and default record type
        initial_data = {
            'record_date': timezone.now().date(),
            'record_type': 'lab_report' if user.is_patient() else None
        }
        form = MedicalRecordForm(initial=initial_data, patient=patient, doctor=doctor)
        
        # Limit record types for patients
        if user.is_patient():
            form.fields['record_type'].choices = [
                (t, label) for t, label in form.fields['record_type'].choices if t in allowed_types
            ]
    
    context = {
        'form': form,
        'patient': patient,
        'is_patient_view': user.is_patient(),
        'active_tab': 'records'
    }
    
    return render(request, 'medical_records/add_record.html', context)


@login_required
def edit_record(request, pk):
    """Edit an existing medical record"""
    
    record = get_object_or_404(MedicalRecord, pk=pk)
    
    # Check if user has permission to edit this record
    user = request.user
    if (user.is_patient() and record.patient.user != user) and \
       (user.is_doctor() and (record.created_by is None or record.created_by.user != user)) and \
       not user.is_admin():
        messages.error(request, "You don't have permission to edit this record.")
        return redirect('accounts:dashboard')
    
    # Patients cannot edit records created by doctors
    if user.is_patient() and record.created_by is not None:
        messages.error(request, "You cannot edit a record that was created by a doctor.")
        return redirect('medical_records:record_detail', pk=record.id)
    
    # Get patient and doctor objects
    patient = record.patient
    doctor = record.created_by if record.created_by else None
    
    if request.method == 'POST':
        form = MedicalRecordForm(
            request.POST, 
            request.FILES, 
            instance=record, 
            patient=patient, 
            doctor=doctor
        )
        
        # Patients should not change record type
        if user.is_patient() and 'record_type' in form.changed_data:
            form.add_error('record_type', "You cannot change the record type.")
        
        if form.is_valid():
            updated_record = form.save()
            
            # If the record is a prescription and it's edited by a doctor, redirect to edit prescription details
            if user.is_doctor() and updated_record.record_type == 'prescription':
                # Check if prescription exists
                if hasattr(updated_record, 'prescription'):
                    return redirect('medical_records:edit_prescription', prescription_id=updated_record.prescription.id)
                else:
                    return redirect('medical_records:add_prescription', record_id=updated_record.id)
            
            messages.success(request, "Medical record has been updated successfully.")
            return redirect('medical_records:record_detail', pk=updated_record.id)
    else:
        form = MedicalRecordForm(instance=record, patient=patient, doctor=doctor)
        
        # Limit editing capabilities for patients
        if user.is_patient():
            form.fields['record_type'].disabled = True
    
    context = {
        'form': form,
        'record': record,
        'patient': patient,
        'is_patient_view': user.is_patient(),
        'active_tab': 'records'
    }
    
    return render(request, 'medical_records/edit_record.html', context)


@login_required
def download_record_file(request, pk):
    """Download the file attached to a medical record"""
    
    record = get_object_or_404(MedicalRecord, pk=pk)
    
    # Check if user has permission to view this record
    user = request.user
    if (user.is_patient() and record.patient.user != user) and \
       (user.is_doctor() and (not hasattr(record, 'prescription') or record.prescription.prescribed_by.user != user)) and \
       not user.is_admin():
        messages.error(request, "You don't have permission to download this file.")
        return redirect('accounts:dashboard')
    
    # Check if file exists
    if not record.file:
        messages.error(request, "This record does not have an attached file.")
        return redirect('medical_records:record_detail', pk=record.id)
    
    # Get file path
    file_path = record.file.path
    
    # Check if file exists on disk
    if not os.path.exists(file_path):
        messages.error(request, "File not found.")
        return redirect('medical_records:record_detail', pk=record.id)
    
    # Get file content type
    content_type, encoding = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = 'application/octet-stream'
    
    # Serve file
    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
    
    return response


@login_required
def prescription_list(request):
    """View list of prescriptions for a patient"""
    
    # If user is a patient, show their prescriptions
    if request.user.is_patient():
        patient = get_object_or_404(PatientProfile, user=request.user)
        prescriptions = Prescription.objects.filter(
            medical_record__patient=patient
        ).order_by('-medical_record__record_date')
    
    # If user is a doctor, show prescriptions they've written
    elif request.user.is_doctor():
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        prescriptions = Prescription.objects.filter(
            prescribed_by=doctor
        ).order_by('-medical_record__record_date')
    
    # If user is admin, show all prescriptions
    elif request.user.is_admin():
        prescriptions = Prescription.objects.all().order_by('-medical_record__record_date')
    
    else:
        messages.error(request, "You don't have permission to view prescriptions.")
        return redirect('accounts:dashboard')
    
    # Filter parameters
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Apply filters
    if search:
        prescriptions = prescriptions.filter(
            Q(medical_record__title__icontains=search) | 
            Q(medications__name__icontains=search)
        ).distinct()
    
    if date_from:
        prescriptions = prescriptions.filter(medical_record__record_date__gte=date_from)
    
    if date_to:
        prescriptions = prescriptions.filter(medical_record__record_date__lte=date_to)
    
    # Pagination
    paginator = Paginator(prescriptions, 10)  # 10 prescriptions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'prescriptions': page_obj,
        'search_query': search,
        'date_from': date_from,
        'date_to': date_to,
        'active_tab': 'prescriptions'
    }
    
    return render(request, 'medical_records/prescription_list.html', context)


@login_required
def prescription_detail(request, pk):
    """View details of a specific prescription"""
    
    prescription = get_object_or_404(Prescription, pk=pk)
    
    # Check if user has permission to view this prescription
    user = request.user
    if (user.is_patient() and prescription.medical_record.patient.user != user) and \
       (user.is_doctor() and prescription.prescribed_by.user != user) and \
       not user.is_admin():
        messages.error(request, "You don't have permission to view this prescription.")
        return redirect('accounts:dashboard')
    
    # Get associated medications
    medications = prescription.medications.all()
    
    context = {
        'prescription': prescription,
        'medications': medications,
        'record': prescription.medical_record,
        'active_tab': 'prescriptions'
    }
    
    return render(request, 'medical_records/prescription_detail.html', context)


@login_required
def add_prescription(request, record_id):
    """Add prescription details to a medical record"""
    
    # Only doctors can add prescriptions
    if not request.user.is_doctor():
        messages.error(request, "Only doctors can add prescriptions.")
        return redirect('accounts:dashboard')
    
    # Get the doctor's profile
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    
    # Get the medical record
    record = get_object_or_404(MedicalRecord, pk=record_id, record_type='prescription')
    
    # Check if the record already has a prescription
    if hasattr(record, 'prescription'):
        messages.info(request, "This record already has prescription details.")
        return redirect('medical_records:edit_prescription', prescription_id=record.prescription.id)
    
    if request.method == 'POST':
        # Process the prescription form
        prescription_form = PrescriptionForm(request.POST, doctor=doctor)
        
        # Create a formset for the medications linked to this prescription
        medication_formset = MedicationFormSet(request.POST, instance=None)
        
        if prescription_form.is_valid() and medication_formset.is_valid():
            # Save the prescription but link it to the medical record
            prescription = prescription_form.save(commit=False)
            prescription.medical_record = record
            prescription.prescribed_by = doctor
            prescription.save()
            
            # Save the medications linked to this prescription
            medications = medication_formset.save(commit=False)
            for medication in medications:
                medication.prescription = prescription
                medication.save()
            
            # Handle deleted medications
            for obj in medication_formset.deleted_objects:
                obj.delete()
            
            # Send notification to patient
            Notification.objects.create(
                user=record.patient.user,
                notification_type='prescription',
                title='New Prescription Added',
                message=f'Dr. {request.user.get_full_name()} has added a new prescription to your records.',
                related_url=f'/records/prescriptions/{prescription.id}/'
            )
            
            messages.success(request, "Prescription has been added successfully.")
            return redirect('medical_records:prescription_detail', pk=prescription.id)
    else:
        # Create empty forms
        prescription_form = PrescriptionForm(doctor=doctor, initial={
            'expiry_date': (timezone.now() + timezone.timedelta(days=30)).date()  # Default 30 days expiry
        })
        medication_formset = MedicationFormSet(instance=None)
    
    context = {
        'prescription_form': prescription_form,
        'medication_formset': medication_formset,
        'record': record,
        'patient': record.patient,
        'active_tab': 'prescriptions'
    }
    
    return render(request, 'medical_records/add_prescription.html', context)


@login_required
def edit_prescription(request, prescription_id):
    """Edit an existing prescription"""
    
    # Only doctors who created the prescription can edit it
    if not request.user.is_doctor():
        messages.error(request, "Only doctors can edit prescriptions.")
        return redirect('accounts:dashboard')
    
    # Get the prescription
    prescription = get_object_or_404(Prescription, pk=prescription_id)
    
    # Check if this doctor is the one who prescribed it
    if prescription.prescribed_by.user != request.user:
        messages.error(request, "You can only edit prescriptions that you have created.")
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        # Process the prescription form
        prescription_form = PrescriptionForm(request.POST, instance=prescription, doctor=prescription.prescribed_by)
        
        # Create a formset for the medications linked to this prescription
        medication_formset = MedicationFormSet(request.POST, instance=prescription)
        
        if prescription_form.is_valid() and medication_formset.is_valid():
            # Save the updated prescription
            prescription_form.save()
            
            # Save the medications
            medications = medication_formset.save(commit=False)
            for medication in medications:
                medication.prescription = prescription
                medication.save()
            
            # Handle deleted medications
            for obj in medication_formset.deleted_objects:
                obj.delete()
            
            messages.success(request, "Prescription has been updated successfully.")
            return redirect('medical_records:prescription_detail', pk=prescription.id)
    else:
        # Create forms with instance data
        prescription_form = PrescriptionForm(instance=prescription, doctor=prescription.prescribed_by)
        medication_formset = MedicationFormSet(instance=prescription)
    
    context = {
        'prescription_form': prescription_form,
        'medication_formset': medication_formset,
        'prescription': prescription,
        'record': prescription.medical_record,
        'patient': prescription.medical_record.patient,
        'active_tab': 'prescriptions'
    }
    
    return render(request, 'medical_records/edit_prescription.html', context)


@login_required
def patient_records(request, patient_id=None):
    """View for doctors to select a patient and view their records"""
    
    # Only doctors and admins can access this view
    if not (request.user.is_doctor() or request.user.is_admin()):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('accounts:dashboard')
    
    # If a specific patient is requested, show their records
    if patient_id:
        patient = get_object_or_404(PatientProfile, pk=patient_id)
        records = MedicalRecord.objects.filter(patient=patient).order_by('-record_date', '-created_at')
        
        # Filter parameters
        record_type = request.GET.get('type', '')
        search = request.GET.get('search', '')
        
        # Apply filters
        if record_type:
            records = records.filter(record_type=record_type)
        
        if search:
            records = records.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        # Count by record type for sidebar
        record_counts = {
            'all': records.count(),
            'lab_report': records.filter(record_type='lab_report').count(),
            'prescription': records.filter(record_type='prescription').count(),
            'medical_image': records.filter(record_type='medical_image').count(),
            'diagnosis': records.filter(record_type='diagnosis').count(),
        }
        
        # Pagination
        paginator = Paginator(records, 10)  # 10 records per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'patient': patient,
            'records': page_obj,
            'record_counts': record_counts,
            'current_type': record_type,
            'search_query': search,
            'active_tab': 'patients'
        }
        
        return render(request, 'medical_records/patient_records.html', context)
    
    # Otherwise, show a list of patients to select from
    if request.user.is_doctor():
        # For doctors, show patients they've had appointments with
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        patients = PatientProfile.objects.filter(
            appointments__doctor=doctor
        ).distinct().order_by('user__last_name', 'user__first_name')
    else:
        # For admins, show all patients
        patients = PatientProfile.objects.all().order_by('user__last_name', 'user__first_name')
    
    # Search patients
    search = request.GET.get('search', '')
    if search:
        patients = patients.filter(
            Q(user__first_name__icontains=search) | 
            Q(user__last_name__icontains=search) | 
            Q(user__email__icontains=search)
        )
    
    context = {
        'patients': patients,
        'search_query': search,
        'active_tab': 'patients'
    }
    
    return render(request, 'medical_records/patient_list.html', context)
