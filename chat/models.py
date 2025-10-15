from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Prefetch

User = get_user_model()

class ConversationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            Prefetch('participants', queryset=User.objects.all())
        )

class Conversation(models.Model):
    CONVERSATION_TYPES = [
        ('direct', 'Direct Chat'),
        ('group', 'Group Chat'),
    ]
    
    participants = models.ManyToManyField(User, related_name='conversations')
    conversation_type = models.CharField(max_length=10, choices=CONVERSATION_TYPES, default='direct')
    name = models.CharField(max_length=100, blank=True, null=True)  # For group chats
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_conversations', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ConversationManager()

    def __str__(self):
        if self.conversation_type == 'group':
            return f"Group: {self.name or 'Unnamed Group'}"
        else:
            participant_names = ", ".join([user.username for user in self.participants.all()])
            return f"Conversation between {participant_names}"
    
    def is_group_chat(self):
        return self.conversation_type == 'group'
    
    def get_display_name(self, user=None):
        if self.conversation_type == 'group':
            return self.name or 'Unnamed Group'
        else:
            # For direct chats, show the other participant's name
            if user:
                other_participants = self.participants.exclude(id=user.id)
                if other_participants.exists():
                    return other_participants.first().username
            return "Direct Chat"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        # Get all participants except the sender
        other_participants = self.conversation.participants.exclude(id=self.sender.id)
        participant_names = ", ".join([user.username for user in other_participants])
        return f"Message from {self.sender.username} to {participant_names}"