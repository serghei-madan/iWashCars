from django import forms
from .models import Booking, Service
from datetime import datetime, timedelta, time

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
        # Limit services to active ones only
        self.fields['service'].queryset = Service.objects.filter(is_active=True)

        time_choices = [('', 'Select a time')]
        start_time = time(8, 0)
        end_time = time(18, 0)

        current_time = datetime.combine(datetime.today(), start_time)
        end_datetime = datetime.combine(datetime.today(), end_time)

        while current_time <= end_datetime:
            time_str = current_time.strftime('%H:%M')
            display_str = current_time.strftime('%I:%M %p')
            time_choices.append((time_str, display_str))
            current_time += timedelta(minutes=30)

        self.fields['booking_time'].choices = time_choices