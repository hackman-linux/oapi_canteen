# apps/menu/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone

# Import models when they're created
# from .models import MenuItem, Category, MenuAvailability
# from .forms import MenuItemForm, CategoryForm, AvailabilityForm

# Placeholder models - replace with actual imports
class MenuItem:
    pass

class Category:
    pass

class MenuAvailability:
    pass


class MenuListView(ListView):
    """Public menu listing view"""
    # model = MenuItem
    template_name = 'menu/list.html'
    context_object_name = 'menu_items'
    paginate_by = 12
    
    def get_queryset(self):
        # return MenuItem.objects.filter(is_available=True, is_active=True).order_by('category', 'name')
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Our Menu',
            'categories': [],  # Category.objects.filter(is_active=True)
            'featured_items': [],  # MenuItem.objects.filter(is_featured=True, is_available=True)[:6]
        })
        return context


class CategoryMenuView(DetailView):
    """Menu items by category"""
    # model = Category
    template_name = 'menu/category.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        context.update({
            'title': f'{category.name} Menu',
            'menu_items': [],  # MenuItem.objects.filter(category=category, is_available=True, is_active=True)
        })
        return context


class MenuItemDetailView(DetailView):
    """Detailed view of a menu item"""
    # model = MenuItem
    template_name = 'menu/item_detail.html'
    context_object_name = 'item'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = self.get_object()
        context.update({
            'title': item.name,
            'related_items': [],  # MenuItem.objects.filter(category=item.category).exclude(id=item.id)[:4]
            'reviews': [],  # Item reviews when implemented
            'avg_rating': 0,  # Average rating
        })
        return context


class MenuSearchView(ListView):
    """Search menu items"""
    # model = MenuItem
    template_name = 'menu/search.html'
    context_object_name = 'menu_items'
    paginate_by = 12
    
    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if not query:
            return []
        
        # return MenuItem.objects.filter(
        #     Q(name__icontains=query) | 
        #     Q(description__icontains=query) |
        #     Q(category__name__icontains=query),
        #     is_available=True,
        #     is_active=True
        # ).order_by('name')
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        context.update({
            'title': f'Search Results for "{query}"',
            'query': query,
            'total_results': self.get_queryset().count(),
        })
        return context


# Admin Views
class AdminMenuListView(LoginRequiredMixin, ListView):
    """Admin menu management"""
    # model = MenuItem
    template_name = 'menu/admin/list.html'
    context_object_name = 'menu_items'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_menu():
            messages.error(request, "You don't have permission to manage menu items.")
            return redirect('menu:list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # return MenuItem.objects.all().order_by('category', 'name')
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Menu Management',
            'total_items': 0,  # MenuItem.objects.count()
            'active_items': 0,  # MenuItem.objects.filter(is_active=True).count()
            'available_items': 0,  # MenuItem.objects.filter(is_available=True).count()
        })
        return context


class MenuItemCreateView(LoginRequiredMixin, CreateView):
    """Create new menu item"""
    # model = MenuItem
    # form_class = MenuItemForm
    template_name = 'menu/admin/item_form.html'
    success_url = reverse_lazy('menu:admin_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_menu():
            messages.error(request, "You don't have permission to create menu items.")
            return redirect('menu:admin_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, f'Menu item "{form.cleaned_data["name"]}" created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Menu Item'
        context['form_action'] = 'Create'
        return context


class MenuItemEditView(LoginRequiredMixin, UpdateView):
    """Edit existing menu item"""
    # model = MenuItem
    # form_class = MenuItemForm
    template_name = 'menu/admin/item_form.html'
    success_url = reverse_lazy('menu:admin_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_menu():
            messages.error(request, "You don't have permission to edit menu items.")
            return redirect('menu:admin_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, f'Menu item "{form.cleaned_data["name"]}" updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Menu Item - {self.object.name}'
        context['form_action'] = 'Update'
        return context


class MenuItemDeleteView(LoginRequiredMixin, DeleteView):
    """Delete menu item"""
    # model = MenuItem
    template_name = 'menu/admin/item_confirm_delete.html'
    success_url = reverse_lazy('menu:admin_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_menu():
            messages.error(request, "You don't have permission to delete menu items.")
            return redirect('menu:admin_list')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        item = self.get_object()
        item_name = item.name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Menu item "{item_name}" has been deleted.')
        return response


# Category Management Views
class CategoryListView(LoginRequiredMixin, ListView):
    """List all categories"""
    # model = Category
    template_name = 'menu/admin/category_list.html'
    context_object_name = 'categories'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_menu():
            messages.error(request, "You don't have permission to manage categories.")
            return redirect('menu:list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Category Management'
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Create new category"""
    # model = Category
    # form_class = CategoryForm
    template_name = 'menu/admin/category_form.html'
    success_url = reverse_lazy('menu:category_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_menu():
            messages.error(request, "You don't have permission to create categories.")
            return redirect('menu:category_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.cleaned_data["name"]}" created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Category'
        context['form_action'] = 'Create'
        return context


class CategoryEditView(LoginRequiredMixin, UpdateView):
    """Edit category"""
    # model = Category
    # form_class = CategoryForm
    template_name = 'menu/admin/category_form.html'
    success_url = reverse_lazy('menu:category_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_menu():
            messages.error(request, "You don't have permission to edit categories.")
            return redirect('menu:category_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.cleaned_data["name"]}" updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Category - {self.object.name}'
        context['form_action'] = 'Update'
        return context


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete category"""
    # model = Category
    template_name = 'menu/admin/category_confirm_delete.html'
    success_url = reverse_lazy('menu:category_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_menu():
            messages.error(request, "You don't have permission to delete categories.")
            return redirect('menu:category_list')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        # Check if category has menu items
        # if MenuItem.objects.filter(category=category).exists():
        #     messages.error(self.request, f'Cannot delete category "{category.name}" - it contains menu items.')
        #     return redirect('menu:category_list')
        
        category_name = category.name
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, f'Category "{category_name}" has been deleted.')
        return response


# Menu Availability Views
class MenuAvailabilityView(LoginRequiredMixin, TemplateView):
    """Manage menu availability"""
    template_name = 'menu/admin/availability.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_menu():
            messages.error(request, "You don't have permission to manage menu availability.")
            return redirect('menu:list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Menu Availability',
            'menu_items': [],  # MenuItem.objects.all()
            'availability_schedules': [],  # MenuAvailability.objects.all()
        })
        return context


class AvailabilityCreateView(LoginRequiredMixin, CreateView):
    """Create availability schedule"""
    # model = MenuAvailability
    # form_class = AvailabilityForm
    template_name = 'menu/admin/availability_form.html'
    success_url = reverse_lazy('menu:availability')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_manage_menu():
            messages.error(request, "You don't have permission to create availability schedules.")
            return redirect('menu:availability')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Availability schedule created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Availability Schedule'
        return context


# API Views
@login_required
def menu_items_api(request):
    """API endpoint for menu items"""
    category_id = request.GET.get('category')
    search = request.GET.get('search', '').strip()
    
    # queryset = MenuItem.objects.filter(is_available=True, is_active=True)
    queryset = []
    
    # if category_id:
    #     queryset = queryset.filter(category_id=category_id)
    
    # if search:
    #     queryset = queryset.filter(
    #         Q(name__icontains=search) | Q(description__icontains=search)
    #     )
    
    items = []
    # items = [{
    #     'id': item.id,
    #     'name': item.name,
    #     'description': item.description,
    #     'price': float(item.price),
    #     'image_url': item.image.url if item.image else None,
    #     'category': item.category.name,
    #     'is_available': item.is_available,
    #     'preparation_time': item.preparation_time,
    # } for item in queryset]
    
    return JsonResponse({'items': items})


@login_required
def add_to_cart_api(request):
    """API endpoint to add item to cart"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    
    try:
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        if not item_id or quantity < 1:
            return JsonResponse({'success': False, 'message': 'Invalid parameters'})
        
        # item = get_object_or_404(MenuItem, id=item_id, is_available=True, is_active=True)
        
        # Add to session cart or database cart
        cart = request.session.get('cart', {})
        if item_id in cart:
            cart[item_id]['quantity'] += quantity
        else:
            cart[item_id] = {
                'quantity': quantity,
                # 'name': item.name,
                # 'price': float(item.price),
                # 'image_url': item.image.url if item.image else None,
            }
        
        request.session['cart'] = cart
        request.session.modified = True
        
        # Calculate cart totals
        cart_count = sum(item['quantity'] for item in cart.values())
        cart_total = 0  # sum(item['quantity'] * item['price'] for item in cart.values())
        
        return JsonResponse({
            'success': True,
            'message': 'Item added to cart successfully',
            'cart_count': cart_count,
            'cart_total': cart_total,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})