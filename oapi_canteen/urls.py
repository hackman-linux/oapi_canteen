# oapi_canteen/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Root redirect to dashboard
    path('', lambda request: redirect('dashboard:home')),
    
    # App URLs
    path('dashboard/', include('apps.dashboard.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('menu/', include('apps.menu.urls')),
    path('orders/', include('apps.orders.urls')),
    path('payments/', include('apps.payments.urls')),
    path('notifications/', include('apps.notifications.urls')),
    
    # Authentication URLs (Django built-in)
    path('auth/', include('django.contrib.auth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)