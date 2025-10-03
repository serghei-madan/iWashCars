"""
Quick test script to verify Mailgun email integration.
Run this to test if emails are being sent correctly.
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iwashcars.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_mailgun():
    """Send a test email via Mailgun"""
    print("Testing Mailgun email integration...")
    print(f"Using backend: {settings.EMAIL_BACKEND}")
    print(f"Mailgun domain: {settings.MAILGUN_SANDBOX_DOMAIN}")
    print(f"From email: {settings.DEFAULT_FROM_EMAIL}")

    try:
        # Send a simple test email
        result = send_mail(
            subject='iWashCars - Test Email',
            message='This is a test email from iWashCars booking system.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['madan.serghei@yahoo.com'],  # Your email from the Mailgun example
            html_message='<h1>Test Email</h1><p>This is a test email from iWashCars booking system.</p>',
            fail_silently=False,
        )

        if result == 1:
            print("✅ Email sent successfully via Mailgun!")
            print("Check your inbox at madan.serghei@yahoo.com (and spam folder)")
        else:
            print("❌ Email failed to send")

    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_mailgun()
