from django.urls import path
from . import views

app_name = 'medical_records'

urlpatterns = [
    # Medical Records
    path('', views.record_list, name='record_list'),
    path('<int:pk>/', views.record_detail, name='record_detail'),
    
    # Add/Edit Records
    path('add/', views.add_record, name='add_record'),
    path('<int:pk>/edit/', views.edit_record, name='edit_record'),
    
    # Prescriptions
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    path('prescriptions/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('record/<int:record_id>/add-prescription/', views.add_prescription, name='add_prescription'),
    path('prescriptions/<int:prescription_id>/edit/', views.edit_prescription, name='edit_prescription'),
    
    # Doctor-Patient Records
    path('patients/', views.patient_records, name='patient_records'),
    path('patients/<int:patient_id>/', views.patient_records, name='patient_records_detail'),
    
    # File Download
    path('<int:pk>/download/', views.download_record_file, name='download_record_file'),
]