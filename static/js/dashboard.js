// static/js/dashboard.js

/**
 * OAPI Canteen Dashboard JavaScript
 * Handles dashboard interactions, AJAX calls, and real-time updates
 */

class Dashboard {
    constructor() {
        this.init();
        this.startRealTimeUpdates();
        this.setupEventListeners();
    }

    init() {
        console.log('Dashboard initialized');
        this.loadInitialData();
    }

    /**
     * Load initial dashboard data
     */
    loadInitialData() {
        this.updateCartBadge();
        this.loadNotifications();
        this.updateOrderStats();
    }

    /**
     * Setup event listeners for interactive elements
     */
    setupEventListeners() {
        // Cart management
        this.setupCartListeners();
        
        // Order management
        this.setupOrderListeners();
        
        // Search functionality
        this.setupSearchListeners();
        
        // Form enhancements
        this.setupFormEnhancements();
    }

    /**
     * Setup cart-related event listeners
     */
    setupCartListeners() {
        // Add to cart buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.add-to-cart-btn')) {
                e.preventDefault();
                const menuItemId = e.target.dataset.menuItemId;
                const quantity = e.target.dataset.quantity || 1;
                this.addToCart(menuItemId, quantity);
            }
        });

        // Cart quantity controls
        document.addEventListener('click', (e) => {
            if (e.target.matches('.cart-qty-increase')) {
                e.preventDefault();
                const menuItemId = e.target.dataset.menuItemId;
                this.updateCartQuantity(menuItemId, 'increase');
            }
            
            if (e.target.matches('.cart-qty-decrease')) {
                e.preventDefault();
                const menuItemId = e.target.dataset.menuItemId;
                this.updateCartQuantity(menuItemId, 'decrease');
            }
            
            if (e.target.matches('.cart-remove-btn')) {
                e.preventDefault();
                const menuItemId = e.target.dataset.menuItemId;
                this.removeFromCart(menuItemId);
            }
        });
    }

    /**
     * Setup order-related event listeners
     */
    setupOrderListeners() {
        // Order status updates
        document.addEventListener('change', (e) => {
            if (e.target.matches('.order-status-select')) {
                const orderId = e.target.dataset.orderId;
                const newStatus = e.target.value;
                this.updateOrderStatus(orderId, newStatus);
            }
        });

        // Order actions
        document.addEventListener('click', (e) => {
            if (e.target.matches('.cancel-order-btn')) {
                e.preventDefault();
                const orderId = e.target.dataset.orderId;
                this.cancelOrder(orderId);
            }
        });
    }

    /**
     * Setup search functionality
     */
    setupSearchListeners() {
        const searchInput = document.getElementById('menu-search');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchMenu(e.target.value);
                }, 300);
            });
        }
    }

    /**
     * Setup form enhancements
     */
    setupFormEnhancements() {
        // Auto-resize textareas
        document.querySelectorAll('textarea').forEach(textarea => {
            textarea.addEventListener('input', this.autoResize);
        });

        // Form validation feedback
        document.querySelectorAll('.needs-validation').forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
    }

    /**
     * Auto-resize textarea
     */
    autoResize(e) {
        e.target.style.height = 'auto';
        e.target.style.height = e.target.scrollHeight + 'px';
    }

    /**
     * Add item to cart
     */
    async addToCart(menuItemId, quantity = 1) {
        try {
            this.showLoading('Adding to cart...');
            
            const response = await fetch('/orders/api/cart/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    menu_item_id: menuItemId,
                    quantity: parseInt(quantity)
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('Item added to cart!', 'success');
                this.updateCartBadge(data.cart_count);
            } else {
                this.showToast(data.message || 'Failed to add item to cart', 'error');
            }
        } catch (error) {
            console.error('Add to cart error:', error);
            this.showToast('Error adding item to cart', 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Update cart item quantity
     */
    async updateCartQuantity(menuItemId, action) {
        try {
            const response = await fetch('/orders/api/cart/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    menu_item_id: menuItemId,
                    action: action
                })
            });

            const data = await response.json();
            
            if (data.success) {
                // Update the quantity display
                const quantityElement = document.querySelector(`[data-quantity-for="${menuItemId}"]`);
                if (quantityElement) {
                    quantityElement.textContent = data.new_quantity;
                }
                
                // Update cart badge
                this.updateCartBadge(data.cart_count);
                
                // Update cart total if on cart page
                this.updateCartTotal(data.cart_total);
            } else {
                this.showToast(data.message || 'Failed to update cart', 'error');
            }
        } catch (error) {
            console.error('Update cart error:', error);
            this.showToast('Error updating cart', 'error');
        }
    }

    /**
     * Remove item from cart
     */
    async removeFromCart(menuItemId) {
        if (!confirm('Remove this item from cart?')) {
            return;
        }

        try {
            const response = await fetch('/orders/api/cart/remove/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    menu_item_id: menuItemId
                })
            });

            const data = await response.json();
            
            if (data.success) {
                // Remove the cart item element
                const cartItem = document.querySelector(`[data-cart-item="${menuItemId}"]`);
                if (cartItem) {
                    cartItem.remove();
                }
                
                this.updateCartBadge(data.cart_count);
                this.updateCartTotal(data.cart_total);
                this.showToast('Item removed from cart', 'success');
            } else {
                this.showToast(data.message || 'Failed to remove item', 'error');
            }
        } catch (error) {
            console.error('Remove from cart error:', error);
            this.showToast('Error removing item from cart', 'error');
        }
    }

    /**
     * Update order status
     */
    async updateOrderStatus(orderId, newStatus) {
        try {
            this.showLoading('Updating order status...');
            
            const response = await fetch('/orders/update-status/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    order_id: orderId,
                    status: newStatus
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('Order status updated successfully', 'success');
                // Refresh the page or update the UI
                setTimeout(() => window.location.reload(), 1000);
            } else {
                this.showToast(data.message || 'Failed to update order status', 'error');
            }
        } catch (error) {
            console.error('Update order status error:', error);
            this.showToast('Error updating order status', 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Cancel order
     */
    async cancelOrder(orderId) {
        if (!confirm('Are you sure you want to cancel this order?')) {
            return;
        }

        try {
            this.showLoading('Cancelling order...');
            
            const response = await fetch(`/orders/cancel/${orderId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('Order cancelled successfully', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                this.showToast(data.message || 'Failed to cancel order', 'error');
            }
        } catch (error) {
            console.error('Cancel order error:', error);
            this.showToast('Error cancelling order', 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Search menu items
     */
    async searchMenu(query) {
        if (query.length < 2) {
            document.getElementById('search-results')?.classList.add('d-none');
            return;
        }

        try {
            const response = await fetch(`/menu/api/items/?search=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            this.displaySearchResults(data.items);
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    /**
     * Display search results
     */
    displaySearchResults(items) {
        const resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) return;

        if (items.length === 0) {
            resultsContainer.innerHTML = '<div class="text-center p-3">No items found</div>';
        } else {
            const resultsHTML = items.map(item => `
                <div class="search-result-item p-2 border-bottom">
                    <div class="d-flex align-items-center">
                        <img src="${item.image || '/static/images/placeholder.jpg'}" 
                             alt="${item.name}" class="rounded me-2" width="40" height="40">
                        <div class="flex-grow-1">
                            <h6 class="mb-0">${item.name}</h6>
                            <small class="text-muted">${item.price} XAF</small>
                        </div>
                        <button class="btn btn-sm btn-primary add-to-cart-btn" 
                                data-menu-item-id="${item.id}">
                            <i class="bi bi-plus"></i>
                        </button>
                    </div>
                </div>
            `).join('');
            
            resultsContainer.innerHTML = resultsHTML;
        }
        
        resultsContainer.classList.remove('d-none');
    }

    /**
     * Update cart badge
     */
    updateCartBadge(count = null) {
        const badge = document.getElementById('cart-badge');
        if (badge) {
            if (count !== null) {
                badge.textContent = count;
                badge.style.display = count > 0 ? 'inline' : 'none';
            } else {
                // Fetch current cart count
                this.fetchCartCount().then(cartCount => {
                    badge.textContent = cartCount;
                    badge.style.display = cartCount > 0 ? 'inline' : 'none';
                });
            }
        }
    }

    /**
     * Fetch current cart count
     */
    async fetchCartCount() {
        try {
            const response = await fetch('/orders/api/cart/count/');
            const data = await response.json();
            return data.count || 0;
        } catch (error) {
            console.error('Error fetching cart count:', error);
            return 0;
        }
    }

    /**
     * Update cart total display
     */
    updateCartTotal(total) {
        const totalElement = document.getElementById('cart-total');
        if (totalElement) {
            totalElement.textContent = `${total} XAF`;
        }
    }

    /**
     * Load notifications
     */
    async loadNotifications() {
        try {
            const response = await fetch('/dashboard/api/notifications/');
            const data = await response.json();
            
            this.updateNotificationBadge(data.notifications.length);
            this.displayNotifications(data.notifications);
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }

    /**
     * Update notification badge
     */
    updateNotificationBadge(count) {
        const badge = document.getElementById('notification-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline' : 'none';
        }
    }

    /**
     * Display notifications
     */
    displayNotifications(notifications) {
        const menu = document.getElementById('notification-menu');
        if (!menu) return;

        let menuHTML = '<li class="dropdown-header">Notifications</li><li><hr class="dropdown-divider"></li>';
        
        if (notifications.length === 0) {
            menuHTML += '<li class="dropdown-item-text text-center text-muted">No new notifications</li>';
        } else {
            notifications.forEach(notification => {
                menuHTML += `
                    <li>
                        <a class="dropdown-item notification-item" href="${notification.url}">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <h6 class="dropdown-header">${notification.title}</h6>
                                    <p class="mb-0 small">${notification.message}</p>
                                </div>
                                <small class="text-muted">${notification.time}</small>
                            </div>
                        </a>
                    </li>
                `;
            });
        }
        
        menu.innerHTML = menuHTML;
    }

    /**
     * Update order statistics
     */
    async updateOrderStats() {
        try {
            const response = await fetch('/dashboard/api/order-stats/');
            const data = await response.json();
            
            // Update stat displays if they exist
            Object.keys(data).forEach(key => {
                const element = document.getElementById(`stat-${key}`);
                if (element) {
                    element.textContent = data[key];
                }
            });
        } catch (error) {
            console.error('Error updating order stats:', error);
        }
    }

    /**
     * Start real-time updates
     */
    startRealTimeUpdates() {
        // Update every 30 seconds
        setInterval(() => {
            this.updateCartBadge();
            this.loadNotifications();
            this.updateOrderStats();
        }, 30000);
    }

    /**
     * Show loading indicator
     */
    showLoading(message = 'Loading...') {
        // Create or show loading modal/indicator
        let loadingElement = document.getElementById('loading-indicator');
        if (!loadingElement) {
            loadingElement = document.createElement('div');
            loadingElement.id = 'loading-indicator';
            loadingElement.className = 'position-fixed top-50 start-50 translate-middle bg-primary text-white p-3 rounded shadow';
            loadingElement.style.zIndex = '9999';
            document.body.appendChild(loadingElement);
        }
        loadingElement.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                ${message}
            </div>
        `;
        loadingElement.style.display = 'block';
    }

    /**
     * Hide loading indicator
     */
    hideLoading() {
        const loadingElement = document.getElementById('loading-indicator');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        // Create toast element
        const toastId = 'toast-' + Date.now();
        const bgClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-info';
        
        const toastHTML = `
            <div id="${toastId}" class="toast ${bgClass} text-white" role="alert">
                <div class="toast-body d-flex justify-content-between align-items-center">
                    ${message}
                    <button type="button" class="btn-close btn-close-white ms-2" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        // Show toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    /**
     * Get CSRF token
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.content || '';
    }

    /**
     * Format currency
     */
    formatCurrency(amount) {
        return new Intl.NumberFormat('fr-CM', {
            style: 'currency',
            currency: 'XAF',
            minimumFractionDigits: 0
        }).format(amount);
    }

    /**
     * Format date
     */
    formatDate(date) {
        return new Intl.DateTimeFormat('fr-CM', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Dashboard;
}