from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^$', views.home, name='ADS Dash Home'),
    url(r'^home', views.home, name='ADS Create Full Dash'),
    url(r'^test_plan', views.test_plan, name='ADS Dash Test Plan'),
    url(r'^update', views.update, name='Update Dashboard'),
]