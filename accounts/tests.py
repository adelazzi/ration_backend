from accounts.models import User
from django.test import TestCase
from django.urls import reverse


class AuthFlowTests(TestCase):
    def test_home_requires_login(self):
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, f"{reverse('login')}?next=/")

    def test_register_logs_in_and_redirects_home(self):
        response = self.client.post(reverse('register'), {
            'full_name': 'Adel Azzi',
            'username': 'adel',
            'email': 'adel@example.com',
            'password': 'S0me-strong-pass',
            'confirm_password': 'S0me-strong-pass',
        })
        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(username='adel').exists())

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(reverse('register'), {
            'full_name': 'Adel Azzi',
            'username': 'adel',
            'email': 'adel@example.com',
            'password': 'S0me-strong-pass',
            'confirm_password': 'other-pass-123',
        })
        self.assertContains(response, 'Passwords do not match.')

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
