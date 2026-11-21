from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .demo import DEMO_ACCOUNTS, demo_login_enabled
from .forms import LoginForm
from .models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = LoginForm(request, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.user)
        return redirect(request.GET.get('next') or 'home')
    return render(request, 'accounts/login.html', {
        'form': form,
        'demo_accounts': [(role, DEMO_ACCOUNTS[role][1]) for role in DEMO_ACCOUNTS] if demo_login_enabled() else [],
    })


@require_POST
def demo_login_view(request):
    """Log in as one of the demo accounts without a password. Only when DJANGO_DEMO_LOGIN is on."""
    if not demo_login_enabled():
        raise Http404
    account = DEMO_ACCOUNTS.get(request.POST.get('role'))
    user = account and User.objects.filter(email=account[2], is_active=True).first()
    if not user:
        messages.error(request, 'The demo accounts don\'t exist yet. Run: python manage.py create_demo_accounts')
        return redirect('login')
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('home')


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')
