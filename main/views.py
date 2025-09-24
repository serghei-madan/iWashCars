from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import BookingForm
from .models import Booking, Service
import json
from datetime import datetime, timedelta

def index(request):
    # Get active services for homepage display
    services = Service.objects.filter(is_active=True).order_by('display_order')
    return render(request, 'main/index.html', {'services': services})

def booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save()
            messages.success(request, f'Booking confirmed! We will contact you at {booking.email} to confirm your appointment.')
            return redirect('booking_success', booking_id=booking.id)
    else:
        form = BookingForm()

    # Get existing bookings with their end times
    existing_bookings = Booking.objects.select_related('service').values(
        'booking_date', 'booking_time', 'booking_end_time', 'service__duration_minutes'
    )

    # Build unavailable slots considering service duration
    unavailable_slots = {}
    for booking_info in existing_bookings:
        date_str = booking_info['booking_date'].strftime('%Y-%m-%d')
        if date_str not in unavailable_slots:
            unavailable_slots[date_str] = []

        # Mark all slots during the service duration as unavailable
        start_time = datetime.combine(booking_info['booking_date'], booking_info['booking_time'])
        end_time = datetime.combine(booking_info['booking_date'], booking_info['booking_end_time'])

        current_slot = start_time
        while current_slot < end_time:
            time_str = current_slot.strftime('%H:%M')
            if time_str not in unavailable_slots[date_str]:
                unavailable_slots[date_str].append(time_str)
            current_slot += timedelta(minutes=30)

    # Get services for JavaScript
    services = Service.objects.filter(is_active=True).values(
        'id', 'name', 'price', 'duration_minutes', 'description', 'tier'
    )
    service_data = {str(s['id']): s for s in services}

    return render(request, 'main/booking.html', {
        'form': form,
        'unavailable_slots': json.dumps(unavailable_slots),
        'service_data': json.dumps(service_data, default=str)
    })

def booking_success(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        return render(request, 'main/booking_success.html', {'booking': booking})
    except Booking.DoesNotExist:
        return redirect('index')

def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id, is_active=True)
    return render(request, 'main/service_detail.html', {'service': service})
