## Setup

1. Install dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:

## Running the Application

Run the server:
```bash
source venv/bin/activate && python manage.py runserver
```

Run the CSS build:
```bash
npm run build-css
```

## Email Notifications

The application uses Mailgun for sending transactional emails:
- **Booking confirmations** - Sent after successful deposit payment
- **30-minute reminders** - Sent via scheduled task before appointments
- **Driver notifications** - Sent for new bookings
- **Service completion receipts** - Sent after final payment is captured
- **Refund receipts** - Sent when deposits are refunded
- **Cancellation notifications** - Sent when bookings are cancelled

Test email functionality:
```bash
python test_email.py              # Simple test email
python test_booking_email.py      # Booking confirmation
python test_reminder_email.py     # Appointment reminder
python test_receipt_emails.py     # Service completion & refund receipts
python test_cancellation.py       # Cancellation notification
```

See [RECEIPT_EMAIL_DOCUMENTATION.md](RECEIPT_EMAIL_DOCUMENTATION.md) for detailed receipt system information.

## Booking Cancellation

Cancel bookings directly from the admin panel:
- One-click cancellation with automatic payment handling
- Calendar slots automatically freed for rebooking
- Email notifications sent to customers
- Full audit trail with cancellation reasons

See [CANCELLATION_GUIDE.md](CANCELLATION_GUIDE.md) for complete cancellation documentation.

