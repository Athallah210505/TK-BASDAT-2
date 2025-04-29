# login_and_logout/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from register.forms import SignUpForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        # <-- PASTIKAN PAKAI SignUpForm
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # opsional, langsung loginkan
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = SignUpForm()

    # path ini harus sesuai lokasi template register.html-mu
    return render(request, 'register/register.html', {'form': form})
