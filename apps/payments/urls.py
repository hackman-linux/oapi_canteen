# apps/payments/urls.py
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment processing
    path('process/', views.ProcessPaymentView.as_view(), name='process'),
    path('success/', views.PaymentSuccessView.as_view(), name='success'),
    path('cancel/', views.PaymentCancelView.as_view(), name='cancel'),
    path('failed/', views.PaymentFailedView.as_view(), name='failed'),
    
    # Payment details
    path('<uuid:payment_id>/', views.PaymentDetailView.as_view(), name='detail'),
    path('order/<str:order_number>/', views.OrderPaymentView.as_view(), name='order_payment'),
    
    # Admin payment management
    path('admin/', views.AdminPaymentListView.as_view(), name='admin_list'),
    path('admin/failed/', views.FailedPaymentsView.as_view(), name='admin_failed'),
    path('admin/<uuid:payment_id>/', views.AdminPaymentDetailView.as_view(), name='admin_detail'),
    
    # Webhooks
    path('webhook/orange/', views.orange_webhook, name='orange_webhook'),
    path('webhook/mtn/', views.mtn_webhook, name='mtn_webhook'),
    
    # API endpoints
    path('api/status/<uuid:payment_id>/', views.payment_status_api, name='status_api'),
    path('api/retry/<uuid:payment_id>/', views.retry_payment_api, name='retry_api'),
]