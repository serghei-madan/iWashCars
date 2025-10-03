# Receipt Email System Documentation

## Overview
The iWashCars system automatically sends receipt emails after payment operations are completed. This includes both service completion receipts and refund receipts.

## Receipt Types

### 1. Service Completion Receipt
**Sent When:** Final payment is fully captured after service completion
**Trigger:** `StripePaymentService.capture_remaining_amount()` succeeds
**Template:** `main/templates/main/emails/service_completion_receipt.html`
**Subject:** `Service Completion Receipt - iWashCars #{booking_id}`

**Includes:**
- Service details (name, date, time, location)
- Payment breakdown (deposit + final payment = total)
- Transaction ID
- Customer information
- Completion timestamp

### 2. Refund Receipt
**Sent When:** Deposit is refunded to customer
**Trigger:** `StripePaymentService.refund_deposit()` succeeds
**Template:** `main/templates/main/emails/refund_receipt.html`
**Subject:** `Refund Receipt - iWashCars #{booking_id}`

**Includes:**
- Original booking details
- Refund amount breakdown
- Refund reason (from payment notes)
- Transaction ID
- Refund processing timeline information

## How It Works

### Service Completion Flow

```
1. Service is completed
   ↓
2. Admin/Driver captures remaining payment
   → stripe_utils.py:capture_remaining_amount()
   ↓
3. Stripe processes the capture
   ↓
4. Payment status updated to 'fully_captured'
   ↓
5. NotificationService.send_service_completion_receipt() called
   ↓
6. Receipt email sent via Mailgun
   ↓
7. Customer receives detailed receipt
```

### Refund Flow

```
1. Refund is initiated
   ↓
2. Admin processes refund
   → stripe_utils.py:refund_deposit()
   ↓
3. Stripe processes the refund
   ↓
4. Payment status updated to 'deposit_refunded'
   ↓
5. NotificationService.send_refund_receipt() called
   ↓
6. Refund receipt email sent via Mailgun
   ↓
7. Customer receives refund confirmation
```

## Code Integration

### Automatic Receipt Sending

Receipts are automatically sent by the `StripePaymentService` class after successful operations:

**In `stripe_utils.py:169-193` (capture_remaining_amount):**
```python
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
```

**In `stripe_utils.py:258-280` (refund_deposit):**
```python
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
```

### Manual Receipt Sending

You can also manually send receipts:

```python
from main.models import Payment
from main.notification_utils import NotificationService

# Get a payment
payment = Payment.objects.get(id=123)

# Send service completion receipt
result = NotificationService.send_service_completion_receipt(payment)
if result['success']:
    print("Receipt sent!")
else:
    print(f"Error: {result['error']}")

# Send refund receipt
result = NotificationService.send_refund_receipt(payment)
if result['success']:
    print("Refund receipt sent!")
```

## Payment Status Flow

```
pending
  ↓ (capture_deposit)
deposit_captured
  ↓ (capture_remaining_amount)
fully_captured  ← Service Completion Receipt Sent

  OR

deposit_captured
  ↓ (refund_deposit)
deposit_refunded  ← Refund Receipt Sent
```

## Testing

### Test Scripts Provided

**Test all receipt emails:**
```bash
python test_receipt_emails.py
```

This will send two test emails:
1. Service completion receipt (fully captured payment)
2. Refund receipt (refunded deposit)

### Testing in Django Shell

```python
python manage.py shell

from main.models import Payment
from main.notification_utils import NotificationService

# Find a completed payment
payment = Payment.objects.filter(status='fully_captured').first()

# Send receipt
result = NotificationService.send_service_completion_receipt(payment)
print(result)
```

## Email Templates

### Service Completion Receipt Template
**File:** `main/templates/main/emails/service_completion_receipt.html`

**Key Features:**
- ✅ Success badge and messaging
- Detailed service information
- Complete payment breakdown (deposit + final = total)
- Transaction ID for reference
- Timestamps for all payment events
- Professional styling with brand colors

### Refund Receipt Template
**File:** `main/templates/main/emails/refund_receipt.html`

**Key Features:**
- 💰 Refund notification badge
- Original booking details
- Refund amount breakdown
- Refund processing timeline info (5-10 business days)
- Reason for refund (if provided)
- Transaction reference

## Important Notes

### Receipt Delivery
- Receipts are sent asynchronously (won't block payment processing)
- If email fails, payment still completes successfully
- Failures are logged for admin review
- Users can request receipts to be resent manually

### Error Handling
- Receipt sending errors are caught and logged
- Payment operations succeed even if email fails
- Check logs for email delivery issues:
  ```bash
  # Look for:
  "Service completion receipt sent for payment #123"
  "Failed to send receipt: [error message]"
  ```

### Mailgun Integration
- All receipts use the Mailgun email backend
- HTML and plain text versions sent
- Templates render with Django template engine
- Proper error handling and logging

## Admin Actions

### To Capture Final Payment and Send Receipt

1. **Via Django Admin:**
   - Go to Payments in admin panel
   - Select payment with status "Deposit Captured"
   - Note the payment ID
   - Use Django shell or custom admin action

2. **Via Django Shell:**
   ```python
   from main.models import Payment
   from main.stripe_utils import StripePaymentService

   payment = Payment.objects.get(id=123)
   result = StripePaymentService.capture_remaining_amount(payment)
   print(result)  # Receipt sent automatically
   ```

### To Issue Refund and Send Receipt

```python
from main.models import Payment
from main.stripe_utils import StripePaymentService

payment = Payment.objects.get(id=123)
result = StripePaymentService.refund_deposit(
    payment,
    reason="Customer requested cancellation"
)
print(result)  # Refund receipt sent automatically
```

## Customization

### Modify Email Templates

Templates are in `main/templates/main/emails/`:
- `service_completion_receipt.html`
- `refund_receipt.html`

### Change Email Subject

Edit in `main/notification_utils.py`:

**Service completion (line 225):**
```python
subject=f'Service Completion Receipt - iWashCars #{booking.id}',
```

**Refund (line 258):**
```python
subject=f'Refund Receipt - iWashCars #{booking.id}',
```

### Disable Automatic Receipts

To disable automatic receipt sending, comment out the email sending code in `stripe_utils.py`:

```python
# # Send service completion receipt email
# try:
#     from .notification_utils import NotificationService
#     receipt_result = NotificationService.send_service_completion_receipt(payment)
# ...
```

## Troubleshooting

### Receipt not received?

1. **Check spam folder**
2. **Verify email address in booking**
3. **Check Django logs** for errors
4. **Verify Mailgun is configured** (check .env)
5. **Test Mailgun connection:**
   ```bash
   python test_email.py
   ```

### Wrong information in receipt?

1. **Verify Payment model data:**
   ```python
   payment = Payment.objects.get(id=123)
   print(f"Total: {payment.get_total_amount_dollars()}")
   print(f"Deposit: {payment.get_deposit_amount_dollars()}")
   print(f"Remaining: {payment.get_remaining_amount_dollars()}")
   ```

2. **Check booking information:**
   ```python
   booking = payment.booking
   print(f"Service: {booking.service.name}")
   print(f"Date: {booking.booking_date}")
   print(f"Email: {booking.email}")
   ```

### Resend a receipt manually?

```python
from main.models import Payment
from main.notification_utils import NotificationService

payment = Payment.objects.get(id=123)

# Resend service completion receipt
if payment.status == 'fully_captured':
    NotificationService.send_service_completion_receipt(payment)

# Resend refund receipt
if payment.status == 'deposit_refunded':
    NotificationService.send_refund_receipt(payment)
```

## Future Enhancements

Potential improvements:
- [ ] PDF receipt attachments
- [ ] Receipt archive in customer portal
- [ ] SMS receipt notifications (optional)
- [ ] Detailed service breakdown in receipt
- [ ] Before/after photos in receipt (if available)
- [ ] QR code for receipt verification
- [ ] Multi-language support

## Support

For issues or questions about receipt emails:
1. Check logs in Django admin
2. Run test scripts to verify functionality
3. Review Mailgun dashboard for delivery status
4. Check this documentation for common issues
