from django.urls import path
from . import views

urlpatterns = [
    path('', views.show_user_booking, name='show_user_booking'),
    path('admin_booking/', views.show_admin_booking, name='show_admin_booking'),
    path('user_booking/', views.show_user_booking, name='show_user_booking'),
]
