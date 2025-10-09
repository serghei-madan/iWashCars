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
        Create a Stripe PaymentIntent for deposit with setup_future_usage to save payment method
        This allows us to charge the remaining amount later without time limits
        """
        try:
            total_amount_cents = int(booking.service.price * 100)
            deposit_amount_cents = booking.service.get_deposit_amount()  # Get deposit from service

            # Create or retrieve Stripe customer
            customer = stripe.Customer.create(
                email=customer_email,
                name=f"{booking.first_name} {booking.last_name}",
                metadata={
                    'booking_id': str(booking.id),
                    'phone': booking.phone or '',
                }
            )

            # Create PaymentIntent for deposit with setup_future_usage
            # This saves the payment method for future off-session charges (no 7-day limit!)
            intent = stripe.PaymentIntent.create(
                amount=deposit_amount_cents,  # Only charge deposit now
                currency='usd',
                customer=customer.id,
                capture_method='manual',  # This allows us to authorize and capture separately
                setup_future_usage='off_session',  # Save payment method for future charges
                metadata={
                    'booking_id': str(booking.id),
                    'service_name': booking.service.name,
                    'customer_name': f"{booking.first_name} {booking.last_name}",
                    'booking_date': str(booking.booking_date),
                    'booking_time': str(booking.booking_time),
                    'deposit_amount': str(deposit_amount_cents),
                    'total_amount': str(total_amount_cents),
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
        Capture the deposit amount and save the payment method for future charges
        """
        try:
            # Capture the deposit amount
            captured_intent = stripe.PaymentIntent.capture(
                payment.stripe_payment_intent_id,
                amount_to_capture=payment.deposit_amount
            )

            # Retrieve the payment method ID from the captured intent
            # This will be used for future off-session charges
            payment_method_id = captured_intent.payment_method

            # Update payment record with payment method and status
            payment.status = 'deposit_captured'
            payment.deposit_captured_at = timezone.now()
            payment.saved_payment_method_id = payment_method_id
            payment.save()

            logger.info(f"Deposit captured and payment method {payment_method_id} saved for booking #{payment.booking.id}")

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
    def charge_saved_payment_method(payment, amount_cents):
        """
        Create a new PaymentIntent to charge a saved payment method off-session
        This has no time limits - can be used weeks or months after the initial booking

        Args:
            payment: Payment object with saved_payment_method_id
            amount_cents: Amount to charge in cents

        Returns:
            dict with success status and message or error
        """
        if not payment.saved_payment_method_id:
            return {
                'success': False,
                'error': 'No saved payment method found. Customer needs to provide payment details.'
            }

        try:
            # Create a new PaymentIntent with the saved payment method
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',
                customer=payment.stripe_customer_id,
                payment_method=payment.saved_payment_method_id,
                off_session=True,  # Indicates customer is not present
                confirm=True,  # Immediately confirm the payment
                metadata={
                    'booking_id': str(payment.booking.id),
                    'payment_type': 'final_payment',
                    'service_name': payment.booking.service.name,
                    'customer_name': f"{payment.booking.first_name} {payment.booking.last_name}",
                }
            )

            logger.info(f"Successfully charged ${amount_cents/100:.2f} for booking #{payment.booking.id} using saved payment method")

            return {
                'success': True,
                'payment_intent_id': intent.id,
                'amount_charged': amount_cents,
                'message': f'Successfully charged ${amount_cents/100:.2f}'
            }

        except stripe.error.CardError as e:
            # Card was declined or requires authentication
            err = e.error
            logger.error(f"Card error charging booking #{payment.booking.id}: {err.message}")

            # Check if authentication is required
            if err.code == 'authentication_required':
                return {
                    'success': False,
                    'error': 'Payment requires customer authentication. Please send a payment request email to the customer.',
                    'requires_action': True,
                    'payment_intent_id': err.payment_intent.id if hasattr(err, 'payment_intent') else None
                }

            return {
                'success': False,
                'error': f'Card was declined: {err.message}'
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error charging booking #{payment.booking.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def capture_remaining_amount(payment):
        """
        Charge the remaining amount using the saved payment method
        Uses the new off-session charge method - no 7-day limit!
        """
        if not payment.can_capture_remaining():
            return {
                'success': False,
                'error': 'Cannot capture remaining amount. Payment status must be deposit_captured.'
            }

        try:
            # Check if already fully captured
            if payment.status == 'fully_captured':
                logger.info(f"Payment #{payment.id} already fully captured")
                return {
                    'success': True,
                    'message': f'Payment already fully captured. Total: ${payment.get_total_amount_dollars():.2f}'
                }

            # Charge the remaining amount using saved payment method
            charge_result = StripePaymentService.charge_saved_payment_method(
                payment,
                payment.remaining_amount
            )

            if not charge_result['success']:
                # Log the error but don't update status yet
                payment.notes = f'Remaining payment failed: {charge_result["error"]}'
                payment.save()
                return charge_result

            # Update payment record
            payment.status = 'fully_captured'
            payment.fully_captured_at = timezone.now()
            payment.notes = f'Remaining ${payment.get_remaining_amount_dollars():.2f} charged successfully via saved payment method'
            payment.save()

            logger.info(f"Remaining amount captured for booking #{payment.booking.id}. Total paid: ${payment.get_total_amount_dollars():.2f}")

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
                receipt_result = {'success': False}

            return {
                'success': True,
                'message': f'Successfully charged remaining ${payment.get_remaining_amount_dollars():.2f}. Total paid: ${payment.get_total_amount_dollars():.2f}',
                'receipt_sent': receipt_result.get('success', False)
            }

        except Exception as e:
            logger.error(f"Unexpected error in capture_remaining_amount: {str(e)}")
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