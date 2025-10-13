from django import forms
from django.core.validators import EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
from .models import Booking, Service
from .address_validator import validate_service_area
from datetime import datetime, timedelta, time
import re

class BookingForm(forms.ModelForm):
    booking_time = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'select select-bordered w-full', 'id': 'booking-time'}),
        required=True
    )

    class Meta:
        model = Booking
        fields = ['first_name', 'last_name', 'email', 'phone', 'vehicle_type', 'service',
                 'booking_date', 'booking_time', 'address', 'city', 'zip_code']

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': '(555) 123-4567'}),
            'vehicle_type': forms.Select(attrs={'class': 'select select-bordered w-full', 'id': 'vehicle-type-select'}),
            'service': forms.Select(attrs={'class': 'select select-bordered w-full', 'id': 'service-select', 'onchange': 'updateServiceDetails()'}),
            'booking_date': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full', 'id': 'booking-date'}),
            'address': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'placeholder': 'Street Address', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'City'}),
            'zip_code': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'ZIP Code'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = Service.objects.filter(is_active=True)

        time_choices = [('', 'Select a time')]
        start_time = time(7, 0)  # 7:00 AM
        end_time = time(21, 0)   # 9:00 PM

        current_time = datetime.combine(datetime.today(), start_time)
        end_datetime = datetime.combine(datetime.today(), end_time)

        while current_time <= end_datetime:
            time_str = current_time.strftime('%H:%M')
            display_str = current_time.strftime('%I:%M %p')
            time_choices.append((time_str, display_str))
            current_time += timedelta(minutes=30)

        self.fields['booking_time'].choices = time_choices

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.strip().lower()
            email_validator = EmailValidator(message="Enter a valid email address.")
            try:
                email_validator(email)
            except ValidationError:
                raise ValidationError("Please enter a valid email address (e.g., user@example.com).")

            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                raise ValidationError("Please enter a valid email address (e.g., user@example.com).")

        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = re.sub(r'[^\d+]', '', phone)

            if not re.match(r'^\+?1?\d{10,15}$', phone):
                raise ValidationError("Please enter a valid phone number with 10-15 digits (e.g., +1234567890 or 1234567890).")

            if len(phone) < 10:
                raise ValidationError("Phone number must be at least 10 digits.")

        return phone

    def clean(self):
        """
        Validate that the service address is within the service area (10 miles from 91602)
        """
        cleaned_data = super().clean()
        address = cleaned_data.get('address')
        city = cleaned_data.get('city')
        zip_code = cleaned_data.get('zip_code')

        # Only validate if we have all address components
        if address and city and zip_code:
            validation_result = validate_service_area(address, city, zip_code)

            if not validation_result['valid']:
                # Add error to the form
                error_message = validation_result['message']
                if validation_result['distance_miles']:
                    error_message += f" (Distance: {validation_result['distance_miles']} miles)"

                raise ValidationError({
                    'address': error_message
                })

        return cleaned_data


class ContactForm(forms.Form):
    """Simple contact form"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Your Name'
        }),
        required=True
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'your.email@example.com'
        }),
        required=True
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '(555) 123-4567'
        }),
        required=False
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Subject'
        }),
        required=True
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'placeholder': 'Your message...',
            'rows': 6
        }),
        required=True
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.strip().lower()
            email_validator = EmailValidator(message="Enter a valid email address.")
            try:
                email_validator(email)
            except ValidationError:
                raise ValidationError("Please enter a valid email address.")
        return email