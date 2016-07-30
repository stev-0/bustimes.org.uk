from django.core.management.base import BaseCommand
from ...models import Operator, Region


class Command(BaseCommand):
    @staticmethod
    def maybe_move_operator(operator, regions):
        if bool(regions) and operator.region not in regions:
            if len(regions) == 1:
                operator.region = regions[0]
                operator.save()
            return 'consider moving %s from %s to %s' % (operator, operator.region, regions)

    @staticmethod
    def maybe_print(output):
        if output is not None:
            print output

    def handle(self, *args, **options):
        for operator in Operator.objects.all():
            # move Anglian Bus to the East Anglia
            regions = Region.objects.filter(service__operator=operator).distinct()
            self.maybe_print(self.maybe_move_operator(operator, regions))

            # move Cumbria to the North West
            regions = Region.objects.filter(
                adminarea__locality__stoppoint__service__operator=operator
            ).distinct()
            self.maybe_print(self.maybe_move_operator(operator, regions))
