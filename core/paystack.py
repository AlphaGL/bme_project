import requests
from django.conf import settings
from decimal import Decimal
import json

class PaystackAPI:
    """Handle all Paystack API interactions"""
    
    BASE_URL = "https://api.paystack.co"
    
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.public_key = settings.PAYSTACK_PUBLIC_KEY
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
    
    def initialize_transaction(self, email, amount, reference, callback_url):
        """
        Initialize a payment transaction
        
        Args:
            email: Customer email
            amount: Amount in kobo (multiply naira by 100)
            reference: Unique transaction reference
            callback_url: URL to redirect after payment
        
        Returns:
            dict: Response from Paystack API
        """
        url = f"{self.BASE_URL}/transaction/initialize"
        
        # Convert amount to kobo (Paystack uses kobo)
        amount_in_kobo = int(Decimal(amount) * 100)
        
        payload = {
            "email": email,
            "amount": amount_in_kobo,
            "reference": reference,
            "callback_url": callback_url,
            "currency": "NGN",
            "metadata": {
                "custom_fields": [
                    {
                        "display_name": "Purpose",
                        "variable_name": "purpose",
                        "value": "FUTO BME Portal Access Fee"
                    }
                ]
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'status': False,
                'message': f'Payment initialization failed: {str(e)}'
            }
    
    def verify_transaction(self, reference):
        """
        Verify a payment transaction
        
        Args:
            reference: Transaction reference to verify
        
        Returns:
            dict: Verification response
        """
        url = f"{self.BASE_URL}/transaction/verify/{reference}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'status': False,
                'message': f'Verification failed: {str(e)}'
            }
    
    def get_transaction(self, transaction_id):
        """Get transaction details"""
        url = f"{self.BASE_URL}/transaction/{transaction_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'status': False,
                'message': f'Failed to get transaction: {str(e)}'
            }


def create_payment_for_student(student, request):
    """
    Create a payment record for a student
    
    Args:
        student: Student instance
        request: Django request object
    
    Returns:
        StudentPayment instance
    """
    from core.models import StudentPayment
    from django.utils import timezone
    
    # Check if payment already exists
    payment, created = StudentPayment.objects.get_or_create(
        student=student,
        defaults={
            'amount': Decimal('1250.00'),
            'department_amount': Decimal('1000.00'),
            'charges': Decimal('250.00'),
            'status': 'pending',
            'ip_address': get_client_ip(request)
        }
    )
    
    return payment


def initialize_student_payment(student, request):
    """
    Initialize payment with Paystack
    
    Args:
        student: Student instance
        request: Django request object
    
    Returns:
        dict: Payment initialization response
    """
    from core.models import StudentPayment
    
    # Create or get payment record
    payment = create_payment_for_student(student, request)
    
    # Initialize with Paystack
    paystack = PaystackAPI()
    
    # Build callback URL
    callback_url = request.build_absolute_uri('/student/payment/verify/')
    
    response = paystack.initialize_transaction(
        email=student.email or f"{student.reg_number}@student.futo.edu.ng",
        amount=payment.amount,
        reference=payment.reference,
        callback_url=callback_url
    )
    
    if response.get('status'):
        # Save Paystack details
        data = response.get('data', {})
        payment.access_code = data.get('access_code')
        payment.paystack_reference = data.get('reference')
        payment.status = 'processing'
        payment.save()
        
        return {
            'status': True,
            'authorization_url': data.get('authorization_url'),
            'access_code': data.get('access_code'),
            'reference': payment.reference
        }
    else:
        return {
            'status': False,
            'message': response.get('message', 'Payment initialization failed')
        }


def verify_student_payment(reference):
    """
    Verify a student's payment
    
    Args:
        reference: Payment reference
    
    Returns:
        dict: Verification result
    """
    from core.models import StudentPayment, Student
    from django.utils import timezone
    import json
    
    try:
        payment = StudentPayment.objects.get(reference=reference)
    except StudentPayment.DoesNotExist:
        return {
            'status': False,
            'message': 'Payment record not found'
        }
    
    # Verify with Paystack
    paystack = PaystackAPI()
    response = paystack.verify_transaction(reference)
    
    if response.get('status'):
        data = response.get('data', {})
        
        # Check if payment was successful
        if data.get('status') == 'success':
            # Update payment record
            payment.status = 'success'
            payment.is_verified = True
            payment.paid_at = timezone.now()
            payment.verification_data = json.dumps(data)
            payment.payment_method = data.get('channel')
            payment.save()
            
            # Update student record
            student = payment.student
            student.has_paid = True
            student.payment_verified_at = timezone.now()
            student.save()
            
            return {
                'status': True,
                'message': 'Payment verified successfully',
                'payment': payment,
                'student': student
            }
        else:
            payment.status = 'failed'
            payment.save()
            
            return {
                'status': False,
                'message': f'Payment failed: {data.get("gateway_response", "Unknown error")}'
            }
    else:
        return {
            'status': False,
            'message': response.get('message', 'Verification failed')
        }


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip