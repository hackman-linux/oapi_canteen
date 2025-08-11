# apps/menu/models.py
from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from PIL import Image
import os

User = get_user_model()


class Category(models.Model):
    """Food categories for menu organization"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Category name (e.g., Main Dishes, Beverages)"
    )
    description = models.TextField(
        blank=True,
        help_text="Category description"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Bootstrap or Font Awesome icon class"
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        help_text="Hex color code for category display"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order for displaying categories (lower numbers first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this category is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'menu_categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('menu:category_detail', kwargs={'pk': self.pk})
    
    def get_active_items_count(self):
        """Return count of active menu items in this category"""
        return self.menu_items.filter(is_available=True).count()


class MenuItem(models.Model):
    """Individual menu items"""
    
    name = models.CharField(
        max_length=200,
        help_text="Menu item name"
    )
    description = models.TextField(
        help_text="Detailed description of the menu item"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='menu_items',
        help_text="Category this item belongs to"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price in XAF (Central African Francs)"
    )
    image = models.ImageField(
        upload_to='menu_items/',
        blank=True,
        null=True,
        help_text="Image of the menu item"
    )
    preparation_time = models.PositiveIntegerField(
        default=15,
        help_text="Estimated preparation time in minutes"
    )
    calories = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Estimated calories per serving"
    )
    ingredients = models.TextField(
        blank=True,
        help_text="Main ingredients (comma-separated)"
    )
    allergens = models.TextField(
        blank=True,
        help_text="Known allergens (comma-separated)"
    )
    is_vegetarian = models.BooleanField(
        default=False,
        help_text="Whether this item is vegetarian"
    )
    is_vegan = models.BooleanField(
        default=False,
        help_text="Whether this item is vegan"
    )
    is_spicy = models.BooleanField(
        default=False,
        help_text="Whether this item is spicy"
    )
    spice_level = models.PositiveIntegerField(
        choices=[(1, 'Mild'), (2, 'Medium'), (3, 'Hot'), (4, 'Very Hot')],
        default=1,
        help_text="Spice level (1-4)"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Whether this item is currently available"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether to feature this item"
    )
    daily_limit = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Daily serving limit (null for unlimited)"
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Average customer rating (0-5)"
    )
    total_orders = models.PositiveIntegerField(
        default=0,
        help_text="Total number of times this item has been ordered"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_menu_items',
        help_text="User who created this menu item"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'menu_items'
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Items'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['is_featured', 'is_available']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.price} XAF"
    
    def get_absolute_url(self):
        return reverse('menu:item_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        """Override save to resize image"""
        super().save(*args, **kwargs)
        
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 400 or img.width > 400:
                output_size = (400, 400)
                img.thumbnail(output_size)
                img.save(self.image.path)
    
    def get_display_price(self):
        """Return formatted price string"""
        return f"{self.price:,.0f} XAF"
    
    def get_spice_level_display_stars(self):
        """Return spice level as star symbols"""
        return "🌶️" * self.spice_level if self.is_spicy else ""
    
    def get_dietary_info(self):
        """Return dietary information as list"""
        info = []
        if self.is_vegetarian:
            info.append("Vegetarian")
        if self.is_vegan:
            info.append("Vegan")
        if self.is_spicy:
            info.append(f"Spicy ({self.get_spice_level_display()})")
        return info
    
    def can_be_ordered_today(self):
        """Check if item can be ordered today based on daily limit"""
        if not self.daily_limit:
            return True
        
        from django.utils import timezone
        from apps.orders.models import OrderItem
        
        today = timezone.now().date()
        today_orders = OrderItem.objects.filter(
            menu_item=self,
            order__created_at__date=today,
            order__status__in=['PENDING', 'CONFIRMED', 'PREPARING', 'READY']
        ).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        
        return today_orders < self.daily_limit
    
    def get_remaining_today(self):
        """Get remaining quantity for today"""
        if not self.daily_limit:
            return None
        
        from django.utils import timezone
        from apps.orders.models import OrderItem
        
        today = timezone.now().date()
        today_orders = OrderItem.objects.filter(
            menu_item=self,
            order__created_at__date=today,
            order__status__in=['PENDING', 'CONFIRMED', 'PREPARING', 'READY']
        ).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        
        return max(0, self.daily_limit - today_orders)


class MenuAvailability(models.Model):
    """Daily menu availability and special offers"""
    
    AVAILABILITY_CHOICES = [
        ('BREAKFAST', 'Breakfast (6:00 - 10:00)'),
        ('LUNCH', 'Lunch (11:00 - 15:00)'),
        ('DINNER', 'Dinner (17:00 - 21:00)'),
        ('ALL_DAY', 'All Day'),
    ]
    
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='availability_schedule'
    )
    date = models.DateField(
        help_text="Date for this availability"
    )
    meal_period = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default='ALL_DAY',
        help_text="When this item is available"
    )
    special_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Special price for this day (optional)"
    )
    quantity_available = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Specific quantity available (overrides daily limit)"
    )
    is_special_offer = models.BooleanField(
        default=False,
        help_text="Mark as special offer"
    )
    notes = models.TextField(
        blank=True,
        help_text="Special notes for this availability"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'menu_availability'
        verbose_name = 'Menu Availability'
        verbose_name_plural = 'Menu Availability'
        unique_together = ['menu_item', 'date', 'meal_period']
        ordering = ['date', 'meal_period']
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.date} ({self.get_meal_period_display()})"
    
    def get_effective_price(self):
        """Return special price if available, otherwise regular price"""
        return self.special_price or self.menu_item.price
    
    def get_effective_quantity(self):
        """Return specific quantity if set, otherwise daily limit"""
        return self.quantity_available or self.menu_item.daily_limit


class MenuReview(models.Model):
    """Customer reviews for menu items"""
    
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='menu_reviews'
    )
    rating = models.PositiveIntegerField(
        choices=[(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(
        blank=True,
        help_text="Optional review comment"
    )
    is_approved = models.BooleanField(
        default=True,
        help_text="Whether this review is approved for display"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'menu_reviews'
        verbose_name = 'Menu Review'
        verbose_name_plural = 'Menu Reviews'
        unique_together = ['menu_item', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.menu_item.name} ({self.rating}★)"
    
    def get_stars_display(self):
        """Return rating as star symbols"""
        return "★" * self.rating + "☆" * (5 - self.rating)