from django import forms
from django.contrib.auth import authenticate, password_validation
from .models import User


class RegisterForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        if password and password != cleaned.get('confirm_password'):
            self.add_error('confirm_password', 'Passwords do not match.')
        elif password:
            user = User(username=cleaned.get('username'), email=cleaned.get('email'),
                        full_name=cleaned.get('full_name'))
            try:
                password_validation.validate_password(password, user)
            except forms.ValidationError as e:
                self.add_error('password', e)
        return cleaned

    def save(self):
        return User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            full_name=self.cleaned_data['full_name'],
        )


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email')
        password = cleaned.get('password')
        if email and password:
            account = User.objects.filter(email__iexact=email).first()
            if account:
                self.user = authenticate(self.request, username=account.username, password=password)
            if self.user is None:
                raise forms.ValidationError('Invalid email or password.')
        return cleaned
