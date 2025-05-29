from django.urls import path
from . import views

urlpatterns = [
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    
    path('profile/visitor/', views.visitor_profile, name='visitor_profile'),
    path('profile/vet/', views.vet_profile, name='vet_profile'),
    path('profile/staff/', views.staff_profile, name='staff_profile'),
    
    path('profile/visitor/update/', views.update_visitor_profile, name='update_visitor_profile'),
    path('profile/vet/update/', views.update_vet_profile, name='update_vet_profile'),
    path('profile/staff/update/', views.update_staff_profile, name='update_staff_profile'),
    
    path('profile/password/', views.password_change, name='password_change'),
]