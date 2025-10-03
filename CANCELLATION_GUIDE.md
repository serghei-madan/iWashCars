# Booking Cancellation System Guide

## Overview

The iWashCars booking system now includes comprehensive cancellation functionality that:
- ✅ Cancels bookings from the admin panel
- ✅ Automatically handles payment refunds/releases
- ✅ Clears calendar slots for rebooking
- ✅ Sends cancellation notifications to customers
- ✅ Tracks cancellation history and reasons

## Booking Status System

### Status Options

| Status | Description | Calendar Visibility |
|--------|-------------|---------------------|
| `pending` | Initial booking, payment not confirmed | Blocks calendar |
| `confirmed` | Deposit paid, booking confirmed | Blocks calendar |
| `completed` | Service finished, full payment captured | Blocks calendar |
| `cancelled` | Booking cancelled | **Frees up calendar slot** ✅ |
| `no_show` | Customer didn't show up | Blocks calendar |

### Status Flow

```
pending → confirmed → completed ✅
   ↓          ↓
cancelled  cancelled
```

## How to Cancel a Booking

### Method 1: From Booking Admin Panel

1. Go to **Django Admin** → **Bookings**
2. Select the booking(s) you want to cancel
3. Choose **Actions** → **"Cancel selected bookings (refund/release payment)"**
4. Click **"Go"**

**What happens automatically:**
- ✅ Booking status set to `cancelled`
- ✅ Payment authorization cancelled OR deposit refunded (depending on payment status)
- ✅ Cancellation timestamp recorded
- ✅ Email notification sent to customer
- ✅ Calendar slot freed up for rebooking

### Method 2: From Payment Admin Panel

1. Go to **Django Admin** → **Payments**
2. Select the payment(s) associated with bookings to cancel
3. Choose **Actions** → **"Cancel authorization (release held funds & cancel booking)"**
4. Click **"Go"**

**What happens automatically:**
- ✅ Payment authorization cancelled
- ✅ Booking marked as cancelled
- ✅ Email notification sent
- ✅ Calendar slot freed

### Method 3: Via Django Shell

```python
python manage.py shell
```

```python
from main.models import Booking, Payment
from main.stripe_utils import StripePaymentService
from main.notification_utils import NotificationService
from django.utils import timezone

# Get the booking
booking = Booking.objects.get(id=123)

# Cancel payment first (if exists)
try:
    payment = booking.payment

    # Option A: Cancel authorization (releases held funds, no refund needed)
    if payment.can_cancel_authorization():
        result = StripePaymentService.cancel_authorization(payment)
        print(result)

    # Option B: Refund deposit (if already captured)
    elif payment.can_refund_deposit():
        result = StripePaymentService.refund_deposit(
            payment,
            reason="Customer requested cancellation"
        )
        print(result)

except Payment.DoesNotExist:
    print("No payment to cancel")

# Update booking status
booking.status = 'cancelled'
booking.cancelled_at = timezone.now()
booking.cancellation_reason = 'Your reason here'
booking.save()

# Send cancellation notification
result = NotificationService.send_cancellation_notification(booking)
print(result)
```

## Payment Handling During Cancellation

### Scenario 1: Authorization Can Be Cancelled (Recommended)

**When:** Payment is in `deposit_captured` status
**Action:** Cancel authorization
**Result:**
- Deposit ($25) is refunded
- Remaining authorization ($50) is released
- Customer pays $0

```python
StripePaymentService.cancel_authorization(payment)
```

### Scenario 2: Deposit Must Be Refunded

**When:** Payment is `fully_captured` or authorization cannot be cancelled
**Action:** Refund deposit
**Result:**
- Deposit ($25) is refunded
- Customer receives $25 back

```python
StripePaymentService.refund_deposit(payment, reason="Cancellation")
```

### Scenario 3: No Payment Exists

**When:** Booking created but payment not processed
**Action:** Just update booking status
**Result:**
- Booking cancelled
- No payment processing needed

## Calendar Slot Clearing

### How It Works

The booking calendar automatically excludes cancelled bookings:

**In `main/views.py:30-34`:**
```python
existing_bookings = Booking.objects.select_related('service').exclude(
    status='cancelled'
).values(...)
```

**What this means:**
- ✅ Cancelled bookings don't block calendar slots
- ✅ Other customers can immediately book the freed time
- ✅ No manual calendar management needed

### Testing Calendar Clearing

1. Create a booking for October 15, 2025 at 2:00 PM
2. Go to booking page - slot should be unavailable
3. Cancel the booking via admin
4. Refresh booking page - slot should now be available ✅

## Email Notifications

### Cancellation Email

**Template:** `main/templates/main/emails/booking_cancellation.html`

**Includes:**
- ❌ Clear cancellation notice
- 📅 Original booking details (date, time, service)
- 💰 Refund information (if applicable)
- 📝 Cancellation reason
- 🕐 Cancellation timestamp

**Sent automatically when:**
- Admin cancels booking via "Cancel selected bookings" action
- Admin cancels payment authorization
- Manual cancellation via Django shell (if you call the notification method)

### Customizing the Email

Edit the template at:
```
main/templates/main/emails/booking_cancellation.html
```

Change the subject in `main/notification_utils.py:304`:
```python
subject=f'Booking Cancellation - iWashCars #{booking.id}',
```

## Admin Panel Features

### Booking List Display

The booking admin now shows:
- **Status Badge**: Color-coded status (pending/confirmed/completed/cancelled/no_show)
- **Payment Status**: Current payment state
- **Filter by Status**: Quickly find cancelled bookings
- **Search**: Search by customer name, email, phone

### Available Actions

1. **Cancel selected bookings** - Full cancellation with payment handling
2. **Mark as completed** - Mark service as finished
3. **Mark as no-show** - Customer didn't show up (keeps deposit)

### Booking Detail View

Organized fieldsets:
- Customer Information
- Service Details
- Location
- **Status** (includes cancellation reason and timestamp)
- Metadata (creation, updates, reminders)

## Common Scenarios

### Scenario 1: Customer Calls to Cancel Same Day

**Steps:**
1. Find booking in admin by customer name/email
2. Select booking → Actions → "Cancel selected bookings"
3. System automatically:
   - Cancels payment authorization
   - Sends cancellation email
   - Frees calendar slot

**Result:** Customer receives email with refund details

### Scenario 2: Service Cannot Be Performed (Weather, etc.)

**Steps:**
1. Select all affected bookings
2. Bulk cancel via admin action
3. Add custom cancellation reason in booking details if needed

**Result:** All customers notified, all slots freed

### Scenario 3: Customer No-Show

**Steps:**
1. Select booking → Actions → "Mark as no-show"
2. Booking stays in system as no-show
3. Deposit is kept (no refund)

**Result:** Slot remains blocked, deposit retained

### Scenario 4: Cancel Before Payment

**Steps:**
1. Find pending booking (no payment yet)
2. Cancel booking
3. No payment processing needed

**Result:** Simple cancellation, email sent

## Reporting & Tracking

### View Cancelled Bookings

**In Admin:**
- Go to Bookings
- Filter by Status → Cancelled
- See all cancellations with reasons and timestamps

**Via Django Shell:**
```python
from main.models import Booking

# Get all cancelled bookings
cancelled = Booking.objects.filter(status='cancelled')

for booking in cancelled:
    print(f"{booking.id}: {booking} - Cancelled on {booking.cancelled_at}")
    print(f"  Reason: {booking.cancellation_reason}")
    print()
```

### Cancellation Metrics

```python
from main.models import Booking
from django.utils import timezone
from datetime import timedelta

# Cancellations this month
this_month = timezone.now().replace(day=1)
cancelled_this_month = Booking.objects.filter(
    status='cancelled',
    cancelled_at__gte=this_month
).count()

print(f"Cancellations this month: {cancelled_this_month}")

# Cancellation rate
total_bookings = Booking.objects.filter(created_at__gte=this_month).count()
rate = (cancelled_this_month / total_bookings * 100) if total_bookings > 0 else 0
print(f"Cancellation rate: {rate:.1f}%")
```

## Testing

### Test Cancellation Email

```bash
python test_cancellation.py
```

This sends a test cancellation email with:
- Cancelled booking details
- Refund information
- Proper formatting

### Manual Test Flow

1. **Create Test Booking**
   ```python
   # Via Django shell or admin panel
   ```

2. **Verify Calendar Blocked**
   - Go to booking page
   - Selected date/time should be unavailable

3. **Cancel Booking**
   - Use admin action or shell command

4. **Verify Calendar Freed**
   - Refresh booking page
   - Time slot should now be available ✅

5. **Check Email**
   - Verify cancellation email received
   - Confirm refund details correct

## Troubleshooting

### Calendar Slot Not Freeing After Cancellation

**Check:**
1. Booking status is actually `cancelled` (not just payment cancelled)
2. Clear browser cache and refresh
3. Check database:
   ```python
   booking = Booking.objects.get(id=123)
   print(booking.status)  # Should be 'cancelled'
   ```

### Cancellation Email Not Sent

**Check:**
1. Mailgun configuration in .env
2. Django logs for errors
3. Try manual send:
   ```python
   NotificationService.send_cancellation_notification(booking)
   ```

### Payment Refund Failed

**Check:**
1. Payment status allows refund
2. Stripe dashboard for errors
3. Payment hasn't already been refunded
4. Try cancellation instead of refund:
   ```python
   StripePaymentService.cancel_authorization(payment)
   ```

### Booking Won't Cancel

**Error:** "Cannot cancel authorization in current status"

**Solution:**
- Check payment status
- If `fully_captured`, use refund instead
- If `pending`, just update booking status
- If `deposit_refunded`, already processed

## Best Practices

### 1. Always Use Admin Actions

✅ **Do:** Use "Cancel selected bookings" action
❌ **Don't:** Manually update status without handling payment

### 2. Provide Cancellation Reasons

✅ **Do:** Add clear reason in booking admin
❌ **Don't:** Leave blank - helps with customer service

### 3. Cancel ASAP

✅ **Do:** Cancel as soon as you know service can't happen
❌ **Don't:** Wait - customer needs time to rebook

### 4. Check Payment Status First

✅ **Do:** Review payment before cancelling
❌ **Don't:** Assume refund will work

### 5. Monitor Cancellation Rates

✅ **Do:** Track monthly cancellations
❌ **Don't:** Ignore patterns

## Future Enhancements

Potential improvements:
- [ ] Customer self-service cancellation portal
- [ ] Automated cancellation emails 24h before for weather
- [ ] Cancellation fee for last-minute cancellations
- [ ] Rescheduling instead of cancellation
- [ ] SMS cancellation notifications
- [ ] Cancellation analytics dashboard

## Summary

The cancellation system provides:

✅ **One-click cancellation** from admin panel
✅ **Automatic payment handling** (refund or release)
✅ **Immediate calendar slot freeing**
✅ **Professional email notifications**
✅ **Complete audit trail** (timestamps & reasons)
✅ **Flexible status tracking**

**Key Benefits:**
- Saves admin time
- Improves customer experience
- Maximizes rebooking opportunities
- Maintains accurate records

## Support

For issues or questions:
1. Check Django logs
2. Review this documentation
3. Test with `test_cancellation.py`
4. Check Stripe dashboard for payment issues
5. Review Mailgun logs for email issues
