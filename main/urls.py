from django.urls import path
from . import views


urlpatterns = [
    path('', views.show_main, name='show_main'),
    path('staff_dashboard/', views.show_staff_dashboard, name='show_staff_dashboard'),
    path('dokter_hewan_dashboard/', views.dokter_hewan_dashboard, name='dokter_hewan_dashboard'),
    path('pengunjung_dashboard/', views.pengunjung_dashboard, name='pengunjung_dashboard'),
    path('penjaga_hewan_dashboard/', views.penjaga_hewan_dashboard, name='penjaga_hewan_dashboard'),
    path('pelatih_pertunjukan_dashboard/', views.pelatih_pertunjukan_dashboard, name='pelatih_pertunjukan_dashboard'),
]