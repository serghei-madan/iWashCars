"""
Test booking reminder email.
This simulates the 30-minute reminder that gets sent before appointments.
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

from main.models import Service, Booking
from main.notification_utils import NotificationService

def test_reminder_email():
    """Test the booking reminder email"""
    print("Testing booking reminder email...")

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

    # Don't save to database, just use for email testing
    test_booking.id = 999  # Mock ID
    test_booking.booking_end_time = service.get_end_time(test_booking.booking_time)

    print(f"\nTest Reminder Details:")
    print(f"  Customer: {test_booking.first_name} {test_booking.last_name}")
    print(f"  Service: {test_booking.service.name}")
    print(f"  Date: {test_booking.booking_date}")
    print(f"  Time: {test_booking.booking_time}")
    print(f"  Email: {test_booking.email}\n")

    # Send reminder email
    print("Sending 30-minute reminder email...")
    result = NotificationService.send_reminder_email(test_booking)

    if result['success']:
        print("✅ Reminder email sent successfully!")
        print(f"   Message: {result['message']}")
        print("\nCheck your inbox at madan.serghei@yahoo.com")
        print("(Also check spam folder)")
    else:
        print(f"❌ Failed to send email: {result.get('error')}")

if __name__ == '__main__':
    test_reminder_email()
