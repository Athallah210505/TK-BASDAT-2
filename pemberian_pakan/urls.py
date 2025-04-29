from django.urls import path
from . import views

urlpatterns = [
    path('', views.show_pemberian_pakan, name='show_pemberian_pakan'),
    path('riwayat_pakan/', views.riwayat_pemberian_pakan, name='riwayat_pemberian_pakan'),
]