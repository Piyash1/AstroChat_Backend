from django.contrib import admin
from .models import CustomUser
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')
    ordering = ('id',)
    



