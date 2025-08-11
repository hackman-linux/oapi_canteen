# apps/notifications/views.py (basic views for the URLs we created)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView
from django.http import JsonResponse
from django.contrib import messages
from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    """List all notifications for current user"""
    model = Notification
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class UnreadNotificationsView(LoginRequiredMixin, ListView):
    """List unread notifications for current user"""
    model = Notification
    template_name = 'notifications/unread.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user, is_read=False)


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """View notification details"""
    model = Notification
    template_name = 'notifications/detail.html'
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.mark_as_read()
        return obj


@login_required
def mark_as_read(request, pk):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    messages.success(request, 'Notification marked as read.')
    return redirect('notifications:list')


@login_required
def mark_all_as_read(request):
    """Mark all notifications as read"""
    count = Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    messages.success(request, f'{count} notifications marked as read.')
    return redirect('notifications:list')


@login_required
def delete_notification(request, pk):
    """Delete notification"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    messages.success(request, 'Notification deleted.')
    return redirect('notifications:list')


class AdminNotificationView(LoginRequiredMixin, TemplateView):
    """Admin notification management"""
    template_name = 'notifications/admin.html'


class SendNotificationView(LoginRequiredMixin, TemplateView):
    """Send notification to users"""
    template_name = 'notifications/send.html'


class BulkNotificationView(LoginRequiredMixin, TemplateView):
    """Send bulk notifications"""
    template_name = 'notifications/bulk.html'


@login_required
def notification_count_api(request):
    """API endpoint for notification count"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def recent_notifications_api(request):
    """API endpoint for recent notifications"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]
    
    data = {
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.notification_type,
                'is_read': n.is_read,
                'url': n.url,
                'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
                'icon': n.get_type_icon(),
                'color': n.get_type_color(),
            }
            for n in notifications
        ]
    }
    return JsonResponse(data)