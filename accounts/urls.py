from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserInfoView, UserRegisterView, LoginView, LogoutView, UserListView

urlpatterns = [
    path('user-info/', UserInfoView.as_view(), name='user-info'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('users/', UserListView.as_view(), name='user-list'),
]
