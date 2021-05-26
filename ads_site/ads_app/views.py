from django.contrib import messages
from django.contrib.auth import user_login_failed
from django.contrib.auth.decorators import login_required
from django.dispatch import receiver
from django.shortcuts import render
import datetime
from .forms import CreateDash
from . import models
import json


def get_user(request):
    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = "unknown user"
    return username


def write_to_log(request, action, item):
    """
        Writes one action to the log file set by LOG_PATH.
        Format: <Timestamp> : <User> <Action>: <Item>
        Example: 12/31/2020 23:59:59 : admin created the test plan: ADS Test 4
    """
    with open(models.LOG_PATH, 'a') as log:
        now = datetime.datetime.now()
        user = get_user(request)
        date_string = now.strftime("%m/%d/%Y %H:%M:%S")
        log.write(date_string + " : " + user + " " + action + ": " + item + "\n")


def write_dashboard_changes_to_log(old_config, new_config):
    """
        Compares two configs in JSON format and writes the changes to the log file set by LOG_PATH.
        Ignores these fields:
        - teamName, version, lastUpdate, executive
    """
    changes_made = False
    config_keys = ['url', 'dashId', 'testPlan', 'folderName', 'folderId', 'choice1', 'choice2', 'choice3',
                   'global_path', 'targeted_project1', 'targeted_project2', 'targeted_project3']

    with open(models.LOG_PATH, 'a') as log:
        for key in config_keys:
            if key not in old_config:
                log.write("                    | - " + key + ": --> " + new_config[key] + "\n")
                changes_made = True
            elif old_config[key] != new_config[key]:
                log.write("                    | - " + key + ": " + old_config[key] + " --> " + new_config[key] + "\n")
                changes_made = True
        if not changes_made:
            log.write("                    | No changes made\n")


@receiver(user_login_failed)
def attempted_login(sender, credentials, **kwargs):
    """
        Writes a failed login attempt to the log file set by LOG_PATH.
        Format: <Timestamp> : login failed for: <Username>
    """
    with open(models.LOG_PATH, 'a') as log:
        now = datetime.datetime.now()
        date_string = now.strftime("%m/%d/%Y %H:%M:%S")
        log.write(date_string + " : " + 'login failed for: {credentials}'
                  .format(credentials=credentials['username']) + "\n")


@login_required
def home(request):
    return render(request, 'ads_app/home.html')


@login_required
def test_plan(request):
    pmo_list = models.get_pmo_list()
    return render(request, 'ads_app/test_plan.html', {'pmo_list': pmo_list})


@login_required
def agile_update(request):
    agile_config_data = models.get_agile_config()
    waterfall_config_data = models.get_waterfall_config()
    return render(request, 'ads_app/agile_update.html', {'agile': agile_config_data, 'waterfall': waterfall_config_data})


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
        child_suites = {
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
                user = get_user(request)
                test_plan_id = models.create_full_test_plan(project, child_suites, user)
                context['test_plan'] = test_plan_id
                write_to_log(request, action, project)
                raise models.DashboardComplete(test_plan_id)
            elif project_type == 'Agile':
                print("Test Plan is : " + project_type)
                test_plan_id = models.create_agile_test_plan(project, child_suites)
                write_to_log(request, action, project)
                context['test_plan'] = test_plan_id
                raise models.DashboardComplete(test_plan_id)
        except models.DashboardComplete:
            print("Test Plan Created")
            messages.success(request, 'The Test Plan was successfully created')
        except Exception as e:
            print("error")
            action = "encountered an error creating a test plan"
            write_to_log(request, action, str(e))
            messages.error(request, e)

    return render(request, 'ads_app/done.html', context)


def radio(request, name):
    option = [(request.POST.get(name))]
    return str(option[0])


def create_dash(request):
    context = {}
    # Setting dictionary key values
    folder_key = 'folder_name'
    url_key = 'url'
    global_key = 'global_path'
    target_key1 = 'target_choice1'
    target_key2 = 'target_choice2'
    target_key3 = 'target_choice3'
    name_key1 = 'target_name1'
    name_key2 = 'target_name2'
    name_key3 = 'target_name3'
    choice_key = 'test_choice'
    test_plan_key = 'test_plan_name'

    organize_by = radio(request, "severity-priority")

    action = "created the dashboard"

    if request.method == 'POST':  # if the request from the HTML is a post
        form = CreateDash(request.POST)
        if form.is_valid():

            # stripping form values
            folder_name = form.cleaned_data[folder_key]
            url = form.cleaned_data[url_key]
            global_path = form.cleaned_data[global_key]
            target_choice1 = form.cleaned_data[target_key1]
            target_choice2 = form.cleaned_data[target_key2]
            target_choice3 = form.cleaned_data[target_key3]
            target_project_name1 = form.cleaned_data[name_key1]
            target_project_name2 = form.cleaned_data[name_key2]
            target_project_name3 = form.cleaned_data[name_key3]
            test_choice = form.cleaned_data[choice_key]
            test_plan_name = form.cleaned_data[test_plan_key]

            # Adding form values to context
            context[folder_key] = folder_name
            context[url_key] = url
            context[global_key] = global_path
            context[target_key1] = target_choice1
            context[target_key2] = target_choice2
            context[target_key3] = target_choice3
            context[name_key1] = target_project_name1
            context[name_key2] = target_project_name2
            context[name_key3] = target_project_name3
            context[choice_key] = test_choice
            context[test_plan_key] = test_plan_name

            choices = [{"choice": target_choice1, "project": target_project_name1},
                       {"choice": target_choice2, "project": target_project_name2},
                       {"choice": target_choice3, "project": target_project_name3}]

            try:
                dash_id = models.create_full_dash(folder_name, url, global_path, test_choice, test_plan_name, choices, organize_by)
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
                    elif str(item.name) == name_key1:
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


def select_row(request):
    request_data = request.POST
    selected = request_data['selected'].strip()
    try:
        config_data = models.get_selected_config(selected)
        return render(request, 'ads_app/update_selected.html', {'json': config_data})
    except FileNotFoundError as error:  # if config file is empty, throw error
        messages.error(request, "Error: The config file is empty")
        config_data = models.get_config()
        write_to_log(request, "encountered an Entry Error", str(error))
        return render(request, 'ads_app/update.html', {'json': config_data})


def submit_update(request):
    context = {}
    # Setting dictionary key values
    folder_key = 'folder_name'
    url_key = 'url'
    global_key = 'global_path'
    target_key1 = 'target_choice1'
    target_key2 = 'target_choice2'
    target_key3 = 'target_choice3'
    name_key1 = 'target_name1'
    name_key2 = 'target_name2'
    name_key3 = 'target_name3'
    choice_key = 'test_choice'
    test_plan_key = 'test_plan_name'

    team_name = "GTO"
    action = "updated the dashboard"
    ignore_first_row = checkbox(request, "ignore_first_row")
    organize_by = radio(request, "severity-priority")

    if request.method == 'POST':  # if the request from the HTML is a post
        form = CreateDash(request.POST)
        print(form)
        if form.is_valid():

            # stripping form values
            folder_name = form.cleaned_data[folder_key]
            url = form.cleaned_data[url_key]
            global_path = form.cleaned_data[global_key]
            target_choice1 = form.cleaned_data[target_key1]
            target_choice2 = form.cleaned_data[target_key2]
            target_choice3 = form.cleaned_data[target_key3]
            target_project_name1 = form.cleaned_data[name_key1]
            target_project_name2 = form.cleaned_data[name_key2]
            target_project_name3 = form.cleaned_data[name_key3]
            test_choice = form.cleaned_data[choice_key]
            test_plan_name_or_id = form.cleaned_data[test_plan_key]

            # Adding form values to context
            context[folder_key] = folder_name
            context[url_key] = url
            context[global_key] = global_path
            context[target_key1] = target_choice1
            context[target_key2] = target_choice2
            context[target_key3] = target_choice3
            context[name_key1] = target_project_name1
            context[name_key2] = target_project_name2
            context[name_key3] = target_project_name3
            context[choice_key] = test_choice
            context[test_plan_key] = test_plan_name_or_id

            choices = [{"choice": target_choice1, "project": target_project_name1},
                       {"choice": target_choice2, "project": target_project_name2},
                       {"choice": target_choice3, "project": target_project_name3}]

            try:
                if ignore_first_row:  # if first rows are ignored, update will get existing values from the config file
                    config_file = models.get_selected_config(folder_name)[0]
                    url = config_file["url"]
                    global_path = config_file["global_path"]
                    choices = [{"choice": config_file["choice1"], "project": config_file["targeted_project1"]},
                       {"choice": config_file["choice2"], "project": config_file["targeted_project2"]},
                       {"choice": config_file["choice3"], "project": config_file["targeted_project3"]}]

                old_config = models.get_selected_config(folder_name)[0]
                dash_id = old_config["dashId"]
                folder_id = old_config["folderId"]
                test_plan_id = models.return_test_plan_id(test_plan_name_or_id, test_choice)

                new_config = models.create_config(team_name, url, dash_id, test_plan_id, folder_name, folder_id,
                                                  global_path, choices, old_config["executive"])
                models.write_config(new_config)
                models.update_dash(folder_name, choices, organize_by, ignore_first_row)
                context["dash_id"] = dash_id
                write_to_log(request, action, folder_name)
                write_dashboard_changes_to_log(old_config, new_config)
                raise models.DashboardComplete(dash_id)  # Populates link with dashboard ID
            except models.DashboardComplete:
                messages.success(request, 'The Dashboard was successfully updated')
                return render(request, 'ads_app/done.html', context)
            except Exception as error:
                messages.error(request, "Entry Error: " + str(error))
                write_to_log(request, "encountered an Entry Error", str(error))
                return render(request, 'ads_app/update_selected.html', context)
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
                    elif str(item.name) == name_key1:
                        error_type = "The Test Project "
                    elif str(item.name) == test_plan_key:
                        error_type = "The Test plan name "
                    messages.error(request, error_type + " needs to be less than 250 characters")
    return render(request, 'ads_app/update_selected.html', context)


def executive(request):
    if request.method == 'POST':  # if the request from the HTML is a post
        request_data = request.POST
        check_list = json.loads(request_data['check_items'])
        action = "updated the executive dashboard"
        selected = ''

        # updates the selected dashboard, throws a general error message if error is encountered
        try:
            models.update_executive(check_list)
            raise models.DashboardComplete()
        except models.DashboardComplete:
            print("Executive dashboard updated")
            messages.success(request, 'The executive dashboard was updated successfully')
        except Exception as e:
            messages.error(request, e)
    config_data = models.get_config()
    write_to_log(request, action, selected)

    return render(request, 'ads_app/update.html', {'json': config_data})


def submit_agile_update(request):
    if request.method == 'POST':  # if the request from the HTML is a post
        request_data = request.POST
        selected = request_data['selected'].strip()
        action = "updated the agile test plan"
        child_suites = {
            'new_feature': checkbox(request, "new_feature"),
            'manual_regression': checkbox(request, "manual_regression"),
            'automated_regression': checkbox(request, "automated_regression"),
            'meter_farm': checkbox(request, "meter_farm"),
            'garden': checkbox(request, "garden"),
            'sve': checkbox(request, "sve")
        }
        # updates the selected dashboard, throws a general error message if error is encountered
        try:
            models.update_agile_plan(selected, child_suites)
            raise models.DashboardComplete()
        except models.DashboardComplete:
            print("Test Plan updated")
            messages.success(request, 'The Test Plan was updated successfully ')
        except Exception as e:
            messages.error(request, e)
    write_to_log(request, action, selected)
    agile_config_data = models.get_agile_config()
    waterfall_config_data = models.get_waterfall_config()

    return render(request, 'ads_app/agile_update.html', {'agile': agile_config_data, 'waterfall': waterfall_config_data})
