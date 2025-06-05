from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'inventory'

urlpatterns = [
    path('', views.item_list, name='item_list'),
    path('create/', views.item_create, name='item_create'),
    path('inventory/<int:item_id>/', views.item_detail, name='item_detail'),
    path('<int:pk>/edit/', views.item_update, name='item_update'),
    path('<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('stockin/', views.Stock_In_Records, name='stock_in_records'),
    path('stockin/<int:pk>/edit/', views.stockin_update, name='stockin_update'),
    path('stockin/<int:pk>/delete/', views.stockin_delete, name='stockin_delete'),
]

