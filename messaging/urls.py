from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Conversation list and details
    path('', views.conversation_list, name='conversation_list'),
    path('<int:pk>/', views.conversation_detail, name='conversation_detail'),
    
    # Create new conversation
    path('new/', views.new_conversation, name='new_conversation'),
    path('new/<int:user_id>/', views.start_conversation, name='start_conversation'),
    
    # Send messages via AJAX/websocket
    path('send/', views.send_message, name='send_message'),
    
    # Mark messages as read
    path('read/<int:pk>/', views.mark_as_read, name='mark_as_read'),
    
    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]