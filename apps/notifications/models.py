# apps/notifications/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Notification(models.Model):
    """User notifications model"""
    
    class NotificationType(models.TextChoices):
        ORDER_UPDATE = 'ORDER_UPDATE', 'Order Update'
        PAYMENT_SUCCESS = 'PAYMENT_SUCCESS', 'Payment Success'
        PAYMENT_FAILED = 'PAYMENT_FAILED', 'Payment Failed'
        SYSTEM_ALERT = 'SYSTEM_ALERT', 'System Alert'
        PROMOTION = 'PROMOTION', 'Promotion'
        GENERAL = 'GENERAL', 'General'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User receiving the notification"
    )
    title = models.CharField(
        max_length=200,
        help_text="Notification title"
    )
    message = models.TextField(
        help_text="Notification message"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
        help_text="Type of notification"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the notification has been read"
    )
    url = models.URLField(
        blank=True,
        help_text="Optional URL to redirect when clicked"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def get_type_icon(self):
        """Get icon for notification type"""
        icons = {
            self.NotificationType.ORDER_UPDATE: 'bi-bag-check',
            self.NotificationType.PAYMENT_SUCCESS: 'bi-check-circle',
            self.NotificationType.PAYMENT_FAILED: 'bi-exclamation-circle',
            self.NotificationType.SYSTEM_ALERT: 'bi-bell',
            self.NotificationType.PROMOTION: 'bi-gift',
            self.NotificationType.GENERAL: 'bi-info-circle',
        }
        return icons.get(self.notification_type, 'bi-info-circle')
    
    def get_type_color(self):
        """Get color for notification type"""
        colors = {
            self.NotificationType.ORDER_UPDATE: 'primary',
            self.NotificationType.PAYMENT_SUCCESS: 'success',
            self.NotificationType.PAYMENT_FAILED: 'danger',
            self.NotificationType.SYSTEM_ALERT: 'warning',
            self.NotificationType.PROMOTION: 'info',
            self.NotificationType.GENERAL: 'secondary',
        }
        return colors.get(self.notification_type, 'secondary')





