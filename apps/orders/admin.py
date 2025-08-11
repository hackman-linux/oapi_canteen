# apps/orders/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Order, OrderItem, OrderStatusHistory, Cart, CartItem


class OrderItemInline(admin.TabularInline):
    """Inline admin for order items"""
    model = OrderItem
    extra = 0
    readonly_fields = ('get_total_price',)
    
    def get_total_price(self, obj):
        if obj.pk:
            return f"{obj.get_total_price():,.0f} XAF"
        return "0 XAF"
    get_total_price.short_description = 'Total'


class OrderStatusHistoryInline(admin.TabularInline):
    """Inline admin for order status history"""
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('timestamp',)
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin configuration for Order model"""
    
    list_display = (
        'order_number', 'customer_link', 'status_badge',
        'order_type', 'total_amount_formatted', 'is_paid',
        'created_at', 'estimated_pickup_time'
    )
    list_filter = (
        'status', 'order_type', 'is_paid', 'payment_method',
        'created_at', 'order_type'
    )
    search_fields = (
        'order_number', 'customer__username',
        'customer__first_name', 'customer__last_name'
    )
    readonly_fields = (
        'order_number', 'created_at', 'updated_at',
        'confirmed_at', 'completed_at', 'cancelled_at'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'status', 'order_type')
        }),
        ('Pricing', {
            'fields': (
                'subtotal', 'tax_amount', 'delivery_fee',
                'discount_amount', 'total_amount'
            )
        }),
        ('Payment', {
            'fields': ('is_paid', 'payment_method')
        }),
        ('Timing', {
            'fields': ('estimated_pickup_time', 'actual_pickup_time')
        }),
        ('Delivery Information', {
            'fields': ('delivery_address', 'delivery_phone', 'delivery_notes'),
            'classes': ('collapse',)
        }),
        ('Special Instructions', {
            'fields': ('special_instructions',)
        }),
        ('Staff Assignment', {
            'fields': ('assigned_to', 'validated_by')
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason', 'cancelled_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at', 'confirmed_at',
                'completed_at', 'cancelled_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    actions = ['mark_as_confirmed', 'mark_as_preparing', 'mark_as_ready']
    
    def customer_link(self, obj):
        """Link to customer admin page"""
        url = reverse('admin:accounts_user_change', args=[obj.customer.pk])
        return format_html('<a href="{}">{}</a>', url, obj.customer.get_full_name())
    customer_link.short_description = 'Customer'
    customer_link.admin_order_field = 'customer'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        return format_html(
            '<span class="badge {}">{}</span>',
            obj.get_status_badge_class(),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def total_amount_formatted(self, obj):
        """Display formatted total amount"""
        return f"{obj.total_amount:,.0f} XAF"
    total_amount_formatted.short_description = 'Total Amount'
    total_amount_formatted.admin_order_field = 'total_amount'
    
    def mark_as_confirmed(self, request, queryset):
        """Action to mark orders as confirmed"""
        for order in queryset:
            if order.status == Order.OrderStatus.PENDING:
                order.update_status(Order.OrderStatus.CONFIRMED, request.user)
        self.message_user(request, f"{queryset.count()} orders marked as confirmed.")
    mark_as_confirmed.short_description = "Mark selected orders as confirmed"
    
    def mark_as_preparing(self, request, queryset):
        """Action to mark orders as preparing"""
        for order in queryset:
            if order.status == Order.OrderStatus.CONFIRMED:
                order.update_status(Order.OrderStatus.PREPARING, request.user)
        self.message_user(request, f"{queryset.count()} orders marked as preparing.")
    mark_as_preparing.short_description = "Mark selected orders as preparing"
    
    def mark_as_ready(self, request, queryset):
        """Action to mark orders as ready"""
        for order in queryset:
            if order.status == Order.OrderStatus.PREPARING:
                order.update_status(Order.OrderStatus.READY, request.user)
        self.message_user(request, f"{queryset.count()} orders marked as ready.")
    mark_as_ready.short_description = "Mark selected orders as ready"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin configuration for OrderItem model"""
    
    list_display = (
        'order', 'menu_item', 'quantity', 'unit_price_formatted',
        'get_total_price_formatted', 'created_at'
    )
    list_filter = ('created_at', 'menu_item__category')
    search_fields = ('order__order_number', 'menu_item__name')
    readonly_fields = ('created_at',)
    
    def unit_price_formatted(self, obj):
        return f"{obj.unit_price:,.0f} XAF"
    unit_price_formatted.short_description = 'Unit Price'
    
    def get_total_price_formatted(self, obj):
        return obj.get_formatted_total()
    get_total_price_formatted.short_description = 'Total Price'


class CartItemInline(admin.TabularInline):
    """Inline admin for cart items"""
    model = CartItem
    extra = 0
    readonly_fields = ('get_total_price',)
    
    def get_total_price(self, obj):
        if obj.pk:
            return f"{obj.get_total_price():,.0f} XAF"
        return "0 XAF"
    get_total_price.short_description = 'Total'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin configuration for Cart model"""
    
    list_display = (
        'user', 'get_total_items', 'get_total_price_formatted',
        'created_at', 'updated_at'
    )
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    inlines = [CartItemInline]
    
    def get_total_price_formatted(self, obj):
        return f"{obj.get_total_price():,.0f} XAF"
    get_total_price_formatted.short_description = 'Total Price'