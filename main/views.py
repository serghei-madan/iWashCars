from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .forms import BookingForm
from .models import Booking, Service, Payment
from .stripe_utils import StripePaymentService
from .notification_utils import NotificationService
from .address_validator import validate_service_area
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

    # Get existing bookings with their end times (exclude cancelled bookings)
    existing_bookings = Booking.objects.select_related('service').exclude(
        status='cancelled'
    ).values(
        'booking_date', 'booking_time', 'booking_end_time', 'service__duration_minutes'
    )

    # Build unavailable slots considering service duration
    unavailable_slots = {}
    for booking_info in existing_bookings:
        date_str = booking_info['booking_date'].strftime('%Y-%m-%d')
        if date_str not in unavailable_slots:
            unavailable_slots[date_str] = []

        # Mark all slots during the service duration as unavailable
        # Add 30 minutes commute time after service
        start_time = datetime.combine(booking_info['booking_date'], booking_info['booking_time'])
        end_time = datetime.combine(booking_info['booking_date'], booking_info['booking_end_time'])
        end_time_with_commute = end_time + timedelta(minutes=30)  # Add 30 min commute buffer

        current_slot = start_time
        while current_slot < end_time_with_commute:
            time_str = current_slot.strftime('%H:%M')
            if time_str not in unavailable_slots[date_str]:
                unavailable_slots[date_str].append(time_str)
            current_slot += timedelta(minutes=30)

    # Get services for JavaScript
    services = Service.objects.filter(is_active=True).select_related('vehicle_type').values(
        'id', 'name', 'price', 'duration_minutes', 'description', 'tier', 'vehicle_type__id', 'vehicle_type__name', 'deposit_amount'
    )
    service_data = {str(s['id']): {
        'id': s['id'],
        'name': s['name'],
        'price': str(s['price']),
        'duration_minutes': s['duration_minutes'],
        'description': s['description'],
        'tier': s['tier'],
        'vehicle_type_id': s['vehicle_type__id'],
        'vehicle_type_name': s['vehicle_type__name'],
        'deposit_amount': s['deposit_amount'],  # Deposit in cents
        'deposit_amount_dollars': s['deposit_amount'] / 100  # Deposit in dollars
    } for s in services}

    return render(request, 'main/booking.html', {
        'form': form,
        'unavailable_slots': json.dumps(unavailable_slots),
        'service_data': json.dumps(service_data, default=str),
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
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


@csrf_exempt
@require_POST
def create_payment_intent(request):
    """Create a Stripe PaymentIntent for the booking"""
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')

        if not booking_id:
            return JsonResponse({'error': 'Booking ID is required'}, status=400)

        booking = get_object_or_404(Booking, id=booking_id)

        # Create payment intent
        result = StripePaymentService.create_payment_intent(booking, booking.email)

        if result['success']:
            return JsonResponse({
                'clientSecret': result['client_secret'],
                'depositAmount': result['deposit_amount'],
                'totalAmount': result['total_amount'],
            })
        else:
            return JsonResponse({'error': result['error']}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def confirm_payment(request):
    """Confirm payment and capture deposit"""
    try:
        data = json.loads(request.body)
        payment_intent_id = data.get('payment_intent_id')

        if not payment_intent_id:
            return JsonResponse({'error': 'Payment Intent ID is required'}, status=400)

        # Get payment record
        payment = get_object_or_404(Payment, stripe_payment_intent_id=payment_intent_id)

        # Capture deposit
        result = StripePaymentService.capture_deposit(payment)

        if result['success']:
            payment.booking.is_confirmed = True
            payment.booking.status = 'confirmed'
            payment.booking.save()

            notification_results = NotificationService.send_all_booking_notifications(payment.booking)

            return JsonResponse({
                'success': True,
                'message': result['message'],
                'booking_id': payment.booking.id,
                'notifications': notification_results
            })
        else:
            return JsonResponse({'error': result['error']}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    import stripe
    from django.http import HttpResponse

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        # Payment succeeded - this happens when the authorization is complete
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=intent['id'])
            if payment.status == 'pending':
                payment.status = 'deposit_captured'
                payment.save()
        except Payment.DoesNotExist:
            pass

    elif event['type'] == 'payment_intent.payment_failed':
        intent = event['data']['object']
        # Payment failed
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=intent['id'])
            payment.status = 'failed'
            payment.save()
        except Payment.DoesNotExist:
            pass

    return HttpResponse(status=200)


def validate_address_api(request):
    """API endpoint for real-time address validation"""
    if request.method == 'GET':
        address = request.GET.get('address', '').strip()
        city = request.GET.get('city', '').strip()
        zip_code = request.GET.get('zip_code', '').strip()

        # Check if all fields are provided
        if not all([address, city, zip_code]):
            return JsonResponse({
                'valid': None,
                'message': 'Please fill in all address fields',
                'distance_miles': None
            })

        # Validate service area
        result = validate_service_area(address, city, zip_code)

        return JsonResponse({
            'valid': result['valid'],
            'message': result['message'],
            'distance_miles': result['distance_miles']
        })

    return JsonResponse({'error': 'Invalid request method'}, status=405)
