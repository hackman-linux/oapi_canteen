# apps/notifications/urls.py
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notification views
    path('', views.NotificationListView.as_view(), name='list'),
    path('unread/', views.UnreadNotificationsView.as_view(), name='unread'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='detail'),
    
    # Notification actions
    path('mark-read/<int:pk>/', views.mark_as_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_read'),
    path('delete/<int:pk>/', views.delete_notification, name='delete'),
    
    # Admin notification management
    path('admin/', views.AdminNotificationView.as_view(), name='admin'),
    path('admin/send/', views.SendNotificationView.as_view(), name='send'),
    path('admin/bulk/', views.BulkNotificationView.as_view(), name='bulk'),
    
    # API endpoints
    path('api/count/', views.notification_count_api, name='count_api'),
    path('api/recent/', views.recent_notifications_api, name='recent_api'),
]