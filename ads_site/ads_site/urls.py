"""ads_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf.urls import url

EMAIL_PATH = settings.BASE_DIR + r'/authentication/templates/authentication/Password Reset Subject template.txt'

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('ads_app.urls')),
    url(r'^ads_app/', include('ads_app.urls')),
    url(r'^authentication/', include('authentication.urls')),
    url(r'^login/', auth_views.LoginView.as_view(template_name='authentication/login.html'), name='login'),
    url(r'^logout/', auth_views.LogoutView.as_view(template_name='authentication/logout.html'), name='logout'),
    url(r'^password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='authentication/password_reset_done.html'), name='password_reset_done'),
    url(r'^password-reset/', auth_views.PasswordResetView.as_view(template_name='authentication/password_reset.html',
                                                                  subject_template_name=EMAIL_PATH),
                                                                  name='password_reset'),
    url(r'^password-reset-confirm/(?P<uidb64>[^/]+)/(?P<token>[^/]+)/$', auth_views.PasswordResetConfirmView.as_view(template_name='authentication/password_reset_confirm.html'), name='password_reset_confirm'),
    url(r'^password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='authentication/password_reset_complete.html'), name='password_reset_complete'),
]
