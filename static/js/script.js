// MedBooking System JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });

    // Appointment date validation
    const appointmentDateInput = document.getElementById('date');
    if (appointmentDateInput) {
        const today = new Date().toISOString().split('T')[0];
        appointmentDateInput.setAttribute('min', today);
        
        appointmentDateInput.addEventListener('change', function() {
            if (this.value < today) {
                alert('Cannot select a date in the past');
                this.value = today;
            }
        });
    }

    // Chat scroll to bottom
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Health record type selection
    const recordTypeSelect = document.getElementById('record_type');
    const descriptionField = document.getElementById('description');
    
    if (recordTypeSelect && descriptionField) {
        recordTypeSelect.addEventListener('change', function() {
            if (this.value === 'prescription') {
                descriptionField.placeholder = 'Enter medication details, dosage, and instructions';
            } else if (this.value === 'lab_report') {
                descriptionField.placeholder = 'Enter test name, results, and reference ranges';
            } else if (this.value === 'doctor_note') {
                descriptionField.placeholder = 'Enter diagnosis, observations, and recommendations';
            } else {
                descriptionField.placeholder = 'Enter description';
            }
        });
    }

    // Feedback star rating visualization
    const ratingSelect = document.getElementById('rating');
    const ratingStars = document.querySelector('.rating-stars');
    
    if (ratingSelect && ratingStars) {
        function updateStars(rating) {
            let starsHTML = '';
            for (let i = 1; i <= 5; i++) {
                if (i <= rating) {
                    starsHTML += '<i class="fas fa-star text-warning"></i>';
                } else {
                    starsHTML += '<i class="far fa-star text-warning"></i>';
                }
            }
            ratingStars.innerHTML = starsHTML;
        }
        
        // Initial stars
        updateStars(ratingSelect.value);
        
        // Update stars on change
        ratingSelect.addEventListener('change', function() {
            updateStars(this.value);
        });
    }

    // Appointment cancellation confirmation
    const cancelButtons = document.querySelectorAll('.cancel-appointment');
    
    if (cancelButtons.length > 0) {
        cancelButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to cancel this appointment? This action cannot be undone.')) {
                    e.preventDefault();
                }
            });
        });
    }

    // Complete appointment confirmation
    const completeButtons = document.querySelectorAll('.complete-appointment');
    
    if (completeButtons.length > 0) {
        completeButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to mark this appointment as completed?')) {
                    e.preventDefault();
                }
            });
        });
    }

    // Doctor selection for appointment booking
    const doctorSelect = document.getElementById('doctor_id');
    const doctorInfo = document.getElementById('doctor-info');
    
    if (doctorSelect && doctorInfo) {
        // We'd need to have doctor data available, so this is a placeholder
        // In a real implementation, this would fetch doctor details via AJAX or use pre-loaded data
        doctorSelect.addEventListener('change', function() {
            if (this.value) {
                doctorInfo.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
                
                // In a real implementation, this would be an AJAX call
                setTimeout(() => {
                    doctorInfo.innerHTML = '<div class="card mt-3"><div class="card-body">Doctor information would be displayed here</div></div>';
                }, 500);
            } else {
                doctorInfo.innerHTML = '';
            }
        });
    }
});
