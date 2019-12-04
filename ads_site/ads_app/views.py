from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.


def home(request):
    return render(request, 'ads_app/home.html')


def test_plan(request):
    return render(request, 'ads_app/test_plan.html')


def update(request):
    return render(request, 'ads_app/update.html')