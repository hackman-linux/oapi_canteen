# apps/orders/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, TemplateView, CreateView
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import uuid

# Import models when they're created
# from .models import Order, OrderItem, Cart, CartItem
# from .forms import CheckoutForm
# from apps.menu.models import MenuItem
# from apps.payments.models import Payment

# Placeholder models - replace with actual imports
class Order:
    pass

class OrderItem:
    pass

class Cart:
    pass

class CartItem:
    pass


class MyOrdersView(LoginRequiredMixin, ListView):
    """User's order history"""
    # model = Order
    template_name = 'orders/my_orders.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        # return Order.objects.filter(user=self.request.user).order_by('-created_at')
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update({
            'title': 'My Orders',
            'total_orders': 0,  # Order.objects.filter(user=user).count()
            'pending_orders': 0,  # Order.objects.filter(user=user, status='PENDING').count()
            'completed_orders': 0,  # Order.objects.filter(user=user, status='COMPLETED').count()
            'total_spent': 0,  # Order.objects.filter(user=user, status='COMPLETED').aggregate(total=Sum('total_amount'))['total'] or 0
        })
        return context


class CartView(LoginRequiredMixin, TemplateView):
    """Shopping cart view"""
    template_name = 'orders/cart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get cart items from session or database
        cart_items = []
        cart_total = 0
        
        # If using session cart
        session_cart = self.request.session.get('cart', {})
        # for item_id, cart_data in session_cart.items():
        #     try:
        #         menu_item = MenuItem.objects.get(id=item_id, is_available=True)
        #         subtotal = cart_data['quantity'] * menu_item.price
        #         cart_items.append({
        #             'menu_item': menu_item,
        #             'quantity': cart_data['quantity'],
        #             'subtotal': subtotal,
        #         })
        #         cart_total += subtotal
        #     except MenuItem.DoesNotExist:
        #         continue
        
        context.update({
            'title': 'Shopping Cart',
            'cart_items': cart_items,
            'cart_total': cart_total,
            'cart_count': len(cart_items),
            'delivery_fee': 0,  # Calculate delivery fee
            'tax': 0,  # Calculate tax
            'grand_total': cart_total,  # cart_total + delivery_fee + tax
        })
        return context


class CheckoutView(LoginRequiredMixin, TemplateView):
    """Checkout process view"""
    template_name = 'orders/checkout.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if cart is not empty
        cart = request.session.get('cart', {})
        if not cart:
            messages.warning(request, 'Your cart is empty.')
            return redirect('orders:cart')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Calculate order summary
        cart = self.request.session.get('cart', {})
        cart_items = []
        cart_total = 0
        
        # Process cart items (similar to CartView)
        
        context.update({
            'title': 'Checkout',
            'cart_items': cart_items,
            'cart_total': cart_total,
            'delivery_fee': 0,
            'tax': 0,
            'grand_total': cart_total,
            'user_profile': user.profile if hasattr(user, 'profile') else None,
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Process checkout form submission"""
        try:
            cart = request.session.get('cart', {})
            if not cart:
                return JsonResponse({'success': False, 'message': 'Cart is empty'})
            
            # Create order
            order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
            
            # order = Order.objects.create(
            #     user=request.user,
            #     order_number=order_number,
            #     status='PENDING',
            #     total_amount=cart_total,
            #     delivery_address=request.POST.get('delivery_address'),
            #     phone_number=request.POST.get('phone_number'),
            #     special_instructions=request.POST.get('special_instructions'),
            # )
            
            # Create order items
            # for item_id, cart_data in cart.items():
            #     menu_item = MenuItem.objects.get(id=item_id)
            #     OrderItem.objects.create(
            #         order=order,
            #         menu_item=menu_item,
            #         quantity=cart_data['quantity'],
            #         unit_price=menu_item.price,
            #         subtotal=cart_data['quantity'] * menu_item.price,
            #     )
            
            # Clear cart
            request.session['cart'] = {}
            request.session.modified = True
            
            messages.success(request, f'Order {order_number} placed successfully!')
            
            return JsonResponse({
                'success': True,
                'message': 'Order placed successfully',
                'order_number': order_number,
                'redirect_url': reverse('orders:detail', kwargs={'order_number': order_number})
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Order detail view"""
    # model = Order
    template_name = 'orders/detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'
    
    def get_object(self):
        order_number = self.kwargs.get('order_number')
        # order = get_object_or_404(Order, order_number=order_number)
        
        # Check permissions
        # if order.user != self.request.user and not self.request.user.can_manage_orders():
        #     raise PermissionDenied("You don't have permission to view this order.")
        
        # return order
        return None  # Placeholder
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context.update({
            'title': f'Order #{order.order_number}' if order else 'Order Details',
            # 'order_items': OrderItem.objects.filter(order=order)
            'order_items': [],
            'payment': None,  # Payment.objects.filter(order=order).first()
        })
        return context


# Staff Views
class OrderListView(LoginRequiredMixin, ListView):
    """All orders list for staff"""
    # model = Order
    template_name = 'orders/staff/list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_orders():
            messages.error(request, "You don't have permission to manage orders.")
            return redirect('orders:my_orders')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # queryset = Order.objects.all().order_by('-created_at')
        queryset = []
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            # queryset = queryset.filter(status=status)
            pass
        
        # Filter by date
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        # if date_from:
        #     queryset = queryset.filter(created_at__date__gte=date_from)
        # if date_to:
        #     queryset = queryset.filter(created_at__date__lte=date_to)
        
        # Search by order number or customer
        search = self.request.GET.get('search')
        if search:
            # queryset = queryset.filter(
            #     Q(order_number__icontains=search) |
            #     Q(user__first_name__icontains=search) |
            #     Q(user__last_name__icontains=search)
            # )
            pass
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Order Management',
            'status_filter': self.request.GET.get('status', ''),
            'search_query': self.request.GET.get('search', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'order_statuses': [
                ('PENDING', 'Pending'),
                ('CONFIRMED', 'Confirmed'),
                ('PREPARING', 'Preparing'),
                ('READY', 'Ready'),
                ('COMPLETED', 'Completed'),
                ('CANCELLED', 'Cancelled'),
            ],
        })
        return context


class PendingOrdersView(LoginRequiredMixin, ListView):
    """Pending orders for quick management"""
    # model = Order
    template_name = 'orders/staff/pending.html'
    context_object_name = 'orders'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_orders():
            messages.error(request, "You don't have permission to manage orders.")
            return redirect('orders:my_orders')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # return Order.objects.filter(status='PENDING').order_by('created_at')
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Pending Orders',
            'pending_count': self.get_queryset().count(),
        })
        return context


class ManageOrderView(LoginRequiredMixin, DetailView):
    """Detailed order management view"""
    # model = Order
    template_name = 'orders/staff/manage.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_orders():
            messages.error(request, "You don't have permission to manage orders.")
            return redirect('orders:my_orders')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context.update({
            'title': f'Manage Order #{order.order_number}' if order else 'Manage Order',
            # 'order_items': OrderItem.objects.filter(order=order)
            'order_items': [],
            'status_choices': [
                ('PENDING', 'Pending'),
                ('CONFIRMED', 'Confirmed'),
                ('PREPARING', 'Preparing'),
                ('READY', 'Ready'),
                ('COMPLETED', 'Completed'),
                ('CANCELLED', 'Cancelled'),
            ],
        })
        return context


# Action Views
@login_required
def update_order_status(request):
    """Update order status via AJAX"""
    if request.method != 'POST' or not request.user.can_manage_orders():
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    
    try:
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        
        # order = get_object_or_404(Order, id=order_id)
        # order.status = new_status
        # order.save()
        
        # Create notification for customer
        # if new_status in ['CONFIRMED', 'PREPARING', 'READY', 'COMPLETED']:
        #     Notification.objects.create(
        #         user=order.user,
        #         title=f'Order #{order.order_number} Update',
        #         message=f'Your order status has been updated to {order.get_status_display()}',
        #         type='ORDER_UPDATE',
        #     )
        
        return JsonResponse({
            'success': True,
            'message': f'Order status updated to {new_status}',
            'new_status': new_status,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def cancel_order(request, order_number):
    """Cancel an order"""
    # order = get_object_or_404(Order, order_number=order_number)
    
    # Check permissions
    # if order.user != request.user and not request.user.can_manage_orders():
    #     messages.error(request, "You don't have permission to cancel this order.")
    #     return redirect('orders:my_orders')
    
    # if order.status not in ['PENDING', 'CONFIRMED']:
    #     messages.error(request, f'Cannot cancel order #{order_number} - it is already {order.get_status_display()}.')
    # else:
    #     order.status = 'CANCELLED'
    #     order.save()
    #     messages.success(request, f'Order #{order_number} has been cancelled.')
    
    # Redirect based on user role
    if request.user.can_manage_orders():
        return redirect('orders:list')
    else:
        return redirect('orders:my_orders')


# Cart API Views
@login_required
def add_to_cart_api(request):
    """Add item to cart via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    
    try:
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        if not item_id or quantity < 1:
            return JsonResponse({'success': False, 'message': 'Invalid parameters'})
        
        # Add to session cart
        cart = request.session.get('cart', {})
        if item_id in cart:
            cart[item_id]['quantity'] += quantity
        else:
            cart[item_id] = {'quantity': quantity}
        
        request.session['cart'] = cart
        request.session.modified = True
        
        cart_count = sum(item['quantity'] for item in cart.values())
        
        return JsonResponse({
            'success': True,
            'message': 'Item added to cart',
            'cart_count': cart_count,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def update_cart_api(request):
    """Update cart item quantity"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    
    try:
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 0))
        
        cart = request.session.get('cart', {})
        
        if quantity <= 0:
            cart.pop(item_id, None)
        else:
            if item_id in cart:
                cart[item_id]['quantity'] = quantity
        
        request.session['cart'] = cart
        request.session.modified = True
        
        cart_count = sum(item['quantity'] for item in cart.values())
        
        return JsonResponse({
            'success': True,
            'message': 'Cart updated',
            'cart_count': cart_count,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def remove_from_cart_api(request):
    """Remove item from cart"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    
    try:
        item_id = request.POST.get('item_id')
        
        cart = request.session.get('cart', {})
        cart.pop(item_id, None)
        
        request.session['cart'] = cart
        request.session.modified = True
        
        cart_count = sum(item['quantity'] for item in cart.values())
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart',
            'cart_count': cart_count,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def clear_cart_api(request):
    """Clear entire cart"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    
    try:
        request.session['cart'] = {}
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': 'Cart cleared',
            'cart_count': 0,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})