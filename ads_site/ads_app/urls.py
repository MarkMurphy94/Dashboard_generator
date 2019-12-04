from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='ADS Dash Home'),
    path('home', views.home, name='ADS Dash Home'),
    path('test_plan', views.test_plan, name='ADS Dash Test Plan'),
    path('update', views.update, name='Update Dashboard'),
]