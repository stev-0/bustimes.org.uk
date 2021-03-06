from datetime import date, timedelta
from django.core.management.base import BaseCommand
from ...models import Service, ServiceDate
from ...utils import timetable_from_service


class Command(BaseCommand):
    def handle(self, *args, **options):
        for service in Service.objects.filter(show_timetable=True):
            today = date.today()
            days = 0
            tried_days = 0

            while days < 7 and tried_days < 100:
                timetables = timetable_from_service(service, today)
                for timetable in timetables:
                    if any(grouping.rows and grouping.rows[0].times for grouping in timetable.groupings):
                        ServiceDate.objects.update_or_create(service=service, date=today)
                        days += 1
                        break
                today += timedelta(days=1)
                tried_days += 1
