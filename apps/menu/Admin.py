# apps/menu/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, MenuItem, MenuAvailability, MenuReview


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model"""
    
    list_display = (
        'name', 'display_order', 'color_preview',
        'get_active_items_count', 'is_active', 'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('display_order', 'name')
    list_editable = ('display_order', 'is_active')
    
    def color_preview(self, obj):
        """Display color as a colored box"""
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color
        )
    color_preview.short_description = 'Color'


class MenuAvailabilityInline(admin.TabularInline):
    """Inline admin for menu availability"""
    model = MenuAvailability
    extra = 0
    fields = ('date', 'meal_period', 'special_price', 'quantity_available', 'is_special_offer')


class MenuReviewInline(admin.TabularInline):
    """Inline admin for menu reviews"""
    model = MenuReview
    extra = 0
    readonly_fields = ('user', 'rating', 'comment', 'created_at')
    can_delete = True


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """Admin configuration for MenuItem model"""
    
    list_display = (
        'name', 'category', 'price', 'image_preview',
        'is_available', 'is_featured', 'rating', 'total_orders'
    )
    list_filter = (
        'category', 'is_available', 'is_featured',
        'is_vegetarian', 'is_vegan', 'is_spicy', 'created_at'
    )
    search_fields = ('name', 'description', 'ingredients')
    ordering = ('category', 'name')
    list_editable = ('is_available', 'is_featured', 'price')
    readonly_fields = ('rating', 'total_orders', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'price', 'image')
        }),
        ('Details', {
            'fields': (
                'preparation_time', 'calories', 'ingredients', 'allergens'
            )
        }),
        ('Dietary Information', {
            'fields': ('is_vegetarian', 'is_vegan', 'is_spicy', 'spice_level')
        }),
        ('Availability', {
            'fields': ('is_available', 'is_featured', 'daily_limit')
        }),
        ('Statistics', {
            'fields': ('rating', 'total_orders'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [MenuAvailabilityInline, MenuReviewInline]
    
    def image_preview(self, obj):
        """Display small image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Image'
    
    def save_model(self, request, obj, form, change):
        """Set created_by when creating new menu item"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MenuAvailability)
class MenuAvailabilityAdmin(admin.ModelAdmin):
    """Admin configuration for MenuAvailability model"""
    
    list_display = (
        'menu_item', 'date', 'meal_period',
        'get_effective_price', 'quantity_available', 'is_special_offer'
    )
    list_filter = ('date', 'meal_period', 'is_special_offer')
    search_fields = ('menu_item__name',)
    ordering = ('-date', 'meal_period')
    date_hierarchy = 'date'
    
    def get_effective_price(self, obj):
        """Display effective price"""
        price = obj.get_effective_price()
        return f"{price:,.0f} XAF"
    get_effective_price.short_description = 'Effective Price'


@admin.register(MenuReview)
class MenuReviewAdmin(admin.ModelAdmin):
    """Admin configuration for MenuReview model"""
    
    list_display = (
        'menu_item', 'user', 'rating_stars', 'is_approved', 'created_at'
    )
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('menu_item__name', 'user__username', 'comment')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    def rating_stars(self, obj):
        """Display rating as stars"""
        return obj.get_stars_display()
    rating_stars.short_description = 'Rating'