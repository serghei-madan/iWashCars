from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


class NotificationService:

    @staticmethod
    def send_customer_booking_confirmation(booking):
        try:
            remaining_balance = float(booking.total_price) - 25.00

            context = {
                'booking': booking,
                'remaining_balance': f"{remaining_balance:.2f}"
            }

            html_message = render_to_string(
                'main/emails/customer_booking_confirmation.html',
                context
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject=f'Booking Confirmed - {booking.service.name}',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.email],
                html_message=html_message,
                fail_silently=False,
            )

            return {'success': True, 'message': 'Customer confirmation email sent'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_driver_booking_notification(booking):
        try:
            remaining_balance = float(booking.total_price) - 25.00

            context = {
                'booking': booking,
                'remaining_balance': f"{remaining_balance:.2f}"
            }

            html_message = render_to_string(
                'main/emails/driver_booking_notification.html',
                context
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject=f'New Booking Alert - {booking.booking_date} at {booking.booking_time}',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DRIVER_NOTIFICATION_EMAIL],
                html_message=html_message,
                fail_silently=False,
            )

            return {'success': True, 'message': 'Driver notification email sent'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_customer_sms(booking):
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            return {'success': False, 'error': 'Twilio credentials not configured'}

        if not booking.phone:
            return {'success': False, 'error': 'Customer phone number not provided'}

        try:
            from twilio.rest import Client

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

            message_body = (
                f"iWashCars Booking Confirmed!\n"
                f"Service: {booking.service.name}\n"
                f"Date: {booking.booking_date.strftime('%m/%d/%Y')}\n"
                f"Time: {booking.booking_time.strftime('%I:%M %p')}\n"
                f"Location: {booking.address}, {booking.city}\n"
                f"See your email for full details."
            )

            message = client.messages.create(
                body=message_body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=booking.phone
            )

            return {'success': True, 'message': 'Customer SMS sent', 'sid': message.sid}

        except ImportError:
            return {'success': False, 'error': 'Twilio library not installed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_driver_sms(booking):
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            return {'success': False, 'error': 'Twilio credentials not configured'}

        if not settings.DRIVER_NOTIFICATION_PHONE:
            return {'success': False, 'error': 'Driver phone number not configured'}

        try:
            from twilio.rest import Client

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

            remaining_balance = float(booking.total_price) - 25.00

            message_body = (
                f"NEW BOOKING ALERT!\n"
                f"ID: #{booking.id}\n"
                f"Service: {booking.service.name}\n"
                f"Date: {booking.booking_date.strftime('%m/%d/%Y')}\n"
                f"Time: {booking.booking_time.strftime('%I:%M %p')}\n"
                f"Customer: {booking.first_name} {booking.last_name}\n"
                f"Location: {booking.address}, {booking.city}\n"
                f"Balance to collect: ${remaining_balance:.2f}\n"
                f"Check email for full details."
            )

            message = client.messages.create(
                body=message_body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=settings.DRIVER_NOTIFICATION_PHONE
            )

            return {'success': True, 'message': 'Driver SMS sent', 'sid': message.sid}

        except ImportError:
            return {'success': False, 'error': 'Twilio library not installed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_reminder_sms(booking):
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            return {'success': False, 'error': 'Twilio credentials not configured'}

        if not booking.phone:
            return {'success': False, 'error': 'Customer phone number not provided'}

        try:
            from twilio.rest import Client

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

            message_body = (
                f"Reminder: Your iWashCars appointment is in 30 minutes!\n"
                f"Service: {booking.service.name}\n"
                f"Time: {booking.booking_time.strftime('%I:%M %p')}\n"
                f"Location: {booking.address}, {booking.city}\n"
                f"See you soon!"
            )

            message = client.messages.create(
                body=message_body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=booking.phone
            )

            return {'success': True, 'message': 'Reminder SMS sent', 'sid': message.sid}

        except ImportError:
            return {'success': False, 'error': 'Twilio library not installed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_reminder_email(booking):
        try:
            context = {
                'booking': booking,
            }

            html_message = render_to_string(
                'main/emails/customer_booking_reminder.html',
                context
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject=f'Reminder: Your iWashCars appointment is in 30 minutes!',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.email],
                html_message=html_message,
                fail_silently=False,
            )

            return {'success': True, 'message': 'Reminder email sent'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_service_completion_receipt(payment):
        """
        Send receipt email after service completion and full payment capture
        """
        try:
            booking = payment.booking

            context = {
                'booking': booking,
                'payment': payment,
            }

            html_message = render_to_string(
                'main/emails/service_completion_receipt.html',
                context
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject=f'Service Completion Receipt - iWashCars #{booking.id}',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.email],
                html_message=html_message,
                fail_silently=False,
            )

            return {'success': True, 'message': 'Service completion receipt sent'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_refund_receipt(payment):
        """
        Send receipt email after refund is processed
        """
        try:
            booking = payment.booking

            context = {
                'booking': booking,
                'payment': payment,
            }

            html_message = render_to_string(
                'main/emails/refund_receipt.html',
                context
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject=f'Refund Receipt - iWashCars #{booking.id}',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.email],
                html_message=html_message,
                fail_silently=False,
            )

            return {'success': True, 'message': 'Refund receipt sent'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_cancellation_notification(booking):
        """
        Send cancellation notification email to customer
        """
        try:
            # Check if there's a payment and its status
            has_payment = False
            payment_refunded = False
            payment_cancelled = False

            try:
                payment = booking.payment
                has_payment = True
                payment_refunded = payment.status == 'deposit_refunded'
                payment_cancelled = payment.status == 'cancelled'
            except:
                pass

            context = {
                'booking': booking,
                'has_payment': has_payment,
                'payment_refunded': payment_refunded,
                'payment_cancelled': payment_cancelled,
            }

            html_message = render_to_string(
                'main/emails/booking_cancellation.html',
                context
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject=f'Booking Cancellation - iWashCars #{booking.id}',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.email],
                html_message=html_message,
                fail_silently=False,
            )

            return {'success': True, 'message': 'Cancellation notification sent'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_all_booking_notifications(booking):
        results = {
            'customer_email': NotificationService.send_customer_booking_confirmation(booking),
            'driver_email': NotificationService.send_driver_booking_notification(booking),
        }

        return results