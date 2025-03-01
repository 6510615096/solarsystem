from django.urls import path
from django.contrib.auth import views as auth_views
from solarapp import views

app_name = "solarapp"

urlpatterns = [
    path("",views.login_request, name="login"),
    path("register/", views.register, name="register"),
    path("home/", views.home , name="home"),
    
]