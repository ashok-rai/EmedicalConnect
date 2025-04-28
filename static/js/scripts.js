// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Appointment booking - Doctor selection
    const doctorSelect = document.getElementById('id_doctor');
    const doctorInfo = document.getElementById('doctor-info');
    
    if (doctorSelect && doctorInfo) {
        doctorSelect.addEventListener('change', function() {
            const doctorId = this.value;
            if (doctorId) {
                // Show loading spinner
                doctorInfo.innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
                
                // Fetch doctor details - In a real app this would be an AJAX call
                setTimeout(() => {
                    fetch(`/api/doctors/${doctorId}/`)
                        .then(response => response.json())
                        .then(data => {
                            const doctorDetails = `
                                <div class="card mt-3">
                                    <div class="card-body">
                                        <h5 class="card-title">Dr. ${data.first_name} ${data.last_name}</h5>
                                        <p class="card-text">${data.specialization}</p>
                                        <p class="card-text"><small class="text-muted">${data.experience_years} years of experience</small></p>
                                        <p class="card-text">${data.bio}</p>
                                    </div>
                                </div>
                            `;
                            doctorInfo.innerHTML = doctorDetails;
                        })
                        .catch(error => {
                            doctorInfo.innerHTML = '<div class="alert alert-danger">Failed to load doctor information</div>';
                        });
                }, 500);
            } else {
                doctorInfo.innerHTML = '';
            }
        });
    }
    
    // Appointment date picker - Disable past dates
    const datePicker = document.getElementById('id_date');
    if (datePicker) {
        const today = new Date();
        const formattedDate = today.toISOString().split('T')[0];
        datePicker.setAttribute('min', formattedDate);
    }
    
    // Confirm deletion modals
    const confirmButtons = document.querySelectorAll('.confirm-action');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm(this.getAttribute('data-confirm-message') || 'Are you sure you want to perform this action?')) {
                e.preventDefault();
            }
        });
    });
    
    // Star rating system for feedback
    const ratingStars = document.querySelectorAll('.rating-stars i');
    const ratingInput = document.getElementById('id_rating');
    
    if (ratingStars.length > 0 && ratingInput) {
        // Set initial rating if present
        const initialRating = ratingInput.value;
        if (initialRating) {
            updateStars(initialRating);
        }
        
        // Handle star click
        ratingStars.forEach((star, index) => {
            star.addEventListener('click', () => {
                const rating = index + 1;
                ratingInput.value = rating;
                updateStars(rating);
            });
            
            star.addEventListener('mouseover', () => {
                const rating = index + 1;
                highlightStars(rating);
            });
            
            star.addEventListener('mouseout', () => {
                const currentRating = ratingInput.value || 0;
                updateStars(currentRating);
            });
        });
    }
    
    function updateStars(rating) {
        ratingStars.forEach((star, index) => {
            if (index < rating) {
                star.classList.remove('far');
                star.classList.add('fas');
            } else {
                star.classList.remove('fas');
                star.classList.add('far');
            }
        });
    }
    
    function highlightStars(rating) {
        ratingStars.forEach((star, index) => {
            if (index < rating) {
                star.classList.remove('far');
                star.classList.add('fas');
            } else {
                star.classList.remove('fas');
                star.classList.add('far');
            }
        });
    }
    
    // Message chat functionality
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const messageContainer = document.getElementById('message-container');
    
    if (chatForm && messageInput && messageContainer) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const message = messageInput.value.trim();
            if (message) {
                // In a real app, this would be an AJAX post request
                // For demo, we'll just append the message to the UI
                const currentUser = document.getElementById('current-user-id').value;
                const messageHtml = `
                    <div class="message message-sent mb-3">
                        <div class="message-content bg-primary text-white p-3 rounded-3">
                            ${message}
                        </div>
                        <div class="message-time text-end">
                            <small class="text-muted">Just now</small>
                        </div>
                    </div>
                `;
                
                messageContainer.insertAdjacentHTML('beforeend', messageHtml);
                messageInput.value = '';
                
                // Scroll to bottom of chat
                messageContainer.scrollTop = messageContainer.scrollHeight;
            }
        });
    }
    
    // Auto-scroll chat to bottom on page load
    if (messageContainer) {
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
    
    // File upload preview
    const fileInput = document.getElementById('id_file');
    const filePreview = document.getElementById('file-preview');
    
    if (fileInput && filePreview) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    const fileName = fileInput.files[0].name;
                    const fileType = fileName.split('.').pop().toLowerCase();
                    
                    let previewHtml = '';
                    
                    if (['jpg', 'jpeg', 'png', 'gif'].includes(fileType)) {
                        previewHtml = `
                            <div class="mt-3">
                                <p class="mb-2">File Preview:</p>
                                <img src="${e.target.result}" class="img-fluid img-thumbnail" style="max-height: 200px;">
                            </div>
                        `;
                    } else {
                        previewHtml = `
                            <div class="mt-3">
                                <p class="mb-2">File Selected:</p>
                                <div class="alert alert-info">
                                    <i class="fas fa-file me-2"></i> ${fileName}
                                </div>
                            </div>
                        `;
                    }
                    
                    filePreview.innerHTML = previewHtml;
                }
                
                reader.readAsDataURL(this.files[0]);
            } else {
                filePreview.innerHTML = '';
            }
        });
    }
});