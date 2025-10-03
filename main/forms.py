from django import forms
from django.core.validators import EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
from .models import Booking, Service
from datetime import datetime, timedelta, time
import re

class BookingForm(forms.ModelForm):
    booking_time = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'select select-bordered w-full', 'id': 'booking-time'}),
        required=True
    )

    class Meta:
        model = Booking
        fields = ['first_name', 'last_name', 'email', 'phone', 'service',
                 'booking_date', 'booking_time', 'address', 'city', 'zip_code']

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': '(555) 123-4567'}),
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