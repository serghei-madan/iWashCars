# Quick Payment & Receipt Guide

## Payment Flow Overview

### 1. Customer Books Service
- Customer selects service and fills booking form
- Stripe PaymentIntent created for full amount
- Only **deposit ($25)** is captured initially
- Remaining amount is **authorized** (held on card)
- **Email sent:** Booking confirmation

### 2. Service is Performed
- Driver arrives and completes service
- Full service amount remains authorized on customer's card

### 3. Capture Final Payment (After Service)
- Admin/Driver captures remaining amount
- Customer is charged the remaining balance
- **Email sent:** Service completion receipt

### Alternative: Refund Scenario
- If service cannot be completed or customer cancels
- Admin can refund the deposit
- Remaining authorization is released
- **Email sent:** Refund receipt

## How to Capture Final Payment

### Method 1: Django Shell (Recommended)

```bash
python manage.py shell
```

```python
from main.models import Payment
from main.stripe_utils import StripePaymentService

# Find the payment (by booking ID or payment ID)
payment = Payment.objects.get(booking_id=123)  # or get(id=456)

# Check payment status
print(f"Status: {payment.status}")
print(f"Can capture? {payment.can_capture_remaining()}")

# Capture remaining amount
result = StripePaymentService.capture_remaining_amount(payment)
print(result)

# Receipt is automatically sent!
```

### Method 2: Direct Code

Create a view or management command:

```python
from main.stripe_utils import StripePaymentService
from main.models import Payment

def complete_service_payment(booking_id):
    """Capture final payment after service completion"""
    payment = Payment.objects.get(booking__id=booking_id)

    if payment.status != 'deposit_captured':
        return {'error': 'Payment not in correct status'}

    result = StripePaymentService.capture_remaining_amount(payment)
    # Receipt email sent automatically
    return result
```

## How to Issue Refund

```python
from main.models import Payment
from main.stripe_utils import StripePaymentService

# Get payment
payment = Payment.objects.get(booking_id=123)

# Check if refundable
print(f"Can refund? {payment.can_refund_deposit()}")

# Refund with reason
result = StripePaymentService.refund_deposit(
    payment,
    reason="Customer requested cancellation"
)
print(result)

# Refund receipt email sent automatically
```

## Payment Status Reference

| Status | Description | Actions Available |
|--------|-------------|-------------------|
| `pending` | Payment created, not captured | Wait for Stripe confirmation |
| `deposit_captured` | Deposit captured, service pending | ✅ Capture remaining<br>✅ Refund deposit<br>✅ Cancel authorization |
| `fully_captured` | Service complete, full payment | ✅ Refund deposit (partial) |
| `deposit_refunded` | Deposit refunded to customer | None |
| `cancelled` | Authorization cancelled | None |
| `failed` | Payment failed | Retry or create new |

## Email Receipts

### Automatic Sending
Receipts are **automatically sent** when:
- Final payment is captured → Service completion receipt
- Deposit is refunded → Refund receipt

### Manual Sending
If you need to resend a receipt:

```python
from main.models import Payment
from main.notification_utils import NotificationService

payment = Payment.objects.get(id=123)

# Resend service completion receipt
NotificationService.send_service_completion_receipt(payment)

# Resend refund receipt
NotificationService.send_refund_receipt(payment)
```

## Common Scenarios

### Scenario 1: Normal Service Completion
```
1. Customer books → Deposit captured
2. Service performed
3. Admin captures final payment
   → Customer charged $50 (if $75 total)
   → Receipt email sent
4. Done!
```

### Scenario 2: Service Cancellation Before Completion
```
1. Customer books → Deposit captured
2. Customer cancels OR service cannot be performed
3. Admin refunds deposit
   → Customer receives $25 back
   → Remaining $50 authorization released
   → Refund receipt email sent
4. Done!
```

### Scenario 3: Customer No-Show
```
1. Customer books → Deposit captured
2. Customer doesn't show up
3. Admin keeps deposit (no action needed)
4. Remaining authorization released automatically after 7 days
5. Customer keeps charge for $25 deposit
```

## Quick Reference Commands

### Check Payment Status
```python
payment = Payment.objects.get(booking_id=123)
print(f"Status: {payment.get_status_display()}")
print(f"Total: ${payment.get_total_amount_dollars():.2f}")
print(f"Deposit: ${payment.get_deposit_amount_dollars():.2f}")
print(f"Remaining: ${payment.get_remaining_amount_dollars():.2f}")
```

### List Payments Ready for Capture
```python
from main.models import Payment

ready_to_capture = Payment.objects.filter(status='deposit_captured')
for payment in ready_to_capture:
    booking = payment.booking
    print(f"Booking #{booking.id}: {booking.first_name} {booking.last_name}")
    print(f"  Date: {booking.booking_date} at {booking.booking_time}")
    print(f"  To capture: ${payment.get_remaining_amount_dollars():.2f}")
    print()
```

### Get Payment Details from Stripe
```python
from main.stripe_utils import StripePaymentService

payment = Payment.objects.get(id=123)
status = StripePaymentService.get_payment_status(payment)
print(status)
```

## Troubleshooting

### "Cannot capture remaining amount. Payment status must be deposit_captured."
**Solution:** Check payment status. It must be `deposit_captured` to capture remaining amount.

### "This PaymentIntent's amount_capturable is already 0."
**Solution:** Payment already fully captured. Check `payment.status` - it should be `fully_captured`.

### Receipt email not sent
**Solution:**
1. Check Django logs for errors
2. Verify Mailgun configuration
3. Manually resend receipt (see above)

### Authorization expired
**Solution:** Stripe authorizations expire after ~7 days. You cannot capture after expiration. Need to create new payment.

## Important Notes

1. **Always capture within 7 days** - Stripe authorizations expire
2. **Receipts send automatically** - No manual action needed
3. **Check email spam folder** - Receipts might go to spam initially
4. **Keep deposit for no-shows** - Don't refund if customer doesn't show up
5. **Log all actions** - All payment operations are logged in Django logs

## Need Help?

- See `RECEIPT_EMAIL_DOCUMENTATION.md` for detailed receipt information
- Check `main/stripe_utils.py` for all payment methods
- Review `main/models.py` Payment model for status definitions
- Test with `test_receipt_emails.py`
