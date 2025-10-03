"""
Test service completion and refund receipt emails.
This simulates sending receipts after payment capture or refund.
"""
import os
import sys
import django
from datetime import date, time, datetime
from decimal import Decimal

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iwashcars.settings')
django.setup()

from django.utils import timezone
from main.models import Service, Booking, Payment
from main.notification_utils import NotificationService

def create_test_booking_and_payment():
    """Create test booking and payment objects for testing"""
    # Get or create a test service
    service, created = Service.objects.get_or_create(
        name='Premium Wash',
        defaults={
            'tier': 'premium',
            'description': 'Premium car wash service',
            'price': Decimal('75.00'),
            'duration_minutes': 90,
            'is_active': True,
        }
    )

    # Create a test booking
    test_booking = Booking(
        first_name='Serghei',
        last_name='Madan',
        email='madan.serghei@yahoo.com',
        phone='+14155552671',
        service=service,
        booking_date=date(2025, 10, 15),
        booking_time=time(14, 0),
        address='123 Test Street',
        city='San Francisco',
        zip_code='94102',
        total_price=Decimal('75.00'),
        is_confirmed=True,
    )
    test_booking.id = 999  # Mock ID
    test_booking.booking_end_time = service.get_end_time(test_booking.booking_time)

    # Create a test payment
    test_payment = Payment(
        booking=test_booking,
        stripe_payment_intent_id='pi_test_1234567890abcdef',
        stripe_customer_id='cus_test_1234567890',
        deposit_amount=2500,  # $25.00
        total_amount=7500,    # $75.00
        remaining_amount=5000, # $50.00
        status='fully_captured',
        deposit_captured_at=timezone.now() - timezone.timedelta(days=1),
        fully_captured_at=timezone.now(),
    )
    test_payment.id = 999  # Mock ID

    return test_booking, test_payment


def test_service_completion_receipt():
    """Test the service completion receipt email"""
    print("=" * 60)
    print("Testing Service Completion Receipt Email")
    print("=" * 60)

    test_booking, test_payment = create_test_booking_and_payment()

    print(f"\nBooking Details:")
    print(f"  Customer: {test_booking.first_name} {test_booking.last_name}")
    print(f"  Service: {test_booking.service.name}")
    print(f"  Date: {test_booking.booking_date}")
    print(f"  Email: {test_booking.email}")

    print(f"\nPayment Details:")
    print(f"  Total Amount: ${test_payment.get_total_amount_dollars():.2f}")
    print(f"  Deposit: ${test_payment.get_deposit_amount_dollars():.2f}")
    print(f"  Final Payment: ${test_payment.get_remaining_amount_dollars():.2f}")
    print(f"  Status: {test_payment.status}")
    print(f"  Completed: {test_payment.fully_captured_at}")

    # Send receipt
    print("\nSending service completion receipt...")
    result = NotificationService.send_service_completion_receipt(test_payment)

    if result['success']:
        print("✅ Service completion receipt sent successfully!")
        print(f"   Message: {result['message']}")
    else:
        print(f"❌ Failed to send receipt: {result.get('error')}")

    print()


def test_refund_receipt():
    """Test the refund receipt email"""
    print("=" * 60)
    print("Testing Refund Receipt Email")
    print("=" * 60)

    test_booking, test_payment = create_test_booking_and_payment()

    # Modify payment to be refunded
    test_payment.status = 'deposit_refunded'
    test_payment.refunded_at = timezone.now()
    test_payment.notes = 'Customer requested cancellation'

    print(f"\nBooking Details:")
    print(f"  Customer: {test_booking.first_name} {test_booking.last_name}")
    print(f"  Service: {test_booking.service.name}")
    print(f"  Date: {test_booking.booking_date}")
    print(f"  Email: {test_booking.email}")

    print(f"\nRefund Details:")
    print(f"  Original Amount: ${test_payment.get_total_amount_dollars():.2f}")
    print(f"  Refund Amount: ${test_payment.get_deposit_amount_dollars():.2f}")
    print(f"  Status: {test_payment.status}")
    print(f"  Refunded: {test_payment.refunded_at}")
    print(f"  Reason: {test_payment.notes}")

    # Send receipt
    print("\nSending refund receipt...")
    result = NotificationService.send_refund_receipt(test_payment)

    if result['success']:
        print("✅ Refund receipt sent successfully!")
        print(f"   Message: {result['message']}")
    else:
        print(f"❌ Failed to send receipt: {result.get('error')}")

    print()


def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "RECEIPT EMAIL TESTING SUITE" + " " * 19 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    # Test service completion receipt
    test_service_completion_receipt()

    # Test refund receipt
    test_refund_receipt()

    print("=" * 60)
    print("Testing Complete!")
    print("=" * 60)
    print("\nCheck your inbox at madan.serghei@yahoo.com")
    print("(Also check spam folder)")
    print("\nYou should have received 2 emails:")
    print("  1. Service Completion Receipt")
    print("  2. Refund Receipt")
    print()


if __name__ == '__main__':
    main()
