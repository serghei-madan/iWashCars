import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iwashcars.settings')
django.setup()

from django_q.models import Schedule

schedule, created = Schedule.objects.get_or_create(
    func='main.tasks.send_booking_reminders',
    defaults={
        'name': 'Send Booking Reminders',
        'schedule_type': Schedule.MINUTES,
        'minutes': 5,
        'repeats': -1,
    }
)

if created:
    print('✅ Schedule created successfully!')
    print(f'Task: {schedule.func}')
    print(f'Runs every: {schedule.minutes} minutes')
else:
    print('⚠️  Schedule already exists')
    print(f'Task: {schedule.func}')
    print(f'Runs every: {schedule.minutes} minutes')