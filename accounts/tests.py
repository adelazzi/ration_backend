from django.core.management import call_command
from django.test import TestCase, override_settings

from accounts.demo import DEMO_ACCOUNTS
from accounts.models import User
from django.urls import reverse


class AuthFlowTests(TestCase):
    def test_home_requires_login(self):
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, f"{reverse('login')}?next=/")

    def test_register_page_is_gone(self):
        self.assertEqual(self.client.get('/register/').status_code, 404)
        self.assertNotContains(self.client.get(reverse('login')), 'Register')

    def test_login_with_email(self):
        User.objects.create_user('adel', 'adel@example.com', 'S0me-strong-pass')
        response = self.client.post(reverse('login'), {
            'email': 'ADEL@example.com',
            'password': 'S0me-strong-pass',
        })
        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)

    def test_login_wrong_password(self):
        User.objects.create_user('adel', 'adel@example.com', 'S0me-strong-pass')
        response = self.client.post(reverse('login'), {
            'email': 'adel@example.com',
            'password': 'wrong',
        })
        self.assertContains(response, 'Invalid email or password.')

    def test_logout(self):
        User.objects.create_user('adel', 'adel@example.com', 'S0me-strong-pass')
        self.client.login(username='adel', password='S0me-strong-pass')
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))


class AdminUserCreationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'S0me-strong-pass')
        self.client.force_login(self.admin)
        self.url = reverse('admin:accounts_user_add')

    def test_admin_creates_user_with_email_name_and_role(self):
        response = self.client.post(self.url, {
            'username': 'acc', 'email': 'acc@example.com', 'full_name': 'Ana Accountant', 'role': 'accountant',
            'usable_password': 'true', 'password1': 'An0ther-strong-pass', 'password2': 'An0ther-strong-pass',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='acc')
        self.assertEqual((user.email, user.full_name, user.role), ('acc@example.com', 'Ana Accountant', 'accountant'))
        self.assertTrue(self.client.login(username='acc', password='An0ther-strong-pass'))

    def test_admin_add_form_requires_email(self):
        response = self.client.post(self.url, {
            'username': 'acc', 'email': '', 'full_name': 'Ana', 'role': 'creator',
            'usable_password': 'true', 'password1': 'An0ther-strong-pass', 'password2': 'An0ther-strong-pass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='acc').exists())


class DemoLoginTests(TestCase):
    def setUp(self):
        call_command('create_demo_accounts', stdout=open('/dev/null', 'w'))

    def test_command_creates_three_accounts_without_passwords(self):
        for role, (_, _, email) in DEMO_ACCOUNTS.items():
            user = User.objects.get(email=email)
            self.assertEqual(user.role, role)
            self.assertFalse(user.has_usable_password())
        call_command('create_demo_accounts', stdout=open('/dev/null', 'w'))
        self.assertEqual(User.objects.filter(email__endswith='@demo.ration').count(), 3)

    @override_settings(DEMO_LOGIN=False)
    def test_demo_login_off_by_default(self):
        self.assertNotContains(self.client.get(reverse('login')), 'Or try a demo account')
        self.assertEqual(self.client.post(reverse('demo_login'), {'role': 'manager'}).status_code, 404)

    @override_settings(DEMO_LOGIN=True)
    def test_buttons_log_in_as_each_role(self):
        page = self.client.get(reverse('login'))
        self.assertContains(page, 'Or try a demo account')
        for role in ('manager', 'accountant', 'creator'):
            self.assertContains(page, f'value="{role}"')
            response = self.client.post(reverse('demo_login'), {'role': role})
            self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)
            user = User.objects.get(pk=self.client.session['_auth_user_id'])
            self.assertEqual(user.role, role)
            self.client.logout()

    @override_settings(DEMO_LOGIN=True)
    def test_unknown_role_or_missing_accounts(self):
        response = self.client.post(reverse('demo_login'), {'role': 'admin'}, follow=True)
        self.assertContains(response, 'create_demo_accounts')
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(DEMO_LOGIN=True)
    def test_demo_login_needs_post(self):
        self.assertEqual(self.client.get(reverse('demo_login')).status_code, 405)
