from django.db import models
from django.conf import settings
import os
# Create your models here.

pmo_path = settings.BASE_DIR + r'\ads_app\static\PMO_List.txt'


def get_pmo_list():
    """
        returns the pmo list from the file in the pmo_path
    """

    with open(pmo_path, 'r') as lines:
        pmo_list = lines.readlines()

    return pmo_list

