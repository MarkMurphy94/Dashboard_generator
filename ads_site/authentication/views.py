from django.shortcuts import render
from django.contrib.auth.forms import   UserCreationForm


def login(request):
    return render(request, 'authentication/login.html')


def register(request):
    form = UserCreationForm()
    return render(request, 'authentication/register.html', {'form': form})
