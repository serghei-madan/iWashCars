from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('booking/', views.booking, name='booking'),
    path('booking/success/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
]