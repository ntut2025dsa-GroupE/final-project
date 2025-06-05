from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    path('', views.alert_view, name='alert_list'),
]
