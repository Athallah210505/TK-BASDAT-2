from django.urls import path
from main.views import show_main, show_management, show_atraksi_management, show_wahana_management, show_user_booking, show_admin_booking

app_name = 'main'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('management/', show_management, name='show_management'),
    path('atraksi/', show_atraksi_management, name='show_atraksi_management'),
    path('wahana/', show_wahana_management, name='show_wahana_management'),
    path('user_booking/', show_user_booking, name='show_user_booking'),
    path('admin_booking/', show_admin_booking, name='show_admin_booking'),
]