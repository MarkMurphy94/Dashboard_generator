from django.contrib.auth import views as auth_views
from django.conf.urls import url

urlpatterns = [
    url(r'^$', auth_views.LoginView.as_view(template_name='authentication/login.html'), name='ADS Dash Login'),
]