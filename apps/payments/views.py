from django.views.generic import View, ListView, DetailView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Payment
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ProcessPaymentView(View):
    def post(self, request):
        # Logic to initiate payment processing
        try:
            # Example: Process payment with a payment gateway
            payment_id = request.POST.get('payment_id')
            # Add your payment gateway integration logic here
            return redirect('payments:success')
        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            return redirect('payments:failed')

class PaymentSuccessView(View):
    def get(self, request):
        return render(request, 'payments/success.html', {'message': 'Payment successful'})

class PaymentCancelView(View):
    def get(self, request):
        return render(request, 'payments/cancel.html', {'message': 'Payment cancelled'})

class PaymentFailedView(View):
    def get(self, request):
        return render(request, 'payments/failed.html', {'message': 'Payment failed'})

class PaymentDetailView(View):
    def get(self, request, payment_id):
        payment = get_object_or_404(Payment, id=payment_id)
        return render(request, 'payments/detail.html', {'payment': payment})

class OrderPaymentView(View):
    def get(self, request, order_number):
        # Fetch payment details associated with order_number
        payment = get_object_or_404(Payment, order_number=order_number)
        return render(request, 'payments/order_payment.html', {'payment': payment})

class AdminPaymentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Payment
    template_name = 'payments/admin_list.html'
    context_object_name = 'payments'

    def test_func(self):
        return self.request.user.is_staff

class FailedPaymentsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Payment
    template_name = 'payments/admin_failed.html'
    context_object_name = 'payments'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return Payment.objects.filter(status='failed')

class AdminPaymentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Payment
    template_name = 'payments/admin_detail.html'
    context_object_name = 'payment'

    def test_func(self):
        return self.request.user.is_staff

def orange_webhook(request):
    if request.method == 'POST':
        # Handle Orange webhook payload
        logger.info("Received Orange webhook")
        try:
            # Process webhook data
            # Example: Update payment status based on webhook
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"Orange webhook error: {str(e)}")
            return HttpResponse(status=400)
    return HttpResponse(status=405)

def mtn_webhook(request):
    if request.method == 'POST':
        # Handle MTN webhook payload
        logger.info("Received MTN webhook")
        try:
            # Process webhook data
            # Example: Update payment status based on webhook
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"MTN webhook error: {str(e)}")
            return HttpResponse(status=400)
    return HttpResponse(status=405)

def payment_status_api(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return JsonResponse({
        'payment_id': str(payment.id),
        'status': payment.status,
        'amount': str(payment.amount),
        'created_at': payment.created_at.isoformat(),
    })

def retry_payment_api(request, payment_id):
    if request.method == 'POST':
        payment = get_object_or_404(Payment, id=payment_id)
        try:
            # Logic to retry payment
            # Example: Re-initiate payment with gateway
            payment.status = 'pending'
            payment.save()
            return JsonResponse({'status': 'retry_initiated', 'payment_id': str(payment.id)})
        except Exception as e:
            logger.error(f"Retry payment failed: {str(e)}")
            return JsonResponse({'error': 'Retry failed'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)