# Data migration to populate initial vehicle types

from django.db import migrations


def create_default_vehicle_types(apps, schema_editor):
    VehicleType = apps.get_model('main', 'VehicleType')

    # Create Regular Car type
    VehicleType.objects.create(
        name='Regular Car',
        description='Standard sedans, coupes, and compact cars',
        price_multiplier=1.00,
        display_order=1,
        is_active=True
    )

    # Create SUV type
    VehicleType.objects.create(
        name='SUV/Large Vehicle',
        description='SUVs, trucks, vans, and large vehicles',
        price_multiplier=1.00,
        display_order=2,
        is_active=True
    )


def reverse_migration(apps, schema_editor):
    VehicleType = apps.get_model('main', 'VehicleType')
    VehicleType.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_create_vehicletype'),
    ]

    operations = [
        migrations.RunPython(create_default_vehicle_types, reverse_migration),
    ]
