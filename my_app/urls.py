from django.contrib import admin
from django.urls import path, include
from my_app import views

urlpatterns = [
    path('admin/', admin.site.urls, name = "admin"),
    path ('', views.home, name = "home"),

    path ('myapp/'), include("djangoProject.urls")
]