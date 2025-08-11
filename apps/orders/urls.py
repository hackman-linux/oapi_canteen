# apps/orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Customer order views
    path('my-orders/', views.MyOrdersView.as_view(), name='my_orders'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('order/<str:order_number>/', views.OrderDetailView.as_view(), name='detail'),
    
    # Staff order management
    path('', views.OrderListView.as_view(), name='list'),
    path('pending/', views.PendingOrdersView.as_view(), name='pending'),
    path('manage/<str:order_number>/', views.ManageOrderView.as_view(), name='manage'),
    
    # Order actions
    path('update-status/', views.update_order_status, name='update_status'),
    path('cancel/<str:order_number>/', views.cancel_order, name='cancel'),
    
    # Cart management API
    path('api/cart/add/', views.add_to_cart_api, name='add_to_cart'),
    path('api/cart/update/', views.update_cart_api, name='update_cart'),
    path('api/cart/remove/', views.remove_from_cart_api, name='remove_from_cart'),
    path('api/cart/clear/', views.clear_cart_api, name='clear_cart'),
]