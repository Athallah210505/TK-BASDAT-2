from django.urls import path
from . import views

app_name = 'animals'

urlpatterns = [
    path('', views.animal_list, name='animal_list'),
    path('create/', views.animal_create, name='animal_create'),
    path('<int:pk>/update/', views.animal_update, name='animal_update'),
]