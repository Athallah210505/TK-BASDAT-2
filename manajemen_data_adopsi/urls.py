from django.urls import path
from . import views

urlpatterns = [
    path('adoptions/', views.adoption_list, name='adoption_list'),
    path('adoption/<int:adoption_id>/', views.adoption_detail, name='adoption_detail'),
    path('adoption/register/<int:animal_id>/', views.register_adopter, name='register_adopter'),
    path('adoption/extend/<int:adoption_id>/', views.extend_adoption, name='extend_adoption'),
    path('adoption/end/<int:adoption_id>/', views.end_adoption, name='end_adoption'),
    path('adopter/<int:adopter_id>/', views.adopter_info, name='adopter_info'),
    path('adoption/certificate/<int:adoption_id>/', views.adoption_certificate, name='adoption_certificate'),
    path('adoption/reports/<int:adoption_id>/', views.animal_condition_report, name='animal_condition_report'),
    path('adoption/reports/create/<int:adoption_id>/', views.create_animal_report, name='create_animal_report'),
]