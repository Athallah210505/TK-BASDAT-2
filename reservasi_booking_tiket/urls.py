from django.urls import path
from . import views

urlpatterns = [
    path('', views.show_user_booking, name='show_user_booking'),
    path('admin_booking/', views.show_admin_booking, name='show_admin_booking'),
    path('user_booking/', views.show_user_booking, name='show_user_booking'),
    path('user_add_booking/', views.show_user_add_booking, name='show_user_add_booking'),
    path('user_edit_booking/', views.show_user_edit_booking, name='show_user_edit_booking'),    
    path('user_cancel_booking/', views.user_cancel_booking, name='user_cancel_booking'),
    path('add-wahana/', views.add_reservasi_wahana, name='add_reservasi_wahana'),
    path('admin_edit_booking/', views.admin_edit_booking, name='admin_edit_booking'),
    path('admin_cancel_booking/', views.admin_cancel_booking, name='admin_cancel_booking'),
    path ('check-availability/', views.check_availability, name='check_availability'),
]

