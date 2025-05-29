from django.urls import path
from . import views

urlpatterns = [
    path('', views.show_jadwal_pemeriksaan, name='show_jadwal_pemeriksaan'),
    path('jadwal_satu_hewan', views.show_jadwal_satu_hewan, name='show_jadwal_satu_hewan'),
    path('jadwal_satu_hewan/edit/', views.edit_jadwal_pemeriksaan, name='edit_jadwal_pemeriksaan'),
    path('jadwal_satu_hewan/hapus/', views.hapus_jadwal_pemeriksaan, name='hapus_jadwal_pemeriksaan'),
    path('jadwal_satu_hewan/tambah/', views.tambah_jadwal_pemeriksaan, name='tambah_jadwal_pemeriksaan'),
    path('jadwal_satu_hewan/edit-frekuensi/', views.edit_frekuensi_pemeriksaan, name='edit_frekuensi_pemeriksaan'),
]
