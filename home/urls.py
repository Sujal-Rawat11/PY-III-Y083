# home/urls.py
from django.urls import path
from home.views import home

app_name = 'home'  # <-- add this line

urlpatterns = [
    path('', home, name='index'),
]
