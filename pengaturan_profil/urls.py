from django.urls import path
from . import views

urlpatterns = [
    path('pengaturan-profil_dh/', views.pengaturan_profil_dh, name='pengaturan_profil_dh'),
    path('ubah-password/', views.ubah_password, name='ubah_password'),

    path('pengaturan-profil/', views.pengaturan_profil_penjaga_hewan, name='pengaturan_profil_penjaga_hewan'),
    path('ubah-password/', views.ubah_password_penjaga_hewan, name='ubah_password_penjaga_hewan'),
]