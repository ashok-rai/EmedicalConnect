from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q, Max, Count
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.utils.timesince import timesince

from .models import Conversation, Message, Notification

User = get_user_model()


@login_required
def conversation_list(request):
    """Display a list of all conversations for the current user"""
    
    # Get all conversations that include the current user
    conversations = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related('participants', 'messages')
    
    # Annotate each conversation with the last message and unread count
    conversations = conversations.annotate(
        last_message_time=Max('messages__timestamp'),
        unread_count=Count('messages', filter=Q(
            messages__is_read=False,
            messages__sender__id__gt=0,  # Prevents NULL issues
            messages__sender__id=request.user.id
        ))
    ).order_by('-last_message_time')
    
    # Prepare context data for conversations
    conversations_data = []
    for conversation in conversations:
        other_user = conversation.get_other_participant(request.user)
        if not other_user:
            continue
            
        last_message = conversation.messages.order_by('-timestamp').first()
        
        conversations_data.append({
            'conversation': conversation,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': conversation.unread_count
        })
    
    # Count total unread messages
    unread_total = sum(c['unread_count'] for c in conversations_data)
    
    # Get all possible users for new conversation (exclude existing conversations)
    user_ids_in_conversations = Conversation.objects.filter(
        participants=request.user
    ).values_list('participants', flat=True).distinct()
    
    potential_recipients = User.objects.exclude(
        id__in=user_ids_in_conversations
    ).exclude(
        id=request.user.id
    )
    
    # For doctor users, show only patients as potential recipients
    if request.user.is_doctor():
        potential_recipients = potential_recipients.filter(role='patient')
    
    # For patient users, show only doctors as potential recipients 
    elif request.user.is_patient():
        potential_recipients = potential_recipients.filter(role='doctor')
    
    context = {
        'conversations': conversations_data,
        'unread_total': unread_total,
        'potential_recipients': potential_recipients,
        'active_tab': 'messages',
    }
    
    return render(request, 'messaging/conversation_list.html', context)


@login_required
def conversation_detail(request, pk):
    """Display a specific conversation and its messages"""
    
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related('participants', 'messages'),
        pk=pk, 
        participants=request.user
    )
    
    other_user = conversation.get_other_participant(request.user)
    
    
    # Mark all messages from the other user as read
    unread_messages = Message.objects.filter(
        conversation=conversation,
        sender=other_user,
        is_read=False
    )
    unread_messages.update(is_read=True)
    
    # Get all messages for the conversation
    messages_list = conversation.messages.order_by('timestamp')
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'other_user': other_user,
        'active_tab': 'messages',
    }
    
    return render(request, 'messaging/conversation_detail.html', context)


@login_required
def new_conversation(request):
    """Create a new conversation selecting a user"""
    
    if request.user.is_doctor():
        # Doctors can message patients
        potential_recipients = User.objects.filter(role='patient')
    elif request.user.is_patient():
        # Patients can message doctors
        potential_recipients = User.objects.filter(role='doctor')
    else:
        # Admins can message anyone
        potential_recipients = User.objects.exclude(id=request.user.id)
    
    # Get all users that already have a conversation with the current user
    existing_conversations = Conversation.objects.filter(
        participants=request.user
    ).values_list('participants', flat=True)
    
    # Exclude users that already have a conversation with the current user
    potential_recipients = potential_recipients.exclude(
        id__in=existing_conversations
    ).exclude(id=request.user.id)
    
    context = {
        'potential_recipients': potential_recipients,
        'active_tab': 'messages',
    }
    
    return render(request, 'messaging/new_conversation.html', context)


@login_required
def start_conversation(request, user_id):
    """Start a new conversation with a specific user"""
    
    other_user = get_object_or_404(User, pk=user_id)
    
    # Check if a conversation already exists between these users
    existing_conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if existing_conversation:
        # If conversation exists, redirect to it
        return redirect('messaging:conversation_detail', pk=existing_conversation.id)
    
    # Create a new conversation
    conversation = Conversation.objects.create()
    conversation.participants.add(request.user, other_user)
    conversation.save()
    
    # Create initial message if POST data is provided
    if request.method == 'POST' and request.POST.get('content'):
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=request.POST.get('content')
        )
        
        # Create notification for the recipient
        Notification.objects.create(
            user=other_user,
            notification_type='message',
            title=f'New message from {request.user.get_full_name() or request.user.email}',
            message=message.content[:50] + ('...' if len(message.content) > 50 else ''),
            related_url=f'/messages/{conversation.id}/'
        )
    
    return redirect('messaging:conversation_detail', pk=conversation.id)


@login_required
def send_message(request):
    """Send a message to a conversation (AJAX)"""
    
    if request.method != 'POST':
        return HttpResponseBadRequest('POST request required')
    
    conversation_id = request.POST.get('conversation_id')
    content = request.POST.get('content')
    
    if not conversation_id or not content:
        return HttpResponseBadRequest('Missing required fields')
    
    # Get the conversation and verify the user is a participant
    conversation = get_object_or_404(
        Conversation, 
        pk=conversation_id, 
        participants=request.user
    )
    
    # Create the message
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content
    )
    
    # Update the conversation's timestamp
    conversation.updated_at = timezone.now()
    conversation.save()
    
    # Create notification for the recipient
    other_user = conversation.get_other_participant(request.user)
    if other_user:
        Notification.objects.create(
            user=other_user,
            notification_type='message',
            title=f'New message from {request.user.get_full_name() or request.user.email}',
            message=content[:50] + ('...' if len(content) > 50 else ''),
            related_url=f'/messages/{conversation.id}/'
        )
    
    # Return the created message as JSON
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'timestamp': message.timestamp.strftime('%b %d, %Y, %I:%M %p'),
            'sender_id': message.sender.id,
            'sender_name': message.sender.get_full_name() or message.sender.email
        }
    })


@login_required
def mark_as_read(request, pk):
    """Mark a message as read"""
    
    message = get_object_or_404(
        Message, 
        pk=pk, 
        conversation__participants=request.user
    )
    
    # Only mark as read if user is not the sender
    if message.sender != request.user:
        message.is_read = True
        message.save()
    
    return JsonResponse({'success': True})


@login_required
def notification_list(request):
    """Display all notifications for the current user"""
    
    # Get all notifications for the current user, newest first
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    context = {
        'notifications': notifications,
        'active_tab': 'notifications',
    }
    
    return render(request, 'messaging/notification_list.html', context)


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    
    Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).update(is_read=True)
    
    messages.success(request, 'All notifications marked as read.')
    return redirect('messaging:notification_list')


@login_required
def api_notifications(request):
    """API endpoint to get recent notifications for the current user"""
    
    # Get unread count
    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    # Get recent notifications (limit to 5)
    recent_notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Format notifications for JSON response
    notifications_data = []
    for notification in recent_notifications:
        notifications_data.append({
            'id': notification.id,
            'notification_type': notification.notification_type,
            'title': notification.title,
            'message': notification.message,
            'related_url': notification.related_url,
            'is_read': notification.is_read,
            'time_ago': timesince(notification.created_at) + ' ago'
        })
    
    return JsonResponse({
        'success': True,
        'unread_count': unread_count,
        'notifications': notifications_data
    })


@login_required
@require_POST
def api_mark_notification_read(request, pk):
    """API endpoint to mark a notification as read"""
    
    notification = get_object_or_404(
        Notification,
        pk=pk,
        user=request.user
    )
    
    notification.is_read = True
    notification.save()
    
    return JsonResponse({'success': True})