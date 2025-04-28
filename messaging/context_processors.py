from .models import Notification, Message, Conversation

def messaging_context(request):
    """
    Context processor that adds notification and message counts to the context.
    Makes these variables available in all templates.
    """
    context = {
        'notification_count': 0,
        'unread_message_count': 0,
    }
    
    if request.user.is_authenticated:
        # Count unread notifications
        context['notification_count'] = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        # Count unread messages
        # First get all conversations the user is part of
        conversations = Conversation.objects.filter(participants=request.user)
        
        # Then count all messages in those conversations that are unread and not sent by the user
        unread_count = 0
        for conversation in conversations:
            # Find the other participant in each conversation
            other_user = conversation.get_other_participant(request.user)
            if other_user:
                # Count unread messages from that user
                conversation_unread = Message.objects.filter(
                    conversation=conversation,
                    sender=other_user,
                    is_read=False
                ).count()
                unread_count += conversation_unread
        
        context['unread_message_count'] = unread_count
        
    return context