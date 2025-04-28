import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, abort, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import db, mail
from models import User, Patient, Doctor, Admin, Appointment, HealthRecord, Message, Feedback
from forms import (LoginForm, RegistrationForm, PatientProfileForm, DoctorProfileForm, AdminProfileForm,
                 AppointmentForm, HealthRecordForm, MessageForm, FeedbackForm)
from flask_mail import Message as MailMessage

# Blueprint definitions
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
patient_bp = Blueprint('patient', __name__)
doctor_bp = Blueprint('doctor', __name__)
admin_bp = Blueprint('admin', __name__)
appointment_bp = Blueprint('appointment', __name__)
health_record_bp = Blueprint('health_record', __name__)
chat_bp = Blueprint('chat', __name__)
feedback_bp = Blueprint('feedback', __name__)

# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def send_notification_email(subject, recipient, template, **kwargs):
    msg = MailMessage(subject, recipients=[recipient])
    msg.html = render_template(template, **kwargs)
    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {str(e)}")
        return False

# Main routes
@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/services')
def services():
    return render_template('services.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

# Auth routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            
            if not next_page or not next_page.startswith('/'):
                if user.is_patient():
                    next_page = url_for('patient.dashboard')
                elif user.is_doctor():
                    next_page = url_for('doctor.dashboard')
                elif user.is_admin():
                    next_page = url_for('admin.dashboard')
                else:
                    next_page = url_for('main.index')
            
            return redirect(next_page)
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            role=form.role.data
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    if current_user.is_patient() and current_user.patient:
        return redirect(url_for('patient.dashboard'))
    elif current_user.is_doctor() and current_user.doctor:
        return redirect(url_for('doctor.dashboard'))
    elif current_user.is_admin() and current_user.admin:
        return redirect(url_for('admin.dashboard'))
    
    if current_user.is_patient():
        form = PatientProfileForm()
        if form.validate_on_submit():
            patient = Patient(
                user_id=current_user.id,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                date_of_birth=form.date_of_birth.data,
                gender=form.gender.data,
                phone=form.phone.data,
                address=form.address.data
            )
            db.session.add(patient)
            db.session.commit()
            flash('Patient profile completed successfully!', 'success')
            return redirect(url_for('patient.dashboard'))
        return render_template('auth/complete_profile_patient.html', form=form)
    
    elif current_user.is_doctor():
        form = DoctorProfileForm()
        if form.validate_on_submit():
            doctor = Doctor(
                user_id=current_user.id,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                specialization=form.specialization.data,
                license_number=form.license_number.data,
                experience_years=form.experience_years.data,
                bio=form.bio.data,
                phone=form.phone.data
            )
            db.session.add(doctor)
            db.session.commit()
            flash('Doctor profile completed successfully!', 'success')
            return redirect(url_for('doctor.dashboard'))
        return render_template('auth/complete_profile_doctor.html', form=form)
    
    elif current_user.is_admin():
        form = AdminProfileForm()
        if form.validate_on_submit():
            admin = Admin(
                user_id=current_user.id,
                first_name=form.first_name.data,
                last_name=form.last_name.data
            )
            db.session.add(admin)
            db.session.commit()
            flash('Admin profile completed successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        return render_template('auth/complete_profile_admin.html', form=form)
    
    return redirect(url_for('main.index'))

# Patient routes
@patient_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_patient():
        abort(403)
    
    if not current_user.patient:
        return redirect(url_for('auth.complete_profile'))
    
    # Get patient's upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        patient_id=current_user.patient.id, 
        status='scheduled'
    ).filter(
        Appointment.date >= datetime.now().date()
    ).order_by(Appointment.date, Appointment.time).limit(5).all()
    
    # Get patient's recent health records
    recent_records = HealthRecord.query.filter_by(
        patient_id=current_user.patient.id
    ).order_by(HealthRecord.created_at.desc()).limit(5).all()
    
    # Get unread messages
    unread_messages = Message.query.filter_by(
        receiver_id=current_user.id,
        is_read=False
    ).count()
    
    return render_template('dashboard/patient.html', 
                          upcoming_appointments=upcoming_appointments,
                          recent_records=recent_records,
                          unread_messages=unread_messages)

@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if not current_user.is_patient():
        abort(403)
    
    if not current_user.patient:
        return redirect(url_for('auth.complete_profile'))
    
    form = PatientProfileForm(obj=current_user.patient)
    
    if form.validate_on_submit():
        current_user.patient.first_name = form.first_name.data
        current_user.patient.last_name = form.last_name.data
        current_user.patient.date_of_birth = form.date_of_birth.data
        current_user.patient.gender = form.gender.data
        current_user.patient.phone = form.phone.data
        current_user.patient.address = form.address.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient.profile'))
    
    return render_template('patient/profile.html', form=form)

# Doctor routes
@doctor_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_doctor():
        abort(403)
    
    if not current_user.doctor:
        return redirect(url_for('auth.complete_profile'))
    
    # Get doctor's upcoming appointments
    today = datetime.now().date()
    today_appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor.id,
        date=today,
        status='scheduled'
    ).order_by(Appointment.time).all()
    
    upcoming_appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor.id,
        status='scheduled'
    ).filter(
        Appointment.date > today
    ).order_by(Appointment.date, Appointment.time).limit(10).all()
    
    # Get unread messages
    unread_messages = Message.query.filter_by(
        receiver_id=current_user.id,
        is_read=False
    ).count()
    
    return render_template('dashboard/doctor.html',
                          today_appointments=today_appointments,
                          upcoming_appointments=upcoming_appointments,
                          unread_messages=unread_messages)

@doctor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if not current_user.is_doctor():
        abort(403)
    
    if not current_user.doctor:
        return redirect(url_for('auth.complete_profile'))
    
    form = DoctorProfileForm(obj=current_user.doctor)
    
    if form.validate_on_submit():
        current_user.doctor.first_name = form.first_name.data
        current_user.doctor.last_name = form.last_name.data
        current_user.doctor.specialization = form.specialization.data
        current_user.doctor.license_number = form.license_number.data
        current_user.doctor.experience_years = form.experience_years.data
        current_user.doctor.bio = form.bio.data
        current_user.doctor.phone = form.phone.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('doctor.profile'))
    
    return render_template('doctor/profile.html', form=form)

@doctor_bp.route('/patients')
@login_required
def patients():
    if not current_user.is_doctor():
        abort(403)
    
    if not current_user.doctor:
        return redirect(url_for('auth.complete_profile'))
    
    # Get all patients who have appointments with this doctor
    patients_with_appointments = db.session.query(Patient).join(
        Appointment, Patient.id == Appointment.patient_id
    ).filter(
        Appointment.doctor_id == current_user.doctor.id
    ).distinct().all()
    
    return render_template('doctor/patients.html', patients=patients_with_appointments)

@doctor_bp.route('/patient/<int:patient_id>/records')
@login_required
def patient_records(patient_id):
    if not current_user.is_doctor():
        abort(403)
    
    if not current_user.doctor:
        return redirect(url_for('auth.complete_profile'))
    
    # Verify that the patient has had an appointment with this doctor
    appointment_exists = Appointment.query.filter_by(
        doctor_id=current_user.doctor.id,
        patient_id=patient_id
    ).first()
    
    if not appointment_exists:
        flash('You do not have authorization to view this patient\'s records.', 'danger')
        return redirect(url_for('doctor.patients'))
    
    patient = Patient.query.get_or_404(patient_id)
    records = HealthRecord.query.filter_by(patient_id=patient_id).order_by(HealthRecord.created_at.desc()).all()
    
    return render_template('doctor/patient_records.html', patient=patient, records=records)

# Admin routes
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin():
        abort(403)
    
    if not current_user.admin:
        return redirect(url_for('auth.complete_profile'))
    
    # Count users by role
    patient_count = User.query.filter_by(role='patient').count()
    doctor_count = User.query.filter_by(role='doctor').count()
    
    # Count appointments by status
    scheduled_count = Appointment.query.filter_by(status='scheduled').count()
    completed_count = Appointment.query.filter_by(status='completed').count()
    cancelled_count = Appointment.query.filter_by(status='cancelled').count()
    
    # Get recent appointments
    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(10).all()
    
    return render_template('dashboard/admin.html',
                          patient_count=patient_count,
                          doctor_count=doctor_count,
                          scheduled_count=scheduled_count,
                          completed_count=completed_count,
                          cancelled_count=cancelled_count,
                          recent_appointments=recent_appointments)

@admin_bp.route('/doctors')
@login_required
def doctors():
    if not current_user.is_admin():
        abort(403)
    
    doctors_list = Doctor.query.all()
    return render_template('admin/doctors.html', doctors=doctors_list)

@admin_bp.route('/patients')
@login_required
def patients():
    if not current_user.is_admin():
        abort(403)
    
    patients_list = Patient.query.all()
    return render_template('admin/patients.html', patients=patients_list)

@admin_bp.route('/appointments')
@login_required
def appointments():
    if not current_user.is_admin():
        abort(403)
    
    appointments_list = Appointment.query.order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    return render_template('admin/appointments.html', appointments=appointments_list)

@admin_bp.route('/feedback')
@login_required
def feedback():
    if not current_user.is_admin():
        abort(403)
    
    feedback_list = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template('admin/feedback.html', feedback=feedback_list)

# Appointment routes
@appointment_bp.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    if not current_user.is_patient():
        abort(403)
    
    if not current_user.patient:
        return redirect(url_for('auth.complete_profile'))
    
    form = AppointmentForm()
    
    # Populate the doctor dropdown
    form.doctor_id.choices = [(doctor.id, f"Dr. {doctor.first_name} {doctor.last_name} - {doctor.specialization}") 
                             for doctor in Doctor.query.all()]
    
    if form.validate_on_submit():
        appointment = Appointment(
            patient_id=current_user.patient.id,
            doctor_id=form.doctor_id.data,
            date=form.date.data,
            time=form.time.data,
            reason=form.reason.data,
            status='scheduled'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        # Get doctor email for notification
        doctor = Doctor.query.get(form.doctor_id.data)
        doctor_user = User.query.get(doctor.user_id)
        
        # Send email notification to doctor
        send_notification_email(
            'New Appointment Request',
            doctor_user.email,
            'emails/new_appointment.html',
            doctor=doctor,
            patient=current_user.patient,
            appointment=appointment
        )
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('patient.dashboard'))
    
    return render_template('appointments/book.html', form=form)

@appointment_bp.route('/manage')
@login_required
def manage():
    if current_user.is_patient():
        if not current_user.patient:
            return redirect(url_for('auth.complete_profile'))
        
        upcoming_appointments = Appointment.query.filter_by(
            patient_id=current_user.patient.id, 
            status='scheduled'
        ).filter(
            Appointment.date >= datetime.now().date()
        ).order_by(Appointment.date, Appointment.time).all()
        
        past_appointments = Appointment.query.filter(
            Appointment.patient_id == current_user.patient.id,
            (Appointment.status != 'scheduled') | (Appointment.date < datetime.now().date())
        ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
        
        return render_template('appointments/manage.html', 
                              upcoming_appointments=upcoming_appointments,
                              past_appointments=past_appointments,
                              user_role='patient')
    
    elif current_user.is_doctor():
        if not current_user.doctor:
            return redirect(url_for('auth.complete_profile'))
        
        upcoming_appointments = Appointment.query.filter_by(
            doctor_id=current_user.doctor.id, 
            status='scheduled'
        ).filter(
            Appointment.date >= datetime.now().date()
        ).order_by(Appointment.date, Appointment.time).all()
        
        past_appointments = Appointment.query.filter(
            Appointment.doctor_id == current_user.doctor.id,
            (Appointment.status != 'scheduled') | (Appointment.date < datetime.now().date())
        ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
        
        return render_template('appointments/manage.html', 
                              upcoming_appointments=upcoming_appointments,
                              past_appointments=past_appointments,
                              user_role='doctor')
    
    else:
        abort(403)

@appointment_bp.route('/<int:appointment_id>/view')
@login_required
def view(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if user has permission to view this appointment
    if current_user.is_patient() and current_user.patient.id != appointment.patient_id:
        abort(403)
    elif current_user.is_doctor() and current_user.doctor.id != appointment.doctor_id:
        abort(403)
    elif not (current_user.is_patient() or current_user.is_doctor() or current_user.is_admin()):
        abort(403)
    
    return render_template('appointments/view.html', appointment=appointment)

@appointment_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if user has permission to cancel this appointment
    if current_user.is_patient() and current_user.patient.id != appointment.patient_id:
        abort(403)
    elif current_user.is_doctor() and current_user.doctor.id != appointment.doctor_id:
        abort(403)
    elif not (current_user.is_patient() or current_user.is_doctor() or current_user.is_admin()):
        abort(403)
    
    # Check if appointment can be cancelled (not in the past)
    if appointment.date < datetime.now().date():
        flash('Cannot cancel an appointment that has already passed.', 'danger')
        return redirect(url_for('appointment.view', appointment_id=appointment_id))
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    # Notify the other party
    if current_user.is_patient():
        # Notify doctor
        doctor = Doctor.query.get(appointment.doctor_id)
        doctor_user = User.query.get(doctor.user_id)
        
        send_notification_email(
            'Appointment Cancelled',
            doctor_user.email,
            'emails/cancelled_appointment.html',
            appointment=appointment,
            cancelled_by='patient'
        )
    elif current_user.is_doctor():
        # Notify patient
        patient = Patient.query.get(appointment.patient_id)
        patient_user = User.query.get(patient.user_id)
        
        send_notification_email(
            'Appointment Cancelled',
            patient_user.email,
            'emails/cancelled_appointment.html',
            appointment=appointment,
            cancelled_by='doctor'
        )
    
    flash('Appointment cancelled successfully.', 'success')
    
    if current_user.is_patient():
        return redirect(url_for('patient.dashboard'))
    else:
        return redirect(url_for('doctor.dashboard'))

@appointment_bp.route('/<int:appointment_id>/complete', methods=['POST'])
@login_required
def complete(appointment_id):
    if not current_user.is_doctor():
        abort(403)
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if this doctor is assigned to this appointment
    if current_user.doctor.id != appointment.doctor_id:
        abort(403)
    
    appointment.status = 'completed'
    db.session.commit()
    
    # Notify patient
    patient = Patient.query.get(appointment.patient_id)
    patient_user = User.query.get(patient.user_id)
    
    send_notification_email(
        'Appointment Completed',
        patient_user.email,
        'emails/completed_appointment.html',
        appointment=appointment
    )
    
    flash('Appointment marked as completed.', 'success')
    return redirect(url_for('doctor.dashboard'))

# Health Record routes
@health_record_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if not (current_user.is_patient() or current_user.is_doctor()):
        abort(403)
    
    form = HealthRecordForm()
    
    if form.validate_on_submit():
        # Determine patient_id based on user role
        if current_user.is_patient():
            patient_id = current_user.patient.id
        else:  # Doctor
            # In this case, we need to select a patient
            if 'patient_id' not in request.form:
                flash('Please select a patient.', 'danger')
                return redirect(url_for('health_record.upload'))
            patient_id = request.form['patient_id']
            
            # Verify doctor has seen this patient
            appointment_exists = Appointment.query.filter_by(
                doctor_id=current_user.doctor.id,
                patient_id=patient_id
            ).first()
            
            if not appointment_exists:
                flash('You cannot upload records for patients you have not seen.', 'danger')
                return redirect(url_for('doctor.dashboard'))
        
        # Handle file upload if provided
        file_path = None
        if form.file.data:
            file = form.file.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create directory if it doesn't exist
                os.makedirs(os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER']), exist_ok=True)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(os.path.join(current_app.root_path, file_path))
        
        # Create health record
        record = HealthRecord(
            patient_id=patient_id,
            title=form.title.data,
            description=form.description.data,
            record_type=form.record_type.data,
            file_path=file_path
        )
        
        db.session.add(record)
        db.session.commit()
        
        flash('Health record uploaded successfully!', 'success')
        
        if current_user.is_patient():
            return redirect(url_for('patient.dashboard'))
        else:
            return redirect(url_for('doctor.patient_records', patient_id=patient_id))
    
    # If doctor is uploading, provide list of patients
    patients = None
    if current_user.is_doctor():
        patients = db.session.query(Patient).join(
            Appointment, Patient.id == Appointment.patient_id
        ).filter(
            Appointment.doctor_id == current_user.doctor.id
        ).distinct().all()
    
    return render_template('health_records/upload.html', form=form, patients=patients)

@health_record_bp.route('/view')
@login_required
def view():
    if current_user.is_patient():
        if not current_user.patient:
            return redirect(url_for('auth.complete_profile'))
        
        records = HealthRecord.query.filter_by(
            patient_id=current_user.patient.id
        ).order_by(HealthRecord.created_at.desc()).all()
        
        return render_template('health_records/view.html', records=records)
    else:
        abort(403)

@health_record_bp.route('/<int:record_id>/download')
@login_required
def download(record_id):
    record = HealthRecord.query.get_or_404(record_id)
    
    # Check permissions
    if current_user.is_patient() and current_user.patient.id != record.patient_id:
        abort(403)
    elif current_user.is_doctor():
        # Verify doctor has seen this patient
        appointment_exists = Appointment.query.filter_by(
            doctor_id=current_user.doctor.id,
            patient_id=record.patient_id
        ).first()
        
        if not appointment_exists:
            flash('You do not have permission to view this record.', 'danger')
            return redirect(url_for('doctor.dashboard'))
    elif not current_user.is_admin():
        abort(403)
    
    # Ensure file exists
    if not record.file_path:
        flash('No file associated with this record.', 'danger')
        return redirect(url_for('health_record.view'))
    
    directory = os.path.join(current_app.root_path, os.path.dirname(record.file_path))
    filename = os.path.basename(record.file_path)
    
    return send_from_directory(directory, filename, as_attachment=True)

# Chat routes
@chat_bp.route('/')
@login_required
def index():
    # Get all users this user has chatted with
    sent_to_users = db.session.query(User).join(
        Message, User.id == Message.receiver_id
    ).filter(
        Message.sender_id == current_user.id
    ).distinct().all()
    
    received_from_users = db.session.query(User).join(
        Message, User.id == Message.sender_id
    ).filter(
        Message.receiver_id == current_user.id
    ).distinct().all()
    
    # Combine and remove duplicates
    chat_users = list(set(sent_to_users + received_from_users))
    
    # For patients, also show all doctors they've had appointments with
    if current_user.is_patient():
        doctors = db.session.query(User).join(
            Doctor, User.id == Doctor.user_id
        ).join(
            Appointment, Doctor.id == Appointment.doctor_id
        ).filter(
            Appointment.patient_id == current_user.patient.id
        ).distinct().all()
        
        # Add doctors they haven't chatted with yet
        for doctor in doctors:
            if doctor not in chat_users:
                chat_users.append(doctor)
    
    # For doctors, also show all patients they've had appointments with
    elif current_user.is_doctor():
        patients = db.session.query(User).join(
            Patient, User.id == Patient.user_id
        ).join(
            Appointment, Patient.id == Appointment.patient_id
        ).filter(
            Appointment.doctor_id == current_user.doctor.id
        ).distinct().all()
        
        # Add patients they haven't chatted with yet
        for patient in patients:
            if patient not in chat_users:
                chat_users.append(patient)
    
    return render_template('chat/index.html', chat_users=chat_users)

@chat_bp.route('/room/<int:user_id>', methods=['GET', 'POST'])
@login_required
def room(user_id):
    other_user = User.query.get_or_404(user_id)
    
    # Check if users should be allowed to chat
    if current_user.is_patient() and other_user.is_doctor():
        # Check if patient has appointment with this doctor
        appointment_exists = Appointment.query.filter_by(
            patient_id=current_user.patient.id,
            doctor_id=other_user.doctor.id
        ).first()
        
        if not appointment_exists:
            flash('You cannot chat with a doctor you have not booked an appointment with.', 'danger')
            return redirect(url_for('chat.index'))
    
    elif current_user.is_doctor() and other_user.is_patient():
        # Check if doctor has appointment with this patient
        appointment_exists = Appointment.query.filter_by(
            doctor_id=current_user.doctor.id,
            patient_id=other_user.patient.id
        ).first()
        
        if not appointment_exists:
            flash('You cannot chat with a patient who has not booked an appointment with you.', 'danger')
            return redirect(url_for('chat.index'))
    
    # Handle message sending
    form = MessageForm()
    form.receiver_id.data = user_id  # Hidden field
    
    if form.validate_on_submit():
        message = Message(
            sender_id=current_user.id,
            receiver_id=user_id,
            content=form.content.data
        )
        
        db.session.add(message)
        db.session.commit()
        
        return redirect(url_for('chat.room', user_id=user_id))
    
    # Get all messages between these users
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()
    
    # Mark received messages as read
    unread_messages = Message.query.filter_by(
        sender_id=user_id,
        receiver_id=current_user.id,
        is_read=False
    ).all()
    
    for msg in unread_messages:
        msg.is_read = True
    
    db.session.commit()
    
    return render_template('chat/room.html', other_user=other_user, messages=messages, form=form)

# Feedback routes
@feedback_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if not current_user.is_patient():
        abort(403)
    
    if not current_user.patient:
        return redirect(url_for('auth.complete_profile'))
    
    form = FeedbackForm()
    
    # Populate appointment dropdown with completed appointments
    completed_appointments = Appointment.query.filter_by(
        patient_id=current_user.patient.id,
        status='completed'
    ).all()
    
    form.appointment_id.choices = [(a.id, f"Dr. {a.doctor.first_name} {a.doctor.last_name} - {a.date.strftime('%Y-%m-%d')}") 
                                  for a in completed_appointments]
    
    if not completed_appointments:
        flash('You don\'t have any completed appointments to provide feedback for.', 'info')
        return redirect(url_for('patient.dashboard'))
    
    if form.validate_on_submit():
        # Check if feedback already exists
        existing_feedback = Feedback.query.filter_by(
            patient_id=current_user.patient.id,
            appointment_id=form.appointment_id.data
        ).first()
        
        if existing_feedback:
            flash('You have already submitted feedback for this appointment.', 'danger')
            return redirect(url_for('feedback.submit'))
        
        feedback = Feedback(
            patient_id=current_user.patient.id,
            appointment_id=form.appointment_id.data,
            rating=form.rating.data,
            comments=form.comments.data
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('patient.dashboard'))
    
    return render_template('feedback/submit.html', form=form)

@feedback_bp.route('/view')
@login_required
def view():
    if current_user.is_doctor():
        # Get feedback for this doctor
        feedback_list = Feedback.query.join(
            Appointment, Feedback.appointment_id == Appointment.id
        ).filter(
            Appointment.doctor_id == current_user.doctor.id
        ).order_by(Feedback.created_at.desc()).all()
        
        return render_template('feedback/view.html', feedback=feedback_list)
    else:
        abort(403)
