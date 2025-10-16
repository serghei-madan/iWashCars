from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('health/', views.health_check, name='health_check'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),
    path('booking/', views.booking, name='booking'),
    path('booking/success/<uuid:booking_id>/', views.booking_success, name='booking_success'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
    # Payment endpoints
    path('api/create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('api/confirm-payment/', views.confirm_payment, name='confirm_payment'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    # Address validation endpoint
    path('api/validate-address/', views.validate_address_api, name='validate_address_api'),
]