"""
URL configuration for emedic project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # User authentication (Django AllAuth)
    path('accounts/', include('allauth.urls')),
    
    # Local apps
    path('', include('accounts.urls')),
    path('appointments/', include('appointments.urls')),
    path('records/', include('medical_records.urls')),
    path('messages/', include('messaging.urls')),
    
    # Django Postman (messaging)
    path('postman/', include('postman.urls', namespace='postman')),
    
    # Static pages
    path('about/', TemplateView.as_view(template_name='pages/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='pages/contact.html'), name='contact'),
    path('privacy/', TemplateView.as_view(template_name='pages/privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='pages/terms.html'), name='terms'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
