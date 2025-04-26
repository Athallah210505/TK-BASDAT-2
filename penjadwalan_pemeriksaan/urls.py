from django.urls import path
from . import views

urlpatterns = [
    path('', views.show_jadwal_pemeriksaan, name='show_jadwal_pemeriksaan'),
    path('jadwal_satu_hewan', views.show_jadwal_satu_hewan, name='show_jadwal_satu_hewan'),
]