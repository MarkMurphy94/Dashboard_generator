from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from . import models
import json
import os
import app


def home(request):
    return render(request, 'ads_app/home.html')


def test_plan(request):
    pmo_list = models.get_pmo_list()
    return render(request, 'ads_app/test_plan.html', {'pmo_list': pmo_list})


def create_test(request):
    context = {}
    if request.method == 'POST':  # if the request from the HTML is a post
        form = request.POST
        project = form['project_list'].strip()
        context['project'] = project

        try:
            test_plan_id = models.create_full_test_plan(project)
            context['test_plan'] = test_plan_id
            raise models.DashboardComplete(test_plan_id)
        except models.DashboardComplete:
            print("Test Plan Created")
            messages.success(request, 'The Test Plan was successfully created')
        except Exception as e:
            print("error")
            messages.error(request, e)

    return render(request, 'ads_app/done.html', context)


def update(request):
    config_data = models.get_config()
    return render(request, 'ads_app/update.html', {'json': config_data})


def done(request):
    return render(request, 'ads_app/done.html')


def submit_update(request):
    if request.method == 'POST':  # if the request from the HTML is a post
        request_data = request.POST
        selected = request_data['selected'].strip()
        print("folder name = " + selected)

    try:
        models.update_dash(selected)
        raise models.DashboardComplete()
    except models.DashboardComplete:
        print("Dashboard updated")
        messages.success(request, 'The Dashboard was updated successfully')
    except Exception as e:
        print("error")
        messages.error(request, e)
    config_data = models.get_config()
    return render(request, 'ads_app/update.html', {'json': config_data})
