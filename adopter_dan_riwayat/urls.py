from django.urls import path
from . import views

urlpatterns = [
    path('adopters/', views.adopter_list, name='adopter_list'),
    path('adopters/detail/<str:adopter_id>/', views.adopter_detail, name='adopter_detail'),
    path('adopters/detail/', views.adopter_detail, name='adopter_detail_default'),
    path('api/adoptions/<str:adoption_id>/', views.delete_adoption, name='delete_adoption'),
    path('api/adopters/<str:adopter_id>/', views.delete_adopter, name='delete_adopter'),
]