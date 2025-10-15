from rest_framework import serializers
from .models import Conversation, Message
from accounts.serializers import CustomUserSerializer

class ConversationSerializer(serializers.ModelSerializer):
    participants = CustomUserSerializer(many=True, read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'conversation_type', 'name', 'created_by', 'created_at', 'updated_at', 'display_name']
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Only add participants if instance is a model instance (not just data)
        if hasattr(instance, 'participants'):
            representation['participants'] = CustomUserSerializer(instance.participants.all(), many=True).data
        return representation
    
    def get_display_name(self, obj):
        # Get the current user from context if available
        request = self.context.get('request')
        user = request.user if request else None
        return obj.get_display_name(user)
        
class MessageSerializer(serializers.ModelSerializer):
    sender = CustomUserSerializer(read_only=True)
    participants = serializers.SerializerMethodField()
    class Meta:
        model = Message
        fields = ['id', 'sender', 'conversation', 'content', 'created_at', 'participants']
        
    def get_participants(self, obj):
        return CustomUserSerializer(obj.conversation.participants.all(), many=True).data

class CreateMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'content', 'created_at']

class CreateGroupConversationSerializer(serializers.ModelSerializer):
    participants = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        help_text="List of user IDs to add to the group"
    )
    
    class Meta:
        model = Conversation
        fields = ['name', 'participants']
    
    def validate_participants(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Group must have at least 2 participants")
        if len(value) > 50:  # Reasonable limit for group size
            raise serializers.ValidationError("Group cannot have more than 50 participants")
        return value
    
    def create(self, validated_data):
        participants_data = validated_data.pop('participants')
        conversation = Conversation.objects.create(
            conversation_type='group',
            created_by=self.context['request'].user,
            **validated_data
        )
        conversation.participants.set(participants_data)
        return conversation
        