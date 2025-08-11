# apps/payments/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
import json

User = get_user_model()


class PaymentMethod(models.Model):
    """Payment method configuration"""
    
    PROVIDER_CHOICES = [
        ('ORANGE', 'Orange Money'),
        ('MTN', 'MTN Mobile Money'),
        ('CASH', 'Cash Payment'),
        ('CARD', 'Credit/Debit Card'),
    ]
    
    name = models.CharField(max_length=50, help_text="Payment method name")
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        help_text="Payment provider"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this payment method is currently active"
    )
    minimum_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('100.00'),
        validators=[MinValueValidator(0)],
        help_text="Minimum transaction amount in XAF"
    )
    maximum_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('500000.00'),
        validators=[MinValueValidator(0)],
        help_text="Maximum transaction amount in XAF"
    )
    transaction_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="Transaction fee percentage"
    )
    fixed_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="Fixed transaction fee in XAF"
    )
    api_configuration = models.JSONField(
        default=dict,
        help_text="API configuration parameters"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers first)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_methods'
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
    
    def calculate_fees(self, amount):
        """Calculate transaction fees"""
        percentage_fee = amount * (self.transaction_fee / 100)
        total_fee = percentage_fee + self.fixed_fee
        return {
            'percentage_fee': percentage_fee,
            'fixed_fee': self.fixed_fee,
            'total_fee': total_fee,
            'amount_with_fees': amount + total_fee
        }
    
    def is_amount_valid(self, amount):
        """Check if amount is within limits"""
        return self.minimum_amount <= amount <= self.maximum_amount


class Payment(models.Model):
    """Payment transaction records"""
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'
        EXPIRED = 'EXPIRED', 'Expired'
    
    # Unique identifiers
    payment_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Unique payment identifier"
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="External transaction ID from payment provider"
    )
    
    # Related objects
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Order this payment is for"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="User making the payment"
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        help_text="Payment method used"
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Payment amount in XAF"
    )
    fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="Transaction fees"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Total amount including fees"
    )
    currency = models.CharField(
        max_length=3,
        default='XAF',
        help_text="Currency code"
    )
    
    # Status and timing
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        help_text="Current payment status"
    )
    
    # Customer information
    customer_phone = models.CharField(
        max_length=15,
        help_text="Customer phone number for mobile money"
    )
    customer_email = models.EmailField(
        blank=True,
        help_text="Customer email for notifications"
    )
    
    # Provider specific data
    provider_data = models.JSONField(
        default=dict,
        help_text="Provider-specific transaction data"
    )
    provider_response = models.JSONField(
        default=dict,
        help_text="Raw response from payment provider"
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text="Payment description"
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Internal reference number"
    )
    failure_reason = models.TextField(
        blank=True,
        help_text="Reason for payment failure"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When payment was processed"
    )
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When payment request expires"
    )
    
    # Refund information
    refunded_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="Amount refunded"
    )
    refund_reason = models.TextField(
        blank=True,
        help_text="Reason for refund"
    )
    refunded_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When refund was processed"
    )
    refunded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_refunds',
        help_text="Staff member who processed the refund"
    )
    
    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.amount} XAF ({self.status})"
    
    def save(self, *args, **kwargs):
        """Calculate total amount including fees"""
        if not self.total_amount:
            fee_info = self.payment_method.calculate_fees(self.amount)
            self.fees = fee_info['total_fee']
            self.total_amount = fee_info['amount_with_fees']
        super().save(*args, **kwargs)
    
    def get_status_badge_class(self):
        """Return CSS class for status badge"""
        status_classes = {
            self.PaymentStatus.PENDING: 'badge-warning',
            self.PaymentStatus.PROCESSING: 'badge-info',
            self.PaymentStatus.COMPLETED: 'badge-success',
            self.PaymentStatus.FAILED: 'badge-danger',
            self.PaymentStatus.CANCELLED: 'badge-secondary',
            self.PaymentStatus.REFUNDED: 'badge-dark',
            self.PaymentStatus.EXPIRED: 'badge-light',
        }
        return status_classes.get(self.status, 'badge-secondary')
    
    def can_be_refunded(self):
        """Check if payment can be refunded"""
        return (self.status == self.PaymentStatus.COMPLETED and 
                self.refunded_amount < self.amount)
    
    def get_refundable_amount(self):
        """Get amount that can still be refunded"""
        return self.amount - self.refunded_amount
    
    def initiate_refund(self, amount, reason, processed_by):
        """Initiate a refund"""
        if not self.can_be_refunded():
            raise ValueError("Payment cannot be refunded")
        
        if amount > self.get_refundable_amount():
            raise ValueError("Refund amount exceeds refundable amount")
        
        self.refunded_amount += amount
        self.refund_reason = reason
        self.refunded_by = processed_by
        self.refunded_at = timezone.now()
        
        if self.refunded_amount >= self.amount:
            self.status = self.PaymentStatus.REFUNDED
        
        self.save()
        
        # Create refund record
        Refund.objects.create(
            payment=self,
            amount=amount,
            reason=reason,
            processed_by=processed_by
        )


class PaymentStatusHistory(models.Model):
    """Track payment status changes"""
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    previous_status = models.CharField(
        max_length=20,
        choices=Payment.PaymentStatus.choices,
        help_text="Previous status"
    )
    new_status = models.CharField(
        max_length=20,
        choices=Payment.PaymentStatus.choices,
        help_text="New status"
    )
    provider_response = models.JSONField(
        default=dict,
        help_text="Provider response at time of status change"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_status_history'
        verbose_name = 'Payment Status History'
        verbose_name_plural = 'Payment Status Histories'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Payment {self.payment.payment_id}: {self.previous_status} → {self.new_status}"


class Refund(models.Model):
    """Refund records"""
    
    class RefundStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
    
    refund_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.PENDING
    )
    reason = models.TextField(help_text="Reason for refund")
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processed_refunds_detail'
    )
    provider_refund_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Refund ID from payment provider"
    )
    provider_response = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'refunds'
        verbose_name = 'Refund'
        verbose_name_plural = 'Refunds'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund {self.refund_id} - {self.amount} XAF"


