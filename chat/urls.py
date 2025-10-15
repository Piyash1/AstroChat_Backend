from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Conversation URLs
    path('conversations/', views.ConversationListCreateView.as_view(), name='conversation-list-create'),
    
    # Message URLs
    path('conversations/<int:conversation_id>/messages/', views.MessageListCreateView.as_view(), name='message-list-create'),
    path('conversations/<int:conversation_id>/messages/<int:pk>/', views.MessageRetrieveDestroyView.as_view(), name='message-retrieve-destroy'),
    
    # Group management URLs
    path('conversations/<int:conversation_id>/members/', views.GroupMemberManagementView.as_view(), name='group-member-management'),
]
