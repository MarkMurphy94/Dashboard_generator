from django.conf import settings
from requests.auth import HTTPBasicAuth

import json
import requests


# reading in token credentials for user

TOKEN_PATH = settings.BASE_DIR + r'\ads_app\static\token.txt'
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
PMO_PATH = settings.BASE_DIR + r'\ads_app\static\PMO_List.txt'

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
        raise DashAlreadyExists("API Response: " + str(response.status_code)
                                + "\nTest Plan with name " + test_plan
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
        raise DashAlreadyExists("API Response: " + str(response.status_code)
                                + "\nTest Plan with name " + suite_name
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
