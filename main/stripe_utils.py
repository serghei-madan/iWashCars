import stripe
from django.conf import settings
from django.utils import timezone
from .models import Payment, Booking
import logging

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentService:
    """Service class for handling Stripe payments"""

    @staticmethod
    def create_payment_intent(booking, customer_email):
        """
        Create a Stripe PaymentIntent with manual capture for deposit + authorization
        """
        try:
            total_amount_cents = int(booking.service.price * 100)
            deposit_amount_cents = settings.STRIPE_DEPOSIT_AMOUNT

            # Create or retrieve Stripe customer
            customer = stripe.Customer.create(
                email=customer_email,
                name=f"{booking.first_name} {booking.last_name}",
                metadata={
                    'booking_id': str(booking.id),
                    'phone': booking.phone or '',
                }
            )

            # Create PaymentIntent with manual capture
            intent = stripe.PaymentIntent.create(
                amount=total_amount_cents,
                currency='usd',
                customer=customer.id,
                capture_method='manual',  # This allows us to authorize and capture separately
                metadata={
                    'booking_id': str(booking.id),
                    'service_name': booking.service.name,
                    'customer_name': f"{booking.first_name} {booking.last_name}",
                    'booking_date': str(booking.booking_date),
                    'booking_time': str(booking.booking_time),
                    'deposit_amount': str(deposit_amount_cents),
                }
            )

            # Create Payment record
            payment = Payment.objects.create(
                booking=booking,
                stripe_payment_intent_id=intent.id,
                stripe_customer_id=customer.id,
                deposit_amount=deposit_amount_cents,
                total_amount=total_amount_cents,
                remaining_amount=total_amount_cents - deposit_amount_cents,
                status='pending'
            )

            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_id': payment.id,
                'deposit_amount': deposit_amount_cents,
                'total_amount': total_amount_cents,
            }

        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e),
            }

    @staticmethod
    def capture_deposit(payment):
        """
        Capture the deposit amount from the authorized PaymentIntent
        """
        try:
            # First capture the deposit amount
            stripe.PaymentIntent.capture(
                payment.stripe_payment_intent_id,
                amount_to_capture=payment.deposit_amount
            )

            # Update payment record
            payment.status = 'deposit_captured'
            payment.deposit_captured_at = timezone.now()
            payment.save()

            return {
                'success': True,
                'message': f'Deposit of ${payment.get_deposit_amount_dollars():.2f} captured successfully'
            }

        except stripe.error.StripeError as e:
            payment.status = 'failed'
            payment.notes = f'Deposit capture failed: {str(e)}'
            payment.save()

            return {
                'success': False,
                'error': str(e),
            }

    @staticmethod
    def capture_remaining_amount(payment):
        """
        Capture the remaining amount after deposit
        """
        if not payment.can_capture_remaining():
            return {
                'success': False,
                'error': 'Cannot capture remaining amount. Payment status must be deposit_captured.'
            }

        try:
            # Get the original PaymentIntent to check current state
            intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)

            # Debug: Log the intent status and amounts
            print(f"PaymentIntent status: {intent.status}")
            print(f"Amount: {intent.amount}, Amount Received: {getattr(intent, 'amount_received', 0)}")
            print(f"Amount Capturable: {getattr(intent, 'amount_capturable', 0)}")

            # Check if already fully captured
            if intent.status == 'succeeded':
                # Payment is already fully captured
                amount_received = getattr(intent, 'amount_received', intent.amount)

                # Update our database to reflect the correct status
                payment.status = 'fully_captured'
                payment.fully_captured_at = timezone.now()
                payment.save()

                # Send service completion receipt email
                try:
                    from .notification_utils import NotificationService
                    receipt_result = NotificationService.send_service_completion_receipt(payment)
                    if receipt_result['success']:
                        logger.info(f"Service completion receipt sent for payment #{payment.id}")
                except Exception as e:
                    logger.error(f"Error sending service completion receipt: {str(e)}")

                return {
                    'success': True,
                    'message': f'Payment already fully captured. Total amount: ${amount_received/100:.2f}',
                    'receipt_sent': receipt_result.get('success', False) if 'receipt_result' in locals() else False
                }

            # Check what's already been captured
            amount_already_captured = getattr(intent, 'amount_received', 0)
            total_authorized = intent.amount
            amount_capturable = getattr(intent, 'amount_capturable', 0)

            # If nothing left to capture
            if amount_capturable <= 0:
                # Check if it's because everything was already captured
                if amount_already_captured >= total_authorized:
                    payment.status = 'fully_captured'
                    payment.fully_captured_at = timezone.now()
                    payment.save()

                    return {
                        'success': True,
                        'message': f'Payment already fully captured. Total: ${total_authorized/100:.2f}'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'No amount available to capture. Status: {intent.status}, Captured: ${amount_already_captured/100:.2f} of ${total_authorized/100:.2f}'
                    }

            # Capture the remaining amount
            captured_intent = stripe.PaymentIntent.capture(
                payment.stripe_payment_intent_id,
                amount_to_capture=amount_capturable
            )

            # Update payment record
            payment.status = 'fully_captured'
            payment.fully_captured_at = timezone.now()
            payment.save()

            # Send service completion receipt email
            try:
                from .notification_utils import NotificationService
                receipt_result = NotificationService.send_service_completion_receipt(payment)
                if receipt_result['success']:
                    logger.info(f"Service completion receipt sent for payment #{payment.id}")
                else:
                    logger.error(f"Failed to send receipt: {receipt_result.get('error')}")
            except Exception as e:
                logger.error(f"Error sending service completion receipt: {str(e)}")

            final_amount = getattr(captured_intent, 'amount_received', amount_capturable)
            return {
                'success': True,
                'message': f'Successfully captured ${amount_capturable/100:.2f}. Total captured: ${final_amount/100:.2f}',
                'receipt_sent': receipt_result.get('success', False) if 'receipt_result' in locals() else False
            }

        except stripe.error.InvalidRequestError as e:
            # Handle the specific "already captured" error
            if 'already been captured' in str(e):
                # Update our database to reflect that it's fully captured
                payment.status = 'fully_captured'
                payment.fully_captured_at = timezone.now()
                payment.notes = 'Payment was already captured in Stripe'
                payment.save()

                return {
                    'success': True,
                    'message': f'Payment was already fully captured. Database updated to reflect current status.'
                }
            else:
                payment.notes = f'Capture failed: {str(e)}'
                payment.save()
                return {
                    'success': False,
                    'error': str(e),
                }

        except stripe.error.StripeError as e:
            payment.notes = f'Remaining capture failed: {str(e)}'
            payment.save()

            return {
                'success': False,
                'error': str(e),
            }

    @staticmethod
    def refund_deposit(payment, reason="Service issue"):
        """
        Refund the captured deposit
        """
        if not payment.can_refund_deposit():
            return {
                'success': False,
                'error': 'Cannot refund deposit. No captured payment found.'
            }

        try:
            # Create a refund for the deposit amount
            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                amount=payment.deposit_amount,
                reason='requested_by_customer',
                metadata={
                    'booking_id': str(payment.booking.id),
                    'refund_reason': reason,
                }
            )

            # Update payment record
            payment.status = 'deposit_refunded'
            payment.refunded_at = timezone.now()
            payment.notes = f'Deposit refunded: {reason}'
            payment.save()

            # Send refund receipt email
            try:
                from .notification_utils import NotificationService
                receipt_result = NotificationService.send_refund_receipt(payment)
                if receipt_result['success']:
                    logger.info(f"Refund receipt sent for payment #{payment.id}")
                else:
                    logger.error(f"Failed to send refund receipt: {receipt_result.get('error')}")
            except Exception as e:
                logger.error(f"Error sending refund receipt: {str(e)}")

            return {
                'success': True,
                'message': f'Deposit of ${payment.get_deposit_amount_dollars():.2f} refunded successfully',
                'refund_id': refund.id,
                'receipt_sent': receipt_result.get('success', False) if 'receipt_result' in locals() else False
            }

        except stripe.error.StripeError as e:
            payment.notes = f'Refund failed: {str(e)}'
            payment.save()

            return {
                'success': False,
                'error': str(e),
            }

    @staticmethod
    def cancel_authorization(payment):
        """
        Cancel the authorization (release held funds without capturing)
        """
        if not payment.can_cancel_authorization():
            return {
                'success': False,
                'error': 'Cannot cancel authorization. Payment must be in deposit_captured state.'
            }

        try:
            # Cancel the PaymentIntent
            stripe.PaymentIntent.cancel(payment.stripe_payment_intent_id)

            # Update payment record
            payment.status = 'cancelled'
            payment.notes = 'Authorization cancelled - funds released'
            payment.save()

            return {
                'success': True,
                'message': 'Authorization cancelled. Remaining funds released to customer.'
            }

        except stripe.error.StripeError as e:
            payment.notes = f'Cancel authorization failed: {str(e)}'
            payment.save()

            return {
                'success': False,
                'error': str(e),
            }

    @staticmethod
    def get_payment_status(payment):
        """
        Get current payment status from Stripe
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
            return {
                'success': True,
                'stripe_status': intent.status,
                'amount': intent.amount,
                'amount_received': getattr(intent, 'amount_received', 0),
                'amount_capturable': getattr(intent, 'amount_capturable', 0),
                'charges': len(intent.charges.data) if hasattr(intent, 'charges') else 0,
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e),
            }

    @staticmethod
    def debug_payment_intent(payment_intent_id):
        """
        Debug function to understand PaymentIntent state
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id, expand=['latest_charge'])

            print(f"\n=== PaymentIntent Debug Info ===")
            print(f"ID: {intent.id}")
            print(f"Status: {intent.status}")
            print(f"Amount: {intent.amount}")
            print(f"Amount Received: {getattr(intent, 'amount_received', 'N/A')}")
            print(f"Amount Capturable: {getattr(intent, 'amount_capturable', 'N/A')}")
            print(f"Currency: {intent.currency}")
            print(f"Capture Method: {intent.capture_method}")

            if hasattr(intent, 'latest_charge') and intent.latest_charge:
                charge = intent.latest_charge
                print(f"Latest Charge ID: {charge.id}")
                print(f"Charge Amount: {charge.amount}")
                print(f"Charge Amount Captured: {getattr(charge, 'amount_captured', 'N/A')}")
                print(f"Charge Amount Refunded: {getattr(charge, 'amount_refunded', 'N/A')}")
                print(f"Charge Status: {charge.status}")

            print(f"=== End Debug Info ===\n")

            return {
                'success': True,
                'debug_info': {
                    'status': intent.status,
                    'amount': intent.amount,
                    'amount_received': getattr(intent, 'amount_received', 0),
                    'amount_capturable': getattr(intent, 'amount_capturable', 0),
                    'capture_method': intent.capture_method,
                }
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e),
            }