# home/urls.py
from django.urls import path
from home.views import home  # <- import 'home', not 'index'

urlpatterns = [
    path('', home, name='index')
]
