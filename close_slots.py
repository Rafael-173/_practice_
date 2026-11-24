from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import InstructorSlot


class Command(BaseCommand):
    help = "Закрывает окна, до начала которых меньше 24 часов."

    def handle(self, *args, **options):
        now = timezone.now()
        closed = 0
        for slot in InstructorSlot.objects.filter(is_booked=False):
            slot_dt = timezone.make_aware(datetime.combine(slot.date, slot.start_time))
            if slot_dt - now < timedelta(hours=24):
                slot.is_booked = True
                slot.save(update_fields=["is_booked"])
                closed += 1
        self.stdout.write(self.style.SUCCESS(f"Закрыто окон: {closed}"))