from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.models import User
from core.models import Material, MaterialPrice

# Cape Town prices from the "Optimum Mix Ratios" sheet.
PRICES = [
    ('Sand', '16.43'),
    ('Stone 13mm', '21.75'),
    ('Cement 50kg', '85.00'),
]


class Command(BaseCommand):
    help = 'Add the Cape Town sample prices as approved prices, recorded under the given user.'

    def add_arguments(self, parser):
        parser.add_argument('email', help='Email of the user to record as entering and approving the prices')

    def handle(self, *args, email, **options):
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            raise CommandError(f'No user with email {email}. Register first.')

        now = timezone.now()
        for name, price in PRICES:
            material = Material.objects.filter(name=name).first()
            if material is None:
                self.stderr.write(f'Skipping {name}: material not found.')
                continue
            MaterialPrice.objects.create(
                material=material,
                price=Decimal(price),
                unit=material.base_unit,
                currency='ZAR',
                status=MaterialPrice.Status.APPROVED,
                created_by=user,
                reviewed_by=user,
                reviewed_at=now,
            )
            self.stdout.write(f'{name}: R {price} / {material.base_unit}')
        self.stdout.write(self.style.SUCCESS('Prices loaded.'))
