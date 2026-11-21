from django.core.management.base import BaseCommand

from accounts.demo import DEMO_ACCOUNTS, demo_login_enabled, ensure_demo_accounts


class Command(BaseCommand):
    help = 'Create the demo manager, accountant and creator used by the login page demo buttons.'

    def handle(self, *args, **options):
        created = ensure_demo_accounts()
        for role, (_, full_name, email) in DEMO_ACCOUNTS.items():
            state = 'created' if any(u.email == email for u in created) else 'ready'
            self.stdout.write(f'{full_name} ({role}, {email}): {state}')
        if not demo_login_enabled():
            self.stdout.write(self.style.WARNING(
                'The demo buttons are hidden until DJANGO_DEMO_LOGIN=true is set in .env.'
            ))
        self.stdout.write(self.style.SUCCESS('Demo accounts ready.'))
