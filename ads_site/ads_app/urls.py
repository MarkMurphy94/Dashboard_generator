from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.home, name='ADS Dash Home'),
    url(r'^home', views.home, name='ADS Create Full Dash'),
    url(r'^test_plan', views.test_plan, name='ADS Dash Test Plan'),
    url(r'^agile_update', views.agile_update, name='ADS Update Agile Test Plan'),
    url(r'^create_test', views.create_test, name='ADS Loading'),
    url(r'^update', views.update, name='Update Dashboard'),
    url(r'^done', views.done, name='Complete'),
    url(r'^create_dash', views.create_dash, name='Create Dashboard'),
    url(r'^submit_update', views.submit_update, name='Submit Update'),
    url(r'^submit_agile_update', views.submit_agile_update, name='Submit Update'),
]