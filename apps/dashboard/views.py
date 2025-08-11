# apps/dashboard/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from apps.accounts.models import User
from apps.accounts.permissions import RoleRequiredMixin
from apps.menu.models import MenuItem, Category
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    """Main dashboard that routes users based on their role"""
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Redirect based on user role
        if user.role == User.UserRole.USER:
            return redirect('dashboard:user_dashboard')
        elif user.role == User.UserRole.CANTEEN_MANAGER:
            return redirect('dashboard:manager_dashboard')
        elif user.role in [User.UserRole.CANTEEN_ADMIN, User.UserRole.SYSTEM_ADMIN]:
            return redirect('dashboard:admin_dashboard')
        else:
            return redirect('dashboard:user_dashboard')


class UserDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard for regular users (customers)"""
    template_name = 'dashboard/user_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Recent orders
        recent_orders = Order.objects.filter(
            customer=user
        ).select_related('payment_method').prefetch_related('items__menu_item')[:5]
        
        # Order statistics
        total_orders = Order.objects.filter(customer=user).count()
        total_spent = Order.objects.filter(
            customer=user, 
            status=Order.OrderStatus.COMPLETED
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Favorite items (most ordered)
        favorite_items = OrderItem.objects.filter(
            order__customer=user,
            order__status=Order.OrderStatus.COMPLETED
        ).values(
            'menu_item__name', 'menu_item__id'
        ).annotate(
            total_ordered=Sum('quantity')
        ).order_by('-total_ordered')[:5]
        
        # Current cart
        cart = getattr(user, 'cart', None)
        cart_items_count = cart.get_total_items() if cart else 0
        cart_total = cart.get_total_price() if cart else Decimal('0.00')
        
        # Popular menu items
        popular_items = MenuItem.objects.filter(
            is_available=True
        ).order_by('-total_orders', '-rating')[:6]
        
        # Current order (if any pending)
        current_order = Order.objects.filter(
            customer=user,
            status__in=[Order.OrderStatus.PENDING, Order.OrderStatus.CONFIRMED, Order.OrderStatus.PREPARING]
        ).first()
        
        context.update({
            'recent_orders': recent_orders,
            'total_orders': total_orders,
            'total_spent': total_spent,
            'favorite_items': favorite_items,
            'cart_items_count': cart_items_count,
            'cart_total': cart_total,
            'popular_items': popular_items,
            'current_order': current_order,
        })
        
        return context


class ManagerDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """Dashboard for canteen managers"""
    template_name = 'dashboard/manager_dashboard.html'
    required_roles = [User.UserRole.CANTEEN_MANAGER]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        # Today's orders
        todays_orders = Order.objects.filter(created_at__date=today)
        pending_orders = todays_orders.filter(status=Order.OrderStatus.PENDING).count()
        preparing_orders = todays_orders.filter(status=Order.OrderStatus.PREPARING).count()
        ready_orders = todays_orders.filter(status=Order.OrderStatus.READY).count()
        
        # Today's revenue
        todays_revenue = todays_orders.filter(
            status=Order.OrderStatus.COMPLETED
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Week's stats
        weekly_orders = Order.objects.filter(created_at__date__gte=week_ago)
        weekly_revenue = weekly_orders.filter(
            status=Order.OrderStatus.COMPLETED
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Orders needing attention (pending validation)
        orders_needing_attention = Order.objects.filter(
            status=Order.OrderStatus.PENDING
        ).select_related('customer').prefetch_related('items__menu_item')[:10]
        
        # Most popular items this week
        popular_items_week = OrderItem.objects.filter(
            order__created_at__date__gte=week_ago,
            order__status=Order.OrderStatus.COMPLETED
        ).values(
            'menu_item__name'
        ).annotate(
            total_ordered=Sum('quantity')
        ).order_by('-total_ordered')[:5]
        
        # Payment status overview
        payment_stats = Payment.objects.filter(
            created_at__date=today
        ).aggregate(
            total_payments=Count('id'),
            completed_payments=Count('id', filter=Q(status=Payment.PaymentStatus.COMPLETED)),
            pending_payments=Count('id', filter=Q(status=Payment.PaymentStatus.PENDING)),
            failed_payments=Count('id', filter=Q(status=Payment.PaymentStatus.FAILED))
        )
        
        context.update({
            'todays_orders_count': todays_orders.count(),
            'pending_orders': pending_orders,
            'preparing_orders': preparing_orders,
            'ready_orders': ready_orders,
            'todays_revenue': todays_revenue,
            'weekly_orders_count': weekly_orders.count(),
            'weekly_revenue': weekly_revenue,
            'orders_needing_attention': orders_needing_attention,
            'popular_items_week': popular_items_week,
            'payment_stats': payment_stats,
        })
        
        return context


class AdminDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """Dashboard for canteen and system administrators"""
    template_name = 'dashboard/admin_dashboard.html'
    required_roles = [User.UserRole.CANTEEN_ADMIN, User.UserRole.SYSTEM_ADMIN]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.now().date()
        month_ago = today - timedelta(days=30)
        
        # Overall statistics
        total_users = User.objects.filter(is_active=True).count()
        total_menu_items = MenuItem.objects.filter(is_available=True).count()
        total_orders = Order.objects.count()
        total_revenue = Order.objects.filter(
            status=Order.OrderStatus.COMPLETED
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Monthly stats
        monthly_orders = Order.objects.filter(created_at__date__gte=month_ago)
        monthly_revenue = monthly_orders.filter(
            status=Order.OrderStatus.COMPLETED
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # User role distribution
        user_roles = User.objects.values('role').annotate(count=Count('role'))
        
        # Menu categories with item counts
        categories_stats = Category.objects.annotate(
            active_items=Count('menu_items', filter=Q(menu_items__is_available=True))
        ).order_by('-active_items')
        
        # Top customers (by order value)
        top_customers = User.objects.annotate(
            total_spent=Sum('orders__total_amount', 
                          filter=Q(orders__status=Order.OrderStatus.COMPLETED))
        ).filter(total_spent__isnull=False).order_by('-total_spent')[:10]
        
        # Recent system activity
        recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:5]
        recent_payments = Payment.objects.select_related('user', 'order').order_by('-created_at')[:5]
        
        # Performance metrics
        avg_order_value = Order.objects.filter(
            status=Order.OrderStatus.COMPLETED
        ).aggregate(avg=Sum('total_amount'))['avg'] or Decimal('0.00')
        
        if total_orders > 0:
            avg_order_value = total_revenue / total_orders
        
        context.update({
            'total_users': total_users,
            'total_menu_items': total_menu_items,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'monthly_orders_count': monthly_orders.count(),
            'monthly_revenue': monthly_revenue,
            'user_roles': user_roles,
            'categories_stats': categories_stats,
            'top_customers': top_customers,
            'recent_orders': recent_orders,
            'recent_payments': recent_payments,
            'avg_order_value': avg_order_value,
        })
        
        return context


class RecentOrdersView(LoginRequiredMixin, TemplateView):
    """View for displaying recent orders"""
    template_name = 'dashboard/components/recent_orders.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.role == User.UserRole.USER:
            # Regular users see their own orders
            orders = Order.objects.filter(customer=user).order_by('-created_at')[:10]
        else:
            # Staff see all orders
            orders = Order.objects.select_related('customer').order_by('-created_at')[:10]
        
        context['orders'] = orders
        return context


class WeeklyStatsView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """View for weekly statistics"""
    template_name = 'dashboard/components/weekly_stats.html'
    required_roles = [User.UserRole.CANTEEN_MANAGER, User.UserRole.CANTEEN_ADMIN, User.UserRole.SYSTEM_ADMIN]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Generate weekly data for the past 7 days
        weekly_data = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            daily_orders = Order.objects.filter(created_at__date=date)
            daily_revenue = daily_orders.filter(
                status=Order.OrderStatus.COMPLETED
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            weekly_data.append({
                'date': date,
                'orders': daily_orders.count(),
                'revenue': daily_revenue
            })
        
        context['weekly_data'] = reversed(weekly_data)
        return context


class PopularMenuView(LoginRequiredMixin, TemplateView):
    """View for popular menu items"""
    template_name = 'dashboard/components/popular_menu.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get popular items based on orders and ratings
        popular_items = MenuItem.objects.filter(
            is_available=True
        ).order_by('-total_orders', '-rating')[:8]
        
        context['popular_items'] = popular_items
        return context


# AJAX API endpoints for dashboard widgets
@login_required
def order_stats_api(request):
    """API endpoint for order statistics"""
    today = timezone.now().date()
    
    if request.user.role == User.UserRole.USER:
        # User stats
        orders = Order.objects.filter(customer=request.user)
    else:
        # Staff stats
        orders = Order.objects.all()
    
    stats = {
        'total': orders.count(),
        'today': orders.filter(created_at__date=today).count(),
        'pending': orders.filter(status=Order.OrderStatus.PENDING).count(),
        'completed': orders.filter(status=Order.OrderStatus.COMPLETED).count(),
    }
    
    return JsonResponse(stats)


@login_required
def sales_chart_api(request):
    """API endpoint for sales chart data"""
    if request.user.role == User.UserRole.USER:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get daily sales for the past 7 days
    sales_data = []
    labels = []
    
    for i in range(7):
        date = timezone.now().date() - timedelta(days=6-i)
        daily_revenue = Order.objects.filter(
            created_at__date=date,
            status=Order.OrderStatus.COMPLETED
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        sales_data.append(float(daily_revenue))
        labels.append(date.strftime('%m/%d'))
    
    return JsonResponse({
        'labels': labels,
        'data': sales_data
    })


@login_required
def notifications_api(request):
    """API endpoint for notifications"""
    user = request.user
    notifications = []
    
    if user.role == User.UserRole.USER:
        # User notifications
        current_order = Order.objects.filter(
            customer=user,
            status__in=[Order.OrderStatus.PENDING, Order.OrderStatus.CONFIRMED, Order.OrderStatus.PREPARING, Order.OrderStatus.READY]
        ).first()
        
        if current_order:
            notifications.append({
                'type': 'order_update',
                'title': f'Order #{current_order.order_number}',
                'message': f'Status: {current_order.get_status_display()}',
                'time': current_order.updated_at.strftime('%H:%M'),
                'url': current_order.get_absolute_url()
            })
    
    else:
        # Staff notifications
        pending_orders = Order.objects.filter(status=Order.OrderStatus.PENDING).count()
        if pending_orders > 0:
            notifications.append({
                'type': 'pending_orders',
                'title': 'Pending Orders',
                'message': f'{pending_orders} orders need attention',
                'time': timezone.now().strftime('%H:%M'),
                'url': '/orders/pending/'
            })
        
        failed_payments = Payment.objects.filter(
            status=Payment.PaymentStatus.FAILED,
            created_at__date=timezone.now().date()
        ).count()
        if failed_payments > 0:
            notifications.append({
                'type': 'failed_payments',
                'title': 'Failed Payments',
                'message': f'{failed_payments} failed payments today',
                'time': timezone.now().strftime('%H:%M'),
                'url': '/payments/failed/'
            })
    
    return JsonResponse({'notifications': notifications})