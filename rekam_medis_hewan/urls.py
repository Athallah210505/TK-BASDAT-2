from django.urls import path
from . import views

urlpatterns = [
    path('', views.show_rekam_medis, name='show_rekam_medis'),
    path('form/', views.form_rekam_medis, name='form_rekam_medis'),
    path('edit/', views.edit_rekam_medis, name='edit_rekam_medis'),
    path('delete/', views.delete_rekam_medis, name='delete_rekam_medis'),
    path('hewan/', views.list_rekam_medis_hewan, name='list_rekam_medis_hewan'),

]