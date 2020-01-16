from django.contrib import messages
from django.shortcuts import render
from . import models


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


def create_dash(request):
    context = {}
    if request.method == 'POST':  # if the request from the HTML is a post
        form = request.POST

        # stripping form values
        folder_name = form['folder_name'].strip()
        url = form['url'].strip()
        global_path = form['global_path'].strip()
        target_choice = form['target_choice'].strip()
        iteration_shortname = form['iteration_shortname'].strip()
        test_choice = form['test_choice'].strip()
        test_plan_name = form['test_plan_name'].strip()

        # Adding form values to context
        context['folder_name'] = folder_name
        context['url'] = url
        context['global_path'] = global_path
        context['target_choice'] = target_choice
        context['iteration_shortname'] = iteration_shortname
        context['test_choice'] = test_choice
        context['test_plan_name'] = test_plan_name

        try:
            dash_id = models.create_full_dash(folder_name, url, global_path, target_choice,
                                              iteration_shortname, test_choice, test_plan_name)
            context['dash_id'] = dash_id
            raise models.DashboardComplete(dash_id)
        except models.DashboardComplete:
            messages.success(request, 'The Dashboard was successfully created')
            return render(request, 'ads_app/done.html', context)
        except Exception as error:
            messages.error(request, "Entry Error: " + str(error))

    return render(request, 'ads_app/home.html', context)


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
    return render(request, 'ads_app/update.html', {'json': config_data})
