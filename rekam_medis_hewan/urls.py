from django.urls import path
from . import views

urlpatterns = [
    path('', views.show_rekam_medis, name='show_rekam_medis'),
    path('form/', views.form_rekam_medis, name='form_rekam_medis'),
]
