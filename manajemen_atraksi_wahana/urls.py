from django.urls import path
from . import views

urlpatterns = [
    path('', views.show_management, name='show_management'),
    path('atraksi/', views.show_atraksi_management, name='show_atraksi_management'),
    path('wahana/', views.show_wahana_management, name='show_wahana_management'),
]
