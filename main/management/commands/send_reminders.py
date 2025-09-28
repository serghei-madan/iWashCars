from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from main.models import Booking
from main.notification_utils import NotificationService


class Command(BaseCommand):
    help = 'Send SMS reminders for bookings starting in 30 minutes'

    def handle(self, *args, **options):
        now = timezone.now()
        reminder_time = now + timedelta(minutes=30)

        bookings = Booking.objects.filter(
            is_confirmed=True,
            reminder_sent=False,
            booking_date=reminder_time.date(),
            booking_time__gte=reminder_time.time(),
            booking_time__lte=(reminder_time + timedelta(minutes=5)).time()
        )

        sent_count = 0
        failed_count = 0

        for booking in bookings:
            booking_datetime = timezone.make_aware(
                timezone.datetime.combine(booking.booking_date, booking.booking_time)
            )

            time_until_booking = (booking_datetime - now).total_seconds() / 60

            if 25 <= time_until_booking <= 35:
                result = NotificationService.send_reminder_sms(booking)

                if result['success']:
                    booking.reminder_sent = True
                    booking.reminder_sent_at = now
                    booking.save()
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Reminder sent for booking #{booking.id} - {booking.first_name} {booking.last_name}'
                        )
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Failed to send reminder for booking #{booking.id}: {result.get("error")}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {sent_count} reminders sent, {failed_count} failed'
            )
        )