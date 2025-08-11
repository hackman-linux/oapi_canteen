# apps/payments/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import PaymentMethod, Payment, PaymentStatusHistory, Refund


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentMethod model"""
    
    list_display = (
        'name', 'provider', 'is_active', 'minimum_amount_formatted',
        'maximum_amount_formatted', 'transaction_fee', 'display_order'
    )
    list_filter = ('provider', 'is_active')
    list_editable = ('is_active', 'display_order')
    ordering = ('display_order', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'provider', 'is_active', 'display_order')
        }),
        ('Limits', {
            'fields': ('minimum_amount', 'maximum_amount')
        }),
        ('Fees', {
            'fields': ('transaction_fee', 'fixed_fee')
        }),
        ('Configuration', {
            'fields': ('api_configuration',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def minimum_amount_formatted(self, obj):
        return f"{obj.minimum_amount:,.0f} XAF"
    minimum_amount_formatted.short_description = 'Min Amount'
    
    def maximum_amount_formatted(self, obj):
        return f"{obj.maximum_amount:,.0f} XAF"
    maximum_amount_formatted.short_description = 'Max Amount'


class PaymentStatusHistoryInline(admin.TabularInline):
    """Inline admin for payment status history"""
    model = PaymentStatusHistory
    extra = 0
    readonly_fields = ('timestamp',)
    can_delete = False
    ordering = ('-timestamp',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for Payment model"""
    
    list_display = (
        'payment_id', 'order', 'user', 'payment_method',
        'amount_formatted', 'status_badge', 'created_at'
    )
    list_filter = (
        'status', 'payment_method__provider', 'created_at', 'processed_at'
    )
    search_fields = (
        'payment_id', 'transaction_id', 'order__order_number',
        'user__username', 'customer_phone'
    )
    readonly_fields = (
        'payment_id', 'created_at', 'updated_at', 'processed_at'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_id', 'transaction_id', 'order', 'user', 'payment_method')
        }),
        ('Amount Details', {
            'fields': ('amount', 'fees', 'total_amount', 'currency')
        }),
        ('Status', {
            'fields': ('status', 'failure_reason')
        }),
        ('Customer Information', {
            'fields': ('customer_phone', 'customer_email')
        }),
        ('Provider Data', {
            'fields': ('provider_data', 'provider_response'),
            'classes': ('collapse',)
        }),
        ('Refund Information', {
            'fields': ('refunded_amount', 'refund_reason', 'refunded_at', 'refunded_by'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('description', 'reference')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [PaymentStatusHistoryInline]
    
    actions = ['check_payment_status', 'mark_as_completed']
    
    def amount_formatted(self, obj):
        return f"{obj.amount:,.0f} XAF"
    amount_formatted.short_description = 'Amount'
    amount_formatted.admin_order_field = 'amount'
    
    def status_badge(self, obj):
        return format_html(
            '<span class="badge {}">{}</span>',
            obj.get_status_badge_class(),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def check_payment_status(self, request, queryset):
        """Action to check payment status with providers"""
        from .services import get_payment_service
        
        updated_count = 0
        for payment in queryset:
            try:
                service = get_payment_service(payment.payment_method.provider)
                result = service.check_payment_status(payment)
                if result['success']:
                    updated_count += 1
            except Exception as e:
                logger.error(f"Status check failed for payment {payment.payment_id}: {e}")
        
        self.message_user(request, f"{updated_count} payments updated.")
    check_payment_status.short_description = "Check payment status with providers"
    
    def mark_as_completed(self, request, queryset):
        """Action to manually mark payments as completed"""
        updated_count = queryset.filter(
            status__in=[Payment.PaymentStatus.PROCESSING, Payment.PaymentStatus.PENDING]
        ).update(
            status=Payment.PaymentStatus.COMPLETED,
            processed_at=timezone.now()
        )
        self.message_user(request, f"{updated_count} payments marked as completed.")
    mark_as_completed.short_description = "Mark selected payments as completed"


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    """Admin configuration for Refund model"""
    
    list_display = (
        'refund_id', 'payment', 'amount_formatted',
        'status', 'processed_by', 'created_at'
    )
    list_filter = ('status', 'created_at', 'processed_at')
    search_fields = ('refund_id', 'payment__payment_id', 'reason')
    readonly_fields = ('refund_id', 'created_at', 'processed_at')
    ordering = ('-created_at',)
    
    def amount_formatted(self, obj):
        return f"{obj.amount:,.0f} XAF"
    amount_formatted.short_description = 'Amount'