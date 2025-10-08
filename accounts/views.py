from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse
from .models import Profile


def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_obj = User.objects.filter(username=email)

        if not user_obj.exists():
            messages.warning(request, 'Account not found')
            return redirect(request.path_info)  # stay on the login page

        profile = user_obj[0].profile
        if not profile.is_email_verified:
            messages.warning(request, 'Your account is not verified')
            return redirect(request.path_info)

        user_obj = authenticate(username=email, password=password)
        if user_obj:
            login(request, user_obj)
            return redirect('/')  # redirect to homepage

        messages.warning(request, 'Invalid Credentials')
        return redirect(request.path_info)

    return render(request, 'accounts/login.html')


def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=email).exists():
            messages.warning(request, 'Email is already taken.')
            return redirect(request.path_info)

        user_obj = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=email
        )
        user_obj.set_password(password)
        user_obj.save()

        messages.success(request, 'An email has been sent to your email address.')
        return redirect(request.path_info)  # stay on the register page

    return render(request, 'accounts/register.html')


def activate_email(request, email_token):
    try:
        profile = Profile.objects.get(email_token=email_token)
        profile.is_email_verified = True
        profile.save()
        messages.success(request, 'Your account has been verified!')
        return redirect('/accounts/login/')
    except Profile.DoesNotExist:
        return HttpResponse('Invalid Email token')
