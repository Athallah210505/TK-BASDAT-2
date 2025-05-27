from django.urls import path
from . import views

urlpatterns = [
    # Atraksi management routes
    path('', views.show_atraksi_management, name='show_atraksi_management'),
    path('add/', views.add_atraksi, name='add_atraksi'),
    path('<str:id>/data/', views.get_atraksi_data, name='get_atraksi_data'),
    path('edit/<str:id>/', views.edit_atraksi, name='edit_atraksi'),
    path('delete/<str:id>/', views.delete_atraksi, name='delete_atraksi'),
    
    # Wahana management routes
    path('wahana/', views.show_wahana_management, name='show_wahana_management'),
    path('wahana/add/', views.add_wahana, name='add_wahana'),
    path('wahana/edit/<str:nama_wahana>/', views.edit_wahana, name='edit_wahana'),
    path('wahana/delete/<str:nama_wahana>/', views.delete_wahana, name='delete_wahana'),
    path('wahana/data/<str:nama_wahana>/', views.get_wahana_data, name='get_wahana_data'),
]