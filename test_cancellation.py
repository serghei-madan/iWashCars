"""
Test booking cancellation functionality.
Tests the complete cancellation flow including email notification.
"""
import os
import sys
import django
from datetime import date, time
from decimal import Decimal

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iwashcars.settings')
django.setup()

from django.utils import timezone
from main.models import Service, Booking, Payment
from main.notification_utils import NotificationService

def test_cancellation_notification():
    """Test the cancellation notification email"""
    print("=" * 60)
    print("Testing Booking Cancellation Notification")
    print("=" * 60)

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
        status='cancelled',
        cancelled_at=timezone.now(),
        cancellation_reason='Cancelled by admin for testing'
    )
    test_booking.id = 999  # Mock ID
    test_booking.booking_end_time = service.get_end_time(test_booking.booking_time)

    # Create mock payment (refunded)
    test_payment = Payment(
        booking=test_booking,
        stripe_payment_intent_id='pi_test_1234567890abcdef',
        stripe_customer_id='cus_test_1234567890',
        deposit_amount=2500,  # $25.00
        total_amount=7500,    # $75.00
        remaining_amount=5000, # $50.00
        status='deposit_refunded',
        deposit_captured_at=timezone.now() - timezone.timedelta(days=1),
        refunded_at=timezone.now(),
    )
    test_payment.id = 999  # Mock ID

    # Manually set the payment relationship (since we're not saving to DB)
    test_booking._payment = test_payment

    # Override the payment property
    original_payment = Booking.payment
    Booking.payment = property(lambda self: getattr(self, '_payment', None))

    print(f"\nCancelled Booking Details:")
    print(f"  Customer: {test_booking.first_name} {test_booking.last_name}")
    print(f"  Service: {test_booking.service.name}")
    print(f"  Original Date: {test_booking.booking_date}")
    print(f"  Original Time: {test_booking.booking_time}")
    print(f"  Status: {test_booking.get_status_display()}")
    print(f"  Cancelled: {test_booking.cancelled_at}")
    print(f"  Reason: {test_booking.cancellation_reason}")
    print(f"  Email: {test_booking.email}")
    print(f"  Payment Status: {test_payment.get_status_display()}")

    # Send cancellation notification
    print("\nSending cancellation notification...")
    result = NotificationService.send_cancellation_notification(test_booking)

    # Restore original property
    Booking.payment = original_payment

    if result['success']:
        print("✅ Cancellation notification sent successfully!")
        print(f"   Message: {result['message']}")
        print("\nCheck your inbox at madan.serghei@yahoo.com")
        print("(Also check spam folder)")
    else:
        print(f"❌ Failed to send notification: {result.get('error')}")

    print()


def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "CANCELLATION TESTING SUITE" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    test_cancellation_notification()

    print("=" * 60)
    print("Testing Complete!")
    print("=" * 60)
    print("\nYou should have received:")
    print("  • Booking Cancellation Email")
    print("  • With refund information included")
    print()


if __name__ == '__main__':
    main()
