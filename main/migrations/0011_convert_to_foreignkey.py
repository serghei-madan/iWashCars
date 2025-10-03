# Migration to convert vehicle_type from CharField to ForeignKey

import django.db.models.deletion
from django.db import migrations, models


def migrate_vehicle_types(apps, schema_editor):
    """Convert existing vehicle_type string values to ForeignKey references"""
    Service = apps.get_model('main', 'Service')
    Booking = apps.get_model('main', 'Booking')
    VehicleType = apps.get_model('main', 'VehicleType')

    # Get the vehicle types
    regular = VehicleType.objects.get(name='Regular Car')
    suv = VehicleType.objects.get(name='SUV/Large Vehicle')

    # Map old string values to new VehicleType instances
    mapping = {
        'regular': regular,
        'suv': suv,
    }

    # Update all services
    for service in Service.objects.all():
        old_value = service.vehicle_type
        if old_value in mapping:
            service.vehicle_type_new = mapping[old_value]
            service.save()

    # Update all bookings
    for booking in Booking.objects.all():
        old_value = booking.vehicle_type
        if old_value in mapping:
            booking.vehicle_type_new = mapping[old_value]
            booking.save()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_populate_vehicletype'),
    ]

    operations = [
        # Add temporary ForeignKey fields
        migrations.AddField(
            model_name='service',
            name='vehicle_type_new',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='services_new',
                to='main.vehicletype'
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='vehicle_type_new',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='bookings_new',
                to='main.vehicletype'
            ),
        ),
        # Migrate the data
        migrations.RunPython(migrate_vehicle_types, migrations.RunPython.noop),
        # Remove old CharField fields
        migrations.RemoveField(
            model_name='service',
            name='vehicle_type',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='vehicle_type',
        ),
        # Rename new fields to original name
        migrations.RenameField(
            model_name='service',
            old_name='vehicle_type_new',
            new_name='vehicle_type',
        ),
        migrations.RenameField(
            model_name='booking',
            old_name='vehicle_type_new',
            new_name='vehicle_type',
        ),
        # Make fields non-nullable
        migrations.AlterField(
            model_name='service',
            name='vehicle_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='services',
                to='main.vehicletype'
            ),
        ),
        migrations.AlterField(
            model_name='booking',
            name='vehicle_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='bookings',
                to='main.vehicletype'
            ),
        ),
    ]
