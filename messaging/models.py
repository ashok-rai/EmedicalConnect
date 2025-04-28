from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User


class Conversation(models.Model):
    """Model for a conversation between users"""
    
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation {self.id} - {', '.join([user.email for user in self.participants.all()])}"
    
    def get_other_participant(self, user=None):
        """Get the other participant in a conversation."""
        if user is None:
            return self.participants.first()
        return self.participants.exclude(id=user.id).first()
    
    def get_unread_messages_count(self):
        """Get the count of unread messages for a user in this conversation."""
        # if user is None:
        #     return self.messages.filter(is_read=False).count()
        sender = self.get_other_participant()
        print('sender', sender)
        return self.messages.all().filter(is_read=False, sender=sender).count()


class Message(models.Model):
    """Model for messages in a conversation"""
    
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='messages_sent'
    )
    content = models.TextField()
    attachment = models.FileField(upload_to='message_attachments/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message from {self.sender.email} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class Notification(models.Model):
    """Model for system notifications"""
    
    NOTIFICATION_TYPES = (
        ('message', 'New Message'),
        ('appointment', 'Appointment Update'),
        ('prescription', 'New Prescription'),
        ('medical_record', 'Medical Record Update'),
        ('system', 'System Notification'),
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user.email}"
