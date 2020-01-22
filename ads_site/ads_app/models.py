from django.conf import settings
import datetime
from requests.auth import HTTPBasicAuth
import os
import json
import requests


# reading in token credentials for user
CONFIGS_PATH = settings.BASE_DIR + r'/ads_app/static/Dashboard configs/'
TOKEN_PATH = settings.BASE_DIR + r'/ads_app/static/token.txt'
with open(TOKEN_PATH, 'r') as TOKEN_FILE:
    USER = TOKEN_FILE.readline().strip()
    TOKEN = TOKEN_FILE.readline().strip()

# setting class level variables
PROJECT = "RnD"
NOT_FOUND = "not found"
JSON_ERROR = "json error"
MAX_ROW = 7  # maximum number of widgets per row
VERSION = 'v0.1'  # Application Version
URL_HEADER = 'https://dev.azure.com/itron/'
PMO_PATH = settings.BASE_DIR + r'/ads_app/static/PMO_List.txt'


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
    """Query Folder already Exists"""

# endregion

# region Create Test Plan
def get_pmo_list():
    """
        returns the pmo list from the file in the pmo_path
    """

    with open(PMO_PATH, 'r') as lines:
        pmo_list = lines.readlines()

    return pmo_list


def create_full_test_plan(test_plan):
    """
        Creates a test plan based on the name given
        :return test plan ID
    """
    create_iteration(test_plan)  # creates iteration
    test_plan_id = create_test_plan(test_plan)
    suite_id = str(int(test_plan_id) + 1)

    # region First Article
    suite_name = "First Article Test"
    first_article = create_suite(suite_name, test_plan_id, suite_id)
    # create two child template suites for first Article
    suite_name = "<product> - Run 1"
    create_suite(suite_name, test_plan_id, first_article)
    create_suite(suite_name, test_plan_id, first_article)
    # endregion

    # region Customer Solution
    suite_name = "Customer Solution Test"
    customer_suite = create_suite(suite_name, test_plan_id, suite_id)
    create_customer_suite_runs(test_plan_id, customer_suite)
    # endregion

    # region System Test
    suite_name = "System Test"
    system_test = create_suite(suite_name, test_plan_id, suite_id)
    create_suite_runs(test_plan_id, system_test)
    # endregion

    # region Early System Test
    suite_name = "Early System Test"
    early_system = create_suite(suite_name, test_plan_id, suite_id)
    create_early_system_children(test_plan_id, early_system)
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
        raise DashAlreadyExists("Test Plan with name " + test_plan
                                + " already exists")

    print(json.dumps(test_plan_response))
    print(test_plan_response["id"])
    return test_plan_response["id"]


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

    # indicates that a test plan with suite name already exists
    if response.status_code != 200:
        raise DashAlreadyExists("Test Plan with name " + suite_name
                                + " already exists")

    print(json.dumps(suite_response))
    print(suite_response["value"][0]["id"])
    return suite_response["value"][0]["id"]


def create_suite_runs(test_plan_id, suite_id):
    """
        Creates second tier child suites
    """
    suite_name = "Run 3"
    row_id = create_suite(suite_name, test_plan_id, suite_id)
    create_children_suites(test_plan_id, row_id)
    suite_name = "Run 2"
    row_id = create_suite(suite_name, test_plan_id, suite_id)
    create_children_suites(test_plan_id, row_id)
    suite_name = "Run 1"
    row_id = create_suite(suite_name, test_plan_id, suite_id)
    create_children_suites(test_plan_id, row_id)


def create_customer_suite_runs(test_plan_id, suite_id):
    """
        Creates the second tier child suites for Customer Solutions
    """
    suite_name = "Run 3"
    row_id = create_suite(suite_name, test_plan_id, suite_id)
    create_customer_children(test_plan_id, row_id, suite_name)
    suite_name = "Run 2"
    row_id = create_suite(suite_name, test_plan_id, suite_id)
    create_customer_children(test_plan_id, row_id, suite_name)
    suite_name = "Run 1"
    row_id = create_suite(suite_name, test_plan_id, suite_id)
    create_customer_children(test_plan_id, row_id, suite_name)


def create_early_system_children(test_plan_id, suite_id):
    """
        Creates the second tier child suites for Early System Test
    """
    suite_name = "Beta 1/Feature Complete"
    row_id = create_suite(suite_name, test_plan_id, suite_id)
    create_children_suites(test_plan_id, row_id)
    suite_name = "Alpha 3"
    row_id = create_suite(suite_name, test_plan_id, suite_id)
    create_children_suites(test_plan_id, row_id)
    suite_name = "Alpha 2"
    row_id = create_suite(suite_name, test_plan_id, suite_id)
    create_children_suites(test_plan_id, row_id)
    suite_name = "Alpha 1"
    row_id = create_suite(suite_name, test_plan_id, suite_id)
    create_children_suites(test_plan_id, row_id)


def create_children_suites(test_plan, suite_id):
    """
        Creates the third tier child suites
    """
    suite_name = "Automatic Regression"
    create_suite(suite_name, test_plan, suite_id)
    suite_name = "Manual Regression"
    create_suite(suite_name, test_plan, suite_id)
    suite_name = "New Features"
    create_suite(suite_name, test_plan, suite_id)


def create_customer_children(test_plan_id, suite_id, parent_suite):
    """
        Creates third tier child suites for Customer Solutions suite
    """
    suite_name = "SVE " + parent_suite
    row_id = create_suite(suite_name, test_plan_id, suite_id)
    suite_name = "Garden " + parent_suite
    row_id = create_suite(suite_name, test_plan_id, suite_id)
    suite_name = "Meter Farm " + parent_suite
    row_id = create_suite(suite_name, test_plan_id, suite_id)
# endregion

# region Create Full Dashboard


def create_full_dash(folder, url, global_path, target_choice, short_name,
                     test_choice, test_suite):
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
    test_plan = return_suite_test_plan_id(test_suite, test_choice)
    dash_id = create_dash(team_name, folder)
    query_folder = create_query_folder(folder)
    populate_baseline_query_folder(query_folder, target_choice, global_path, short_name)
    make_dash(team_name, url, test_plan, folder, query_folder, dash_id)

    create_config(team_name, url, dash_id, test_plan, folder, query_folder)
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
        raise FolderAlreadyExists("Query Folder with name " + folder + " already exists")


def return_suite_test_plan_id(test_suite, test_choice):
    """
        Returns test plan ID given test suite ID and testChoice

        :return test plan id as a string
    """
    if test_choice == "1":
        test_plan_id = return_test_plan_id(test_suite)
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
    dash_response = response.json()

    # indicates that a dashboard with dashName already exists
    if response.status_code != 200:
        raise DashAlreadyExists("Dashboard with name " + dash_name
                                + " already exists")

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
        raise FolderAlreadyExists('Query Folder with name "' + folder + '" already exists')

    query_response = response.json()
    return query_response['id']


def populate_baseline_query_folder(query_folder, target_choice, global_reqs_path, short_name):
    """
        Populates the given folder with the standard queries
    """
    json_obj = {"name": "New Bugs"}

    # Target clause is dependent on User's GUI choice
    if str(target_choice) == '0':
        target_clause = "[Custom.TargetedProject] contains " + repr(short_name)
    else:
        target_clause = "[System.Tags] contains " + repr(short_name)

    # New Bugs Query
    wiql = "select [System.Id], [System.WorkItemType], [System.Title]," \
           " [Microsoft.VSTS.Common.Severity], [Microsoft.VSTS.Common.Priority]," \
           " [System.AssignedTo], [System.State], [System.CreatedDate]," \
           " [Microsoft.VSTS.Common.ResolvedDate], [System.Tags] " \
           "from WorkItems where [System.WorkItemType] = 'Bug' " \
           "and [System.State] in ('New', 'Active') and " + target_clause \
           + " and not [System.Tags] contains 'Monitor'"
    json_obj["wiql"] = wiql
    create_query(json_obj, query_folder)
    print("Created New Bugs Query for: " + short_name)

    # All Bugs Query
    json_obj["name"] = short_name + " All"
    wiql = "select [System.Id], [System.WorkItemType], [System.Title]," \
           " [Microsoft.VSTS.Common.Severity], [Microsoft.VSTS.Common.Priority]," \
           " [System.AssignedTo], [System.State], [System.CreatedDate]," \
           " [Microsoft.VSTS.Common.ResolvedDate], [System.Tags] " \
           "from WorkItems where [System.WorkItemType] = 'Bug' " \
           "and " + target_clause + \
           " order by [System.CreatedDate] desc"
    json_obj["wiql"] = wiql
    create_query(json_obj, query_folder)
    print("Created All Bugs Query for: " + short_name)

    # All closed this week Query
    json_obj["name"] = short_name + " All closed this week"
    wiql = "select [System.Id], [System.WorkItemType], [System.Title], " \
           "[System.AssignedTo], [System.State], [System.Tags], " \
           "[System.CreatedBy], [System.CreatedDate], " \
           "[Microsoft.VSTS.Common.Severity], " \
           "[Microsoft.VSTS.Common.ClosedDate] " \
           "from WorkItems where [System.WorkItemType] = 'Bug' " \
           "and " + target_clause \
           + " and [Microsoft.VSTS.Common.ClosedDate] >= @today - 7 " \
             "and [System.State] = 'Closed' order by [System.CreatedDate] desc"
    json_obj["wiql"] = wiql
    create_query(json_obj, query_folder)
    print("Created All closed this week Query for: " + short_name)

    # All created this week Query
    json_obj["name"] = short_name + " All created this week"
    wiql = "select [System.Id], [System.WorkItemType], [System.Title], " \
           "[System.AssignedTo], [System.State], [System.Tags], " \
           "[System.CreatedBy], [System.CreatedDate], " \
           "[Microsoft.VSTS.Common.Severity] " \
           "from WorkItems where [System.WorkItemType] = 'Bug' " \
           "and " + target_clause \
           + " and [System.CreatedDate] > @today - 7 " \
             "order by [System.CreatedDate] desc"
    json_obj["wiql"] = wiql
    create_query(json_obj, query_folder)
    print("Created All created this week Query for: " + short_name)

    # All Monitored Query
    json_obj["name"] = short_name + " All Monitored"
    wiql = "select [System.Id], [System.WorkItemType], [System.Title]," \
           " [Microsoft.VSTS.Common.Severity], [Microsoft.VSTS.Common.Priority]," \
           " [System.AssignedTo], [System.State], [System.CreatedDate]," \
           " [Microsoft.VSTS.Common.ResolvedDate], [System.Tags] " \
           "from WorkItems where [System.WorkItemType] = 'Bug' " \
           "and not [System.State] contains 'Closed' " \
           "and " + target_clause + \
           " and [System.Tags] contains 'Monitor' " \
           "order by [System.CreatedDate] desc"
    json_obj["wiql"] = wiql
    create_query(json_obj, query_folder)
    print("Created All Monitored Query for: " + short_name)

    # All NOT Closed Query
    json_obj["name"] = short_name + " All NOT Closed"
    wiql = "select [System.Id], [System.WorkItemType], [System.Title]," \
           " [Microsoft.VSTS.Common.Severity], [Microsoft.VSTS.Common.Priority], " \
           "[System.AssignedTo], [System.State], [System.CreatedDate], " \
           "[Microsoft.VSTS.Common.ResolvedDate], [System.Tags] " \
           "from WorkItems where [System.WorkItemType] = 'Bug' " \
           "and not [System.State] in ('Closed', 'Resolved') " \
           "and " + target_clause + \
           " order by [System.CreatedDate] desc"
    json_obj["wiql"] = wiql
    create_query(json_obj, query_folder)
    print("Created All NOT Closed Query for: " + short_name)

    # All Resolved this week Query
    json_obj["name"] = short_name + " All resolved this week"
    wiql = "select [System.Id], [System.WorkItemType], [System.Title], " \
           "[System.AssignedTo], [System.State], [System.Tags], " \
           "[System.CreatedBy], [System.CreatedDate], " \
           "[Microsoft.VSTS.Common.Severity], " \
           "[Microsoft.VSTS.Common.ResolvedDate] " \
           "from WorkItems where [System.WorkItemType] = 'Bug' " \
           "and " + target_clause + \
           " and [Microsoft.VSTS.Common.ResolvedDate] >= @today - 7 " \
           "and [System.State] = 'Resolved' " \
           "order by [System.CreatedDate] desc"
    json_obj["wiql"] = wiql
    create_query(json_obj, query_folder)
    print("Created All Resolved This Week Query for: " + short_name)

    # RTT Query
    json_obj["name"] = "RTT"
    wiql = "select [System.Id], [System.WorkItemType], [System.Title]," \
           " [Microsoft.VSTS.Common.Severity], [Microsoft.VSTS.Common.Priority]," \
           " [System.AssignedTo], [System.State], [System.CreatedDate]," \
           " [Microsoft.VSTS.Common.ResolvedDate], [System.Tags] " \
           "from WorkItems where [System.WorkItemType] = 'Bug' " \
           "and [System.State] = 'Resolved' and " + target_clause + \
           " and not [System.Tags] contains 'Monitor'"
    json_obj["wiql"] = wiql
    create_query(json_obj, query_folder)
    print("Created RTT Query for: " + short_name)

    # SQA Test Features Query
    json_obj["name"] = "SQA Test Features"
    wiql = "select [System.Id], [System.WorkItemType], [System.Title], " \
           "[System.AssignedTo], [System.State], [System.Tags] " \
           "from WorkItems " \
           "where [System.WorkItemType] = 'Feature' and [System.AreaPath] " \
           "under 'GlobalReqs\\System Test' and [System.IterationPath] " \
           "under " + repr(global_reqs_path) + " and [System.State] <> 'Removed' " \
                                               "order by [System.Id] "
    json_obj["wiql"] = wiql
    create_query(json_obj, query_folder)
    print("Created SQA Test Features Query for: " + short_name)

    # SQA Test Features without test cases
    json_obj["name"] = "SQA Test Features without test cases"
    wiql = "select [System.Id], [System.WorkItemType], [System.Title], " \
           "[System.AssignedTo], [System.State], [System.Tags] " \
           "from WorkItemLinks " \
           "where (Source.[System.WorkItemType] = 'Feature' " \
           "and Source.[System.AreaPath] under 'GlobalReqs\\System Test' " \
           "and Source.[System.IterationPath] under " \
           + repr(global_reqs_path) + ") " \
           "and (Target.[System.WorkItemType] = 'Test Case') " \
           "and Source.[System.State] <> 'Removed' " \
           "order by [System.Id] mode (DoesNotContain)"
    json_obj["wiql"] = wiql
    create_query(json_obj, query_folder)
    print("Created SQA Test Features without test cases Query for: "
          + short_name)


def make_dash(output_team, url, test_plan, program_name, query_folder,
              overview_id):
    """
        Populates a given dashboard with widgets based on the queries
        in the query folder provided, and the test suites found in the given
        test plan.
    """
    # region First Widget Row
    test_suite_id = str(int(test_plan) + 1)
    url = url.strip()
    tree_link = "\n"

    if url:
        tree_link = " \n [Link To Requirements Tree](" + url + ") "

    # region Main MarkDown
    main_text = "#" + program_name + tree_link + "\n # \n " \
                                                 "#Overall Program Test Status \n #------->"

    main_markdown = return_markdown(1, 1, main_text)
    create_widget(output_team, overview_id, main_markdown)
    # endregion

    # region 4 Query Tile
    # Creating All Bugs widget
    name = "All Bugs"
    color = "#fbbc3d"
    query_contains = "All NOT Closed"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    all_bugs = return_query_tile(2, 1, name, query_name, query_id, color)
    create_widget(output_team, overview_id, all_bugs)

    # Creating Dev Bugs widget
    name = "Dev Bugs"
    color = "#e60017"
    query_contains = "New Bugs"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    dev_bugs = return_query_tile(3, 1, name, query_name, query_id, color)
    create_widget(output_team, overview_id, dev_bugs)

    # Creating Monitored widget
    name = "Monitored"
    color = "#cccccc"
    query_contains = "All Monitored"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    monitored_tile = return_query_tile(2, 2, name, query_name, query_id, color)
    create_widget(output_team, overview_id, monitored_tile)

    # Creating RTT widget
    name = "RTT"
    color = "#c9e7e7"
    query_contains = "RTT"
    query_name = return_query_name(query_contains, query_folder)
    query_id = return_query_id(query_contains, query_folder)
    rtt_tile = return_query_tile(3, 2, name, query_name, query_id, color)
    create_widget(output_team, overview_id, rtt_tile)
    # endregion

    # region Bug Trend
    name = program_name + " Bug Trend"
    query_id = return_query_id("All NOT Closed", query_folder)
    history = "last12Weeks"

    bug_trend = return_chart(4, 1, name, query_id, history=history, direction="descending")
    create_widget(output_team, overview_id, bug_trend)
    # endregion

    # region Bug Severity
    name = program_name + " Bug Severity"
    query_id = return_query_id("All NOT Closed", query_folder)
    chart_type = "ColumnChart"

    bug_severity = return_chart(6, 1, name, query_id, chart_type=chart_type)
    create_widget(output_team, overview_id, bug_severity)
    # endregion

    # region RTT Trend
    name = program_name + " RTT Trend"
    query_id = return_query_id("RTT", query_folder)
    history = "last12Weeks"

    rtt_trend = return_chart(8, 1, name, query_id, history=history, direction="descending")
    create_widget(output_team, overview_id, rtt_trend)
    # endregion

    # region RTT Severity
    name = "RTT Severity"
    query_id = return_query_id("RTT", query_folder)
    chart_type = "ColumnChart"
    # property_ = "value"

    rtt_severity = return_chart(10, 1, name, query_id, chart_type=chart_type)
    create_widget(output_team, overview_id, rtt_severity)
    # endregion

    # region Arrival Last 7 Days
    name = program_name + " Arrival Last 7 Days"
    query_id = return_query_id("All created this week", query_folder)
    chart_type = "stackBarChart"
    series = "System.CreatedDate"

    arrival_7_days = return_chart(12, 1, name, query_id, chart_type=chart_type, series=series)
    create_widget(output_team, overview_id, arrival_7_days)
    # endregion

    # region Resolved Last 7 Days
    name = program_name + " Resolved Last 7 Days"
    query_id = return_query_id("All resolved this week", query_folder)
    chart_type = "stackBarChart"
    series = "Microsoft.VSTS.Common.ResolvedDate"

    sys_features = return_chart(14, 1, name, query_id, chart_type=chart_type, series=series)
    create_widget(output_team, overview_id, sys_features)
    # endregion

    # region Closed Last 7 Days
    name = program_name + " Closed Last 7 Days"
    query_id = return_query_id("All closed this week", query_folder)
    chart_type = "stackBarChart"
    series = "Microsoft.VSTS.Common.ClosedDate"

    sys_features = return_chart(16, 1, name, query_id, chart_type=chart_type, series=series)
    create_widget(output_team, overview_id, sys_features)
    # endregion
    # endregion

    # region Second Row Widgets

    resources_suite = return_suite_child_id("Resource", test_plan,
                                            test_suite_id)
    # if the resources suite is not found then create two blank widgets instead
    if resources_suite == NOT_FOUND:
        # Create and place blank widgets with "Resource Path Not Found" message
        # on dashboard
        blank = return_blank_square(2, 3, "#No Resources Test Plan Path found")
        create_widget(output_team, overview_id, blank)
        blank = return_blank_square(4, 3, "#No Resources Test Plan Path found")
        create_widget(output_team, overview_id, blank)
    else:
        # return the child suite within resources
        name = "All New Feature Test Cases (Resources)"
        suite = return_suite_child_id("New", test_plan,
                                      resources_suite)
        new_features = return_test_chart(2, 3, name, suite, test_plan)
        create_widget(output_team, overview_id, new_features)
        # endregion

        # region All Manual Regression (Resources)
        name = "All Regression Test Cases"
        suite = return_suite_child_id("Reg", test_plan,
                                      resources_suite)
        new_features = return_test_chart(4, 3, name, suite, test_plan)
        create_widget(output_team, overview_id, new_features)
        # endregion

    # region SQA Test Features by State
    # noinspection SpellCheckingInspection
    name = "System Test Features by State (GlobalReqs)"
    query_id = return_query_id("SQA Test Features", query_folder)
    group = "System.State"
    chart_type = "PieChart"
    property_ = "value"
    direction = "descending"
    scope = "WorkitemTracking.Queries"

    sys_features = return_chart(6, 3, name, query_id, chart_type=chart_type,
                                group=group, _property=property_,
                                direction=direction, scope=scope)
    create_widget(output_team, overview_id, sys_features)
    # endregion

    # region SQA Test Features without test cases
    name = "SQA Test Features without test cases"
    query_title = "SQA Test Features without test cases"
    query_id = return_query_id(query_title, query_folder)

    all_features = return_features_table(8, 3, name, query_id)
    create_widget(output_team, overview_id, all_features)
    # endregion

    create_widget(output_team, overview_id, return_blank_square(12, 3))
    create_widget(output_team, overview_id, return_blank_square(14, 3))
    # endregion

    # region Early System Test
    starting_row = 5

    # return all children suites of "Early System Test" and sort
    early_system = return_suite_child_id("Early System Test", test_plan,
                                         test_suite_id)

    if early_system != NOT_FOUND:
        suite_list = return_suite_child_list(test_plan, early_system)

        # Creates a Early System Test row per Alpha found in Test Plan tree
        for suite in suite_list:
            suite_id = str(suite['id'])
            suite_name = suite['name']
            starting_column = 2
            count = 0
            # suite_name = Return_Suite_Name(suite_id, testPlanId)
            # region Alpha Markdown
            row_text = "#Early \n #System Test \n ###" + suite_name + "\n#------->"

            row_markdown = return_markdown(1, starting_row, row_text, height=2)
            create_widget(output_team, overview_id, row_markdown)
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

            while count <= 7:
                create_widget(output_team, overview_id,
                              return_blank_square(starting_column, starting_row))
                count += 1
                starting_column += 2

            starting_row += 2  # each widget is of size 2 so we much increment by 2
    # suite_id = Return_Suite_ID(Alpha + str(count), testPlanId)
    # endregion

    # region System Test
    system_suite_id = return_suite_child_id("System Test", test_plan,
                                            test_suite_id)
    if system_suite_id != NOT_FOUND:
        suite_list = return_suite_child_list(test_plan, system_suite_id)

        # Creates row of System Test widgets for each Run found in System Test
        for suite in suite_list:
            suite_id = str(suite['id'])
            suite_name = suite['name']
            starting_column = 2
            count = 0

            # region System Test Markdown
            row_text = "#System Test \n ###" + suite_name + "\n#------->"

            row_markdown = return_markdown(1, starting_row, row_text, height=2)
            create_widget(output_team, overview_id, row_markdown)
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
            while count <= 7:
                create_widget(output_team, overview_id,
                              return_blank_square(starting_column, starting_row))
                count += 1
                starting_column += 2

            starting_row += 2  # each widget is of size 2 so we much increment by 2
    # endregion

    # region Customer Solution

    customer_solution = return_suite_child_id("Customer Solution", test_plan,
                                              test_suite_id)
    if customer_solution != NOT_FOUND:
        suite_list = return_suite_child_list(test_plan, customer_solution)
        # Creates a row of Customer widgets per Run found in Customer Solution tree
        for suite in suite_list:
            suite_id = str(suite['id'])
            suite_name = suite['name']
            starting_column = 2
            count = 0

            # region Customer Solution Markdown
            row_text = "#Customer Solution \n ###" + suite_name + " \n#------->"

            row_markdown = return_markdown(1, starting_row, row_text, height=2)
            create_widget(output_team, overview_id, row_markdown)
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

            while count <= 7:
                create_widget(output_team, overview_id,
                              return_blank_square(starting_column, starting_row))
                count += 1
                starting_column += 2

            starting_row += 2  # each widget is of size 2 so we much increment by 2
    # endregion

    # region First Article
    first_article = return_suite_child_id("First Article", test_plan,
                                          test_suite_id)
    if first_article != NOT_FOUND:
        suite_list = return_suite_child_list(test_plan, first_article)
        # Creates a row of First Article widgets per Run found in First Article tree
        for suite in suite_list:
            suite_id = str(suite['id'])
            suite_name = suite['name']
            starting_column = 2
            count = 0

            # region Customer Solution Markdown
            row_text = "#First Article Test\n ###" + suite_name + " \n#------->"

            row_markdown = return_markdown(1, starting_row, row_text, height=2)
            create_widget(output_team, overview_id, row_markdown)
            count += 1
            # endregion

            # region Customer Solution - Test Case Readiness
            name = suite_name + " - Test Case Readiness"
            test_readiness = return_test_chart(starting_column, starting_row, name,
                                               suite_id, test_plan)
            create_widget(output_team, overview_id, test_readiness)
            starting_column += 2
            count += 1
            # endregion

            # region Overall - Customer Solution
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

            while count <= 7:
                create_widget(output_team, overview_id,
                              return_blank_square(starting_column, starting_row))
                count += 1
                starting_column += 2

            starting_row += 2  # each widget is of size 2 so we much increment by 2
    # endregion


def create_config(team_name, url, dash_id, test_plan, folder_name, folder_id):
    """
        Creates a JSON config file with the parameters provided, this is used
        when performing the update function
    """
    now = datetime.datetime.now()
    date_string = now.strftime("%d/%m/%Y %H:%M:%S")
    file_directory = CONFIGS_PATH + folder_name + '.txt'

    config_file = {
        'teamName': team_name,
        'url': url,
        'dashId': dash_id,
        'testPlan': test_plan,
        'folderName': folder_name,
        'folderId': folder_id,
        'version': VERSION,
        'lastUpdate': date_string
    }

    with open(file_directory, 'w') \
            as outfile:
        json.dump(config_file, outfile)


def return_test_plan_id(test_plan, continuation_token=''):
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
            # if(type == child["name"].split(' ')[0]):
            return str(child["id"])
    if continue_key not in response.headers._store:
        raise TestPlanError("Test Plan: " + test_plan + " not Found in Azure")
    return return_test_plan_id(test_plan, response.headers._store[continue_key][1])


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
            # if(type == child["name"].split(' ')[0]):
            return child["name"]
    return NOT_FOUND


def return_query_id(name, folder):
    """
        Returns the query id if a query if it is found in the given folder

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


def return_chart(column, row, name, query_id, chart_type="StackAreaChart",
                 aggregation="count", group="Microsoft.VSTS.Common.Severity",
                 _property="label", direction="ascending", series="",
                 history="", scope=""):
    """
        Creates a chart widget

        :returns the json template for the chart
    """
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
    settings["transformOptions"]["groupBy"] = group
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


def return_blank_square(column, row, name=" "):
    """
        Returns a json template for each widget type

        Optional parameter name for markdown text

        :return json template for a blank markdown
    """
    blank_square = return_widget_obj("Markdown")
    blank_square["settings"] = name
    blank_square["size"]["columnSpan"] = 2
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
    settings["userColors"] = standardPieChartColorArray

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

        :return list of child suites
    """
    child_list = []

    trigger_list = ['Alpha', 'Beta', 'Run']

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

    child_list = sorted(child_list, key=lambda name: child['name'])
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
                "lastArtifactName": "All NOT Closed by Severity"
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
                "queryName": "PEA1.5 All NOT Closed",
                "colorRules": [],
                "lastArtifactName": "PEA1.5 All NOT Closed"
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

    child_list.clear()
    for key in sorted_dictionary:
        if sorted_dictionary[key]:
            items = sorted_dictionary[key]
            for item in items:
                child_list.append(item)

    return child_list
# endregion

# region Update Dashboard


def get_config():
    directory = CONFIGS_PATH
    file_path = os.listdir(directory)
    file_path.sort()
    config_data = []
    for file in file_path:
        file1 = directory + file
        with open(file1, 'r') as json_file:
            config_data.append(json.load(json_file))
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


def clear_dash(team_name, dashboard_id):
    """
        Clears all widgets from a dashboard
    """
    version = {'api-version': '4.1-preview.2'}
    response = requests.get(URL_HEADER + PROJECT + '/' + team_name
                            + '/_apis/dashboard/dashboards/' + dashboard_id
                            + '?', auth=HTTPBasicAuth(USER, TOKEN),
                            params=version)
    dash_response = response.json()
    for widgets in dash_response["widgets"]:
        print(widgets["id"])
        delete_widget(team_name, widgets["id"], dashboard_id)
    print("Dashboard cleared")


def update_dash(file):
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
        folder = config_data['folderName']
        query_folder = config_data['folderId']

    clear_dash(team_name, dash_id)
    make_dash(team_name, url, test_plan, folder, query_folder, dash_id)
    print("Dashboard Updated")

    now = datetime.datetime.now()
    date_string = now.strftime("%d/%m/%Y %H:%M:%S")
    with open(file_directory, 'w') as outfile:
        config_data['lastUpdate'] = date_string
        json.dump(config_data, outfile)

# endregion
