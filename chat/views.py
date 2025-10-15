from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, CreateMessageSerializer, CreateGroupConversationSerializer

User = get_user_model()

class ConversationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related('participants')
    
    def create(self, request, *args, **kwargs):
        conversation_type = request.data.get('conversation_type', 'direct')
        
        if conversation_type == 'group':
            # Handle group chat creation
            serializer = CreateGroupConversationSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                # Ensure the creator is included in participants
                participants_data = serializer.validated_data['participants']
                if request.user.id not in participants_data:
                    participants_data.append(request.user.id)
                
                conversation = serializer.save()
                return Response(ConversationSerializer(conversation, context={'request': request}).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            # Handle direct chat creation (existing logic)
            participants_data = request.data.get('participants', [])
            participants = User.objects.filter(id__in=participants_data)
            
            if len(participants) != 2:
                return Response({"error": "Direct conversation must have exactly 2 participants"}, status=status.HTTP_400_BAD_REQUEST)
            
            if len(participants_data) != 2:
                return Response({"error": "Direct conversation must have exactly 2 participants"}, status=status.HTTP_400_BAD_REQUEST)
            
            if str(request.user.id) not in map(str, participants_data):
                return Response({"error": "You must be a participant in the conversation"}, status=status.HTTP_400_BAD_REQUEST)
            
            existing_conversation = Conversation.objects.filter(participants__id = participants_data[0]).filter(participants__id = participants_data[1]).distinct()
            if existing_conversation.exists():
                return Response(
                    {"error": "Conversation already exists between these participants"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            conversation = Conversation.objects.create(conversation_type='direct')
            conversation.participants.set(participants)
            conversation.save()
            return Response(self.get_serializer(conversation).data, status=status.HTTP_201_CREATED)
        

class MessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_id')
        conversation = self.get_conversation(conversation_id)
        
        return Message.objects.filter(conversation=conversation).order_by('created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateMessageSerializer
        return MessageSerializer
    
    def get_conversation(self, conversation_id):
        return get_object_or_404(Conversation, id=conversation_id, participants=self.request.user)
    
    def perform_create(self, request, *args, **kwargs):
        conversation_id = self.kwargs.get('conversation_id')
        conversation = self.get_conversation(conversation_id)
        serializer = CreateMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sender=self.request.user, conversation=conversation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
class MessageRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_id')
        conversation = self.get_conversation(conversation_id)
        return Message.objects.filter(conversation=conversation)
    
    def get_conversation(self, conversation_id):
        return get_object_or_404(Conversation, id=conversation_id, participants=self.request.user)
    
    def perform_destroy(self, instance):
        if instance.sender != self.request.user:
            return Response({"error": "You are not the sender of this message"}, status=status.HTTP_403_FORBIDDEN)
        instance.delete()
        return Response({"message": "Message deleted successfully"}, status=status.HTTP_200_OK)


class GroupMemberManagementView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, conversation_id):
        """Add members to a group chat"""
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        
        if not conversation.is_group_chat():
            return Response({"error": "This is not a group chat"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user is the creator or has permission to add members
        if conversation.created_by != request.user:
            return Response({"error": "Only the group creator can add members"}, status=status.HTTP_403_FORBIDDEN)
        
        member_ids = request.data.get('member_ids', [])
        if not member_ids:
            return Response({"error": "No member IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        new_members = User.objects.filter(id__in=member_ids)
        if len(new_members) != len(member_ids):
            return Response({"error": "Some users not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Add new members
        conversation.participants.add(*new_members)
        
        return Response({
            "message": f"Added {len(new_members)} members to the group",
            "conversation": ConversationSerializer(conversation, context={'request': request}).data
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, conversation_id):
        """Remove members from a group chat"""
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        
        if not conversation.is_group_chat():
            return Response({"error": "This is not a group chat"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user is the creator or has permission to remove members
        if conversation.created_by != request.user:
            return Response({"error": "Only the group creator can remove members"}, status=status.HTTP_403_FORBIDDEN)
        
        member_ids = request.data.get('member_ids', [])
        if not member_ids:
            return Response({"error": "No member IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Don't allow removing the creator
        if request.user.id in member_ids:
            return Response({"error": "Cannot remove the group creator"}, status=status.HTTP_400_BAD_REQUEST)
        
        members_to_remove = User.objects.filter(id__in=member_ids)
        conversation.participants.remove(*members_to_remove)
        
        return Response({
            "message": f"Removed {len(members_to_remove)} members from the group",
            "conversation": ConversationSerializer(conversation, context={'request': request}).data
        }, status=status.HTTP_200_OK)
        
        