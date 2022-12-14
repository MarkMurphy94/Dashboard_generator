from django.conf import settings
from requests.auth import HTTPBasicAuth
from pytz import reference
import datetime
import os
import json
import requests

# reading in token credentials for user
CONFIGS_PATH = settings.BASE_DIR + r'/ads_app/static/Dashboard configs/'
LOG_PATH = settings.BASE_DIR + r'/ads_app/static/logs.txt'
TOKEN_PATH = settings.BASE_DIR + r'/ads_app/static/token.txt'
AGILE_PATH = settings.BASE_DIR + r'/ads_app/static/agile_plans.txt'
WATERFALL_PATH = settings.BASE_DIR + r'/ads_app/static/waterfall_plans.txt'
with open(TOKEN_PATH, 'r') as TOKEN_FILE:
    USER = TOKEN_FILE.readline().strip()
    TOKEN = TOKEN_FILE.readline().strip()

# setting class level variables
PROJECT = "RnD"
GTO = 'GTO'
EXECUTIVE_ID = '1d9b31cb-3538-40f1-8830-92ae1575b269'
NOT_FOUND = "not found"
JSON_ERROR = "json error"
DATE_FORMAT = " MM/DD-MM/DD"
MAX_WIDGETS = 8  # maximum number of widgets per row, set to meet max limit of 200 per dashboard
MAX_COLUMN = 2*MAX_WIDGETS  # maximum number of columns per row, most widgets take 2 columns
CURRENT_SPRINT_DEFAULT = 2
VERSION = 'v0.2'  # Application Version
URL_HEADER = 'https://dev.azure.com/itron/'
DASH_HEADER = 'https://dev.azure.com/itron/RnD/_dashboards/dashboard/'
PMO_PATH = settings.BASE_DIR + r'/ads_app/static/PMO_List.txt'
SUITE_RUNS = ["Run 3" + DATE_FORMAT, "Run 2" + DATE_FORMAT, "Run 1" + DATE_FORMAT]
CUSTOMER_SUITES = ["SVE ", "Garden ", "Meter Farm "]
CUSTOMER_KEYS = ["sve", "garden", "meter_farm"]

# settings dictionary for json charts
standardChartSettings = """
                    {"chartType":"StackAreaChart",
                    "groupKey":"TBD",
                    "scope":"WorkitemTracking.Queries",
                    "title":"Widget",
                    "transformOptions":{
                        "filter":"TBD",
                        "groupBy":"System.AreaPath",
                        "orderBy":{
                            "propertyName":"value",
                            "direction":"descending"},
                        "measure":{
                            "aggregation":"sum",
                            "propertyName":"Microsoft.VSTS.Scheduling.Effort"},
                        "historyRange":null},
                        "userColors":[],
                        "lastArtifactName":"TBD"}
                    """

# region Chart Colors
standardRNDWitColorArray = [
    {
        "value": "1 - Critical",
        "backgroundColor": "#e60017"
    },
    {
        "value": "Production",
        "backgroundColor": "#e60017"
    },
    {
        "value": "4 - Low",
        "backgroundColor": "#339947"
    },
    {
        "value": "2 - High",
        "backgroundColor": "#f58b1f"
    },
    {
        "value": "3 - Medium",
        "backgroundColor": "#3f9bd8"
    },
    {
        "value": "4",
        "backgroundColor": "#339947"
    },
    {
        "value": "3",
        "backgroundColor": "#3f9bd8"
    },
    {
        "value": "2",
        "backgroundColor": "#f58b1f"
    },
    {
        "value": "1",
        "backgroundColor": "#e60017"
    },
    {
        "value": "(blank)",
        "backgroundColor": "#cccccc"
    },
]

standardPieChartColorArray = [
    {
        "value": "Design",
        "backgroundColor": "#3f9bd8"
    },
    {
        "value": "Ready",
        "backgroundColor": "#339947"
    }
]

standardTestPlanWitColorArray = [
    {
        "value": "Passed",
        "backgroundColor": "#339947"
    },
    {
        "value": "Blocked",
        "backgroundColor": "#525151"
    },
    {
        "value": "Not run",
        "backgroundColor": "#292e6b"
    },
    {
        "value": "Failed",
        "backgroundColor": "#e31e26"
    },
    {
        "value": "Not applicable",
        "backgroundColor": "#71338d"
    },
    {
        "value": "In progress",
        "backgroundColor": "#ffcc05"
    },
    {
        "value": "Inconclusive",
        "backgroundColor": "#86cdde"
    },
]

# noinspection SpellCheckingInspection
standardWitColorArray = [
    {
        "backgroundColor": "#e60017",
        "value": "New"
    },
    {
        "backgroundColor": "#e87025",
        "value": "Active"
    },
    {
        "backgroundColor": "#60af49",
        "value": "Resolved"
    },
    {
        "backgroundColor": "#86cdde",
        "value": "Closed"
    }
]
# endregion

# dictionary for features chart
features_dictionary = [
    {
        "referenceName": "System.Title",
        "name": "Title"
    },
    {
        "referenceName": "System.AssignedTo",
        "name": "Assigned To"
    },
    {
        "referenceName": "System.State",
        "name": "State"
    },
    {
        "referenceName": "Microsoft.VSTS.Scheduling.Effort",
        "name": "Effort"
    }
]


# region Custom Exceptions
class TestPlanError(Exception):
    """Error Finding Test Plan!"""


class DashboardComplete(Exception):
    """Dashboard Completed Successfully"""


class ApiTestIDNotFound(Exception):
    """Test Plan ID was not Found"""


class FolderAlreadyExists(Exception):
    """Query Folder already Exists"""


class DashAlreadyExists(Exception):
    """Dashboard already Exists"""


class QueryUpdateError(Exception):
    """Folders do not support WIQL"""


class DashDoesNotExists(Exception):
    """Dashboard does not Exist"""


class QueryFolderNotFound(Exception):
    """Query folder not found"""


class TestPlanNotFound(Exception):
    """Test plan not found"""


# endregion


# region Create Test Plan
def get_pmo_list():
    """
        returns the pmo list from the file in the pmo_path
    """

    with open(PMO_PATH, 'r') as lines:
        pmo_list = lines.readlines()

    return pmo_list


def create_agile_test_plan(test_plan, child_suites):
    """
        Creates an Agile test plan based on the name given
        :return test plan ID
    """
    create_iteration(test_plan)  # creates iteration
    test_plan_id = create_test_plan(test_plan)
    suite_id = str(int(test_plan_id) + 1)

    # region Final Product
    suite_name = "Final Product Test"
    final_suite = create_suite(suite_name, test_plan_id, suite_id)
    # create a child template suite for Final Product
    suite_name = "<Device> Sprint <#>" + DATE_FORMAT
    device_suite = create_suite(suite_name, test_plan_id, final_suite)
    create_final_product(test_plan_id, device_suite)
    # endregion

    # region Sprints
    suite_name = "Sprints"
    sprints_suite = create_suite(suite_name, test_plan_id, suite_id)
    create_sprint_suite_runs(test_plan_id, sprints_suite, child_suites)
    # endregion

    create_agile_config(test_plan, test_plan_id, sprints_suite)

    return test_plan_id


def create_full_test_plan(test_plan, child_suites, user_name):
    """
        Creates a test plan based on the name given
        :return test plan ID
    """
    create_iteration(test_plan)  # creates iteration
    test_plan_id = create_test_plan(test_plan)
    suite_id = str(int(test_plan_id) + 1)
    create_waterfall_config(test_plan, test_plan_id, user_name)

    # region Final Product
    suite_name = "Final Product Test"
    final_suite = create_suite(suite_name, test_plan_id, suite_id)
    # create two child template suites for Final Product
    suite_name = "<Device #2> - Run 1 <version>" + DATE_FORMAT
    device_suite = create_suite(suite_name, test_plan_id, final_suite)
    create_final_product(test_plan_id, device_suite)

    suite_name = "<Device #1> - Run 1 <version>" + DATE_FORMAT
    device_suite = create_suite(suite_name, test_plan_id, final_suite)
    create_final_product(test_plan_id, device_suite)
    # endregion

    # region Customer Solution
    # Don't create Customer Solution Test suite if no child suites are checked
    any_customer_suites_checked = False
    for x in range(len(CUSTOMER_SUITES)):
        if child_suites[CUSTOMER_KEYS[x]]:
            any_customer_suites_checked = True
    if any_customer_suites_checked:
        suite_name = "Customer Solution Test"
        customer_suite = create_suite(suite_name, test_plan_id, suite_id)
        create_customer_suite_runs(test_plan_id, customer_suite, child_suites)
    # endregion

    # region System Test
    suite_name = "System Test"
    system_test = create_suite(suite_name, test_plan_id, suite_id)
    create_suite_runs(test_plan_id, system_test, child_suites)
    # endregion

    # region Early System Test
    suite_name = "Early System Test"
    early_system = create_suite(suite_name, test_plan_id, suite_id)
    create_early_system_children(test_plan_id, early_system, child_suites)
    # endregion

    return test_plan_id


def create_iteration(test_plan):
    """
        Creates an iteration path under RnD/GTO
    """
    version = {'api-version': '5.1'}
    iteration = {
        "name": test_plan
    }
    response = requests.post(URL_HEADER + PROJECT
                             + '/_apis/wit/classificationnodes/Iterations/GTO?',
                             auth=HTTPBasicAuth(USER, TOKEN),
                             json=iteration, params=version)
    dash_response = response.json()
    print(response.status_code)
    if response.status_code == 400:
        print(json.dumps(response.json()))
        raise DashAlreadyExists("""
                                Failed to create iteration.
                                Do not include these characters in your test plan name: 
                                $ ? : # % | +
                                """)


def create_test_plan(test_plan):
    """
        Creates test plan
        :return test plan ID
    """
    version = {'api-version': '5.0'}
    path = "RnD\\GTO\\"
    json_obj = {
        "name": test_plan,
        "area": {
            "name": path
        },
        "iteration": path + test_plan
    }

    response = requests.post(URL_HEADER + PROJECT + '/_apis/test/plans?',
                             auth=HTTPBasicAuth(USER, TOKEN),
                             json=json_obj, params=version)
    test_plan_response = response.json()

    # indicates that a test plan with test_plan name already exists
    if response.status_code != 200:
        print(json.dumps(response.json()))
        raise DashAlreadyExists("Test Plan with name " + test_plan
                                + " already exists")

    print(json.dumps(test_plan_response))
    print(test_plan_response["id"])
    return test_plan_response["id"]


def create_waterfall_config(test_plan, test_plan_id, user_name):
    """
        Creates a JSON config file for a waterfall test plan with the parameters provided
    """
    now = datetime.datetime.now()
    localtime = reference.LocalTimezone()
    date_string = now.strftime("%m/%d/%Y %H:%M:%S, " + localtime.tzname(now))

    data = []

    try:
        with open(WATERFALL_PATH, 'r') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        file = open(WATERFALL_PATH, 'w+')
        file.close()
    except ValueError:  # json loads fails on empty file
        pass

    config_file = {
        'test_plan': test_plan,
        'test_plan_id': test_plan_id,
        'lastUpdate': date_string,
        'createdBy': user_name
    }

    data.append(config_file)

    with open(WATERFALL_PATH, 'w') as outfile:
        json.dump(data, outfile)


def create_suite(suite_name, test_plan_id, suite_id):
    """
        Creates a test suite
        :return test suite ID
    """
    version = {'api-version': '5.0'}
    json_obj = {
        "suiteType": "StaticTestSuite",
        "name": suite_name
    }

    response = requests.post(URL_HEADER + PROJECT + '/_apis/test/Plans/'
                             + str(test_plan_id) + '/suites/' + str(suite_id)
                             + '?', auth=HTTPBasicAuth(USER, TOKEN),
                             json=json_obj, params=version)
    suite_response = response.json()

    if response.status_code == 404:  # indicates that the test plan was not found
        print(json.dumps(response.json()))
        raise TestPlanError(
            "Test Plan with Id " + str(test_plan_id) + " not found or no longer exists")
    if response.status_code != 200:  # indicates that a test plan with suite name already exists
        print(json.dumps(response.json()))
        raise DashAlreadyExists("Test Plan with name " + suite_name
                                + " already exists")

    print(json.dumps(suite_response))
    print(suite_response["value"][0]["id"])
    return suite_response["value"][0]["id"]


def create_suite_runs(test_plan_id, suite_id, child_suites):
    """
        Creates second tier child suites
    """
    for suite_name in SUITE_RUNS:
        row_id = create_suite(suite_name, test_plan_id, suite_id)
        create_children_suites(test_plan_id, row_id, child_suites)


def create_customer_suite_runs(test_plan_id, suite_id, child_suites):
    """
        Creates the second tier child suites for Customer Solutions
    """
    for suite_name in SUITE_RUNS:
        create_customer_suites(test_plan_id, suite_id, suite_name, child_suites)


def create_sprint_suite_runs(test_plan_id, suite_id, child_suites):
    """
        Creates the second tier child suites for Customer Solutions
    """
    sprints = ["Sprint 1"]
    for suite_name in sprints:
        row_id = create_suite(suite_name + DATE_FORMAT, test_plan_id, suite_id)
        create_customer_children(test_plan_id, row_id, child_suites)
        create_children_suites(test_plan_id, row_id, child_suites)


def create_early_system_children(test_plan_id, suite_id, child_suites):
    """
        Creates the second tier child suites for Early System Test
    """
    suite_names = ["Beta 1/Feature Complete" + DATE_FORMAT, "Alpha 3" + DATE_FORMAT,
                   "Alpha 2" + DATE_FORMAT, "Alpha 1" + DATE_FORMAT]
    for suite_name in suite_names:
        row_id = create_suite(suite_name, test_plan_id, suite_id)
        create_children_suites(test_plan_id, row_id, child_suites)


def create_final_product(test_plan_id, suite_id):
    """
        Creates the second tier child suites for Final Product
    """
    suite_names = ["Product Secure", "HW FAT Test Suites",
                   "FW FAT Test Suites", "E2E FAT Test Suites"]

    for suite_name in suite_names:
        create_suite(suite_name, test_plan_id, suite_id)


def create_children_suites(test_plan, suite_id, child_suites):
    """
        Creates the third tier child suites for Garden and SVE suites
    """
    suite_names = ["Automatic Regression", "Manual Regression", "New Features"]
    if child_suites["automated_regression"]:
        create_suite(suite_names[0], test_plan, suite_id)
    if child_suites["manual_regression"]:
        create_suite(suite_names[1], test_plan, suite_id)
    if child_suites["new_feature"]:
        create_suite(suite_names[2], test_plan, suite_id)


def create_meter_farm_suites(test_plan, suite_id):
    """
        Creates the third tier child suites for Meter Farm suites
    """
    suite_names = ["System ZZZ", "System YYY", "System XXX"]

    for suite_name in suite_names:
        create_suite(suite_name, test_plan, suite_id)


def create_customer_children(test_plan_id, suite_id, child_suites):
    """
        Creates third tier child suites for Customer Solutions suite
    """
    if child_suites["sve"]:
        create_suite(CUSTOMER_SUITES[0], test_plan_id, suite_id)
    if child_suites["garden"]:
        create_suite(CUSTOMER_SUITES[1], test_plan_id, suite_id)
    if child_suites["meter_farm"]:
        create_suite(CUSTOMER_SUITES[2], test_plan_id, suite_id)


def create_customer_suites(test_plan_id, suite_id, parent_suite, child_suites):
    """
        Creates third tier child suites for Customer Solutions suite
    """
    for x in range(len(CUSTOMER_SUITES)):
        if child_suites[CUSTOMER_KEYS[x]]:
            suite_title = CUSTOMER_SUITES[x] + parent_suite
            row_id = create_suite(suite_title, test_plan_id, suite_id)
            if CUSTOMER_SUITES[x] == "Meter Farm ":
                create_meter_farm_suites(test_plan_id, row_id)
            else:
                create_children_suites(test_plan_id, row_id, child_suites)


def create_agile_config(test_plan, test_plan_id, sprints_suite):
    """
        Creates a JSON config file with the parameters provided, this is used
        when performing the update function
    """
    now = datetime.datetime.now()
    date_string = now.strftime("%m/%d/%Y %H:%M:%S")

    data = []

    try:
        with open(AGILE_PATH, 'r') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        file = open(AGILE_PATH, 'w+')
        file.close()
    except ValueError:  # json loads fails on empty file
        pass

    config_file = {
        'test_plan': test_plan,
        'test_plan_id': test_plan_id,
        'sprints_suite': sprints_suite,
        'current_sprint': "1",
        'lastUpdate': date_string
    }

    data.append(config_file)

    with open(AGILE_PATH, 'w') as outfile:
        json.dump(data, outfile)


# endregion

# region Create Full Dashboard


def create_full_dash(folder, url, global_path, test_choice, test_suite, choices, organize_by):
    """
        Calls functions to complete the tasks below:
         - Verifies query folder does not exist
         - Verifies test plan id or name is found
         - Creates a blank dashboard
         - Populates the created dashboard with widgets
         - Creates a config file for future updates

        :returns the id of the dashboard created
    """
    # PROJECT = 'SoftwareProducts'
    team_name = 'GTO'  # 'SQA'
    check_folder_exists(folder)
    test_plan = return_test_plan_id(test_suite, test_choice)
    dash_id = create_dash(team_name, folder)
    query_folder = create_query_folder(folder)
    populate_baseline_query_folder(query_folder, global_path, choices)
    populate_dash(team_name, url, test_plan, folder, query_folder, dash_id, global_path, organize_by)

    json_config = create_config(team_name, url, dash_id, test_plan, folder, query_folder, global_path, choices)
    write_config(json_config)
    return dash_id


def check_folder_exists(folder):
    """
        Verifies that Query folder already exists

        :raises a FolderAlreadyExists Exception if the folder is found
    """
    query_path = 'Shared Queries/GTO/' + folder
    payload = {'api-version': '5.1'}

    response = requests.get(URL_HEADER + PROJECT + '/_apis/wit/queries/'
                            + query_path + '?',
                            auth=HTTPBasicAuth(USER, TOKEN), params=payload)
    # indicates that query folder with folderName already exists
    if response.status_code == 200:
        print(json.dumps(response.json()))
        raise FolderAlreadyExists("Query Folder with name " + folder + " already exists")


def return_test_plan_id(test_suite, test_choice):
    """
        Returns test plan ID given test suite ID and testChoice

        :return test plan id as a string
    """
    if test_choice == "1":
        test_plan_id = find_test_plan_id_by_name(test_suite)
    else:
        test_plan_id = int(test_suite) - 1
        check_test_plan_id(test_plan_id)
    return str(test_plan_id)


def create_dash(team_name, dash_name):
    """
        Creates a blank dashboard
        :return Dashboard ID
    """
    version = {'api-version': '4.1-preview.2'}
    dash_board = {
        "name": dash_name
    }
    response = requests.post(URL_HEADER + PROJECT + '/' + team_name +
                             '/_apis/dashboard/dashboards?',
                             auth=HTTPBasicAuth(USER, TOKEN),
                             json=dash_board, params=version)

    # indicates that a dashboard with dashName already exists
    if response.status_code != 200:
        print(json.dumps(response.json()))
        raise DashAlreadyExists("Dashboard with name " + dash_name
                                + " already exists")

    dash_response = response.json()
    print(json.dumps(dash_response))
    print(dash_response["id"])
    return dash_response["id"]


def create_query_folder(folder):
    """
        Creates a query folder with the provided folder name

        :returns the id of the query folder created
    """
    query = 'Shared Queries/GTO'
    payload = {'api-version': '5.1'}
    json_obj = {"name": folder, "isFolder": "true"}

    response = requests.post(URL_HEADER + PROJECT + '/_apis/wit/queries/'
                             + query + '?', auth=HTTPBasicAuth(USER, TOKEN),
                             json=json_obj, params=payload)

    # indicates that query folder with folderName already exists
    if response.status_code != 201:
        print(json.dumps(response.json()))
        raise FolderAlreadyExists('Query Folder with name "' + folder + '" already exists')

    query_response = response.json()
    return query_response['id']


def populate_baseline_query_folder(query_folder, global_reqs_path, choices, first_time=True):
    """
        Populates the given folder with the standard queries.

        If first_time is set to False:
         - Checks if standard queries exist
         - Creates missing standard queries
         - Updates existing standard queries
    """

    # Target clause is dependent on User's GUI choice, can include up to 3 targeted projects/tags
    target_clause = "("
    count = 0
    for target, next_ in zip(choices, choices[1:] + ["end"]):
        if target["project"] != "":
            count += 1
            if target["choice"] == "0":
                target_clause += "[Custom.TargetedProject] contains '{}'".format(str(target["project"]))
                if count < 3 and next_["project"] != "":
                    target_clause += " or "
                else:
                    target_clause += ") "
            else:
                target_clause += "[Custom.Tags] contains '{}'".format(str(target["project"]))
                if count < 3 and next_["project"] != "":
                    target_clause += " or "
                else:
                    target_clause += ") "

    # region WIQL constants
    selected_columns = "select [System.Id], [System.WorkItemType], [System.Title]," \
                       " [Microsoft.VSTS.Common.Severity], [Microsoft.VSTS.Common.Priority]," \
                       " [System.AssignedTo], [System.State], [System.CreatedDate]," \
                       " [Microsoft.VSTS.Common.ResolvedDate], [System.AreaPath]," \
                       " [System.IterationPath], [Custom.TargetedProject], [System.Tags]"
    from_bugs = " from WorkItems where [System.WorkItemType] = 'Bug' "
    # endregion

    # region WIQL statements
    wiql_dev_bugs = selected_columns + from_bugs + \
                    "and [System.State] in ('New', 'Active') " \
                    "and " + target_clause + \
                    "and [Custom.Monitoring] = False"
    wiql_all_closed_this_week = selected_columns + ", [Microsoft.VSTS.Common.ClosedDate]" + from_bugs + \
                                "and " + target_clause + \
                                "and [Microsoft.VSTS.Common.ClosedDate] >= @today - 7 " \
                                "and [System.State] = 'Closed' " \
                                "order by [System.CreatedDate] desc"
    wiql_all_created_this_week = selected_columns + from_bugs + \
                                 "and " + target_clause + \
                                 "and [System.CreatedDate] > @today - 7 " \
                                 "order by [System.CreatedDate] desc"
    wiql_monitored = selected_columns + from_bugs + \
                     "and not [System.State] contains 'Closed' " \
                     "and " + target_clause + \
                     "and [Custom.Monitoring] = True " \
                     "order by [System.CreatedDate] desc"
    wiql_new_issues_last_24_hours = selected_columns + from_bugs + \
                                    "and [System.State] <> 'Closed' " \
                                    "and " + target_clause + \
                                    "and [System.CreatedDate] >= @today - 1"
    wiql_cannot_reproduce = selected_columns + from_bugs + \
                            "and [System.State] <> 'Closed' " \
                            "and " + target_clause + \
                            "and [System.reason] = 'Cannot Reproduce' "
    wiql_all_bugs = selected_columns + from_bugs + \
                    "and not [System.State] contains 'Closed' " \
                    "and " + target_clause + \
                    "order by [System.CreatedDate] desc"
    wiql_all_resolved_this_week = selected_columns + from_bugs + \
                                  "and " + target_clause + \
                                  "and [Microsoft.VSTS.Common.ResolvedDate] >= @today - 7 " \
                                  "and [System.State] = 'Resolved' " \
                                  "order by [System.CreatedDate] desc"
    wiql_rtt = selected_columns + from_bugs + \
               "and [System.State] = 'Resolved' " \
               "and " + target_clause + \
               "and [Custom.Monitoring] = False"
    wiql_lifetime_bugs = selected_columns + from_bugs + \
                         "and " + target_clause
    wiql_failed_test = selected_columns + ", [System.AreaLevel2]" + from_bugs + \
                       "and " + target_clause + \
                       "and (ever [System.Reason] = 'Test Failed' " \
                       "or ever [System.Reason] = 'Not fixed')"

    # SQA Features statements
    wiql_sqa_test_features = "select [System.Id], [System.WorkItemType], [System.Title], " \
                             "[System.AssignedTo], [System.State], [System.Tags] " \
                             "from WorkItems " \
                             "where [System.WorkItemType] = 'Feature' " \
                             "and [System.AreaPath] under 'GlobalReqs\\System Test' " \
                             "and [System.IterationPath] under " + repr(global_reqs_path) + " "\
                             "and [System.State] <> 'Removed' " \
                             "order by [System.Id] "
    wiql_sqa_test_features_without_test_cases = "select [System.Id], [System.WorkItemType], [System.Title], " \
                                                "[System.AssignedTo], [System.State], [System.Tags] " \
                                                "from WorkItemLinks " \
                                                "where (Source.[System.WorkItemType] = 'Feature' " \
                                                "and Source.[System.AreaPath] under 'GlobalReqs\\System Test' " \
                                                "and Source.[System.IterationPath] under " + repr(global_reqs_path) + ") " \
                                                "and (Target.[System.WorkItemType] = 'Test Case') " \
                                                "and Source.[System.State] <> 'Removed' " \
                                                "order by [System.Id] mode (DoesNotContain)"
    # endregion

    # region Populate Standard Query Objects
    query_objects = [{"name": "Dev Bugs", "wiql": wiql_dev_bugs},
                     {"name": "All closed this week", "wiql": wiql_all_closed_this_week},
                     {"name": "All created this week", "wiql": wiql_all_created_this_week},
                     {"name": "Monitored", "wiql": wiql_monitored},
                     {"name": "New Issues last 24 hours", "wiql": wiql_new_issues_last_24_hours},
                     {"name": "Cannot Reproduce", "wiql": wiql_cannot_reproduce},
                     {"name": "All Bugs", "wiql": wiql_all_bugs},
                     {"name": "All resolved this week", "wiql": wiql_all_resolved_this_week},
                     {"name": "RTT", "wiql": wiql_rtt},
                     {"name": "Lifetime Bugs", "wiql": wiql_lifetime_bugs},
                     {"name": "Failed Test", "wiql": wiql_failed_test}]
    # endregion

    if not first_time:
        query_folder_children = return_query_folder_children(query_folder)
    else:
        query_folder_children = []

    for json_obj in query_objects:
        if first_time or (json_obj["name"] not in query_folder_children):
            create_query(json_obj, query_folder)
            print("Created " + json_obj["name"])
        else:
            temp_wiql = json_obj["wiql"]
            json_obj["wiql"] = {"wiql": temp_wiql}
            update_query(json_obj["wiql"], query_folder, json_obj["name"])
            print("Updated " + json_obj["name"])

    # SQA queries are dependent on global_reqs_path instead of first_time
    if global_reqs_path.upper() != "N/A" and global_reqs_path.upper() != "NA":
        sqa_query_objects = [{"name": "SQA Test Features", "wiql": wiql_sqa_test_features},
                             {"name": "SQA Test Features without test cases", "wiql": wiql_sqa_test_features_without_test_cases}]
        for json_obj in sqa_query_objects:
            if json_obj["name"] not in query_folder_children:
                create_query(json_obj, query_folder)
                print("Created " + json_obj["name"])
            else:
                temp_wiql = json_obj["wiql"]
                json_obj["wiql"] = {"wiql": temp_wiql}
                update_query(json_obj["wiql"], query_folder, json_obj["name"])
                print("Updated " + json_obj["name"])


def first_2_rows(output_team, url, test_plan, program_name, query_folder,
                 overview_id, global_reqs_path, test_suite_id, starting_column, starting_row, organize_by):
    # region First Widget Row
    url = url.strip()
    tree_link = "\n"

    if url:
        tree_link = " \n [Link To Requirements Tree](" + url + ") "

    # region Main MarkDown
    main_text = "#" + program_name + tree_link + "\n # \n " \
                                                 "#Overall Program Test Status \n #------->"

    main_markdown = return_markdown(starting_column, starting_row, main_text)
    create_widget(output_team, overview_id, main_markdown)
    # endregion

    # region 6 Query Tile
    # Creating All Bugs widget
    starting_column += 1
    name = "All Bugs"
    color = "#fbbc3d"
    query_contains = "All Bugs"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    all_bugs = return_query_tile(starting_column, starting_row, name, query_name, query_id, color)
    create_widget(output_team, overview_id, all_bugs)

    # Creating Dev Bugs widget
    starting_column += 1
    name = "Dev Bugs"
    color = "#e60017"
    query_contains = "Dev Bugs"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    dev_bugs = return_query_tile(starting_column, starting_row, name, query_name, query_id, color)
    create_widget(output_team, overview_id, dev_bugs)

    # Creating New Issues last 24 hours widget
    starting_column += 1
    name = "New Issues"
    color = "#fbbc3d"
    query_contains = "New Issues last 24 hours"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    new_issues_tile = return_query_tile(starting_column, starting_row, name, query_name, query_id, color)
    create_widget(output_team, overview_id, new_issues_tile)

    # Creating Monitored widget
    starting_column -= 2
    starting_row += 1
    name = "Monitored"
    color = "#cccccc"
    query_contains = "Monitored"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    monitored_tile = return_query_tile(starting_column, starting_row, name, query_name, query_id, color)
    create_widget(output_team, overview_id, monitored_tile)

    # Creating RTT widget
    starting_column += 1
    name = "RTT"
    color = "#c9e7e7"
    query_contains = "RTT"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    rtt_tile = return_query_tile(starting_column, starting_row, name, query_name, query_id, color)
    create_widget(output_team, overview_id, rtt_tile)

    # Creating Cannot Reproduce widget
    starting_column += 1
    name = "Cannot Reproduce"
    color = "#fbfd52"
    query_contains = "Cannot Reproduce"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    cannot_reproduce_tile = return_query_tile(starting_column, starting_row, name, query_name, query_id, color)
    create_widget(output_team, overview_id, cannot_reproduce_tile)
    # endregion

    # region Bug Trend
    starting_column += 1
    starting_row -= 1
    name = program_name + " Bug Trend"
    query_id = return_query_id("Dev Bugs", query_folder)
    history = "last12Weeks"

    bug_trend = return_chart(starting_column, starting_row, name, query_id, organize_by, history=history, direction="descending")
    create_widget(output_team, overview_id, bug_trend)
    # endregion

    # region Bug Severity
    starting_column += 2
    name = program_name + " Bug Severity"
    query_id = return_query_id("Dev Bugs", query_folder)
    chart_type = "ColumnChart"

    bug_severity = return_chart(starting_column, starting_row, name, query_id, organize_by, chart_type=chart_type)
    create_widget(output_team, overview_id, bug_severity)
    # endregion

    # region RTT Trend
    starting_column += 2
    name = program_name + " RTT Trend"
    query_id = return_query_id("RTT", query_folder)
    history = "last12Weeks"

    rtt_trend = return_chart(starting_column, starting_row, name, query_id, organize_by, history=history, direction="descending")
    create_widget(output_team, overview_id, rtt_trend)
    # endregion

    # region RTT Severity
    starting_column += 2
    name = "RTT Severity"
    query_id = return_query_id("RTT", query_folder)
    chart_type = "ColumnChart"
    # property_ = "value"

    rtt_severity = return_chart(starting_column, starting_row, name, query_id, organize_by, chart_type=chart_type)
    create_widget(output_team, overview_id, rtt_severity)
    # endregion

    # region Arrival Last 7 Days
    starting_column += 2
    name = program_name + " Arrival Last 7 Days"
    query_id = return_query_id("All created this week", query_folder)
    chart_type = "stackBarChart"
    series = "System.CreatedDate"

    arrival_7_days = return_chart(starting_column, starting_row, name, query_id, organize_by, chart_type=chart_type, series=series)
    create_widget(output_team, overview_id, arrival_7_days)
    # endregion

    # region Resolved Last 7 Days
    starting_column += 2
    name = program_name + " Resolved Last 7 Days"
    query_id = return_query_id("All resolved this week", query_folder)
    chart_type = "stackBarChart"
    series = "Microsoft.VSTS.Common.ResolvedDate"

    sys_features = return_chart(starting_column, starting_row, name, query_id, organize_by, chart_type=chart_type, series=series)
    create_widget(output_team, overview_id, sys_features)
    # endregion

    # region Closed Last 7 Days
    starting_column += 2
    name = program_name + " Closed Last 7 Days"
    query_id = return_query_id("All closed this week", query_folder)
    chart_type = "stackBarChart"
    series = "Microsoft.VSTS.Common.ClosedDate"

    sys_features = return_chart(starting_column, starting_row, name, query_id, organize_by, chart_type=chart_type, series=series)
    create_widget(output_team, overview_id, sys_features)
    # endregion

    # region Fill In with Blank Widgets
    starting_column += 2

    while starting_column <= MAX_COLUMN:
        remainder = min(MAX_COLUMN - starting_column + 2, 10)  # returns the minimum value in the given range
        create_widget(output_team, overview_id, return_blank_square(starting_column, starting_row, remainder))
        starting_column += remainder
    # endregion

    starting_row += 2

    # endregion

    # region Second Row Widgets

    resources_suite = return_suite_child_id("Resource", test_plan,
                                            test_suite_id)
    starting_column = 2
    # if the resources suite is found then create Resource widgets
    if resources_suite != NOT_FOUND:
        # return the child suite within resources
        name = "All New Feature Test Cases (Resources)"
        suite = return_suite_child_id("New", test_plan,
                                      resources_suite)
        new_features = return_test_chart(starting_column, starting_row, name, suite, test_plan)
        create_widget(output_team, overview_id, new_features)
        starting_column += 2

        # region All Manual Regression (Resources)
        name = "All Regression Test Cases"
        suite = return_suite_child_id("Reg", test_plan,
                                      resources_suite)
        new_features = return_test_chart(starting_column, starting_row, name, suite, test_plan)
        create_widget(output_team, overview_id, new_features)
        starting_column += 2
        # endregion

    if ("SQA Test Features" and "SQA Test Features without test cases" in return_query_folder_children(query_folder)) \
            and (global_reqs_path.upper() != "N/A" and global_reqs_path.upper() != "NA"):
        # region SQA Test Features by State
        name = "System Test Features by State (GlobalReqs)"
        query_id = return_query_id("SQA Test Features", query_folder)
        group = "System.State"
        chart_type = "PieChart"
        property_ = "value"
        direction = "descending"
        scope = "WorkitemTracking.Queries"

        sys_features = return_chart(starting_column, starting_row, name, query_id, chart_type=chart_type,
                                    group=group, _property=property_,
                                    direction=direction, scope=scope)
        create_widget(output_team, overview_id, sys_features)
        starting_column += 2
        # endregion

        # region SQA Test Features without test cases
        name = "SQA Test Features without test cases"
        query_title = "SQA Test Features without test cases"
        query_id = return_query_id(query_title, query_folder)

        all_features = return_features_table(starting_column, starting_row, name, query_id)
        create_widget(output_team, overview_id, all_features)
        starting_column += 4
        # endregion
    else:
        no_global_reqs = "No Global Reqs iteration path provided"
        custom_markdown = return_custom_markdown(starting_column, 2, starting_row, no_global_reqs, 2)
        create_widget(output_team, overview_id, custom_markdown)
        starting_column += 2
        custom_markdown = return_custom_markdown(starting_column, 4, starting_row, no_global_reqs, 2)
        create_widget(output_team, overview_id, custom_markdown)
        starting_column += 4

    # region Reported In
    name = "Reported In"
    query_id = return_query_id("Lifetime Bugs", query_folder)
    chart_type = "ColumnChart"
    group = "Custom.ReportedIn"
    _property = "value"
    direction = "descending"

    reported_in = return_chart(starting_column, starting_row, name, query_id, chart_type=chart_type, group=group,
                               _property=_property, direction=direction)
    create_widget(output_team, overview_id, reported_in)
    starting_column += 2
    # endregion

    # region Failed Test by Area Path
    name = "Failed Test by Area Path"
    query_id = return_query_id("Failed Test", query_folder)
    chart_type = "PieChart"
    group = "System.AreaLevel2"
    _property = "value"
    direction = "descending"

    failed_test_chart = return_chart(starting_column, starting_row, name, query_id, chart_type=chart_type, group=group,
                                     _property=_property, direction=direction)
    create_widget(output_team, overview_id, failed_test_chart)

    starting_column += 2
    # endregion

    # region Fill In with Blank Widgets
    while starting_column <= MAX_COLUMN:
        remainder = min(MAX_COLUMN - starting_column + 2, 10)
        create_widget(output_team, overview_id, return_blank_square(starting_column, starting_row, remainder))
        starting_column += remainder
    # endregion
    # endregion


def populate_dash(output_team, url, test_plan, program_name, query_folder,
                  overview_id, global_reqs_path, organize_by, ignore_first_row=False):
    """
        Populates a given dashboard with widgets based on the queries
        in the query folder provided, and the test suites found in the given
        test plan.
    """

    starting_column = 1
    starting_row = 1

    # adds 1 to plan id to get suite id
    test_suite_id = str(int(test_plan) + 1)

    if not ignore_first_row:
        first_2_rows(output_team, url, test_plan, program_name, query_folder,
                     overview_id, global_reqs_path, test_suite_id, starting_column, starting_row, organize_by)
    starting_row += 4

    # region Sprint Row

    # return all children suites of "Sprint" and sort
    sprint_suite = return_suite_child_id("Sprint", test_plan,
                                         test_suite_id)

    if sprint_suite != NOT_FOUND:
        suite_list = return_sprint_child_list(test_plan, sprint_suite)

        # Creates a Sprint Test row per Alpha found in Test Plan tree
        for suite in suite_list:
            suite_id = str(suite['id'])
            suite_name = suite['name']
            starting_column = 1
            count = 0
            # suite_name = Return_Suite_Name(suite_id, testPlanId)
            # region Alpha Markdown
            row_text = "#" + suite_name + "\n#------->"

            row_markdown = return_markdown(starting_column, starting_row, row_text, height=2)
            create_widget(output_team, overview_id, row_markdown)
            starting_column += 1
            count += 1
            # endregion

            # region Test Case Readiness - Alpha
            name = "Test Case Readiness " + suite_name
            test_readiness = return_test_chart(starting_column, starting_row, name,
                                               suite_id, test_plan)
            create_widget(output_team, overview_id, test_readiness)
            starting_column += 2
            count += 1
            # endregion

            # region Alpha Overall
            name = suite_name + " - Overall"
            group = "Outcome"
            test_results = True
            test_readiness = return_test_chart(starting_column, starting_row, name,
                                               suite_id, test_plan, group=group,
                                               test_results=test_results)
            create_widget(output_team, overview_id, test_readiness)
            starting_column += 2
            count += 1
            # endregion

            # create widgets for children suites if found
            child_list = return_suite_child_full(test_plan, suite_id)
            child_count = 0
            for child in child_list:
                if child_count >= 5:
                    break
                else:
                    child_id = str(child['id'])
                    name = child['name']
                child_count += 1

                group = "Outcome"
                test_results = True
                test_readiness = return_test_chart(starting_column, starting_row,
                                                   name, child_id, test_plan,
                                                   group=group,
                                                   test_results=test_results)
                create_widget(output_team, overview_id, test_readiness)
                starting_column += 2
                count += 1
                # endregion

            # region Fill In with Blank Widgets
            while starting_column <= MAX_COLUMN:
                remainder = min(MAX_COLUMN - starting_column + 2, 10)
                create_widget(output_team, overview_id, return_blank_square(starting_column, starting_row, remainder))
                starting_column += remainder
            # endregion

            starting_row += 2  # each widget is of size 2 so we much increment by 2
    # endregion

    # region Early System Test

    # return all children suites of "Early System Test" and sort
    early_system = return_suite_child_id("Early System Test", test_plan,
                                         test_suite_id)

    if early_system != NOT_FOUND:
        suite_list = return_suite_child_list(test_plan, early_system)

        # Creates a Early System Test row per Alpha found in Test Plan tree
        if len(suite_list) > 0:
            for suite in suite_list:
                suite_id = str(suite['id'])
                suite_name = suite['name']
                starting_column = 1
                count = 0
                # region Alpha Markdown
                row_text = "#Early \n #System Test \n ###" + suite_name + "\n#------->"

                row_markdown = return_markdown(starting_column, starting_row, row_text, height=2)
                create_widget(output_team, overview_id, row_markdown)
                starting_column += 1
                count += 1
                # endregion

                # region Test Case Readiness - Alpha
                name = "Test Case Readiness " + suite_name
                test_readiness = return_test_chart(starting_column, starting_row, name,
                                                   suite_id, test_plan)
                create_widget(output_team, overview_id, test_readiness)
                starting_column += 2
                count += 1
                # endregion

                # region Alpha Overall
                name = suite_name + " - Overall"
                group = "Outcome"
                test_results = True
                test_readiness = return_test_chart(starting_column, starting_row, name,
                                                   suite_id, test_plan, group=group,
                                                   test_results=test_results)
                create_widget(output_team, overview_id, test_readiness)
                starting_column += 2
                count += 1
                # endregion

                # create widgets for children suites if found
                child_list = return_suite_child_full(test_plan, suite_id)
                for child in child_list:
                    if starting_column > MAX_COLUMN:
                        break
                    else:
                        child_id = str(child['id'])
                        if "New Feat" in child['name']:
                            # region Alpha - New Features
                            name = suite_name + " - New Features"

                            # endregion
                        elif "Man" in child['name']:
                            # region Alpha  - Manual Regression
                            name = suite_name + "- Manual Regression"
                            # endregion
                        elif "Auto" in child['name']:
                            # region Alpha - Automated Regression
                            name = suite_name + "- Automated Regression"
                        else:
                            name = child['name']

                    group = "Outcome"
                    test_results = True
                    test_readiness = return_test_chart(starting_column, starting_row,
                                                       name, child_id, test_plan,
                                                       group=group,
                                                       test_results=test_results)
                    create_widget(output_team, overview_id, test_readiness)
                    starting_column += 2
                    count += 1
                    # endregion

                # region Fill In with Blank Widgets
                while starting_column <= MAX_COLUMN:
                    remainder = min(MAX_COLUMN - starting_column + 2, 10)
                    create_widget(output_team, overview_id, return_blank_square(starting_column, starting_row, remainder))
                    starting_column += remainder
                # endregion

                starting_row += 2  # each widget is of size 2 so we much increment by 2
    # endregion

    # region System Test
    system_suite_id = return_suite_child_id("System Test", test_plan,
                                            test_suite_id)
    if system_suite_id != NOT_FOUND:
        suite_list = return_suite_child_list(test_plan, system_suite_id)

        # Creates row of System Test widgets for each Run found in System Test
        if len(suite_list) > 0:
            for suite in suite_list:
                suite_id = str(suite['id'])
                suite_name = suite['name']
                starting_column = 1
                count = 0

                # region System Test Markdown
                row_text = "#System Test \n ###" + suite_name + "\n#------->"

                row_markdown = return_markdown(starting_column, starting_row, row_text, height=2)
                create_widget(output_team, overview_id, row_markdown)
                starting_column += 1
                count += 1
                # endregion

                # region System Test - Test Case Readiness
                name = "System Test - Test Case Readiness"
                test_readiness = return_test_chart(starting_column, starting_row, name,
                                                   suite_id, test_plan)
                create_widget(output_team, overview_id, test_readiness)
                starting_column += 2
                count += 1
                # endregion

                # region Overall - System Test
                name = "Overall - System Test"
                group = "Outcome"
                test_results = True
                test_readiness = return_test_chart(starting_column, starting_row,
                                                   name, suite_id, test_plan,
                                                   group=group,
                                                   test_results=test_results)
                create_widget(output_team, overview_id, test_readiness)
                starting_column += 2
                count += 1
                # endregion

                child_list = return_suite_child_full(test_plan, suite_id)
                child_count = 0
                for child in child_list:
                    if child_count >= 5:
                        break
                    else:
                        # region optional widgets
                        child_id = str(child['id'])
                        if "New Feat" in child['name']:
                            # region Run - New Features
                            name = "New Feature - System Test"

                            # endregion
                        elif "Man" in child['name']:
                            # region Run  - Manual Regression
                            name = "Manual Regression - System Test"
                            # endregion
                        elif "Auto" in child['name']:
                            # region Run - Automated Regression
                            name = "Automated Regression - System Test"
                        else:
                            name = child['name']
                    child_count += 1

                    group = "Outcome"
                    test_results = True
                    test_readiness = return_test_chart(starting_column, starting_row,
                                                       name, child_id, test_plan,
                                                       group=group,
                                                       test_results=test_results)
                    create_widget(output_team, overview_id, test_readiness)
                    starting_column += 2
                    count += 1
                    # endregion

                # region Fill In with Blank Widgets
                while starting_column <= MAX_COLUMN:
                    remainder = min(MAX_COLUMN - starting_column + 2, 10)
                    create_widget(output_team, overview_id, return_blank_square(starting_column, starting_row, remainder))
                    starting_column += remainder
                # endregion

                starting_row += 2  # each widget is of size 2 so we much increment by 2
    # endregion

    # region Customer Solution

    customer_solution = return_suite_child_id("Customer Solution", test_plan,
                                              test_suite_id)
    if customer_solution != NOT_FOUND:
        suite_list = return_suite_child_list(test_plan, customer_solution)
        # Creates a row of Customer widgets per Run found in Customer Solution tree
        if len(suite_list) > 0:
            for suite in suite_list:
                suite_id = str(suite['id'])
                suite_name = suite['name']
                starting_column = 1
                count = 0

                # region Customer Solution Markdown
                row_text = "#Customer Solution \n ###" + suite_name + " \n#------->"

                row_markdown = return_markdown(starting_column, starting_row, row_text, height=2)
                create_widget(output_team, overview_id, row_markdown)
                starting_column += 1
                count += 1
                # endregion

                # region Customer Solution - Test Case Readiness
                name = "Customer Solution - Test Case Readiness"
                test_readiness = return_test_chart(starting_column, starting_row, name,
                                                   suite_id, test_plan)
                create_widget(output_team, overview_id, test_readiness)
                starting_column += 2
                count += 1
                # endregion

                # region Overall - Customer Solution
                name = "Overall - Customer Solution"
                group = "Outcome"
                test_results = True
                test_readiness = return_test_chart(starting_column, starting_row, name,
                                                   suite_id, test_plan, group=group,
                                                   test_results=test_results)
                create_widget(output_team, overview_id, test_readiness)
                starting_column += 2
                count += 1
                # endregion

                child_list = return_suite_child_full(test_plan, suite_id)
                child_count = 0
                for child in child_list:
                    if child_count >= 5:
                        break
                    else:
                        # region optional widgets
                        child_id = str(child['id'])
                        if "New Feat" in child['name']:
                            # region Run - New Features
                            name = "New Features - Customer Solution"

                            # endregion
                        elif "Man" in child['name']:
                            # region Run  - Manual Regression
                            name = "Manual Regression - Customer Solution"
                            # endregion
                        elif "Auto" in child['name']:
                            # region Run - Automated Regression
                            name = "Automated Regression - Customer Solution"
                        else:
                            name = child['name']
                    child_count += 1

                    group = "Outcome"
                    test_results = True
                    test_readiness = return_test_chart(starting_column, starting_row,
                                                       name, child_id, test_plan,
                                                       group=group,
                                                       test_results=test_results)
                    create_widget(output_team, overview_id, test_readiness)
                    starting_column += 2
                    count += 1
                    # endregion

                # region Fill In with Blank Widgets
                while starting_column <= MAX_COLUMN:
                    remainder = min(MAX_COLUMN - starting_column + 2, 10)
                    create_widget(output_team, overview_id, return_blank_square(starting_column, starting_row, remainder))
                    starting_column += remainder

                # endregion

                starting_row += 2  # each widget is of size 2 so we much increment by 2
    # endregion

    # region First Article/Final Product
    suite_title = "First Article"
    product_suite = return_suite_child_id(suite_title, test_plan, test_suite_id)

    if product_suite == NOT_FOUND:
        suite_title = "Final Product"
        product_suite = return_suite_child_id(suite_title, test_plan, test_suite_id)

    if product_suite != NOT_FOUND:
        suite_list = return_suite_child_list(test_plan, product_suite)
        # Creates a row of product suite widgets per Run found in product suite tree
        if len(suite_list) > 0:
            for suite in suite_list:
                suite_id = str(suite['id'])
                suite_name = suite['name']
                starting_column = 1
                count = 0

                # region First Article/Final Product Markdown
                row_text = "#" + suite_title + " Test\n ###" + suite_name + " \n#------->"

                row_markdown = return_markdown(starting_column, starting_row, row_text, height=2)
                create_widget(output_team, overview_id, row_markdown)
                starting_column += 1
                count += 1
                # endregion

                # region First Article/Final Product - Test Case Readiness
                name = suite_name + " - Test Case Readiness"
                test_readiness = return_test_chart(starting_column, starting_row, name,
                                                   suite_id, test_plan)
                create_widget(output_team, overview_id, test_readiness)
                starting_column += 2
                count += 1
                # endregion

                # region Overall - First Article/Final Product
                name = "Overall " + suite_name
                group = "Outcome"
                test_results = True
                test_readiness = return_test_chart(starting_column, starting_row, name,
                                                   suite_id, test_plan, group=group,
                                                   test_results=test_results)
                create_widget(output_team, overview_id, test_readiness)
                starting_column += 2
                count += 1
                # endregion

                child_list = return_suite_child_full(test_plan, suite_id)
                child_count = 0
                for child in child_list:
                    if child_count >= 5:
                        break
                    else:
                        # region optional widgets
                        child_id = str(child['id'])
                        if "New Feat" in child['name']:
                            # region Run - New Features
                            name = "New Features " + suite_name

                            # endregion
                        elif "Man" in child['name']:
                            # region Run  - Manual Regression
                            name = "Manual Regression - " + suite_name
                            # endregion
                        elif "Auto" in child['name']:
                            # region Run - Automated Regression
                            name = "Automated Regression - " + suite_name
                        else:
                            name = child['name']
                        child_count += 1

                    group = "Outcome"
                    test_results = True
                    test_readiness = return_test_chart(starting_column, starting_row,
                                                       name, child_id, test_plan,
                                                       group=group,
                                                       test_results=test_results)
                    create_widget(output_team, overview_id, test_readiness)
                    starting_column += 2
                    count += 1
                    # endregion

                # region Fill In with Blank Widgets
                while starting_column <= MAX_COLUMN:
                    remainder = min(MAX_COLUMN - starting_column + 2, 10)
                    create_widget(output_team, overview_id, return_blank_square(starting_column, starting_row, remainder))
                    starting_column += remainder
                # endregion

                starting_row += 2  # each widget is of size 2 so we much increment by 2
    # endregion


def create_config(team_name, url, dash_id, test_plan, folder_name, folder_id, global_path, choices, executive=False):
    """
        Creates JSON object using string arguments unless otherwise specified:
            - team name             - targeted project name or tag flag (bool)
            - URL                   - global reqs iteration path
            - dashboard ID          - targeted project name or tag
            - test plan ID          - [calculated] config version
            - query folder name     - [calculated] time last updated
            - query folder ID       - [optional] executive dashboard flag (bool)
    """
    now = datetime.datetime.now()
    date_string = now.strftime("%m/%d/%Y %H:%M:%S")

    choice1 = choices[0]["choice"]
    choice2 = choices[1]["choice"]
    choice3 = choices[2]["choice"]
    targeted_project1 = choices[0]["project"]
    targeted_project2 = choices[1]["project"]
    targeted_project3 = choices[2]["project"]

    json_config = {
        'teamName': team_name,
        'url': url,
        'dashId': dash_id,
        'testPlan': test_plan,
        'folderName': folder_name,
        'folderId': folder_id,
        'choice1': choice1,
        'choice2': choice2,
        'choice3': choice3,
        'global_path': global_path,
        'targeted_project1': targeted_project1,
        'targeted_project2': targeted_project2,
        'targeted_project3': targeted_project3,
        'version': VERSION,
        'lastUpdate': date_string,
        'executive': executive
    }
    return json_config


def write_config(json_config):
    """
        Writes or overwrites a JSON config to a file using config["folderName] as the file name.
        This is used when performing the update or create dashboard function
    """
    file_directory = CONFIGS_PATH + json_config["folderName"] + '.txt'
    with open(file_directory, 'w') as outfile:
        json.dump(json_config, outfile)


def find_test_plan_id_by_name(test_plan, continuation_token=''):
    """
        Returns test plan ID, calls recursively until the test plan is found or
        there is no more continuation tokens in the rest api response.

        :raises TestPlanError exception if test plan is not found in ADS
        :returns test plan id
    """

    continue_key = 'x-ms-continuationtoken'

    payload = {'api-version': '5.1-preview.1',
               '$expand': 'children',
               'continuationToken': continuation_token
               }
    response = requests.get(URL_HEADER + PROJECT + '/_apis/testplan/plans/?',
                            auth=HTTPBasicAuth(USER, TOKEN), params=payload)
    query_response = response.json()
    for child in query_response["value"]:
        if test_plan in child["name"]:
            return str(child["id"])
    if continue_key not in response.headers._store:
        print(json.dumps(response.json()))
        raise TestPlanError("Test Plan: " + test_plan + " not Found in Azure")
    return find_test_plan_id_by_name(test_plan, response.headers._store[continue_key][1])


def check_test_plan_id(test_plan):
    """
        Checks to see if a test plan with the given id exists, if one is found
        the function raises an exception

        :raises ApiTestIDNotFound exception is the test plan is found
    """
    payload = {'api-version': '5.1-preview.1'}
    response = requests.get(URL_HEADER + PROJECT + '/_apis/testplan/plans/'
                            + str(test_plan) + '?',
                            auth=HTTPBasicAuth(USER, TOKEN), params=payload)
    if response.status_code != 200:
        print(json.dumps(response.json()))
        raise ApiTestIDNotFound("Test Plan ID was not Found in Azure DevOps")


def create_query(json_obj, query_folder):
    """
        Submits the query json object to ADS

    """
    version = {'api-version': '4.1'}
    response = requests.post(URL_HEADER + PROJECT + '/_apis/wit/queries/'
                             + query_folder + '?',
                             auth=HTTPBasicAuth(USER, TOKEN), json=json_obj,
                             params=version)
    print(response.json())


def return_markdown(column, row, text, height=4):
    """
        Returns a standard size markdown with the given text

        :return markdown object
    """
    main_markdown = return_widget_obj("Markdown")
    main_markdown["settings"] = text
    main_markdown["size"]["columnSpan"] = 1
    main_markdown["size"]["rowSpan"] = height
    main_markdown["position"]["column"] = column
    main_markdown["position"]["row"] = row

    return main_markdown


def return_custom_markdown(column, width, row, text, height):
    """
        Returns a non-standard markdown with the given parameters

        :return markdown object
    """
    custom_markdown = return_widget_obj("Markdown")
    custom_markdown["settings"] = text
    custom_markdown["size"]["columnSpan"] = width
    custom_markdown["size"]["rowSpan"] = height
    custom_markdown["position"]["column"] = column
    custom_markdown["position"]["row"] = row

    return custom_markdown


def create_widget(output_team, overview_id, dash_board_obj):
    """
        Creates a widget to a dashboard
    """
    version = {'api-version': '4.1-preview.2'}
    response = requests.post(URL_HEADER + PROJECT + '/' + output_team
                             + '/_apis/dashboard/dashboards/' + overview_id
                             + '/widgets?', auth=HTTPBasicAuth(USER, TOKEN),
                             json=dash_board_obj, params=version)
    js = response.json()

    print("Object Returned:")
    print(json.dumps(js))


def return_query_name(name, folder):
    """
        Returns the query name of a query if it is found in the given folder

        :returns query id if found, if not found returns NotFound variable
    """
    payload = {'api-version': '4.1',
               '$expand': 'clauses',
               '$depth': 1
               }
    response = requests.get(URL_HEADER + PROJECT + '/_apis/wit/queries/'
                            + folder + '?', auth=HTTPBasicAuth(USER, TOKEN),
                            params=payload)
    query_response = response.json()
    for child in query_response["children"]:
        if name in child["name"]:
            return child["name"]
    return NOT_FOUND


def return_query_id(name, folder):
    """
        Returns the query id of a query if it is found in the given folder

        :returns query id if found, if not found returns NotFound variable
    """
    payload = {'api-version': '4.1',
               '$expand': 'clauses',
               '$depth': 1
               }
    response = requests.get(URL_HEADER + PROJECT + '/_apis/wit/queries/'
                            + folder + '?', auth=HTTPBasicAuth(USER, TOKEN),
                            params=payload)
    query_response = response.json()
    for child in query_response["children"]:
        if name in child["name"]:
            if (name == "SQA Test Features") and (name != child['name']):
                continue
            return child["id"]
    return NOT_FOUND


def return_query_tile(column, row, name, query_name, query_id, color):
    """
        Returns a query tile widget
    """
    query_tile = return_widget_obj("QueryTile")
    query_tile["name"] = name
    query_tile["size"]["columnSpan"] = 1
    query_tile["size"]["rowSpan"] = 1
    query_tile["position"]["column"] = column
    query_tile["position"]["row"] = row
    del query_tile["settings"]["lastArtifactName"]
    query_tile["settings"]["defaultBackgroundColor"] = color
    # Getting query settings
    query_tile["settings"]["queryName"] = query_name
    query_tile["settings"]["queryId"] = query_id
    query_tile["settings"] = json.dumps(query_tile["settings"])
    print("Object Sent:")
    print(json.dumps(query_tile))

    return query_tile


def return_chart(column, row, name, query_id, organize_by="severity", chart_type="StackAreaChart",
                 aggregation="count", group="Microsoft.VSTS.Common.Severity",
                 _property="label", direction="ascending", series="",
                 history="", scope=""):
    """
        Creates a chart widget

        :returns the json template for the chart
    """
    if (row < 2) and (organize_by == "severity"):
        option = "Microsoft.VSTS.Common.Severity"
    elif (row < 2) and (organize_by == "priority"):
        option = "Microsoft.VSTS.Common.Priority"
    else:
        option = group

    chart = return_widget_obj("Chart")
    chart["name"] = name
    chart["size"]["columnSpan"] = 2
    chart["size"]["rowSpan"] = 2
    chart["position"]["column"] = column
    chart["position"]["row"] = row

    settings = json.loads(standardChartSettings)
    settings["chartType"] = chart_type
    settings["groupKey"] = query_id
    settings["transformOptions"]["filter"] = query_id
    settings["userColors"] = standardRNDWitColorArray
    settings["transformOptions"]["measure"]["aggregation"] = aggregation
    settings["transformOptions"]["groupBy"] = option
    settings["transformOptions"]["orderBy"]["propertyName"] = _property
    settings["transformOptions"]["orderBy"]["direction"] = direction
    settings["transformOptions"]["series"] = series
    settings["transformOptions"]["historyRange"] = history
    settings["scope"] = scope

    chart["settings"] = json.dumps(settings)
    print(chart)

    return chart


def return_suite_child_id(suite_name, test_plan, suite_id):
    """
        Returns the id of a child suite if it contains the suite_name provided

        :return child id if found, if not found returns NotFound variable
    """
    payload = {'api-version': '5.1-preview.1',
               'expand': 'children'
               }
    response = requests.get(URL_HEADER + PROJECT + '/_apis/testplan/plans/'
                            + test_plan + '/suites/' + suite_id + '?',
                            auth=HTTPBasicAuth(USER, TOKEN), params=payload)
    query_response = response.json()
    for child in query_response["children"]:
        if child["name"].startswith(suite_name):
            return str(child["id"])
        elif (suite_name in child["name"]) and suite_name != "System Test":
            return str(child["id"])
    return NOT_FOUND


def return_blank_square(column, row, column_span, name=" "):
    """
        Returns a json template for each widget type

        Optional parameter name for markdown text

        :return json template for a blank markdown
    """
    blank_square = return_widget_obj("Markdown")
    blank_square["settings"] = name
    blank_square["size"]["columnSpan"] = column_span
    blank_square["size"]["rowSpan"] = 2
    blank_square["position"]["column"] = column
    blank_square["position"]["row"] = row

    return blank_square


def return_test_chart(column, row, name, suite, test_plan,
                      group="System.State", test_results=False):
    """
        Creates a test chart object based on parameters

        :return test chart object
    """
    # if the test_results parameter is provided, either Execution or Authoring
    # will be selected for the chart data source
    if test_results:
        chart_for = "&chartDataSource=execution"  # for test result charts
    else:
        chart_for = "&chartDataSource=authoring"  # for test case charts

    test_chart = return_widget_obj("TestChart")
    test_chart["name"] = name
    test_chart["size"]["columnSpan"] = 2
    test_chart["size"]["rowSpan"] = 2
    test_chart["position"]["column"] = column
    test_chart["position"]["row"] = row

    settings = json.loads(standardChartSettings)
    settings["chartType"] = "PieChart"
    settings["groupKey"] = suite
    settings["scope"] = "TestManagement.Reports"
    settings["transformOptions"]["filter"] = "planId=" + test_plan + \
                                             "&suiteId=" + suite + chart_for
    settings["transformOptions"]["groupBy"] = group
    settings["transformOptions"]["orderBy"]["direction"] = "descending"
    settings["transformOptions"]["orderBy"]["propertyName"] = "value"
    settings["transformOptions"]["measure"]["propertyName"] = "Tests"
    settings["transformOptions"]["measure"]["aggregation"] = "count"
    settings["userColors"] = standardTestPlanWitColorArray

    test_chart["settings"] = json.dumps(settings)
    print("Object Sent:")
    print(json.dumps(test_chart))

    return test_chart


def return_features_table(column, row, name, query):
    """
        Returns a query object with the the Features settings
    """
    table = return_widget_obj("Query")
    table["name"] = name
    table["size"]["columnSpan"] = 4
    table["size"]["rowSpan"] = 2
    table["position"]["column"] = column
    table["position"]["row"] = row
    del table["settings"]["lastArtifactName"]
    table["settings"]["query"]["queryId"] = query
    table["settings"]["selectedColumns"] = features_dictionary
    table["settings"] = json.dumps(table["settings"])
    print("Object Sent:")
    print(json.dumps(table))

    return table


def return_suite_child_list(test_plan, suite_id):
    """
        Returns the given suite's children suites in a list if they contain
        one of the row trigger phrases ('Alpha', 'Beta', 'Run')

        Returns an empty list if there are no children

        :return list of child suites
    """
    child_list = []

    trigger_list = ['Alpha', 'Beta', 'Run', 'Sprint']

    payload = {'api-version': '5.1-preview.1',
               'expand': 'children'
               }
    response = requests.get(URL_HEADER + PROJECT + '/_apis/testplan/plans/'
                            + test_plan + '/suites/' + suite_id + '?',
                            auth=HTTPBasicAuth(USER, TOKEN), params=payload)
    query_response = response.json()

    # Check the query_response for the 'children' attribute before iterating
    if 'children' in query_response:
        for child in query_response['children']:
            if any(trigger.upper() in child['name'].upper() for trigger in trigger_list):
                child_list.append(child)
        child_list = sorted(child_list, key=lambda name: child['name'])

    return child_list


def return_sprint_child_list(test_plan, suite_id):
    """
        Returns the given suite's children suites in a list if they contain
        one of the row trigger phrases ('Alpha', 'Beta', 'Run')

        :return list of child suites
    """
    child_list = []

    trigger_list = ['Alpha', 'Beta', 'Run', 'Sprint']

    payload = {'api-version': '5.1-preview.1',
               'expand': 'children'
               }
    response = requests.get(URL_HEADER + PROJECT + '/_apis/testplan/plans/'
                            + test_plan + '/suites/' + suite_id + '?',
                            auth=HTTPBasicAuth(USER, TOKEN), params=payload)
    query_response = response.json()

    for child in query_response['children']:
        if any(trigger in child['name'] for trigger in trigger_list):
            child_list.append(child)

    return child_list


def return_suite_child_full(test_plan, suite_id):
    """
        Returns the full list of child suites

        :returns the list of children suites
    """
    child_list = []

    payload = {'api-version': '5.1-preview.1',
               'expand': 'children'
               }
    response = requests.get(URL_HEADER + PROJECT + '/_apis/testplan/plans/'
                            + test_plan + '/suites/' + suite_id + '?',
                            auth=HTTPBasicAuth(USER, TOKEN), params=payload)
    query_response = response.json()

    if 'children' in query_response:
        for child in query_response['children']:
            child_list.append(child)
        child_list = sort_child_list(child_list)
    return child_list


def return_widget_obj(_type):
    """
        Creates a standard JSON template for the object type given
        :return: JSON template
    """

    if _type == "Markdown":  # standard json template for markdown object
        markdown_obj = {
            "configurationContributionRelativeId": "Microsoft.VisualStudioOnline.Dashboards.MarkdownWidget.Configuration",
            "contributionId": "ms.vss-dashboards-web.Microsoft.VisualStudioOnline.Dashboards.MarkdownWidget",
            "settingsVersion": {
                "minor": 0,
                "major": 1,
                "patch": 0
            },
            "name": "Markdown",
            "size": {
                "columnSpan": 10,
                "rowSpan": 1
            },
            "settings": "# You forgot to update it HH\n#Program: TEMPLATE  \n",
            "contentUri": 'null',
            "loadingImageUrl": "https://dev.azure.com/itron/_static/Widgets/markdownLoading.png",
            "typeId": "Microsoft.VisualStudioOnline.Dashboards.MarkdownWidget",
            "configurationContributionId": "ms.vss-dashboards-web.Microsoft.VisualStudioOnline.Dashboards.MarkdownWidget.Configuration",
            "artifactId": "",
            "position": {
                "column": 2,
                "row": 1
            },
            "lightboxOptions": {
                "height": 500,
                "resizable": 'true',
                "width": 600
            }
        }

        return markdown_obj

    if _type == "Chart":  # standard json template for chart object
        pie_chart_effort = {
            "loadingImageUrl": "https://dev.azure.com/itron/_static/Widgets/ChartLoading.png",
            "typeId": "Microsoft.VisualStudioOnline.Dashboards.WitChartWidget",
            "name": "Feature ROM Totals by Team",
            "position": {
                "column": 2,
                "row": 2
            },
            "contributionId": "ms.vss-dashboards-web.Microsoft.VisualStudioOnline.Dashboards.WitChartWidget",
            "configurationContributionId": "ms.vss-dashboards-web.Microsoft.VisualStudioOnline.Dashboards.WitChartWidget.Configuration",
            "settingsVersion": {
                "minor": 0,
                "patch": 0,
                "major": 3
            },
            "lightboxOptions": {
                "height": 700,
                "resizable": "true",
                "width": 900
            },
            "size": {
                "rowSpan": 3,
                "columnSpan": 4
            },
            "artifactId": "",
            "contentUri": "null",
            "configurationContributionRelativeId": "Microsoft.VisualStudioOnline.Dashboards.WitChartWidget.Configuration"
        }
        return pie_chart_effort

    if _type == "StackChart":  # standard json template for stack chart object
        stack_chart_obj = {
            "contributionId": "ms.vss-dashboards-web.Microsoft.VisualStudioOnline.Dashboards.WitChartWidget",

            "position": {
                "row": 1,
                "column": 4
            },
            "configurationContributionId": "ms.vss-dashboards-web.Microsoft.VisualStudioOnline.Dashboards.WitChartWidget.Configuration",
            "name": "Bug Trend",
            "configurationContributionRelativeId": "Microsoft.VisualStudioOnline.Dashboards.WitChartWidget.Configuration",
            "size": {
                "rowSpan": 2,
                "columnSpan": 2
            },
            "settings": {
                "chartType": "StackAreaChart",
                "groupKey": "cf5a33f5-57e1-4429-a078-3d9dc25e783e",
                "scope": "WorkitemTracking.Queries",
                "title": "Bug Trend",
                "transformOptions": {
                    "filter": "cf5a33f5-57e1-4429-a078-3d9dc25e783e",
                    "groupBy": "Microsoft.VSTS.Common.Severity",
                    "orderBy": {
                        "propertyName": "label",
                        "direction": "ascending"
                    },
                    "measure": {
                        "aggregation": "count",
                        "propertyName": ""
                    },
                    "historyRange": "last12Weeks"
                },
                "userColors": [
                    {
                        "value": "1 - Critical",
                        "backgroundColor": "#e60017"
                    },
                    {
                        "value": "4 - Low",
                        "backgroundColor": "#339947"
                    },
                    {
                        "value": "2 - High",
                        "backgroundColor": "#f58b1f"
                    },
                    {
                        "value": "3 - Medium",
                        "backgroundColor": "#3f9bd8"
                    }
                ],
                "lastArtifactName": "All Bugs by Severity"
            },
            "settingsVersion": {
                "major": 3,
                "minor": 0,
                "patch": 0
            },
            "typeId": "Microsoft.VisualStudioOnline.Dashboards.WitChartWidget",
            "loadingImageUrl": "https://dev.azure.com/itron/_static/Widgets/ChartLoading.png",
            "lightboxOptions": {
                "width": 900,
                "height": 700,
            }
        }
        return stack_chart_obj

    if _type == "TestChart":  # standard json template for test chart object
        test_pie_obj = {
            "loadingImageUrl": "https://dev.azure.com/itron/_static/Widgets/ChartLoading.png",
            "typeId": "Microsoft.VisualStudioOnline.Dashboards.TcmChartWidget",
            "name": "Feature ROM Totals by Team",
            "position": {
                "column": 2,
                "row": 2
            },
            "contributionId": "ms.vss-dashboards-web.Microsoft.VisualStudioOnline.Dashboards.TcmChartWidget",
            "configurationContributionId": "ms.vss-dashboards-web.Microsoft.VisualStudioOnline.Dashboards.TcmChartWidget.Configuration",
            "settingsVersion": {
                "minor": 0,
                "patch": 0,
                "major": 3
            },
            "lightboxOptions": {
                "height": 700,
                "resizable": "true",
                "width": 900
            },
            "size": {
                "rowSpan": 3,
                "columnSpan": 4
            },
            "artifactId": "",
            "contentUri": "null",
            "configurationContributionRelativeId": "Microsoft.VisualStudioOnline.Dashboards.WitChartWidget.Configuration"
        }

        return test_pie_obj

    if _type == "Query":  # standard json template for query object
        query_obj = {
            "contributionId": "ms.vss-mywork-web.Microsoft.VisualStudioOnline.MyWork.WitViewWidget",
            "position": {
                "row": 6,
                "column": 6
            },
            "configurationContributionId": "ms.vss-mywork-web.Microsoft.VisualStudioOnline.MyWork.WitViewWidget.Configuration",
            "name": "Features for AREAPATH Team",
            "configurationContributionRelativeId": "Microsoft.VisualStudioOnline.MyWork.WitViewWidget.Configuration",
            "size": {
                "columnSpan": 4,
                "rowSpan": 2
            },
            "loadingImageUrl": "https://dev.azure.com/itron/_static/MyWork/queryResultsLoading.png",
            "typeId": "Microsoft.VisualStudioOnline.MyWork.WitViewWidget",
            "settings": {
                "lastArtifactName": "TeamFeature_GlobalReqs_OWOC-CM_Query for - DaVinci_MR1",
                "query": {
                    "queryId": "621d2d8c-0e88-4a2b-83f7-86751574dd66",
                    "queryName": "TeamFeature_GlobalReqs_OWOC-CM_Query for - DaVinci_MR1"
                },
                "selectedColumns": [
                    {
                        "referenceName": "System.Title",
                        "name": "Title"
                    },
                    {
                        "referenceName": "System.AssignedTo",
                        "name": "Assigned To"
                    },
                    {
                        "referenceName": "System.State",
                        "name": "State"
                    },
                    {
                        "referenceName": "Microsoft.VSTS.Scheduling.Effort",
                        "name": "Effort"
                    }
                ]
            },
            "settingsVersion": {
                "patch": 0,
                "major": 1,
                "minor": 0
            }
        }
        return query_obj

    if _type == "QueryTile":  # standard json template for query tile object

        query_obj = {
            "contributionId": "ms.vss-dashboards-web.Microsoft.VisualStudioOnline.Dashboards.QueryScalarWidget",
            "position": {
                "row": 1,
                "column": 2
            },
            "configurationContributionId": "ms.vss-dashboards-web.Microsoft.VisualStudioOnline.Dashboards.QueryScalarWidget.Configuration",
            "name": "Features for AREAPATH Team",
            "configurationContributionRelativeId": "Microsoft.VisualStudioOnline.Dashboards.QueryScalarWidget.Configuration",
            "size": {
                "columnSpan": 1,
                "rowSpan": 1
            },
            "loadingImageUrl": "https://dev.azure.com/itron/_static/Widgets/scalarLoading.png",
            "typeId": "Microsoft.VisualStudioOnline.Dashboards.QueryScalarWidget",
            "settings": {
                "defaultBackgroundColor": "#fbbc3d",
                "queryId": "94d32c67-eaf8-42fe-b2f9-4919a32ffe81",
                "queryName": "PEA1.5 All Bugs",
                "colorRules": [],
                "lastArtifactName": "PEA1.5 All Bugs"
            },
            "settingsVersion": {
                "patch": 0,
                "major": 1,
                "minor": 0
            }
        }
        return query_obj


def sort_child_list(child_list):
    """
        Sorts the child list adding New Features, Manual, and Automated test
        suites in the front of hte list

        :return sorted child list
    """
    sorted_dictionary = {0: list(), 1: list(), 2: list(), 3: list(), 4: list(),
                         5: list(), 6: list()}

    if len(child_list) <= 1:
        return child_list
    else:
        for child in child_list:
            name = child['name']
            if "New Feat" in name:
                sorted_dictionary[0].append(child)
            elif "Man" in name:
                sorted_dictionary[1].append(child)
            elif "Auto" in name:
                sorted_dictionary[2].append(child)
            elif "Meter Farm" in name:
                sorted_dictionary[3].append(child)
            elif "Garden" in name:
                sorted_dictionary[4].append(child)
            elif "SVE" in name:
                sorted_dictionary[5].append(child)
            else:
                sorted_dictionary[6].append(child)

    del child_list[:]
    for key in sorted_dictionary:
        if sorted_dictionary[key]:
            items = sorted_dictionary[key]
            for item in items:
                child_list.append(item)

    return child_list
# endregion

# region Update Dashboard


def get_config():
    """
        Returns a json object of all dashboard config files
        :return: config_data
    """
    directory = CONFIGS_PATH
    file_path = os.listdir(directory)
    file_path.sort()
    config_data = []
    for file in file_path:
        file1 = directory + file
        no_data = {"folderName": file + " -- CONFIG IS EMPTY --"}
        with open(file1, 'r') as json_file:
            if os.stat(file1).st_size == 0:  # Checks if dashboard config file is empty
                config_data.append(no_data)
            else:
                config_data.append(json.load(json_file))
    return config_data


def get_selected_config(selected_file):
    """
        Returns the config for a selected dashboard in a json object
        :param selected_file:
        :return config_data:
    """
    directory = CONFIGS_PATH
    config_data = []
    file = directory + selected_file + ".txt"
    with open(file, 'r') as json_file:
        items = json.load(json_file)
        config_data.append(items)
    return config_data


def delete_widget(team_name, widget_id, dashboard_id):
    """
        Removes a widget from the dashboard
    """
    version = {'api-version': '5.1-preview.2'}
    response = requests.delete(URL_HEADER + PROJECT + '/' + team_name
                               + '/_apis/dashboard/dashboards/' + dashboard_id
                               + '/widgets/' + widget_id + '?',
                               auth=HTTPBasicAuth(USER, TOKEN), params=version)
    js = response.json()
    print("Object Deleted: ")
    print(json.dumps(js))


def clear_dash(team_name, dashboard_id, ignore_first_row=False):
    """
        Clears all widgets from a dashboard
    """
    version = {'api-version': '4.1-preview.2'}
    response = requests.get(URL_HEADER + PROJECT + '/' + team_name
                            + '/_apis/dashboard/dashboards/' + dashboard_id
                            + '?', auth=HTTPBasicAuth(USER, TOKEN),
                            params=version)
    if response.status_code != 200:
        print(json.dumps(response.json()))
        raise DashDoesNotExists("Dashboard with the selected name does not exist")

    dash_response = response.json()
    for widget in dash_response["widgets"]:
        if ignore_first_row:
            print("Ignoring first 2 widget rows")
            if widget["position"]["row"] not in [1, 2, 3]:
                print(widget["id"])
                delete_widget(team_name, widget["id"], dashboard_id)
        else:
            print(widget["id"])
            delete_widget(team_name, widget["id"], dashboard_id)
    print("Dashboard cleared")


def return_query_folder_children(folder):
    payload = {'api-version': '4.1',
               '$expand': 'clauses',
               '$depth': 1
               }
    response = requests.get(URL_HEADER + PROJECT + '/_apis/wit/queries/'
                            + folder + '?', auth=HTTPBasicAuth(USER, TOKEN),
                            params=payload)
    if response.status_code != 200:
        print(json.dumps(response.json()))
        raise QueryFolderNotFound
    query_response = response.json()
    queries = []
    for child in query_response["children"]:
        queries.append(child["name"])

    return queries


def update_query(json_obj, query_folder, query_name):
    """
        Submits the query json object to ADS

        This function should only be called if the query exists.

    """
    version = {'api-version': '6.0'}
    query_id = return_query_id(query_name, query_folder)

    wiql_response = requests.patch(URL_HEADER + PROJECT + '/_apis/wit/queries/'
                              + query_id + '?',
                              auth=HTTPBasicAuth(USER, TOKEN), json=json_obj,
                              params=version)
    if wiql_response.status_code != 200:
        print(wiql_response.status_code, wiql_response.reason)
        raise QueryUpdateError("Error updating query: " + str(wiql_response.reason))
    print("-----------------------------")


def update_dash(file, choices, organize_by, ignore_first_row):
    """
        Updates a dashboard based on the given dashboard config file
    """
    print(os.curdir)
    print(file)
    file_directory = CONFIGS_PATH + file + '.txt'
    with open(file_directory, 'r') as json_file:
        config_data = json.load(json_file)
        team_name = config_data['teamName']
        url = config_data['url']
        dash_id = config_data['dashId']
        test_plan = config_data['testPlan']
        global_reqs_path = config_data['global_path']
        folder_name = config_data['folderName']
        query_folder = config_data['folderId']

    if not ignore_first_row:
        populate_baseline_query_folder(query_folder, global_reqs_path, choices, first_time=False)

    clear_dash(team_name, dash_id, ignore_first_row)
    populate_dash(team_name, url, test_plan, folder_name, query_folder, dash_id, global_reqs_path, organize_by, ignore_first_row)

    print("Dashboard Updated")

    now = datetime.datetime.now()
    localtime = reference.LocalTimezone()
    date_string = now.strftime("%m/%d/%Y %H:%M:%S, " + localtime.tzname(now))
    with open(file_directory, 'w') as outfile:
        config_data['lastUpdate'] = date_string
        json.dump(config_data, outfile)


# endregion


# region Update Agile Test Plan
def get_agile_config():
    """
        Returns a json object of all agile test plan configs
        :return: config_data
    """
    config_data = []

    try:
        with open(AGILE_PATH, 'r') as json_file:
            config_data = json.load(json_file)
    except FileNotFoundError:
        file = open(AGILE_PATH, 'w+')
        file.close()
    except ValueError:  # json loads fails on empty file
        pass
    return config_data


def get_waterfall_config():
    """
        Returns a json object of all waterfall test plan configs
        :return: config_data
    """
    config_data = []

    try:
        with open(WATERFALL_PATH, 'r') as json_file:
            config_data = json.load(json_file)
    except FileNotFoundError:
        file = open(WATERFALL_PATH, 'w+')
        file.close()
    except ValueError:  # json loads fails on empty file
        pass
    return config_data


def add_sprint_suite(test_plan_id, suite_id, current_sprint, child_suites):
    """
        Creates the second tier child suites for Customer Solutions
    """
    sprints = ["Sprint " + str(current_sprint)]
    for suite_name in sprints:
        row_id = create_suite(suite_name + DATE_FORMAT, test_plan_id, suite_id)
        create_customer_children(test_plan_id, row_id, child_suites)
        create_children_suites(test_plan_id, row_id, child_suites)


def update_agile_plan(selected, child_suites):
    now = datetime.datetime.now()
    date_string = now.strftime("%m/%d/%Y %H:%M:%S")
    test_plan = ''
    current_sprint = CURRENT_SPRINT_DEFAULT

    agile_config = get_agile_config()

    for config in agile_config:
        if str(config['sprints_suite']) == str(selected):
            current_sprint = int(config['current_sprint'])
            current_sprint += 1
            config['current_sprint'] = str(current_sprint)
            config['lastUpdate'] = date_string
            test_plan = config['test_plan_id']
            break

    add_sprint_suite(test_plan, selected, current_sprint, child_suites)

    with open(AGILE_PATH, 'w') as outfile:
        json.dump(agile_config, outfile)
# endregion


# region Executive Dashboard
def update_executive(check_list):
    """
        Updates the executive dashboard
    """
    print("\nUpdating Executive Dashboard...\n")
    row = 1

    update_executive_config(check_list)  # update the existing config
    dash_data = get_config()
    # get a list of agile test plan ids
    agile_config = get_agile_config()
    agile_plan_ids = []
    for plan in agile_config:
        agile_plan_ids.append(str(plan['test_plan_id']))

    clear_dash(GTO, EXECUTIVE_ID)

    for dash in dash_data:  # creates a row for each valid dashboard
        team_name = dash['teamName']
        dash_id = dash['dashId']
        dash_name = dash['folderName']
        query_folder = dash['folderId']
        executive = dash['executive']

        if executive and dashboard_exists(team_name, dash_id):
            print("Adding executive row for " + dash_name)
            # check if this dashboard's test plan is an agile plan
            add_executive_row(dash_name, dash_id, query_folder, row)

            row += 2


def update_executive_config(check_list):
    """
        Updates the executive dashboard configs with the selections from the GUI
    """
    directory = CONFIGS_PATH
    file_path = os.listdir(directory)
    file_path.sort()
    config_data = []
    for file in file_path:  # loads json file
        file1 = directory + file
        with open(file1, 'r') as json_file:
            config_data = json.load(json_file)

        with open(file1, 'w') as outfile:  # updates and writes json object
            config_data['executive'] = check_list[config_data['dashId']]
            json.dump(config_data, outfile)


def add_executive_row(dash_name, dash_id, query_folder, row):
    """
        Adds the row to the executive dashboard
    """

    # markdown widget with link to original dashboard
    main_text = "#[" + dash_name + "](" + DASH_HEADER + dash_id + ") "

    main_markdown = return_markdown(1, row, main_text, height=2)
    create_widget(GTO, EXECUTIVE_ID, main_markdown)

    add_four_square(query_folder, GTO, EXECUTIVE_ID, row)


def add_four_square(query_folder, output_team, overview_id, row):
    """
        Adds the Bugs charts to a dashboard
    """
    # region 4 Query Tile
    # Creating All Bugs widget
    name = "All Bugs"
    color = "#fbbc3d"
    query_contains = "All Bugs"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    all_bugs = return_query_tile(2, row, name, query_name, query_id, color)
    create_widget(output_team, overview_id, all_bugs)

    # Creating Dev Bugs widget
    name = "Dev Bugs"
    color = "#e60017"
    query_contains = "Dev Bugs"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    dev_bugs = return_query_tile(3, row, name, query_name, query_id, color)
    create_widget(output_team, overview_id, dev_bugs)

    # Increment row
    row += 1

    # Creating Monitored widget
    name = "Monitored"
    color = "#cccccc"
    query_contains = "Monitored"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    monitored_tile = return_query_tile(2, row, name, query_name, query_id, color)
    create_widget(output_team, overview_id, monitored_tile)

    # Creating RTT widget
    name = "RTT"
    color = "#c9e7e7"
    query_contains = "RTT"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    rtt_tile = return_query_tile(3, row, name, query_name, query_id, color)
    create_widget(output_team, overview_id, rtt_tile)
    # endregion


def dashboard_exists(output_team, overview_id):
    """
        Checks is a dashboard exists
    """
    print("team: " + output_team)
    print("id: " + overview_id)
    version = {'api-version': '5.1-preview.2'}
    response = requests.get(URL_HEADER + PROJECT + '/' + output_team
                             + '/_apis/dashboard/dashboards/' + overview_id
                             + '/widgets?', auth=HTTPBasicAuth(USER, TOKEN), params=version)

    print("Object Returned:" + str(response.status_code))

    if response.status_code != 200:
        print(json.dumps(response.json()))
        return False

    return True


# endregion
