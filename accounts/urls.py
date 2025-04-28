from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # User dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # User profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Doctor listings
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/<int:pk>/', views.doctor_detail, name='doctor_detail'),
    
    # Doctor API
    path('api/doctors/<int:pk>/', views.doctor_info_api, name='doctor_info_api'),
    
    # For admin
    path('admin/doctors/', views.admin_doctor_list, name='admin_doctor_list'),
    path('admin/patients/', views.admin_patient_list, name='admin_patient_list'),
]