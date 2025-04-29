from django.urls import path
from . import views

app_name = 'habitat'

urlpatterns = [
    path('', views.habitat_list, name='habitat_list'),
    path('create/', views.habitat_create, name='habitat_create'),
    path('detail/', views.habitat_detail, name='habitat_detail'),
]