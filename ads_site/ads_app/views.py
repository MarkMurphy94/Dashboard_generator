from django.contrib import messages
from django.contrib.auth import user_login_failed
from django.contrib.auth.decorators import login_required
from django.dispatch import receiver
from django.shortcuts import render
import datetime
from .forms import CreateDash
from . import models


def get_user(request):
    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = "unknown user"
    return username


def write_to_log(request, action, item):
    with open(models.LOG_PATH, 'a') as log:
        now = datetime.datetime.now()
        user = get_user(request)
        date_string = now.strftime("%m/%d/%Y %H:%M:%S")
        log.write(date_string + " : " + user + " " + action + ": " + item + "\n")


@receiver(user_login_failed)
def attempted_login(sender, credentials, **kwargs):
    with open(models.LOG_PATH, 'a') as log:
        now = datetime.datetime.now()
        date_string = now.strftime("%m/%d/%Y %H:%M:%S")
        log.write(date_string + " : " + 'login failed for: {credentials}'
                  .format(credentials=credentials,) + "\n")


@login_required
def home(request):
    return render(request, 'ads_app/home.html')


@login_required
def test_plan(request):
    pmo_list = models.get_pmo_list()
    return render(request, 'ads_app/test_plan.html', {'pmo_list': pmo_list})


@login_required
def agile_update(request):
    config_data = models.get_agile_config()
    return render(request, 'ads_app/agile_update.html', {'json': config_data})


def checkbox(request, selection):
    value = [(request.POST.get(selection))]
    print(str(selection) + " is " + str(value))
    if value[0] == "on":
        checked = True
    else:
        checked = False
    return checked


def create_test(request):
    context = {}
    action = "created the test plan"
    if request.method == 'POST':  # if the request from the HTML is a post
        form = request.POST
        selected = {
            'new_feature': checkbox(request, "new_feature"),
            'manual_regression': checkbox(request, "manual_regression"),
            'automated_regression': checkbox(request, "automated_regression"),
            'meter_farm': checkbox(request, "meter_farm"),
            'garden': checkbox(request, "garden"),
            'sve': checkbox(request, "sve")
        }
        project = form['project_list'].strip()
        project_type = form['project_type'].strip()
        context['project'] = project

        try:
            print(project_type)
            if project_type == 'Waterfall':
                print("Test Plan is: " + project_type)
                test_plan_id = models.create_full_test_plan(project, selected)
                context['test_plan'] = test_plan_id
                write_to_log(request, action, project)
                raise models.DashboardComplete(test_plan_id)
            elif project_type == 'Agile':
                print("Test Plan is : " + project_type)
                test_plan_id = models.create_agile_test_plan(project, selected)
                write_to_log(request, action, project)
                context['test_plan'] = test_plan_id
                raise models.DashboardComplete(test_plan_id)
        except models.DashboardComplete:
            print("Test Plan Created")
            messages.success(request, 'The Test Plan was successfully created')
        except Exception as e:
            print("error")
            action = "encountered an error creating a test plan"
            write_to_log(request, action, e)
            messages.error(request, e)

    return render(request, 'ads_app/done.html', context)


def create_dash(request):
    context = {}
    # Setting dictionary key values
    folder_key = 'folder_name'
    url_key = 'url'
    global_key = 'global_path'
    target_key = 'target_choice'
    name_key = 'short_name'
    choice_key = 'test_choice'
    test_plan_key = 'test_plan_name'

    action = "created the dashboard"

    if request.method == 'POST':  # if the request from the HTML is a post
        form = CreateDash(request.POST)
        if form.is_valid():

            # stripping form values
            folder_name = form.cleaned_data[folder_key]
            url = form.cleaned_data[url_key]
            global_path = form.cleaned_data[global_key]
            target_choice = form.cleaned_data[target_key]
            short_name = form.cleaned_data[name_key]
            test_choice = form.cleaned_data[choice_key]
            test_plan_name = form.cleaned_data[test_plan_key]

            # Adding form values to context
            context[folder_key] = folder_name
            context[url_key] = url
            context[global_key] = global_path
            context[target_key] = target_choice
            context[name_key] = short_name
            context[choice_key] = test_choice
            context[test_plan_key] = test_plan_name

            try:
                dash_id = models.create_full_dash(folder_name, url, global_path, target_choice,
                                                  short_name, test_choice, test_plan_name)
                context['dash_id'] = dash_id
                write_to_log(request, action, folder_name)
                raise models.DashboardComplete(dash_id)
            except models.DashboardComplete:
                messages.success(request, 'The Dashboard was successfully created')
                return render(request, 'ads_app/done.html', context)
            except Exception as error:
                messages.error(request, "Entry Error: " + str(error))
                write_to_log(request, "encountered an Entry Error", str(error))
                return render(request, 'ads_app/home.html', context)
        else:
            for item in form:
                error_type = "A form field "
                if len(str(form[item.name].value())) > 250:
                    if str(item.name) == folder_key:
                        error_type = "Project name"
                    elif str(item.name) == url_key:
                        error_type = "The URL to MRS tree"
                    elif str(item.name) == global_key:
                        error_type = "Global Reqs iteration path"
                    elif str(item.name) == name_key:
                        error_type = "The Test Project "
                    elif str(item.name) == test_plan_key:
                        error_type = "The Test plan name "
                    messages.error(request, error_type + " needs to be less than 250 characters")
    return render(request, 'ads_app/home.html', context)


@login_required
def update(request):
    config_data = models.get_config()
    return render(request, 'ads_app/update.html', {'json': config_data})


def done(request):
    return render(request, 'ads_app/done.html')


def submit_update(request):
    if request.method == 'POST':  # if the request from the HTML is a post
        request_data = request.POST
        selected = request_data['selected'].strip()
        action = "updated the dashboard"

        # updates the selected dashboard, throws a general error message if error is encountered
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
    write_to_log(request, action, selected)

    return render(request, 'ads_app/update.html', {'json': config_data})


def submit_agile_update(request):
    if request.method == 'POST':  # if the request from the HTML is a post
        request_data = request.POST
        selected = request_data['selected'].strip()
        action = "updated the agile test plan"

        # updates the selected dashboard, throws a general error message if error is encountered
        try:
            models.update_agile_plan(selected)
            raise models.DashboardComplete()
        except models.DashboardComplete:
            print("Test Plan updated")
            messages.success(request, 'The Test Plan was updated successfully ')
        except Exception as e:
            messages.error(request, e)
    config_data = models.get_agile_config()
    write_to_log(request, action, selected)

    return render(request, 'ads_app/agile_update.html', {'json': config_data})
