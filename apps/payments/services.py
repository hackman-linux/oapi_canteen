# apps/payments/services.py
import requests
import json
import hashlib
import hmac
from django.conf import settings
from django.utils import timezone
from .models import Payment, PaymentStatusHistory
import logging

logger = logging.getLogger(__name__)


class MobileMoneyService:
    """Base class for mobile money services"""
    
    def __init__(self):
        self.timeout = 30
    
    def initiate_payment(self, payment):
        """Initiate payment with provider - to be implemented by subclasses"""
        raise NotImplementedError
    
    def check_payment_status(self, payment):
        """Check payment status with provider"""
        raise NotImplementedError
    
    def process_webhook(self, request_data):
        """Process webhook from provider"""
        raise NotImplementedError


class OrangeMoneyService(MobileMoneyService):
    """Orange Money payment service"""
    
    def __init__(self):
        super().__init__()
        self.config = settings.ORANGE_MONEY
        self.base_url = self.config['BASE_URL']
        self.api_key = self.config['API_KEY']
        self.api_secret = self.config['API_SECRET']
        self.merchant_key = self.config['MERCHANT_KEY']
    
    def get_access_token(self):
        """Get access token for Orange Money API"""
        url = f"{self.base_url}/oauth/token"
        
        headers = {
            'Authorization': f'Basic {self._get_basic_auth()}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(url, headers=headers, data=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()['access_token']
        except requests.RequestException as e:
            logger.error(f"Orange Money token request failed: {e}")
            raise
    
    def _get_basic_auth(self):
        """Generate basic auth header"""
        import base64
        credentials = f"{self.api_key}:{self.api_secret}"
        return base64.b64encode(credentials.encode()).decode()
    
    def initiate_payment(self, payment):
        """Initiate Orange Money payment"""
        access_token = self.get_access_token()
        
        url = f"{self.base_url}/webpayment/v1/transactionrequests"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Callback-Url': f"{settings.SITE_URL}/payments/webhook/orange/",
        }
        
        payload = {
            'amount': str(payment.total_amount),
            'currency': 'XAF',
            'orderId': str(payment.order.order_number),
            'customerMsisdn': payment.customer_phone,
            'customerEmail': payment.customer_email,
            'merchantTransactionId': str(payment.payment_id),
            'description': f"Payment for order #{payment.order.order_number}",
            'returnUrl': f"{settings.SITE_URL}/payments/success/",
            'cancelUrl': f"{settings.SITE_URL}/payments/cancel/",
            'notifUrl': f"{settings.SITE_URL}/payments/webhook/orange/",
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            
            # Update payment with provider data
            payment.transaction_id = result.get('transactionId')
            payment.provider_data = result
            payment.status = Payment.PaymentStatus.PROCESSING
            payment.save()
            
            # Create status history
            PaymentStatusHistory.objects.create(
                payment=payment,
                previous_status=Payment.PaymentStatus.PENDING,
                new_status=Payment.PaymentStatus.PROCESSING,
                provider_response=result,
                notes="Payment initiated with Orange Money"
            )
            
            return {
                'success': True,
                'payment_url': result.get('paymentUrl'),
                'transaction_id': result.get('transactionId'),
                'message': 'Payment initiated successfully'
            }
            
        except requests.RequestException as e:
            logger.error(f"Orange Money payment initiation failed: {e}")
            payment.status = Payment.PaymentStatus.FAILED
            payment.failure_reason = str(e)
            payment.save()
            
            return {
                'success': False,
                'message': f'Payment initiation failed: {e}'
            }
    
    def check_payment_status(self, payment):
        """Check payment status with Orange Money"""
        if not payment.transaction_id:
            return {'success': False, 'message': 'No transaction ID available'}
        
        access_token = self.get_access_token()
        url = f"{self.base_url}/webpayment/v1/transactionrequests/{payment.transaction_id}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            old_status = payment.status
            
            # Map Orange Money status to our status
            orange_status = result.get('status', '').upper()
            if orange_status == 'SUCCESS':
                payment.status = Payment.PaymentStatus.COMPLETED
                payment.processed_at = timezone.now()
            elif orange_status in ['FAILED', 'DECLINED']:
                payment.status = Payment.PaymentStatus.FAILED
                payment.failure_reason = result.get('message', 'Payment failed')
            elif orange_status == 'CANCELLED':
                payment.status = Payment.PaymentStatus.CANCELLED
            elif orange_status == 'EXPIRED':
                payment.status = Payment.PaymentStatus.EXPIRED
            
            payment.provider_response = result
            payment.save()
            
            # Create status history if status changed
            if old_status != payment.status:
                PaymentStatusHistory.objects.create(
                    payment=payment,
                    previous_status=old_status,
                    new_status=payment.status,
                    provider_response=result,
                    notes=f"Status updated from Orange Money API"
                )
            
            return {'success': True, 'status': payment.status}
            
        except requests.RequestException as e:
            logger.error(f"Orange Money status check failed: {e}")
            return {'success': False, 'message': str(e)}


class MTNMoneyService(MobileMoneyService):
    """MTN Mobile Money payment service"""
    
    def __init__(self):
        super().__init__()
        self.config = settings.MTN_MONEY
        self.base_url = self.config['BASE_URL']
        self.api_key = self.config['API_KEY']
        self.api_secret = self.config['API_SECRET']
        self.subscription_key = self.config['SUBSCRIPTION_KEY']
    
    def get_access_token(self):
        """Get access token for MTN MoMo API"""
        url = f"{self.base_url}/collection/token/"
        
        headers = {
            'Authorization': f'Basic {self._get_basic_auth()}',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()['access_token']
        except requests.RequestException as e:
            logger.error(f"MTN MoMo token request failed: {e}")
            raise
    
    def _get_basic_auth(self):
        """Generate basic auth header"""
        import base64
        credentials = f"{self.api_key}:{self.api_secret}"
        return base64.b64encode(credentials.encode()).decode()
    
    def initiate_payment(self, payment):
        """Initiate MTN Mobile Money payment"""
        access_token = self.get_access_token()
        
        url = f"{self.base_url}/collection/v1_0/requesttopay"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Reference-Id': str(payment.payment_id),
            'X-Target-Environment': 'sandbox',  # Change to 'production' for live
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'amount': str(payment.total_amount),
            'currency': 'XAF',
            'externalId': str(payment.order.order_number),
            'payer': {
                'partyIdType': 'MSISDN',
                'partyId': payment.customer_phone.replace('+', '')
            },
            'payerMessage': f"Payment for order #{payment.order.order_number}",
            'payeeNote': f"OAPI Canteen - Order #{payment.order.order_number}"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            # MTN returns 202 for successful initiation
            if response.status_code == 202:
                payment.transaction_id = str(payment.payment_id)
                payment.provider_data = payload
                payment.status = Payment.PaymentStatus.PROCESSING
                payment.save()
                
                # Create status history
                PaymentStatusHistory.objects.create(
                    payment=payment,
                    previous_status=Payment.PaymentStatus.PENDING,
                    new_status=Payment.PaymentStatus.PROCESSING,
                    provider_response={'status': 'initiated'},
                    notes="Payment initiated with MTN Mobile Money"
                )
                
                return {
                    'success': True,
                    'transaction_id': payment.transaction_id,
                    'message': 'Payment initiated successfully. Please complete on your phone.'
                }
            else:
                payment.status = Payment.PaymentStatus.FAILED
                payment.failure_reason = 'Payment initiation failed'
                payment.save()
                
                return {
                    'success': False,
                    'message': 'Payment initiation failed'
                }
                
        except requests.RequestException as e:
            logger.error(f"MTN MoMo payment initiation failed: {e}")
            payment.status = Payment.PaymentStatus.FAILED
            payment.failure_reason = str(e)
            payment.save()
            
            return {
                'success': False,
                'message': f'Payment initiation failed: {e}'
            }
    
    def check_payment_status(self, payment):
        """Check payment status with MTN Mobile Money"""
        if not payment.transaction_id:
            return {'success': False, 'message': 'No transaction ID available'}
        
        access_token = self.get_access_token()
        url = f"{self.base_url}/collection/v1_0/requesttopay/{payment.transaction_id}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Target-Environment': 'sandbox',  # Change to 'production' for live
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            old_status = payment.status
            
            # Map MTN status to our status
            mtn_status = result.get('status', '').upper()
            if mtn_status == 'SUCCESSFUL':
                payment.status = Payment.PaymentStatus.COMPLETED
                payment.processed_at = timezone.now()
            elif mtn_status == 'FAILED':
                payment.status = Payment.PaymentStatus.FAILED
                payment.failure_reason = result.get('reason', 'Payment failed')
            elif mtn_status == 'PENDING':
                payment.status = Payment.PaymentStatus.PROCESSING
            
            payment.provider_response = result
            payment.save()
            
            # Create status history if status changed
            if old_status != payment.status:
                PaymentStatusHistory.objects.create(
                    payment=payment,
                    previous_status=old_status,
                    new_status=payment.status,
                    provider_response=result,
                    notes=f"Status updated from MTN MoMo API"
                )
            
            return {'success': True, 'status': payment.status}
            
        except requests.RequestException as e:
            logger.error(f"MTN MoMo status check failed: {e}")
            return {'success': False, 'message': str(e)}


def get_payment_service(provider):
    """Factory function to get payment service"""
    services = {
        'ORANGE': OrangeMoneyService,
        'MTN': MTNMoneyService,
    }
    
    service_class = services.get(provider)
    if not service_class:
        raise ValueError(f"Unsupported payment provider: {provider}")
    
    return service_class()


