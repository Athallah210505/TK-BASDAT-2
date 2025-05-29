from django.urls import path
from . import views

app_name = 'informasi'

urlpatterns = [
    path('satwa/', views.satwa_list, name='satwa_list'),
]
