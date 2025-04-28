from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Book an appointment
    path('book/', views.book_appointment, name='book_appointment'),
    
    # View, manage appointments
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('<int:pk>/reschedule/', views.reschedule_appointment, name='reschedule_appointment'),
    
    # For doctors
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/<int:pk>/complete/', views.complete_appointment, name='complete_appointment'),
    path('doctor/<int:pk>/add-notes/', views.add_appointment_notes, name='add_appointment_notes'),
    
    # Feedback
    path('<int:pk>/feedback/', views.add_feedback, name='add_feedback'),
    path('feedback/', views.view_feedback, name='view_feedback'),
    
    # For Admin
    path('admin/all/', views.admin_all_appointments, name='admin_all_appointments'),
]