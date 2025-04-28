from django.urls import path
from . import views

app_name = 'medical_records'

urlpatterns = [
    # View records
    path('', views.record_list, name='record_list'),
    path('<int:pk>/', views.record_detail, name='record_detail'),
    
    # Create, update records
    path('add/', views.add_record, name='add_record'),
    path('<int:pk>/edit/', views.edit_record, name='edit_record'),
    
    # Prescriptions
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    path('prescriptions/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('prescriptions/add/', views.add_prescription, name='add_prescription'),
    
    # Doctors can see their patients' records
    path('patient/<int:patient_id>/records/', views.patient_records, name='patient_records'),
    
    # Download files
    path('<int:pk>/download/', views.download_record_file, name='download_record_file'),
]