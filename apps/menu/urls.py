# apps/menu/urls.py
from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    # Public menu views
    path('', views.MenuListView.as_view(), name='list'),
    path('category/<int:pk>/', views.CategoryMenuView.as_view(), name='category'),
    path('item/<int:pk>/', views.MenuItemDetailView.as_view(), name='item_detail'),
    path('search/', views.MenuSearchView.as_view(), name='search'),
    
    # Admin menu management
    path('admin/', views.AdminMenuListView.as_view(), name='admin_list'),
    path('admin/items/create/', views.MenuItemCreateView.as_view(), name='item_create'),
    path('admin/items/<int:pk>/edit/', views.MenuItemEditView.as_view(), name='item_edit'),
    path('admin/items/<int:pk>/delete/', views.MenuItemDeleteView.as_view(), name='item_delete'),
    
    # Category management
    path('admin/categories/', views.CategoryListView.as_view(), name='category_list'),
    path('admin/categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('admin/categories/<int:pk>/edit/', views.CategoryEditView.as_view(), name='category_edit'),
    path('admin/categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # Menu availability
    path('admin/availability/', views.MenuAvailabilityView.as_view(), name='availability'),
    path('admin/availability/create/', views.AvailabilityCreateView.as_view(), name='availability_create'),
    
    # API endpoints
    path('api/items/', views.menu_items_api, name='items_api'),
    path('api/add-to-cart/', views.add_to_cart_api, name='add_to_cart_api'),
]