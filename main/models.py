from django.db import models
from django.core.validators import RegexValidator
from decimal import Decimal

class Service(models.Model):
    TIER_CHOICES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('deluxe', 'Deluxe'),
    ]

    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration_minutes = models.IntegerField(help_text="Duration in minutes")
    features = models.JSONField(default=list, blank=True)  # List of features included
    details = models.TextField(blank=True, help_text="Detailed description of the service process, what's included, etc.")
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'price']

    def __str__(self):
        return f"{self.name} - ${self.price}"

    def get_duration_display(self):
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        return f"{minutes}m"

    def get_end_time(self, start_time):
        """Calculate end time given a start time"""
        from datetime import datetime, timedelta
        start_datetime = datetime.combine(datetime.today(), start_time)
        end_datetime = start_datetime + timedelta(minutes=self.duration_minutes)
        return end_datetime.time()


class ServiceImage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='service_images/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'created_at']

    def __str__(self):
        return f"{self.service.name} - Image {self.id}"

    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary images for this service
        if self.is_primary:
            ServiceImage.objects.filter(service=self.service, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class Booking(models.Model):
    # Customer information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)

    # Service details
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='bookings')
    booking_date = models.DateField()
    booking_time = models.TimeField()
    booking_end_time = models.TimeField(null=True, blank=True)

    # Location
    address = models.TextField()
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)

    # Booking metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_confirmed = models.BooleanField(default=False)
    total_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['booking_date', 'booking_time']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.booking_date} at {self.booking_time}"

    def save(self, *args, **kwargs):
        # Auto-calculate end time and price
        if self.service:
            self.booking_end_time = self.service.get_end_time(self.booking_time)
            if not self.total_price:
                self.total_price = self.service.price
        super().save(*args, **kwargs)

    def overlaps_with(self, other_booking):
        """Check if this booking overlaps with another booking"""
        if self.booking_date != other_booking.booking_date:
            return False

        # Check for time overlap
        return (
            (self.booking_time <= other_booking.booking_time < self.booking_end_time) or
            (other_booking.booking_time <= self.booking_time < other_booking.booking_end_time)
        )
