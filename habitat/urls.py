from django.urls import path
from . import views

app_name = 'habitat'

urlpatterns = [
    path('', views.habitat_list, name='habitat_list'),
    path('create/', views.habitat_create, name='habitat_create'),
    path('<str:nama>/edit/', views.habitat_edit, name='habitat_edit'),
    path('<str:nama>/delete/', views.habitat_delete, name='habitat_delete'),
    path('<str:nama>/', views.habitat_detail, name='habitat_detail'),
]