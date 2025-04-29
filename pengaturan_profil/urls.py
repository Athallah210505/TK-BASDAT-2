from django.urls import path
from . import views

urlpatterns = [
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
]