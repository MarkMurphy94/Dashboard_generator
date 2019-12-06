from django.shortcuts import render
from django.http import HttpResponse
from . import models

# Create your views here.


def home(request):
    return render(request, 'ads_app/home.html')


def test_plan(request):
    pmo_list = models.get_pmo_list()
    return render(request, 'ads_app/test_plan.html', {'pmo_list': pmo_list})


def update(request):
    return render(request, 'ads_app/update.html')