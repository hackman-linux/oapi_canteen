# apps/notifications/admin.py
from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for Notification model"""
    
    list_display = (
        'title', 'user', 'notification_type', 'is_read', 'created_at'
    )
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'read_at')
    ordering = ('-created_at',)
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        count = queryset.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        self.message_user(request, f"{count} notifications marked as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        count = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None
        )
        self.message_user(request, f"{count} notifications marked as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"


