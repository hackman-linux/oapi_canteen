# apps/orders/models.py
from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class Order(models.Model):
    """Main order model"""
    
    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        PREPARING = 'PREPARING', 'Preparing'
        READY = 'READY', 'Ready for Pickup'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'
    
    class OrderType(models.TextChoices):
        PICKUP = 'PICKUP', 'Pickup'
        DELIVERY = 'DELIVERY', 'Delivery'
    
    # Unique identifier
    order_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique order number"
    )
    
    # Customer information
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        help_text="Customer who placed the order"
    )
    
    # Order details
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        help_text="Current order status"
    )
    order_type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.PICKUP,
        help_text="Order type"
    )
    
    # Pricing
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="Subtotal before taxes and fees"
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="Tax amount"
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="Delivery fee if applicable"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="Discount amount applied"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        help_text="Final total amount"
    )
    
    # Timing
    estimated_pickup_time = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Estimated time for pickup"
    )
    actual_pickup_time = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Actual pickup time"
    )
    
    # Delivery information (if applicable)
    delivery_address = models.TextField(
        blank=True,
        help_text="Delivery address"
    )
    delivery_phone = models.CharField(
        max_length=15,
        blank=True,
        help_text="Delivery contact phone"
    )
    delivery_notes = models.TextField(
        blank=True,
        help_text="Special delivery instructions"
    )
    
    # Special requests
    special_instructions = models.TextField(
        blank=True,
        help_text="Special cooking or preparation instructions"
    )
    
    # Payment
    is_paid = models.BooleanField(
        default=False,
        help_text="Whether the order has been paid"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('ORANGE', 'Orange Money'),
            ('MTN', 'MTN Mobile Money'),
            ('CASH', 'Cash'),
            ('CARD', 'Credit/Debit Card'),
        ],
        blank=True,
        help_text="Payment method used"
    )
    
    # Staff assignments
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders',
        help_text="Staff member assigned to handle this order"
    )
    validated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_orders',
        help_text="Manager who validated this order"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    
    # Cancellation
    cancellation_reason = models.TextField(
        blank=True,
        help_text="Reason for cancellation"
    )
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_orders',
        help_text="User who cancelled this order"
    )
    
    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['order_number']),
        ]
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.customer.get_full_name()}"
    
    def save(self, *args, **kwargs):
        """Generate order number if not provided"""
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('orders:detail', kwargs={'order_number': self.order_number})
    
    @staticmethod
    def generate_order_number():
        """Generate unique order number"""
        import random
        import string
        from django.utils import timezone
        
        # Format: YYYYMMDD-XXXX (e.g., 20250806-A1B2)
        date_part = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        order_number = f"{date_part}-{random_part}"
        
        # Ensure uniqueness
        while Order.objects.filter(order_number=order_number).exists():
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            order_number = f"{date_part}-{random_part}"
        
        return order_number
    
    def calculate_totals(self):
        """Calculate order totals based on items"""
        items_subtotal = sum(item.get_total_price() for item in self.items.all())
        self.subtotal = items_subtotal
        
        # Calculate tax (e.g., 5% VAT)
        tax_rate = Decimal('0.05')
        self.tax_amount = self.subtotal * tax_rate
        
        # Calculate total
        self.total_amount = self.subtotal + self.tax_amount + self.delivery_fee - self.discount_amount
        
        return {
            'subtotal': self.subtotal,
            'tax_amount': self.tax_amount,
            'delivery_fee': self.delivery_fee,
            'discount_amount': self.discount_amount,
            'total_amount': self.total_amount,
        }
    
    def get_status_badge_class(self):
        """Return CSS class for status badge"""
        status_classes = {
            self.OrderStatus.PENDING: 'badge-warning',
            self.OrderStatus.CONFIRMED: 'badge-info',
            self.OrderStatus.PREPARING: 'badge-primary',
            self.OrderStatus.READY: 'badge-success',
            self.OrderStatus.COMPLETED: 'badge-success',
            self.OrderStatus.CANCELLED: 'badge-danger',
            self.OrderStatus.REFUNDED: 'badge-secondary',
        }
        return status_classes.get(self.status, 'badge-secondary')
    
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in [self.OrderStatus.PENDING, self.OrderStatus.CONFIRMED]
    
    def can_be_modified(self):
        """Check if order can be modified"""
        return self.status == self.OrderStatus.PENDING
    
    def get_estimated_completion_time(self):
        """Calculate estimated completion time based on items"""
        if not self.estimated_pickup_time:
            max_prep_time = max(
                (item.menu_item.preparation_time for item in self.items.all()),
                default=15
            )
            return self.created_at + timezone.timedelta(minutes=max_prep_time)
        return self.estimated_pickup_time
    
    def update_status(self, new_status, user=None):
        """Update order status with timestamp tracking"""
        old_status = self.status
        self.status = new_status
        
        # Set appropriate timestamps
        if new_status == self.OrderStatus.CONFIRMED and not self.confirmed_at:
            self.confirmed_at = timezone.now()
            if user:
                self.validated_by = user
        elif new_status == self.OrderStatus.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
            self.actual_pickup_time = timezone.now()
        elif new_status == self.OrderStatus.CANCELLED and not self.cancelled_at:
            self.cancelled_at = timezone.now()
            if user:
                self.cancelled_by = user
        
        self.save()
        
        # Create status history entry
        OrderStatusHistory.objects.create(
            order=self,
            previous_status=old_status,
            new_status=new_status,
            changed_by=user,
            notes=f"Status changed from {old_status} to {new_status}"
        )
    
    def get_total_items_count(self):
        """Get total number of items in order"""
        return sum(item.quantity for item in self.items.all())
    
    def get_items_summary(self):
        """Get a summary string of items in the order"""
        items = self.items.select_related('menu_item')[:3]
        summary = ", ".join(f"{item.menu_item.name} x{item.quantity}" for item in items)
        if self.items.count() > 3:
            summary += f" and {self.items.count() - 3} more items"
        return summary


class OrderItem(models.Model):
    """Individual items within an order"""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Order this item belongs to"
    )
    menu_item = models.ForeignKey(
        'menu.MenuItem',
        on_delete=models.CASCADE,
        related_name='order_items',
        help_text="Menu item being ordered"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Quantity ordered"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price per unit at time of order"
    )
    special_instructions = models.TextField(
        blank=True,
        help_text="Special instructions for this item"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_items'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        unique_together = ['order', 'menu_item']
    
    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity} - Order #{self.order.order_number}"
    
    def save(self, *args, **kwargs):
        """Set unit price from menu item if not provided"""
        if not self.unit_price:
            self.unit_price = self.menu_item.price
        super().save(*args, **kwargs)
    
    def get_total_price(self):
        """Calculate total price for this item"""
        return self.unit_price * self.quantity
    
    def get_formatted_total(self):
        """Return formatted total price"""
        return f"{self.get_total_price():,.0f} XAF"


class OrderStatusHistory(models.Model):
    """Track order status changes"""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    previous_status = models.CharField(
        max_length=20,
        choices=Order.OrderStatus.choices,
        help_text="Previous status"
    )
    new_status = models.CharField(
        max_length=20,
        choices=Order.OrderStatus.choices,
        help_text="New status"
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who changed the status"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the status change"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_status_history'
        verbose_name = 'Order Status History'
        verbose_name_plural = 'Order Status Histories'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Order #{self.order.order_number}: {self.previous_status} → {self.new_status}"


class Cart(models.Model):
    """Shopping cart for users"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carts'
        verbose_name = 'Shopping Cart'
        verbose_name_plural = 'Shopping Carts'
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Cart"
    
    def get_total_price(self):
        """Calculate total price of items in cart"""
        return sum(item.get_total_price() for item in self.items.all())
    
    def get_total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    def clear(self):
        """Remove all items from cart"""
        self.items.all().delete()
    
    def add_item(self, menu_item, quantity=1, special_instructions=''):
        """Add item to cart or update quantity if exists"""
        cart_item, created = self.items.get_or_create(
            menu_item=menu_item,
            defaults={
                'quantity': quantity,
                'unit_price': menu_item.price,
                'special_instructions': special_instructions
            }
        )
        
        if not created:
            cart_item.quantity += quantity
            if special_instructions:
                cart_item.special_instructions = special_instructions
            cart_item.save()
        
        return cart_item
    
    def remove_item(self, menu_item):
        """Remove item from cart"""
        self.items.filter(menu_item=menu_item).delete()
    
    def update_item_quantity(self, menu_item, quantity):
        """Update item quantity"""
        if quantity <= 0:
            self.remove_item(menu_item)
        else:
            cart_item = self.items.get(menu_item=menu_item)
            cart_item.quantity = quantity
            cart_item.save()


class CartItem(models.Model):
    """Items in shopping cart"""
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        'menu.MenuItem',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    special_instructions = models.TextField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cart_items'
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ['cart', 'menu_item']
    
    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        """Set unit price from menu item if not provided"""
        if not self.unit_price:
            self.unit_price = self.menu_item.price
        super().save(*args, **kwargs)
    
    def get_total_price(self):
        """Calculate total price for this cart item"""
        return self.unit_price * self.quantity


