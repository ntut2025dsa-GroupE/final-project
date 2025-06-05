from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.transaction_list, name='transaction_list'),
    path('new/', views.transaction_create, name='transaction_create'),
    path('export_csv/', views.export_csv, name='export_csv'),
]
