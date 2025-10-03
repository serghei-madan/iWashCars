import requests
import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

logger = logging.getLogger(__name__)


class MailgunEmailBackend(BaseEmailBackend):
    """
    Custom email backend that uses Mailgun API to send emails.
    Based on Mailgun's official documentation.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'MAILGUN_API_KEY', '')
        self.domain = getattr(settings, 'MAILGUN_SANDBOX_DOMAIN', '')
        self.base_url = getattr(settings, 'MAILGUN_BASE_URL', 'https://api.mailgun.net')

        if not self.api_key or not self.domain:
            logger.warning("Mailgun API key or domain not configured. Emails will not be sent.")

    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of email
        messages sent.
        """
        if not email_messages:
            return 0

        sent_count = 0
        for message in email_messages:
            try:
                if self._send_message(message):
                    sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send email via Mailgun: {str(e)}")
                if not self.fail_silently:
                    raise

        return sent_count

    def _send_message(self, message):
        """
        Send a single EmailMessage using Mailgun API.
        """
        if not self.api_key or not self.domain:
            logger.error("Mailgun not configured. Skipping email send.")
            return False

        # Prepare the API endpoint
        url = f"{self.base_url}/v3/{self.domain}/messages"

        # Prepare email data
        data = {
            "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
            "to": message.to,
            "subject": message.subject,
        }

        # Add CC and BCC if present
        if message.cc:
            data["cc"] = message.cc
        if message.bcc:
            data["bcc"] = message.bcc

        # Handle both plain text and HTML content
        if message.body:
            data["text"] = message.body

        # Check if there's an HTML alternative
        if hasattr(message, 'alternatives') and message.alternatives:
            for alternative in message.alternatives:
                if alternative[1] == 'text/html':
                    data["html"] = alternative[0]
                    break

        try:
            # Send the request to Mailgun API
            response = requests.post(
                url,
                auth=("api", self.api_key),
                data=data,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Email sent successfully via Mailgun to {message.to}")
                return True
            else:
                logger.error(
                    f"Mailgun API error: Status {response.status_code}, "
                    f"Response: {response.text}"
                )
                return False

        except requests.RequestException as e:
            logger.error(f"Mailgun request failed: {str(e)}")
            if not self.fail_silently:
                raise
            return False
