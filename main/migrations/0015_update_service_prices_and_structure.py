# Data migration to update service prices and structure
from django.db import migrations


def update_services(apps, schema_editor):
    """
    Replace old services with new pricing structure
    and proper vehicle type associations
    """
    Service = apps.get_model('main', 'Service')
    VehicleType = apps.get_model('main', 'VehicleType')

    # Get vehicle types
    try:
        regular_car = VehicleType.objects.get(name='Regular Car')
        suv = VehicleType.objects.get(name='SUV/Large Vehicle')
    except VehicleType.DoesNotExist:
        # If vehicle types don't exist, skip this migration
        return

    # Delete old services from migration 0002
    Service.objects.filter(
        tier__in=['basic', 'premium', 'deluxe'],
        vehicle_type__isnull=True
    ).delete()

    # Also delete any services with old prices
    Service.objects.filter(price__in=[25.00, 45.00, 65.00]).delete()

    # Create new services for Regular Car
    regular_services = [
        {
            'name': 'Basic Wash',
            'tier': 'basic',
            'description': 'Exterior wash, wheel cleaning, and drying. Perfect for a quick refresh.',
            'price': 50.00,
            'duration_minutes': 30,
            'display_order': 1,
            'is_active': True,
            'vehicle_type': regular_car,
            'deposit_amount': 2500,
        },
        {
            'name': 'Premium Wash',
            'tier': 'premium',
            'description': 'Complete exterior and interior cleaning. Our most popular service.',
            'price': 100.00,
            'duration_minutes': 60,
            'display_order': 2,
            'is_active': True,
            'vehicle_type': regular_car,
            'deposit_amount': 2500,
        },
        {
            'name': 'Deluxe Wash',
            'tier': 'deluxe',
            'description': 'Premium wash with wax protection and deep interior detailing.',
            'price': 150.00,
            'duration_minutes': 90,
            'display_order': 3,
            'is_active': True,
            'vehicle_type': regular_car,
            'deposit_amount': 2500,
        }
    ]

    # Create new services for SUV/Large Vehicle
    suv_services = [
        {
            'name': 'SUV Basic Wash',
            'tier': 'basic',
            'description': 'Exterior wash, wheel cleaning, and drying for larger vehicles.',
            'price': 100.00,
            'duration_minutes': 45,
            'display_order': 4,
            'is_active': True,
            'vehicle_type': suv,
            'deposit_amount': 2500,
        },
        {
            'name': 'SUV Premium Wash',
            'tier': 'premium',
            'description': 'Complete exterior and interior cleaning for SUVs and large vehicles.',
            'price': 150.00,
            'duration_minutes': 75,
            'display_order': 5,
            'is_active': True,
            'vehicle_type': suv,
            'deposit_amount': 2500,
        },
        {
            'name': 'SUV Deluxe Wash',
            'tier': 'deluxe',
            'description': 'Premium wash with wax protection and deep interior detailing for large vehicles.',
            'price': 200.00,
            'duration_minutes': 120,
            'display_order': 6,
            'is_active': True,
            'vehicle_type': suv,
            'deposit_amount': 2500,
        }
    ]

    # Create services (only if they don't already exist)
    for service_data in regular_services + suv_services:
        Service.objects.get_or_create(
            name=service_data['name'],
            vehicle_type=service_data['vehicle_type'],
            defaults=service_data
        )


def reverse_migration(apps, schema_editor):
    """Reverse the migration by deleting new services"""
    Service = apps.get_model('main', 'Service')
    Service.objects.filter(
        name__in=[
            'Basic Wash', 'Premium Wash', 'Deluxe Wash',
            'SUV Basic Wash', 'SUV Premium Wash', 'SUV Deluxe Wash'
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_alter_booking_id'),
    ]

    operations = [
        migrations.RunPython(update_services, reverse_migration),
    ]
