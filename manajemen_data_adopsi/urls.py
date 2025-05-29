from django.urls import path
from . import views

urlpatterns = [
    path('adoptions/', views.adoption_list, name='adoption_list'),
    
    path('adoption/register/', views.register_adopter, name='register_adopter_general'),
    path('adoption/extend/', views.extend_adoption, name='extend_adoption_general'),
    path('adoption/end/', views.end_adoption, name='end_adoption_general'),
    path('adopter/', views.adopter_info, name='adopter_info_general'),
    path('adoption/certificate/', views.adoption_certificate, name='adoption_certificate_general'),
    path('adoption/reports/', views.animal_condition_report, name='animal_condition_report_general'),
    path('adoption/reports/create/', views.create_animal_report, name='create_animal_report_general'),
    
    path("adoption/<str:adoption_id>/", views.adoption_detail, name="adoption_detail"),    path('adoption/register/<uuid:animal_id>/', views.register_adopter, name='register_adopter'),
    path('adoption/extend/<str:adoption_id>/', views.extend_adoption, name='extend_adoption'),
    path('adoption/end/<str:adoption_id>/', views.end_adoption, name='end_adoption'),
    path('adopter/<uuid:adopter_id>/', views.adopter_info, name='adopter_info'),
    path('adoption/certificate/<str:adoption_id>/', views.adoption_certificate, name='adoption_certificate'),
    path('adoption/reports/<str:adoption_id>/', views.animal_condition_report, name='animal_condition_report'),
    path('adoption/reports/create/<str:adoption_id>/', views.create_animal_report, name='create_animal_report'),
]