from django.urls import path
from . import views

urlpatterns = [
    path('pemberian-pakan/', views.show_pemberian_pakan, name='show_pemberian_pakan'),
    path('pemberian-pakan/<uuid:id_hewan>/', views.show_pemberian_pakan, name='show_pemberian_pakan'),
    
    path('pemberian-pakan/<uuid:id_hewan>/tambah/', views.add_feeding_schedule, name='add_feeding_schedule'),
    path('pemberian-pakan/<uuid:id_hewan>/edit/<str:jadwal>/', views.update_feeding_schedule, name='update_feeding_schedule'),
    path('pemberian-pakan/<uuid:id_hewan>/hapus/<str:jadwal>/', views.delete_feeding_schedule, name='delete_feeding_schedule'),
    path('pemberian-pakan/<uuid:id_hewan>/selesai/<str:jadwal>/', views.mark_feeding_complete, name='mark_feeding_complete'),
    
    path('riwayat-pemberian-pakan/', views.riwayat_pemberian_pakan, name='riwayat_pemberian_pakan'),
]