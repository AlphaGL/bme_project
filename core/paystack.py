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
            amount: Amount in naira (will be converted to kobo)
            reference: Unique transaction reference
            callback_url: URL to redirect after payment
        
        Returns:
            dict: Response from Paystack API
        """
        url = f"{self.BASE_URL}/transaction/initialize"
        
        # FIXED: Ensure amount is properly converted to kobo (integer)
        try:
            # Convert to Decimal first if it's not already
            if not isinstance(amount, Decimal):
                amount = Decimal(str(amount))
            
            # Convert to kobo (multiply by 100) and ensure it's an integer
            amount_in_kobo = int(amount * 100)
            
            # IMPORTANT: Paystack requires minimum amount of 10 naira (1000 kobo)
            if amount_in_kobo < 1000:
                return {
                    'status': False,
                    'message': 'Amount must be at least ₦10.00'
                }
        except (ValueError, TypeError) as e:
            return {
                'status': False,
                'message': f'Invalid amount format: {str(e)}'
            }
        
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
            print(f"DEBUG: Initializing payment with payload: {payload}")  # Debug log
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            
            # Log response for debugging
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response body: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            # Get detailed error message from Paystack
            error_msg = 'Payment initialization failed'
            try:
                error_data = response.json()
                error_msg = error_data.get('message', str(e))
            except:
                error_msg = str(e)
            
            return {
                'status': False,
                'message': error_msg
            }
        except requests.exceptions.Timeout:
            return {
                'status': False,
                'message': 'Payment service timeout. Please try again.'
            }
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
            response = requests.get(url, headers=self.headers, timeout=30)
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
            response = requests.get(url, headers=self.headers, timeout=30)
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
    import uuid
    
    # Create or get payment record
    payment = create_payment_for_student(student, request)
    
    # CRITICAL FIX: Generate a NEW unique reference each time
    # This prevents "Duplicate Transaction Reference" error
    new_reference = f"BME-{uuid.uuid4().hex[:12].upper()}"
    payment.reference = new_reference
    payment.status = 'pending'  # Reset status
    payment.save()
    
    # FIXED: Generate proper email if student doesn't have one
    email = student.email
    if not email or '@' not in email:
        # Use a valid email format
        email = f"{student.reg_number.replace('/', '_')}@student.futo.edu.ng"
    
    # Initialize with Paystack
    paystack = PaystackAPI()
    
    # Build callback URL (make sure it's absolute URL)
    callback_url = request.build_absolute_uri('/student/payment/verify/')
    
    print(f"DEBUG: Initializing payment for {student.reg_number}")
    print(f"DEBUG: Email: {email}")
    print(f"DEBUG: Amount: {payment.amount}")
    print(f"DEBUG: Reference: {new_reference}")
    print(f"DEBUG: Callback URL: {callback_url}")
    
    response = paystack.initialize_transaction(
        email=email,
        amount=payment.amount,
        reference=new_reference,
        callback_url=callback_url
    )
    
    print(f"DEBUG: Paystack response: {response}")
    
    if response.get('status'):
        # Save Paystack details
        data = response.get('data', {})
        payment.access_code = data.get('access_code')
        
        # CRITICAL: Save BOTH references
        # Paystack returns its own reference which might be different
        payment.paystack_reference = data.get('reference', new_reference)
        payment.status = 'processing'
        payment.save()
        
        print(f"DEBUG: Payment saved with:")
        print(f"  - Our reference: {payment.reference}")
        print(f"  - Paystack reference: {payment.paystack_reference}")
        print(f"  - Access code: {payment.access_code}")
        
        return {
            'status': True,
            'authorization_url': data.get('authorization_url'),
            'access_code': data.get('access_code'),
            'reference': payment.reference,
            'paystack_reference': payment.paystack_reference
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
        reference: Payment reference (could be our reference or Paystack's)
    
    Returns:
        dict: Verification result
    """
    from core.models import StudentPayment, Student
    from django.utils import timezone
    import json
    
    # Try to find payment by either reference field
    payment = None
    try:
        payment = StudentPayment.objects.get(reference=reference)
        print(f"DEBUG verify: Found by our reference")
    except StudentPayment.DoesNotExist:
        try:
            payment = StudentPayment.objects.get(paystack_reference=reference)
            print(f"DEBUG verify: Found by Paystack reference")
        except StudentPayment.DoesNotExist:
            print(f"DEBUG verify: Payment not found with reference: {reference}")
            # Try to find any pending payment (last resort)
            payment = StudentPayment.objects.filter(status='processing').first()
            if not payment:
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