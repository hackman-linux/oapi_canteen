# apps/dashboard/urls.py
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard home
    path('', views.DashboardHomeView.as_view(), name='home'),
    
    # User dashboard
    path('user/', views.UserDashboardView.as_view(), name='user_dashboard'),
    
    # Staff dashboards
    path('manager/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    
    # Quick actions
    path('orders/recent/', views.RecentOrdersView.as_view(), name='recent_orders'),
    path('stats/weekly/', views.WeeklyStatsView.as_view(), name='weekly_stats'),
    path('menu/popular/', views.PopularMenuView.as_view(), name='popular_menu'),
    
    # AJAX endpoints for dashboard widgets
    path('api/order-stats/', views.order_stats_api, name='order_stats_api'),
    path('api/sales-chart/', views.sales_chart_api, name='sales_chart_api'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
]