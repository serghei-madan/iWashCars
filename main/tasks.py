from django.utils import timezone
from datetime import timedelta
from main.models import Booking
from main.notification_utils import NotificationService
import logging

logger = logging.getLogger(__name__)


def send_booking_reminders():
    now = timezone.now()
    reminder_window_start = now + timedelta(minutes=25)
    reminder_window_end = now + timedelta(minutes=35)

    bookings = Booking.objects.filter(
        is_confirmed=True,
        reminder_sent=False,
        booking_date=reminder_window_start.date()
    )

    sent_count = 0
    failed_count = 0

    for booking in bookings:
        booking_datetime = timezone.make_aware(
            timezone.datetime.combine(booking.booking_date, booking.booking_time)
        )

        if reminder_window_start <= booking_datetime <= reminder_window_end:
            result = NotificationService.send_reminder_email(booking)

            if result['success']:
                booking.reminder_sent = True
                booking.reminder_sent_at = now
                booking.save()
                sent_count += 1
                logger.info(
                    f'Reminder sent for booking #{booking.id} - {booking.first_name} {booking.last_name}'
                )
            else:
                failed_count += 1
                logger.error(
                    f'Failed to send reminder for booking #{booking.id}: {result.get("error")}'
                )

    logger.info(f'Reminder task completed: {sent_count} sent, {failed_count} failed')
    return {'sent': sent_count, 'failed': failed_count}